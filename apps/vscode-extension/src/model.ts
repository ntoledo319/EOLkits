import * as vscode from 'vscode';

export interface Finding {
    severity: 'critical' | 'high' | 'medium' | 'low';
    message: string;
    uri: vscode.Uri;
    file: string;
    line: number;
    character: number;
    endCharacter: number;
    code: string;
}

export interface FileScan {
    uri: vscode.Uri;
    status: 'scanned' | 'pending' | 'failed' | 'skipped';
    findings: Finding[];
    reason?: string;
}

export interface ScanRun {
    scope: string;
    status: 'scanning' | 'complete' | 'cancelled' | 'failed';
    total: number;
    processed: number;
}

export interface ScanSnapshot {
    findings: Finding[];
    scanned: number;
    pending: number;
    failed: FileScan[];
    skipped: FileScan[];
    scopeErrors: string[];
    run?: ScanRun;
}

export function severityRank(severity: Finding['severity']): number {
    return { low: 1, medium: 2, high: 3, critical: 4 }[severity];
}

export function incomplete(snapshot: ScanSnapshot): boolean {
    return snapshot.pending > 0 || snapshot.failed.length > 0 || snapshot.skipped.length > 0 ||
        snapshot.scopeErrors.length > 0 || snapshot.run?.status === 'cancelled' ||
        snapshot.run?.status === 'failed';
}

/** Every surface uses the same scope-qualified coverage, including zero results. */
export function coverageSummary(snapshot: ScanSnapshot): string {
    if (snapshot.run?.status === 'scanning') {
        return `Scanning ${snapshot.run.scope}: ${snapshot.run.processed}/${snapshot.run.total} files processed.`;
    }
    const counts = `${snapshot.scanned} scanned, ${snapshot.failed.length} unreadable, ` +
        `${snapshot.skipped.length} skipped, ${snapshot.pending} pending`;
    if (incomplete(snapshot)) {
        const reason = snapshot.run?.status === 'cancelled' ? 'Scan cancelled' : 'Scan incomplete';
        return `${reason}: ${counts}. Run a workspace scan to retry.`;
    }
    if (snapshot.scanned === 0) {
        return 'No supported files scanned. Open a workspace with supported source or infrastructure files.';
    }
    return `${counts}. Results cover scanned file contents and enabled rules only; they are not a migration guarantee.`;
}
