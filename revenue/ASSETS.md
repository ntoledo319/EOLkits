# Asset audit — August 22, 2026

This audit records what a stranger can use or buy, not what old pages claimed.
All code and evidence below is inside the workspace jail.

## 1. Static site and browser scanner

- Buyer sentence: scan pasted AWS source/IaC locally in the browser and read
  cited migration/error guidance without uploading code.
- Stack: deterministic Python/Jinja/PyYAML generator producing docs/ for GitHub
  Pages; client-side scanner and first-party event beacon.
- Completeness: 18 generated-site tests pass; the 84-file output is
  byte-deterministic across consecutive builds, link/source checked, and free of
  trailing whitespace. The GitHub Pages project-path build keeps static links
  under `/EOLkits` and API calls on `eolkits.com`. Both GitHub Pages deployment
  paths now publish that same artifact, and a public probe passed at
  https://ntoledo319.github.io/EOLkits/. The observed `eolkits.com` deployment
  is still obsolete until the owner runs the reviewed GRACE ship path.
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
  commit `3ea1a169`, so `uses: ntoledo319/EOLkits@v2` works now. The Marketplace
  page still exposes the stale v1.1.0 release until the owner publishes the
  prepared private v2.0.0 draft with the Marketplace checkbox.
- License/provenance: MIT kit licenses; AWS SDK dependencies are Apache-2.0.
- Capability worth paying for: a shareable, decision-ready report rather than
  raw console matches.
- Smallest sellable unit: free Marketplace check that routes an applicable
  finding to the paid Audit.

## 3. VS Code extension

- Buyer sentence: flag bundled AWS deprecation patterns locally on save or on
  demand in YAML, JSON/JSONC, Terraform/HCL, JavaScript/TypeScript, and Python.
- Completeness: TypeScript compile, current ESLint, scanner behavior suite, and
  minimal 11-file VSIX package pass. It is not yet observed in the Marketplace.
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
- Completeness: 72 API cases and 14 report-runner cases pass; production
  operation is unproved. Checkout
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
  410, the Worker defaults to tombstone mode, and its normal deploy command
  fails deliberately. Dormant PR-runner/JWT code and autonomous publisher
  scripts were removed.
- $0 deploy: do not deploy except a temporary Worker tombstone needed to close
  an existing unsafe route.
- License/provenance: historical source remains MIT where stated; no artifact is
  approved for sale.
- Capability worth paying for: none today.
- Smallest sellable unit: none until rebuilt and proved through a new audit.

## 6. Content and launch corpus

- Buyer sentence: cited fix/deadline pages can answer specific migration
  questions and lead to the free scanner.
- Completeness: generated on-site pages separate provider-sourced dates from
  workload-specific checks and are link-checked. A false universal IMDSv1
  deadline now has a noindex correction route. Twenty-five
  DEV posts were observed, with zero comments on the profile; their old paid
  claims require manual review. Outreach, social, HN, Gumroad, and repost
  material is archived and marked do-not-publish.
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
  Audit v2.
- Distribution: the Action v2 ref and repaired GitHub Pages fallback are public,
  but the Marketplace listing remains stale at v1.1.0; VS is not observed in
  its marketplace, and owned-site traffic is unknown.
- Legal: accurate seller/controller identity, address, governing law, tax
  posture, and $0 incremental hosting confirmation are owner-only gates.
- Remote history: origin/main accumulated synthetic status/benchmark commits and
  low-information weekly pages; the repaired tree is now on main and those
  generators are removed.
- Funnel sprawl: closed Migration Pack, organization, partner, and scanner
  research-list forms were removed. Those pages no longer collect speculative
  leads or promise future features.
