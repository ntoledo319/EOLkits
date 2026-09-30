const assert = require('node:assert/strict');
const path = require('node:path');
const Module = require('node:module');

// This host double activates the real extension and observes public VS Code surfaces.
// No files, network, extension host download, or third-party test dependency is needed.
class Emitter {
  listeners = new Set();
  event = (listener, thisArg, disposables) => {
    const callback = value => listener.call(thisArg, value);
    this.listeners.add(callback);
    const disposable = { dispose: () => this.listeners.delete(callback) };
    disposables?.push(disposable);
    return disposable;
  };
  fire(value) { for (const listener of [...this.listeners]) listener(value); }
  dispose() { this.listeners.clear(); }
}
class Uri {
  constructor(scheme, authority, uriPath) { Object.assign(this, { scheme, authority, path: uriPath, fsPath: uriPath }); }
  static file(file) { return new Uri('file', '', file); }
  static parse(value) { const url = new URL(value); return new Uri(url.protocol.slice(0, -1), url.host, decodeURIComponent(url.pathname)); }
  toString() { return `${this.scheme}://${this.authority}${this.path}`; }
}
class Position { constructor(line, character) { Object.assign(this, { line, character }); } }
class Range {
  constructor(a, b, c, d) {
    this.start = typeof a === 'number' ? new Position(a, b) : a;
    this.end = typeof a === 'number' ? new Position(c, d) : b;
  }
}
class CancellationTokenSource {
  emitter = new Emitter();
  token = { isCancellationRequested: false, onCancellationRequested: this.emitter.event };
  cancel() { if (!this.token.isCancellationRequested) { this.token.isCancellationRequested = true; this.emitter.fire(); } }
  dispose() { this.emitter.dispose(); }
}
const tick = () => new Promise(resolve => setImmediate(resolve));
async function until(predicate) {
  for (let attempt = 0; attempt < 50; attempt++) { if (predicate()) return; await tick(); }
  assert.fail('Expected asynchronous host operation did not start');
}
async function promptly(operation) {
  let timeout;
  try {
    return await Promise.race([operation, new Promise((_, reject) => {
      timeout = setTimeout(() => reject(new Error('Cancellation waited for an unresponsive file provider')), 1000);
    })]);
  } finally { clearTimeout(timeout); }
}
function deferred() {
  let resolve;
  const promise = new Promise(fulfil => { resolve = fulfil; });
  return { promise, resolve };
}
const fixtureRoot = path.resolve(__dirname, 'virtual-workspace');
const file = (relative) => Uri.file(path.join(fixtureRoot, relative));
const oldRuntime = 'Resources:\n  Function:\n    Runtime: nodejs18.x\n';
const cleanRuntime = 'Resources:\n  Function:\n    Runtime: nodejs24.x\n';
function document(uri, text, languageId = 'yaml') {
  return {
    uri, fileName: uri.fsPath, languageId, getText: () => text,
    positionAt: index => { const lines = text.slice(0, index).split('\n'); return new Position(lines.length - 1, lines.at(-1).length); },
    lineAt: line => ({ text: text.split('\n')[line] || '' })
  };
}
function createHost(initial = []) {
  const host = {
    files: new Map(initial.map(doc => [doc.uri.toString(), doc])),
    roots: [file('one'), file('two')], commands: new Map(), contexts: new Map(), diagnostics: new Map(),
    settings: { eolkits: {}, rupture: {} }, scoped: new Map(), events: {},
    panels: [], notifications: [], progresses: [], jobs: [], opens: [], finds: [], external: [], changes: 0,
    subscriptions: [],
  };
  for (const name of ['save', 'change', 'delete', 'rename', 'folders', 'configuration', 'watchCreate', 'watchChange', 'watchDelete']) host.events[name] = new Emitter();
  const workspaceFolder = uri => host.roots.find(root => root.scheme === uri.scheme && root.authority === uri.authority && (uri.path === root.path || uri.path.startsWith(root.path + '/')));
  const api = {
    Uri, Position, Range, EventEmitter: Emitter, CancellationTokenSource,
    ProgressLocation: { Notification: 15 }, ViewColumn: { One: 1 },
    TreeItemCollapsibleState: { None: 0, Collapsed: 1 }, DiagnosticSeverity: { Error: 0, Warning: 1, Information: 2 },
    Diagnostic: class { constructor(range, message, severity) { Object.assign(this, { range, message, severity }); } },
    ThemeIcon: class { constructor(id) { this.id = id; } },
    TreeItem: class { constructor(label, collapsibleState) { Object.assign(this, { label, collapsibleState }); } },
    RelativePattern: class { constructor(baseUri, pattern) { Object.assign(this, { baseUri, pattern }); } },
    env: { openExternal: async uri => { host.external.push(uri); return true; } },
    languages: { createDiagnosticCollection: () => {
      let disposed = false;
      return {
        set: (uri, values) => { assert.equal(disposed, false, 'Disposed diagnostics received stale results'); host.diagnostics.set(uri.toString(), values); },
        delete: uri => host.diagnostics.delete(uri.toString()),
        dispose: () => { disposed = true; host.diagnostics.clear(); },
      };
    } },
    commands: {
      registerCommand: (name, callback) => { host.commands.set(name, callback); return { dispose: () => host.commands.delete(name) }; },
      executeCommand: async (name, ...args) => {
        if (name === 'setContext') { host.contexts.set(args[0], args[1]); host.changes++; return; }
        assert.ok(host.commands.has(name), `Missing command ${name}`);
        return host.commands.get(name)(...args);
      },
    },
    window: {
      registerTreeDataProvider: (name, tree) => { assert.equal(name, 'eolkits.deprecations'); host.tree = tree; return { dispose() {} }; },
      withProgress: (options, callback) => {
        const tokenSource = new CancellationTokenSource();
        const progress = { options, tokenSource, reports: [] };
        host.progresses.push(progress);
        const job = Promise.resolve().then(() => callback({ report: value => progress.reports.push(value) }, tokenSource.token));
        host.jobs.push(job);
        return job;
      },
      showWarningMessage: async (message, ...actions) => { host.notifications.push({ kind: 'warning', message, actions }); },
      showInformationMessage: async message => { host.notifications.push({ kind: 'information', message }); },
      createWebviewPanel: () => {
        const disposed = new Emitter();
        const panel = { webview: { html: '' }, reveal() { this.revealed = true; }, onDidDispose: disposed.event, dispose: () => disposed.fire() };
        host.panels.push(panel);
        return panel;
      },
    },
    workspace: {
      getWorkspaceFolder: uri => { const root = workspaceFolder(uri); return root && { uri: root }; },
      asRelativePath: uri => uri.path.slice(fixtureRoot.length + 1),
      getConfiguration: (namespace, uri) => {
        const values = { ...host.settings[namespace], ...host.scoped.get(`${namespace}:${workspaceFolder(uri)?.toString()}`) };
        return {
          get: (key, fallback) => values[key] === undefined ? fallback : values[key],
          inspect: key => values[key] === undefined ? undefined : { workspaceValue: values[key] },
        };
      },
      findFiles: async (include, exclude, limit, token) => {
        host.finds.push({ include, exclude, limit, token });
        if (host.findOverride) return host.findOverride(include);
        return [...host.files.values()].map(doc => doc.uri).filter(uri => workspaceFolder(uri) &&
          /\.(yaml|yml|json|jsonc|tf|hcl|js|jsx|ts|tsx|py)$/.test(uri.path) && !uri.path.split('/').includes('node_modules') &&
          (typeof include === 'string' || uri.path.startsWith(include.baseUri.path + '/')));
      },
      openTextDocument: async uri => {
        host.opens.push(uri);
        if (host.openOverride) return host.openOverride(uri);
        const doc = host.files.get(uri.toString());
        if (!doc || doc.error) throw new Error('Host file unavailable');
        return doc;
      },
      onDidSaveTextDocument: host.events.save.event,
      onDidChangeTextDocument: host.events.change.event,
      onDidDeleteFiles: host.events.delete.event,
      onDidRenameFiles: host.events.rename.event,
      onDidChangeWorkspaceFolders: host.events.folders.event,
      onDidChangeConfiguration: host.events.configuration.event,
      createFileSystemWatcher: () => ({
        onDidCreate: host.events.watchCreate.event, onDidChange: host.events.watchChange.event,
        onDidDelete: host.events.watchDelete.event, dispose() {},
      }),
    },
  };
  host.api = api;
  host.flush = async () => {
    let count;
    do { count = host.jobs.length; await Promise.all(host.jobs); await tick(); } while (count !== host.jobs.length);
  };
  host.execute = api.commands.executeCommand;
  host.save = doc => { host.files.set(doc.uri.toString(), doc); host.events.save.fire(doc); };
  host.configure = key => host.events.configuration.fire({ affectsConfiguration: name => name === key });
  host.dispose = () => { host.extension.deactivate(); for (const disposable of host.subscriptions) disposable.dispose(); };
  const originalLoad = Module._load;
  const outputRoot = path.resolve(__dirname, '../out') + path.sep;
  for (const cacheKey of Object.keys(require.cache)) if (cacheKey.startsWith(outputRoot)) delete require.cache[cacheKey];
  Module._load = function (name, ...args) { return name === 'vscode' ? api : originalLoad.call(this, name, ...args); };
  try { host.extension = require('../out/extension.js'); } finally { Module._load = originalLoad; }
  host.extension.activate({ subscriptions: host.subscriptions });
  return host;
}
async function treeFindings(host) {
  const roots = await host.tree.getChildren();
  const children = await Promise.all(roots.filter(item => ['critical', 'high', 'medium', 'low'].includes(item.type)).map(item => host.tree.getChildren(item)));
  return children.flat();
}
async function assertViews(host, count) {
  assert.equal([...host.diagnostics.values()].flat().length, count, 'Problems panel count');
  assert.equal((await treeFindings(host)).length, count, 'Explorer tree count');
  assert.equal(host.contexts.get('eolkits.hasDeprecations'), count > 0, 'Command context');
  if (host.panels.length) assert.match(host.panels.at(-1).webview.html, new RegExp(`<h2>${count} potential issue`), 'Open report count');
}

async function main() {
  const a = file('one/main.yaml');
  const b = file('two/main.yaml');
  {
    const host = createHost([document(a, oldRuntime), document(b, oldRuntime)]);
    await host.flush();
    for (const name of ['eolkits', 'rupture']) for (const command of ['scanWorkspace', 'showReport', 'getAudit']) assert.ok(host.commands.has(`${name}.${command}`));
    await host.execute('rupture.showReport');
    await assertViews(host, 2);
    host.save(document(a, cleanRuntime));
    await assertViews(host, 1);
    assert.match(host.panels[0].webview.html, /2 scanned, 0 unreadable/);
    const editing = document(b, cleanRuntime);
    host.events.change.fire({ document: editing, contentChanges: [{ text: cleanRuntime }] });
    await assertViews(host, 0);
    assert.match(host.panels[0].webview.html, /Scan incomplete.*1 pending/);
    host.save(editing);
    await assertViews(host, 0);
    assert.match(host.panels[0].webview.html, /2 scanned, 0 unreadable, 0 skipped, 0 pending/);
    await host.execute('eolkits.showReport');
    assert.equal(host.panels.length, 1, 'Report command reuses the live panel');
    await host.execute('rupture.getAudit');
    assert.equal(host.external[0].scheme, 'https');
    assert.equal(host.external.length, 1, 'Only the explicit audit command opens a URL');
    host.dispose();
  }
  {
    const host = createHost([document(a, oldRuntime), document(b, oldRuntime)]);
    await host.flush();
    await host.execute('eolkits.showReport');
    host.files.set(a.toString(), document(a, cleanRuntime));
    host.files.set(b.toString(), document(b, cleanRuntime));
    host.findOverride = async () => [a, b];
    await host.execute('rupture.scanWorkspace', file('one'));
    await assertViews(host, 1);
    assert.equal((await treeFindings(host))[0].command.arguments[0].toString(), b.toString(), 'Folder scan preserves unrelated results');
    assert.match(host.panels[0].webview.html, /Latest scan scope: one/);
    assert.equal(host.finds.at(-1).exclude, '**/node_modules/**');
    const increments = host.progresses[0].reports.reduce((total, report) => total + (report.increment || 0), 0);
    assert.ok(Math.abs(increments - 100) < 0.001, 'Progress advances once per file and ends at 100%');
    host.files.delete(b.toString());
    host.events.watchDelete.fire(b);
    await assertViews(host, 0);
    host.save(document(file('one/node_modules/dep/index.yaml'), oldRuntime));
    await assertViews(host, 0);
    host.dispose();
  }
  {
    const js = file('two/sdk.js');
    const host = createHost([document(a, oldRuntime), document(js, "import AWS from 'aws-sdk';", 'javascript')]);
    host.settings.rupture = { severityThreshold: 'high', autoScan: false };
    await host.flush();
    await host.execute('eolkits.showReport');
    await assertViews(host, 1);
    host.save(document(a, cleanRuntime));
    await assertViews(host, 0);
    assert.match(host.panels[0].webview.html, /Scan incomplete/);
    host.events.watchChange.fire(js);
    await assertViews(host, 0);
    assert.match(host.panels[0].webview.html, /2 pending/, 'External changes remain visibly pending when auto-scan is disabled');
    host.settings.eolkits = { autoScan: true, severityThreshold: 'medium' };
    host.configure('eolkits.severityThreshold');
    await host.flush();
    await assertViews(host, 1);
    host.save(document(a, oldRuntime));
    await assertViews(host, 2);
    host.settings.eolkits.enabledKits = ['python-pivot'];
    host.configure('eolkits.enabledKits');
    await host.flush();
    await assertViews(host, 0);
    assert.doesNotMatch(host.panels[0].webview.html, /Scan incomplete/);
    host.settings.eolkits.enabledKits = ['lambda-lifeline'];
    host.scoped.set(`eolkits:${file('two')}`, { severityThreshold: 'critical' });
    host.configure('eolkits.enabledKits');
    await host.flush();
    await assertViews(host, 1);
    host.dispose();
  }
  {
    const host = createHost([document(a, cleanRuntime), { uri: b, error: true }]);
    await host.flush();
    await host.execute('eolkits.showReport');
    await host.execute('eolkits.scanWorkspace');
    await assertViews(host, 0);
    assert.match(host.notifications.at(-1).message, /Scan incomplete.*1 unreadable/);
    assert.equal(host.notifications.at(-1).kind, 'warning');
    assert.match(host.panels[0].webview.html, /two\/main.yaml.*could not be opened/);
    const errorGroup = (await host.tree.getChildren()).find(item => item.type === 'errors');
    assert.equal((await host.tree.getChildren(errorGroup))[0].command.arguments[0].toString(), b.toString());
    host.files.set(b.toString(), document(b, oldRuntime));
    host.events.watchCreate.fire(b);
    await host.flush();
    await assertViews(host, 1);
    assert.doesNotMatch(host.panels[0].webview.html, /Scan incomplete/);
    host.dispose();
  }
  {
    const host = createHost([document(a, oldRuntime), document(b, oldRuntime)]);
    await host.flush();
    await host.execute('eolkits.showReport');
    const blocked = deferred();
    const opens = host.opens.length;
    host.openOverride = () => blocked.promise;
    const scan = host.execute('eolkits.scanWorkspace');
    await until(() => host.opens.length > opens);
    assert.equal(host.progresses.at(-1).options.cancellable, true);
    host.progresses.at(-1).tokenSource.cancel();
    await promptly(scan);
    await assertViews(host, 0);
    assert.match(host.notifications.at(-1).message, /Scan cancelled.*2 pending/);
    assert.match(host.panels[0].webview.html, /Scan cancelled/);
    blocked.resolve(document(a, oldRuntime));
    delete host.openOverride;
    await host.execute('eolkits.scanWorkspace');
    await assertViews(host, 2);
    assert.doesNotMatch(host.panels[0].webview.html, /Scan cancelled|Scan incomplete/);
    host.dispose();
  }
  {
    const host = createHost([document(a, oldRuntime)]);
    await host.flush();
    const blocked = deferred();
    host.findOverride = () => blocked.promise;
    const scan = host.execute('eolkits.scanWorkspace');
    await tick();
    host.progresses.at(-1).tokenSource.cancel();
    await promptly(scan);
    await assertViews(host, 0);
    assert.match(host.notifications.at(-1).message, /Scan cancelled/);
    blocked.resolve([a]);
    await tick();
    await assertViews(host, 0);
    host.dispose();
  }
  {
    const host = createHost([document(a, oldRuntime)]);
    await host.flush();
    await host.execute('eolkits.showReport');
    host.findOverride = async () => { throw new Error('Discovery failed'); };
    await host.execute('eolkits.scanWorkspace');
    await assertViews(host, 0);
    assert.match(host.panels[0].webview.html, /Could not discover files in workspace/);
    assert.equal(host.notifications.at(-1).kind, 'warning');
    delete host.findOverride;
    await host.execute('eolkits.scanWorkspace', file('one'));
    await assertViews(host, 1);
    assert.match(host.panels[0].webview.html, /Scan incomplete/,'A folder retry cannot certify failed workspace discovery');
    await host.execute('eolkits.scanWorkspace');
    assert.doesNotMatch(host.panels[0].webview.html, /Scan incomplete/);
    host.dispose();
  }
  for (const event of ['save', 'edit', 'delete', 'supersede', 'dispose']) {
    const host = createHost([document(a, oldRuntime)]);
    await host.flush();
    await host.execute('eolkits.showReport');
    const blocked = deferred();
    const opens = host.opens.length;
    let first = true;
    host.openOverride = uri => {
      if (first) { first = false; return blocked.promise; }
      return Promise.resolve(host.files.get(uri.toString()));
    };
    const scan = host.execute('eolkits.scanWorkspace');
    await until(() => host.opens.length > opens);
    if (event === 'save') host.save(document(a, cleanRuntime));
    if (event === 'edit') host.events.change.fire({ document: document(a, cleanRuntime), contentChanges: [{ text: cleanRuntime }] });
    if (event === 'delete') { host.files.delete(a.toString()); host.events.delete.fire({ files: [a] }); }
    if (event === 'supersede') {
      host.files.set(a.toString(), document(a, cleanRuntime));
      await host.execute('eolkits.scanWorkspace');
    }
    if (event === 'dispose') host.dispose();
    const changes = host.changes;
    blocked.resolve(document(a, oldRuntime));
    await scan;
    if (event === 'dispose') { assert.equal(host.changes, changes, 'Disposed scan did not update views'); continue; }
    await assertViews(host, 0);
    if (event === 'edit') assert.match(host.panels[0].webview.html, /Scan incomplete.*1 pending/);
    if (event === 'delete') assert.match(host.panels[0].webview.html, /Scan cancelled/);
    if (event === 'supersede') assert.doesNotMatch(host.panels[0].webview.html, /Scan cancelled|Scan incomplete/);
    host.dispose();
  }
  {
    const host = createHost([document(a, oldRuntime)]);
    await host.flush();
    const blocked = deferred();
    host.findOverride = () => blocked.promise;
    const scan = host.execute('eolkits.scanWorkspace');
    await tick();
    host.save(document(a, cleanRuntime));
    blocked.resolve([a]);
    await scan;
    await assertViews(host, 0);
    host.dispose();
  }
  {
    const host = createHost([document(a, oldRuntime)]);
    await host.flush();
    await host.execute('eolkits.showReport');
    const blocked = deferred();
    host.openOverride = () => blocked.promise;
    host.events.watchChange.fire(a);
    await tick();
    host.save(document(a, cleanRuntime));
    blocked.resolve(document(a, oldRuntime));
    await host.flush();
    await assertViews(host, 0);
    assert.doesNotMatch(host.panels[0].webview.html, /Scan incomplete/);
    host.dispose();
  }
  {
    const host = createHost([document(a, oldRuntime), document(b, oldRuntime)]);
    await host.flush();
    const renamed = file('one/renamed.yaml');
    host.files.delete(a.toString());
    host.files.set(renamed.toString(), document(renamed, oldRuntime));
    host.events.rename.fire({ files: [{ oldUri: a, newUri: renamed }] });
    await host.flush();
    await assertViews(host, 2);
    assert.equal(host.diagnostics.has(a.toString()), false);
    host.roots = [file('one')];
    host.events.folders.fire({ removed: [{ uri: file('two') }], added: [] });
    await host.flush();
    await assertViews(host, 1);
    assert.equal(host.diagnostics.has(b.toString()), false);
    host.dispose();
  }
  {
    const broken = document(a, oldRuntime);
    broken.getText = () => { throw new Error('Document became unavailable'); };
    const host = createHost([broken]);
    await host.flush();
    await host.execute('eolkits.showReport');
    await assertViews(host, 0);
    assert.match(host.panels[0].webview.html, /Scan incomplete.*1 unreadable/);
    assert.match(host.panels[0].webview.html, /could not be scanned/);
    host.save(document(a, oldRuntime));
    await assertViews(host, 1);
    host.dispose();
  }
  {
    const escaped = file('one/<img src=x onerror=alert(1)>.yaml');
    const host = createHost([document(escaped, oldRuntime, 'plaintext')]);
    await host.flush();
    await host.execute('eolkits.showReport');
    await assertViews(host, 1);
    assert.match(host.panels[0].webview.html, /&lt;img src=x onerror=alert\(1\)&gt;/);
    assert.doesNotMatch(host.panels[0].webview.html, /<img|<script/);
    const diagnostic = [...host.diagnostics.values()].flat()[0];
    assert.ok(diagnostic.range.end.character <= oldRuntime.split('\n')[diagnostic.range.end.line].length);
    host.dispose();
  }
  {
    const remote = new Uri('vscode-remote', 'ssh-remote+test', file('one/remote.yaml').path);
    const host = createHost([document(remote, oldRuntime)]);
    host.roots = [new Uri(remote.scheme, remote.authority, file('one').path)];
    await host.flush();
    await assertViews(host, 1);
    assert.equal((await treeFindings(host))[0].command.arguments[0], remote, 'Tree navigation preserves remote URI authority');
    host.dispose();
  }
  {
    const host = createHost([document(file('one/notes.md'), oldRuntime, 'markdown')]);
    await host.flush();
    host.save(document(file('one/notes.md'), oldRuntime, 'markdown'));
    assert.doesNotMatch((await host.tree.getChildren())[0].tooltip, /Scan incomplete/);
    await host.execute('eolkits.scanWorkspace');
    await assertViews(host, 0);
    assert.match(host.notifications.at(-1).message, /No supported files scanned/);
    assert.doesNotMatch(host.notifications.at(-1).message, /No deprecation issues found/);
    host.dispose();
  }
  console.log('extension lifecycle tests passed');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
