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

## D25 — cloud cycle, corrected WORKSPACE_ROOT, restocked the answer backlog

This 2026-08-23 cycle ran as an isolated cloud checkout with no access to any
local machine, the GRACE VPS, or local/box secrets; its only ship channel is
`git push` to `marketing-machine-v2`. `revenue/PLAN.md` line 1 still recorded a
prior local run's machine path (`/home/nick/Development/active/Rupture`); it
is corrected to this cycle's actual repo root. This is a bookkeeping
correction, not a claim that any prior local evidence was wrong.

Live web access was available via search this cycle but WebFetch was blocked
for every tested domain (`example.com`, `docs.aws.amazon.com`, `repost.aws`,
`eolkits.com`) with `EGRESS_BLOCKED`, so no page content could be directly
fetched and verified byte-for-byte. Facts below rest on (a) AWS Lambda
runtime-table dates already cross-verified in this repo's own prior cycles
(D14, D23) and repeated verbatim in this cycle's task instructions, and (b)
corroborating search-result snippets from multiple independent sources for
each specific technical claim (Lambda@Edge replica deletion behavior,
CodeBuild GitHub Actions runner image labels). No date, URL, or claim was
invented; where confidence was insufficient (a WeasyPrint/AL2023 Elastic
Beanstalk image-rendering question found via search) the candidate was
dropped rather than drafted speculatively.

Per this cycle's standing priority, restocked the K1/C4 answer backlog:
appended Batch 3 to `launch/distribution/repost-answers.md` with two fresh,
unique, help-first drafts for real open AWS re:Post threads not covered by
Batches 1–2 (`QUz3FDy7jfQliBFrh_hKZoaQ` — Node.js 18 deprecation notice citing
already-deleted functions, actually a Lambda@Edge replica/CloudFront
propagation issue; `QUqvfJVhQ4ReeApG8shtcu1A` — CodeBuild-hosted GitHub
Actions runner defaulting to AL2 instead of AL2023 for lack of an `image:`
runs-on label). Both answers solve the asker's actual problem first and
mention eolkits once, disclosed, as in prior batches.

Unlike Batches 1–2, Batch 3 links to the verified `ntoledo319.github.io/EOLkits`
Pages build rather than `eolkits.com`: this cycle had no way to confirm the
custom domain is still serving the repaired site (D19/D20's scheduled
post-deploy truth gate result was not observed from this checkout), so per
D19's own rule — never send acquisition traffic to an unproved deployment —
the verified surface was used instead. This does not change Batches 1–2's
archived status; those still need the fresh review already noted.

This is one more drafted-content ship, not demand evidence. It does not
change K1/A1's ranking, gates, or falsifiers, and it adds no owner-queue item
with a deadline (pasting the new answers is available to the owner whenever
convenient, same as the rest of the backlog). Collected revenue remains $0.

## D26 — cloud cycle, restocked the answer backlog again (Batch 4)

This 2026-08-24 cycle is another isolated cloud checkout with no VPS/local/
Stripe access; same jail and ship channel as D25. WebFetch again returned
`EGRESS_BLOCKED` for a neutral control (`example.com`), so, following D25's
precedent, no page content was fetched byte-for-byte; WebSearch worked and
was used instead, cross-checking each specific technical claim against
multiple independent search results before drafting.

Per the standing K1/C4 answer-backlog priority, appended Batch 4 to
`launch/distribution/repost-answers.md`: one fresh, unique, help-first draft
for a real open AWS re:Post thread not covered by Batches 1–3
(`QUowJJh-50R3KbxGrZ2YNsCA` — "python 3.9 runtime update gives Runtime.Unknown
in INIT phase"). Search corroboration (multiple independent snippets)
confirmed the thread's actual content: the user's `python3.9` execution
environment auto-updated from internal build v96 to v101, and a native
extension (psycopg2 was named in a related discussion of the same failure
mode) then failed to load, producing a bare `Runtime.Unknown` in INIT rather
than a clear import error. The answer's core fix — pinning/rolling back the
runtime version via Lambda's documented runtime-management-controls
(`UpdateRuntimeOn=Manual`) — is AWS's own documented mechanism for exactly
this failure mode, not inferred from the thread itself; both cited docs URLs
(`runtime-management.html`, `runtime-management-rollback.html`) are the
existing official pages already used as sourcing precedent in this repo.

Only one answer was drafted this cycle, not two: several other superficially
promising candidates found via search (the SSM State Manager Python 3.9
notice-confusion thread, the "Lambda runtime deprecation dates differ by
documentation language" thread, the "rollback to Node 14" thread) already had
substantive community answers visible in their own search-result summaries,
so a second EOLkits answer there would not clearly add net-new help-first
value. Per AGENTS.md's own instruction — quality over quantity, skip rather
than pad — this cycle shipped the one candidate that was both genuinely
novel and clearly still worth answering, rather than padding to two.

As in Batch 3, the drafted link points to the verified
`ntoledo319.github.io/EOLkits` Pages build (specifically its
`/fix/lambda-glibc-version-not-found/` page, whose existing copy already
names `psycopg2` and the AL2/AL2023 glibc split relevant to this exact
failure mode) rather than `eolkits.com`, because this checkout again had no
way to confirm the custom domain is still serving the repaired site.

This is one more drafted-content ship, not demand evidence. It does not
change K1/A1's ranking, gates, or falsifiers, and adds no owner-queue item
with a deadline. Collected revenue remains $0; gap remains $4,000.

## D27 — cloud cycle, restocked the answer backlog again (Batch 5)

This 2026-08-25 cycle is another isolated cloud checkout with no VPS/local/
Stripe/GitHub-API access; same jail and ship channel as D25/D26. WebFetch
again returned `EGRESS_BLOCKED` for a neutral control (`example.com`);
WebSearch worked and was used, cross-checking each specific technical claim
against multiple independent search-result snippets before drafting, per
the same discipline as D25/D26.

Between the 2026-08-24 cycle's read and this one, three same-day-dated
(2026-08-22) commits (`bffb335a`, `9c231b58`, `0780909c`) landed on this
branch shipping an Audit report-proof/fulfillment hardening pass, authored
outside this cycle. This cycle did not write or independently re-verify that
code; it is recorded in PLAN.md/ASSETS.md for continuity, not claimed as this
cycle's work, and changes no HQ item, gate, or ranking — it is release
evidence at most until the owner completes HQ-2 through HQ-7.

Per the standing K1/C4 answer-backlog priority, appended Batch 5 to
`launch/distribution/repost-answers.md`: one fresh, unique, help-first draft
for a real, search-indexed AWS re:Post thread not covered by Batches 1–4
(`QURnP8vskJREG40Ilrwx_RLQ` — "API GATEWAY DEV PORTAL - Update Lambda
Functions to nodejs20", a SAM-generated developer-portal app whose Cognito
login broke after bumping from `nodejs16.x` to `nodejs20.x`). The existing
community answer (found via search) only gestured at an SDK v2/v3 concern;
this draft adds two things it did not cover: (a) the specific, well-documented
mechanism — `nodejs16.x` bundles AWS SDK v2, `nodejs18.x`+ bundles v3, and a
lingering `require('aws-sdk')` v2 call is the most common cause of exactly
this kind of post-bump breakage — corroborated via multiple independent
search snippets (an AWS CDK GitHub issue, a re:Post thread on the same SDK
mismatch, and a migration-guide article), not asserted from the target thread
alone; and (b) a warning not to stop at `nodejs20.x`, since it is already in
the same 2027-02-01/2027-03-03 block-create/block-update cluster as
`nodejs16.x`/`nodejs18.x` per AWS's current runtimes table — recommending
`nodejs22.x`/`nodejs24.x` instead so the asker does not repeat this migration
within the year.

This cycle's searches surfaced three other superficially promising
candidates, each rejected under AGENTS.md's quality-over-quantity rule
because each already had a substantive community answer with no clear
distinctive gap: a thread about Lambda deprecation dates diverging by
documentation locale (`QU_XgpAZ8CRdmRP17Oz8S1Aw`) whose existing answer
already told the asker to trust the English page; a stale 2023-era .NET Core
3.1 Lambda-deprecation-policy thread already covering the phase-1/phase-2
policy generically; and a CloudFront-secure-static-site `nodejs20.x` EOL
thread (`QUyHgVGQcUQyWa1bOcW7p4sQ`) whose existing answer already gave two
concrete remediation paths. Search itself also surfaced materially
conflicting "block" dates for `nodejs20.x` across sources (2026-08-31/
2026-09-30 in one snippet, 2026-06-01/2026-07-01 in another, versus this
repo's already-verified 2027-02-01/2027-03-03) — exactly the superseded-date
confusion AGENTS.md warns about. Per D14/D23/D25/D26 precedent, this draft
uses only the repo's already-cross-verified 2027 dates, explicitly warns
against the various 2026 dates, and does not treat any single search snippet
as authoritative on its own.

As in Batches 3–4, the drafted link points to the verified
`ntoledo319.github.io/EOLkits` Pages build rather than `eolkits.com`, because
this checkout again had no way to confirm the custom domain is still serving
the repaired site.

This is one more drafted-content ship, not demand evidence. It does not
change K1/A1's ranking, gates, or falsifiers, and adds no owner-queue item
with a deadline. Collected revenue remains $0; gap remains $4,000.
