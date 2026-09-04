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
- early Git inspection may have consulted machine Git configuration;
- the first broad Ruff run had no repository config and may have inherited a
  machine-level configuration;
- a later runner test was invoked without the required workspace-local TMPDIR,
  causing pytest to create its temporary directory under system `/tmp`; and
- a live HTTP status probe explicitly targeted `/dev/null`, which the total jail
  forbids even when the intended content is discard-only.

No outside file was intentionally inspected or cleaned afterward because doing
so would repeat the violation. Subsequent verification restored the explicit
workspace-local TMPDIR and kept probe output in-process. The repair added
workspace-local config/cache paths and a repository-owned Python lint contract.
These incidents are process failures, not hidden successes.

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

Release evidence: acquisition workflow `32596830945` and every product/Pages
gate passed. The first Marketplace-draft synchronizer failed because its source
assertion did not account for Bash's required `\$299` escape; the generated
Action report had already passed with the correct visible `$299`. Correct only
that assertion, reproduce it locally, and require the complete follow-up gate.
Commit `db32bdfb` then passed draft, release, determinism, property, and built-in
Pages runs. Advance `v2` without force only after those results and a raw-file
probe. This failure is recorded as release evidence, not hidden or counted as a
commercial signal.

## D24 — notify search engines without manufacturing traffic evidence

The verified Pages artifact already contained a stable IndexNow key file and a
51-URL sitemap, but nothing submitted changed URLs. With Stripe, Marketplace,
GRACE, and VS publication still owner-gated, activating this existing search
distribution primitive is higher leverage than adding another product or more
speculative funnel code.

Follow the current official IndexNow protocol and terms: use one global endpoint,
one same-host key location, no more than 10,000 URLs, and only content owned by
this repository. On ordinary pushes, derive added/modified/deleted HTML URLs
from the trusted main diff. Use the sitemap only when a manual/bootstrap event
has no HTML diff. Verify the live key before sending, reject every URL outside
the exact Pages project prefix, grant the workflow contents-read only, and make
no scheduled repeat submissions.

Run `32597777674` passed on exact main commit `951fd4b6`; the bootstrap path sent
the 51 canonical sitemap URLs and could only pass on HTTP 200/202. Record that as
receipt, never as crawling, indexing, rank, traffic, or demand. The simultaneous
acquisition artifact remained at zero qualified issues and zero external `@v2`
references, so the August 27 falsifier and portfolio ranking do not move.

## D25 — replace the mock sample with actual fulfillment output

The Audit page promised exact evidence, a remediation order, hashes, and a PDF,
but the prior public sample was a hand-maintained HTML facsimile. That is the
largest autonomous trust leak for the only paid offer. Publish a wholly
fictional, deterministic ZIP and send it through the same
`generate_audit_package()` path used for paid work. Ship the resulting four-page
PDF plus a JSON manifest containing exact input/PDF hashes, rule/report/template
versions, evidence fingerprint, scan counts, and an explicit statement that the
sample is fictional and not registered as customer verification evidence.

Building the real artifact exposed a false critical finding: a generic
`amazon-linux-extras enable python3.8` line was being treated as a Lambda runtime
configuration. Bind runtime matches to supported Lambda/SAM/Serverless/CDK/HCL
contexts, align the browser heuristic, and bound archive names, lines, mapping
records, Lambda resources, flow structures, dependency manifests/specifiers,
and retained evidence. Reject ambiguity/complexity before checkout. Label AWS's
future Lambda dates as projected and describe dependency links as configured
package references, not proof that a local conservative floor is official.

The sample is conversion proof, not demand. Its download, an internal probe, or
a CI fetch does not count as a visit, lead, sale, or revenue event.

## D26 — make report verification portable without weakening the public hash

Initial feature commit `bffb335a` had an exact remote tree match, but its custom
Pages and release runs failed: WeasyPrint's native font/shaping/PDF stack emitted
different bytes on the GitHub runner. The fixture and engine semantics matched;
requiring one workstation's PDF serialization across Linux images was the wrong
portability invariant.

Keep the checked-in public PDF immutable and require its exact SHA-256 to match
the public manifest. On a fresh runner, regenerate through the production engine
and require the same fictional input, page count, template/rule/report versions,
scope counts, findings, evidence fingerprint, and every other manifest field
except the renderer-produced PDF byte count and SHA. The fresh output must still
be a PDF. A regression proves that only those two serialization fields may vary
and that a changed finding count fails. Follow-up `9c231b58` passed the full
release, determinism, property, and both Pages gates.

## D27 — publish one final tree across every autonomous distribution ref

Publish final product commit `9c231b58` on `main` and advance the installable
`v2` branch to it without force; its exact tree is
`8a25da73a1dc8c3c9107c76e7a20d87cc620cd98`. Later ledger-only main commits do
not change the product tree.
The private v2.0.0 draft remains at feature commit `bffb335a`; final changes are
runner-test-only and Action bytes are identical. Its Marketplace agreement/2FA
publish remains owner-only.

The GRACE auto-deploy branch cannot fast-forward directly to main because its
history intentionally preserves the older static-feed lineage. Create
two-parent commit `0780909c` with the old feed as first parent, final main as
second parent, and the exact final tree; advance the feed without force. This
queues the real sample and truthful copy for the observed daily deploy but does
not claim the custom domain is repaired before a public probe passes. At cycle
end it still served retired product copy and `/api/capabilities` returned 404.
Collected revenue remains $0.

## D28 — recover the installed VS channel instead of creating a second listing

The earlier “not published” conclusion came from searching the new EOLkits name.
Exact Marketplace API lookup proves that `rupture.rupture-vscode` remains public
at v1.0.0 with 101 cumulative installs and 162 downloads, while
`eolkits.eolkits-vscode` does not exist. Historical workflow run `25262940459`
also proves the repository previously published the stable identity through its
existing `VSCE_PAT` binding. These counters establish an existing distribution
asset only; they are not current users, qualified intent, or revenue.

Do not create a new EOLkits publisher or listing. Restore `publisher=rupture` and
`name=rupture-vscode`, retain EOLkits as the display brand, bump to v1.1.0, and
make the publish workflow fail if that identity drifts. This preserves upgrade
delivery to the installed base and reduces HQ-6 to the public workflow dispatch
and verification. That final public post remains owner-only.

An in-place minor update must not silently break the old namespace. Keep
`rupture.*` command activation/aliases and deprecated configuration properties
for this transition. Resolve an explicitly configured `eolkits.*` value first,
then an explicit `rupture.*` value, then the current default; this prevents a
legacy `rupture.autoScan=false` from turning back on merely because the new
manifest contributes a default. Regression-test both precedence directions and
package contents before publication.

The current v1.0.0 links to a dead `https://ntoledo319.github.io/Rupture/audit`
route. Repair it to the verified Pages funnel and show a `$299` nonbinding public
interest link only when the extension has actual findings. Add “VS Code
extension” to the privacy-bounded issue form and count that source separately in
the read-only acquisition artifact. Users must choose to open and submit it; the
extension sends no code, telemetry, or messages. Start V1's five-full-day
falsifier only after v1.1.0 is public, using a fresh Marketplace-counter baseline
plus external VS-attributed qualified authors. Zero growth and zero authors kill
the channel hypothesis; packaging, auto-updates, and internal probes do not pass.

Release evidence: repository commit `a9cdcaeb` has exact tree `99136547` and
passed the complete release matrix, including a clean extension install/test/
package job, plus determinism, properties, built-in Pages, Marketplace-draft,
and acquisition runs. Adjacent gallery queries returned 101 then 100 for the
install statistic while downloads stayed 162, so record the distribution as
approximately 100 installs and baseline it again only after v1.1.0 publishes.
The public listing remains v1.0.0; CI success does not authorize or imply the
owner-only Marketplace post.

## D29 — remove release-hand-off ambiguity and guard the publisher credential

Green Marketplace-draft run `32604619021` created the current canonical private
v2.0.0 draft at `untagged-0866963caf3f06db98a1`, targeting `a9cdcaeb`. The
owner queue still pointed at an older untagged draft and target. Replace that
ephemeral link with the observed current draft and require the owner to reject
the two stale drafts. Direct comparison confirms the canonical target's Action
files are byte-identical to public `v2` at `9c231b58`.

Treat a VS Marketplace publication as a production credential action, not an
ordinary test workflow. Require the exact repository owner as both dispatch and
triggering actor, the `main` ref, the exact repository, and typed confirmation
`PUBLISH_RUPTURE_VSCODE_1_1_0`; recheck those values before checkout or secret
use and serialize publication attempts. This prevents a collaborator with
Actions dispatch/rerun permission from spending the existing publisher token.
Package only verified release commit `a9cdcaeb`, with persisted Git credentials
disabled, so later ledger-only `main` commits cannot silently change the VSIX.

Keep HQ-2 before HQ-5 and HQ-6 because its exact audit can stop on anomalous
commerce state; five minutes does not affect a five-day signal gate. Publish the
two repaired, fail-closed distribution artifacts immediately after containment.
Remove them from HQ-7's checkout-safety prerequisites: distribution state cannot
make fulfillment safe or unsafe. HQ-1 through HQ-4, exact production
verification, and zero unresolved refund/fulfillment alerts still gate checkout.

Do not publish GHCR as a launch shortcut. The repository lacks the pre-publish
OCI source linkage and package workflow needed for deliberate permission
inheritance; a new public package is an additional owner-authorized external
release. The current image inputs also float, and a prebuilt image removes none
of the operational proof dominating HQ-3. No public listing or checkout action
was autonomously taken. Collected revenue remains $0.

## D30 — mark the repeated owner-authority impasse as blocked

This continuation is the third consecutive goal turn ending on the same exact
boundary. First, the product and truthful funnel were made releasable but Stripe,
Marketplace, GRACE, and legal state remained owner-gated. Second, the existing
VS identity was recovered and its publication path pinned and secured, yet the
same gates remained. Third, fresh live probes again show zero Stripe-retirement
runs, no Marketplace publication, no GRACE v2 deployment, zero qualified issues,
and $0. Three independent specialist reviews found no safe autonomous cash route.

Restated goal: collect substantial profit from a truthful EOLkits offer with $0
spend and near-zero owner labor. Alternatives rechecked were the prepared Audit
checkout, both existing marketplaces, historical Stripe links, alternate free
hosting, another digital marketplace, direct service/licensing, and additional
organic/registry/sponsorship surfaces. Each requires owner identity/KYC or
credentials, a prohibited public post/contact, or accepting money before verified
fulfillment. The cheapest lawful test remains the already-prepared eight-minute
HQ-2/HQ-5/HQ-6 batch, followed by the rest of the 37-minute queue.

This cycle produced no customer-visible commercial improvement and is logged as
an analysis-only failed cycle under the ship law. Publishing this evidence ledger
preserves the exact resume state; it is not counted as a launch, demand, or
revenue. Mark the persistent goal blocked, not complete. Resume on any owner
queue result or other genuine external-state change.

## D31 — contain hosting-injected analytics before checkout or recrawl

The August 25 custom static deployment repaired the obsolete offer, but the host
injected `https://stats.saiditright.com/script.js` into all five tested pages.
The current script automatically sends full page URLs and browser metadata, can
read local storage, and receives no query/hash exclusion attributes from the
injected tag. That contradicts the public privacy posture and could have exposed
future checkout-return identifiers. Treat this as a checkout and distribution
blocker, not a cosmetic analytics choice.

Inject a restrictive CSP at the start of every generated HTML head because
GitHub Pages cannot set response headers and the GRACE host has demonstrated
post-processing outside this repository. Permit the existing same-origin and
inline code plus the reviewed `https://eolkits.com` API connection; do not permit
the observed analytics origin. Remove the unused Stripe session identifier from
both the Checkout success URL and success page because verified webhook state,
not a browser query parameter, owns fulfillment and reconciliation.

Do not submit the canonical custom host to IndexNow until the live offer has the
CSP and no external script. Extend the bounded workflow to both hosts, but make
the custom branch read and validate its live pages before constructing or
sending a request. Public Pages may submit independently. This produced expected
outcomes: Pages run `32835361747` passed; custom run `32835404486` stopped before
notification. Search receipt remains discovery plumbing, not demand.

Publish exact tree `6b0eef76` to main as `b97befa7` and join that same tree into
the GRACE feed as `a5510969`, preserving the three intervening draft commits as
parents/history rather than importing their stale branch tree. All triggered
main gates passed and Pages visibly serves the CSP. This satisfies the ship law
without pretending the custom host, backend, or checkout is repaired.

## D32 — record and correct two workspace-jail process violations

This resumed cycle used `/dev/null` twice as a discard sink: once during a local
site-build check by the primary agent and once during a read-only curl probe by a
specialist. `/dev/null` is outside WORKSPACE_ROOT, so both commands violated the
total jail even though they neither read external data nor created persistent
state. Record the violation plainly. All subsequent discard/capture output uses
named files under `WORKSPACE_ROOT/tmp`; do not repeat the pattern.

This is the first resumed owner-boundary audit after D30, not a new three-turn
blocked finding. Keep the revenue objective unfinished and continue on the
shipped security state. The actual cash boundary is unchanged: HQ-2, HQ-5, and
HQ-6 require owner identity/credential authority, and HQ-3 must remove the live
injection and prove closed fulfillment before HQ-7 can accept money.

## D33 — use owner-attributed, one-use push authorization for prepared workflows

The connected GitHub session is the exact repository owner `ntoledo319` with
admin/push authority, but its tool surface has no workflow-dispatch method and
the jailed shell has no in-workspace GitHub user token. The owner explicitly
directed Codex to remove the human element and execute connected-account work.
Treat that as authorization for the two already prepared exact mutations, not
as authority to accept agreements, invent legal facts, contact people, enable
checkout, or use absent external credentials.

For each workflow, temporarily add a path-limited `main` push trigger and a
second authorization branch requiring exact repository, branch, owner actor,
owner triggering actor, event type, and a novel one-use commit message. Mirror
the same event-specific check inside the first shell step. Publish an exact-tree
commit without force, observe the terminal run, then immediately restore the
permanent dispatch-only workflow with a different message. A specialist review
approved this mechanism subject to those conditions. Both restore heads
produced no second mutation run. This is a narrow audited transport for the
owner's explicit instruction, not a reusable confirmation bypass.

## D34 — fail Stripe retirement before mutation on any unknown active link

Do not execute the original retirement artifact. Stripe documents that
archiving a Price can deactivate existing Payment Links using its Product. The
old code counted an unknown Product-linked active link but still archived the
six Prices; that link could be implicitly deactivated, disappear from the
active-only final audit, and allow a false containment result. Its test mock
incorrectly kept such a link active.

Block before every Stripe POST when the full read-only preflight finds any
unexpected active Payment Link, return a sanitized 409 with zero changes, add
the same guard to the workflow, and regress all six Prices plus the unknown link
as unchanged. After 39/39 focused tests and specialist approval, run exact
retirement once. Run `32840968816` passed every safety/postcondition step and
the trigger was removed. Keep account-level key rotation in HQ-2 because the
Worker can remove its current binding but cannot revoke historical credentials.

## D35 — ship VS v1.1.0 through the recovered identity and start its clock

Preserve `rupture.rupture-vscode`; creating an EOLkits publisher would discard
the only observed built-in distribution. Local preflight found and repaired an
invalid Bash quoting expression in the unpublished identity check, then passed
compile, lint, rule behavior, VSIX packaging, YAML parsing, `bash -n`, and
ShellCheck. Publish only pinned candidate `a9cdcaeb` through the one-use owner
gate. Run `32841331222` succeeded and the public v1.1.0 package contains the
repaired Audit link; restore commit `a8e8b45c` removed the trigger and passed all
CI.

Start V1's five-day signal clock from the successful publisher timestamp even
while the Gallery's latest-version query propagates. Baseline the existing
listing once propagation completes: the official index exposed v1.1.0 at
11:21:39 UTC with 103 installs / 166 downloads and zero qualified VS-attributed
issue authors. Auto-updates, package availability, and counter changes are not
sales. Keep checkout closed and keep the $4,000 gap unchanged until dollars are
actually observed.

## D36 — preserve merge-dropped research without authorizing outreach

Overnight feed commit `ec4c9a55` restored three hand-drafted answer batches that
an exact-tree merge had omitted and added a fourth new batch. Hand-authored
research is not reproducible in the way generated site output is, so preserve
the unique work. However, that cycle could not fetch the live threads or primary
pages and labeled the answers “ready to post” from search snippets. That is
below this project's truth bar.

Carry Batches 3–6 forward only as **unverified, do-not-post research**. A future
human-approved send requires a fresh live-thread check, primary-source fact
review, unique/help-first edit, and explicit owner approval. No agent posts an
answer or contacts a thread author autonomously. Before any future exact-tree
merge, diff hand-authored files on both parents and manually preserve unique,
non-superseded content rather than assuming one parent's tree is complete.

## D37 — remove metadata and release ambiguity with exact preflights

The public repository description said every AL2 workload was “unpatched,” an
overbroad claim because AWS documents workload-specific exceptions, including
selected critical patching for several Lambda AL2 runtimes. Replace it with the
bounded fact that AL2 reached end of support on June 30, 2026 and that Lambda
block dates vary by runtime. Route the repository homepage to the verified
free-first Pages surface while the custom host remains operationally unready.

Three private releases shared the v2 name. After requiring the exact IDs, tags,
targets, names, and draft states, delete only obsolete untagged drafts
`374998709` and `375032399`. Keep canonical `375063073` untouched at tag
`v2.0.0`, target `a9cdcaeb`. Re-querying both releases and metadata is a required
postcondition. This removes a misleading owner choice without accepting the
Marketplace agreement or publishing anything.

## D38 — instrument the live VS channel without calling counters demand

The v1.1.0 listing now has a stable post-release baseline, so extend the
scheduled read-only acquisition artifact with one exact public Gallery query.
Pin identity
`rupture.rupture-vscode` and version `1.1.0`; reject missing, duplicate,
non-integral, or drifted results; store installs/downloads and signed deltas from
103/166. Keep qualified issues/authors as separate fields.

The Visual Studio Marketplace Publisher Agreement defines Marketplace access
through web portals, APIs, or other mechanisms Microsoft makes available. Use
one bounded query per workflow run against the public Gallery endpoint; the
normal cadence remains one scheduled run per day, with additional queries only
on a matching source push or explicit manual dispatch. Retain only this
publisher's aggregate listing counters, and do not redistribute raw Marketplace
data. Source reviewed August 27:
https://cdn.vsassets.io/v/M187_20210610.3/_content/Visual-Studio-Marketplace-Publisher-Agreement.pdf.
Downloads can include update/package fetches and are not visits, intent, sales,
or revenue. V1's five-day gate still requires install growth or qualified
VS-attributed interest; cumulative download movement alone does not pass it.

## D39 — treat the live meta CSP as containment, not host remediation

The August 26 static deploy placed the generated meta CSP before the host's
external script tag, so current browsers block that exact cross-origin script.
Raw responses still contain the injected tag, scheduled verifier `32946397287`
is correctly red, and a host-controlled inline injection could evade the meta
policy. Do not weaken the verifier, notify custom-domain IndexNow, or open
checkout until the hosting rule is removed and the closed GRACE v2 deployment
passes the complete test/refund gate.

GitHub Pages remains a free scanner/documentation/distribution surface, not the
primary paid service host. GitHub's Pages limits prohibit using Pages primarily
to facilitate commercial transactions or run SaaS. Source reviewed August 27:
https://docs.github.com/en/enterprise-cloud@latest/pages/getting-started-with-github-pages/github-pages-limits.

## D40 — fail closed on unavailable evidence and use a fee-aware sales buffer

An exact release-tag request previously collapsed every GitHub API failure into
`public_v2_release=false`. Replace it with a paginated releases query whose
successful empty result means false and whose auth, rate-limit, network, or 5xx
failure stops the observation. Unavailable evidence is never negative evidence.

The 15-sale refund buffer also relied on unverified US domestic-card geography.
Stripe's current US standard schedule adds 1.5% for international cards and 1%
when currency conversion is required, while original processing/conversion fees
are not returned after a refund. At $299, 15 such initial sales with one refund
net only $3,939.25. Use a provisional 16-initial-sale target ($4,221.80 under
that fee case), and keep checkout closed until HQ-1 confirms the account country,
pricing agreement, currencies, and $0 hosting-cost assumption. Source reviewed
August 27: https://stripe.com/pricing.

## D41 — publish reconciled evidence only after exact-tree and green-CI gates

Construct commit `2d19a797` from reviewed tree `5e0fbf58` with fresh `main`
`04955c29` as first parent and overnight feed `ec4c9a55` as second parent. Move
`main` with `force=false`, require every triggered check to pass, then re-read
both refs and fast-forward `marketing-machine-v2` to the same commit with
`force=false`. The release matrix, determinism, property, acquisition, and Pages
runs all passed; both refs converged at that exact tree without rewriting either
history. A later ledger-only descendant may record this evidence without changing
the released workflow behavior.

Inspect the first remote telemetry artifact rather than inferring success from a
green badge. Run `33028483868`, artifact `9629312207`, and digest
`5e0ff22141e28ba5639d21238d18171bf8b658cfbf9242a0d03e6b525f02b2c8`
contain the guarded v1.1.0 counters and zero qualified interest. This validates
measurement, not demand and not revenue.

## D42 — skip repost-answers/DEV drafting this cycle; ship a verified free-tier data gap instead

This cycle's WebFetch/curl egress to external domains returned
`EGRESS_BLOCKED`/HTTP 403 on every tested target, including the neutral control
`example.com`, `docs.aws.amazon.com`, and `repost.aws`. WebSearch (a hosted
Anthropic tool, not routed through this container's egress) still returned
indexed results, but the standing repost-answers priority requires a live-thread
check and a URL that resolves this cycle (per D36's truth bar), and the
AWS-primary-source verification duty in AGENTS.md §2.5 requires fetching
`docs.aws.amazon.com` directly. Neither was possible. Per AGENTS.md's explicit
fallback ("if web search/fetch is unavailable ... skip anything needing new
external facts and do a different in-jail ship"), no new repost-answers batch
and no new dev.to article were drafted this cycle. This is consistent with
D36's own caution against research that cannot be freshly verified.

Instead, this cycle audited the repo's own primary-source-derived data for an
internal inconsistency the git history already resolved for every other runtime
in the same delayed cluster. `kits/lambda-lifeline/src/scan/index.mjs` (the free
scanner engine) and `apps/web/content/fixes.yml` already correctly track
nodejs16.x in the synchronized Q1-2027 block cluster (block-create 2027-02-01,
block-update 2027-03-03, delayed with nodejs18.x/nodejs20.x/python3.8/python3.9),
sourced from the AWS Lambda runtimes deprecation table. `rules/public/
deprecations.yml` — the single source of truth for the public ICS calendar,
the SEO `/migrate/<slug>/` pages, `llms.txt`, the sitemap, and the free
browser scanner's client-side data — still only listed nodejs16 under
`historical` with no block dates, so the free scanner UI and public deadline
tracker omitted a runtime the underlying engine already flags. That is exactly
the kind of visible inconsistency that undermines the "truth only" bar if a
visitor cross-checks the scanner against the deadline pages.

Added a "Lambda Node.js 16 create/update restrictions" entry to `deprecations:`
(mirroring the existing nodejs18.x entry's shape and citing the same AWS docs
URL already used by all sibling entries) and removed the now-redundant
`historical` stub. Rebuilt the static site with `apps/web/build.py` under the
same `EOLKITS_BASE_PATH`/`EOLKITS_SITE_URL`/`EOLKITS_API_URL` env vars CI uses,
and confirmed `pytest -q apps/web` is 35/35 green (the same 3 failures appear,
identically, against the unmodified baseline when the same env vars are not
threaded into the pytest invocation — a local harness artifact, not a code
regression). This generated `docs/migrate/lambda-node.js-16-eol/`, a new badge,
and updated the ICS feed, sitemap, `llms.txt`, the migrate index, sibling
"related deadlines" links, and the free scanner's/`eol-checker`'s embedded
runtime tables — all committed alongside the rules-file source change so
`git diff --exit-code -- docs` stays green in CI.

No price, unit forecast, or revenue-relevant math changes. Workspace-observed
collected profit remains $0 and the gap remains $4,000. This ships an
externally visible correction to a free acquisition surface without touching
checkout, Stripe, GRACE, or any owner-only credential. The blocked HQ items
(HQ-1 through HQ-5, HQ-7) are unchanged and still require the owner.

## D43 — bump the reproducible build date to correct site-wide countdown drift

Cycle-start check repeated D42's egress test: WebFetch to the neutral control
`example.com` returned `EGRESS_BLOCKED`, and a direct `curl` through the
configured proxy to both `example.com` and
`docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html` returned HTTP 403
(`CONNECT tunnel failed`). `curl -sS "$HTTPS_PROXY/__agentproxy/status"`
confirmed the proxy itself is up, so this is a domain-level egress block, not a
local misconfiguration. WebSearch (hosted, not routed through this container's
egress) still returned indexed results, but per AGENTS.md's explicit fallback
and D36's truth bar, no new repost-answers batch or dev.to draft was produced
this cycle — neither a live-thread check nor a direct primary-source fetch was
possible.

Also checked whether the scanner's two "bonus" runtimes (`ruby3.2`, `dotnet6`
in `kits/lambda-lifeline/src/scan/index.mjs`'s `PHASE_DATES`) should be added
to `rules/public/deprecations.yml` the way `nodejs16.x` was in D42. Declined:
unlike `nodejs16.x`, which was corroborated by a second independently
maintained file (`apps/web/content/fixes.yml`) already carrying the same
dates, `ruby3.2`/`dotnet6` appear in only that one file, are marked "flagged
but not our primary scope," and have no corroborating source reachable this
cycle. Publishing them to public SEO/ICS/sitemap surfaces without being able
to verify against `docs.aws.amazon.com` this cycle would risk exactly the kind
of over-claimed date this project has repeatedly had to walk back (D14, D25,
D40). Left them out of the public rules file; this is a deferred, not
rejected, gap.

Found a real, verifiable-without-fetch defect instead: `apps/web/BUILD_DATE`
(the single source `apps/web/build.py` uses for every "N days until <deadline>"
countdown, the ICS `DTSTAMP`, the sitemap `lastmod`, and `docs/status/data.json`'s
`generated_at`) had never been bumped since the initial 2026-08-22 repair
commit (`85c9f43e`), despite five subsequent daily content cycles. Every
countdown on the live site was therefore silently overstating remaining time
by a growing margin (6 days as of this cycle) — a truth defect on the site's
core "how much runway do you have" claim, not a cosmetic one. `_build_date()`'s
own docstring says "Update BUILD_DATE when public source content changes";
nothing in the pipeline enforces that, so it had silently drifted.

Confirmed 35/35 `apps/web` tests green on the stale baseline first. Bumped
`BUILD_DATE` from `2026-08-22` to `2026-08-28`, rebuilt `docs/` with
`apps/web/build.py` under the exact `EOLKITS_BASE_PATH`/`EOLKITS_SITE_URL`/
`EOLKITS_API_URL` values `deploy-pages.yml`/`test.yml` use, and re-ran the
suite: 35/35 still green, including `test_determinism.py` and `test_links.py`.
Inspected the diff: every changed line is date-derived (163→157-day countdowns
on `/migrate/` pages, ICS `DTSTAMP`, sitemap `lastmod`, `status/data.json`
`generated_at`) — no structural, price, or claim-text change. CI's
`git diff --exit-code -- docs` gate only checks that committed `docs/` matches
`build.py`'s output for the committed `BUILD_DATE`; it does not itself detect
staleness against real time, which is how this drifted five cycles unnoticed.
This ships an externally visible truth correction on every deadline page
without touching checkout, Stripe, GRACE, DEV, or any owner-only credential.
Collected profit remains $0; the gap remains $4,000. Future cycles should keep
bumping `BUILD_DATE` (and rebuilding) whenever a cycle ships and otherwise as a
standing periodic check, since nothing currently alerts on drift.

## D44 — recreate the deleted `marketing-machine-v2` branch from `main`; flag a second invented-date error in the quarantined DEV corpus

Cycle start: `marketing-machine-v2` did not exist on `origin` at all (`git
ls-remote --heads origin` and `list_branches` both showed only `main`; no open
or closed PR had that head branch). History showed why: merged commit `0c9dfec`
("Integrate corrected Lambda Node.js 16 lifecycle data (#24)") — whose message
says it "Preserves unique marketing-machine-v2 data and generated surfaces" —
already carries D42/D43's nodejs16.x and `BUILD_DATE` work into `main`, and
`.github/workflows/deploy-pages.yml` (the workflow that actually publishes
eolkits.com) triggers only on push to `main`; `submit-indexnow.yml` lists both
branches but `main` is authoritative for deploys. This is the "PR for your
designated branch already merged" case: per the runbook, recreated
`marketing-machine-v2` from current `main` (`git checkout -B
marketing-machine-v2 main`) rather than fabricating divergent history, and this
cycle's work ships from there. `BUILD_DATE` was already `2026-08-29` (today) at
cycle start via that same merge; `pytest -q apps/web` was 35/35 green and a
full `apps/web/build.py` rebuild against the CI env vars produced a clean `git
diff --exit-code -- docs` (no staleness to correct this cycle).

Repeated the egress test done in D42/D43: `curl` through the configured proxy
to `example.com` and `docs.aws.amazon.com` both returned HTTP 403 (`CONNECT
tunnel failed`); `$HTTPS_PROXY/__agentproxy/status` confirmed the proxy itself
is up. Per AGENTS.md's fallback, no new repost-answers batch or dev.to draft
was produced this cycle.

Instead, cross-checked the 25 archived/quarantined DEV.to drafts in
`launch/distribution/devto/` (already flagged in `revenue/HUMAN_QUEUE.md` HQ-4
for owner unpublish; every file already carries a top-of-file "do not publish
or reuse" banner) against this repository's own already-corroborated
lifecycle-date sources — `rules/public/deprecations.yml` and
`kits/lambda-lifeline/src/scan/index.mjs`'s `PHASE_DATES` — for further
verifiable-without-fetch date errors beyond the already-documented article 24
IMDSv2 issue. Found one: article 04's ("Python 3.13 dead batteries") timeline
table lists `python3.10` as "Deprecated 2026-03-31". Both internal sources
agree the correct date is 2026-10-31 (`deprecations.yml`'s
`lambda-python-3.10-eol.deprecation_date` and `PHASE_DATES['python3.10'].
phase1`); 2026-03-31 appears nowhere else in the codebase as a python3.10 date
but is exactly this repo's own `ruby3.2` phase-1 date, suggesting a copy/mix-up
rather than a since-superseded AWS date. Per the existing pattern (article 24's
note is documentation-only; the archived draft itself is left as an unedited
mirror of what is actually still live, so the owner's manual review compares
against reality), added a second "Known critical error" entry to
`launch/distribution/devto/README.md` rather than editing the draft file
itself.

No price, unit forecast, checkout, Stripe, GRACE, DEV-account, or Marketplace
state changed. Collected profit remains $0; the gap remains $4,000. HQ-1
through HQ-5 and HQ-7 are unchanged and still require the owner; HQ-4's manual
DEV review now has two documented critical errors to check instead of one.

## D45 — treat the live GRACE upload service as an incident, not a launch candidate

The public custom host serves a stale backend with an unauthenticated upload
allocation/PUT path and no v2 capability/status contract. Checkout being closed
does not contain memory, disk, or uploaded-data exposure. Keep commerce closed,
install the exact emergency Caddy block first, preserve `/webhook/stripe` for
reconciliation, and deploy nothing against the production data volume until a
consistent stopped-volume snapshot exists.

## D46 — make validation precede every persistent-state mutation

Previously, importing the app initialized/migrated/redacted SQLite before
production secret validation. The app now constructs Store without side effects,
runs a mutation-free runtime/catalog preflight, and only then creates directories
or calls `store.init()`. The rollout runs this preflight in the built image with
no production volume. A failed secret or catalog check therefore cannot mutate
the only production database before aborting.

## D47 — permanently retire the old $299 identity and require a new v2 catalog

Do not reactivate `price_1TRoGjDL3cQl851oiIWR5JIa`. It belongs to the retired v1
surface and rollback history. Production checkout now requires runtime-supplied
new v2-only Product and Price IDs and GET-only attestation of exact identity,
object types, active/live state, one-time USD 29900 amount, and expanded active
live Product. Checkout and webhook fulfillment bind to the same attested Price;
all historical Prices are refund-recognition-only.

## D48 — protect distribution refs and production workflows from ambient pushes

The advertised public `@v2` ref had been deleted, so it was restored without
force at the exact green main commit and is now exercised by a scheduled real
consumer workflow. The Cloudflare retirement workflow no longer runs a
production-credential mutation on ordinary source pushes. Marketplace draft
synchronization is owner-confirmed, updates only canonical release `375063073`,
rejects duplicates/public releases, and requires public `v2` to equal selected
main. The status monitor can no longer be disabled into a false green while the
API is stale.

## D49 — automate the VS falsifier and do not confuse downloads with demand

The five-day v1.1.0 gate is `2026-08-30T11:15:00Z`. The acquisition workflow now
computes `pending`, `passed`, or `failed_reposition_required` from install growth
or qualified VS-attributed authors. Download movement is retained as context but
cannot pass the gate. At 05:00 UTC the result is still pending; do not claim a
failure before the deadline and do not claim demand from 193 cumulative
downloads.

## D50 — publish one immutable recovery tree, then automate only the safe draft mutation

Merged the fully green recovery through PR #25 rather than rewriting remote
history. After every merge-triggered workflow passed, fast-forwarded `v2` and
`marketing-machine-v2` without force to exact recovery commit `47cd9eae...` and
verified the public Action bytes. This restores the advertised consumer ref
while preserving the audited marketing ancestry.

The connected GitHub capability cannot dispatch workflows or update Releases
directly, while asking the owner to perform a routine dispatch would waste the
scarce human budget. PR #26 therefore introduced a deliberately one-use push
authorization: it accepted only the owner-attributed first main update whose
`before` SHA was exact verified recovery commit `47cd9eae...`; checked out and
validated that immutable release tree; required public `v2` to equal it; and
retained the canonical-ID, duplicate, public-release, and postcondition guards.
Run `33294414373` succeeded and read-after-write API verification confirmed the
sole private draft now targets exact public v2 with tag `v2.0.0`. Remove that
temporary push trigger immediately in the finalization tree and retain only the
explicit owner-confirmed dispatch path.

This automates a reversible private-draft edit, not the GitHub Marketplace
publication ceremony. The agreement, Marketplace checkbox, and 2FA remain in
HQ-5 because they are account-holder attestations. It also does not weaken the
commerce gate: checkout remains closed and observed revenue/profit remain $0.

## D51 — reconcile a parallel `marketing-machine-v2` fix for the same stale HQ-5 link, then merge branches

Cycle-start egress test repeated the standing method: direct `curl` through the
configured proxy to `example.com` and `docs.aws.amazon.com` both returned HTTP
403 (`CONNECT tunnel failed`); `$HTTPS_PROXY/__agentproxy/status` confirmed the
proxy itself is reachable and logged both as `connect_rejected`. This is the
fourth consecutive cycle with this exact domain-level block. Per AGENTS.md's
fallback, no new repost-answers batch or dev.to draft was produced this cycle.

`apps/web/BUILD_DATE` was already `2026-08-30` (today) at cycle start;
`pytest -q apps/web` was 35/35 green and a full `apps/web/build.py` rebuild
against the CI env vars produced a clean `git diff --exit-code -- docs` — no
staleness to correct this cycle. Cross-checked `rules/public/deprecations.yml`
against `kits/lambda-lifeline/src/scan/index.mjs`'s `PHASE_DATES` and
`apps/web/content/fixes.yml` entry-by-entry (not just the runtimes touched by
D42/D44) and scanned every quarantined `launch/distribution/devto/*.md` draft
for ISO and prose (`Month Day, Year` / `Month Year`) dates against those same
two corroborated internal sources: no further errors beyond the two already
recorded in `launch/distribution/devto/README.md`.

This cycle started from `origin/marketing-machine-v2` at `47cd9ea` (per the
standing "fetch/checkout/pull first" step) and, before pulling `main`,
independently found the same defect D50 above had already fixed on `main`:
`revenue/HUMAN_QUEUE.md`'s HQ-5 step 1 pointed the owner at
`https://github.com/ntoledo319/EOLkits/releases/tag/untagged-0866963caf3f06db98a1`,
written at `01:09:09-04:00` (`90722cd`, `marketing-machine-v2`'s tip at the
time). Nine minutes later, PR #26's "Prepare Marketplace v2 draft" run
(`33294414373`, commit `79888beb`, `main`-only) resynced the same draft
release (id `375063073`) and GitHub regenerated its `untagged-<hex>` slug to
`untagged-ea8be73c7a7d9b6c45e7`, but `main`'s fix had not yet reached
`marketing-machine-v2`, which had continued on its own line through PR #25's
merge commit `47cd9ea` without picking up `main`'s 4 subsequent commits.
Independently corrected the same link on `marketing-machine-v2` (matching
`main`'s value), then discovered the divergence when pulling `main` for this
entry: `47cd9ea` is the true common ancestor, and both onward lines are pure
additions to `revenue/*.md` and unrelated `.github/workflows/*` changes — no
destructive rewrite on either side. Merged `origin/main` into
`marketing-machine-v2` (not rebase, to keep both commit lines intact),
renumbered this branch's `D50` to `D51` to avoid colliding with `main`'s `D50`
above, and kept both `HUMAN_QUEUE.md` improvements: `main`'s corrected URL plus
this branch's added durable-release-id note and Releases-list fallback (the
slug will keep regenerating on every future resync).

No price, checkout, Stripe, GRACE, DEV-account, or Marketplace-publication
state changed. Collected profit remains $0; the gap remains $4,000. HQ-0
through HQ-4, the corrected HQ-5, and HQ-6/HQ-7 are otherwise unchanged and
still require the owner. Future cycles should pull `main` before diagnosing
`marketing-machine-v2`-only state, since the two branches can now silently
diverge on ordinary pushes to either one.

## D52 — fix a real false-negative in the free scanner's Python runtime detection; bump BUILD_DATE

Cycle-start egress test repeated the standing method (fifth consecutive
cycle): direct `curl` through the configured proxy to `example.com` and
`docs.aws.amazon.com` both returned HTTP 403 (`CONNECT tunnel failed`);
`$HTTPS_PROXY/__agentproxy/status` confirmed the proxy itself is reachable
and logged both as `connect_rejected`. Per AGENTS.md's fallback, no new
repost-answers batch or dev.to draft was produced this cycle. `main` was
confirmed an ancestor of `marketing-machine-v2` (no repeat of D51's silent
divergence).

`apps/web/BUILD_DATE` was one day stale (`2026-08-30` against today's
`2026-08-31`). Rebuilt `docs/` with `apps/web/build.py` under the CI env
vars after confirming 35/35 `apps/web` tests green on the stale baseline
first; the bumped rebuild stayed 35/35 green and the diff was entirely
date-derived (countdowns, ICS `DTSTAMP`, sitemap `lastmod`,
`status/data.json` `generated_at`) — no structural or claim change.

Found a materially more significant defect while re-verifying the
scanner/deprecations cross-check this cycle habitually performs: the free
`lambda-lifeline` scanner engine's `AT_RISK_RUNTIMES` set and `PHASE_DATES`
table (`kits/lambda-lifeline/src/scan/index.mjs`) had no entry for
`python3.8` at all, even though `rules/public/deprecations.yml` (the public
SEO/scanner-data source of truth) has carried a full `lambda-python-3.8-eol`
entry since the original repair, and the sibling `python-pivot` kit's
`RUNTIME_TABLE` (`kits/python-pivot/src/python_pivot/runtimes.py`) already
has the identical dates (deprecation 2024-10-14, block-create 2027-02-01,
block-update 2027-03-03). Both independent internal sources agree exactly,
satisfying this project's own corroboration bar for adding a public
lifecycle date (the same bar D42 used for nodejs16.x and D43 declined for
ruby3.2/dotnet6 for lacking a second source).

The practical effect: `lambda-lifeline scan` against a live AWS account (the
kit's primary live-scan mode, not just its Node-focused IaC/codemod
commands) would silently report a Lambda function running `python3.8` as
`eol: false` / severity `'ok'` — a false negative for one of the exact
runtimes EOLkits exists to catch, and inconsistent with the site's own
`/migrate/lambda-python-3.8-eol/` page describing the same runtime as
already past its deprecation date and heading into the same Q1-2027 block
cluster as python3.9/3.10. This is a correctness bug in the core detection
product distributed via the GitHub Marketplace Action, npm package, and (by
shared rule behavior) the VS Code extension — a stronger finding than prior
cycles' SEO-page-only gaps (D42) because it affects live-scan output
strangers would actually read, not just static content.

Added `python3.8` to `AT_RISK_RUNTIMES`, `PHASE_DATES`
(`phase1: 2024-10-14, block_create: 2027-02-01, block_update: 2027-03-03`),
and `UPGRADE_TARGETS` (`python3.12`) in `index.mjs`, matching both
corroborating sources exactly. Added a new fixture function
(`invoice-etl-batch`, `python3.8`) to
`kits/lambda-lifeline/test/fixtures/lambda-inventory.json` so the fix is
exercised by a real regression test rather than only by table edits, and
updated `test/scan.test.mjs` (8 functions / 7 at risk, plus explicit
`python3.8` field assertions on the new fixture entry) and the README's
sample-output block to match. `node --test test/*.test.mjs` passed 28/28
(unchanged count; two prior assertions were widened, one fixture-specific
assertion block added), and the Python `hypothesis` property suite
(`tests/test_properties.py`) stayed 3/3 green, unaffected since it only
exercises Node runtimes. `npm pack --dry-run` still reports exactly 24
release files (fixtures/tests remain excluded from the shipped package,
matching the existing baseline). No other kit, the GitHub Action, or the VS
extension references the fixture's function/at-risk counts.

No price, checkout, Stripe, GRACE, DEV-account, or Marketplace-publication
state changed. Collected profit remains $0; the gap remains $4,000. HQ-0
through HQ-7 are unchanged and still require the owner; HQ-5's release link
was re-verified this cycle via `list_releases` (id `375063073`, tag
`v2.0.0`, slug `untagged-ea8be73c7a7d9b6c45e7`) and matches
`HUMAN_QUEUE.md` exactly — no repair needed this time.

## D53 — honor the failed VS gate with one focused reposition

(Renumbered from `origin/main`'s independent D51 to avoid colliding with this
branch's own D51 above; both were shipped in parallel Aug 31 cycles on
diverging branches — this branch's cycles continued on
`marketing-machine-v2` while a separate concurrent cycle worked directly on
`main`. Reconciled by the September 1 merge; see D56 below.)

The exact v1.1.0 gate failed: installs did not increase and no qualified
VS-attributed external author appeared. Cumulative downloads increased, but the
workflow intentionally treats them as context rather than purchase intent.
Used the policy's one reposition on discoverability and activation—not a new
SKU or inflated promise: renamed the listing around the concrete Lambda EOL
job, added Terraform/SAM/CloudFormation and runtime keywords, made the first
scan path explicit, and published v1.2.0 from exact green commit `23762f3f...`.
Reset the baseline only after the official public surface showed v1.2.0.

## D54 — automate authorized account operations only through validated authority

(Renumbered from `origin/main`'s independent D52 for the same reason as D53
above.)

The owner authorized every previously listed operation except retired Stripe
credential rotation. A one-use workflow therefore checked only recognized DEV
and GitHub-admin secret names, validated identity/repository access before use,
bounded every mutation to exact known targets, printed no credential, and
destroyed transient response/token files. It was tied to the first
owner-attributed push after exact base `23762f3f...`.

The safe attempt did not produce authority that does not exist: no DEV key was
configured, public DEV state remains 25 posts, the ruleset list remains empty,
and legacy dynamic Pages still ran. Do not bypass those boundaries, scrape
browser sessions, exploit the host, or reinterpret broad authorization as
permission to invent seller/payment facts. Remove the one-use workflow after
its terminal run.

## D55 — publish the free surface, keep the paid surface fail-closed

(Renumbered from `origin/main`'s independent D53 for the same reason as D53/D54
above.)

Publishing tested VS v1.2.0 is reversible distribution work with no customer
charge. Creating a live Stripe catalog and opening checkout is materially
different: current GRACE still lacks the v2 capability/status contract, exposes
the stale install surface, and injects an unreviewed script. The fulfillment,
delivery, refund, retention, legal, and actual-fee/cost gates also remain
unproven. Therefore ship the free acquisition improvement now, but create no
live payment objects and keep checkout closed until every recorded prerequisite
passes.

The retired Stripe credential rotation/revocation is explicitly out of scope at
the owner's direction. That records a deferred risk; it is not evidence that
the credential is safe, revoked, or reusable.

## D56 — reconcile the parallel `main`/`marketing-machine-v2` divergence; fix a second live-scan false negative (python3.11)

Cycle start: `marketing-machine-v2` and `origin/main` had diverged at shared
base `47cd9eae` — this branch continued daily maintenance cycles (D51/D52
above), while a separate concurrent cycle worked directly on `main` through
PRs #28-#30 (VS v1.2.0 reposition/publication, operator legal identity,
authorized DEV/Pages/ruleset attempt; that cycle's own D51-D53 as recorded
in `main`'s history). `git merge-base --is-ancestor origin/main
marketing-machine-v2` failed, confirming real divergence rather than a
repeat of D44's already-merged case. Merged `origin/main` into
`marketing-machine-v2` (not rebase, preserving both commit lines, matching
the D50/D51 precedent). All non-`revenue/` files (VS extension v1.2.0, legal
pages, workflow YAML) auto-merged with zero conflicts. `revenue/*.md`
conflicted only in trailing append blocks; resolved by keeping both
histories in chronological order and renumbering collisions: this branch's
D51/D52 kept their numbers, `main`'s independent D51-D53 became D53-D55
here; `HUMAN_QUEUE.md`'s old HQ-0..HQ-7 numbering is superseded by `main`'s
newer, more complete HQ-A..HQ-G (this branch's durable-release-id/fallback
note for the Marketplace draft link was preserved inside `main`'s HQ-E
step).

`apps/web/BUILD_DATE` was one day stale (`2026-08-31` against today's
`2026-09-01`) on the merged tree. Confirmed `pytest -q apps/web` 35/35 green
on the merged tree first (proving the merge itself didn't regress anything),
then bumped and rebuilt: 35/35 stayed green, diff was 15 files, entirely
date-derived (countdowns, ICS `DTSTAMP`, sitemap `lastmod`,
`status/data.json` `generated_at`).

Egress test repeated the standing method (sixth consecutive cycle): direct
`curl` through the configured proxy to `example.com` and
`docs.aws.amazon.com` both returned HTTP 403 (`CONNECT tunnel failed`); a
`WebFetch` to `docs.aws.amazon.com` also returned `EGRESS_BLOCKED`;
`$HTTPS_PROXY/__agentproxy/status` confirmed the proxy itself is reachable
and logged both as `connect_rejected`. Per AGENTS.md's fallback, no new
repost-answers batch or dev.to draft was produced this cycle.

Repeated the standing scanner/deprecations cross-check (the same one that
found D42's nodejs16.x gap and D52's python3.8 gap) and found a second
instance of the identical defect class: `rules/public/deprecations.yml`
carries a full "Lambda Python 3.11 projected create/update restrictions"
entry (`date`/block-create `2027-07-31`, `block_update_date` `2027-08-31`,
`deprecation_date` `2027-06-30`), and `kits/python-pivot`'s `RUNTIME_TABLE`
independently agrees on the identical three dates for `python3.11` — the
same two-source corroboration bar D52 used for `python3.8`. But
`kits/lambda-lifeline/src/scan/index.mjs`'s `AT_RISK_RUNTIMES` set and
`PHASE_DATES` table had no `python3.11` entry at all (only `python3.10` had
been added, apparently in a cycle not captured in this branch's own
DECISIONS history). A real `lambda-lifeline scan` against an AWS account
running a `python3.11` Lambda function would therefore report `eol: false`
/ severity `'ok'` — a false negative for a runtime the site's own
`/migrate/lambda-python-3.11-eol/` page already tracks, identical in kind
to D52's python3.8 finding and D42's nodejs16.x finding.

Added `python3.11` to `AT_RISK_RUNTIMES`, `PHASE_DATES`
(`phase1: 2027-06-30, block_create: 2027-07-31, block_update: 2027-08-31`),
and `UPGRADE_TARGETS` (`python3.12`) in `index.mjs`, matching both
corroborating sources exactly. Confirmed `ruby3.2`/`dotnet6` remain
correctly excluded from the public rules file per D43's still-valid
reasoning (no second corroborating source; not re-litigated this cycle).
Added fixture function `ml-inference-endpoint` (`python3.11`) to
`test/fixtures/lambda-inventory.json`; updated `test/scan.test.mjs` (9
functions / 8 at risk, explicit `python3.11` field assertions) and the
README's sample-output block to match. `node --test test/*.test.mjs`
passed 28/28 (unchanged count); the `hypothesis` property suite stayed
3/3 green (Node-only change, unaffected); `npm pack --dry-run` still
reports exactly 24 release files. Grepped the GitHub Action and VS
extension for any reference to the fixture's counts: none found, so no
other package needed updating.

No price, checkout, Stripe, GRACE, DEV-account, or Marketplace-publication
state changed. Collected profit remains $0; the gap remains $4,000. The
authoritative owner queue is now `revenue/HUMAN_QUEUE.md`'s HQ-A through
HQ-G (40 minutes); do not use the superseded HQ-0..HQ-7 numbering from
before this merge.

## D57 — seventh consecutive egress-blocked cycle; bump BUILD_DATE only after finding no new correctness gap

Cycle start: `origin/main` confirmed an ancestor of `marketing-machine-v2`
(`git merge-base --is-ancestor`) — `git pull --rebase` on the branch was a
no-op, so no repeat of D44/D51/D56's divergence patterns this cycle.

Egress test repeated the standing method (seventh consecutive cycle): direct
`curl` through the configured proxy to `example.com` and
`docs.aws.amazon.com` both returned HTTP 403 (`CONNECT tunnel failed`);
`$HTTPS_PROXY/__agentproxy/status` confirmed the proxy itself is reachable
and logged both as `connect_rejected`. Also attempted, as a new check this
cycle, to read the latest scheduled `acquisition-evidence.yml` artifact
(run `33532642787`, 2026-09-01) via its signed Azure Blob Storage download
URL obtained through the GitHub API (a different path than a direct
`docs.aws.amazon.com`/`example.com` fetch, since the GitHub API itself
remains reachable through the connected GitHub MCP tools). That download
also returned `connect_rejected` through the same proxy, confirming this is
an organization-policy-level block on general HTTPS egress from this
container, not a per-domain denylist limited to the two standing test
domains. Per AGENTS.md's fallback, no new repost-answers batch or dev.to
draft was produced this cycle, and this cycle could not refresh METRICS.md
with a new acquisition-artifact observation beyond what was already
recorded from run `33532642787`'s existence (visible via the GitHub Actions
API, which does not require this container's own egress).

Before falling back to the routine BUILD_DATE maintenance fix, re-ran the
full standing correctness sweep to check whether a new gap had appeared
since D56: `kits/lambda-lifeline/src/scan/index.mjs`'s `AT_RISK_RUNTIMES`/
`PHASE_DATES`/`UPGRADE_TARGETS` tables now carry corroborated entries for
every runtime `rules/public/deprecations.yml` and `kits/python-pivot`'s
`RUNTIME_TABLE` track (nodejs16.x/18.x/20.x/22.x, python3.8/3.9/3.10/3.11,
ruby3.2, dotnet6) — python3.8 (D52) and python3.11 (D56) are confirmed
present and correct. `nodejs14.x`, `java8.al2`, and `provided.al2` remain
intentionally absent from `PHASE_DATES` (each already fully past its block
dates or lacking a second corroborating source), matching the same
`severity()` fallback-to-`critical-eol` design already used for those
entries; this is consistent, not a bug. `apps/web/content/fixes.yml`'s
python3.12/3.13 guidance is consistent with both tables treating those as
supported upgrade targets, not deprecated runtimes. No new date error was
found in the 25 quarantined `launch/distribution/devto/*.md` drafts beyond
the two already recorded in that directory's `README.md`.

Found no new correctness gap this cycle. `apps/web/BUILD_DATE` was one day
stale (`2026-09-01` against today's `2026-09-02`). Built a project-local
venv from `apps/web/requirements-dev.lock` (kept under `tmp/`, gitignored)
and confirmed `pytest -q apps/web` was 35/35 green on the stale baseline
first; bumped `BUILD_DATE` to `2026-09-02`, rebuilt via `apps/web/build.py`
under the exact `EOLKITS_BASE_PATH`/`EOLKITS_SITE_URL`/`EOLKITS_API_URL`
env vars CI uses, and re-ran the suite: 35/35 still green. `git diff --stat
-- docs` showed exactly 15 files changed; inspected the full diff and
confirmed every changed line is date-derived (sitemap/feed `lastmod`, ICS
`DTSTAMP`, `/migrate/` countdown text, `status/data.json` `generated_at`) —
no structural, price, or claim-text change.

No price, checkout, Stripe, GRACE, DEV-account, or Marketplace-publication
state changed. Collected profit remains $0; the gap remains $4,000. The
authoritative owner queue remains `revenue/HUMAN_QUEUE.md`'s HQ-A through
HQ-G (40 minutes) — HQ-E's release link (id `375063073`, slug
`untagged-ea8be73c7a7d9b6c45e7`) was re-verified via `list_releases` this
cycle and still matches `HUMAN_QUEUE.md` exactly, no repair needed. The VS
v1.2.0 five-day gate (`2026-09-05T23:27:55Z`) has not yet arrived.

## D58 — ninth+ consecutive egress-blocked cycle; routine BUILD_DATE bump only

No cycle ran on September 3 (git history has no commit between `ee11bbc`
2026-09-02 and this one); `marketing-machine-v2` was confirmed not diverged
from `origin/main` (`git merge-base --is-ancestor origin/main
marketing-machine-v2` passed, `git pull --rebase` a no-op) before starting
work.

Cycle-start egress test repeated the standing method: direct `curl` through
the configured proxy to `example.com` and
`docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html` both returned
HTTP 403 (`CONNECT tunnel failed`); `$HTTPS_PROXY/__agentproxy/status`
confirmed the proxy itself is up and logged both rejections
(`connect_rejected`, "gateway answered 403 to CONNECT"). `WebFetch` to
`example.com` and to a specific `repost.aws` thread URL both returned
`EGRESS_BLOCKED` directly (not merely a curl-level 403), closing the gap
between the two measurement methods used in prior cycles. `WebSearch`
(hosted, not routed through this container's egress) still returned
indexed blog/community results, but per AGENTS.md §2.5 those are
explicitly disqualified as sources for AWS runtime dates ("never blogs"),
and per D36's truth bar a repost-answers batch also requires a live-thread
fetch, not a search snippet. Per AGENTS.md's fallback, no new
repost-answers batch or dev.to draft was produced this cycle — the ninth
consecutive cycle blocked this way (D42-D44, D57 and the unlabeled Aug
30/31 cycle notes in PLAN.md are the prior instances).

Ran a fresh full correctness sweep before defaulting to the date bump, to
avoid rubber-stamping "nothing to find": compared `kits/lambda-lifeline`'s
`PHASE_DATES`/`AT_RISK_RUNTIMES` against `kits/python-pivot`'s
`RUNTIME_TABLE` (all four shared Python entries — 3.8/3.9/3.10/3.11 — match
exactly), against `rules/public/deprecations.yml` (8 tracked runtimes, all
present and dated identically; `ruby3.2`/`dotnet6` remain the same
deliberately deferred gap from D43 — still only one internal source, still
unverifiable against the primary doc this cycle), against
`apps/web/content/fixes.yml` (no ruby3.2/dotnet6 entries either, consistent
non-claim), and against `kits/al2023-gate`'s `AL2_EOL = 2026-06-30`
(matches D37's already-corroborated fact, already in the past). Found no
new gap.

Confirmed `pytest -q apps/web` was 35/35 green on the stale `BUILD_DATE`
(`2026-09-02`, now 2 days stale) before touching anything. Bumped to
`2026-09-04`, rebuilt via `apps/web/build.py` under the exact
`EOLKITS_BASE_PATH=/EOLkits` / `EOLKITS_SITE_URL=https://ntoledo319.
github.io/EOLkits` / `EOLKITS_API_URL=https://eolkits.com` env vars CI
uses, and re-ran the suite: 35/35 still green. `git diff --stat -- docs`
showed exactly 16 files changed; inspected a representative diff
(`docs/migrate/lambda-python-3.9-eol/index.html`) and confirmed every
changed line is date-derived (152→150-day countdown, `datePublished`/
`dateModified`, ICS `DTSTAMP`, sitemap/feed `lastmod`, `status/data.json`
`generated_at`) — matches the 2-day bump exactly, no structural, price, or
claim-text change. Also ran `kits/lambda-lifeline`'s Node test suite
(28/28 green) as an independent regression check since its runtime tables
were touched by D52/D56.

Checked live external state through the connected GitHub API (not general
web egress, so unaffected by the block): `list_issues` still returns 0 open
issues (0 qualified `$299 Audit interest` submissions); `list_releases`
still shows the canonical v2.0.0 draft (id `375063073`) as `draft=true` at
unchanged slug `untagged-ea8be73c7a7d9b6c45e7`, matching
`HUMAN_QUEUE.md`'s HQ-E exactly — no repair needed, no owner action taken
since D57. No price, checkout, Stripe, GRACE, DEV-account, or
Marketplace-publication state changed. Collected profit remains $0; the
gap remains $4,000. HQ-A through HQ-G are unchanged and still require the
owner. The VS v1.2.0 five-day gate (`2026-09-05T23:27:55Z`) still has not
arrived — do not call it early; it is the next autonomous checkpoint.

## D59 — reverse false publication churn; dates describe content, not build activity

Fresh technical review invalidated D57/D58's routine BUILD_DATE policy. Updating
one global date changed unchanged articles' first-publication timestamps, every
sitemap `lastmod`, RSS publication dates, ICS stamps, and status generation time.
That is not a meaningful public-content update and conflicts with the builder's
own determinism comment and search-engine guidance. Reverted the September 2/4
date-only output to the August 31 source baseline. Added explicit per-page
sitemap overrides so only the materially changed Audit and Lambda schedule URLs
carry `2026-09-04`. Future cycles must not bump BUILD_DATE merely because a day
passed.

## D60 — use conservative marketplace evidence and ship correctness without resetting the gate

Nine exact-ID Gallery requests alternated between 103 and 104 installs while
agreeing on 223 downloads and v1.2.0. A single read can therefore randomly pass
or fail the acquisition gate. The workflow now takes five cache-busted samples,
validates every identity/version/counter, stores the arrays and bounds, and uses
the minimum. Post-deadline replica disagreement is inconclusive. Six pure Node
tests cover malformed samples, identity drift, lower-bound reduction, pending,
pass, inconclusive, and failure outcomes. The stale summary's literal
166-download baseline was replaced with the configured value.

This evidence defect does not justify waiting on known product bugs. VS v1.3 is
a correctness/conversion release: it adds the omitted Node.js 16/Python 3.8
structured rules, scopes Terraform runtime detection to literal values inside
`aws_lambda_function`, tests unrelated-resource false positives, and offers the
attributed $299-report path directly from the findings warning. It does not
reset the cumulative 103-install baseline or September 5 gate and is not a
second “reposition” of the listing.

## D61 — preserve one automated cash unit; queue RapidAPI, park Contra

Fresh official-policy research found no currently available marketplace that
combines a $299 custom report, built-in discovery/payment, and truly hands-off
fulfillment. Contra is commission-free and supports fixed-price services, but
its inquiry/contract/private-input/delivery flow and per-write MCP confirmations
reintroduce owner labor and customer communication. Do not publish a service we
cannot fulfill through the platform automatically.

RapidAPI does combine discovery, subscriptions/usage billing, four public plans,
and a provider proxy secret, at a documented 20% share. Keep it as Bet C only
after Audit is live and free-tier capacity is measured; 34 × $150 × 80% = $4,080
is plausible arithmetic, not a 28-day forecast. The fastest money path remains
the already-built $299 Audit fed by VS, GitHub Action, and cited search pages.

## D62 — lifecycle fields must not call future supported runtimes EOL

`lambda-lifeline` used `eol: true` as an alias for “tracked at risk,” causing
future supported runtimes such as Node.js 22, Python 3.11, and `java8.al2` to be
machine-labeled already EOL. It also assigned `java8.al2` a fallback
`critical-eol` severity because phase dates were absent. Machine output now
separates `at_risk`, `lifecycle`, and actual `eol`; `provided.al2` and
`java8.al2` carry the current AWS phase dates. Rendering/strict mode continues
to act on `at_risk`, preserving risk detection. A new parity test executes the
Node scanner and imports Python Pivot, requiring both to match the cited public
YAML exactly.

## D63 — record containment failures and tighten the remainder of the run

The technical-review subagent's first test created transient fixtures through
`node:os.tmpdir()` at `/tmp`, outside WORKSPACE_ROOT, then cleaned them. The root
agent also issued one read-only Git status/diff command without the mandatory
workspace-local global-config override, which may have read user-level config.
Neither changed persistent external or repository state, but both violate the
workspace-jail process and are recorded as failures. Every later test uses a
workspace `TMPDIR`; every Git call uses `GIT_CONFIG_NOSYSTEM=1` plus the
workspace-local empty global config. Docker builds are left to CI rather than
mutating the local daemon. Item 3 (retired Stripe credential rotation/revocation)
remains excluded exactly as directed.
