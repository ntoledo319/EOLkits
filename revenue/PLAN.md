WORKSPACE_ROOT: /Users/nicholastoledo/Development/active/Rupture

**▶ RESUME: read `HANDOFF-2026-07-15.md` at the repo root FIRST** (then `AGENTS.md`, then all six `revenue/` files).

# PLAN — Revenue Loop v2 (EOLkits)

**Day 0 = 2026-07-13 · Day 28 = 2026-08-10 · Target = $4,000 collected profit · Collected so far = $0 · GAP = $4,000**

Jail (§1) in effect: all writes inside WORKSPACE_ROOT. The agent **cannot** SSH to the GRACE VPS (key is in
`$HOME/.grace-keys/`, outside the jail) or create KYC accounts. Ship channel = `git push` to
`marketing-machine-v2` → box cron auto-deploys eolkits.com daily + auto-publishes dev.to.

---

## The situation in one paragraph
EOLkits is real, live, tested, and delivering (email fixed in prior work; Stripe links live). It has earned **$0**
because it has **~0 qualified traffic and 0 buyers** — the bottleneck is 100% distribution + demand, not product.
Cycle-0 audit + verified platform research + 40+ scored frames confirm: **no autonomous $0 action reaches a ready
buyer in 28 days** — every payment channel is first-publish KYC-gated. **UPDATE 2026-07-14:** the owner ruled out
Upwork (ongoing personal time) and Fiverr (KYC won't clear), so the fast-outreach path is gone (DECISIONS D7). The
**compounding flywheel is now the primary engine** — one-time marketplace publishes + autonomous content — feeding
the $299 audit and $1,499 Pack by *discovery*, not outreach. Realistic honest outcomes: **$4,000 by Day 28 is now
very unlikely** (flywheel compounds over months); collected-by-Day-28 ≈ **$0–600**; the real inflection is the
**Q1-2027 Lambda block wave (Feb 1 / Mar 3 2027)**.

---

## The 2–3 concurrent bets (§6)

### ~~Bet A — Upwork/Fiverr gig~~ · **KILLED 2026-07-14 (owner constraint — see DECISIONS D7)**
Owner: no Upwork ("won't spend my own time on platforms"), no Fiverr ("they won't verify me"). No owner outreach and
no fast-gig shortcut exists. Replaced by:

### Bet A′ — FAST(er) · Gumroad "AWS Runtime EOL Migration Toolkit" digital bundle
- **Frame:** sell a bundle/service-artifact via a Merchant-of-Record with built-in payments and **one-time setup, no
  per-job owner time** (fits the owner constraint).
- **Arithmetic to $4k:** bundle at **$79** (packaging + migration playbook PDF + IaC templates + the 3 free CLIs),
  Gumroad 10%+$0.50 → **~$70 net/sale**. This is a *first-dollar / volume* play, not a $4k driver on its own
  (~57 sales for $4k); its job is a cheap early conversion + a lead into the $299 audit.
- **Funnel:** the same discovery flywheel (Bet C) → a low-friction $79 buy for teams not ready for a $299 audit.
- **Falsifier:** Gumroad rejects the owner's KYC (as Fiverr did) ⇒ bundle sold via the existing Stripe rail on
  eolkits.com instead; or 3 weeks live with traffic and 0 sales ⇒ the code is too "free-on-GitHub" to sell — drop it.
- **Human unlocks:** HQ-1′ (Gumroad account — one-time; verify KYC clears), HQ-2′ (owner runs the build script,
  uploads the zip, pastes the listing copy, clicks publish). **Built 2026-07-18 — see `launch/gumroad/`, HQ-2′ is
  now a ~10-minute click-through, not agent work.**

### Bet B — HEAVY · $1,499 Migration Pack (real PR, CI-fail auto-refund)
- **Frame:** fixed-scope service artifact via the already-live Stripe link; highest revenue-per-unit.
- **Arithmetic to $4k:** $1,499 gross, Stripe 2.9%+$0.30 → **$1,455.23 net/sale**. **3 sales = $4,365.69 = clears the
  goal outright.** 2 = $2,910; 1 = $1,455 (36%).
- **Funnel:** the CI-failure moment — the GitHub Action PR comment + (once registered) the GitHub App surface
  "[Have it fixed: Migration Pack]" exactly when a deprecated runtime blocks a merge. Secondary: upsell a $299-audit
  buyer. The auto-refund-if-CI-fails guarantee makes a cold $1,499 ask viable.
- **Falsifier:** `sandbox_e2e.py` against a sandbox repo does **not** produce a clean, CI-passing PR end-to-end
  (grace-api + github-app path is UNVERIFIED today) ⇒ pull the Pack until proven; or no repo-access buyer in 28 days.
- **Money-path reviewed 2026-07-14 (DECISIONS D9):** one critical charge-with-no-delivery-no-refund bug FIXED (+test);
  refund-policy gaps + stubbed org_license/drift_watch flagged. **Pre-sale gates are in HQ-5 / HQ-5b — clear them first.**
- **Human unlocks:** HQ-4 (register GitHub App + creds to VPS `.env`, SSH owner-only), HQ-5 (run `sandbox_e2e.py`),
  HQ-6 (one real $1,499 Stripe charge+refund test).

### Bet C — COMPOUNDING · VS Code + Open VSX extension (+ PyPI/npm/GitHub Action/dev.to) → $299 audit
- **Frame:** sell placement — built-in marketplace distribution; payment stays on external Stripe.
- **Arithmetic:** direct 4-wk revenue is honestly **~$0–290** (maybe 1 cold-install audit). Real value is the
  **flywheel:** 30M+ VS Code users + 300M/mo Open VSX (Cursor/VSCodium) + PyPI/npm + dev.to authority accrue
  install/review/backlink volume that lowers CAC for every audit/pack sale **after** day 28. Not an in-window $4k driver.
- **Funnel:** marketplace + registry + GitHub-Marketplace search → in-tool CTA → eolkits.com/audit (utm-tagged).
- **Falsifier:** 3 weeks post-publish, installs <25 **and** 0 `utm_source=vscode` audit sessions in `track.js`
  ⇒ demote to background SEO.
- **Human unlocks:** HQ-7 (VS Code publisher + `vsce publish`), HQ-8 (Open VSX publisher + `ovsx publish`),
  HQ-9 (PyPI/npm publish), HQ-10 (list GitHub Action), HQ-11 (DEVTO_API_KEY on box). **Packages are prepared →
  each unlock is minutes of owner work.**

---

## What shipped this cycle (externally visible, in-jail, $0, no human contact)
1. **VS Code extension made marketplace-ready** — added icon, marketplace-grade README, storefront metadata; packages
   to a valid `.vsix`. (Bet C, submission-ready.)
2. **Three §2.5 truth/credibility fixes** de-risking the bet assets (see DECISIONS): corrected `lambda-lifeline`'s
   stale Node/Python block dates → AWS-authoritative Feb 1 / Mar 3 2027 (was Sep 30 2026), fixed its brittle test
   (24/24 green), and corrected the VS Code scanner's wrong Python EOL dates + Node20 message.
3. **Verified the live commerce data is correct** — `deprecations.yml` (Node/Python 2027 blocks) matches AWS; left
   unchanged. (Prevented a wrong-date edit the synthesis had suggested.)
4. **The six `revenue/` state files** (this brain).

## Cycle 2026-07-15 (cloud routine)
5. **Truth fix — removed fabricated pricing from all 3 kit READMEs** (`915ebb1`): `lambda-lifeline`, `al2023-gate`,
   `python-pivot` each advertised a "Solo $499 / Team $999 / Enterprise $2,499" tier ladder, a $999/$1,999/$4,997
   kit bundle, a Slack channel, live pairing sessions, on-call support, and `support@eolkits-kits.dev` — **none of
   which exist** in `pricing.yml`, `grace-api`, or Stripe; `eolkits-kits.com` is not a real domain. This is a live,
   public-repo §2.5 violation (undeliverable claims) and a conversion dead-end (a reader who clicks through finds
   nothing to buy). Replaced with the real, working ladder — Audit PDF $299 / Migration Pack $1,499 — linking to the
   live `eolkits.com/audit` and `/pack` Stripe checkouts. `lambda-lifeline` tests still 24/24 green. See DECISIONS D11.
   **Why this over a new dev.to article this cycle:** WebFetch (the tool this loop uses for primary-source lookups)
   returned HTTP 403 on every URL tested this cycle, including AWS docs and a control site (`example.com`) — a
   sandbox/proxy outage, not an AWS block. §2.5 requires verifying new AWS date claims against the authoritative
   runtimes table before shipping; with that tool down, the correct move was a fix that needed **no new external
   fact-checking** (reuses already-cross-checked SKUs/prices) rather than risk shipping an unverified date, which is
   exactly the mistake D3 caught last cycle. A new article is still queued — see Next actions.

## Cycle 2026-07-16 (cloud routine)
6. **WebFetch/direct fetch confirmed still down** — 3rd consecutive cycle (`example.com` control → HTTP 403; direct
   `curl` through the proxy also 403'd). `WebSearch` works but can't confirm a URL resolves, so per the outage rule,
   no new re:Post answers or dev.to article this cycle — see DECISIONS D14.
7. **Truth/do-no-harm fix — pulled Drift Watch's live self-serve checkout** (`2a843b9`): `drift_watch` ($19/mo) had
   a fully live, actively-upsold checkout (`/drift/` page, homepage "Start watching" CTA, and an upsell card on the
   audit success page shown to every $299 buyer) but its fulfillment is a complete no-op — a subscriber would be
   charged monthly, forever, for nothing. Replaced with an honest "coming soon / join the waitlist" page, removed the
   upsell, marked README "(coming soon)." `org_license` checked too and found lower-risk (inquiry form, not
   self-serve; the real key IS generated, just never emailed — deferred). Full reasoning + verification in DECISIONS
   D14. This closes an active live-harm exposure that opened up now that real distribution (the re:Post answers) has
   started sending traffic.

## Cycle 2026-07-18 (cloud routine)
8. **Built the Gumroad bundle end-to-end** (`launch/gumroad/`): a verified-working `build_bundle.sh` that assembles
   the 3 kit sources + an original `MIGRATION-PLAYBOOK.md` (consolidates the Q1-2027 block cluster + AL2 EOL +
   per-kit migration steps, sourced entirely from the repo's own already-verified `deprecations.yml` — no new
   external fetch needed) + `ATTRIBUTIONS.md` (§9 license-hygiene gate: MIT + Apache-2.0 deps, no copyleft, AI
   provenance disclosed) into a 164KB/137-file zip, tested locally. `LISTING-COPY.md` has the entire Gumroad listing
   (title/price $79/description/tags/refund policy) ready to paste plus exact publish steps. This closes out Bet A′
   — the owner's only remaining step is HQ-1′/HQ-2′ (~10 min). See DECISIONS D15.
9. **Confirmed the WebFetch/proxy outage is a persistent gateway policy denial, not transient** — checked
   `$HTTPS_PROXY/__agentproxy/status` this cycle (previous cycles only saw the symptom, not the cause): both
   `example.com` and the AWS docs URL show `connect_rejected` / "gateway answered 403 to CONNECT (policy denial or
   upstream failure)" in `recentRelayFailures`. 4th consecutive cycle blocked from new external fact-verification —
   worth the owner's attention if it doesn't self-resolve, since it's now blocking the standing re:Post-backlog
   priority every cycle it persists.

## Cycle 2026-07-19 (cloud routine)
10. **Shipped the deferred org_license email-delivery fix** (`edfba40`): `_store_license` in `grace-api/app.py`
    generated + stored a real license key on a $14,999 checkout but never sent it anywhere the buyer could see it —
    queued since D9/D14, deferred twice more (D14, D15) each time a more urgent truth/harm fix pre-empted it. This
    cycle found no more-urgent issue, so it finally got picked up. Now sends the key via the existing Resend path
    (same pattern as audit-PDF delivery); a self-review catch corrected an initially-dead "verify" link to the real
    working API endpoint. 2 new regression tests, 38/38 green. **Code-only** — needs the owner's next `eolkits-api`
    VPS redeploy to take effect in production (not on the git-push auto-deploy path); folded into the existing HQ-4
    SSH trip so it isn't a new standalone owner ask.
11. **Re-confirmed the WebFetch/proxy outage — 5th consecutive cycle** (07-15, -16, -18, -19), and this cycle found a
    concrete reason the outage rule matters: a `WebSearch` sanity-check for the Node20 Lambda block date returned
    the exact superseded 2026 dates (D3 already corrected these on 2026-07-13) — confirming search alone can't
    safely stand in for a working `WebFetch` against the authoritative AWS table. Skipped new re:Post answers/dev.to
    again. Worth the owner's attention if it doesn't clear soon — it's now blocked the standing distribution
    priority for 5 straight cycles.

## Cycle 2026-07-20 (cloud routine)
12. **Root-caused the "WebFetch outage"** (6 consecutive cycles: 07-15, -16, -18, -19, -20): `/root/.ccr/README.md`
    states plainly that a 403 from the proxy is an **organization egress-policy denial**, not a transient fault —
    "do not retry or route around it, report the blocked host." This environment's policy allowlists only package
    registries (npm/PyPI/crates/Go proxy) and denies general web including neutral controls and AWS docs. **This is
    not going to clear on its own** — re-testing it every cycle was the wrong framing; see DECISIONS D17 and
    HUMAN_QUEUE for the owner-facing ask. The content engine's only viable path now is sourcing new articles/pages
    entirely from data **already verified and live in this repo** (as D15's Gumroad playbook and the 07-19 article-08
    commit both already did) — new re:Post answers (which require finding + confirming a real new thread URL each
    time) have no such substitute and stay blocked until the policy changes.
13. **Found (2026-07-19, unlogged until now):** a separate process pushed `content(devto): add article 08` (commit
    `5747950`, Node 22 `crypto.createCipher` removal) after D16's cycle commit — real, non-duplicative, low-risk
    fact (a well-established Node.js API removal, not a disputed AWS date). Logged here for continuity.
14. **Fresh no-fetch truth/harm audit found no new issue** — traced `apps/runner/main.py`'s job handlers against
    `_execute_job`/`_dispatch_runner` in `grace-api/app.py`; confirmed `handle_license_key`/`handle_drift_watch_setup`
    are dead code (the real license logic is `_store_license`, already fixed D16; drift_watch has no dispatch case,
    consistent with D14's already-shipped fix). The known gap surface stays closed.
15. **Shipped dev.to article 09** (`09-lambda-glibc-version-not-found.md`) — the `GLIBC_2.28 not found` native-Lambda-
    dependency error, sourced entirely from the already-verified `apps/web/content/fixes.yml` entry (no new fetch).
    Non-duplicative of articles 01–08. Canonical → the real, registered `/fix/lambda-glibc-version-not-found/` page.
    Frontmatter validated against the repo's own `publish_devto.py` parser.

## Cycle 2026-07-21 (cloud routine)
16. **WebFetch re-tested, still 403 on the neutral control (`example.com`)** — 7th cycle blocked from fresh external
    fact-checking (07-15, -16, -18, -19, -20, -21; no 07-17 run recorded). Per D17's root cause (permanent egress
    policy denial, not transient), no re-diagnosis needed — went straight to the no-new-fetch content path.
17. **Shipped dev.to article 10** (`10-python-asyncio-has-no-attribute-coroutine.md`) — the Python 3.11
    `AttributeError: module 'asyncio' has no attribute 'coroutine'` removal, sourced entirely from the
    already-verified `fixes.yml` entry (`python-asyncio-has-no-attribute-coroutine`, `source_url:
    docs.python.org/3/whatsnew/3.11.html`, itself an uncontroversial, long-established Python stdlib fact, not a
    disputed AWS date). Non-duplicative of articles 01–09 (checked: no existing article covers the asyncio.coroutine
    removal; article 04's one "asyncio" mention is an unrelated telnetlib3 replacement note). Canonical → the real,
    registered `/fix/python-asyncio-has-no-attribute-coroutine/` page. Frontmatter validated against
    `publish_devto.py`'s own `_parse()` for all 10 articles — title/canonical_url/4-tag-max all parse correctly.

## Cycle 2026-07-22 (cloud routine)
18. **WebFetch re-tested, still 403 on the neutral control (`example.com`)** — 8th cycle blocked from fresh external
    fact-checking (07-15, -16, -18, -19, -20, -21, -22; no 07-17 run recorded). Per D17's root cause (permanent
    egress policy denial), no re-diagnosis needed — went straight to the no-new-fetch content path.
19. **Shipped dev.to article 11** (`11-node-decoder-routines-unsupported.md`) — the OpenSSL 3
    `error:1E08010C:DECODER routines::unsupported` failure when Lambda loads a legacy-format (PKCS#1 / weak-cipher)
    private key after a Node.js runtime upgrade, sourced entirely from the already-verified `fixes.yml` entry
    (`node-error-decoder-routines-unsupported`, `source_url: nodejs.org/api/crypto.html`). Confirmed non-duplicative
    of article 06 (which covers a *different* OpenSSL 3 error — build-time `digital envelope routines::unsupported`
    from webpack's MD4 hash call, not runtime key decoding). Canonical → the real, registered
    `/fix/node-error-decoder-routines-unsupported/` page. Frontmatter validated against `publish_devto.py`'s own
    `_parse()` for all 11 articles — title/canonical_url/4-tag-max all parse correctly, no duplicate titles.

## Cycle 2026-07-23 (cloud routine)
20. **WebFetch re-tested, still 403 on the neutral control (`example.com`)** — 9th consecutive cycle blocked from
    fresh external fact-checking (07-15, -16, -18, -19, -20, -21, -22, -23; no 07-17 run recorded). Per D17's root
    cause (permanent egress policy denial), no re-diagnosis needed — went straight to the no-new-fetch content path.
21. **Found (unlogged until now): a separate process pushed `fix(site): correct live blog Node-20 block dates to
    AWS-accurate Feb 1 / Mar 3, 2027`** (commit `ab660bc`, authored "Eve" + Claude Opus 4.8, dated 2026-07-22) after
    article 11's commit — corrected the last two stale "Sep 30, 2026" mentions in `launch/blog-post.md` +
    `apps/web/build.py`'s blog-index copy to the same AWS-authoritative Feb 1 / Mar 3 2027 dates D3 established
    2026-07-13. Consistent with already-verified facts, no conflict — logged here per the article-08 precedent (D17).
22. **Shipped dev.to article 12** (`12-lambda-importmoduleerror-triage.md`) — a triage/decision-tree guide for
    `Runtime.ImportModuleError: Cannot find module` that identifies which of four root causes applies (aws-sdk v2
    removal, esbuild 0.22+ external node_modules, layer OS/arch mismatch, glibc/native-binary mismatch) and routes
    two of them to the existing deep-dive articles (05, 09) rather than duplicating them. Sourced entirely from the
    already-verified `fixes.yml` entry (`lambda-runtime-importmoduleerror-cannot-find-module`, `source_url:
    repost.aws/knowledge-center/lambda-import-module-error-nodejs`) — no new external fetch. Confirmed non-duplicative:
    article 05 is a deep migration guide for the aws-sdk-specific case only; article 09 is a deep dive on the glibc
    case only; this is the first piece covering the full triage plus the esbuild/layer-arch causes neither existing
    article treats in depth. Canonical → the real, registered `/fix/lambda-runtime-importmoduleerror-cannot-find-module/`
    page (slug confirmed in `fixes.yml`). Frontmatter validated via `publish_devto.py`'s own `_parse()` against all 12
    articles — title/canonical_url/4-tag-max all parse correctly, zero duplicate titles. Also ran `apps/web`'s own
    `test_determinism.py` (4/4) and `test_surge.py` (4/4 assertions) in a jail-local `python3.12` venv (deleted after
    use) to confirm the unrelated blog-date commit (#21) didn't regress the build — clean.
23. **This exhausts the currently-scoped no-fetch dev.to backlog** per PLAN's prior "remaining fixes.yml entries"
    note — AL2023 dnf/iptables package-management errors and the stdlib-removal pieces (`smtpd`, `asyncore`) are the
    next candidates once picked up (each already has a `fixes.yml` entry with a source_url, so still no-fetch-viable).

## Cycle 2026-07-24 (cloud routine)
24. **WebFetch re-tested, still 403 on the neutral control (`example.com`)** — 10th consecutive cycle blocked from
    fresh external fact-checking (07-15, -16, -18 through -24; no 07-17 run recorded). Per D17's root cause (permanent
    egress policy denial), no re-diagnosis needed — went straight to the no-new-fetch content path.
25. **Truth/harm sweep found nothing new** — checked all commits since the last cycle's audit (07-23 → 07-24): only
    automated `chore(status): synthetic check` and dependency-bump commits landed from other routines; no new
    fulfillment-path or checkout-path change to review this cycle.
26. **Shipped dev.to article 13** (`13-al2023-dnf-unable-to-find-a-match.md`) — the AL2023 `Error: Unable to find a
    match: <package>` dnf lookup failure (renamed/version-namespaced/SPAL/EPEL/dropped packages after moving off
    AL2), sourced entirely from the already-verified `fixes.yml` entry (`amazon-linux-2023-dnf-unable-to-find-a-match`,
    `source_url: docs.aws.amazon.com/linux/al2023/ug/package-management.html`) — no new external fetch. Confirmed
    non-duplicative: article 01 only lists this error in a one-line overview table, no dedicated deep dive. Canonical
    → `/fix/amazon-linux-2023-dnf-unable-to-find-a-match/`, confirmed already referenced from the live, deployed AL2
    checklist page (`build_al2_checklist_page` in `apps/web/build.py`) — not a new orphan page. Frontmatter validated
    via `publish_devto.py`'s own `_parse()` against all 13 articles — 4 tags each, zero parse errors, zero duplicate
    titles. Ran `apps/web`'s `test_determinism.py` + `test_surge.py` (4/4 total) in a fresh jail-local `python3.12`
    venv (deleted after use) — regression-clean.

## Next actions (priority order) — post-pivot
- **P0 — Owner (one-time, then autonomous forever):** the flywheel publishes — HQ-7 `vsce publish`, HQ-8 `ovsx publish`,
  HQ-9 PyPI/npm, HQ-10 GitHub Action listing, HQ-11 confirm dev.to key. Plus HQ-4 GitHub App (enables the $1,499 Pack),
  HQ-6 one real test purchase, and now **HQ-1′/HQ-2′ (Gumroad — fully built, ~10 min to publish)**. **All one-time
  setup — no ongoing owner time** (fits the constraint).
- **P0-NEW — Owner, only if you want live web fact-checking back:** this cloud environment's egress policy denies
  general web access by design (confirmed via `/root/.ccr/README.md`, not a bug) — see HUMAN_QUEUE. Without it, new
  re:Post answers (which need a freshly-found, confirmed real thread) can't be drafted from this environment; new
  dev.to articles still can, as long as they're sourced from already-repo-verified facts (as article 09 was).
- **P1 — Agent (next cycle):** another no-new-fetch dev.to article, sourced from a `fixes.yml` entry not yet covered:
  `amazon-linux-2023-iptables-service-not-found` (the nftables migration counterpart to article 13's dnf piece — also
  only a passing mention in article 01 today), or the stdlib-removal pieces (`python-no-module-named-smtpd`,
  `python-no-module-named-asyncore` — could combine into one "Python 3.12 stdlib removals" piece as article 10 did
  for `asyncio.coroutine`). Same safe pattern as articles 09–13, no fetch needed.
- **Done 2026-07-24:** shipped dev.to article 13 (`amazon-linux-2023-dnf-unable-to-find-a-match`, commit `9cc53dc`).
- **Done 2026-07-23:** shipped dev.to article 12 (`lambda-runtime-importmoduleerror-cannot-find-module`, commit
  `d93d830`) — see above.
- **Done 2026-07-22:** shipped dev.to article 11 (`node-error-decoder-routines-unsupported`, commit `ab660bc`'s
  parent, i.e. `e3fdf6f`) — see above.
- **Done 2026-07-21:** shipped dev.to article 10 (`python-asyncio-has-no-attribute-coroutine`, commit `709d367`).
- **Done 2026-07-19:** fixed `org_license`'s missing license-key email delivery (commit `edfba40`, DECISIONS D16) —
  code-only, still needs the owner's next VPS redeploy of `eolkits-api` to take effect live (folded into HQ-4).
- **Done 2026-07-15:** repo-wide grep (`.md`/`.py`/`.yml`/`.html`/`.ts`/`.js`/`.mjs`) for the same fabricated-tier
  pattern (`eolkits-kits`, "Team ($999)", "Enterprise ($2,499)", fake Slack/on-call/pairing claims) found no other
  live occurrence outside the 3 kit READMEs already fixed (one stale mention remains in the **retired, undeployed**
  `apps/worker` — left alone per prior DECISIONS "do not revive").
- **Done 2026-07-16:** pulled `drift_watch`'s live self-serve checkout (§2.5 do-no-harm — see DECISIONS D14); a real
  §2.5 truth/harm violation, not padding.
- **Done 2026-07-18:** built the Gumroad bundle (`launch/gumroad/`) — zip build script + migration playbook +
  ATTRIBUTIONS + ready-to-paste listing copy. Bet A′ is now a single owner publish-click. See DECISIONS D15.
- **P2 — Agent:** write the one-command PUBLISH docs for `vsce`/`ovsx`/PyPI so each owner publish is copy-paste.

## Leading indicator to watch
`eolkits.com/status` (data.json, rebuilt daily) — the first `checkout_click` in `track.js` means a buyer is imminent.
Clicks with no buys ⇒ a conversion/trust problem to fix, not a traffic problem.
