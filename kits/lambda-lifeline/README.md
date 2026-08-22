# lambda-lifeline

> Check, preview, and execute guarded AWS Lambda Node.js runtime migration steps. Review every proposed change and use your own production release controls.

**Official AWS source:** [Lambda runtimes docs](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)

| Runtime | Phase 1 — patches stop | Phase 2 — block create | Phase 3 — block update (hard) |
|---|---|---|---|
| `nodejs16.x` | Jun 12, 2024 ✗ past | Feb 1, 2027 | **Mar 3, 2027** |
| `nodejs18.x` | Sep 1, 2025 ✗ past  | Feb 1, 2027 | **Mar 3, 2027** |
| `nodejs20.x` | **Apr 30, 2026**    | Feb 1, 2027 | **Mar 3, 2027** |
| `nodejs22.x` | Apr 30, 2027 (projected) | Jun 1, 2027 | **Jul 1, 2027** |

AWS marks future runtime dates as subject to change. Recheck the linked table before scheduling a production migration.

---

## What this kit does

Eight commands cover specific parts of a Node.js Lambda migration:

| Step | Command | What it does |
|---|---|---|
| 1 | `scan` | Lists Lambda functions visible to the active credentials in the selected regions and flags configured runtimes |
| 2 | `codemod` | Rewrites `import … assert` → `with`, flags `Buffer` negative-index & stream HWM risks |
| 3 | `audit` | Scans `package.json` for configured native-binary packages, reports a conservative version baseline, and calls out the required Node.js 24 upstream/target-runtime verification |
| 4 | `certs` | Sets `NODE_EXTRA_CA_CERTS=/var/runtime/ca-cert.pem` on functions that connect to RDS or other Amazon-managed TLS endpoints |
| 5 | `iac` | Patches supported old Node runtime references in SAM, CloudFormation, CDK (TS/JS), Terraform, and Serverless Framework files to `nodejs24.x` |
| 6 | `plan` | Prints a staged canary deploy plan (5 → 25 → 50 → 100% over weighted alias routing) |
| 7 | `deploy` | Executes the plan with a CloudWatch alarm guard. If the alarm trips at any stage, it auto-rollbacks to the last stable version |
| 8 | `rollback` | Manual rollback of a function alias to the previous version |

File and AWS mutations require `--apply`. The tested rewrite rules are idempotent. Validate the generated plan, alarms, permissions, and rollback behavior in a non-production environment first.

---

## Why this exists

On **April 30, 2026** AWS stops applying security patches to `nodejs20.x` Lambda functions. AWS delayed the hard block dates into the synchronized Q1-2027 cluster: on **February 1, 2027** you can't create new `nodejs20.x` functions, and on **March 3, 2027** you can't even update code or config on the existing ones — they become frozen until you migrate.

The official AWS Health emails tell you *that* it's happening. This kit helps you
identify which functions visible to a selected credential profile are affected,
which configured `package.json` dependencies may have Node 24 compatibility risk,
and which supported IaC files contain old runtime references. Run `scan` once per
account/profile and every relevant region; it does not enumerate an AWS
Organization automatically.

That's this kit.

---

## Quickstart

```bash
# 1. Clone & install (zero deps for offline use; AWS SDK only for live scan/deploy)
git clone https://github.com/ntoledo319/EOLkits.git
cd EOLkits/kits/lambda-lifeline
npm ci        # only needed for scan (live mode), certs, deploy, rollback

# 2. Inventory your fleet
./bin/cli.mjs scan --regions us-east-1,us-west-2,eu-west-1 --out scan.json

# 3. Fix your code (dry-run first, then apply)
./bin/cli.mjs codemod --path ./src
./bin/cli.mjs codemod --path ./src --apply

# 4. Audit native dependencies
./bin/cli.mjs audit --path . --strict

# 5. Patch your IaC
./bin/cli.mjs iac --path ./infra --apply

# 6. Preview the deploy plan
./bin/cli.mjs plan --function orders-ingest

# 7. Ship it with alarm guard
./bin/cli.mjs deploy --function orders-ingest --apply \
    --alarm arn:aws:cloudwatch:us-east-1:123456789012:alarm:orders-5xx
```

## Sample output

Run against the included fixture. The `Days` value is computed from the run date,
so it is shown as `…` below:

```
$ lambda-lifeline scan --fixture test/fixtures/lambda-inventory.json
ℹ Scanned 7 functions · 1 healthy · 6 at risk

Function                             Runtime        Region         Severity           Days   Target
---------------------------------------------------------------------------------------------------
api-orders-ingest                    nodejs20.x     us-east-1      high               …      nodejs24.x
billing-webhook-processor            nodejs18.x     us-east-1      high               …      nodejs24.x
legacy-cron-cleanup                  nodejs16.x     us-west-2      high               …      nodejs24.x
events-api-current                   nodejs22.x     us-east-1      medium             …      nodejs24.x
report-generator                     python3.10     us-east-1      medium             …      python3.12
ruby-legacy-processor                ruby3.2        us-east-1      high               …      ruby3.4
```

```
$ lambda-lifeline codemod --path examples/sample-app
ℹ [lint]    examples/sample-app/src/handler.mjs · buffer-negative-index · 1 hit(s)
ℹ [lint]    examples/sample-app/src/handler.mjs · streams-hwm · 1 hit(s)
✓ 1 file(s) with 2 edit(s). Preview only.
⚠ 2 lint finding(s) need human review (cannot auto-fix safely).
```

```
$ lambda-lifeline audit --path examples/sample-app
  ⚠ sharp                        UPGRADE    declared 0.32.6  →  need ≥ 0.33.0
  ⚠ bcrypt                       UPGRADE    declared 5.0.1   →  need ≥ 5.1.1
  ⚠ better-sqlite3               UPGRADE    declared 10.0.0  →  need ≥ 11.0.0
  ✗ node-sass                    REPLACE    replace this dep
  ✗ grpc                         REPLACE    replace this dep
⚠ 5 native dep(s) need action before Node 24.
```

```
$ lambda-lifeline iac --path examples/sample-app --apply
ℹ [SAM/CFN]   template.yaml         · 3 runtime ref(s): nodejs20.x, nodejs18.x, nodejs16.x
ℹ [Terraform] infra/main.tf         · 2 runtime ref(s): nodejs20.x, nodejs18.x
ℹ [CDK]       cdk/stack.ts          · 2 runtime ref(s): NODEJS_18_X, NODEJS_20_X
✓ 3 file(s) · 7 runtime ref(s) updated.
```

## Safety

- **Dry-run is the default.** Every command that mutates anything requires `--apply`.
- **Deploys require a CloudWatch alarm ARN.** The kit will refuse to run a live deploy without one, because we want auto-rollback to actually work.
- **Rewrites are minimal and version-control-friendly.** Codemods touch only the bytes they need to. Diffs are readable.
- **Idempotent.** Run `iac --apply` twice and the second run is a no-op.
- **Tested.** `npm test` runs the checked-in 28-case behavioral suite. Live AWS
  mutation still requires your own non-production validation and release review.

```bash
npm test
# tests 28  pass 28  fail 0
```

---

## What the free tier gets you (this repo)

- All 8 CLI commands, full source
- Test suite
- Sample SAM + Terraform + CDK app with before/after diffs
- GitHub Actions CI template
- MIT license — use it however you want

## Hosted option

This CLI is free and MIT-licensed. The only paid product currently offered is a
server-gated [$299 repository evidence report](https://eolkits.com/audit): static
source/IaC findings with exact observed file/line locations, limitations, and cited
sources. It does not inspect an AWS account. Migration Pack and the previously
described hosted products are not for sale.

---

## Roadmap

Future runtime rules are added only after their source dates and behavior have
tests. Proposed Node and Ruby expansions are not committed products.

---

## Evaluate alternatives

Tool capabilities and pricing change. Compare this repository's source and tests
with each alternative's current official documentation instead of relying on a
stale feature matrix.

---

## License

MIT. Use it commercially, fork it, rewrite it. If it saves your weekend, an [eolkits.com/audit](https://eolkits.com/audit) purchase funds the next kit.

## Support

- GitHub Issues: bug reports, feature requests
