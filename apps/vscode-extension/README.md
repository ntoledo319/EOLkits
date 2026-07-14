# EOLkits — AWS Deprecation Scanner for VS Code

**Catch AWS runtime & OS end-of-life risks the moment you write them — right in the editor, offline, with nothing uploaded.**

AWS retires runtimes and operating systems on a hard schedule. When a deadline passes, deploys start failing, functions get frozen, and AMIs stop receiving security patches — and most teams find out in production. EOLkits scans your infrastructure-as-code and application source as you work and flags the resources that are about to break.

> Free and MIT-licensed. It runs entirely on your machine — no account, no telemetry, no code leaves your editor.

---

## What it does

- **Scans on save and on demand** — CloudFormation/SAM, Terraform/HCL, JavaScript, TypeScript, Python, and JSON files across your workspace (`node_modules` excluded).
- **Inline diagnostics** — deprecated runtimes are underlined with severity and the exact EOL date, so you see the risk at the line that causes it.
- **Deprecations tree view** — a consolidated list of every finding in the workspace, in the Explorer sidebar.
- **Deprecation report** — a summary panel grouping findings by severity.

## What it detects today

| Signal | Where | Severity |
|---|---|---|
| Lambda `nodejs20.x` runtime | CloudFormation / SAM | Critical |
| Lambda `python3.9` / `3.10` / `3.11` | CloudFormation / SAM | High / Medium |
| Amazon Linux 2 AMIs (`amazonlinux2`, `AL2`) | CloudFormation / Terraform | High |
| Deprecated runtimes in Terraform resources | `*.tf` / `*.hcl` | varies |

Every finding carries the real published AWS end-of-life date so you can prioritize by deadline.

## Commands

| Command | What it does |
|---|---|
| **EOLkits: Scan Workspace for Deprecations** | Scan every supported file in the workspace |
| **EOLkits: Show Deprecation Report** | Open the grouped findings report |
| **EOLkits: Get Full Audit Report** | Open the hosted, hash-anchored audit flow |

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

- **Free, MIT CLIs** — one per deadline (`al2023-gate`, `python-pivot`, `lambda-lifeline`). They rewrite source and IaC, generate a staged canary rollout, and produce a rollback script. Clone and run them yourself: <https://github.com/ntoledo319/EOLkits>
- **[$299 Audit](https://eolkits.com/audit/?utm_source=vscode&utm_medium=marketplace&source=vscode)** — a hash-anchored report scoring every finding by severity × blast-radius, with a roll-forward roadmap and cost-of-not-fixing estimate. **30-day money-back.**
- **[$1,499 Migration Pack](https://eolkits.com/pack/?utm_source=vscode&utm_medium=marketplace&source=vscode)** — a real pull request opened on your repo with the codemods, IaC patches, canary plan, and rollback. Refund auto-fires if your CI fails.

Track every deadline at **[eolkits.com/migrate](https://eolkits.com/migrate)**.

---

## Privacy

The scanner runs locally in VS Code. It reads files in your open workspace to detect patterns and never transmits your code. The only network calls are ones you trigger yourself — opening the hosted audit page from a command or the report link.

## License

MIT. Source: <https://github.com/ntoledo319/EOLkits> (`apps/vscode-extension`).
