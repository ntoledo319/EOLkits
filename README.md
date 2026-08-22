# EOLkits

EOLkits finds AWS runtime and Amazon Linux migration risks in source code and
infrastructure-as-code. The scanners run locally; the optional paid product turns
a repository ZIP or source file into a shareable evidence report.

## Use it free

Run the verified [browser scanner](https://ntoledo319.github.io/EOLkits/scan/?source=github_readme&utm_source=github&utm_medium=readme)
or use one of the MIT-licensed kits in this repository:

- [`lambda-lifeline`](./kits/lambda-lifeline) checks Lambda Node.js runtime,
  dependency, source, and IaC compatibility.
- [`python-pivot`](./kits/python-pivot) checks Lambda Python runtime, removed
  standard-library APIs, dependency, and IaC compatibility.
- [`al2023-gate`](./kits/al2023-gate) checks Amazon Linux 2 to Amazon Linux 2023
  package, cloud-init, Ansible, and rollout concerns.

Each kit has its own installation and command reference. Fixture and dry-run modes
let you inspect proposed work before using cloud credentials or changing files.

## GitHub Action

Add the free repository check to a workflow:

```yaml
permissions:
  contents: read
  pull-requests: write # only needed when comment-pr is true

steps:
  - uses: actions/checkout@v6
  - uses: ntoledo319/EOLkits@v2
    with:
      kit: auto
      path: .
      fail-on: any
      comment-pr: true
```

The action installs the three local kits, scans only the selected workspace path,
and writes a job summary. Pull-request comments are off by default; enable
`comment-pr: true` only when the caller deliberately grants write permission.

## Paid repository evidence report

The only paid product EOLkits is prepared to offer is a **$299 static repository
evidence report**. Checkout is shown only when the v2 fulfillment backend reports
itself ready; while that operational gate is closed, the report is not
purchasable.

The report includes:

- exact observed file and line locations, capped per finding type;
- severity, remediation notes, and primary-source links;
- the uploaded input SHA-256, rule-pack version, and deterministic evidence
  fingerprint;
- explicit scope and limitations.

It does **not** inspect an AWS account, predict downtime or cost, prove exploitability,
or digitally sign the PDF. A successfully delivered report causes its source upload
to be deleted immediately; checkout-bound source uploads expire within 48 hours and
reports within 30 days. See the [terms](./legal/terms.md),
[privacy notice](./legal/privacy.md), and [security model](./SECURITY.md).

[See the $299 report scope and availability](https://ntoledo319.github.io/EOLkits/audit/?source=github_readme&utm_source=github&utm_medium=readme)

## Not for sale

Migration Pack, Drift Watch, Organization License, partner white-labeling, and the
public GitHub App are closed research or private-beta concepts. Their API checkout
and fulfillment paths reject requests. They should not be represented as available
products.

## Local verification

```bash
# Use project-local environments; CI carries the complete matrix.
python3 -m venv tmp/verify-venv
tmp/verify-venv/bin/pip install -r apps/grace-api/requirements-dev.txt
tmp/verify-venv/bin/pip install -r apps/runner/requirements-dev.txt
tmp/verify-venv/bin/pip install -r apps/web/requirements-dev.txt
TMPDIR="$PWD/tmp/runtime-tmp" tmp/verify-venv/bin/pytest -q apps/grace-api
TMPDIR="$PWD/tmp/runtime-tmp" tmp/verify-venv/bin/pytest -q apps/runner
TMPDIR="$PWD/tmp/runtime-tmp" tmp/verify-venv/bin/pytest -q apps/web

# Node kit
(cd kits/lambda-lifeline && npm test)

# Worker
(cd apps/worker && npm test)

# Static site
tmp/verify-venv/bin/python apps/web/build.py
```

Use each component's lockfile or requirements file when constructing an isolated
environment. The CI workflows are the canonical full matrix.

## Architecture

- `kits/` — local migration scanners and codemods
- `apps/github-action/` + `action.yml` — free CI distribution surface
- `apps/vscode-extension/` — local editor scanner
- `apps/web/` — deterministic static-site generator
- `apps/grace-api/` — upload, checkout, webhook, job, refund, and delivery service
- `apps/runner/` — evidence extraction and PDF rendering
- `rules/public/` — cited deprecation dates used by public surfaces
- `revenue/` — current commercial plan, evidence, decisions, and owner queue

## License

The repository code is MIT-licensed unless a file says otherwise. Third-party
licenses are recorded in [`ATTRIBUTIONS.md`](./ATTRIBUTIONS.md).
