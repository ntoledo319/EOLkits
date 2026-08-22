# EOLkits — AWS Deprecation Scanner for VS Code

**Catch AWS runtime & OS end-of-life risks the moment you write them — right in the editor, offline, with nothing uploaded.**

AWS retires runtimes and operating systems on published schedules. EOLkits scans your infrastructure-as-code and application source as you work and flags references that need review before AWS applies runtime create/update restrictions or an operating-system migration becomes urgent.

> Free and MIT-licensed. It runs entirely on your machine — no account, no telemetry, no code leaves your editor.

---

## What it does

- **Scans on save and on demand** — CloudFormation/SAM, Terraform/HCL, JavaScript, TypeScript, Python, and JSON files across your workspace (`node_modules` excluded).
- **Inline diagnostics** — matched runtime and compatibility patterns are underlined with severity and rule-specific context.
- **Deprecations tree view** — a consolidated list of every finding in the workspace, in the Explorer sidebar.
- **Deprecation report** — a summary panel grouping findings by severity.

## What it detects today

| Signal | Where | Severity |
|---|---|---|
| Lambda `nodejs20.x` runtime | CloudFormation / SAM | Critical |
| Lambda `python3.9` / `3.10` / `3.11` | CloudFormation / SAM | High / Medium |
| Amazon Linux 2 AMIs (`amazonlinux2`, `AL2`) | CloudFormation / Terraform | High |
| Amazon Linux 2 image references | `*.tf` / `*.hcl` | High |

Date-bearing findings identify the AWS schedule used by that bundled extension version. Recheck the linked EOLkits/AWS sources before production planning.

## Commands

| Command | What it does |
|---|---|
| **EOLkits: Scan Workspace for Deprecations** | Scan every supported file in the workspace |
| **EOLkits: Show Deprecation Report** | Open the grouped findings report |
| **EOLkits: Get Repository Evidence Report** | Open the hosted static-analysis audit flow |

Right-click any folder in the Explorer to scan it directly.

## Settings

| Setting | Default | Description |
|---|---|---|
| `eolkits.enabledKits` | all three | Which deprecation kits to run |
| `eolkits.severityThreshold` | `medium` | Minimum severity to report |
| `eolkits.autoScan` | `true` | Scan automatically on file save |

---

## From "flagged" to "fixed"

The extension tells you **what** is deprecated. To **fix** it, EOLkits ships:

- **Free, MIT CLIs** — one per deadline (`al2023-gate`, `python-pivot`, `lambda-lifeline`). Their documented commands scan specific source and IaC patterns; selected commands can prepare migration edits or rollout artifacts. Review all output before applying it: <https://github.com/ntoledo319/EOLkits>
- Prefer a 10-second check before installing? Paste your config into the **[free AWS EOL checker](https://eolkits.com/eol-checker/?utm_source=vscode&utm_medium=marketplace&source=vscode)** — nothing uploaded.
- **[$299 Audit](https://eolkits.com/audit/?utm_source=vscode&utm_medium=marketplace&source=vscode)** — when checkout is enabled, upload a repository ZIP or source file and receive a static PDF with exact observed file/line evidence, remediation notes, scope limits, and cited sources. **30-day money-back.**

Migration Pack and the other previously described hosted products are not available for purchase.

Track every deadline at **[eolkits.com/migrate](https://eolkits.com/migrate)**.

---

## Privacy

The scanner runs locally in VS Code. It reads files in your open workspace to detect patterns and never transmits your code. The only network calls are ones you trigger yourself — opening the hosted audit page from a command or the report link.

## License

MIT. Source: <https://github.com/ntoledo319/EOLkits> (`apps/vscode-extension`).
