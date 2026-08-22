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
- Retired Worker tombstone: TypeScript build plus 10 passed, including inert
  acknowledgement of the retained legacy Queue consumer.
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
  Pack and Drift Watch claims. HQ-3 remains mandatory; the custom domain is not
  counted as repaired or ready for checkout.

## Distribution release evidence — August 22, 2026

- The public branch `https://github.com/ntoledo319/EOLkits/tree/v2` resolves to
  the fully verified release-ledger commit `3ea1a169849e913b3c4086c0ff8251d24e1400d9`.
  The raw `action.yml` hash matched that commit, so
  `uses: ntoledo319/EOLkits@v2` is an immediately valid install ref.
- Commit `9d369ccbb516f5578665f3edfaae618c1a88b111` added a one-shot, idempotent
  Marketplace draft workflow. Run
  https://github.com/ntoledo319/EOLkits/actions/runs/32589265862 passed and its
  authenticated log recorded creation of the private v2.0.0 draft targeting
  that commit. The same commit's release-surface
  (https://github.com/ntoledo319/EOLkits/actions/runs/32589265886), determinism
  (https://github.com/ntoledo319/EOLkits/actions/runs/32589265872), property
  (https://github.com/ntoledo319/EOLkits/actions/runs/32589265838), and built-in
  Pages (https://github.com/ntoledo319/EOLkits/actions/runs/32589265194) runs also
  passed.
- The Marketplace page still reports v1.1.0 and displays its stale release copy.
  A release branch and private draft do not update the listing; only the owner's
  Marketplace checkbox, agreement, 2FA, and publish action count as publication.
- These are distribution/release facts, not external runs, visits, purchases, or
  revenue. Collected revenue remains $0.

## Verified acquisition routing — August 22, 2026

- Commit `8748cf6a34bb18c3c5cdecd5bb98f5305f0eb997` moved repository, Action,
  kit-package, and VS extension acquisition links from the obsolete custom-domain
  pages to `https://ntoledo319.github.io/EOLkits/`. The static smoke monitor now
  probes Pages separately from the optional `eolkits.com` API origin.
- Local verification passed the real Action findings fixture and report-link
  assertion, VS compile/lint/scanner tests and minimal VSIX packaging, both
  Python wheel/sdist builds, all 28 Lambda kit cases, Node package dry-run, YAML
  parsing, ShellCheck, and a stale-acquisition-link gate.
- Remote runs passed: release surfaces
  https://github.com/ntoledo319/EOLkits/actions/runs/32589723873,
  determinism https://github.com/ntoledo319/EOLkits/actions/runs/32589723804,
  properties https://github.com/ntoledo319/EOLkits/actions/runs/32589723777,
  built-in Pages https://github.com/ntoledo319/EOLkits/actions/runs/32589722988,
  and Marketplace-draft synchronization
  https://github.com/ntoledo319/EOLkits/actions/runs/32589723779.
- The draft workflow log recorded synchronization of private v2.0.0 to the exact
  `8748cf6a` commit. After every gate passed, the public `v2` branch advanced
  without force to the same commit. A public raw-file probe confirmed its Action
  report uses the Pages Audit URL and no obsolete `eolkits.com/audit` link.
- The public Marketplace page still reports v1.1.0. No external Action run,
  qualified visit, checkout, purchase, delivery, or revenue was observed by this
  release work.

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

## GRACE static-feed recovery — August 22, 2026

- Public DNS resolved `eolkits.com` directly to `15.204.209.97`, the documented
  GRACE host. Caddy served the home page with `Last-Modified: Sat, 22 Aug 2026
  07:17:02 GMT`.
- The remote `marketing-machine-v2` branch advanced at 06:14:56 UTC to commit
  `8fbbbf654cafccfbe2f7415d6be0b3c57179c634`; its public content was still the
  retired multi-product tree. The one-hour sequence plus the installed cron's
  documented branch and webroot is evidence that the daily static deploy remains
  active. It is not evidence that the API redeploys from Git pushes.
- The remote branch was not an ancestor of repaired main because it contained
  one additional date-fix commit. Commit
  `c311215121fe3a76241632500154ac457d964eab` merged that tip and main without
  force while selecting the exact verified main tree
  `0ceb6ec8d4576d4dad568765a8cd251f2cb5f1b5`.
- The GRACE root-domain build completed locally and all 18 generated-site tests
  passed with `EOLKITS_BASE_PATH` empty and both site/API origins set to
  `https://eolkits.com`. The committed Pages variant was regenerated afterward
  and matched Git with no diff.
- `.github/workflows/verify-grace-static.yml` now checks the custom domain after
  the observed daily deploy window for the single $299 offer, unavailable
  product tombstones, fail-closed Audit form, root-domain links/canonicals, and
  absence of retired $1,499/$14,999 prices.
- At the time of this branch repair, the public custom domain still served the
  obsolete products and `/api/capabilities` still returned 404. No checkout,
  purchase, delivery, qualified visit, or revenue was observed. Collected
  revenue remains $0.

## Legacy Cloudflare commerce retirement — August 22, 2026

- Before repair, the public pre-rename Worker at
  `https://rupture-worker.rupture-kits.workers.dev/status.json` returned a
  healthy production status with Stripe in live mode. This was an unsafe bypass,
  not revenue evidence.
- Main commit `90c7b147851db7b3c9945f0c7080a164930c8f7b` contains the bounded
  retirement workflow and dedicated old-account target. Successful run
  https://github.com/ntoledo319/EOLkits/actions/runs/32591848083 tested the
  replacement, deployed it to the exact historical `rupture-worker`, and proved
  the public closure after edge propagation.
- Independent public probes observed `{"ok":false,"retired":true}` at `/health`
  and HTTP 410 at `/checkout`, `/api/checkout`, `/pack/install`, and
  `/webhook/stripe`. The old direct payment, App-install, and webhook surface is
  closed.
- The old-account token could not see a unique `eolkits.com` zone, so it changed
  no Worker route. Public DNS resolves `eolkits.com` directly to the GRACE IP,
  making a Cloudflare Worker route non-invocable today; the deployed tombstone
  also fails closed if routing changes later.
- No checkout, purchase, report delivery, qualified visit, or revenue was
  observed. Collected revenue remains $0.
