# Evidence ledger

Only observed evidence belongs here. Forecasts are in OPPORTUNITIES.md and PLAN.md.

## Commercial baseline — August 22, 2026

- Collected revenue recorded by the workspace: $0.
- Paid reports recorded as delivered: 0.
- Profit gap: $4,000.
- Stripe dashboard has not been independently reconciled in this cycle; the
  owner must archive legacy links and confirm whether any unrecognized charge or
  refund exists before checkout opens.
- GitHub repository observed at 1 star and 0 forks:
  https://github.com/ntoledo319/EOLkits
- Existing GitHub Marketplace Action observed live at v1.1.0:
  https://github.com/marketplace/actions/rupture-aws-deprecation-check
- DEV profile observed with 25 posts and 0 comments:
  https://dev.to/ntoledo319
- No EOLkits result was observed in Visual Studio Marketplace search. This is an
  inference that the extension is not published, not a marketplace account audit.

## Live-surface baseline — August 21–22, 2026

- https://eolkits.com returned the old site, advertising Migration Pack,
  Organization License, Drift Watch, unsupported blast-radius/cost claims, and
  done-for-you PR fulfillment.
- That live surface is unsafe and is not evidence that those products work.
- The repaired static build presents only the free tools and the server-gated
  $299 evidence report. Deployment evidence must be appended after the public
  URL serves the repaired copy.

## Verification evidence — August 22, 2026

- al2023-gate: 49 passed.
- python-pivot: 50 passed.
- Grace Audit API: 72 passed, including an anchored-window rate-limit regression.
- Audit PDF/HTTP runner: 14 passed after dormant migration-PR code removal.
- Generated web: 18 passed, including link/source integrity, false-claim and
  closed-product tombstones, Node.js 22 timeline, privacy, trailing-whitespace,
  and GitHub Pages/API-origin regressions.
- lambda-lifeline on Node.js 24: 28 passed, including nodejs22.x-to-nodejs24.x
  planning and multiline stream-constructor coverage.
- Retired Worker tombstone: TypeScript build plus 9 passed.
- lambda-lifeline randomized properties: 3 passed across 60 generated examples;
  this gate found and drove the Node.js 14 IaC regression repair.
- VS extension: TypeScript compile, ESLint 10, scanner behavior suite, minimal
  11-file/19.81-KiB VSIX, and archive integrity passed.
- GitHub Action: clean fixture and findings fixture both produced the expected
  outputs under Node.js 24.
- Three scanners and the 84-file generated site were deterministic across
  consecutive runs.
- Python formatting/lint/type checks: Black, Ruff, and mypy passed; all ten
  workflow/rule YAML files parsed and repository shell scripts passed ShellCheck.
- Both Python kits built wheel and source archives with current SPDX license
  metadata and no Setuptools deprecation warning. lambda-lifeline's npm package
  dry-run contains 24 intended release files and excludes tests/cache artifacts.
- Dependency checks: both hash-locked Python graphs reported no known
  vulnerabilities; all three production Node graphs and the full VS development
  graph reported zero vulnerabilities; 98 non-development Node lock records had
  no missing or forbidden license declaration. The source secret-pattern scan
  found no secret-shaped token.
- AWS claim corrections: the unsupported universal IMDSv1 deadline is retired;
  Node.js 22 is represented as a projected 2027 timeline, Node.js 24 is the
  bounded tool target, and provider dates are no longer presented as proof of
  workload-specific migration impact.
- The GitHub Pages project-path artifact was built locally and checked: static
  links use `/EOLkits`, while status, scan, widget, and pageview events retain
  the `https://eolkits.com` API origin.
- Migration Pack, organization-license, partner, and generic scanner research
  forms were removed; the legacy license inquiry now returns 410. These are
  release facts, not market signal.
- Container builds are delegated to remote GitHub CI because a local Docker
  build would write daemon state outside the workspace jail.

Tests and commits are release evidence, not market signal.

## Events that count after launch

Record timestamp, source, and observed value for:

1. collected dollars, processor fees, and refunds;
2. paid reports successfully delivered;
3. valid checkout starts and completed purchases;
4. qualified Audit page views;
5. external GitHub Action runs/listing traffic;
6. VS installs and attributable Audit views.

Do not put projections, synthetic status values, commit counts, generated
benchmarks, or unverified analytics in this ledger.
