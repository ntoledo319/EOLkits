function auditLink(deadline, kit) {
  const params = new URLSearchParams({ source: 'scan', utm_source: 'scan', utm_medium: 'tool', utm_campaign: 'free-scan' });
  if (deadline) params.set('deadline', deadline);
  if (kit) params.set('kit', kit);
  return SITE_BASE + '/audit/?' + params.toString();
}

const SEV_RANK = { critical: 0, high: 1, medium: 2, low: 3 };
const SCOPE_NOTE = 'Configured Lambda runtime and Node/Python dependency patterns in selected files only. No AWS account, deployed behavior, full syntax validation, included requirements files, lockfile resolution, or complete repository analysis.';

function orderedFindings(findings) {
  return [...findings].sort((a, b) => (SEV_RANK[a.severity] - SEV_RANK[b.severity]) ||
    a.file.localeCompare(b.file, 'en') || a.name.localeCompare(b.name, 'en') || (a.lines[0] - b.lines[0]));
}

function findingDetail(finding) {
  if (finding.kind !== 'runtime') return '<p class="finding-change"><code>' + esc(finding.declared) + '</code> <span aria-label="to">→</span> <strong>' + esc(finding.required) + '</strong></p>';
  const prefix = finding.projected ? 'Projected ' : '';
  const dates = [[prefix + 'Deprecation', finding.deprecation], [prefix + 'Create restriction', finding.date], [prefix + 'Update restriction', finding.blockUpdate]];
  return '<dl class="milestones">' + dates.filter(pair => pair[1]).map(pair => '<div><dt>' + esc(pair[0]) + '</dt><dd>' + esc(pair[1]) + '</dd></div>').join('') + '</dl>';
}

function render(all) {
  const box = $('#results');
  const query = $('#finding-search').value.trim().toLowerCase();
  const severity = $('#severity-filter').value;
  const visible = all.filter(f => (!severity || f.severity === severity) && (!query || (f.file + ' ' + f.name).toLowerCase().includes(query)));
  $('#filter-count').textContent = visible.length + ' of ' + all.length + ' findings';
  $('#next-step').hidden = !all.length;
  if (!all.length) {
    const scanned = scanState.files.filter(file => file.status === 'scanned').length;
    const incomplete = scanState.files.some(file => file.status !== 'scanned');
    box.innerHTML = '<div class="empty-result"><h3>' + (scanned ? 'No configured pattern matched' : 'No files were scanned') + '</h3><p>' +
      (scanned ? 'This is a limited source check, not proof that your repository or AWS account is free of migration risk.' : 'Choose a supported, nonempty source file and try again.') +
      (incomplete ? ' Review the file coverage below before drawing conclusions.' : '') + '</p></div>';
    return;
  }
  const rows = visible.map(f => {
    const lines = [...new Set(f.lines)].join(', ');
    const source = f.source && /^https:\/\//.test(f.source) ? '<a href="' + esc(f.source) + '" target="_blank" rel="noopener noreferrer">' + (f.kind === 'runtime' ? 'AWS source' : 'Package reference') + ' ↗</a>' : '';
    const guide = f.guide ? '<a href="' + SITE_BASE + '/migrate/' + encodeURIComponent(f.guide) + '/">Migration timeline →</a>' : '';
    return '<li class="finding"><div class="finding-heading"><span class="severity sev-' + f.severity + '">' + esc(f.severity) + '</span><h3>' + esc(f.name) + '</h3><span class="finding-kind">' + ({ runtime: 'Lambda runtime', native: 'Node dependency', wheel: 'Python dependency' }[f.kind]) + '</span></div>' +
      '<p class="finding-location"><code>' + esc(f.file) + '</code><span>Line' + (f.lines.length === 1 ? '' : 's') + ' ' + esc(lines) + '</span></p>' +
      findingDetail(f) + '<p class="finding-note">' + esc(f.note || '') + '</p><div class="finding-links">' + source + guide + '</div></li>';
  }).join('');
  box.innerHTML = visible.length ? '<ol class="findings">' + rows + '</ol>' : '<div class="empty-result"><h3>No findings match these filters</h3><p>Change the severity or search text to see the other findings. The download always includes all findings.</p></div>';
  const next = $('#next-step');
  next.innerHTML = '<div><h3>Need an archive-wide review artifact?</h3><p>Inspect the optional one-repository evidence report ($299): PDF, evidence fingerprint, remediation order, and explicit scope. Availability is checked before checkout.</p></div>' +
    '<a class="scan-button secondary" href="' + auditLink(null, all[0].kit) + '">See sample and availability →</a>' +
    '<p class="scan-interest"><a href="' + INTEREST_URL + '" target="_blank" rel="noopener noreferrer">Record nonbinding Audit interest on GitHub</a>. This is public; do not include code, secrets, company, or personal information.</p>';
}

const dz = $('#dz'), fi = $('#fi');
let scanState = { files: [], findings: [], label: '', busy: false };
let generation = 0;
let activeReader = null;

function setStatus(message) { $('#scan-status').textContent = message; }

function setBusy(busy) {
  scanState.busy = busy;
  $('#cancel-scan').hidden = !busy;
  $('#download-results').disabled = busy || !scanState.files.length;
  $('#scan-output').setAttribute('aria-busy', String(busy));
}

function renderCoverage() {
  const files = scanState.files;
  $('#file-coverage').innerHTML = files.map(file => '<li><span class="file-state state-' + file.status + '">' + esc(file.status) + '</span><code>' + esc(file.name) + '</code><span>' + esc(file.reason || 'Checked configured patterns') + '</span></li>').join('');
  const total = files.reduce((sum, file) => sum + (file.count || 1), 0);
  const issues = total - files.filter(file => file.status === 'scanned').length;
  $('#coverage-summary').textContent = 'File coverage · ' + total + ' selected' + (issues ? ' · ' + issues + ' need attention' : '');
  $('#coverage').open = issues > 0;
}

function showResults(cancelled = false) {
  scanState.findings = orderedFindings(scanState.findings);
  const scanned = scanState.files.filter(file => file.status === 'scanned').length;
  const total = scanState.files.reduce((sum, file) => sum + (file.count || 1), 0);
  const issues = total - scanned;
  $('#scan-output').hidden = false;
  $('#results-title').textContent = cancelled ? 'Scan cancelled' : issues ? 'Scan incomplete' : 'Scan complete';
  $('#scan-origin').textContent = scanState.label;
  $('#scanned-count').textContent = String(scanned);
  $('#findings-count').textContent = String(scanState.findings.length);
  $('#attention-count').textContent = String(issues);
  $('#finding-controls').hidden = !scanState.findings.length;
  render(scanState.findings);
  renderCoverage();
  setStatus((cancelled ? 'Cancelled. ' : '') + scanned + ' of ' + total + ' files scanned. ' + scanState.findings.length + ' findings. ' + issues + ' files need attention.');
}

function stopReading() {
  generation++;
  if (activeReader && activeReader.readyState === 1) activeReader.abort();
  activeReader = null;
}

function readText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    activeReader = reader;
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new ScanInputError('Could not read this file. Choose it again and retry.'));
    reader.onabort = () => reject(new ScanInputError('Reading cancelled.'));
    reader.readAsText(file, 'UTF-8');
  });
}

async function handle(files, label = 'Your selected files') {
  const selected = [...files];
  if (!selected.length) return;
  stopReading();
  const current = generation;
  scanState = {
    files: selected.slice(0, SCAN_LIMITS.files).map(file => ({ name: file.webkitRelativePath || file.name, bytes: file.size, status: 'pending' })),
    findings: [], label, busy: true
  };
  if (selected.length > SCAN_LIMITS.files) scanState.files.push({ name: (selected.length - SCAN_LIMITS.files) + ' additional files', count: selected.length - SCAN_LIMITS.files, status: 'skipped', reason: 'The limit is 100 files per scan. Scan the remaining files in another batch.' });
  $('#severity-filter').value = '';
  $('#finding-search').value = '';
  $('#scan-output').hidden = true;
  setBusy(true);
  let bytes = 0;
  for (let i = 0; i < Math.min(selected.length, SCAN_LIMITS.files); i++) {
    const file = selected[i], record = scanState.files[i];
    if (!classify(record.name)) {
      record.status = 'skipped'; record.reason = 'Unsupported type. Extract ZIP archives and choose supported source files.';
      continue;
    }
    if (!file.size || file.size > SCAN_LIMITS.fileBytes || bytes + file.size > SCAN_LIMITS.totalBytes) {
      record.status = 'skipped'; record.reason = !file.size ? 'File is empty.' : file.size > SCAN_LIMITS.fileBytes ? 'File exceeds 1 MiB.' : 'Batch exceeds 10 MiB. Scan this file in another batch.';
      continue;
    }
    bytes += file.size;
    setStatus('Scanning file ' + (i + 1) + ' of ' + Math.min(selected.length, SCAN_LIMITS.files) + '…');
    try {
      const content = await readText(file);
      if (current !== generation) return;
      scanState.findings.push(...scanFile(record.name, content));
      record.status = 'scanned';
    } catch (error) {
      if (current !== generation) return;
      record.status = 'failed';
      record.reason = error instanceof ScanInputError ? error.message : 'This file could not be scanned. Check its format and retry.';
    }
    // Give cancel/replacement input a turn between files, even when reads complete quickly.
    await new Promise(resolve => setTimeout(resolve, 0));
    if (current !== generation) return;
  }
  activeReader = null;
  setBusy(false);
  showResults();
  try {
    if (typeof window.eolkitsTrack === 'function') window.eolkitsTrack('scan_completed', { sku: 'audit', meta: { finding_count: scanState.findings.length, file_count: scanState.files.filter(file => file.status === 'scanned').length } });
  } catch { /* Aggregate telemetry must never affect the local result. */ }
}

function reportData() {
  return {
    schema_version: 1, tool: 'EOLkits browser scanner', rules_version: DATA.version,
    input: scanState.label, scope: SCOPE_NOTE,
    selected_file_count: scanState.files.reduce((sum, file) => sum + (file.count || 1), 0),
    scanned_file_count: scanState.files.filter(file => file.status === 'scanned').length,
    complete: !scanState.busy && scanState.files.every(file => file.status === 'scanned'),
    files: scanState.files.map(file => ({ ...file })), findings: scanState.findings.map(finding => ({ ...finding }))
  };
}

dz.addEventListener('dragover', event => { event.preventDefault(); dz.classList.add('over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('over'));
dz.addEventListener('drop', event => { event.preventDefault(); dz.classList.remove('over'); void handle(event.dataTransfer.files); });
$('#choose-files').addEventListener('click', () => fi.click());
fi.addEventListener('change', () => { void handle(fi.files); fi.value = ''; });
$('#severity-filter').addEventListener('change', () => render(scanState.findings));
$('#finding-search').addEventListener('input', () => render(scanState.findings));

$('#paste-form').addEventListener('submit', event => {
  event.preventDefault();
  const content = $('#paste-source').value;
  if (!content.trim()) { setStatus('Paste some source before scanning.'); $('#paste-source').focus(); return; }
  void handle([new File([content], $('#paste-kind').value, { type: 'text/plain' })], 'Pasted source');
});

$('#try-sample').addEventListener('click', () => {
  void handle([
    new File(['Resources:\n  ExampleFunction:\n    Type: AWS::Serverless::Function\n    Properties:\n      Runtime: nodejs20.x\n'], 'example/template.yaml'),
    new File(['{\n  "dependencies": {\n    "node-sass": "^9.0.0",\n    "sharp": "^0.32.0"\n  }\n}\n'], 'example/package.json'),
    new File(['# Fictional example dependencies\nnumpy==1.24.0\n'], 'example/requirements.txt')
  ], 'Fictional example · not your repository');
});

$('#cancel-scan').addEventListener('click', () => {
  stopReading();
  for (const file of scanState.files) if (file.status === 'pending') { file.status = 'cancelled'; file.reason = 'Not scanned. Run this file again to finish the check.'; }
  setBusy(false);
  showResults(true);
});

$('#clear-scan').addEventListener('click', () => {
  stopReading();
  scanState = { files: [], findings: [], label: '', busy: false };
  fi.value = '';
  $('#paste-source').value = '';
  $('#results').replaceChildren();
  $('#file-coverage').replaceChildren();
  $('#next-step').replaceChildren();
  $('#scan-output').hidden = true;
  setBusy(false);
  setStatus('Cleared. Choose files, paste source, or try the example.');
});

$('#download-results').addEventListener('click', () => {
  if (scanState.busy || !scanState.files.length) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(reportData(), null, 2) + '\n'], { type: 'application/json' }));
  const link = document.createElement('a');
  link.href = url; link.download = 'eolkits-findings.json';
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  setStatus('Downloaded the complete local scan result, including file coverage and all findings.');
});
