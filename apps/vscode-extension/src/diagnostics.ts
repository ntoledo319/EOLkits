import * as vscode from 'vscode';
import { Finding } from './model';

export class EOLkitsDiagnostics implements vscode.Disposable {
    private readonly diagnosticCollection: vscode.DiagnosticCollection;

    constructor() {
        this.diagnosticCollection = vscode.languages.createDiagnosticCollection('eolkits');
    }

    setFindings(uri: vscode.Uri, findings: Finding[]): void {
        const diagnostics: vscode.Diagnostic[] = findings.map(f => {
            const range = new vscode.Range(
                new vscode.Position(f.line - 1, f.character),
                new vscode.Position(f.line - 1, f.endCharacter)
            );

            const diagnostic = new vscode.Diagnostic(
                range,
                f.message,
                this.severityToDiagnostic(f.severity)
            );
            diagnostic.code = f.code;
            diagnostic.source = 'EOLkits';

            return diagnostic;
        });

        this.diagnosticCollection.set(uri, diagnostics);
    }

    delete(uri: vscode.Uri): void {
        this.diagnosticCollection.delete(uri);
    }

    dispose(): void {
        this.diagnosticCollection.dispose();
    }

    private severityToDiagnostic(severity: string): vscode.DiagnosticSeverity {
        switch (severity) {
            case 'critical':
            case 'high':
                return vscode.DiagnosticSeverity.Error;
            case 'medium':
                return vscode.DiagnosticSeverity.Warning;
            case 'low':
            default:
                return vscode.DiagnosticSeverity.Information;
        }
    }
}
