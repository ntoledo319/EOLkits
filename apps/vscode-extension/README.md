# AWS Lambda EOL Scanner — EOLkits for VS Code

**Find deprecated Lambda runtimes, Amazon Linux 2 references, and AWS SDK v2 compatibility risks before the next runtime change reaches production.**

EOLkits scans Terraform, SAM/CloudFormation, and application source as you work. It flags exact file and line references that need review against AWS's published runtime schedules. It does not need AWS credentials or an AWS account connection.

> Free and MIT-licensed. It runs entirely on your machine — no account, no telemetry, no code leaves your editor.

---

## Run your first scan

1. Open a repository containing Terraform, SAM/CloudFormation, JavaScript,
   TypeScript, Python, YAML, or JSON.
2. Run **EOLkits: Scan Workspace for Deprecations** from the Command Palette, or
   right-click a folder and choose the same command.
3. Review inline findings, the Problems panel, or the **AWS Deprecations** view
   in Explorer.

No AWS login or extension configuration is required.

## What the output looks like

Real output from the bundled scanners on a small test repository — not a mock-up.

**Deprecated Python stdlib and removed decorators, with exact line numbers:**

```
$ python-pivot codemod myrepo/handler.py
▸ Python codemod · myrepo/handler.py · DRY-RUN
⚠ DRY RUN — no changes written. Pass --apply to execute.
  1 file(s) scanned
ℹ [lint]    myrepo/handler.py:1 · imp-module — `imp` module removed in 3.12. Use `importlib` instead.
ℹ [lint]    myrepo/handler.py:5 · asyncio-coroutine-decorator — `@asyncio.coroutine` removed in 3.11. Use `async def` instead.

✓ 0 rewrite(s) across 0 file(s), 2 lint finding(s).
```

**Deprecated Lambda runtime in SAM/CloudFormation:**

```
$ python-pivot iac myrepo/template.yaml
▸ IaC patcher · myrepo/template.yaml · DRY-RUN
  1 IaC candidate file(s) scanned
ℹ [rewrite] myrepo/template.yaml · sam-cfn-runtime · 1 hit(s)

✓ 1 rewrite(s) across 1 file(s).
ℹ Re-run with --apply to write changes.
```

**Amazon Linux 2 patterns that break on AL2023:**

```
$ al2023-gate cloudinit myrepo/Dockerfile
▸ cloud-init diff · 1 file(s)

myrepo/Dockerfile
  [medium] line 2: yum-to-dnf
    RUN yum install -y python3
    → `yum` still works as a compat alias on AL2023 but is deprecated.
```

Inside the editor the same findings appear as inline diagnostics, in the Problems
panel, and in the **AWS Deprecations** view — the extension surfaces them where you
are already working. Every finding is a dry run by default: nothing is rewritten
unless you ask for it.

## What it does

- **Scans on save and on demand** — CloudFormation/SAM, Terraform/HCL, JavaScript, TypeScript, Python, and JSON files across your workspace (`node_modules` excluded).
- **Inline diagnostics** — matched runtime and compatibility patterns are underlined with severity and rule-specific context.
- **Deprecations tree view** — a consolidated list of every finding in the workspace, in the Explorer sidebar.
- **Deprecation report** — a summary panel grouping findings by severity.

## What it detects today

| Signal | Where | Severity |
|---|---|---|
| Lambda `nodejs16.x`, `nodejs18.x`, `nodejs20.x`, or `nodejs22.x` runtime | CloudFormation / SAM / Terraform | High / Medium |
| Lambda `python3.8` / `3.9` / `3.10` / `3.11` | CloudFormation / SAM / Terraform | High / Medium |
| Amazon Linux 2 AMIs (`amazonlinux2`, `AL2`) | CloudFormation / Terraform | High |
| Amazon Linux 2 image references | `*.tf` / `*.hcl` | High |
| Bundled AWS SDK for JavaScript v2 assumptions | JavaScript / TypeScript | Medium |
| Removed or moved Python APIs (`distutils`, `imp`, `collections.Mapping`) | Python | Medium / Low |

Date-bearing findings identify the AWS schedule used by that bundled extension version. Recheck the linked EOLkits/AWS sources before production planning.

Terraform runtime findings are limited to literal `runtime` values inside
`aws_lambda_function` resource blocks. Variables and computed expressions are not
resolved.

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
- Prefer a 10-second check before installing? Paste your config into the **[free AWS EOL checker](https://ntoledo319.github.io/EOLkits/eol-checker/?utm_source=vscode&utm_medium=marketplace&source=vscode)**. Pasted input is not uploaded; bounded first-party usage events may be sent.
- **[$299 Audit](https://ntoledo319.github.io/EOLkits/audit/?utm_source=vscode&utm_medium=marketplace&source=vscode)** — upload a repository ZIP or source file and receive a static PDF with exact observed file/line evidence, remediation notes, scope limits, and configured rule or package references. **30-day money-back.**



Track every deadline on the **[verified migration schedule](https://ntoledo319.github.io/EOLkits/migrate/)**.

---

## Privacy

The scanner runs locally in VS Code. It reads files in your open workspace to detect patterns and never transmits your code. The only network calls are ones you trigger yourself — opening the hosted audit page from a command or the report link.

## License

MIT. Source: <https://github.com/ntoledo319/EOLkits> (`apps/vscode-extension`).
