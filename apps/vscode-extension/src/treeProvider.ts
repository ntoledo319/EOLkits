import * as vscode from 'vscode';
import { ScanSnapshot, coverageSummary, incomplete } from './model';

export class EOLkitsTreeProvider implements vscode.TreeDataProvider<EOLkitsTreeItem>, vscode.Disposable {
    private readonly changed = new vscode.EventEmitter<EOLkitsTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData = this.changed.event;
    private snapshot: ScanSnapshot = { findings: [], scanned: 0, pending: 0, failed: [], skipped: [], scopeErrors: [] };

    update(snapshot: ScanSnapshot): void {
        this.snapshot = snapshot;
        this.changed.fire();
    }

    getTreeItem(element: EOLkitsTreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: EOLkitsTreeItem): Thenable<EOLkitsTreeItem[]> {
        const snapshot = this.snapshot;
        if (!element) {
            const scanning = snapshot.run?.status === 'scanning';
            const label = scanning ? 'Scan in progress' : incomplete(snapshot) ? 'Scan incomplete — retry' : `${snapshot.scanned} files scanned`;
            const status = new EOLkitsTreeItem(label, 'status', vscode.TreeItemCollapsibleState.None);
            status.tooltip = coverageSummary(snapshot);
            status.iconPath = new vscode.ThemeIcon(scanning ? 'sync~spin' : incomplete(snapshot) ? 'warning' : 'info');
            status.command = { command: incomplete(snapshot) && !scanning ? 'eolkits.scanWorkspace' : 'eolkits.showReport', title: 'Review Scan Coverage' };
            const items = [status];
            for (const severity of ['critical', 'high', 'medium', 'low']) {
                const count = snapshot.findings.filter(finding => finding.severity === severity).length;
                if (count > 0) items.push(new EOLkitsTreeItem(`${severity.toUpperCase()} (${count})`, severity, vscode.TreeItemCollapsibleState.Collapsed));
            }
            const errors = snapshot.failed.length + snapshot.skipped.length + snapshot.scopeErrors.length;
            if (errors > 0) items.push(new EOLkitsTreeItem(`Files and folders needing attention (${errors})`, 'errors', vscode.TreeItemCollapsibleState.Collapsed));
            if (snapshot.findings.length === 0 && !scanning && !incomplete(snapshot)) {
                items.push(new EOLkitsTreeItem(snapshot.scanned > 0 ? 'No matches at configured threshold' : 'No supported files scanned', 'info', vscode.TreeItemCollapsibleState.None));
            }
            return Promise.resolve(items);
        }
        if (element.type === 'errors') {
            const items = [...snapshot.failed, ...snapshot.skipped].map(file => {
                const item = new EOLkitsTreeItem(vscode.workspace.asRelativePath(file.uri, true), 'error', vscode.TreeItemCollapsibleState.None);
                item.tooltip = file.reason;
                item.command = { command: 'vscode.open', title: 'Open File', arguments: [file.uri] };
                return item;
            });
            items.push(...snapshot.scopeErrors.map(error => new EOLkitsTreeItem(error, 'error', vscode.TreeItemCollapsibleState.None)));
            return Promise.resolve(items);
        }
        return Promise.resolve(snapshot.findings.filter(finding => finding.severity === element.type).map(finding => {
            const item = new EOLkitsTreeItem(finding.message, 'finding', vscode.TreeItemCollapsibleState.None);
            item.description = `${vscode.workspace.asRelativePath(finding.uri, true)}:${finding.line}`;
            item.tooltip = `${finding.code}\n${finding.file}:${finding.line}:${finding.character + 1}\n${finding.message}`;
            item.command = {
                command: 'vscode.open', title: 'Open File', arguments: [finding.uri, {
                    selection: new vscode.Range(finding.line - 1, finding.character, finding.line - 1, finding.endCharacter)
                }]
            };
            return item;
        }));
    }

    dispose(): void { this.changed.dispose(); }
}

class EOLkitsTreeItem extends vscode.TreeItem {
    constructor(label: string, public readonly type: string, collapsibleState: vscode.TreeItemCollapsibleState) {
        super(label, collapsibleState);
        this.contextValue = type;
        this.iconPath = new vscode.ThemeIcon(type === 'critical' || type === 'error' ? 'error' : type === 'high' ? 'warning' : type === 'finding' ? 'file-code' : 'info');
    }
}
