import * as vscode from 'vscode';
import { EOLkitsDiagnostics } from './diagnostics';
import { EOLkitsTreeProvider } from './treeProvider';
import { resolveSetting } from './settings';
import { ScanLifecycle, SUPPORTED_FILES } from './lifecycle';
import { generateReportHtml } from './report';

const AUDIT_URL = 'https://ntoledo319.github.io/EOLkits/audit/?utm_source=vscode&utm_medium=extension&source=vscode';
let activeLifecycle: ScanLifecycle | undefined;

function openAudit(): Thenable<boolean> {
    return vscode.env.openExternal(vscode.Uri.parse(AUDIT_URL));
}

function autoScan(uri: vscode.Uri): boolean {
    return resolveSetting(vscode.workspace.getConfiguration('eolkits', uri),
        vscode.workspace.getConfiguration('rupture', uri), 'autoScan', true);
}

export function activate(context: vscode.ExtensionContext): void {
    const diagnostics = new EOLkitsDiagnostics();
    const tree = new EOLkitsTreeProvider();
    let report: vscode.WebviewPanel | undefined;
    const showReport = () => {
        if (report) {
            report.reveal(vscode.ViewColumn.One);
        } else {
            report = vscode.window.createWebviewPanel('eolkitsReport', 'EOLkits Deprecation Report', vscode.ViewColumn.One, {});
            report.onDidDispose(() => { report = undefined; }, undefined, context.subscriptions);
        }
        report.webview.html = generateReportHtml(lifecycle.snapshot());
    };
    const lifecycle = new ScanLifecycle(diagnostics, snapshot => {
        tree.update(snapshot);
        if (report) report.webview.html = generateReportHtml(snapshot);
        void vscode.commands.executeCommand('setContext', 'eolkits.hasDeprecations', snapshot.findings.length > 0);
    }, showReport, openAudit);
    activeLifecycle = lifecycle;
    context.subscriptions.push(
        lifecycle, diagnostics, tree,
        { dispose: () => report?.dispose() },
        vscode.window.registerTreeDataProvider('eolkits.deprecations', tree)
    );
    for (const namespace of ['eolkits', 'rupture']) {
        context.subscriptions.push(
            vscode.commands.registerCommand(`${namespace}.scanWorkspace`, (resource?: vscode.Uri) => lifecycle.scanWorkspace(resource)),
            vscode.commands.registerCommand(`${namespace}.showReport`, showReport),
            vscode.commands.registerCommand(`${namespace}.getAudit`, openAudit)
        );
    }
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument(document => {
            if (autoScan(document.uri)) lifecycle.scanSavedDocument(document);
            else lifecycle.markChanged(document);
        }),
        vscode.workspace.onDidChangeTextDocument(event => {
            if (event.contentChanges.length > 0) lifecycle.markChanged(event.document);
        }),
        vscode.workspace.onDidDeleteFiles(event => lifecycle.remove(event.files)),
        vscode.workspace.onDidRenameFiles(event => {
            lifecycle.remove(event.files.map(file => file.oldUri));
            void lifecycle.scanWorkspace(undefined, false);
        }),
        vscode.workspace.onDidChangeWorkspaceFolders(() => { void lifecycle.scanWorkspace(undefined, false); }),
        vscode.workspace.onDidChangeConfiguration(event => {
            if (['eolkits.enabledKits', 'eolkits.severityThreshold', 'rupture.enabledKits', 'rupture.severityThreshold', 'files.associations']
                .some(setting => event.affectsConfiguration(setting))) void lifecycle.scanWorkspace(undefined, false);
        })
    );
    const watcher = vscode.workspace.createFileSystemWatcher(SUPPORTED_FILES);
    const changedOnDisk = (uri: vscode.Uri) => {
        if (autoScan(uri)) void lifecycle.scanUri(uri);
        else lifecycle.markUriChanged(uri);
    };
    context.subscriptions.push(watcher,
        watcher.onDidDelete(uri => lifecycle.remove([uri])),
        watcher.onDidCreate(changedOnDisk),
        watcher.onDidChange(changedOnDisk)
    );
    void lifecycle.scanWorkspace(undefined, false);
}

export function deactivate(): void {
    activeLifecycle?.dispose();
    activeLifecycle = undefined;
}
