import * as vscode from 'vscode';
import { Finding, severityRank } from './model';
import {
    RuleMatch,
    scanJavaScriptText,
    scanPythonText,
    scanStructuredText,
    scanTerraformText
} from './rules';
import { resolveSetting } from './settings';

export class EOLkitsScanner {
    supportsDocument(document: vscode.TextDocument): boolean {
        return ['yaml', 'json', 'jsonc', 'javascript', 'javascriptreact', 'typescript', 'typescriptreact', 'python'].includes(document.languageId) ||
            /\.(tf|hcl|yaml|yml|json|jsonc|js|jsx|ts|tsx|py)$/i.test(document.fileName);
    }

    scanDocument(document: vscode.TextDocument): Finding[] | undefined {
        if (!this.supportsDocument(document)) return undefined;
        const text = document.getText();
        let findings: Finding[] = [];
        const extension = document.fileName.split('.').pop()?.toLowerCase();

        // Extension fallback keeps a supported file scannable without another language extension.
        if (extension === 'tf' || extension === 'hcl') {
            findings = this.toFindings(scanTerraformText(text), document);
        } else if (['yaml', 'json', 'jsonc'].includes(document.languageId) ||
            ['yaml', 'yml', 'json', 'jsonc'].includes(extension || '')) {
            findings = this.toFindings(scanStructuredText(text), document);
        } else if (['javascript', 'javascriptreact', 'typescript', 'typescriptreact'].includes(document.languageId) ||
            ['js', 'jsx', 'ts', 'tsx'].includes(extension || '')) {
            findings = this.toFindings(scanJavaScriptText(text), document);
        } else if (document.languageId === 'python' || extension === 'py') {
            findings = this.toFindings(scanPythonText(text), document);
        } else {
            return undefined;
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
            severityRank(finding.severity) >= severityRank(threshold)
        );
        return findings;
    }

    private toFindings(matches: RuleMatch[], document: vscode.TextDocument): Finding[] {
        return matches.map(match => {
            const position = document.positionAt(match.index);
            return {
                severity: match.severity,
                message: match.message,
                uri: document.uri,
                file: document.fileName,
                line: position.line + 1,
                character: position.character,
                endCharacter: Math.min(position.character + 10, document.lineAt(position.line).text.length),
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
}
