const $ = (s) => document.querySelector(s);
const RT_VALUE_RE = /^(nodejs\d+\.x|python\d+\.\d+|ruby\d+\.\d+|java\d+|dotnet\d+|dotnetcore\d+\.\d+|go\d+\.x|provided\.al\d+|provided)\b/i;
const CDK_VALUE_RE = /Runtime\.(NODEJS|PYTHON|RUBY|JAVA|DOTNET|GO)_(\d+)(?:_(\d+))?(?:_X)?/i;
function cdkId(l, a, b) { l = l.toLowerCase(); if (l === 'nodejs') return 'nodejs' + a + '.x'; if (l === 'python') return 'python' + a + '.' + (b || '0'); if (l === 'ruby') return 'ruby' + a + '.' + (b || '0'); return l + a; }
function esc(s) { return String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }
function classify(name) {
  const n = name.replace(/\\/g, '/').split('/').pop().toLowerCase();
  if (n === 'package.json') return 'pkg';
  if (/^requirements[^/]*\.txt$/.test(n)) return 'req';
  if (n === 'pyproject.toml') return 'pyproject';
  if (/\.(yaml|yml|json|tf|hcl|ts|tsx|js|jsx|mjs|cjs|py|sh|txt)$/.test(n)) return 'iac';
  return null;
}
const SCAN_LIMITS = Object.freeze({ files: 100, fileBytes: 1048576, totalBytes: 10485760 });
class ScanInputError extends Error {}

function lineLookup(content) {
  const starts = [0];
  for (let i = 0; i < content.length; i++) if (content[i] === '\n') starts.push(i + 1);
  return index => {
    let low = 0, high = starts.length;
    while (low + 1 < high) { const middle = (low + high) >>> 1; if (starts[middle] <= index) low = middle; else high = middle; }
    return low + 1;
  };
}

// Token locations are retained from valid JSON rather than guessed from matching text.
// This disambiguates identical runtime/package values in unrelated objects.
function jsonInput(content) {
  let value;
  try { value = JSON.parse(content); }
  catch { throw new ScanInputError('Invalid JSON. Correct the syntax and scan again.'); }
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new ScanInputError('Expected a JSON object, not an array or scalar.');
  }
  const tokens = [...content.matchAll(/"(?:\\.|[^"\\])*"|[{}\[\],:]|[^\s{}\[\],:]+/g)];
  const properties = [];
  let cursor = 0, line = 1, previous = 0;
  for (const token of tokens) {
    for (let i = previous; i < token.index; i++) if (content[i] === '\n') line++;
    token.line = line;
    previous = token.index;
  }
  function visit(path) {
    if (path.length > 64) throw new ScanInputError('JSON nesting exceeds the 64-level scan limit.');
    const token = tokens[cursor++];
    if (token[0] === '{') {
      while (tokens[cursor][0] !== '}') {
        const key = JSON.parse(tokens[cursor++][0]);
        cursor++; // colon, already validated by JSON.parse
        visit(path.concat(key));
        if (tokens[cursor][0] === ',') cursor++;
      }
      cursor++;
    } else if (token[0] === '[') {
      let index = 0;
      while (tokens[cursor][0] !== ']') {
        visit(path.concat(String(index++)));
        if (tokens[cursor][0] === ',') cursor++;
      }
      cursor++;
    } else {
      properties.push({ path, value: JSON.parse(token[0]), line: token.line });
    }
  }
  visit([]);
  return { value, properties };
}

class RuntimeLocations extends Map {
  add(runtime, line) {
    if (!this.has(runtime)) this.set(runtime, new Set());
    if (Number.isInteger(line) && line > 0) this.get(runtime).add(line);
  }
}
function vtuple(v) { return (v || '').replace(/^[^\d]*/, '').split(/[.\-+]/).map((x) => parseInt(x, 10) || 0); }
function vlt(a, b) { const A = vtuple(a), B = vtuple(b); for (let i = 0; i < Math.max(A.length, B.length); i++) { const x = A[i] || 0, y = B[i] || 0; if (x < y) return true; if (x > y) return false; } return false; }
function cleanV(v) { return v ? v.replace(/^[\^~>=<\s]+/, '') : null; }
function extractMin(spec) { if (!spec) return null; for (const op of ['==', '>=']) { for (let part of spec.split(',')) { part = part.trim(); if (part.indexOf(op) === 0) return part.slice(op.length).trim(); } } return null; }
function runtimeId(value) {
  const cleaned = String(value || '').trim().replace(/^['"]/, '');
  const m = cleaned.match(RT_VALUE_RE);
  return m ? m[1].toLowerCase() : null;
}
function configRecords(c) {
  const records = [], stack = [], lines = c.split(/\r?\n/); let documentId = 0;
  const keyRe = /^([ \t]*)(["']?)([A-Za-z0-9_.-]+)\2\s*:\s*(.*)$/;
  for (let i = 0; i < lines.length; i++) {
    if (/^[ \t]*(?:---|\.\.\.)[ \t]*(?:#.*)?$/.test(lines[i])) { stack.length = 0; documentId++; continue; }
    const m = lines[i].match(keyRe); if (!m) continue;
    const indent = m[1].replace(/\t/g, '        ').length;
    while (stack.length && stack[stack.length - 1][0] >= indent) stack.pop();
    const key = m[3].toLowerCase();
    const raw = m[4].replace(/\s+#.*$/, '').trim().replace(/,$/, '').trim();
    let value = raw;
    if (value.length >= 2 && ((value[0] === '"' && value[value.length - 1] === '"') || (value[0] === "'" && value[value.length - 1] === "'"))) value = value.slice(1, -1);
    const path = stack.slice(-8).map((item) => item[1]).concat([key]);
    records.push({ documentId, line: i + 1, key, value, path });
    if (raw === '' || raw === '{') stack.push([indent, key]);
  }
  return records;
}
function samePath(left, right) { return left.length === right.length && left.every((value, index) => value === right[index]); }
function samDocuments(c) {
  const documents = new Set(); let documentId = 0, pendingIndent = null;
  for (const line of c.split(/\r?\n/)) {
    if (/^[ \t]*(?:---|\.\.\.)[ \t]*(?:#.*)?$/.test(line)) { documentId++; pendingIndent = null; continue; }
    const transform = line.match(/^([ \t]*)["']?Transform["']?\s*:\s*(.*)$/i);
    if (transform) {
      const value = transform[2].replace(/\s+#.*$/, '').trim();
      if (/AWS::Serverless-/i.test(value)) documents.add(documentId);
      pendingIndent = value ? null : transform[1].replace(/\t/g, '        ').length;
      continue;
    }
    if (pendingIndent === null || !line.trim()) continue;
    const indent = (line.match(/^[ \t]*/) || [''])[0].replace(/\t/g, '        ').length;
    if (indent <= pendingIndent) pendingIndent = null;
    else if (/^[ \t]*-[ \t]*["']?AWS::Serverless-/i.test(line)) { documents.add(documentId); pendingIndent = null; }
  }
  return documents;
}
function yamlLambdaRuntimes(c, found) {
  const records = configRecords(c), resources = new Set(), providers = new Set(), sam = samDocuments(c);
  for (const r of records) {
    if (r.key === 'type' && /^(AWS::Lambda::Function|AWS::Serverless::Function)$/i.test(r.value) && r.path.includes('resources')) resources.add(r.documentId + '\u0000' + r.path.slice(0, -1).join('\u0000'));
    if (samePath(r.path, ['provider', 'name']) && r.value.toLowerCase() === 'aws') providers.add(r.documentId);
  }
  for (const r of records) {
    if (r.key !== 'runtime') continue;
    const resourceRuntime = r.path.length >= 3 && samePath(r.path.slice(-2), ['properties', 'runtime']) && resources.has(r.documentId + '\u0000' + r.path.slice(0, -2).join('\u0000'));
    const samGlobal = sam.has(r.documentId) && samePath(r.path, ['globals', 'function', 'runtime']);
    const serverless = providers.has(r.documentId) && (samePath(r.path, ['provider', 'runtime']) || (r.path.length === 3 && r.path[0] === 'functions' && r.path[2] === 'runtime'));
    if (resourceRuntime || samGlobal || serverless) { const id = runtimeId(r.value); if (id) found.add(id, r.line); }
  }
}
function jsonLambdaRuntimes(c, found) {
  if (!c.trim().startsWith('{')) return;
  const { value: document, properties } = jsonInput(c);
  const transforms = Array.isArray(document.Transform) ? document.Transform : [document.Transform];
  const sam = transforms.some(item => typeof item === 'string' && item.toLowerCase().startsWith('aws::serverless-'));
  for (const record of properties) {
    const path = record.path;
    const resource = path.length === 4 && path[0] === 'Resources' && path[2] === 'Properties' && path[3] === 'Runtime'
      ? document.Resources?.[path[1]] : null;
    const lambda = resource && /^AWS::(?:Lambda|Serverless)::Function$/i.test(String(resource.Type || ''));
    if (lambda || (sam && samePath(path, ['Globals', 'Function', 'Runtime']))) {
      const id = runtimeId(record.value); if (id) found.add(id, record.line);
    }
  }
}
function hclCodeLines(c) {
  const output = []; let block = false, heredoc = null;
  for (const original of c.split(/\r?\n/)) {
    if (heredoc) { const candidate = heredoc[1] ? original.trim() : original; if (candidate === heredoc[0]) heredoc = null; output.push([original, ' '.repeat(original.length)]); continue; }
    const visible = [...original]; let quote = null, escaped = false, i = 0;
    while (i < original.length) {
      const ch = original[i], pair = original.slice(i, i + 2);
      if (block) { visible[i] = ' '; if (pair === '*/') { visible[i + 1] = ' '; block = false; i += 2; continue; } i++; continue; }
      if (quote) { visible[i] = ' '; if (escaped) escaped = false; else if (ch === '\\') escaped = true; else if (ch === quote) quote = null; i++; continue; }
      if (pair === '/*') { visible[i] = visible[i + 1] = ' '; block = true; i += 2; continue; }
      if (pair === '//' || ch === '#') { for (let j = i; j < visible.length; j++) visible[j] = ' '; break; }
      if (ch === '"' || ch === "'") { visible[i] = ' '; quote = ch; }
      i++;
    }
    const code = visible.join(''), marker = code.match(/<<(-?)([A-Za-z_][A-Za-z0-9_]*)/);
    if (marker) heredoc = [marker[2], marker[1] === '-'];
    output.push([original, code]);
  }
  return output;
}
function terraformLambdaRuntimes(c, found) {
  let inside = false, depth = 0, structuralEvents = 0, line = 0;
  const declaration = /\bresource\s+["']aws_lambda_function["']\s+["'][^"']+["']\s*\{/i;
  for (const pair of hclCodeLines(c)) {
    line++;
    const original = pair[0], code = pair[1], declarationMatch = inside ? null : original.match(declaration);
    const visibleResource = inside ? -1 : code.search(/\bresource\s+/i);
    const resource = declarationMatch && declarationMatch.index === visibleResource ? declarationMatch : null;
    if (resource) { inside = true; depth = 0; }
    if (!inside) continue;
    let position = resource ? resource.index : 0;
    while (position < code.length) {
      const character = code[position];
      if (character === '{') { depth++; structuralEvents++; }
      else if (character === '}') { depth--; structuralEvents++; }
      else if (depth === 1 && code.slice(position, position + 7).toLowerCase() === 'runtime') {
        const key = code.slice(position).match(/^\bruntime\b\s*=/i);
        if (!key) { position++; continue; }
        const runtime = original.slice(position).match(/^\bruntime\b\s*=\s*["']?([^"'\s}]+)/i), id = runtime && runtimeId(runtime[1]);
        if (id) found.add(id, line); position += key[0].length; structuralEvents++;
        if (structuralEvents > 100000) throw new ScanInputError('Terraform exceeds the scan complexity limit. Split the file and retry.');
        continue;
      }
      if (structuralEvents > 100000) throw new ScanInputError('Terraform exceeds the scan complexity limit. Split the file and retry.');
      if (depth <= 0 && character === '}') { inside = false; break; }
      position++;
    }
  }
}
function explicitLambdaRuntimes(c, found) {
  const importedRuntime = /(?:aws-cdk-lib|@aws-cdk)\/aws-lambda|from\s+aws_cdk\.aws_lambda\s+import[^\n]*\bRuntime\b|software\.amazon\.awscdk\.services\.lambda\.Runtime|Amazon\.CDK\.AWS\.Lambda/i.test(c);
  let number = 0;
  for (const line of c.split(/\r?\n/)) {
    number++;
    if (/^\s*(?:#|\/\/)/.test(line)) continue;
    const cli = line.match(/\baws\s+lambda\b[^\n]*--runtime(?:\s+|=)["']?([^"'\s]+)/i); const cliId = cli && runtimeId(cli[1]); if (cliId) found.add(cliId, number);
    const qualified = line.match(/\bruntime\b\s*[:=(]\s*(?:aws_)?_?lambda\.(Runtime\.[A-Z0-9_]+)/i);
    const imported = importedRuntime && line.match(/\bruntime\b\s*[:=(]\s*(Runtime\.[A-Z0-9_]+)/i);
    const cdk = qualified || imported; const match = cdk && cdk[1].match(CDK_VALUE_RE); const id = match && cdkId(match[1], match[2], match[3]); if (id) found.add(id, number);
  }
}
function scanIaC(file, c) {
  const f = new RuntimeLocations(), out = [];
  if (/\.json$/i.test(file) || c.trim().startsWith('{')) jsonLambdaRuntimes(c, f);
  else {
    yamlLambdaRuntimes(c, f);
    terraformLambdaRuntimes(c, f);
    explicitLambdaRuntimes(c, f);
  }
  f.forEach((locations, rt) => {
    const d = DATA.runtimes[rt];
    const lines = [...locations].sort((a, b) => a - b);
    if (d) out.push({ kind: 'runtime', file, name: rt, lines, severity: d.historical ? 'critical' : (d.severity || 'high'), date: d.date, deprecation: d.deprecation, blockUpdate: d.blockUpdate, projected: d.projected, source: d.source, guide: d.slug, kit: d.kit, historical: d.historical, note: d.historical ? 'Past a published milestone; recheck the linked provider status and enforcement dates.' : 'Runtime with an AWS-published deprecation and create/update restriction timeline.' });
  });
  return out;
}
function scanPkg(file, c) {
  const { value: pkg, properties } = jsonInput(c);
  for (const section of ['dependencies', 'devDependencies', 'optionalDependencies']) {
    if (pkg[section] !== undefined && (!pkg[section] || typeof pkg[section] !== 'object' || Array.isArray(pkg[section]) || Object.values(pkg[section]).some(v => typeof v !== 'string'))) {
      throw new ScanInputError(section + ' must be an object of package names and version strings.');
    }
  }
  const out = [];
  for (const property of properties) {
    if (property.path.length !== 2 || !['dependencies', 'devDependencies', 'optionalDependencies'].includes(property.path[0])) continue;
    const name = property.path[1];
    const info = Object.hasOwn(DATA.native, name) ? DATA.native[name] : null; if (!info) continue;
    const declared = cleanV(property.value);
    const evidence = { lines: [property.line], source: 'https://www.npmjs.com/package/' + encodeURIComponent(name) };
    if (info.min === null) { out.push({ ...evidence, kind: 'native', file, name, severity: 'critical', declared: declared || '(unpinned)', required: '(unmaintained — replace)', note: info.note }); continue; }
    if (declared && !vlt(declared, info.min)) { out.push({ ...evidence, kind: 'native', file, name, severity: 'low', declared, required: 'verify Node.js 24 support', note: 'Meets the configured older baseline; confirm the package release and rebuild/test on Node.js 24.' }); continue; }
    out.push({ ...evidence, kind: 'native', file, name, severity: 'high', declared: declared || '(unpinned)', required: '>= ' + info.min, note: info.note });
  }
  return out;
}
function pyFindings(pkgs, file) {
  const out = [];
  for (const pair of pkgs) {
    const name = pair[0].replace(/[._-]+/g, '-'), spec = pair[1], req = Object.hasOwn(DATA.wheels, name) ? DATA.wheels[name] : null; if (!req) continue;
    const evidence = { lines: [pair[2]], source: 'https://pypi.org/project/' + encodeURIComponent(name) + '/' };
    const declared = extractMin(spec);
    if (req.min === null) { out.push({ ...evidence, kind: 'wheel', file, name, severity: 'critical', declared: spec || '(unpinned)', required: '(no cp312 wheels)', note: req.note }); continue; }
    if (declared === null) { out.push({ ...evidence, kind: 'wheel', file, name, severity: 'low', declared: '(unpinned)', required: '>= ' + req.min, note: 'unpinned; pin >= ' + req.min + ' for reproducibility.' }); continue; }
    if (vlt(declared, req.min)) out.push({ ...evidence, kind: 'wheel', file, name, severity: 'high', declared: spec, required: '>= ' + req.min, note: req.note });
  }
  return out;
}
function parseReq(content) {
  const out = [];
  content.split(/\r?\n/).forEach((raw, index) => {
    const line = raw.trim();
    if (/^(?:-[rce]|--(?:requirement|constraint|editable))(?:[=\s]|[^-])/i.test(line)) {
      throw new ScanInputError('Referenced requirements, constraints, and editable installs are not resolved. Export a flat requirements.txt and scan it.');
    }
    if (!line || line[0] === '#' || line[0] === '-') return;
    const match = line.match(/^([A-Za-z0-9_.-]+)\s*(?:\[[^\]]*\])?\s*([<>=!~].+)?/);
    if (match) out.push([match[1].toLowerCase(), (match[2] || '').split(';')[0].trim() || null, index + 1]);
  });
  return out;
}

function parsePyproject(content) {
  const out = [];
  const lineNumber = lineLookup(content);
  // This is deliberately a bounded PEP 621 dependency-list scan, not TOML validation.
  // A table-based Poetry manifest is refused instead of appearing to have no risks.
  if (/^\s*\[tool\.poetry(?:\.|\])/m.test(content) && !/^\s*\[project\]/m.test(content)) {
    throw new ScanInputError('Poetry tables are not supported. Export requirements.txt and scan that file.');
  }
  const headers = [...content.matchAll(/^\s*\[([^\]\n]+)\][^\n]*$/gm)];
  for (let i = 0; i < headers.length; i++) {
    const section = headers[i][1].trim();
    if (!['project', 'project.optional-dependencies'].includes(section)) continue;
    const start = headers[i].index + headers[i][0].length;
    const block = content.slice(start, i + 1 < headers.length ? headers[i + 1].index : content.length);
    if (section === 'project' && /\bdynamic\s*=\s*\[[^\]]*["'](?:dependencies|optional-dependencies)["']/.test(block)) {
      throw new ScanInputError('Dynamic dependencies are not resolved. Export a flat requirements.txt and scan it.');
    }
    const arrays = /([A-Za-z0-9_-]+)\s*=\s*\[((?:[^"'\[\]]|"(?:\\.|[^"\\])*"|'[^']*')*)\]/g;
    let parsedList = false;
    for (const array of block.matchAll(arrays)) {
      if (section === 'project' && array[1] !== 'dependencies') continue;
      parsedList = true;
      const valuesStart = start + array.index + array[0].indexOf('[') + 1;
      for (const value of array[2].matchAll(/"([^"\n]*)"|'([^'\n]*)'/g)) {
        const requirement = value[1] ?? value[2];
        const match = requirement.match(/^\s*([A-Za-z0-9_.-]+)\s*(?:\[[^\]]*\])?\s*([<>=!~][^;]*)?/);
        if (match) out.push([match[1].toLowerCase(), (match[2] || '').trim() || null, lineNumber(valuesStart + value.index)]);
      }
    }
    if (!parsedList && (section === 'project' ? /^\s*dependencies\s*=/m.test(block) : /^\s*[A-Za-z0-9_-]+\s*=/m.test(block))) {
      throw new ScanInputError('Could not read the PEP 621 dependency list. Validate pyproject.toml or export requirements.txt.');
    }
  }
  return out;
}

function scanFile(name, content) {
  const kind = classify(name);
  if (!kind) throw new ScanInputError('Unsupported file type. Extract archives and choose supported source files.');
  if (typeof content !== 'string' || !content.trim()) throw new ScanInputError('File is empty. No source was scanned.');
  if (new TextEncoder().encode(content).length > SCAN_LIMITS.fileBytes) throw new ScanInputError('File exceeds the 1 MiB scan limit.');
  if (/[\u0000-\u0008\u000b\u000c\u000e-\u001f\ufffd]/.test(content)) throw new ScanInputError('File is binary or is not valid UTF-8 text.');
  if (/\.json$/i.test(name)) jsonInput(content);
  if (kind === 'pkg') return scanPkg(name, content);
  if (kind === 'req') return pyFindings(parseReq(content), name);
  if (kind === 'pyproject') return pyFindings(parsePyproject(content), name);
  return scanIaC(name, content);
}
