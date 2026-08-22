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
Regression tests cover the split; the committed `docs/` tree is the GitHub Pages
project artifact. The manual GRACE ship path builds a fresh root-domain artifact
immediately before its reviewed rsync, so it does not reuse the project-path
bytes.

Remove the Migration Pack, organization-license, partner, and generic scanner
research forms. Closed-product routes are short noindex tombstones with no
checkout, account, waitlist, or future-feature promise; the legacy organization
inquiry API returns 410. The production API's unused Stripe Connect partner
helpers were deleted. This keeps acquisition pointed at one paid artifact.

The durable rate limiter now anchors each window to a key's first request instead
of an epoch boundary. That closes the boundary double-burst found by the final
API run and preserves the configured eight-per-minute lead limit.

## D17 — publish through the connected GitHub object API

The jailed terminal had no GitHub HTTPS credential, and reading machine Git/SSH
credentials outside WORKSPACE_ROOT is forbidden. Use the already-connected,
repository-scoped GitHub app instead: create changed blobs/trees in bounded
batches, require the final remote tree SHA to equal the local Git tree SHA, make
a two-parent commit on current main, and advance `main` with `force=false`.

This published commit 85c9f43e while retaining both prior histories. The first
five workflows passed. A public probe then showed that GitHub's legacy
branch-source Pages deployment could race and overwrite the custom Actions
artifact. Therefore the committed `docs/` tree itself becomes the `/EOLkits`
project-path artifact, and GRACE's manual ship script builds the root-domain
variant immediately before rsync. Both GitHub deployment mechanisms will now
publish identical bytes. Commit f4ef711e implemented that contract; both Pages
deployments passed and the second public probe confirmed the prefixed navigation
and split API origin.

The first release-surface run after that change exposed one stale CI assertion:
it rejected every `ntoledo319.github.io` URL even though that host is now the
intentional Pages canonical. All twelve non-web jobs passed. Commit b9cf566d
narrowed the assertion to reject unprefixed and legacy URLs, reproduced the web
job locally, and passed the replacement release, determinism, property, and
built-in Pages runs. This failure and correction are release evidence only.

## D18 — make Action v2 usable without impersonating the owner

The repaired README documented `uses: ntoledo319/EOLkits@v2`, but no such ref
existed because GitHub's Marketplace agreement, publish checkbox, and 2FA are
owner-controlled. GitHub's official custom-action guidance permits a branch
named for a release. Create public branch `v2` at the fully verified `3ea1a169`
tree and verify the raw `action.yml` bytes. This makes direct v2 installs work
without claiming the Marketplace page has changed.

Prepare, but do not publicly publish, an honest v2.0.0 release draft using a
path-triggered GitHub workflow and the repository-scoped `GITHUB_TOKEN`. The
draft targets commit `9d369ccb`; its workflow passed and printed the private
draft URL. The automation is idempotent and refuses README copy containing the
retired price claims. Publication remains in HQ-5 because accepting Marketplace
terms and using the owner's 2FA cannot be delegated, and the public v1.1.0
listing remains stale until that action occurs.

## D19 — never send acquisition traffic to an unproved deployment

The public `eolkits.com` site still serves retired products, while the repaired
GitHub Pages build is verified. Therefore route repository, Action report, kit
metadata, kit README, and VS extension links to the Pages project URL. Keep the
Pages static origin and `eolkits.com` API origin separate in the read-only smoke
workflow so deploying the API later does not require sending users back to stale
static pages.

CI now executes the Action fixture and asserts its generated report contains the
Pages Audit URL, tests the compiled VS extension and manifest URLs, and rejects
obsolete custom-domain acquisition paths across distribution sources. Commit
8748cf6a passed the full remote release, determinism, property, Pages, and draft
workflows. Only after those gates passed did the `v2` branch fast-forward without
force to that commit; the private v2.0.0 draft was synchronized to the same tree.

## D20 — recover the observed GRACE static feed without smuggling an API deploy

The production home page reported a 07:17 UTC modification time. The source
branch used by the historically installed GRACE cron had advanced at 06:14 UTC
the same day, proving that the static auto-deploy remained active even though
the repository copy of the cron was retired. That branch still contained the
unsafe multi-product site and was one commit ahead of the history already joined
into repaired main.

Do not force the branch and do not hide infrastructure mutation inside the
static builder. Instead create a two-parent commit whose first parent is the
live branch tip, whose second parent is verified main, and whose tree exactly
matches main. Advancing `marketing-machine-v2` without force to `c3112151`
preserves the remote date correction while giving the next daily static build
the truthful, fail-closed site.

Add a read-only scheduled workflow after the observed deployment window. It
must reject retired prices/products, Pages-only paths on the root domain, and an
Audit form that is not initially gated. This can remove the manual static rsync
from owner labor only after the public probe passes. It cannot deploy or validate
the paid API, reuse secret material, accept Marketplace terms, or establish
demand; those gates remain separate.

## D21 — close the proven Cloudflare bypass before chasing new distribution

The directly reachable pre-rename `rupture-worker` still reported a healthy
production environment with Stripe in live mode. Public DNS sent
`eolkits.com` straight to GRACE, so a route audit alone could not retire that
separate `workers.dev` bypass.

Use the existing repository Cloudflare token only through a narrow workflow.
Test the tombstone first, target the exact historical account and Worker from
repository history, verify public health and commerce paths, and delete a route
only if both its script name and `eolkits.com` pattern match. Early runs exposed
three real deployment facts without changing the public Worker: Wrangler now
requires Node 22+, the token belongs to the pre-migration account rather than
the current TOML account, and the old service retains a Queue consumer. The
final replacement therefore uses Node 24, a dedicated retirement-only config,
and a tested handler that acknowledges stale queue events without invoking any
former fulfillment code.

Run `32591848083` passed. Independent probes confirmed `retired: true` and HTTP
410 for direct checkout, App-install, and Stripe-webhook paths. The old-account
token could not see a unique `eolkits.com` zone and changed no route. Because
the domain resolves directly to GRACE, that route cannot execute today; keeping
the exact Worker as an explicit tombstone is also safer than deletion if routing
is changed later. Remove the three-minute Cloudflare task from the owner queue.
This is risk retirement, not demand or revenue; collected revenue remains zero.

## D22 — retire the exact Stripe catalog before reopening one verified SKU

The GRACE production API still exposes charge-capable checkout handlers for the
retired Audit, Migration Pack, and Drift products. Closing only public links or
the old Cloudflare Worker is insufficient: a stale server can create new
Checkout Sessions directly from an active Price ID. Treat this as the primary
commercial blocker, ahead of additional acquisition work.

Publish a manual, owner-gated Stripe retirement workflow rather than asking the
owner to make a long sequence of error-prone dashboard edits. It accepts only
the exact repository, `main` ref, repository owner as both actor identities, and
the confirmation phrase `RETIRE_EXACT_EOLKITS_STRIPE_2026_08_22`. Its temporary
admin Worker remains fail-closed on public routes and uses a short-lived bearer
token. The audit validates the six known live Prices, their four Products,
amounts, currencies, billing types, and the six historical Payment Link URLs;
it refuses to silently absorb unexpected catalog state.

Before mutation, enumerate open Checkout Sessions, recent completed live
Sessions, subscriptions in every status, and subscription schedules including
phase items and add-invoice items. Apply catalog mutations sequentially, then
repeat an independent audit. Any observed open, paid, subscribed, scheduled, or
unexpected object leaves `containment_complete` false and requires review even
if an object transitions during the run. This favors evidence preservation over
a misleading green result.

Archive all six historical Prices, including the canonical $299 Price. The
$299 Price is the only SKU eligible for later reactivation, but only after the
closed Audit v2 deployment completes a real Stripe test-mode upload-to-PDF,
delivery, verification, retention, and refund exercise. At launch, reactivate
that Price alone; do not revive a historical Payment Link or any other SKU.

Removing the Worker's `STRIPE_KEY` binding prevents the current service from
using the credential, but Cloudflare version history can retain earlier secret
snapshots. Therefore account-level Stripe key rotation/revocation remains an
owner-only step in the same batch. The source, 39 focused Worker tests, dry-run
bundle, YAML, ShellCheck, and public tombstone reassertion passed at main commit
`e4109e3e`. The production workflow has not run, so no Stripe state changed and
collected revenue remains $0.

## D23 — measure price-qualified demand without reviving unsafe commerce

Anonymous page beacons against the stale custom-domain backend cannot answer the
commercial question: GitHub Pages CORS rejected them, the old store retained
them indefinitely, public low-volume counts leaked activity, and raw URL
attribution could carry sensitive values. Do not send more acquisition traffic
into that system or treat repaired tracking code as demand.

Use a GitHub-native signal that works before deployment. Show a structured
`$299 Audit interest` issue form only after an actual browser or Action finding,
and on the explicitly closed Audit gate. Require acknowledgement of a real
finding, one static $299 report, purchase consideration, public visibility, and
the prohibition on project/company/security/personal data. State that it is
nonbinding and not an order, reservation, waitlist, support request, or promise
of follow-up. This is inbound research, not autonomous human contact.

Measure only public lower bounds in a scheduled read-only workflow: distinct
external human issue authors, near-term purchase windows, and public exact
`@v2` code references. Never commit synthetic counters, comment on issues, or
call interest revenue. Baseline every count at zero and apply Bet A's five-day
falsifier after the surface is live.

Prepare future first-party telemetry safely: no cookies, local storage,
referrer, visitor ID, repository name, or secret-bearing field; exact Pages CORS;
v2 capability gating; canonical path/token schemas; 2 KiB bodies, 60/hour per
source, 2,000/day global, 128 MiB shared-database guard; 30-day event and two-day
rate-key retention; public readiness only, with detailed funnel/commerce/jobs
admin-only and `no-store`. This hardening permits later directional measurement
after the real v2 deploy, but it does not authorize deployment or checkout.
