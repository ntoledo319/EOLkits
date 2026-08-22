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

## Remote publication evidence — August 22, 2026

- Repaired main commit: https://github.com/ntoledo319/EOLkits/commit/85c9f43e330a668779e1de60c80ed5023a90129d
- The remote tree SHA exactly matched the verified local tree SHA
  `cdd26962ff0e7c93cffcd7c2772b43bf2422c3a5`; main advanced without force and
  retains both prior main and the prior working branch as parents.
- Initial push workflows all completed successfully: release surfaces
  https://github.com/ntoledo319/EOLkits/actions/runs/32556971966, Pages
  https://github.com/ntoledo319/EOLkits/actions/runs/32556971977, determinism
  https://github.com/ntoledo319/EOLkits/actions/runs/32556971979, properties
  https://github.com/ntoledo319/EOLkits/actions/runs/32556971965, and GitHub's
  Pages build https://github.com/ntoledo319/EOLkits/actions/runs/32556970104.
- The first public Pages probe returned 200 but exposed a race: the legacy
  branch-source deployment overwrote the custom artifact with root-domain links.
  The follow-up commit
  https://github.com/ntoledo319/EOLkits/commit/f4ef711e022ce032a31d15f2fb0ab845b2225e91
  made committed `docs/` the `/EOLkits` artifact and made the GRACE ship script
  build the root-domain variant immediately before rsync. The custom Pages run
  https://github.com/ntoledo319/EOLkits/actions/runs/32557385166 and built-in
  Pages run https://github.com/ntoledo319/EOLkits/actions/runs/32557384585 both
  passed.
- The release-surface run on that follow-up failed only because its stale-URL
  guard still rejected the now-intentional GitHub Pages origin; its other twelve
  jobs, including both container builds, passed. Commit
  https://github.com/ntoledo319/EOLkits/commit/b9cf566d0c39eb9b7eb831a575bd7618a2984d8d
  corrected the guard. Its replacement release run
  https://github.com/ntoledo319/EOLkits/actions/runs/32557638726,
  determinism run https://github.com/ntoledo319/EOLkits/actions/runs/32557638717,
  property run https://github.com/ntoledo319/EOLkits/actions/runs/32557638719,
  and built-in Pages run
  https://github.com/ntoledo319/EOLkits/actions/runs/32557638168 all passed.
- The final public probe returned 200 for the Pages home, scanner, and retired
  Migration Pack route. Navigation is prefixed with `/EOLkits`; scanner Audit
  links use `https://ntoledo319.github.io/EOLkits`; status, events, and scanner
  API calls use `https://eolkits.com`; and the retired Pack page has no checkout,
  account, or waitlist. This is release evidence, not a visit or demand event.
- A separate public probe of `https://eolkits.com/` still found the old Migration
  Pack and Drift Watch claims. HQ-4 remains mandatory; the custom domain is not
  counted as repaired or ready for checkout.

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
