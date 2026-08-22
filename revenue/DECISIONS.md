# Decision ledger — compacted August 22, 2026

The previous multi-thousand-line ledger mixed stale plans, synthetic metrics,
and contradictory handoffs. Git history preserves it. This file records the
current decision chain needed to resume safely.

## D0 — containment is absolute

WORKSPACE_ROOT is /home/nick/Development/active/Rupture. Every local target,
temporary directory, cache, virtual environment, and tool config is kept below
that root. Remote deployment is permitted; local reads/writes outside it are not.

Containment incidents disclosed during this repair:

- early dependency commands were run before project-local pip/npm temp and
  config overrides were consistently set;
- an earlier failed Wrangler invocation wrote its own log outside the jail;
- early Git inspection may have consulted machine Git configuration; and
- the first broad Ruff run had no repository config and may have inherited a
  machine-level configuration.

No outside file was intentionally inspected or cleaned afterward because doing
so would repeat the violation. The repair added workspace-local config/cache
paths and a repository-owned Python lint contract. These incidents are process
failures, not hidden successes.

## D1 — reject the premise that profitability was established

Observed collected revenue is $0, with zero recorded delivered reports and weak
public signal. High gross margin per hypothetical sale is not profitability or
demand. All plans and reporting now distinguish observed evidence from forecast.

## D2 — collapse to one paid offer

Keep one $299 static repository evidence report. Remove surge pricing and reject
customer-controlled urgency pricing. Migration Pack, Drift Watch, Organization
License, public GitHub App, partner/white-label fulfillment, paid bundles, and
subscriptions are closed.

Reason: only a bounded static report can be described and tested truthfully
without customer-specific engineering labor or unbuilt recurring operations.

## D3 — define the report by observable evidence

Audit v2 reports exact file/line matches, observed counts, citations, input hash,
rule/report versions, evidence fingerprint, remediation order, and limitations.
They do not claim AWS-account inventory, runtime reachability, exploitability,
digital signatures, downtime dollars, cost savings, or completeness.

Safe ZIP handling rejects traversal, symlinks/special entries, malformed/binary
input, expansion bombs, excessive files/bytes/ratio, and inputs over the raw
limit. PDF output is written atomically and verified by size/hash before
delivery.

## D4 — fail closed before accepting money

Checkout defaults off. A shared readiness gate covers upload and checkout and
requires the explicit switch, runner, email, correct Stripe mode, writable
storage, no unresolved refund, and no at-risk fulfillment.

Stripe checkout and webhooks verify exact SKU, Price ID, amount, currency,
livemode, and upload binding. Purchases/jobs are committed atomically; jobs use
leases/retries. Refund reconciliation matches exact refund ID, full amount, and
payment. Pending/failed refunds block new checkout and remain operator-visible.

The production gate is a real Stripe test-mode checkout through PDF, Resend,
signed download, verification lookup, retention, and failure refund. Unit tests
cannot substitute for it.

## D5 — minimize retained customer/payment data

Uploads are immutable and signed. Successfully delivered source is deleted
immediately; abandoned uploads expire in 24 hours, checkout-bound input in 48
hours, and reports/verification metadata in 30 days. Stripe webhook bodies are
reduced to operational fields and a migration scrubs older stored payloads.
Public status omits customer/job detail; admin detail requires a token.

## D6 — remove dormant mutation paths

The deployable runner accepts only audit_pdf jobs. Dormant GitHub-App PR code,
sandbox script, JWT/crypto dependency, and automatic platform/email publishers
were removed. The legacy Worker stays only as a default-410 tombstone with its
normal deployment command disabled. Old launch/outreach/Gumroad material is
marked do-not-publish.

Reason: unreachable but executable commerce/contact code is unnecessary attack
surface and invites accidental revival of false products.

## D7 — use free tools as distribution, not separate paid SKUs

The existing GitHub Marketplace Action is Bet A. The VS extension and cited
search pages are compounding acquisition surfaces. All route relevant findings
to the same Audit availability page. No autonomous post, email, DM, bid, or
customer commitment is allowed.

The existing Action identity remains “Rupture AWS Deprecation Check” so v2
updates the live listing rather than fragmenting it. Action paths are confined to
GITHUB_WORKSPACE and dependencies are project-local. The VS extension shares
scanner rule behavior, clears stale diagnostics, supports the documented file
types, and packages only compiled code/manifest/docs/icon/license.

## D8 — make releases reproducible

The static build uses a committed build date and validates source citations and
generated links. CI tests every kit/app, real Action fixtures, VS packaging,
containers, locked dependency graphs, formatting/lint/type checks, and generated
site parity. Python production graphs are hash locked and inventories are
generated from clean installs.

The property gate found a real Node.js 14 IaC omission; the migration set and a
unit regression were repaired, and subprocess property deadlines were disabled
to remove machine-speed flakiness.

## D9 — license and dependency posture

Root ATTRIBUTIONS and resolved inventories describe shipped graphs. Pyphen's
MPL-1.1 option is selected; its implementation/dictionaries are server
dependencies and are not copied into the paid PDF. The VSIX contains no
node_modules. Current pip-audit/npm audit results are clean, but those are
time-stamped checks, not perpetual claims.

## D10 — preserve the jail during container verification

Do not run local Docker builds because the daemon would write image/cache state
outside the workspace. GitHub CI is the remote build environment and must pass
both Dockerfiles after publication.

## D11 — join remote history without force

The working branch is far ahead of its old base while origin/main accumulated
hourly synthetic status/benchmark commits. Remote-only meaningful changes were
an MIT license, AWS date corrections, generated status/calendar files, and
low-information weekly commit-count pages. The repaired tree already preserves
the license and accurate date corrections while intentionally removing the
generators and stale artifacts.

After final verification, commit the repaired tree, fetch the latest main, and
join it with an ours merge so origin/main is an ancestor. This permits a normal
fast-forward push with no force and prevents obsolete generated pages from
re-entering the release tree.

## D12 — current platform/policy choices

- GitHub Actions can update the existing Marketplace listing from a public root
  action.yml and release; the owner must accept terms/use the publish checkbox.
- VS publication requires the owner publisher credential; current Microsoft
  guidance notes global PAT retirement on December 1, 2026.
- DEV requires substantive good-faith posts and owner-controlled publishing;
  old promotional posts are a manual truth-review item.
- Stripe's published fee/refund behavior is used for target math; original
  processing fees are not treated as recoverable after a full refund.

## D13 — cost assumption is a gate

Static distribution uses free GitHub/marketplace surfaces. The API may use
existing GRACE only if the owner confirms $0 incremental cost. If that is false,
checkout remains off and a genuine free-tier deployment must be selected before
accepting money. Revenue arithmetic must include any real cost.

## D14 — correct provider facts before optimizing conversion

Remove the claimed universal December 31, 2025 IMDSv1 enforcement date: AWS
documents account, AMI, launch-option, and instance-type behavior instead. Keep
the old route only as a noindex correction page and queue the false DEV article
for owner unpublication.

Track Lambda nodejs22.x with AWS's projected 2027 dates, but do not call it
deprecated in August 2026. The bounded Lambda rewrite/IaC path now targets the
supported nodejs24.x runtime, and CI exercises it under Node.js 24. Preserve the
old phase-1 URLs for inbound compatibility while correcting their visible names
to create/update restrictions.

Provider status dates and EOLkits workload checks are separate evidence types.
Pages, feeds, badges, structured data, and reports must not imply that a single
AWS runtime-table citation proves every migration concern in every workload.

## D15 — remove speculative funnel branches and release debris

Drift Watch's legacy route now states only that it is unavailable: no planned
price, feature promise, or waitlist. Migration Pack and other closed concepts
remain fail-closed. One paid artifact, one price, and one fulfillment gate are
easier to trust and operate.

The Lambda npm artifact uses an explicit release-file allowlist so cache/test
artifacts cannot enter a package. Both Python kits use current SPDX license
metadata and build without the Setuptools license deprecation warning. These are
release-quality repairs, not customer or revenue signal.

## D16 — make fallback distribution functional and singular

GitHub Pages serves a project path, not a domain root. Its release build now
prefixes static navigation with `/EOLkits` while keeping status, verification,
scanner, widget, and pageview requests on the live `eolkits.com` API origin.
Regression tests cover the split; the committed `docs/` tree remains the
root-domain GRACE artifact.

Remove the Migration Pack, organization-license, partner, and generic scanner
research forms. Closed-product routes are short noindex tombstones with no
checkout, account, waitlist, or future-feature promise; the legacy organization
inquiry API returns 410. The production API's unused Stripe Connect partner
helpers were deleted. This keeps acquisition pointed at one paid artifact.

The durable rate limiter now anchors each window to a key's first request instead
of an epoch boundary. That closes the boundary double-burst found by the final
API run and preserves the configured eight-per-minute lead limit.
