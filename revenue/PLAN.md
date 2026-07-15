WORKSPACE_ROOT: /Users/nicholastoledo/Development/active/Rupture

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
- **Human unlocks:** HQ-1′ (Gumroad account — one-time; verify KYC clears), HQ-2′ (agent builds the bundle zip +
  listing copy; owner clicks publish). **Not yet built — next cycle.**

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

## Next actions (priority order) — post-pivot
- **P0 — Owner (one-time, then autonomous forever):** the flywheel publishes — HQ-7 `vsce publish`, HQ-8 `ovsx publish`,
  HQ-9 PyPI/npm, HQ-10 GitHub Action listing, HQ-11 confirm dev.to key. Plus HQ-4 GitHub App (enables the $1,499 Pack)
  and HQ-6 one real test purchase. **All one-time setup — no ongoing owner time** (fits the constraint).
- **P1 — Agent (next cycle):** authority content ship — a dev.to article "The AWS Lambda Node.js 20 deadline everyone
  gets wrong" (many blogs cite the superseded Sep 30 2026; AWS delayed it to Mar 3 2027) → auto-publishes + backlinks.
  This is the highest-leverage autonomous move now that outreach is off the table.
- **P1 — Agent (next cycle):** build the **Gumroad bundle** (zip + playbook + listing copy) so Bet A′ is one publish-click.
- **P2 — Agent:** reframe AL2 copy/pyproject from "before Jun 30 2026" (past) to post-EOL emergency; verify the live
  `/migrate` AL2 page shows correct post-deadline framing.
- **P2 — Agent:** write the one-command PUBLISH docs for `vsce`/`ovsx`/PyPI so each owner publish is copy-paste.

## Leading indicator to watch
`eolkits.com/status` (data.json, rebuilt daily) — the first `checkout_click` in `track.js` means a buyer is imminent.
Clicks with no buys ⇒ a conversion/trust problem to fix, not a traffic problem.
