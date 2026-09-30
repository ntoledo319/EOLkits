import { ScanSnapshot, coverageSummary } from './model';

function escapeHtml(value: string): string {
    return value.replace(/[&<>"']/g, character => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[character] as string));
}

export function generateReportHtml(snapshot: ScanSnapshot): string {
    const rows = snapshot.findings.map(finding => `<tr>
        <td><span class="severity ${finding.severity}">${finding.severity.toUpperCase()}</span></td>
        <td>${escapeHtml(finding.message)}<br><code>${escapeHtml(finding.code)}</code></td>
        <td class="path">${escapeHtml(finding.file)}</td>
        <td>Line ${finding.line}, column ${finding.character + 1}</td>
    </tr>`).join('');
    const errors = [...snapshot.scopeErrors, ...[...snapshot.failed, ...snapshot.skipped].map(file =>
        `${file.uri.fsPath}: ${file.reason}`)];
    const interestLink = snapshot.findings.length > 0
        ? `<p><strong>Would you consider a one-time $299 repository evidence report?</strong>
            <a href="https://github.com/ntoledo319/EOLkits/issues/new?template=audit-interest.yml">Record nonbinding Audit interest</a>
            in a public GitHub form. Do not include project, company, security, or personal data.</p>` : '';
    return `<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline';">
<style>
    body { font-family: var(--vscode-font-family, sans-serif); color: var(--vscode-editor-foreground); background: var(--vscode-editor-background); padding: 20px; line-height: 1.5; }
    h1 { font-size: 1.7rem; } a { color: var(--vscode-textLink-foreground); }
    .coverage { padding: 12px 16px; border-left: 3px solid var(--vscode-focusBorder); background: var(--vscode-textBlockQuote-background); }
    .table-scroll { overflow-x: auto; } table { width: 100%; border-collapse: collapse; }
    th, td { padding: 10px; text-align: left; vertical-align: top; border-bottom: 1px solid var(--vscode-panel-border); }
    th { font-weight: 600; } .path, li { overflow-wrap: anywhere; } code { font-size: .85em; }
    .severity { font-size: .8em; font-weight: bold; } .critical, .high { color: var(--vscode-errorForeground); }
    .medium { color: var(--vscode-editorWarning-foreground); } .low { color: var(--vscode-editorInfo-foreground); }
</style></head><body>
<h1>EOLkits Deprecation Report</h1>
<div class="coverage" role="status"><strong>${escapeHtml(coverageSummary(snapshot))}</strong>
${snapshot.run ? `<p>Latest scan scope: ${escapeHtml(snapshot.run.scope)}. Findings below combine the current scanned files across open folders.</p>` : ''}
<p>Files in node_modules are excluded. Disabled kits, findings below your severity threshold, variables, and computed runtime expressions are outside this result. Scan again after changing files.</p></div>
${errors.length ? `<h2>Files and folders needing attention</h2><ul>${errors.map(error => `<li>${escapeHtml(error)}</li>`).join('')}</ul>` : ''}
<h2>${snapshot.findings.length} potential issue${snapshot.findings.length === 1 ? '' : 's'}</h2>
${rows ? `<div class="table-scroll"><table><thead><tr><th scope="col">Severity</th><th scope="col">Issue</th><th scope="col">File</th><th scope="col">Location</th></tr></thead><tbody>${rows}</tbody></table></div>` : '<p>No matches in the currently scanned files at the configured threshold. Check the coverage above before interpreting this result.</p>'}
<p>Date-bearing findings use the schedule bundled with this extension. Verify current dates and references on the <a href="https://ntoledo319.github.io/EOLkits/migrate/">sourced migration schedule</a> before production planning.</p>
${interestLink}
<p><a href="https://ntoledo319.github.io/EOLkits/audit/?utm_source=vscode&utm_medium=extension&source=vscode">Get repository evidence report →</a></p>
</body></html>`;
}
