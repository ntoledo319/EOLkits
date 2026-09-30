# python-pivot
### AWS Lambda Python 3.9/3.10/3.11 → 3.12 migration kit

> AWS publishes separate Lambda runtime deprecation, block-create, and block-update dates and may revise them. Check the linked AWS runtime table before planning a production change.

`python-pivot` checks Python Lambda functions visible to the selected credentials and regions, detects supported Python 3.12 compatibility patterns, audits curated dependency versions, previews supported IaC rewrites, and provides guarded deploy and rollback commands.

Works offline (fixture mode) for demos and CI. Works live against AWS with standard boto3 credentials.

[![Tests](https://img.shields.io/badge/tests-CI%20verified-green)](test/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python 3.9 EOL](https://img.shields.io/badge/python3.9-EOL%202025--12--15-red)](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)

---

## The deadline

Use the [AWS Lambda runtime table](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)
as the source of truth. The repository's cited snapshot is in
[`rules/public/deprecations.yml`](../../rules/public/deprecations.yml), but AWS can
change enforcement dates after a release is cut.

---

## Install

```bash
git clone https://github.com/ntoledo319/EOLkits.git
cd EOLkits/kits/python-pivot
python3 -m venv .venv
.venv/bin/pip install -e .
. .venv/bin/activate
```

No required external runtime dependencies. `boto3` is needed for live AWS
commands. TOML audits use the standard library on Python 3.11+; on Python
3.9/3.10, use a flat requirements file or install the optional `tomli` parser.

---

## The 6 commands

```
python-pivot scan        # find Python Lambdas by runtime, severity, days-to-EOL
python-pivot codemod     # rewrite source for 3.12 (collections.abc, distutils, asyncio, …)
python-pivot audit       # compare declared dependencies with curated cp312 baselines
python-pivot iac         # patch Runtime: python3.9 → python3.12 across SAM/CDK/Terraform/Serverless
python-pivot deploy      # staged canary deploy with CloudWatch-alarm auto-rollback
python-pivot rollback    # revert alias to previous version
```

---

## 5-minute demo

### 1. Scan

```bash
$ python-pivot scan --fixture test/fixtures/lambda-inventory.json

▸ Scanning fixture test/fixtures/lambda-inventory.json
ℹ Scanned 6 Python Lambda function(s). 4 need migration.

FUNCTION           RUNTIME     REGION     SEVERITY      EOL DELTA    TARGET
---------------------------------------------------------------------------
payment-webhook    python3.9   us-east-1  critical-eol     250d ago  python3.12
analytics-daily    python3.8   us-east-1  critical-eol     677d ago  python3.12
image-resize       python3.10  us-east-2  high               in 70d  python3.12
slack-notify       python3.11  us-east-1  low               in 312d  python3.12
order-fulfillment  python3.12  us-east-1  ok                      —  python3.12
legacy-etl         python3.7   eu-west-1  critical-eol     999d ago  python3.12

⚠ python3.9 reached EOL 250 day(s) ago. Next: `python-pivot codemod`
```

Add `--strict` for CI, `--format json|csv|md`, `--regions us-east-1,eu-west-1` for multi-region live scans.

### 2. Codemod your source

```bash
$ python-pivot codemod src/ --apply

▸ Python codemod · src/ · APPLY
  42 file(s) scanned
ℹ [rewrite] src/lib/config.py · collections-abc-imports · 1 hit(s)
ℹ [lint]    src/lib/legacy.py:12 · distutils-import — `distutils` removed in Python 3.12.
ℹ [lint]    src/handlers/webhook.py:8 · datetime-utcnow — `datetime.utcnow()` deprecated in 3.12.
ℹ [lint]    src/lib/plugins.py:4 · pkg-resources — `pkg_resources` slow and deprecated.

✓ 1 rewrite(s) across 1 file(s), 3 lint finding(s).
```

**Rewrites** (auto-fixed): `collections.Mapping` → `collections.abc.Mapping` (the named exports), etc.

**Lints** (flagged for human review, no auto-fix): `distutils`, `imp`, `@asyncio.coroutine`, `datetime.utcnow()`, `asyncio.get_event_loop()`, `typing.io/re` submodules, `unittest.makeSuite`, `pkg_resources`.

No pyupgrade-style over-rewriting. Lambda Lambda code is production code — we rewrite only what is mechanically safe.

### 3. Audit native wheels

```bash
$ python-pivot audit requirements.txt

▸ Native-wheel audit · requirements.txt
  [high]     numpy            declared===1.24.0  · needs >=1.26.0
      1.26+ ships cp312 wheels.
  [high]     cryptography     declared===40.0.0  · needs >=41.0.5
      41.0.5+ for cp312 (libssl3).
  [high]     pillow           declared===9.5.0   · needs >=10.1.0
  [high]     python-snappy    declared===0.6.1   · needs >=0.7.0
      0.7.0+ (2024-02-27) ships a pure-Python py3-none-any wheel built on `cramjam` — installs fine on cp312, no library swap needed.

⚠ 10 package(s) need attention before Python 3.12.
```

The curated table compares configured package baselines; it does not query PyPI,
resolve dependencies, or verify wheels for your target architecture. Packages
outside the table are not checked. `high` means the declared baseline precedes
the configured minimum; `low` means a baseline cannot be established from the
declaration and needs review. Markers are inspected across all declared
environments, rather than evaluated against the machine running the audit.

Supported input:

- Flat requirements files with named requirements, extras, version constraints,
  markers and comments. Includes, editable installs, installer options and
  hash/continuation files require a flat input instead.
- `pyproject.toml` using PEP 621 `project.dependencies` and every
  `project.optional-dependencies` group, with TOML single or double quotes.
- `Pipfile` `packages` and `dev-packages`, including inline version tables.

Dynamic and tool-specific dependency tables such as Poetry are not resolved.
Malformed or unsupported input exits 2 and does not emit a clean JSON array.
`--strict` exits 1 for findings; clean scans remain limited to the curated table.

### 4. Patch IaC

```bash
$ python-pivot iac infra/ --apply

▸ IaC patcher · infra/ · APPLY
  23 IaC candidate file(s) scanned
ℹ [rewrite] infra/template.yaml · sam-cfn-runtime · 8 hit(s)
ℹ [rewrite] infra/cdk/stack.ts · cdk-runtime-enum · 3 hit(s)
ℹ [rewrite] infra/terraform/main.tf · terraform-runtime · 5 hit(s)

✓ 16 rewrite(s) across 3 file(s).
```

Supports:
- **SAM / CloudFormation** — JSON and YAML Lambda `Properties.Runtime` and SAM `Globals.Function.Runtime`
- **CDK** (TS + Python) — `Runtime.PYTHON_3_9` enum
- **Terraform** — direct `runtime` attributes of `aws_lambda_function` in HCL and `.tf.json`
- **Serverless Framework** — AWS provider and direct function runtimes in YAML/JSON

Idempotent. Already-migrated resources and unrelated runtime settings are not
touched by the template editors. Replacements retain quotes, comments, unrelated
tags, and line endings. YAML supports block mappings and single-line flow
mappings; lists remain data. Runtime expressions, structural aliases/merge keys,
and multiline flow mappings require manual review. Detected input errors return
exit 2 before any file in the batch is written; this is not a full YAML/IaC
validator. CDK remains a
source-pattern rewrite; it does not resolve imports or prove deployment
compatibility. Preview without `--apply`, review the resulting diff, then
validate with your IaC toolchain.

### 5. Deploy with canary + auto-rollback

```bash
$ python-pivot deploy \
    --function payment-webhook \
    --alias live \
    --stages 5,25,50,100 \
    --dwell 60 \
    --alarm arn:aws:cloudwatch:us-east-1:1234:alarm:PaymentErrors \
    --apply

▸ Updating runtime of payment-webhook → python3.12
ℹ Waiting for update to settle…
▸ Publishing new version
✓ Published version 47
ℹ Previous stable version: 46
▸ Canary 5% → 47 (stable 46)
ℹ   dwelling 60s…
✓   alarm state: OK
▸ Canary 25% → 47 (stable 46)
ℹ   dwelling 60s…
✓   alarm state: OK
▸ Canary 50% → 47 (stable 46)
ℹ   dwelling 60s…
✗ Alarm arn:aws:…:PaymentErrors is in ALARM state — rolling back.
✓ Alias live reverted to 46
```

Requires `--alarm` with `--apply`. No alarm = no deploy. After each configured
dwell interval the command checks CloudWatch; an observed `ALARM` state triggers
an alias rollback. This is not continuous monitoring.

### 6. Manual rollback

```bash
$ python-pivot rollback --function payment-webhook --alias live --apply
▸ Rollback alias live on payment-webhook
ℹ Current alias version: 47
✓ Alias live now points at version 46
```

---

## Safety

- Every write operation defaults to **dry-run**.
- `scan` is strictly read-only (Lambda `ListFunctions` only).
- `deploy --apply` refuses to run without `--alarm`.
- Every stage of canary has automatic rollback built in.
- No telemetry. No network calls outside AWS. No LLM.

---

## Free and hosted options

The CLI is free and MIT-licensed. EOLkits is prepared to offer one paid product: a
server-gated [$299 repository evidence report](https://ntoledo319.github.io/EOLkits/audit/): static
source/IaC findings with exact observed file/line locations, limitations, and configured
references. It does not inspect an AWS account. Migration Pack and the previously
described hosted products are not for sale.

---

## Roadmap

- [ ] Lambda Layer compatibility scanner
- [ ] Lambda Extension Python version check
- [ ] AWS Lambda Powertools version compat matrix
- [ ] boto3 breaking-change scanner (deprecated parameters, removed API versions)
- [ ] GitHub Action template

---

## License

MIT. See [LICENSE](LICENSE).

---

## Primary sources

- [AWS Lambda runtime support policy](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)
- [Python 3.9 release schedule (PEP 596)](https://peps.python.org/pep-0596/)
- [Python 3.10 release schedule (PEP 619)](https://peps.python.org/pep-0619/)
- [Python 3.12 What's New](https://docs.python.org/3.12/whatsnew/3.12.html)
- [PyPI wheel compatibility tags](https://peps.python.org/pep-0425/)

*Built by [EOLkits Kits](https://github.com/ntoledo319/EOLkits). Tracked AWS deprecations deserve tested migration paths.*
