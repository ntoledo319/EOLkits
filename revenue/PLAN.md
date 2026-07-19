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

## Next actions (priority order) — post-pivot
- **P0 — Owner (one-time, then autonomous forever):** the flywheel publishes — HQ-7 `vsce publish`, HQ-8 `ovsx publish`,
  HQ-9 PyPI/npm, HQ-10 GitHub Action listing, HQ-11 confirm dev.to key. Plus HQ-4 GitHub App (enables the $1,499 Pack),
  HQ-6 one real test purchase, and now **HQ-1′/HQ-2′ (Gumroad — fully built, ~10 min to publish)**. **All one-time
  setup — no ongoing owner time** (fits the constraint).
- **P1 — Agent (next cycle):** a new, non-duplicative dev.to article — first re-verify WebFetch/primary-source access
  is back (it has now 403'd on every URL for **5 consecutive cycles** — 2026-07-15, -16, -18, -19 — including a
  control site and the AWS docs URL directly, plus this cycle's proof that `WebSearch` alone surfaces stale/wrong
  dates — see DECISIONS D14/D15/D16); if still down, ship a tutorial-format piece instead (e.g. "scan your AWS
  account for EOL runtimes free" using an already-verified kit) rather than risk a stale-date error.
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
