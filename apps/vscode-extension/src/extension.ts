import * as vscode from 'vscode';
import { EOLkitsScanner } from './scanner';
import { EOLkitsDiagnostics } from './diagnostics';
import { EOLkitsTreeProvider } from './treeProvider';
import { resolveSetting } from './settings';

let scanner: EOLkitsScanner;
let diagnostics: EOLkitsDiagnostics;
let treeProvider: EOLkitsTreeProvider;
const AUDIT_URL = 'https://ntoledo319.github.io/EOLkits/audit/?utm_source=vscode&utm_medium=extension&source=vscode';

function openAudit(): Thenable<boolean> {
    return vscode.env.openExternal(vscode.Uri.parse(AUDIT_URL));
}

export function activate(context: vscode.ExtensionContext) {
    console.log('EOLkits extension activated');

    // Initialize components
    diagnostics = new EOLkitsDiagnostics();
    scanner = new EOLkitsScanner(diagnostics);
    treeProvider = new EOLkitsTreeProvider();

    // Register tree view
    context.subscriptions.push(
        vscode.window.registerTreeDataProvider('eolkits.deprecations', treeProvider),
        diagnostics
    );

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('eolkits.scanWorkspace', (resource?: vscode.Uri) => {
            void scanWorkspace(resource);
        }),
        vscode.commands.registerCommand('eolkits.showReport', () => {
            showReport();
        }),
        vscode.commands.registerCommand('eolkits.getAudit', () => {
            return openAudit();
        }),
        vscode.commands.registerCommand('rupture.scanWorkspace', (resource?: vscode.Uri) => {
            void scanWorkspace(resource);
        }),
        vscode.commands.registerCommand('rupture.showReport', () => {
            showReport();
        }),
        vscode.commands.registerCommand('rupture.getAudit', () => {
            return openAudit();
        })
    );

    // Auto-scan on save
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((document) => {
            const config = vscode.workspace.getConfiguration('eolkits', document.uri);
            const legacyConfig = vscode.workspace.getConfiguration('rupture', document.uri);
            if (resolveSetting(config, legacyConfig, 'autoScan', true)) {
                void scanner.scanDocument(document);
            }
        })
    );

    // Initial workspace scan
    void scanWorkspace();
}

async function scanWorkspace(resource?: vscode.Uri) {
    const progressOptions = {
        location: vscode.ProgressLocation.Window,
        title: 'EOLkits: Scanning for AWS deprecations...'
    };

    await vscode.window.withProgress(progressOptions, async (progress) => {
        diagnostics.clear();
        const include = resource
            ? new vscode.RelativePattern(resource, '**/*.{yaml,yml,json,jsonc,tf,hcl,js,jsx,ts,tsx,py}')
            : '**/*.{yaml,yml,json,jsonc,tf,hcl,js,jsx,ts,tsx,py}';
        const files = await vscode.workspace.findFiles(
            include,
            '**/node_modules/**'
        );

        progress.report({ increment: 0 });

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            try {
                const document = await vscode.workspace.openTextDocument(file);
                await scanner.scanDocument(document);
            } catch {
                // Skip files that can't be opened
            }
            progress.report({ increment: (i / files.length) * 100 });
        }

        // Update tree view
        const findings = diagnostics.getAllFindings();
        treeProvider.updateFindings(findings);
        await vscode.commands.executeCommand('setContext', 'eolkits.hasDeprecations', findings.length > 0);

        // Show summary
        const count = findings.length;
        if (count > 0) {
            vscode.window.showWarningMessage(
                `EOLkits found ${count} potential deprecation issue${count === 1 ? '' : 's'}.`,
                'View Report',
                'See $299 Report'
            ).then(selection => {
                if (selection === 'View Report') {
                    showReport();
                } else if (selection === 'See $299 Report') {
                    void openAudit();
                }
            });
        } else {
            vscode.window.showInformationMessage('EOLkits: No deprecation issues found.');
        }
    });
}

function showReport() {
    const findings = diagnostics.getAllFindings();

    const panel = vscode.window.createWebviewPanel(
        'eolkitsReport',
        'EOLkits Deprecation Report',
        vscode.ViewColumn.One,
        {}
    );

    panel.webview.html = generateReportHtml(findings);
}

function generateReportHtml(findings: any[]): string {
    const rows = findings.map(f => `
        <tr>
            <td><span class="severity ${escapeHtml(f.severity)}">${escapeHtml(f.severity)}</span></td>
            <td>${escapeHtml(f.message)}</td>
            <td>${escapeHtml(f.file)}</td>
            <td>Line ${escapeHtml(String(f.line))}</td>
        </tr>
    `).join('');
    const interestLink = findings.length > 0
        ? `<p><strong>Would you consider a one-time $299 repository evidence report?</strong>
            <a href="https://github.com/ntoledo319/EOLkits/issues/new?template=audit-interest.yml">Record nonbinding Audit interest</a>
            in a public GitHub form. Do not include project, company, security, or personal data.</p>`
        : '';

    return `<!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline';">
        <style>
            body { font-family: sans-serif; padding: 20px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #f5f5f5; }
            .severity { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
            .critical { background: #fee; color: #c00; }
            .high { background: #ffe8cc; color: #c60; }
            .medium { background: #ffffcc; color: #880; }
            .low { background: #efe; color: #080; }
        </style>
    </head>
    <body>
        <h1>EOLkits Deprecation Report</h1>
        <p>Found ${findings.length} issue(s)</p>
        <table>
            <tr>
                <th>Severity</th>
                <th>Issue</th>
                <th>File</th>
                <th>Location</th>
            </tr>
            ${rows}
        </table>
        ${interestLink}
        <p><a href="https://ntoledo319.github.io/EOLkits/audit/?utm_source=vscode&utm_medium=extension&source=vscode">Get repository evidence report →</a></p>
    </body>
    </html>`;
}

function escapeHtml(value: string): string {
    return value.replace(/[&<>"']/g, (character) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }[character] as string));
}

export function deactivate() {
    console.log('EOLkits extension deactivated');
}
