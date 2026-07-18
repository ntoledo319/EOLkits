# Attributions & License Disclosure

This bundle ("AWS Runtime EOL Migration Toolkit") packages three open-source CLIs from the EOLkits project
(`github.com/ntoledo319/EOLkits`) plus an original migration playbook. This file satisfies the pre-publish license
audit required before selling any packaged artifact (§9 of the project's operating doc).

## Bundled tools and their licenses

| Component | License | Copyright |
|---|---|---|
| `al2023-gate` | MIT | © 2026 EOLkits Kits |
| `python-pivot` | MIT | © 2026 EOLkits |
| `lambda-lifeline` | MIT | © 2026 EOLkits |
| `MIGRATION-PLAYBOOK.md` (this bundle) | MIT | © 2026 EOLkits |

Full license text for each tool is included in its own `LICENSE` file inside this bundle. MIT permits commercial
resale, modification, and redistribution — the terms explicitly allowed here are: use, copy, modify, merge, publish,
distribute, sublicense, and sell copies, provided the copyright notice and permission notice are retained (already
present in each `LICENSE` file, unmodified).

## Runtime dependencies (declared, not vendored)

None of the three CLIs bundle third-party code — dependencies are declared in `pyproject.toml` / `package.json` and
installed separately by the end user (`pip install` / `npm install`), so no third-party source ships inside this
zip. For transparency, the optional/runtime dependencies a user's own install step will pull in:

| Dependency | Used by | License |
|---|---|---|
| `boto3` (optional, for live AWS scans) | `al2023-gate`, `python-pivot` | Apache-2.0 |
| `@aws-sdk/client-cloudwatch` | `lambda-lifeline` | Apache-2.0 |
| `@aws-sdk/client-lambda` | `lambda-lifeline` | Apache-2.0 |
| `@aws-sdk/client-sts` | `lambda-lifeline` | Apache-2.0 |
| `@aws-sdk/credential-providers` | `lambda-lifeline` | Apache-2.0 |

Apache-2.0 is permissive and compatible with MIT redistribution. **No copyleft (GPL/AGPL/LGPL) dependencies are
present anywhere in this dependency tree** — confirmed by direct inspection of each kit's manifest.

## AI-assisted provenance

This bundle's tooling and this playbook were developed with AI assistance (Claude, by Anthropic) under human
direction and review, as part of the EOLkits project. Disclosed here per marketplace provenance requirements.

## Deadline data source

All AWS deadline dates cited in `MIGRATION-PLAYBOOK.md` are sourced from AWS's own public documentation — the
Lambda runtime deprecation table (`docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html`) and the Amazon Linux
2 FAQ (`aws.amazon.com/amazon-linux-2/faqs/`) — cross-checked against the same dataset (`rules/public/deprecations.yml`)
that drives the live calendar at `eolkits.com/status`. Snapshot date: 2026-07-18. AWS may revise these dates; check
the live source before treating any date as final.
