import * as vscode from 'vscode';
import { EOLkitsDiagnostics } from './diagnostics';
import { EOLkitsScanner } from './scanner';
import { FileScan, ScanRun, ScanSnapshot, coverageSummary, incomplete, severityRank } from './model';

export const SUPPORTED_FILES = '**/*.{yaml,yml,json,jsonc,tf,hcl,js,jsx,ts,tsx,py}';
const EXCLUDED_FILES = '**/node_modules/**';

function contains(parent: vscode.Uri, child: vscode.Uri): boolean {
    return parent.scheme === child.scheme && parent.authority === child.authority &&
        (parent.path === child.path || child.path.startsWith(parent.path.replace(/\/$/, '') + '/'));
}

/** Release the UI promptly even when a remote provider cannot cancel its read. */
function untilCancelled<T>(operation: Thenable<T>, token: vscode.CancellationToken): Promise<T | undefined> {
    return new Promise((resolve, reject) => {
        let cancellation: vscode.Disposable | undefined;
        cancellation = token.onCancellationRequested(() => {
            cancellation?.dispose();
            resolve(undefined);
        });
        Promise.resolve(operation).then(value => {
            cancellation?.dispose();
            resolve(value);
        }, error => {
            cancellation?.dispose();
            reject(error);
        });
        if (token.isCancellationRequested) {
            cancellation?.dispose();
            resolve(undefined);
        }
    });
}

/** One owner for file results; views never keep an independent source of findings. */
export class ScanLifecycle implements vscode.Disposable {
    private readonly files = new Map<string, FileScan>();
    private readonly revisions = new Map<string, number>();
    private readonly scopeErrors = new Map<string, { uri?: vscode.Uri; message: string }>();
    private sequence = 0;
    private epoch = 0;
    private active?: { epoch: number; source: vscode.CancellationTokenSource };
    private run?: ScanRun;
    private disposed = false;
    private readonly scanner = new EOLkitsScanner();

    constructor(
        private readonly diagnostics: EOLkitsDiagnostics,
        private readonly onChange: (snapshot: ScanSnapshot) => void,
        private readonly showReport: () => void,
        private readonly openAudit: () => Thenable<boolean>
    ) {}

    snapshot(): ScanSnapshot {
        const files = [...this.files.values()];
        return {
            findings: files.flatMap(file => file.findings).sort((a, b) =>
                severityRank(b.severity) - severityRank(a.severity) ||
                a.uri.toString().localeCompare(b.uri.toString()) || a.line - b.line ||
                a.character - b.character || a.code.localeCompare(b.code)),
            scanned: files.filter(file => file.status === 'scanned').length,
            pending: files.filter(file => file.status === 'pending').length,
            failed: files.filter(file => file.status === 'failed'),
            skipped: files.filter(file => file.status === 'skipped'),
            scopeErrors: [...this.scopeErrors.values()].map(error => error.message),
            run: this.run && { ...this.run }
        };
    }

    private publish(): void {
        if (!this.disposed) this.onChange(this.snapshot());
    }

    private set(file: FileScan): void {
        this.files.set(file.uri.toString(), file);
        this.diagnostics.setFindings(file.uri, file.findings);
    }

    private bump(uri: vscode.Uri): number {
        const revision = ++this.sequence;
        this.revisions.set(uri.toString(), revision);
        return revision;
    }

    private accepts(uri: vscode.Uri): boolean {
        return !!vscode.workspace.getWorkspaceFolder(uri) && !uri.path.split('/').includes('node_modules');
    }

    private scan(document: vscode.TextDocument): void {
        try {
            const findings = this.scanner.scanDocument(document);
            this.set({ uri: document.uri, status: findings ? 'scanned' : 'skipped', findings: findings || [],
                reason: findings ? undefined : 'This document has no supported scanner.' });
        } catch {
            this.set({ uri: document.uri, status: 'failed', findings: [], reason: 'The file could not be scanned. Retry after checking that it is readable.' });
        }
    }

    scanSavedDocument(document: vscode.TextDocument): void {
        if (this.disposed || !this.accepts(document.uri) || !this.scanner.supportsDocument(document)) return;
        this.bump(document.uri);
        this.scan(document);
        this.publish();
    }

    markChanged(document: vscode.TextDocument): void {
        if (this.disposed || !this.files.has(document.uri.toString())) return;
        this.markUriChanged(document.uri);
    }

    markUriChanged(uri: vscode.Uri): void {
        if (this.disposed || !this.accepts(uri)) return;
        this.bump(uri);
        this.set({ uri, status: 'pending', findings: [] });
        this.publish();
    }

    async scanUri(uri: vscode.Uri): Promise<void> {
        if (this.disposed || !this.accepts(uri)) return;
        const epoch = this.epoch;
        const revision = this.bump(uri);
        this.set({ uri, status: 'pending', findings: [] });
        this.publish();
        const current = () => !this.disposed && epoch === this.epoch && this.revisions.get(uri.toString()) === revision;
        try {
            const document = await vscode.workspace.openTextDocument(uri);
            if (current()) this.scan(document);
        } catch {
            if (current()) this.set({ uri, status: 'failed', findings: [], reason: 'The file could not be opened. Check permissions and retry the scan.' });
        }
        if (current()) this.publish();
    }

    remove(uris: readonly vscode.Uri[]): void {
        if (this.disposed) return;
        // A deleted directory can also invalidate a discovery still in flight.
        this.active?.source.cancel();
        for (const uri of uris) {
            this.bump(uri);
            for (const [key, file] of this.files) {
                if (!contains(uri, file.uri)) continue;
                this.bump(file.uri);
                this.files.delete(key);
                this.diagnostics.delete(file.uri);
            }
            for (const [key, error] of this.scopeErrors) {
                if (error.uri && contains(uri, error.uri)) this.scopeErrors.delete(key);
            }
        }
        this.publish();
    }

    async scanWorkspace(resource?: vscode.Uri, announce = true): Promise<void> {
        if (this.disposed) return;
        this.active?.source.cancel();
        const epoch = ++this.epoch;
        const source = new vscode.CancellationTokenSource();
        this.active = { epoch, source };
        const startRevision = this.sequence;
        const scope = resource ? vscode.workspace.asRelativePath(resource, true) : 'workspace';
        const run: ScanRun = { scope, status: 'scanning', total: 0, processed: 0 };
        this.run = run;
        const inScope = (uri: vscode.Uri) => resource ? contains(resource, uri) : this.accepts(uri);
        for (const [key, file] of this.files) {
            if (!this.accepts(file.uri)) {
                this.files.delete(key);
                this.diagnostics.delete(file.uri);
            } else if (inScope(file.uri)) {
                this.set({ uri: file.uri, status: 'pending', findings: [] });
            }
        }
        this.publish();
        const current = () => !this.disposed && this.active?.epoch === epoch;
        const stopped = () => !current() || source.token.isCancellationRequested;

        try {
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: `EOLkits: Scanning ${scope}`,
                cancellable: true
            }, async (progress, token) => {
                const cancellation = token.onCancellationRequested(() => source.cancel());
                if (token.isCancellationRequested) source.cancel();
                try {
                    const include = resource ? new vscode.RelativePattern(resource, SUPPORTED_FILES) : SUPPORTED_FILES;
                    const discovered = await untilCancelled(vscode.workspace.findFiles(include, EXCLUDED_FILES, undefined, source.token), source.token);
                    if (!discovered || stopped()) return;
                    const files = [...new Map(discovered.filter(uri => this.accepts(uri) && inScope(uri)).map(uri => [uri.toString(), uri])).values()];
                    const keys = new Set(files.map(uri => uri.toString()));
                    for (const [key, file] of this.files) {
                        if (inScope(file.uri) && !keys.has(key) && (this.revisions.get(key) || 0) <= startRevision) {
                            this.files.delete(key);
                            this.diagnostics.delete(file.uri);
                        }
                    }
                    for (const [key, error] of this.scopeErrors) {
                        if (!resource || (error.uri && contains(resource, error.uri))) this.scopeErrors.delete(key);
                    }
                    run.total = files.length;
                    for (const uri of files) {
                        if ((this.revisions.get(uri.toString()) || 0) <= startRevision) this.set({ uri, status: 'pending', findings: [] });
                    }
                    this.publish();
                    for (const [index, uri] of files.entries()) {
                        if (stopped()) break;
                        const revision = this.revisions.get(uri.toString()) || 0;
                        // A save/change after discovery owns the newer result or pending state.
                        if (revision <= startRevision) {
                            try {
                                const document = await untilCancelled(vscode.workspace.openTextDocument(uri), source.token);
                                if (!document || stopped()) break;
                                if ((this.revisions.get(uri.toString()) || 0) === revision) this.scan(document);
                            } catch {
                                if (stopped()) break;
                                if ((this.revisions.get(uri.toString()) || 0) === revision) {
                                    this.set({ uri, status: 'failed', findings: [], reason: 'The file could not be opened. Check permissions and retry the scan.' });
                                }
                            }
                        }
                        run.processed++;
                        progress.report({ increment: 100 / files.length, message: `${run.processed}/${run.total} files` });
                        if (index % 20 === 0 || index === files.length - 1) this.publish();
                    }
                } finally {
                    cancellation.dispose();
                }
            });
            if (!current()) return;
            run.status = source.token.isCancellationRequested ? 'cancelled' : 'complete';
        } catch {
            if (!current()) return;
            run.status = source.token.isCancellationRequested ? 'cancelled' : 'failed';
            if (run.status === 'failed') this.scopeErrors.set(resource?.toString() || 'workspace', {
                uri: resource, message: `Could not discover files in ${scope}. Check that the folder is available and retry.`
            });
        } finally {
            source.dispose();
            if (current()) {
                this.active = undefined;
                this.publish();
            }
        }
        if (!this.disposed && this.epoch === epoch && announce) this.announce();
    }

    private announce(): void {
        const snapshot = this.snapshot();
        const count = snapshot.findings.length;
        const summary = coverageSummary(snapshot);
        if (count > 0 || incomplete(snapshot)) {
            void vscode.window.showWarningMessage(
                `EOLkits: ${count} potential deprecation issue${count === 1 ? '' : 's'} in current results. ${summary}`,
                'View Report', 'See $299 Report'
            ).then(selection => {
                if (this.disposed) return;
                if (selection === 'View Report') this.showReport();
                else if (selection === 'See $299 Report') void this.openAudit();
            });
        } else {
            void vscode.window.showInformationMessage(snapshot.scanned > 0
                ? `EOLkits: No matches in scanned files at the configured threshold. ${summary}` : `EOLkits: ${summary}`);
        }
    }

    dispose(): void {
        if (this.disposed) return;
        this.disposed = true;
        this.active?.source.cancel();
        this.files.clear();
        this.revisions.clear();
        this.scopeErrors.clear();
    }
}
