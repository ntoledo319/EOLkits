# Asset audit — August 22, 2026

This audit records what a stranger can use or buy, not what old pages claimed.
All code and evidence below is inside the workspace jail.

## 1. Static site and browser scanner

- Buyer sentence: scan pasted AWS source/IaC locally in the browser and read
  cited migration/error guidance without uploading code.
- Stack: deterministic Python/Jinja/PyYAML generator producing docs/ for GitHub
  Pages; client-side scanner and first-party event beacon.
- Completeness: 35 generated-site tests pass; the 87-file public tree is
  byte-deterministic across consecutive builds, link/source checked, and free of
  trailing whitespace. The GitHub Pages project-path build keeps static links
  under `/EOLkits` and API calls on `eolkits.com`. Both GitHub Pages deployment
  paths now publish that same artifact, and a public probe passed at
  https://ntoledo319.github.io/EOLkits/. The August 25 `eolkits.com` static
  deployment now serves the truthful single-$299 funnel and retired-product
  tombstones, but a hosting layer injects an unreviewed cross-origin analytics
  script into every tested page. The August 26 deployment added the generated
  meta CSP, which blocks that exact external script, but the raw injection
  remains and the scheduled verifier is correctly red. The custom domain is
  therefore not checkout-safe even though its product copy is repaired.
- Search distribution: both hosts expose a valid IndexNow ownership key and a
  51-URL same-scope sitemap. A contents-read-only workflow submits bounded Pages
  URLs from `main`; the custom-domain path additionally verifies the live offer,
  generated CSP, and absence of external scripts before any request. Pages run
  `32835361747` succeeded. Custom run `32835404486` refused submission before
  the endpoint call; a retry remains blocked by the still-injected external
  script. Receipt is not proof of indexing, ranking, visits, or demand.
- $0 deploy: GitHub Pages.
- License/provenance: repository MIT; factual AWS claims require primary-source
  review. No buyer code leaves the browser scanner.
- Capability worth paying for: none by itself; its value is qualified discovery
  for the evidence report.
- Smallest sellable unit: the resulting repository evidence report, not scanner
  access.

## 2. Three local kits and GitHub Action

- Buyer sentence: detect and preview selected Lambda runtime, Python compatibility,
  and Amazon Linux migration risks in source, dependencies, and supported IaC.
- Components: lambda-lifeline (Node), python-pivot and al2023-gate (Python), plus
  a path-confined composite GitHub Action.
- Completeness: 49 al2023-gate, 50 python-pivot, and 28 lambda-lifeline cases
  pass, along with real Action fixtures, three property cases, and deterministic
  scanner checks. Node runtime and IaC paths now include nodejs22.x and target
  nodejs24.x. Commands remain dry-run unless an apply flag is supplied.
- $0 deploy/distribution: public GitHub repository and the existing GitHub
  Marketplace Action listing.
- Distribution state: the tested `v2` release branch is public and resolves to
  green commit `9c231b58`, so `uses: ntoledo319/EOLkits@v2` works now and routes report
  interest to the verified Pages funnel. The Marketplace
  page still exposes the stale v1.1.0 release until the owner publishes the
  canonical private v2.0.0 draft from green run `32604619021` with the
  Marketplace checkbox. Its target is `a9cdcaeb`; its Action files are
  byte-identical to public `v2`.
- License/provenance: MIT kit licenses; AWS SDK dependencies are Apache-2.0.
- Capability worth paying for: a shareable, decision-ready report rather than
  raw console matches.
- Smallest sellable unit: free Marketplace check that routes an applicable
  finding to the paid Audit.

## 3. VS Code extension

- Buyer sentence: flag bundled AWS deprecation patterns locally on save or on
  demand in YAML, JSON/JSONC, Terraform/HCL, JavaScript/TypeScript, and Python.
- Completeness: the exact public listing `rupture.rupture-vscode` is live at
  v1.1.0. Green run `32841331222` published the pinned candidate in place while
  preserving the stable identity, legacy commands/settings, and installed base.
  The official Gallery index moved from its 103-install/166-download release
  baseline to 103 installs/183 downloads by August 27: +17 cumulative downloads
  and zero install growth. Downloads can include update/package fetches and are
  not qualified demand or revenue. The permanent publish workflow is again
  dispatch-only and retains its owner, confirmation, identity, and pinned-
  commit guards.
- $0 deploy/distribution: Visual Studio Marketplace.
- License/provenance: MIT; VSIX contains compiled project code, manifest, README,
  icon, and license, with no node_modules.
- Capability worth paying for: none directly; the extension is a contextual
  acquisition surface for Audit.
- Smallest sellable unit: free local extension.

## 4. Audit v2 API and PDF runner

- Buyer sentence: turn one repository ZIP or supported source file into a static
  evidence PDF with exact locations, cited rules, hashes, and explicit limits.
- Stack: FastAPI, SQLite FULL WAL, immutable bounded uploads, Stripe webhooks,
  durable jobs/refunds, Resend, WeasyPrint, signed report URLs.
- Completeness: 74 API cases and 33 report-runner cases pass. A genuine
  four-page fictional PDF, its five-file ZIP input, and an exact hash/evidence
  manifest are public and generated through the same report engine. Production
  operation remains unproved. Checkout
  defaults off and readiness also fails closed on missing runner, email, Stripe,
  storage, pending refunds, or at-risk fulfillment.
- $0 deploy: existing GRACE capacity only if the owner confirms $0 incremental
  cost. Otherwise this asset remains blocked; no paid infrastructure is allowed.
- License/provenance: hash-locked dependency graphs, generated license
  inventories, root ATTRIBUTIONS, and clean vulnerability audits. The PDF does
  not redistribute implementation code or dependency source.
- Capability worth paying for: exact, shareable evidence and remediation order.
- Smallest sellable unit: one $299 static repository evidence report.

## 5. Legacy Worker, GitHub App, and multi-SKU concepts

- Buyer sentence: none; these are retired prototypes, not products.
- Components: retired Cloudflare Worker, old Migration Pack/App material, Drift
  Watch, Organization License, partner/white-label routes.
- Completeness: incomplete or operationally unproved. Active API routes return
  410. The verified live pre-rename Worker was replaced in production with the
  tested tombstone: health reports retirement and checkout, App-install, and
  webhook paths return 410. Its retained Queue consumer acknowledges stale
  events without fulfillment. Dormant PR-runner/JWT code and autonomous
  publisher scripts were removed. A separate owner-gated workflow now validates
  the exact six live Price/Product/amount/currency/interval tuples, active
  Product Prices, six historical Payment Link URLs, open and recent-completed
  Checkout Sessions, subscriptions, and schedules before making only reversible
  Price/Link changes. Exact owner-attributed run `32840968816` completed those
  bounded changes and verification; all six historical Prices are inactive,
  no approved or unexpected active Payment Links remain, and the Worker Stripe
  binding was removed. Account-level key rotation remains external.
- $0 deploy: the closure workflow uses the existing Cloudflare account and
  preserves only the explicit tombstone. Do not restore commerce bindings or
  deploy a new Worker product.
- License/provenance: historical source remains MIT where stated; no artifact is
  approved for sale.
- Capability worth paying for: none today.
- Smallest sellable unit: none until rebuilt and proved through a new audit.

## 6. Content and launch corpus

- Buyer sentence: cited fix/deadline pages can answer specific migration
  questions and lead to the free scanner.
- Completeness: generated on-site pages separate provider-sourced dates from
  workload-specific checks and are link-checked. A false universal IMDSv1
  deadline now has a noindex correction route. All 25 local DEV source copies
  carry an explicit do-not-publish guard. The 25 already-live DEV posts were
  observed with zero comments and still require owner unpublication because
  their scope/privacy/product claims are stale. Outreach, social, HN, Gumroad,
  and repost material is archived and marked do-not-publish. Three merge-dropped
  answer batches restored on August 27 plus one newly drafted batch are preserved
  as unverified research only; none is authorized for posting.
- $0 deploy/distribution: GitHub Pages; external platforms require owner review
  and manual approval under their current terms.
- License/provenance: owned drafts, but technical facts and platform policy must
  be rechecked before reuse.
- Capability worth paying for: no standalone proof yet; useful only as honest
  inbound discovery for Audit.
- Smallest sellable unit: none. The existing content should earn qualified
  traffic before any paid content product is considered.

## Cross-asset risks

- Revenue/demand: observed collected revenue is $0; no customer delivery proves
  willingness to pay.
- Operations: no real Stripe test-mode end-to-end evidence has been recorded for
  Audit v2. The formerly live Stripe-capable Cloudflare Worker and its exact
  historical Prices/Payment Links are now closed by verified run `32840968816`.
  The stale GRACE service still has not deployed v2, and historical Worker
  versions still require account-level key rotation.
- Distribution: the Action v2 ref and repaired GitHub Pages fallback are public,
  and the 51 canonical Pages URLs have one accepted IndexNow submission, but the
  GitHub Marketplace listing remains stale at v1.1.0. The VS Marketplace repair
  is public at v1.1.0, but its +17 downloads/zero install growth is not qualified
  demand. Repository metadata now points to verified Pages and uses bounded AL2
  wording; the custom host remains blocked by raw analytics injection.
- Legal: accurate seller/controller identity, address, governing law, tax
  posture, and $0 incremental hosting confirmation are owner-only gates.
- Remote history: origin/main accumulated synthetic status/benchmark commits and
  low-information weekly pages; the repaired tree is now on main and those
  generators are removed.
- Funnel sprawl: closed Migration Pack, organization, partner, and scanner
  research-list forms were removed. Those pages no longer collect speculative
  leads or promise future features.

## Demand-signal and privacy hardening — August 22

- The browser scanner now reveals a structured `$299 Audit interest` GitHub
  issue form only after at least one real finding. The closed Audit page exposes
  the same form. It requires a real-project finding, exact $299 scope
  acknowledgement, purchase consideration, and a no-sensitive-data pledge. It
  is explicitly public, nonbinding, and not an order, reservation, waitlist, or
  promise of follow-up.
- A daily read-only workflow records public lower bounds for qualified external
  issue authors and public `@v2` code references. It writes only a run summary
  and 14-day artifact; it never comments, posts, commits metrics, or calls an
  external person. Interest remains a signal, never revenue.
- The generated site has 32 passing cases, including JavaScript parsing of the
  Audit, scanner, and status pages. It stores no visitor ID, cookie, referrer,
  or local-storage attribution. Telemetry stays dormant until the v2 capability
  handshake succeeds, then sends only canonical first-party fields.
- The API has 74 passing cases. GitHub Pages is exact-origin CORS-allowed;
  impostor origins are rejected. Raw events expire after 30 days, abuse keys
  after two days, ingestion is body/rate/database bounded, PII-like attribution
  is discarded, and funnel/commerce/order detail is admin-only with no-store
  caching.
- The signal is now public: Pages serves the qualified CTA, the authenticated
  GitHub form is installed, `v2` carries the findings-only Action link, and
  acquisition-evidence run `32596830945` completed successfully with a preserved
  observation artifact. This is measurement availability, not customer demand.
- Search notification run `32597777674` subsequently passed after verifying the
  public key and the 51 same-scope sitemap URLs. Fresh acquisition artifact
  `acquisition-evidence-32597777625` still observed zero qualified authors and
  zero external public `@v2` references. Search-engine receipt and those zero
  lower bounds do not establish demand.

## Engine-generated proof release — August 22

- Main contains product commit `9c231b58`, and public `v2` resolves to it; the remote tree
  `8a25da73a1dc8c3c9107c76e7a20d87cc620cd98` exactly matches the final locally
  verified tree.
- Pages serves the real four-page Audit PDF at
  https://ntoledo319.github.io/EOLkits/audit/sample/eolkits-sample-report.pdf,
  the complete fictional input at
  https://ntoledo319.github.io/EOLkits/audit/sample/fictional-repository.zip,
  and its manifest at
  https://ntoledo319.github.io/EOLkits/audit/sample/eolkits-sample-report.json.
- The PDF/ZIP/manifest SHA-256 values are respectively `855c793c8b2735f54fad08465f05c50943cb7908fd194b43dacf0eca9c423d9a`,
  `3fd7c4f6cfdb27d436399a0a639d4990303030839a0a338bb343a1ef12031b67`,
  and `8ad77bb90851ec9ec1ae893118bb3efca69d4545e72ee179915b957222396a58`.
- The report engine now binds Lambda-runtime findings to supported Lambda
  configuration contexts, bounds archive/line/config/resource/evidence and
  dependency complexity, records skipped files and page count, and labels
  future AWS dates as projected. These are product-quality facts, not proof of
  buyer demand.
- The first remote sample gate exposed platform-specific native PDF
  serialization. The replacement keeps the published PDF's exact manifest hash
  while requiring identical fixture, page count, rule pack, findings, evidence,
  and every other renderer-independent engine field. All replacement release,
  determinism, property, and Pages gates passed.
- The GRACE static feed now has the exact final tree at `0780909c`, but the
  current custom domain still serves obsolete product copy and its capabilities
  endpoint returns 404. Collected revenue remains $0.

## VS Marketplace distribution recovery — August 22

- Exact Marketplace API lookup found the existing public identity
  `rupture.rupture-vscode`; searching only for the EOLkits rebrand had produced
  a false negative. The old listing reports v1.0.0, approximately 100 installs,
  and 162 downloads. These are historical baseline counters, not current EOLkits
  demand, attributable traffic, or revenue.
- The currently published v1.0.0 code links findings to
  `https://ntoledo319.github.io/Rupture/audit`, which now returns HTTP 404. A
  repository rebrand had also changed the package identity to the nonexistent
  `eolkits.eolkits-vscode`, abandoning the only observed extension distribution.
- The release candidate restores the immutable Marketplace identity while
  retaining EOLkits display branding, bumps to v1.1.0, routes to the verified
  Pages Audit, and keeps legacy `rupture.*` commands and explicitly configured
  settings working through the transition. The package workflow rejects any
  identity other than `rupture.rupture-vscode`.
- A findings-only, public, nonbinding `$299 Audit interest` path now provides a
  privacy-bounded signal. Acquisition evidence separates VS-attributed issues
  and external authors. Neither the form nor the local package is a sale; the
  five-day V1 falsifier starts only after the owner publishes v1.1.0.
- Repository commit `a9cdcaeb` published this v1.1.0 source/package candidate
  with exact tree `99136547`; the full release matrix, extension package job,
  determinism, properties, built-in Pages, draft synchronization, and acquisition
  measurement passed. The Marketplace itself remains v1.0.0.

## Third-cycle authority boundary — August 22

The sellable code, truthful sample, fail-closed funnel, installable Action ref,
and guarded VS candidate are finished repository assets. They are not a live
business: no paid checkout is enabled, neither prepared Marketplace update is
public, and GRACE has no v2 capability endpoint. Repository configuration still
contains no GRACE deploy transport, Stripe/Resend runtime bundle, or self-hosted
runner. The remaining missing assets are external operating authority and
credentials, not another code artifact.

Do not repurpose the six historical Stripe links as a sellable asset. Public
probes return Stripe-hosted pages, but only the authenticated exact retirement
audit can establish their catalog/session/subscription state, and Audit v2
fulfillment is not deployed. Accepting payment through them would be unsafe and
would not create a verified report-delivery path.

## Hosting-injection containment release — August 25

- Public `main` commit `b97befa7` and GRACE feed commit `a5510969` share exact
  tree `6b0eef76`. The latter preserves the three intervening draft commits as
  history while replacing their stale branch tree with the reviewed release.
- All 64 generated HTML documents now place a restrictive CSP at the start of
  the document head. It allows same-origin/inline site code and the reviewed
  `https://eolkits.com` API connection, but it does not authorize the observed
  `https://stats.saiditright.com` script or its cross-origin requests.
- Pages deployed the new tree and five live-page probes found CSP on all five,
  no external script, and no Stripe session identifier. The custom domain still
  had zero CSP markers and the injected analytics tag on all five probes at
  `2026-08-25T10:07Z`; its last-modified time was still 07:17 UTC.
- Audit checkout success URLs no longer include `{CHECKOUT_SESSION_ID}`. Durable
  fulfillment and reconciliation continue through the verified Stripe webhook
  and server-side session record; 74 API tests cover the service and 35 web tests
  cover the generated surface.
- This is a security/distribution asset, not a sale. GRACE v2, Stripe retirement,
  Marketplace publication, and checkout remain owner-gated.

## Hands-off retirement and VS release — August 25

- The Stripe retirement tool now refuses every mutation when its read-only
  preflight finds an active Payment Link outside the exact URL allowlist. This
  closes a real Stripe behavior gap: archiving a Price can also deactivate links
  using that Product. The worker guard, workflow guard, and zero-POST regression
  all passed; the focused Worker/tombstone suite is 39/39 green.
- Owner-attributed run `32840968816` then completed the exact live retirement.
  Every verification, mutation, cleanup, tombstone, and public fail-closed step
  passed. The success postcondition requires all six exact Prices inactive, no
  approved or unexpected active links, and no matching open/recent Sessions,
  future subscriptions, or schedules. The current Worker Stripe binding was
  removed. Account-level legacy-key rotation remains outside the connected
  tooling and stays in HQ-2.
- Owner-attributed run `32841331222` published the pinned existing identity
  `rupture.rupture-vscode@1.1.0`. Its exact-SHA, install, compile/lint/rule test,
  identity, version, package, and publish steps all passed. The publisher log
  records the successful release, and the public version-specific VSIX endpoint
  returns a package whose manifest is `rupture.rupture-vscode@1.1.0`, branded
  EOLkits, with the repaired Pages Audit URL.
- Both narrowly scoped one-shot push gates were removed immediately after their
  terminal runs. Restoration head `a8e8b45c` has tree `cb5a151b`, both permanent
  workflows are dispatch-only again, and all four workflows on that head passed.
  The VS workflow retains a repaired Bash identity check found by preflight
  validation.
- Fresh GRACE capability run `32840796298` remained `deploy_transport=false`
  and `runtime_bundle=false`. Repository-owner GitHub authority is connected;
  GRACE/Stripe account control, legal facts, DEV control, and GitHub Marketplace
  agreement/2FA are still absent capabilities rather than missing code.

## Current external distribution state — August 27

- The repository description now says AL2 reached end of support rather than
  claiming every AL2 workload is necessarily unpatched. Its homepage points to
  the verified free-first Pages surface while GRACE remains unready.
- Two obsolete untagged v2 release drafts were deleted after an exact preflight.
  Canonical private draft `375063073` remains the only draft, tagged `v2.0.0`,
  targeting `a9cdcaeb`, and still requiring the owner's Marketplace agreement,
  checkbox, and 2FA action.
- Public commit `2d19a797` now measures the exact VS identity/version,
  cumulative installs/downloads, and deltas from the 103/166 release baseline.
  Remote run `33028483868` passed and artifact `9629312207` independently
  preserved the expected 103 installs / 183 downloads, +0 / +17 deltas, and
  zero qualified VS-attributed authors. The counters remain non-revenue context.

## Free-tier data-consistency correction — August 27

`kits/lambda-lifeline` (the free scanner/CLI kit) and `apps/web/content/
fixes.yml` already tracked `nodejs16.x` correctly in the delayed Q1-2027 Lambda
block cluster. `rules/public/deprecations.yml` — the shared source of truth for
the ICS calendar, SEO `/migrate/` pages, `llms.txt`, sitemap, and the free
browser scanner's embedded data — did not, listing it only as `historical`
with no block dates. Added the missing entry so the free acquisition surfaces
match the scanner engine; see DECISIONS D42 and METRICS's "Free-tier
data-completeness ship" entry. This closes an internal-consistency gap in the
free tier; it does not change any asset's completeness, license, or
monetization frame.

## Build-date drift correction — August 28

Asset 1 (static site/browser scanner)'s generated deadline copy was computed
from a `BUILD_DATE` fixed at 2026-08-22 across five subsequent content cycles,
so every "days until deadline" figure on the live-eligible artifact understated
urgency by 6 days. Bumped `apps/web/BUILD_DATE` to 2026-08-28 and rebuilt;
`pytest -q apps/web` stayed 35/35 and the diff was entirely date-derived. See
DECISIONS D43 and METRICS's "Build-date drift correction" entry. This is a
truth/quality fix to an existing free asset, not a new asset, license change,
or monetization-frame change.
