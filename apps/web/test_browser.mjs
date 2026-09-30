/** Real Chromium smoke test. No npm dependencies, uploads, or external services.
 * Run from the repository root: node apps/web/test_browser.mjs
 * EOLKITS_CHROME selects an installed Chrome/Chromium executable on PATH.
 * Artifacts and the isolated browser profile stay under the repository's tmp/.
 */
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { mkdir, mkdtemp, readFile, realpath, rm, stat, writeFile } from 'node:fs/promises';
import { dirname, extname, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = await realpath(resolve(dirname(fileURLToPath(import.meta.url)), '../..'));
assert.equal(await realpath(process.cwd()), root, 'Run the browser check from the repository root');
const docs = await realpath(join(root, 'docs'));
const tmp = join(root, 'tmp');
await mkdir(tmp, { recursive: true });
assert.equal(await realpath(tmp), tmp, 'Temporary directory must not redirect outside the repository');
const session = await mkdtemp(join(tmp, 'browser-check-'));
const artifacts = join(tmp, 'product-improvement/browser');
await mkdir(artifacts, { recursive: true });
assert.equal(await realpath(artifacts), artifacts);
const failures = [], traffic = [];
let browser, socket, sequence = 0;
const pending = new Map();
let onProtocolEvent = () => {};

const server = createServer(async (request, response) => {
  try {
    const url = new URL(request.url, 'http://localhost');
    if (url.pathname === '/favicon.ico') { response.writeHead(204); response.end(); return; }
    const relative = decodeURIComponent(url.pathname).replace(/^\/EOLkits(?=\/|$)/, '');
    let path = resolve(docs, '.' + relative);
    assert.ok(path.startsWith(docs + sep) || path === docs);
    if ((await stat(path)).isDirectory()) path = join(path, 'index.html');
    const actual = await realpath(path);
    assert.ok(actual.startsWith(docs + sep));
    const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.json': 'application/json' };
    response.writeHead(200, { 'Content-Type': types[extname(actual)] || 'application/octet-stream' });
    response.end(await readFile(actual));
  } catch { response.writeHead(404); response.end('Not found'); }
});

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function waitFor(predicate, description) {
  const deadline = Date.now() + 15000;
  while (Date.now() < deadline) {
    if (await predicate()) return;
    await delay(30);
  }
  throw new Error('Timed out: ' + description);
}
function cdp(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error('Protocol timeout: ' + method)); }, 15000);
    pending.set(id, { resolve, reject, timer });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const result = await cdp('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
async function complete() {
  await waitFor(() => evaluate('!scanState.busy && !document.querySelector("#scan-output").hidden'), 'scan completes');
}
async function screenshot(name, width, height) {
  await cdp('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: width < 600 });
  await evaluate('window.scrollTo(0, 0)');
  assert.ok(await evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'No horizontal overflow at ' + width);
  const metrics = await cdp('Page.getLayoutMetrics');
  const result = await cdp('Page.captureScreenshot', {
    format: 'png', captureBeyondViewport: true,
    clip: { x: 0, y: 0, width, height: Math.ceil(metrics.cssContentSize.height), scale: 1 }
  });
  await writeFile(join(artifacts, name + '.png'), Buffer.from(result.data, 'base64'));
}

try {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = 'http://127.0.0.1:' + server.address().port;
  const profile = join(session, 'profile');
  browser = spawn(process.env.EOLKITS_CHROME || 'google-chrome', [
    '--headless=new', '--disable-gpu', '--disable-dev-shm-usage', '--no-first-run',
    '--no-default-browser-check', '--disable-background-networking', '--disable-component-update',
    '--disable-extensions', '--disable-sync', '--disable-default-apps', '--metrics-recording-only',
    '--password-store=basic', '--use-mock-keychain', '--remote-debugging-port=0',
    '--user-data-dir=' + profile, '--disk-cache-dir=' + join(session, 'cache'), 'about:blank'
  ], {
    cwd: root, stdio: ['pipe', 'pipe', 'pipe'],
    env: { ...process.env, TMPDIR: session, XDG_CONFIG_HOME: join(session, 'config'), XDG_CACHE_HOME: join(session, 'cache') }
  });
  browser.stdin.end();
  let browserError = '', launchError = null;
  browser.on('error', error => { launchError = error; });
  browser.stdout.on('data', () => {});
  browser.stderr.on('data', bytes => { browserError = (browserError + bytes.toString()).slice(-3000); });
  let debugPort;
  await waitFor(async () => {
    if (launchError) throw launchError;
    if (browser.exitCode !== null) throw new Error('Chrome exited: ' + browserError);
    try { debugPort = (await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]; return true; }
    catch { return false; }
  }, 'isolated Chrome starts').catch(async error => {
    await writeFile(join(artifacts, 'chrome-startup.log'), browserError);
    throw new Error(error.message + '\n' + browserError);
  });
  const targets = await (await fetch('http://127.0.0.1:' + debugPort + '/json/list')).json();
  socket = new WebSocket(targets.find(target => target.type === 'page').webSocketDebuggerUrl);
  socket.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.id) {
      const task = pending.get(message.id);
      if (!task) return;
      pending.delete(message.id); clearTimeout(task.timer);
      if (message.error) task.reject(new Error(JSON.stringify(message.error)));
      else task.resolve(message.result);
    } else onProtocolEvent(message);
  });
  await new Promise((resolve, reject) => { socket.addEventListener('open', resolve, { once: true }); socket.addEventListener('error', reject, { once: true }); });
  onProtocolEvent = message => {
    if (message.method === 'Runtime.exceptionThrown') failures.push(message.params.exceptionDetails);
    if (message.method === 'Fetch.requestPaused') {
      const { requestId, request } = message.params;
      traffic.push({ url: request.url, body: request.postData || '' });
      const local = request.url.startsWith(origin + '/');
      void cdp(local ? 'Fetch.continueRequest' : 'Fetch.fulfillRequest', local ? { requestId } : { requestId, responseCode: 404, body: '' }).catch(error => failures.push(error.message));
    }
  };
  await cdp('Runtime.enable');
  await cdp('Page.enable');
  await cdp('Fetch.enable', { patterns: [{ urlPattern: '*' }] });
  await cdp('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  await cdp('Page.navigate', { url: origin + '/EOLkits/scan/' });
  await waitFor(() => evaluate('typeof handle === "function"'), 'scanner initializes');
  await screenshot('desktop-empty', 1280, 900);

  // A real keyboard event invokes the example button; no simulated scan result.
  await cdp('Page.bringToFront');
  await evaluate('document.querySelector("#try-sample").focus()');
  assert.equal(await evaluate('document.activeElement.id'), 'try-sample');
  await cdp('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', text: '\r', unmodifiedText: '\r', windowsVirtualKeyCode: 13 });
  await cdp('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
  await complete();
  const sample = await evaluate('reportData()');
  assert.equal(sample.complete, true);
  assert.equal(sample.files.length, 3);
  assert.equal(sample.findings.length, 4);
  assert.equal(sample.findings[0].severity, 'critical');
  assert.match(sample.input, /Fictional/);
  assert.ok(sample.findings.every(finding => finding.lines.length && finding.source.startsWith('https://')));
  await screenshot('desktop-results', 1280, 900);
  await screenshot('mobile-results', 390, 844);
  await screenshot('mobile-narrow', 320, 700);

  await evaluate('document.querySelector("#severity-filter").value="critical"; document.querySelector("#severity-filter").dispatchEvent(new Event("change"))');
  assert.equal(await evaluate('document.querySelectorAll(".finding").length'), 1);
  await evaluate('document.querySelector("#finding-search").value="no-such-file"; document.querySelector("#finding-search").dispatchEvent(new Event("input"))');
  assert.match(await evaluate('document.querySelector("#results").textContent'), /No findings match/);

  const downloads = join(artifacts, 'downloads');
  await mkdir(downloads, { recursive: true });
  const downloadPath = join(downloads, 'eolkits-findings.json');
  await rm(downloadPath, { force: true });
  await cdp('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: downloads });
  await evaluate('document.querySelector("#download-results").click()');
  await waitFor(async () => { try { return JSON.parse(await readFile(downloadPath, 'utf8')).findings.length === 4; } catch { return false; } }, 'real local JSON download');
  const downloaded = JSON.parse(await readFile(downloadPath, 'utf8'));
  assert.deepEqual(downloaded, sample, 'Download includes all findings regardless of filters');
  assert.ok(!JSON.stringify(downloaded).includes('Resources:\\n'), 'No source contents in the exported evidence');

  // Browser file-picker path with a genuine local file, including a filename hostile to HTML.
  const filename = 'private-<img onerror=alert(1)>.yaml';
  const fixture = join(session, filename);
  await writeFile(fixture, 'Resources:\n  Fn:\n    Type: AWS::Lambda::Function\n    Properties:\n      Runtime: python3.9\n');
  const document = await cdp('DOM.getDocument');
  const input = await cdp('DOM.querySelector', { nodeId: document.root.nodeId, selector: '#fi' });
  await cdp('DOM.setFileInputFiles', { nodeId: input.nodeId, files: [fixture] });
  await complete();
  assert.equal(await evaluate('reportData().findings[0].file'), filename);
  assert.equal(await evaluate('document.querySelectorAll("#results img").length'), 0);

  await evaluate('window.tracked=[]; window.eolkitsTrack=(name,payload)=>window.tracked.push({name,payload}); document.querySelector(".paste-panel").open=true; document.querySelector("#paste-kind").value="package.json"; document.querySelector("#paste-source").value=\'{"dependencies":{"sharp":"0.32.0",}\'; document.querySelector("#paste-form").requestSubmit()');
  await complete();
  assert.equal(await evaluate('reportData().complete'), false);
  assert.match(await evaluate('document.querySelector("#file-coverage").textContent'), /Invalid JSON/);
  assert.equal(await evaluate('document.querySelector("#results-title").textContent'), 'Scan incomplete');
  await screenshot('mobile-input-error', 390, 844);
  await evaluate('document.querySelector("#paste-source").value=\'{"dependencies":{"sharp":"0.32.0"}}\'; document.querySelector("#paste-form").requestSubmit()');
  await complete();
  assert.equal(await evaluate('reportData().findings.length'), 1);
  assert.equal(await evaluate('reportData().complete'), true);
  const tracked = await evaluate('window.tracked');
  assert.ok(tracked.length >= 2);
  assert.ok(tracked.every(item => JSON.stringify(item).match(/^\{"name":"scan_completed","payload":\{"sku":"audit","meta":\{"finding_count":\d+,"file_count":\d+\}\}\}$/)));

  // Unsupported, oversized, empty and unreadable input never qualifies as scanned.
  await evaluate('handle([new File(["PK"],"archive.zip"),new File(["x".repeat(1048577)],"big.yaml"),new File([],"empty.yaml"),new File(["\\u0000"],"binary.yaml")])');
  await complete();
  assert.equal(await evaluate('reportData().files.filter(f=>f.status==="scanned").length'), 0);
  assert.equal(await evaluate('reportData().complete'), false);
  assert.match(await evaluate('document.querySelector("#results").textContent'), /No files were scanned/);
  await evaluate('handle(Array.from({length: 103}, (_, i) => new File(["Settings: {}"], "selected-" + i + ".yaml")))');
  await complete();
  assert.equal(await evaluate('reportData().selected_file_count'), 103);
  assert.equal(await evaluate('reportData().scanned_file_count'), 100);
  assert.equal(await evaluate('document.querySelector("#attention-count").textContent'), '3');
  assert.equal(await evaluate('reportData().complete'), false);
  await evaluate('handle(Array.from({length: 11}, (_, i) => new File(["#" + "x".repeat(1048575)], "limit-" + i + ".yaml")))');
  await complete();
  assert.equal(await evaluate('reportData().scanned_file_count'), 10);
  assert.match(await evaluate('reportData().files[10].reason'), /10 MiB/);
  assert.equal(await evaluate('reportData().complete'), false);
  await evaluate('window.RealFileReader=FileReader; window.FileReader=class {readAsText(){this.readyState=2; queueMicrotask(()=>this.onerror());}}; handle([new File(["hello"],"unreadable.yaml")])');
  await complete();
  assert.match(await evaluate('reportData().files[0].reason'), /Could not read/);
  await evaluate('window.FileReader=window.RealFileReader');

  // Late completion from a superseded batch cannot overwrite the current result.
  await evaluate(`window.lateReads=[]; window.FileReader=class {
    constructor(){this.readyState=0;}
    readAsText(){this.readyState=1; window.lateReads.push(this);}
    abort(){this.readyState=2; this.onabort();}
  }; void handle([new File(['old'],'old.yaml')]);`);
  await evaluate('window.FileReader=window.RealFileReader; handle([new File(["Settings: {}"],"new.yaml")])');
  await complete();
  await evaluate('window.lateReads[0].result="Resources:\\n  Fn:\\n    Type: AWS::Lambda::Function\\n    Properties:\\n      Runtime: python3.9"; window.lateReads[0].onload()');
  assert.deepEqual(await evaluate('reportData().files.map(f=>f.name)'), ['new.yaml']);
  assert.equal(await evaluate('reportData().findings.length'), 0);
  assert.match(await evaluate('document.querySelector("#results").textContent'), /not proof/);

  await evaluate('window.FileReader=class {readAsText(){this.readyState=1;} abort(){this.readyState=2;this.onabort();}}; void handle([new File(["pending"],"pending.yaml")]); document.querySelector("#cancel-scan").click(); window.FileReader=window.RealFileReader');
  await complete();
  assert.equal(await evaluate('reportData().complete'), false);
  assert.equal(await evaluate('reportData().files[0].status'), 'cancelled');
  await evaluate('document.querySelector("#clear-scan").click()');
  assert.equal(await evaluate('document.querySelector("#scan-output").hidden'), true);
  assert.equal(await evaluate('document.querySelector("#paste-source").value'), '');
  assert.deepEqual(await evaluate('reportData().files'), []);

  assert.equal(failures.length, 0, JSON.stringify(failures));
  assert.ok(traffic.every(request => !request.url.includes('private-') && !request.body.includes('sharp') && !request.body.includes('Runtime')), 'HTTP requests must never contain scanned filenames or source');
  await writeFile(join(artifacts, 'verification.json'), JSON.stringify({
    result: 'passed', screens: [1280, 390, 320], sampleFiles: sample.files.length, sampleFindings: sample.findings.length,
    runtimeErrors: failures.length, localDownload: 'downloads/eolkits-findings.json',
    checks: ['keyboard example', 'exact locations', 'severity/search', 'full export', 'file picker', 'HTML escaping', 'paste failure/recovery', 'aggregate-only telemetry', 'unsupported/empty/size/binary limits', 'read failure', 'batch replacement', 'cancellation', 'clear', 'no HTTP source leakage']
  }, null, 2) + '\n');
  console.log('BROWSER_VERIFIED: Chromium workflows, responsive screenshots, local download and failure recovery passed');
} catch (error) {
  if (socket?.readyState === WebSocket.OPEN) {
    const state = await evaluate('({status:document.querySelector("#scan-status")?.textContent, active:document.activeElement?.id, state:typeof scanState === "undefined" ? null : scanState})').catch(() => null);
    await writeFile(join(artifacts, 'failure.json'), JSON.stringify({ error: error.message, failures, state }, null, 2));
    console.error(JSON.stringify({ error: error.message, failures, state }).slice(0, 5000));
  }
  throw error;
} finally {
  if (socket?.readyState === WebSocket.OPEN) socket.close();
  for (const task of pending.values()) clearTimeout(task.timer);
  if (browser && browser.exitCode === null) {
    browser.kill('SIGTERM');
    await Promise.race([new Promise(resolve => browser.once('exit', resolve)), delay(3000)]);
    if (browser.exitCode === null) browser.kill('SIGKILL');
  }
  server.closeAllConnections();
  await new Promise(resolve => server.close(resolve));
  await rm(session, { recursive: true, force: true, maxRetries: 3, retryDelay: 100 });
}
