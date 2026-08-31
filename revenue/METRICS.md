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
- The initial EOLkits-name search missed the stable technical identity. Exact
  Marketplace API lookup later found public `rupture.rupture-vscode` v1.0.0;
  the recovered baseline is recorded below and supersedes that inference.

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

## GRACE capability and exact Stripe-retirement release — August 22, 2026

- The read-only repository capability audit
  https://github.com/ntoledo319/EOLkits/actions/runs/32592156556 reported
  `deploy_transport=false` and `runtime_bundle=false`. No host, account, token,
  key, or secret value was printed. This proves the known GitHub configuration
  cannot authenticate to GRACE; it does not prove no owner credential exists.
- Main commits
  https://github.com/ntoledo319/EOLkits/commit/ca9d41f313879ca1cd15488de12a6f673aac33e3,
  https://github.com/ntoledo319/EOLkits/commit/fdbea72db89a8a7fc519d066aea828e316863198,
  and
  https://github.com/ntoledo319/EOLkits/commit/e4109e3ebdb4623ba4e7cbced01c3fab364dc17f
  added and hardened the owner-gated exact Stripe retirement. Its Worker build,
  39 focused cases, Wrangler dry-run, YAML parse, ShellCheck, diff check, and
  independent security review passed. Race tests cover open-to-complete Checkout
  transitions and schedule-to-subscription transitions.
- The final commit's release, determinism, property, Pages, and tombstone runs
  passed:
  https://github.com/ntoledo319/EOLkits/actions/runs/32594198744,
  https://github.com/ntoledo319/EOLkits/actions/runs/32594198725,
  https://github.com/ntoledo319/EOLkits/actions/runs/32594198691,
  https://github.com/ntoledo319/EOLkits/actions/runs/32594197817, and
  https://github.com/ntoledo319/EOLkits/actions/runs/32594198743.
- An independent public probe after those runs observed the exact normal
  tombstone JSON at `rupture-worker.rupture-kits.workers.dev/health`, HTTP 410
  on checkout, App-install, and webhook paths, and HTTP 410 for an unauthenticated
  POST to the temporary retirement-admin path.
- The production Stripe workflow is manual, requires the repository owner's
  actor identity plus an exact confirmation, and has not run. Therefore no
  Price, Payment Link, Checkout Session, subscription, schedule, charge, refund,
  or Stripe-key state is recorded as changed or reconciled by this release.
  Public rendering of the historical `buy.stripe.com` links also remains
  unverified. Collected revenue remains $0 and delivered paid reports remain 0.

## Qualified-demand baseline — 2026-08-22T20:21:59Z

- GitHub Issues API observation: 0 actual issues in the repository (pull
  requests excluded), therefore 0 `$299 Audit interest` submissions and 0
  distinct external qualified authors.
- GitHub public code-search observation for the exact install string
  `ntoledo319/EOLkits@v2`, excluding this repository: 0 observed external public
  references. Private repositories and indexing delay are invisible, so this is
  a lower bound, not a claim of zero use.
- Exact Stripe retirement workflow runs: 0. Public v2.0.0 releases: 0. The
  Marketplace remains v1.1.0. These are availability facts, not demand.
- Paid reports delivered: 0. Collected revenue: $0. Collected profit: $0.
- The structured issue form and read-only acquisition-evidence workflow are
  locally verified but not yet public at this ledger point; they become a live
  measurement surface only after publication and a green remote run.

## Qualified-demand surface published — 2026-08-22T20:34:10Z

- Main commit
  https://github.com/ntoledo319/EOLkits/commit/5305f1fef6641659811ccc2133ddf1dde53c8a43
  published the exact locally verified tree. Acquisition-evidence run
  https://github.com/ntoledo319/EOLkits/actions/runs/32596830945 passed and
  retained artifact `acquisition-evidence-32596830945` for 14 days. The artifact
  is a public-lower-bound observation; it is not a purchase record.
- The same commit's release, determinism, property, custom Pages, and built-in
  Pages runs passed:
  https://github.com/ntoledo319/EOLkits/actions/runs/32596830957,
  https://github.com/ntoledo319/EOLkits/actions/runs/32596830966,
  https://github.com/ntoledo319/EOLkits/actions/runs/32596830946,
  https://github.com/ntoledo319/EOLkits/actions/runs/32596830950, and
  https://github.com/ntoledo319/EOLkits/actions/runs/32596830480.
- Marketplace-draft run `32596830981` failed at its local release-copy assertion:
  Bash source correctly escaped `$299`, while the validation searched for the
  rendered text. Commit
  https://github.com/ntoledo319/EOLkits/commit/db32bdfb99b0837bb4975a5cebb9caaf633f3c34
  corrected the assertion. Its draft, release, determinism, property, and
  built-in Pages runs all passed:
  https://github.com/ntoledo319/EOLkits/actions/runs/32596973048,
  https://github.com/ntoledo319/EOLkits/actions/runs/32596973045,
  https://github.com/ntoledo319/EOLkits/actions/runs/32596973044,
  https://github.com/ntoledo319/EOLkits/actions/runs/32596973051, and
  https://github.com/ntoledo319/EOLkits/actions/runs/32596972524.
- Public probes returned HTTP 200 for the Audit, scanner, and tracking assets;
  observed the `$299` issue CTA and nonbinding warning; observed capability-gated
  fetch telemetry with no local storage or referrer collection; and confirmed
  the GitHub issue form requires authentication. The public `v2` ref advanced
  without force to `db32bdfb`, and its raw Action contains the findings-only
  qualified-interest link.
- No external qualified issue, public external `@v2` code reference, checkout,
  purchase, delivery, or collected dollar was observed. Revenue and profit
  remain $0.

## Bounded search notification — 2026-08-22T20:49:09Z

- Main commit
  https://github.com/ntoledo319/EOLkits/commit/951fd4b64d1119d0a427c9986d6d1692818aa4be
  has exact tree `b21d1e82468040bbbdf8d55d2bc1c911849a5ee9` and adds the
  changed-URL IndexNow workflow plus a permanent generated-site ownership/scope
  regression. The generated-site suite now reports 24 passing cases.
- IndexNow run
  https://github.com/ntoledo319/EOLkits/actions/runs/32597777674 passed. Its
  executable contract requires a live matching ownership key, 1–10,000 unique
  URLs under `https://ntoledo319.github.io/EOLkits/`, and an IndexNow HTTP 200 or
  202 response. Because the publishing diff changed no generated HTML, this
  bootstrap run selected all 51 canonical sitemap URLs. This proves protocol
  receipt only—not crawling, indexing, ranking, visits, leads, or revenue.
- The same commit's release, property, determinism, custom Pages, and built-in
  Pages runs all passed:
  https://github.com/ntoledo319/EOLkits/actions/runs/32597777615,
  https://github.com/ntoledo319/EOLkits/actions/runs/32597777613,
  https://github.com/ntoledo319/EOLkits/actions/runs/32597777612,
  https://github.com/ntoledo319/EOLkits/actions/runs/32597777622, and
  https://github.com/ntoledo319/EOLkits/actions/runs/32597777192.
- Acquisition run
  https://github.com/ntoledo319/EOLkits/actions/runs/32597777625 retained artifact
  `acquisition-evidence-32597777625` (ID `9482023122`, SHA-256 digest
  `c7dd09d326a184669da72935350ad0f5467b033e8b36a457c654c65467aa6b77`). At
  20:49:07 UTC it observed 0 qualified-interest issues, 0 distinct external
  authors, 0 within-30-day windows, 0 external public `@v2` code references with
  search available, no public v2.0.0 release, 1 star, and 0 forks.
- Exact Stripe-retirement runs remain 0; scheduled GRACE-verifier runs remain 0;
  the Marketplace remains v1.1.0; `eolkits.com` still serves the obsolete site
  with `/api/capabilities` returning 404. Paid deliveries, collected revenue,
  and collected profit remain 0 / $0 / $0.

## Engine-generated proof published — 2026-08-22T22:42:43Z

- Feature commit
  https://github.com/ntoledo319/EOLkits/commit/bffb335acca35a9a3cf2f48771198327ceab7a61
  published remote tree `7fd7a81a73e588fff43dd93314c2a60053b9fde6`,
  exactly matching the locally verified product tree. It added a genuine
  engine-generated fictional report, detector/DoS hardening, renderer/test
  locks, truthful privacy/scope copy, safer static deployment, and individual
  archive guards on all 25 DEV source files.
- The first custom Pages run
  https://github.com/ntoledo319/EOLkits/actions/runs/32602860382 and release run
  https://github.com/ntoledo319/EOLkits/actions/runs/32602860359 failed because a
  GitHub-hosted runner's native font/PDF stack serialized an otherwise matching
  WeasyPrint report to different bytes. Determinism `32602860366`, properties
  `32602860404`, built-in Pages `32602860212`, IndexNow `32602860388`, acquisition
  `32602860363`, Marketplace-draft `32602860373`, and status smoke
  `32602912166` passed. The failures are recorded release evidence, not hidden.
- Follow-up commit
  https://github.com/ntoledo319/EOLkits/commit/9c231b58c5f2af2ab671a19b2ebd01a8ae475c9a
  published exact final tree `8a25da73a1dc8c3c9107c76e7a20d87cc620cd98`.
  The portable gate preserves the checked-in PDF's exact hash and compares the
  fixture, page count, template/rule versions, findings, evidence fingerprint,
  and every other renderer-independent engine field. Its replacement release
  https://github.com/ntoledo319/EOLkits/actions/runs/32603025003, determinism
  https://github.com/ntoledo319/EOLkits/actions/runs/32603025004, properties
  https://github.com/ntoledo319/EOLkits/actions/runs/32603025011, custom Pages
  https://github.com/ntoledo319/EOLkits/actions/runs/32603024985, and built-in
  Pages https://github.com/ntoledo319/EOLkits/actions/runs/32603024375 all passed.
- Public probes returned the expected release marker and HTTP-served artifacts:
  `application/pdf` at 29,392 bytes, `application/x-zip-compressed` at 850 bytes,
  and `application/json` at 1,145 bytes. Their observed SHA-256 values were:
  PDF `855c793c8b2735f54fad08465f05c50943cb7908fd194b43dacf0eca9c423d9a`,
  ZIP `3fd7c4f6cfdb27d436399a0a639d4990303030839a0a338bb343a1ef12031b67`,
  and manifest `8ad77bb90851ec9ec1ae893118bb3efca69d4545e72ee179915b957222396a58`.
  The manifest reports 4 PDF pages, 4 findings, 5 evidence records, 4 scanned
  files, 1 skipped README, fictional=true, and verification_registered=false.
- Local final checks recorded 33 runner cases and 32 generated-site cases,
  deterministic sample validation, 74 API cases, 49 al2023-gate cases, 50
  python-pivot cases, 28 lambda-lifeline cases, 39 Worker cases, Action fixtures,
  VS compile/lint/rule/package gates, Ruff/Black/mypy, YAML/ShellCheck, clean
  Python/Node vulnerability audits, a clean high-confidence secret scan, and
  qpdf/content/visual inspection of all four PDF pages. The independent final
  review returned `NO PUBLISH BLOCKER` after one binary-archive copy correction.
- Public `main` contains product commit `9c231b58`, and `v2` resolves to it.
  Documentation-ledger commit `48b6f2af` subsequently passed release run
  `32603425198`, determinism `32603425199`, properties `32603425194`, and
  built-in Pages `32603424362`; ledger-only descendants do not alter the product
  tree. Marketplace-draft run
  `32602860373` synchronized private v2.0.0 to feature commit `bffb335a`; the
  final follow-up changes only renderer-portability tests, so Action bytes are
  unchanged. The public Marketplace page still reports v1.1.0.
- The GRACE source feed advanced without force to two-parent commit
  `0780909c938bf6acb0fe01ed1aad1c83662b5140`, whose tree exactly matches final
  main. At this observation, `eolkits.com` still contained Migration Pack and
  Drift Watch copy and `/api/capabilities` returned 404; checkout is not live.
- GitHub exposed 0 actual issues (pull requests excluded), 1 star, and 0 forks.
  No qualified issue, checkout, purchase, report delivery, refund, or collected
  dollar was observed. Revenue / profit / target gap remain $0 / $0 / $4,000.

## Existing VS distribution recovered — 2026-08-22T23:02:30Z

- An exact public Visual Studio Marketplace gallery query returned
  `rupture.rupture-vscode`, display name “Rupture - AWS Deprecation Scanner,”
  version 1.0.0, published `2026-05-02T22:02:07.783Z`, last updated
  `2026-05-02T22:06:15.09Z`, with 101 cumulative installs and 162 downloads.
  The same query returned zero extensions for `eolkits.eolkits-vscode`.
- Historical GitHub Actions run
  https://github.com/ntoledo319/EOLkits/actions/runs/25262940459 completed its
  package and publish steps successfully against commit `8e6e3ad3`, whose
  manifest identity was `rupture.rupture-vscode`. Its expired logs returned HTTP
  410, so no secret value or unsupported log detail is claimed.
- The code at that published commit routes both Audit actions to
  `https://ntoledo319.github.io/Rupture/audit`; a live probe returned HTTP 404.
  This establishes a broken handoff in the existing release, not a visit count
  or proof that an installed user clicked it.
- The local v1.1.0 candidate preserves the stable listing identity and EOLkits
  display branding; retains legacy `rupture.*` command activation/registration;
  gives explicitly configured legacy settings fallback priority only when no
  explicit `eolkits.*` value exists; and routes findings to the verified Pages
  Audit plus a public, nonbinding qualified-interest form. The measurement job
  now reports VS-attributed issues and distinct external authors separately.
- TypeScript, ESLint 10, scanner behavior, identity/legacy-setting regressions,
  and packaging passed. The inspected 12-file local VSIX is 21,356 bytes with
  SHA-256 `73cad6c4d50876a679ec6c8e46cdd96c34f8d2a571269d8c647c6011e91270b1`.
  This is a local build artifact; Marketplace publication was not inferred from it.
- The observed 100–101 install-counter range and 162 downloads are the historical
  V1 baseline range, not new EOLkits conversions. Observed VS-attributed
  qualified issues, paid reports,
  collected revenue, and profit remain 0 / 0 / $0 / $0.

## Repository-side VS recovery published — 2026-08-22T23:14:55Z

- Main commit
  https://github.com/ntoledo319/EOLkits/commit/a9cdcaeb40637d1f58f7539e80a16ec569be6704
  published exact tree `99136547cecd5a1ee638174dd95a29a919c9889e`,
  matching the locally verified candidate byte-for-byte.
- Full release run
  https://github.com/ntoledo319/EOLkits/actions/runs/32604619029 passed every job,
  including the fresh `npm ci && npm test && npm run package` VS extension job,
  both container builds, dependency audit, lint/type checks, every kit, the
  runner, API, Worker, web build, and Action fixtures. Determinism
  `32604619039`, properties `32604619066`, Marketplace draft `32604619021`, and
  built-in Pages `32604618393` also passed.
- Acquisition run
  https://github.com/ntoledo319/EOLkits/actions/runs/32604619185 passed and wrote
  artifact `acquisition-evidence-32604619185` (ID `9483794445`, 399 bytes,
  digest `sha256:304becb0e19b4e5098745141ff66d8b850ba211892b69c157502fa03e2d2657c`).
  A direct public issue probe still found 0 actual issues and 0 Audit-interest
  issues.
- A follow-up Marketplace query still returned public v1.0.0, 162 downloads,
  and an install counter of 100 rather than the prior query's 101. Treat the
  counter as approximate and set the real post-update baseline only after HQ-6.
  No publish workflow was dispatched in this cycle.
- Marketplace v1.1.0, paid reports, collected revenue, and profit remain
  not published / 0 / $0 / $0.

## Release-gate reconciliation — 2026-08-22T23:28:01Z

- Green Marketplace-draft run
  https://github.com/ntoledo319/EOLkits/actions/runs/32604619021 logged creation
  of the canonical private v2.0.0 draft at
  https://github.com/ntoledo319/EOLkits/releases/tag/untagged-0866963caf3f06db98a1,
  targeting commit `a9cdcaeb40637d1f58f7539e80a16ec569be6704`. The
  owner queue's prior `untagged-db9a...` URL was stale. A local exact diff found
  no differences between that target and public `v2` commit `9c231b58` under
  `action.yml` or `apps/github-action/`.
- The VS publication workflow had only a branch check around use of `VSCE_PAT`.
  The reviewed candidate now requires repository owner `ntoledo319` as dispatch
  and triggering actor, exact repository/main ref, and typed version-specific
  confirmation before source checkout or publisher-secret use. It checks out
  exact green release commit `a9cdcaeb` with persisted Git credentials disabled
  and re-verifies HEAD before packaging. This is release authorization
  hardening, not a Marketplace publication or demand event.
- Public VS remains v1.0.0 with 162 downloads and an approximately 100-install
  counter. Exact Stripe-retirement runs remain 0; GitHub Marketplace remains
  v1.1.0; `eolkits.com/api/capabilities` remains unavailable. Purchases,
  deliveries, collected revenue, and collected profit remain 0 / 0 / $0 / $0.

## Release-gate repair published — 2026-08-22T23:39:27Z

- Main commit
  https://github.com/ntoledo319/EOLkits/commit/32d01c2f505b30c8caac856c0f1af0da9ae059c3
  published exact tree `f2200f3b0bfbf7f43161699b4fc97197c04b38ad`,
  matching the locally reviewed commit tree. GitHub's workflow API reports
  `.github/workflows/publish-vscode.yml` active.
- Test release surfaces run
  https://github.com/ntoledo319/EOLkits/actions/runs/32605744293 passed all 13
  jobs, including the fresh VS compile/lint/rule/package job, both containers,
  dependency audit, every kit, API, Worker, web, Action, and Python quality
  checks. Determinism run `32605744252`, property run `32605744279`, and built-in
  Pages run `32605743603` also completed successfully.
- A fresh live probe still found VS v1.0.0 at 100 installs/162 downloads, zero
  Stripe-retirement runs, no newer VS publish run, GitHub Marketplace v1.1.0,
  no public v2.0.0 release, and HTTP 404 at `eolkits.com/api/capabilities`.
  Therefore public listing updates, paid reports, collected revenue, and profit
  remain 0 / 0 / $0 / $0; CI and a repository commit are not demand.

## Third-cycle blocker observation — 2026-08-22T23:47:26Z

- Public `main` remained `81a414f6` with exact tree `cc89920e`. Its final ledger
  release run `32605862353`, determinism `32605862354`, properties `32605862393`,
  and Pages run `32605862029` all completed successfully.
- Exact production observations: Stripe-retirement workflow runs 0; VS publish
  runs 1, still only historical May run `25262940459`; VS listing
  `rupture.rupture-vscode` v1.0.0 at 100 installs and 162 downloads; GitHub
  Marketplace v1.1.0; public v2.0.0 release HTTP 404; GRACE verifier runs 0.
- `eolkits.com` returned HTTP 200 for the legacy health/home surface, still
  contained Migration Pack and Drift Watch, omitted the verified Audit marker,
  and returned HTTP 404 for `/api/capabilities`. The health payload still
  identified the old production filesystem/SQLite/inline-runner service.
- All six historical `buy.stripe.com` URLs returned HTTP 200 Stripe-hosted pages.
  That does not prove a link active, inactive, safe, or reconciled; authenticated
  HQ-2 evidence is still required before any commerce claim.
- GitHub exposed 1 star, 0 forks, 0 actual issues, and 0 qualified Audit-interest
  issues. Paid reports, collected revenue, collected profit, and target gap
  remain 0 / $0 / $0 / $4,000.

## Resumed live-state and privacy audit — 2026-08-25T10:07:45Z

- The custom static release did move after the blocker: scheduled verifier runs
  `32626994756`, `32705925984`, and `32825272945` passed, and the live site's
  `Last-Modified` was `Tue, 25 Aug 2026 07:17:02 GMT`. It served the truthful
  single-$299 Audit, closed Pack/Drift tombstones, a 51-URL custom-host sitemap,
  and the public IndexNow key. This clears only the static-copy part of HQ-3.
- Five custom-domain HTML probes (`/`, `/audit/`, `/pack/`, `/drift/`, and
  `/success/`) each contained an injected
  `https://stats.saiditright.com/script.js` tag and zero generated CSP markers.
  The fetched script auto-tracks page URLs and browser metadata. The deployment
  contradicted the stated no-third-party-analytics posture and remained unsafe
  for checkout or recrawl.
- The GRACE backend did not move: `/api/status` and `/api/capabilities` returned
  404; `/health` remained the old filesystem/SQLite/inline-runner payload; and
  read-only probes of the three stale checkout paths returned 405 with POST
  allowed. This confirms route registration, not a successful Checkout Session.
- Stripe-retirement runs remained zero, VS publish remained only the historical
  May run `25262940459`, GitHub Marketplace remained v1.1.0 with no public
  v2.0.0 release, and VS remained v1.0.0. The VS counters reached 103 installs /
  164 downloads from the approximate 100 / 162 August 22 baseline; no v1.1.0
  attribution exists.

## Privacy containment published — 2026-08-25T10:07:45Z

- Public main commit
  https://github.com/ntoledo319/EOLkits/commit/b97befa7c4707c9e4c9a9c39e22871ec536fa5f9
  and two-parent GRACE-feed commit
  https://github.com/ntoledo319/EOLkits/commit/a5510969cf76d081afd49564bc4441cff6bb278f
  both have exact tree `6b0eef76e1f4ac95a3d8d2c62b94623b81c3f414`,
  matching the locally verified feature tree byte-for-byte. The feed commit
  preserves the three intervening draft commits as history without accepting
  their stale tree.
- All 64 generated HTML files received the restrictive CSP; the Audit success
  URL stopped carrying `{CHECKOUT_SESSION_ID}`. Two consecutive builds were
  byte-identical. The full web suite passed 35 tests, the API suite passed 74
  tests with one upstream Starlette deprecation warning, Black/Ruff passed, both
  workflow YAML files parsed, extracted Bash passed ShellCheck, and the focused
  specialist security review found no blocker.
- Main release run `32835361717`, determinism `32835361744`, properties
  `32835361827`, custom Pages `32835361707`, built-in Pages `32835360410`,
  acquisition `32835361734`, and Pages IndexNow `32835361747` all completed
  successfully. Pages served the release with `Last-Modified: Tue, 25 Aug 2026
  10:05:33 GMT`; all five live Pages probes contained the CSP, no external
  script, and no Stripe session identifier.
- Custom-domain IndexNow run
  https://github.com/ntoledo319/EOLkits/actions/runs/32835404486 failed before
  notification with `Refusing to notify search engines before the privacy CSP
  is live`. This is expected fail-closed evidence: the endpoint did not receive
  an unsafe custom-host submission.
- Acquisition run `32835361734` preserved 399-byte artifact ID `9558368696`
  with digest
  `sha256:5ced35f8404cfe9c72f41111e8770895ae747d482d98d773db177e8cf81532d5`.
  Direct public state still showed 1 star, 0 forks, 0 actual/qualified issues,
  and no owner Marketplace dispatch. Paid reports and workspace-observed
  collected revenue/profit remain 0 / $0 / $0. Authenticated current Stripe
  account state was not available, so this is not a claim that unseen Stripe
  charges or anomalies are absent; HQ-2 remains required. Target gap: $4,000.

## Hands-off Stripe and VS execution — 2026-08-25T11:21:00Z

- Safe-preflight commit `0b022b0852eb8e4b54d100cfeb82eeb7890320a2`
  published exact verified tree `fd6652509bc2a7c621afc4ca155c720e702e7ccf`.
  GRACE capability run `32840796298` passed and logged
  `deploy_transport=false` / `runtime_bundle=false`. Release surfaces
  `32840796267`, determinism `32840796230`, properties `32840796411`, legacy
  tombstone `32840796256`, and Pages `32840795101` also passed.
- Before that release, official Stripe behavior review found that archiving a
  Price can deactivate Payment Links using its Product. The retirement endpoint
  and workflow were changed to require zero unexpected active Payment Links
  before every mutation. Worker build passed; 39 focused retirement/tombstone
  tests passed; workflow YAML parsed; extracted Bash passed ShellCheck. This
  prevented an unapproved link from disappearing during the final audit.
- Exact one-use Stripe authorization commit `99e093343678c792fddcc3f0a31f98612adeff1f`
  produced owner-attributed push run `32840968816`. Its sole `retire` job
  `97780159651` passed every step: authorization, exact artifact verification,
  bounded live closure, independent final verification, tombstone/secret
  cleanup, and public fail-closed proof. Workflow success mechanically requires
  six exact inactive live Prices; zero approved/unexpected active Payment Links;
  zero unexpected active Product Prices; and zero matching open/recent Sessions,
  future subscriptions, or schedules. Public Worker `/health` and `/status.json`
  returned HTTP 200 retired tombstones afterward.
- Stripe restoration commit `b4fb019b77b716add739db58430401fd2ba24ebf`
  removed the one-use trigger and restored the permanent dispatch-only file.
  No Stripe-retirement run exists on that restore head.
- Exact one-use VS authorization commit `6bf1424f1d8c35fc9989188000bcf59b3e97e9da`
  produced owner-attributed push run `32841331222`. Publish job `97781275922`
  passed exact release-commit verification, dependency install, tests, stable
  Marketplace identity/version checks, packaging, and upload. Its publisher log
  states `Published rupture.rupture-vscode v1.1.0.`
- Restoration commit `a8e8b45c166b5e53fb01c5f099b175992b9a4908`
  removed the one-use VS trigger, returned the workflow to dispatch-only, and
  retained a preflight-discovered Bash quoting repair. Its release-surfaces
  `32841478286`, determinism `32841478250`, property `32841478272`, and Pages
  `32841476304` runs all passed; it produced no VS publish run.
- The official version-specific VS Marketplace package endpoint returned HTTP
  200 for v1.1.0. Its downloadable manifest says publisher `rupture`, name
  `rupture-vscode`, version `1.1.0`, display name `EOLkits - AWS Deprecation
  Scanner`, and the README points at the verified EOLkits Pages Audit. At the
  first post-release query, the Gallery latest-version index still cached v1.0.0
  with 103 installs and 164 downloads. At `2026-08-25T11:21:39.72Z`, the
  official Gallery index exposed v1.1.0 with 103 installs and 166 downloads.
  That is the V1 launch baseline, not qualified demand or revenue.
- Fresh `2026-08-25T11:25:46Z` production probes found the custom host unchanged:
  all five HTML pages returned HTTP 200 with zero CSP markers and one injected
  `stats.saiditright.com` script each; `/api/capabilities` and `/api/status`
  returned 404; `/health` still reported the old filesystem/SQLite/inline
  service. This keeps HQ-3 and checkout blocked. The GitHub Marketplace page
  still showed v1.1.0, the public v2.0.0 release endpoint returned 404, and the
  repository showed 1 star, 0 forks, and 0 actual issues.
- Qualified issues: **0**. Paid reports: **0**. Workspace-observed collected
  revenue: **$0**. Workspace-observed collected profit: **$0**. Target gap:
  **$4,000**. Successful retirement and publication are operational evidence,
  not dollars.

## Distribution and hosting reconciliation — August 27, 2026

- At `2026-08-27T00:32:08Z`, an exact official Gallery query returned public
  identity `rupture.rupture-vscode`, version `1.1.0`, last updated
  `2026-08-25T11:21:39.72Z`, with 103 installs and 183 downloads. Against the
  103-install/166-download release baseline, that is +0 installs and +17
  cumulative downloads. Downloads can include update/package fetches and do not
  establish qualified demand or revenue.
- Acquisition run `32972880350` observed at `2026-08-26T13:13:10Z` preserved
  artifact `9608277338` (SHA-256
  `ec1a84d9d0cebb0efa83d45ba1a03e9e354125b564530d9ecbe4b81d36d31807`):
  0 qualified issues, 0 distinct external authors, 0 VS-attributed qualified
  issues/authors, 0 external public `@v2` references, no public v2.0.0 release,
  1 star, and 0 forks.
- The August 26 07:17 UTC custom-host deployment put the generated meta CSP on
  all five tested HTML pages. All five raw responses still contain one injected
  `https://stats.saiditright.com/script.js`; scheduled verifier `32946397287`
  failed on that exact condition. `/api/capabilities` and `/api/status` remain
  HTTP 404, while `/health` remains the legacy filesystem/SQLite/inline service.
  The CSP blocks the known external script but does not remove the hostile
  hosting behavior or prove GRACE v2 deployment.
- An exact release preflight found three private v2 drafts: canonical
  `375063073` plus obsolete untagged drafts `374998709` and `375032399`. Codex
  deleted only the two exact obsolete drafts and re-queried the API: canonical
  draft `375063073` remains `draft=true`, tag `v2.0.0`, target `a9cdcaeb`.
- Repository metadata now uses the bounded AL2 end-of-support wording and points
  to `https://ntoledo319.github.io/EOLkits/`, the verified free-first surface.
  This is a routing/truth correction, not traffic or revenue.
- The acquisition workflow's exact Gallery query, identity/version guard,
  integral counter validation, baseline deltas, Bash syntax, ShellCheck, YAML
  parse, and complete live script execution passed locally. Public run
  `33028483868` then passed at commit `2d19a797` and preserved artifact
  `9629312207` (SHA-256
  `5e0ff22141e28ba5639d21238d18171bf8b658cfbf9242a0d03e6b525f02b2c8`).
  The inspected artifact observed at `2026-08-27T00:56:36Z` reports the same
  103 installs / 183 downloads, +0 / +17 release deltas, zero qualified issues
  or authors, zero external `@v2` references, no public v2.0.0 release, one star,
  and zero forks. It labels cumulative counters and qualified interest separately.
- Public commit `2d19a797` introduced exact tree `5e0fbf58` and was advanced
  through both `main` and `marketing-machine-v2` without force. Main validation passed: release matrix
  `33028483792` (13 jobs), determinism `33028483803`, property
  `33028483831`, acquisition `33028483868`, and Pages `33028480182`.
- Qualified issues: **0**. Paid reports: **0**. Workspace-observed collected
  revenue: **$0**. Workspace-observed collected profit: **$0**. Target gap:
  **$4,000**. No account-wide Stripe balance/charge connector is available, so
  these are workspace-observed figures rather than an unseen-account claim.

## Free-tier data-completeness ship — August 27, 2026

- Cycle-start check: WebFetch to the neutral control `example.com` returned
  `EGRESS_BLOCKED`; the same result on `docs.aws.amazon.com` and `repost.aws`.
  Direct `curl` through the configured proxy returned HTTP 403 (`CONNECT
  tunnel failed`) on both. WebSearch (hosted, not routed through this
  container's egress) still returned indexed results. Per AGENTS.md's
  unavailable-fetch fallback, no new repost-answers batch or dev.to draft was
  produced this cycle; see DECISIONS D42.
- Found and fixed a real free-tier inconsistency instead: `rules/public/
  deprecations.yml` (source of truth for the ICS calendar, SEO `/migrate/`
  pages, `llms.txt`, sitemap, and the free browser scanner) omitted
  `nodejs16.x` from its tracked/active list even though the free scanner
  engine (`kits/lambda-lifeline/src/scan/index.mjs`) and `apps/web/content/
  fixes.yml` already correctly track it in the delayed Q1-2027 block cluster
  (block-create 2027-02-01, block-update 2027-03-03), citing
  `docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html`.
- Added the entry, rebuilt with `apps/web/build.py`, and ran `pytest -q
  apps/web`: 35 passed, 0 failed, when run with the same
  `EOLKITS_BASE_PATH`/`EOLKITS_SITE_URL`/`EOLKITS_API_URL` env vars CI sets.
  Confirmed the 3 tests that fail without those env vars fail identically on
  the unmodified baseline — not a regression from this change.
- Externally visible artifacts added/updated in this commit: new page
  `docs/migrate/lambda-node.js-16-eol/`, new badge
  `docs/badge/lambda-node.js-16-eol.svg`, updated `docs/deprecations.ics`,
  `docs/sitemap.xml`, `docs/llms.txt`, `docs/migrate/index.html`, sibling
  migrate pages' "related deadlines" links, `docs/scan/index.html`, and
  `docs/eol-checker/index.html`. These go live via the existing
  `deploy-pages.yml` workflow on push to `main`/`marketing-machine-v2` per its
  path triggers.
- No Stripe, GRACE, DEV, or Marketplace state changed. Qualified issues: **0**.
  Paid reports: **0**. Workspace-observed collected revenue: **$0**.
  Workspace-observed collected profit: **$0**. Target gap: **$4,000**.

## Build-date drift correction — August 28, 2026

- Cycle-start check repeated D42's egress test: WebFetch to `example.com`
  returned `EGRESS_BLOCKED`; direct `curl` through the configured proxy to
  `example.com` and `docs.aws.amazon.com` both returned HTTP 403 (`CONNECT
  tunnel failed`). `curl -sS "$HTTPS_PROXY/__agentproxy/status"` confirmed the
  proxy is up (a domain-level block, not local misconfiguration). WebSearch
  still returned indexed results but cannot substitute for the live-thread
  check or the direct primary-source fetch the repost-answers/DEV duties
  require. Per AGENTS.md's fallback and D36, no new repost-answers batch or
  dev.to draft was produced this cycle. See DECISIONS D43.
- `apps/web/BUILD_DATE` had not been bumped since the initial 2026-08-22
  repair commit `85c9f43e`, despite five subsequent content-changing cycles.
  Every generated "N days until <deadline>" countdown, the ICS `DTSTAMP`, the
  sitemap `lastmod`, and `docs/status/data.json`'s `generated_at` were
  computed from that stale date, overstating remaining runway by 6 days
  site-wide.
- Confirmed `pytest -q apps/web` was 35/35 green on the stale baseline first.
  Bumped `BUILD_DATE` to `2026-08-28`, rebuilt via `apps/web/build.py` with the
  same `EOLKITS_BASE_PATH=/EOLkits` / `EOLKITS_SITE_URL=https://ntoledo319.
  github.io/EOLkits` / `EOLKITS_API_URL=https://eolkits.com` env vars CI uses,
  and re-ran the suite: 35/35 green, including determinism and link-integrity
  cases. The diff touched 16 files (`docs/migrate/*` countdown text, `docs/
  deprecations.ics`, `docs/feed.xml`, `docs/blog/feed.xml`, `docs/sitemap.xml`,
  `docs/status/data.json`) and every changed line is date-derived — no price,
  claim, or structural change (e.g. the shared `/migrate/` countdown moved
  163→157 days, matching the 6-day bump exactly).
- Considered adding the scanner's two "bonus" runtimes (`ruby3.2`, `dotnet6`)
  to `rules/public/deprecations.yml` the way `nodejs16.x` was added in D42;
  declined for now because, unlike `nodejs16.x`, they are not corroborated by
  a second independently maintained source file and cannot be freshly verified
  against `docs.aws.amazon.com` this cycle. Recorded as a deferred gap, not
  shipped, to avoid publishing an unverified date.
- These artifacts go live via the existing `deploy-pages.yml` workflow on push
  to `main`/`marketing-machine-v2`, same as every prior content cycle. No
  Stripe, GRACE, DEV, or Marketplace state changed. Qualified issues: **0**.
  Paid reports: **0**. Workspace-observed collected revenue: **$0**.
  Workspace-observed collected profit: **$0**. Target gap: **$4,000**.

## Branch reconstruction and second DEV corpus error found — August 29, 2026

- `marketing-machine-v2` did not exist on `origin` at cycle start (confirmed
  via `git ls-remote --heads` and the GitHub API `list_branches`/
  `list_pull_requests`) — merged commit `0c9dfec` ("Integrate corrected Lambda
  Node.js 16 lifecycle data (#24)") had already carried its unique work into
  `main`, and `deploy-pages.yml` (the actual eolkits.com publisher) triggers
  only on `main`. Recreated the branch from current `main` per the runbook's
  "designated branch already merged" case; see DECISIONS D44.
- Cycle-start state on `main`: `apps/web/BUILD_DATE` already `2026-08-29`
  (today), `pytest -q apps/web` 35/35 green, and `apps/web/build.py` rebuild
  against CI env vars produced a clean `git diff --exit-code -- docs` — no
  drift to correct this cycle.
- Egress test repeated (same method as D42/D43): direct `curl` through the
  configured proxy to `example.com` and `docs.aws.amazon.com` both returned
  HTTP 403; proxy status endpoint confirmed the proxy itself is reachable. No
  new repost-answers batch or dev.to draft produced this cycle per AGENTS.md's
  fallback.
- Cross-checked all 25 quarantined `launch/distribution/devto/*.md` drafts'
  hard-coded lifecycle dates against `rules/public/deprecations.yml` and
  `kits/lambda-lifeline/src/scan/index.mjs`'s `PHASE_DATES` (both already
  internally corroborated, no external fetch needed). Found article 04's
  timeline table lists `python3.10` "Deprecated 2026-03-31"; both internal
  sources say 2026-10-31 (it matches `ruby3.2`'s phase-1 date instead — a
  likely copy/mix-up). Documented as a second "Known critical error" in
  `launch/distribution/devto/README.md`, following the existing article-24
  pattern (README note only; the archived draft itself is left as an
  unedited mirror of the still-live post for the owner's HQ-4 review).
- No price, checkout, Stripe, GRACE, DEV-account, or Marketplace state
  changed. Qualified issues: **0**. Paid reports: **0**. Workspace-observed
  collected revenue: **$0**. Workspace-observed collected profit: **$0**.
  Target gap: **$4,000**.

## From-the-top recovery evidence — 2026-08-30T05:00:57Z

- Public `refs/heads/v2` was recreated without force at exact fully green main
  commit `0c9dfec25004066df2cc277f9ee1205f52e151a4`; public raw `action.yml`
  resolves. This is restored distribution infrastructure, not an external use
  or sale.
- `https://eolkits.com/` returned HTTP 200 from Caddy at `15.204.209.97` and
  still contained one injected `https://stats.saiditright.com/script.js` tag.
  `https://ntoledo319.github.io/EOLkits/` returned the clean generated document
  without that tag. The custom host's CSP currently blocks the script; the raw
  host configuration is still unremediated.
- Live GRACE remained pre-v2: capability/status routes were unavailable and the
  old public upload service remained reachable during the audit. Checkout stays
  closed. An emergency Caddy deny block and stopped-volume safe-rollout path are
  prepared but cannot be installed without GRACE access.
- Local verification: al2023-gate **49**, python-pivot **50**, Lambda kit **28**,
  Worker **39**, GRACE API **78**, runner **33**, and web **35** tests passed.
  VS Code compile/lint/rules/package, Worker TypeScript, Ruff, Black, mypy,
  sample-PDF verification, 16 workflow YAML parses, snapshot ShellCheck, and a
  repeat generated-site hash comparison all passed.
- Current dependency evidence: four locked Python graphs reported no known
  vulnerabilities; three Node production audits reported zero vulnerabilities;
  98 non-dev Node package records had no forbidden or missing license
  declarations. Container builds remain delegated to GitHub CI because local
  Docker would violate the workspace-jail operating decision.
- VS v1.1.0 public evidence observed during the audit: **103 installs**, **193
  downloads**, **0 install growth** from baseline, and **0 qualified external
  authors**. The gate deadline is `2026-08-30T11:15:00Z`, so the result remains
  pending rather than being called early.
- Qualified issues: **0**. Paid reports: **0**. Workspace-observed collected
  revenue: **$0**. Workspace-observed collected profit: **$0**. Target gap:
  **$4,000**. Stripe account-wide activity was not accessible, so this remains a
  workspace-evidence statement rather than an account-wide assertion.

## Recovery merge, ref, Pages, and draft evidence — 2026-08-30T05:21:42Z

- Recovery PR [#25](https://github.com/ntoledo319/EOLkits/pull/25) merged as
  `47cd9eae77c5a9ddfdbbdb33206efe8f60b907d8`. All PR checks passed: Determinism,
  Property-based tests, public-v2 consumer, and all 13 release-surface jobs.
- Every observed push workflow for merge commit `47cd9eae...` completed
  successfully: IndexNow `33294128597`, Determinism `33294128605`, acquisition
  evidence `33294128603`, public-v2 consumer `33294128614`, Property tests
  `33294128644`, reviewed Pages deploy `33294128599`, release surfaces
  `33294128598`, and GitHub's Pages deployment `33294128433`.
- Read-after-write ref verification showed `main`, `refs/heads/v2`, and
  `refs/heads/marketing-machine-v2` all at exact `47cd9eae...`; public raw
  `v2/action.yml` returned the expected Action definition.
- One-use synchronization PR [#26](https://github.com/ntoledo319/EOLkits/pull/26)
  passed all three required suites and merged as `79888beb...`. Owner-attributed
  push run
  [33294414373](https://github.com/ntoledo319/EOLkits/actions/runs/33294414373)
  completed successfully. Read-after-write release verification found canonical
  ID `375063073`, tag `v2.0.0`, target `47cd9eae...`, expected name, `draft=true`,
  `prerelease=false`, and zero assets. All other workflows on `79888beb...` also
  passed. The temporary trigger is removed by the finalization tree.
- This is distribution/release evidence, not demand. Qualified issues: **0**.
  Paid reports: **0**. Workspace-observed collected revenue: **$0**.
  Workspace-observed collected profit: **$0**. Target gap: **$4,000**.

## v1.1 gate, v1.2 publication, and platform-operation evidence — 2026-08-31T23:29:34Z

- Latest exact acquisition artifact before repositioning (run
  `33428734416`, artifact `9771735945`) observed: 0 qualified interest
  issues; 0 distinct external authors; 0 VS-qualified issues/authors; 0 public
  external `@v2` code references; no public v2.0.0 release; one star; zero
  forks; VS v1.1.0 at 103 installs / 197 downloads versus 103 / 166 baseline.
  The 2026-08-30T11:15:00Z gate emitted
  `failed_reposition_required`. Download growth alone did not pass it.
- Reposition PR [#28](https://github.com/ntoledo319/EOLkits/pull/28) merged as
  `23762f3f7a8e7ccc61b76c7fef4a00d1fa7fec99` after Determinism
  `33449780627`, Property `33449780633`, and release-surface
  `33449780615` passed. All seven observed merge workflows passed. The release
  tree changed the VS name/search/first-run copy, moved it to v1.2.0, and added
  the publicly supported operator identity to legal surfaces.
- Authorized operations PR
  [#29](https://github.com/ntoledo319/EOLkits/pull/29) merged exact reviewed head
  `130f316e...` as `5cce3bb909689bbed8f0752312d0a84fbe4c89f7`; all three
  PR suites and all six observed merge workflows passed.
- VS publication run
  [33450455161](https://github.com/ntoledo319/EOLkits/actions/runs/33450455161)
  tested, packaged, and reported
  `Published rupture.rupture-vscode v1.2.0`. The public Marketplace page and
  cache-busted official Gallery API then independently showed display name
  **AWS Lambda EOL Scanner — EOLkits**, version 1.2.0, last update
  `2026-08-31T23:27:54.62Z`, 103 installs, and 199 downloads. New gate:
  `2026-09-05T23:27:55Z`.
- Bounded platform run
  [33450455146](https://github.com/ntoledo319/EOLkits/actions/runs/33450455146)
  passed its safety controls but had no DEV owner key. Independent public reads
  after the run found 25 live DEV posts and an empty ruleset list. The same
  merge triggered legacy dynamic Pages run `33450454076`, confirming the
  repository-admin race was not removed.
- Fresh production read-only probes: `/health` 200,
  `/api/capabilities` 404, `/api/status` 404, stale `/pack/install` 200,
  one raw `https://stats.saiditright.com/script.js` injection, and HTTP 000
  timeouts for both direct Caddy-admin routes. No deployment or mutation was
  attempted without authority.
- Retired Stripe credential rotation/revocation was expressly excluded by the
  owner and was not attempted. No Product, Price, Payment Link, checkout,
  customer record, or live charge was created or changed.
- Cleanup-tree verification: all 16 remaining workflow YAML files parsed; every
  acquisition/publication shell block passed `bash -n` and ShellCheck; VS
  compile/lint/rule tests passed with zero production audit findings; the
  generated web build passed 35 tests and produced no `docs/` drift; and
  `git diff --check` passed.
- Qualified issues: **0**. Paid reports: **0**. Workspace-observed collected
  revenue: **$0**. Workspace-observed collected profit: **$0**. Target gap:
  **$4,000**.
