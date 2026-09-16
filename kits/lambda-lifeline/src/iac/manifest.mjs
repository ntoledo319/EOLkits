// Source spans let us change a literal without serializing the user's template.
// JSON is validated in full. YAML supports block and single-line flow mappings
// plus opaque list data; ambiguous structural values fail for manual review.

const mapping = () => ({ entries: new Map() });

function put(node, key, value) {
  if (!node.entries) throw new Error('Mixed YAML mapping and sequence; review manually.');
  if (node.entries.has(key)) throw new Error(`Duplicate manifest key ${JSON.stringify(key)}; review manually.`);
  node.entries.set(key, value);
}

export function parseJSON(text) {
  JSON.parse(text);
  const tokens = [...text.matchAll(/"(?:\\[\s\S]|[^"\\])*"|[{}\[\]:,]|[^\s{}\[\]:,]+/g)];
  let cursor = 0;
  function value() {
    const token = tokens[cursor++];
    if (token[0] === '{') {
      const result = mapping();
      while (tokens[cursor][0] !== '}') {
        const key = JSON.parse(tokens[cursor++][0]);
        cursor++; // colon; JSON.parse has validated the grammar
        put(result, key, value());
        if (tokens[cursor][0] === ',') cursor++;
      }
      cursor++;
      return result;
    }
    if (token[0] === '[') {
      const items = [];
      while (tokens[cursor][0] !== ']') {
        items.push(value());
        if (tokens[cursor][0] === ',') cursor++;
      }
      cursor++;
      return { items };
    }
    return { value: JSON.parse(token[0]), start: token.index, end: token.index + token[0].length, quote: '"' };
  }
  return value();
}

function uncomment(value) {
  let quote = null;
  const collection = /^[\[{]/.test(value);
  for (let i = 0; i < value.length; i++) {
    const char = value[i];
    if (quote === '"' && char === '\\') { i++; continue; }
    if (char === quote) {
      if (quote === "'" && value[i + 1] === "'") { i++; continue; }
      quote = null;
    } else if (!quote && (i === 0 || collection) && (char === '"' || char === "'")) quote = char;
    else if (!quote && char === '#' && (i === 0 || /\s/.test(value[i - 1]))) return value.slice(0, i).trimEnd();
  }
  if (quote) throw new Error('Unterminated YAML string; review manually.');
  return value.trimEnd();
}

function scalar(raw, start) {
  let value = raw;
  const quote = raw[0] === '"' || raw[0] === "'" ? raw[0] : '';
  if (quote) {
    if (raw.at(-1) !== quote) throw new Error('Unsupported YAML scalar; review manually.');
    value = quote === '"' ? JSON.parse(raw) : raw.slice(1, -1).replaceAll("''", "'");
  }
  const opaque = !quote && /^[!&*|>\[{]/.test(raw);
  return { value, start, end: start + raw.length, quote, opaque };
}

// Single-line flow collections are common in small SAM templates. Keep their
// spans as well; multiline flow documents are intentionally left for review.
function flow(raw, start) {
  let cursor = 0;
  const space = () => { while (/\s/.test(raw[cursor] || '') && cursor < raw.length) cursor++; };
  function atom(key = false) {
    space();
    const begin = cursor;
    const quote = raw[cursor];
    if (quote === '"' || quote === "'") {
      cursor++;
      while (cursor < raw.length) {
        if (quote === '"' && raw[cursor] === '\\') { cursor += 2; continue; }
        if (raw[cursor++] === quote) {
          if (quote === "'" && raw[cursor] === "'") { cursor++; continue; }
          return scalar(raw.slice(begin, cursor), start + begin);
        }
      }
      throw new Error('Unterminated flow YAML string; review manually.');
    }
    while (cursor < raw.length && !(key ? /[:,{}\[\]]/ : /[,{}\[\]]/).test(raw[cursor])) cursor++;
    const value = raw.slice(begin, cursor).trimEnd();
    if (!value) throw new Error('Unsupported flow YAML value; review manually.');
    return scalar(value, start + begin);
  }
  function value() {
    space();
    const open = raw[cursor];
    if (open !== '{' && open !== '[') return atom();
    cursor++;
    const result = open === '{' ? mapping() : { items: [] };
    const close = open === '{' ? '}' : ']';
    space();
    while (raw[cursor] !== close) {
      if (cursor >= raw.length) throw new Error('Multiline or unterminated flow YAML needs manual review.');
      if (open === '{') {
        const key = atom(true).value;
        space();
        if (raw[cursor++] !== ':' || key === '<<') throw new Error('Unsupported flow YAML mapping; review manually.');
        put(result, key, value());
      } else result.items.push(value());
      space();
      if (raw[cursor] === ',') { cursor++; space(); }
      else if (raw[cursor] !== close) throw new Error('Unsupported flow YAML separator; review manually.');
    }
    cursor++;
    return result;
  }
  const result = value();
  space();
  if (cursor !== raw.length) throw new Error('Unsupported trailing flow YAML; review manually.');
  return result;
}

export function parseYAML(text) {
  if (text.trimStart().startsWith('{')) {
    try { return parseJSON(text); } catch (error) {
      if (text.trim().includes('\n')) throw error;
      return flow(uncomment(text.trim()), text.indexOf('{'));
    }
  }
  const root = mapping();
  const stack = [{ indent: -1, node: root }];
  let offset = 0;
  let opaqueIndent = null;
  let seenDocument = false;
  let seenContent = false;
  for (const line of text.split(/(?<=\n)/)) {
    const body = line.replace(/\r?\n$/, '');
    const start = offset;
    offset += line.length;
    if (!body.trim() || body.trimStart().startsWith('#')) continue;
    if (body === '---') {
      if (seenDocument || seenContent) throw new Error('Multiple YAML documents are not supported; split the templates.');
      seenDocument = true;
      continue;
    }
    if (body === '...') continue;
    seenContent = true;
    const whitespace = body.match(/^\s*/)[0];
    if (whitespace.includes('\t')) throw new Error('YAML tab indentation is not supported; review manually.');
    const indent = whitespace.length;
    if (opaqueIndent !== null && indent > opaqueIndent) continue;
    opaqueIndent = null;
    const item = body.slice(indent).match(/^-(?:\s+|$)(.*)$/);
    if (item) {
      while (stack.at(-1).indent > indent) stack.pop();
      const node = stack.at(-1).node;
      if (node.entries?.size) throw new Error('Mixed YAML mapping and sequence; review manually.');
      node.entries = undefined;
      node.items ??= [];
      // Nested list data is opaque. Literal Transform entries are enough to
      // identify SAM Globals; no runtime edits are made through a sequence.
      node.items.push({ ...scalar(uncomment(item[1]), 0), opaque: true });
      opaqueIndent = indent;
      continue;
    }
    const pair = body.slice(indent).match(/^("(?:\\.|[^"\\])*"|'(?:''|[^'])*'|[^:\s][^:]*?)\s*:(?:\s+|$)(.*)$/);
    if (!pair) throw new Error('Unsupported YAML structure; use block mappings or JSON and review manually.');
    while (stack.at(-1).indent >= indent) stack.pop();
    const parent = stack.at(-1).node;
    const key = scalar(pair[1].trim(), 0).value;
    if (key === '<<') throw new Error('YAML merge keys need manual review; no changes written.');
    const raw = uncomment(pair[2]);
    if (!raw) {
      const node = mapping();
      put(parent, key, node);
      stack.push({ indent, node });
    } else {
      const valueStart = start + body.length - pair[2].length;
      put(parent, key, /^[\[{]/.test(raw) ? flow(raw, valueStart) : scalar(raw, valueStart));
      opaqueIndent = indent; // Never interpret block strings or sequences as configuration.
    }
  }
  return root;
}

function objectAt(node, key) {
  const child = node?.entries?.get(key);
  if (child && !child.entries) throw new Error(`${key} must be an explicit mapping; resolve aliases or expressions manually.`);
  return child;
}

export function runtimeNodes(root, { serverless = false, terraform = false } = {}) {
  const found = [];
  function runtime(node, key) {
    const value = node?.entries?.get(key);
    if (!value) return;
    if (value.opaque || value.entries || value.items || typeof value.value !== 'string') {
      throw new Error(`${key} is not a literal runtime; resolve it manually. No changes written.`);
    }
    found.push(value);
  }
  if (terraform) {
    const resources = objectAt(objectAt(root, 'resource'), 'aws_lambda_function');
    for (const resource of resources?.entries?.values() || []) {
      if (!resource.entries) throw new Error('Terraform resources must be explicit mappings; review manually.');
      runtime(resource, 'runtime');
    }
  } else if (serverless) {
    const provider = objectAt(root, 'provider');
    if (provider?.entries.get('name')?.value !== 'aws') return found;
    runtime(provider, 'runtime');
    const functions = objectAt(root, 'functions');
    for (const fn of functions?.entries?.values() || []) {
      if (!fn.entries) throw new Error('Serverless function definitions must be explicit mappings; review manually.');
      runtime(fn, 'runtime');
    }
  } else {
    const resources = objectAt(root, 'Resources');
    const transform = root.entries?.get('Transform');
    let sam = transform?.value === 'AWS::Serverless-2016-10-31'
      || transform?.items?.some(item => item.value === 'AWS::Serverless-2016-10-31');
    for (const resource of resources?.entries?.values() || []) {
      if (!resource.entries) throw new Error('CloudFormation resources must be explicit mappings; review manually.');
      const type = resource.entries.get('Type');
      if (type?.opaque || type?.entries || type?.items) throw new Error('Resource Type must be a literal string; resolve aliases or expressions manually.');
      if (type?.value === 'AWS::Serverless::Function') sam = true;
      if (['AWS::Lambda::Function', 'AWS::Serverless::Function'].includes(type?.value)) {
        runtime(objectAt(resource, 'Properties'), 'Runtime');
      }
    }
    if (sam) runtime(objectAt(objectAt(root, 'Globals'), 'Function'), 'Runtime');
  }
  return found;
}

export function patchManifest(text, { json = false, from, to, ...options }) {
  const root = json ? parseJSON(text) : parseYAML(text);
  const matches = runtimeNodes(root, options).filter(node => from.includes(node.value) && node.value !== to);
  let changed = text;
  for (const node of [...matches].sort((a, b) => b.start - a.start)) {
    const replacement = node.quote === '"' ? JSON.stringify(to) : node.quote === "'" ? `'${to}'` : to;
    changed = changed.slice(0, node.start) + replacement + changed.slice(node.end);
  }
  return { changed, hits: matches.map(node => node.value) };
}
