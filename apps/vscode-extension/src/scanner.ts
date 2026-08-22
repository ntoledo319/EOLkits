import * as vscode from 'vscode';
import { EOLkitsDiagnostics } from './diagnostics';
import {
    RuleMatch,
    scanJavaScriptText,
    scanPythonText,
    scanStructuredText,
    scanTerraformText
} from './rules';
import { resolveSetting } from './settings';

export class EOLkitsScanner {
    constructor(private diagnostics: EOLkitsDiagnostics) {}

    async scanDocument(document: vscode.TextDocument): Promise<void> {
        const text = document.getText();
        let findings: Finding[] = [];

        // Check file type and run appropriate scan
        if (['yaml', 'json', 'jsonc'].includes(document.languageId)) {
            findings.push(...this.toFindings(scanStructuredText(text), document));
        }

        if (['javascript', 'javascriptreact', 'typescript', 'typescriptreact'].includes(document.languageId)) {
            findings.push(...this.toFindings(scanJavaScriptText(text), document));
        }

        if (document.languageId === 'python') {
            findings.push(...this.toFindings(scanPythonText(text), document));
        }

        if (document.fileName.endsWith('.tf') || document.fileName.endsWith('.hcl')) {
            findings.push(...this.toFindings(scanTerraformText(text), document));
        }

        const config = vscode.workspace.getConfiguration('eolkits', document.uri);
        const legacyConfig = vscode.workspace.getConfiguration('rupture', document.uri);
        const enabled = new Set(resolveSetting(config, legacyConfig, 'enabledKits', [
            'lambda-lifeline',
            'al2023-gate',
            'python-pivot'
        ]));
        const threshold = resolveSetting<Finding['severity']>(
            config,
            legacyConfig,
            'severityThreshold',
            'medium'
        );
        findings = findings.filter(finding =>
            enabled.has(this.kitForFinding(finding)) &&
            this.severityRank(finding.severity) >= this.severityRank(threshold)
        );

        // Update diagnostics for this document
        this.diagnostics.setFindings(document.uri, findings);
    }

    private toFindings(matches: RuleMatch[], document: vscode.TextDocument): Finding[] {
        return matches.map(match => {
            const position = document.positionAt(match.index);
            return {
                severity: match.severity,
                message: match.message,
                file: document.fileName,
                line: position.line + 1,
                character: position.character,
                code: match.code
            };
        });
    }

    private kitForFinding(finding: Finding): string {
        if (finding.code.startsWith('PYTHON_') || finding.code.startsWith('LAMBDA_PYTHON')) {
            return 'python-pivot';
        }
        if (finding.code.includes('AL2') || finding.code.startsWith('AMAZON_LINUX')) {
            return 'al2023-gate';
        }
        return 'lambda-lifeline';
    }

    private severityRank(severity: Finding['severity']): number {
        return { low: 1, medium: 2, high: 3, critical: 4 }[severity];
    }
}

interface Finding {
    severity: 'critical' | 'high' | 'medium' | 'low';
    message: string;
    file: string;
    line: number;
    character: number;
    code: string;
}
