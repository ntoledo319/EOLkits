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
buyer in 28 days** — every payment channel is first-publish KYC-gated. The two paths that can actually collect $4k
both need ~15–60 min of owner account/click work (batched in HUMAN_QUEUE). Realistic honest outcomes: autonomous-only
≈ **$0–600**; owner does Upwork + 1–2 closes ≈ **$1,000–2,500**; full **$4,000** needs 3 Migration-Pack sales or a
strong Upwork run — both owner-dependent.

---

## The 2–3 concurrent bets (§6)

### Bet A — FAST · Productized "AWS runtime EOL audit + fix PR" gig on Upwork/Fiverr
- **Frame:** sell a service artifact on a marketplace that supplies BOTH demand and escrow payment.
- **Arithmetic to $4k:** gig priced **$499**; Upwork 10% → **$449.10 net/gig**. 1 gig = first dollar; a healthy
  new-seller 4-wk run of **3–4 gigs = $1,347–$1,796 net** (≈⅓–½ of goal). Pair with Bet B to reach $4k.
- **Funnel:** Upwork job feed (CTOs posting "migrate Lambda off Node 18/20", "Amazon Linux 2 upgrade", "Python 3.10
  Lambda EOL") where the owner submits **agent-drafted** proposals; + Fiverr search for "AWS Lambda runtime upgrade."
  Built-in buyer intent + escrow; no owned audience needed.
- **Falsifier:** owner sends ~15 agent-drafted proposals over 2 weeks → **0 funded contracts** ⇒ niche/new-seller
  thesis dead; shift effort to Bet B + Bet C.
- **Human unlocks:** HQ-1 (Upwork/Fiverr account + KYC), HQ-2 (publish gig), HQ-3 (send drafted proposals).

### Bet B — HEAVY · $1,499 Migration Pack (real PR, CI-fail auto-refund)
- **Frame:** fixed-scope service artifact via the already-live Stripe link; highest revenue-per-unit.
- **Arithmetic to $4k:** $1,499 gross, Stripe 2.9%+$0.30 → **$1,455.23 net/sale**. **3 sales = $4,365.69 = clears the
  goal outright.** 2 = $2,910; 1 = $1,455 (36%).
- **Funnel:** the CI-failure moment — the GitHub Action PR comment + (once registered) the GitHub App surface
  "[Have it fixed: Migration Pack]" exactly when a deprecated runtime blocks a merge. Secondary: upsell a $299-audit
  buyer. The auto-refund-if-CI-fails guarantee makes a cold $1,499 ask viable.
- **Falsifier:** `sandbox_e2e.py` against a sandbox repo does **not** produce a clean, CI-passing PR end-to-end
  (grace-api + github-app path is UNVERIFIED today) ⇒ pull the Pack until proven; or no repo-access buyer in 28 days.
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

## Next actions (priority order)
- **P0 — Owner:** burn down HUMAN_QUEUE, KYC items first (HQ-1 Upwork, HQ-4 GitHub App, HQ-6 test purchase).
- **P1 — Agent (next cycle):** on Upwork "yes" → re-run demand search + draft one tailored proposal per live job.
  Publish the VS Code `.vsix` prep is done; write an `ovsx`/`vsce` one-command PUBLISH doc. Draft the Gumroad/Lemon
  Squeezy "AWS EOL Migration Toolkit" bundle as a first-dollar fallback.
- **P1 — Agent (next cycle):** authority content ship — a dev.to article "The AWS Lambda Node.js 20 deadline everyone
  gets wrong" (many blogs cite the superseded Sep 30 2026; AWS delayed it to Mar 3 2027) → auto-publishes + backlinks.
- **P2 — Agent:** reframe AL2 copy/pyproject from "before Jun 30 2026" (past) to post-EOL emergency; verify the live
  `/migrate` AL2 page shows correct post-deadline framing.

## Leading indicator to watch
`eolkits.com/status` (data.json, rebuilt daily) — the first `checkout_click` in `track.js` means a buyer is imminent.
Clicks with no buys ⇒ a conversion/trust problem to fix, not a traffic problem.
