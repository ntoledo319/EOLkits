# HUMAN_QUEUE — batched owner actions (§10)

Every item: **what / why human-only / click-by-click / link / minutes.** The agent cannot legally or
technically do these (KYC, marketplace publish, VPS SSH, sending messages). **Do the CORE BATCH first** —
it is the only thing standing between "$0" and real revenue. Running total kept lean (§3: ≤60 min for the run).

Legend: 🔴 KYC-latency (start first) · 🟢 minutes of clicking · ⚪ optional/compounding.

---

## ⛔ REMOVED 2026-07-14 (owner constraint — DECISIONS D7)
- ~~HQ-1 Upwork account~~, ~~HQ-2 publish Upwork/Fiverr gig~~, ~~HQ-3 send proposals~~ — owner won't do Upwork
  (ongoing personal time) or Fiverr (KYC won't clear). No outreach path. See `OPPORTUNITIES.md`.

## 🎯 FASTEST PATH TO ACTUAL BUYERS — paste ready-made answers (drafts stay stocked automatically)
The agent can't post as you or cold-contact anyone (the one hard rule), so the closest-to-a-buyer move is answering
people **already asking about this exact EOL**. Vetted, help-first, TOS-clean answers are ready to paste:
- **`launch/distribution/repost-answers.md`** — batch 1 (3 answers). ✅ **Owner posted all 3 on 2026-07-15 (pending moderation).**
- **`launch/distribution/repost-answers-batch2.md`** — batch 2 (**7 more**, drafted + accuracy/uniqueness-vetted 2026-07-15).
**AUTOMATED:** the nightly routine now keeps this backlog stocked — it drafts fresh answers to new questions each cycle
(it never posts). So your only job is: open a file, paste each answer to its linked thread from your re:Post account
(one unique answer per thread). Each is a real engineer with the problem now — peak intent, $0, durable SEO/backlinks.

## CORE BATCH — one-time setups, then autonomous forever (fits the "no ongoing time" constraint)

### 🟢 HQ-1′ + HQ-2′ — Publish the Gumroad bundle (built 2026-07-18)  *(Bet A′ · ~10 min total, one-time)*
- **Why human-only:** account + payout/KYC (Merchant of Record) + the actual "Publish" click. **Watch:** Fiverr
  wouldn't verify you — if Gumroad also rejects KYC, sell the bundle via the existing eolkits.com Stripe rail instead
  (no new account needed; ping the agent next cycle to wire up a `bundle` SKU in `pricing.yml`).
- **Everything else is done** — `launch/gumroad/` has the built+verified zip source, the migration playbook, license
  ATTRIBUTIONS, and the entire Gumroad listing copy (title/price $79/description/tags/refund policy) ready to paste.
- **Steps:** 1) https://gumroad.com → sign up → add payout method (~5 min). 2) From the repo root:
  `bash launch/gumroad/build_bundle.sh` (writes `launch/gumroad/dist/eolkits-migration-toolkit.zip`). 3) On Gumroad,
  **New product → Digital product** → paste every field from `launch/gumroad/LISTING-COPY.md` → upload the zip →
  **Publish**. Full walkthrough with exact copy-paste text is in that file. **~10 min.**

### 🔴 HQ-4 — Register the GitHub App + put creds on the GRACE box  *(Bet B · ~10 min, one-time)*
- **Why human-only:** requires GitHub org settings + SSH to the VPS (key is on your Mac only, outside the agent's jail).
- **Steps:** 1) https://github.com/settings/apps/new → name "EOLkits Migration", set permissions (Contents: R/W,
  Pull requests: R/W), generate a **private key** (.pem). 2) `ssh ubuntu@15.204.209.97`; paste `APP_ID` + the key path
  into `/home/ubuntu/sites/eolkits-api/.env.production`; restart `eolkits-api`.
- **Link:** https://github.com/settings/apps/new · **~10 min**.

### 🟢 HQ-6 — Run ONE real end-to-end purchase (de-risk fulfillment)  *(Bets A/B · ~5 min)*
- **Why human-only:** a real card charge; the last un-derisked link (Stripe → PDF/PR → email has never fired for a
  real payment). Refund yourself after.
- **Steps:** Buy the **$299 audit** at https://eolkits.com/audit with your own card → confirm the PDF email arrives
  ≤5 min → refund in the Stripe dashboard. (Ideally also HQ-5 below before selling the $1,499 Pack.)
- **~5 min.**

### 🟡 HQ-5 — Prove the $1,499 Pack end-to-end BEFORE selling it  *(Bet B · ~30 min — the guarantee must be real)*
Money-path reviewed 2026-07-14 (see DECISIONS D9). Fully coded; the worst bug is fixed (installation fallback + test).
Remaining gates — **do not sell a Pack until all pass** (a broken PR or broken refund destroys trust):
1. **PR half (no payment):** after HQ-4, run `docker exec eolkits-api python /app/runner/scripts/sandbox_e2e.py` with
   real App creds against `ntoledo319/eolkits-sandbox` → expect `{"ok": true, "pr_url": …}`; confirm the PR really opened
   with a diff + the guarantee body + labels.
2. **Refund half (real self-purchase — the only true test):** buy a Pack with your own card + the sandbox repo + a
   correct installation_id ($1,499, refund yourself) → confirm the PR opens and `/status` shows `pr_number` set → make
   CI **fail** → confirm GitHub delivered `check_run/completed/failure`, `purchases.refunded=1`, the Stripe refund, and
   the refund email. Then repeat with the `override:ci-failure` label and confirm **no** refund fires.
3. **Decide two policy gaps first (DECISIONS D9):** (a) repos using the legacy **Status API** get no auto-refund —
   subscribe to `status` events or document it; (b) refund currently fires on **any** red check — a flaky third-party
   check → a full $1,499 refund. Decide the refund policy before selling.

### 🔴 HQ-5b — org_license / drift_watch fulfillment gaps (§2.5) — **UPDATE 2026-08-14: drift_watch's backend charge endpoint closed in code, do the Stripe-dashboard step below NOW (2 min, no VPS needed)**
**UPDATE 2026-08-14 (elevated priority — do item 0 today, it's the fastest close on an active-harm exposure in this
whole queue):** this cycle found that D14's 2026-07-16 fix only removed the *frontend* `/drift/` checkout form —
the backend `POST /api/drift/checkout` endpoint itself was still live in `apps/grace-api/eolkits_grace/app.py` and
would open a real, recurring **$19/mo Stripe subscription** for anyone who reached it directly (a stale bookmark,
an old shared link, a cached reference), for a product (`drift_watch`) whose fulfillment is a confirmed no-op —
meaning a real subscriber would be billed monthly, forever, for literally nothing happening. **Fixed in code this
cycle** (the endpoint now returns `410` instead of charging — see DECISIONS D42) **but this needs the same VPS
redeploy as item 2 below to take effect in production** — until then the old, harmful behavior is still live.
0. **DO THIS NOW, doesn't need the VPS or any code deploy — deactivate the `drift_watch` Stripe Price/Payment Link**
   in the Stripe dashboard. This is the only immediate way to close the live exposure before your next VPS visit.
   ~2 min. Link: https://dashboard.stripe.com/prices → find "Drift Watch" → deactivate/archive the price.
1. Once you're on the VPS anyway (see item 2 / HQ-4), redeploy `eolkits-api` so the code-level fix (the endpoint
   returning 410) actually takes effect — folds into the same trip, no separate action.
2. **org_license ($14,999/yr) email-delivery gap — FIXED IN CODE 2026-07-19 (commit `edfba40`), NEEDS A VPS REDEPLOY
   TO GO LIVE.** `_store_license` in `grace-api/app.py` used to generate and store a real license key but never
   email it to the buyer; it now sends it via the existing Resend path (same as audit-PDF delivery), tested
   (38/38 green — see DECISIONS D16). **Why this is still a queue item:** `apps/grace-api` is not on the git-push
   auto-deploy path (only `apps/web`/the static site is) — this fix sits in the repo but does nothing in production
   until you next redeploy `eolkits-api` on the VPS. **Action:** next time you SSH in for any reason (e.g. HQ-4's
   GitHub App creds), redeploy `eolkits-api` so this AND the drift-checkout fix both land — one trip, two fixes.
3. **Once drift_watch fulfillment is actually built** (real IAM-role validation + a scheduled weekly scan + delta
   PDF — a multi-day feature, intentionally not attempted autonomously given the security sensitivity of assuming a
   customer's IAM role), revert the "coming soon" copy and restore the checkout.

---

## OPTIONAL / COMPOUNDING BATCH — do when convenient (Bet C flywheel; not an in-window $4k driver)

### ⚪ HQ-7 — Publish the VS Code extension  *(~8 min · package already built)*
- Steps: 1) https://aka.ms/vscode-create-publisher → create publisher **`eolkits`** (Microsoft acct). 2)
  https://dev.azure.com → User Settings → Personal Access Tokens → new token, scope **Marketplace: Manage**. 3) In
  `apps/vscode-extension/`: `npx vsce login eolkits` (paste PAT) → `npx vsce publish`. Live in minutes. Zero fees.

### ⚪ HQ-8 — Publish to Open VSX  *(~6 min · reaches Cursor/VSCodium/Gitpod)*
- Steps: sign in at https://open-vsx.org with GitHub → create an access token → sign the Publisher Agreement →
  `npx ovsx publish -p <token>` from `apps/vscode-extension/`.

### ⚪ HQ-9 — Publish the CLIs to PyPI (+ lambda-lifeline to npm)  *(~10 min · makes `pip install` real)*
**✅ DE-RISKED 2026-07-14:** all three names are free (al2023-gate, python-pivot on PyPI; lambda-lifeline on npm);
both wheels build, pass `twine check`, install clean into a fresh venv, and their console scripts run; npm packs
clean. Exact verified copy-paste commands are in **`launch/PUBLISH-CHECKLIST.md` §1–2**. Just create the accounts
(PyPI: register+2FA+token; npm: `npm login`) and run them. AL2 pyproject copy already reframed post-EOL.

### ⚪ HQ-10 — List the GitHub Action on Marketplace  *(~5 min · free; peak-intent funnel · NO new repo needed)*
- **Verified (GitHub docs):** list it **directly from the existing EOLkits repo** — root `action.yml` is present with
  name/description/branding, monorepos are allowed, and tags exist. Steps: on GitHub open `action.yml` → **Draft a
  release** → check **Publish this Action to the GitHub Marketplace** → accept the Developer Agreement (first time) →
  pick categories → set tag+title → **Publish** (2FA). Full detail: `launch/PUBLISH-CHECKLIST.md` §5.

### ⚪ HQ-11 — Confirm DEVTO_API_KEY is on the box  *(~1 min · likely already done)*
- Prior handoff says the key is at `/home/ubuntu/.eolkits-dist.env`. Verify the daily cron is auto-publishing dev.to
  articles; if not, drop/rotate the key. Unblocks autonomous backlink publishing.

---

## Cycle 2026-07-15 (cloud routine)
No new items added — this cycle's ship (README truth fix, commit `915ebb1`) was fully autonomous, in-jail, $0, no
human contact needed. The queue below is unchanged from 2026-07-14; **HQ-7/HQ-10/HQ-4 remain the highest-ROI owner
clicks** (they unlock the discovery flywheel every other bet depends on).

## Cycle 2026-07-16 (cloud routine)
HQ-5b updated (see above) — drift_watch's live checkout is pulled (fully autonomous, in-jail, $0). Two small optional
items added under HQ-5b (deactivate the Stripe Price; note the org_license email gap for the next VPS redeploy).
Nothing here requires urgent owner action; **HQ-7/HQ-10/HQ-4 + pasting the answer backlog remain highest-ROI.**

## Cycle 2026-07-18 (cloud routine)
HQ-1′/HQ-2′ merged and fully specified — the Gumroad bundle (zip + playbook + attributions + listing copy) is built
and verified; the owner's remaining step is purely account+publish clicks (~10 min), no agent work left on Bet A′.
**Tooling note:** WebFetch/direct-proxy fetch has now failed for 4 consecutive cycles (2026-07-15, -16, -18 —
confirmed today via `$HTTPS_PROXY/__agentproxy/status` as a gateway-level `connect_rejected` policy denial on
`example.com` and AWS docs both). This blocks new re:Post-answer drafting and new dev.to articles until it clears —
not an owner action item yet, but flagging in case it doesn't self-resolve.

## Cycle 2026-07-19 (cloud routine)
HQ-5b's org_license item updated: the code fix is done and tested (commit `edfba40`), the remaining ask is just
"redeploy `eolkits-api` next time you're on the VPS anyway" — no new standalone action, folded into HQ-4's existing
SSH trip. WebFetch/proxy outage confirmed persistent a 5th consecutive cycle (2026-07-15, -16, -18, -19); this is
now blocking the standing re:Post-answer-backlog priority for that long — worth a look if it doesn't clear on its
own, since it's the main thing keeping the content engine idle each cycle.

## ⚪ NEW 2026-07-20 — Optional: restore live web fact-checking for this cloud environment
- **What:** the WebFetch/WebSearch-verification path has been blocked for 6 consecutive daily cycles
  (2026-07-15, -16, -18, -19, -20). This cycle root-caused it: `/root/.ccr/README.md` (the environment's own proxy
  diagnostic) states a 403 from the proxy is an **organization egress-policy denial** — "do not retry or route
  around it, report the blocked host." The policy allowlists package registries (npm, PyPI, etc.) but denies general
  web hosts, including a neutral control (`example.com`) and `docs.aws.amazon.com`. **This will not self-resolve.**
- **Why human-only:** changing a cloud environment's network egress policy is an environment-config action outside
  the agent's WORKSPACE_ROOT jail (§1) — the agent cannot and should not touch it.
- **Impact if left as-is:** new re:Post answers (which require finding + confirming a real new thread each cycle)
  stay permanently blocked from this environment. New dev.to articles can still ship **if** sourced entirely from
  facts already verified and recorded in this repo (as articles 08 and 09 both did) — a real but narrower channel.
- **If you want it fixed:** check this environment's network/egress policy settings (wherever this Claude Code cloud
  environment was configured) and allow outbound HTTPS to general web hosts, or at minimum `docs.aws.amazon.com` +
  `repost.aws` + `stackoverflow.com`, for this session/environment. If that's not something you control or want
  changed, no action needed — the content engine will keep shipping from repo-verified facts only.
- **Not time-boxed / no minutes estimate** — depends entirely on your environment's admin console, which this queue
  has no visibility into.

## Cycle 2026-07-21 (cloud routine)
No new items added — this cycle's ship (dev.to article 10, no-new-fetch) was fully autonomous, in-jail, $0, no
human contact needed. WebFetch outage confirmed persistent a 7th consecutive cycle; the standing owner-facing ask
above (2026-07-20 entry) is unchanged — no new information to add, not re-logging it as a fresh item.

## Cycle 2026-07-22 (cloud routine)
No new items added — this cycle's ship (dev.to article 11, no-new-fetch) was fully autonomous, in-jail, $0, no
human contact needed. WebFetch outage confirmed persistent an 8th consecutive cycle; the standing owner-facing ask
above (2026-07-20 entry) is unchanged. **Still the highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′
(Gumroad, ~10 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).** None show any observed
signal of having been done yet (no new listing/install shows up in this repo's state — the agent has no visibility
into Gumroad/marketplace dashboards directly, only what would show up here or on `eolkits.com/status`).

## Cycle 2026-07-23 (cloud routine)
No new items added — this cycle's ship (dev.to article 12, no-new-fetch) was fully autonomous, in-jail, $0, no
human contact needed. WebFetch outage confirmed persistent a 9th consecutive cycle; the standing owner-facing ask
above (2026-07-20 entry) is unchanged. **Still the highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′
(Gumroad, ~10 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).** None show any observed
signal of having been done yet (no new listing/install shows up in this repo's state — the agent has no visibility
into Gumroad/marketplace dashboards directly, only what would show up here or on `eolkits.com/status`). 10 days
into the 28-day window (Day 0 = 07-13); at $0 collected, the gap math in PLAN.md (Bet B needs one $1,499 sale — gated
on HQ-4/5/6 — to move the needle materially) is unchanged from last cycle.

## Cycle 2026-07-24 (cloud routine)
No new items added — this cycle's ship (dev.to article 13, no-new-fetch) was fully autonomous, in-jail, $0, no
human contact needed. WebFetch outage confirmed persistent a 10th consecutive cycle; the standing owner-facing ask
above (2026-07-20 entry) is unchanged. **Still the highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′
(Gumroad, ~10 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).** 11 days into the
28-day window (Day 0 = 07-13); at $0 collected, the gap math in PLAN.md is unchanged — none of these show any
observed signal of having been actioned yet.

## Cycle 2026-07-25 (cloud routine)
No new items added — this cycle's ship (dev.to article 14, no-new-fetch) was fully autonomous, in-jail, $0, no
human contact needed. WebFetch/proxy outage status checked (11th consecutive cycle since 07-15); consistent with
D17's root cause, no re-diagnosis performed. The standing owner-facing ask (2026-07-20 entry) is unchanged.
**Still the highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-7 (`vsce
publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).** 12 days into the 28-day window (Day 0 = 07-13); at
$0 collected, the gap math in PLAN.md is unchanged — none of these show any observed signal of having been
actioned yet.

## Cycle 2026-07-26 (cloud routine)
No new items added — this cycle's ship (dev.to article 15, no-new-fetch) was fully autonomous, in-jail, $0, no
human contact needed. WebFetch/proxy outage status checked (12th consecutive cycle since 07-15); consistent with
D17's root cause, no re-diagnosis performed. The standing owner-facing ask (2026-07-20 entry) is unchanged.
**Still the highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-7 (`vsce
publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).** 13 days into the 28-day window (Day 0 = 07-13); at
$0 collected, the gap math in PLAN.md is unchanged — none of these show any observed signal of having been
actioned yet.

## Cycle 2026-07-27 (cloud routine)
No new items added — this cycle's ship (dev.to article 17, no-new-fetch) was fully autonomous, in-jail, $0, no
human contact needed. WebFetch outage confirmed persistent a 13th consecutive cycle; the standing owner-facing ask
(2026-07-20 entry) is unchanged. **Still the highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′
(Gumroad, ~10 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).** 14 days into the
28-day window (Day 0 = 07-13); at $0 collected, the gap math in PLAN.md is unchanged — none of these show any
observed signal of having been actioned yet.

## Cycle 2026-07-28 (cloud routine)
No new items added — this cycle's ship (dev.to article 18, no-new-fetch) was fully autonomous, in-jail, $0, no
human contact needed. WebFetch outage confirmed persistent a 14th consecutive cycle; the standing owner-facing ask
(2026-07-20 entry) is unchanged. **Still the highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′
(Gumroad, ~10 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).** 15 days into the
28-day window (Day 0 = 07-13); at $0 collected, the gap math in PLAN.md is unchanged — none of these show any
observed signal of having been actioned yet.

## Cycle 2026-07-29 (cloud routine)
No new items added — this cycle's ship (dev.to article 19, no-new-fetch) was fully autonomous, in-jail, $0, no
human contact needed. WebFetch outage confirmed persistent a 15th consecutive cycle; the standing owner-facing ask
(2026-07-20 entry) is unchanged. **Still the highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′
(Gumroad, ~10 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).** 16 days into the
28-day window (Day 0 = 07-13); at $0 collected, the gap math in PLAN.md is unchanged — none of these show any
observed signal of having been actioned yet.

## Cycle 2026-07-31 (cloud routine)
No new items added — this cycle's ship (dev.to article 21, a synthesis piece, no-new-fetch) was fully autonomous,
in-jail, $0, no human contact needed. WebFetch outage confirmed persistent a 17th consecutive cycle; the standing
owner-facing ask (2026-07-20 entry) is unchanged. **Still the highest-ROI owner clicks, unactioned as of this
cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).**
18 days into the 28-day window (Day 0 = 07-13); at $0 collected, the gap math in PLAN.md is unchanged — none of
these show any observed signal of having been actioned yet.

## Cycle 2026-08-01 (cloud routine)
No new items added — this cycle's ships (a live truth-bug fix in `fixes.yml`, commit `668f505`, and dev.to article
22, symptom-first framing) were fully autonomous, in-jail, $0, no human contact needed. WebFetch outage confirmed
persistent an 18th consecutive cycle; the standing owner-facing ask (2026-07-20 entry) is unchanged. **Still the
highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-7 (`vsce publish`), HQ-10
(GitHub Action listing), HQ-4 (GitHub App).** 19 days into the 28-day window (Day 0 = 07-13); at $0 collected, the
gap math in PLAN.md is unchanged — none of these show any observed signal of having been actioned yet.

## Cycle 2026-08-02 (cloud routine)
No new items added — this cycle's ship (5 more instances of the recurring superseded-2026-date truth bug found and
fixed across `README.md` + `kits/lambda-lifeline/`, commit pending) was fully autonomous, in-jail, $0, no human
contact needed. WebFetch outage confirmed persistent a 19th consecutive cycle; the standing owner-facing ask
(2026-07-20 entry) is unchanged. **Still the highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′
(Gumroad, ~10 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).** 20 days into the
28-day window (Day 0 = 07-13); at $0 collected, the gap math in PLAN.md is unchanged — none of these show any
observed signal of having been actioned yet.

## Cycle 2026-08-03 (cloud routine) — Day 21 §8 gate
No new items added — this cycle's ship (a 13-instance truth-fix sweep across 8 files, incl. a live answer-template
file, commit pending) was fully autonomous, in-jail, $0, no human contact needed. This was the formal Day-21 gate
(§8); recomputed the gap ($0 collected, $4,000 gap, unchanged) and confirmed no pivot is warranted — see DECISIONS
D31. WebFetch outage confirmed persistent a 20th consecutive cycle; the standing owner-facing ask (2026-07-20
entry) is unchanged. **Still the highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10
min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).** 21 days into the 28-day window
(Day 0 = 07-13); at $0 collected, the gap math is unchanged — none of these show any observed signal of having
been actioned yet. **Only 7 days remain in the original 28-day window** — the core batch (HQ-1′/2′, HQ-4, HQ-6,
HQ-7, HQ-10, ~35 min total) is the only lever left that can still move the needle before Day 28.

## Cycle 2026-08-04 (cloud routine)
No new items added — this cycle's ship (a truth fix in the committed `docs/` build snapshot — the stale-date bug
found in a new layer, see DECISIONS D32) was fully autonomous, in-jail, $0, no human contact needed. WebFetch
outage confirmed persistent a 21st consecutive cycle; the standing owner-facing ask (2026-07-20 entry) is
unchanged. **Still the highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-7
(`vsce publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).** 22 days into the 28-day window (Day 0 =
07-13); at $0 collected, the gap math is unchanged — none of these show any observed signal of having been
actioned yet. **Only 6 days remain in the original 28-day window** — the core batch (HQ-1′/2′, HQ-4, HQ-6, HQ-7,
HQ-10, ~35 min total) is the only lever left that can still move the needle before Day 28.

## Cycle 2026-08-05 (cloud routine)
No new items added — this cycle's ship (cross-linking all 27 `/fix/` pages to `/eol-checker/`, commit `3314d93`)
was fully autonomous, in-jail, $0, no human contact needed. WebFetch outage confirmed persistent a 22nd consecutive
cycle; the standing owner-facing ask (2026-07-20 entry) is unchanged. **Still the highest-ROI owner clicks,
unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing),
HQ-4 (GitHub App).** 23 days into the 28-day window (Day 0 = 07-13); at $0 collected, the gap math is unchanged —
none of these show any observed signal of having been actioned yet. **Only 5 days remain in the original 28-day
window** — the core batch (HQ-1′/2′, HQ-4, HQ-6, HQ-7, HQ-10, ~35 min total) is the only lever left that can still
move the needle before Day 28. This cycle's truth-fix sweep and no-fetch content backlog both came up exhausted —
the agent-side autonomous levers inside the jail are now genuinely thin; the owner batch above is what's left.

## Cycle 2026-08-06 (cloud routine)
No new items added — this cycle's ship (cross-linking all 8 `/migrate/` pages + index to `/eol-checker/`, commit
`90a06ae`) was fully autonomous, in-jail, $0, no human contact needed. WebFetch outage confirmed persistent a 23rd
consecutive cycle; the standing owner-facing ask (2026-07-20 entry) is unchanged. **Still the highest-ROI owner
clicks, unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action
listing), HQ-4 (GitHub App).** 24 days into the 28-day window (Day 0 = 07-13); at $0 collected, the gap math is
unchanged — none of these show any observed signal of having been actioned yet. **Only 4 days remain in the
original 28-day window** — the core batch (HQ-1′/2′, HQ-4, HQ-6, HQ-7, HQ-10, ~35 min total) is the only lever left
that can still move the needle before Day 28.

## Cycle 2026-08-07 (cloud routine)
No new items added — this cycle's ship (cross-linking dev.to article 21 + Gumroad `MIGRATION-PLAYBOOK.md` to
`/eol-checker/`, commit `ad4893a`) was fully autonomous, in-jail, $0, no human contact needed. WebFetch outage
confirmed persistent a 24th consecutive cycle (now surfacing as an explicit `EGRESS_BLOCKED` error type rather than
a bare 403 — same root cause, no change in status). **Still the highest-ROI owner clicks, unactioned as of this
cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).**
25 days into the 28-day window (Day 0 = 07-13); at $0 collected, the gap math is unchanged — none of these show any
observed signal of having been actioned yet. **Only 3 days remain in the original 28-day window** — the core batch
(HQ-1′/2′, HQ-4, HQ-6, HQ-7, HQ-10, ~35 min total) is the only lever left that can still move the needle before Day
28.

## Cycle 2026-08-08 (cloud routine) — Day 26
No new items added — this cycle's ship (cross-linking all 3 `/vs/` comparison pages + index to `/eol-checker/`,
commit `d76cfb4`) was fully autonomous, in-jail, $0, no human contact needed. WebFetch outage confirmed persistent
a 25th consecutive cycle (`EGRESS_BLOCKED`, tested via the tool itself). **Still the highest-ROI owner clicks,
unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing),
HQ-4 (GitHub App).** 26 days into the 28-day window (Day 0 = 07-13); at $0 collected, the gap math is unchanged —
none of these show any observed signal of having been actioned yet. **Only 2 days remain in the original 28-day
window** — the core batch (HQ-1′/2′, HQ-4, HQ-6, HQ-7, HQ-10, ~35 min total) is the only lever left that can still
move the needle before Day 28.

## Cycle 2026-08-09 (cloud routine) — Day 27
No new items added — this cycle's ship (cross-linking all 3 kit READMEs to `/eol-checker/`, commit `f4a29e9`) was
fully autonomous, in-jail, $0, no human contact needed. WebFetch outage confirmed persistent a 26th consecutive
cycle. **Still the highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-7 (`vsce
publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).** 27 days into the 28-day window (Day 0 = 07-13); at
$0 collected, the gap math is unchanged — none of these show any observed signal of having been actioned yet.
**Only 1 day remains in the original 28-day window (Day 28 = 08-10)** — the core batch (HQ-1′/2′, HQ-4, HQ-6,
HQ-7, HQ-10, ~35 min total) is the only lever that could still move the needle before Day 28, and at this point
that is very unlikely to land in time; the loop continues past the window regardless (no natural stop condition,
per D36) since the flywheel and the Q1-2027 Lambda block wave are multi-month plays, not tied to the original
28-day boundary.

## Cycle 2026-08-10 (cloud routine) — Day 28, end of original window
No new items added — this cycle's ships (verifying a separate process's dev.to article 24, and cross-linking the
VS Code extension README to `/eol-checker/`, commit `5560eb4`) were fully autonomous, in-jail, $0, no human
contact needed. WebFetch outage confirmed persistent a 27th consecutive cycle. **Still the highest-ROI owner
clicks, unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action
listing), HQ-4 (GitHub App).** 28 days into the 28-day window (Day 0 = 07-13, Day 28 = 08-10) — **the original
window closes today.** At $0 collected, the gap math is unchanged from Day 0 — none of the core-batch items show
any observed signal of having been actioned. The core batch (HQ-1′/2′, HQ-4, HQ-6, HQ-7, HQ-10, ~35 min total
owner time) remains the only lever that can move the $4,000 gap; the agent-side autonomous levers inside the jail
(content, truth fixes, cross-linking) are now exhausted on every surface swept to date. The loop continues past
Day 28 with no natural stop condition — see DECISIONS D38.

## Cycle 2026-08-11 (cloud routine) — Day 29
No new items added — this cycle's ship (a 1-line truth fix in the committed `docs/blog/index.html` snapshot, a spot
the 2026-08-04 docs/ sweep missed) was fully autonomous, in-jail, $0, no human contact needed. WebFetch outage
confirmed persistent a 28th consecutive cycle. **Still the highest-ROI owner clicks, unactioned as of this cycle:
HQ-1′/2′ (Gumroad, ~10 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).** 29 days
since Day 0 (07-13), 1 day past the original 28-day window close (08-10); at $0 collected, the gap math is
unchanged — none of the core-batch items show any observed signal of having been actioned yet.

## Cycle 2026-08-12 (cloud routine) — Day 30
No new items added — this cycle's ship (a homepage stale-urgency truth fix: the `al2023-gate` kit card's "Jun 30,
2026" deadline badge, now 6.5 weeks past and still shown red/urgent, corrected to honest post-EOL phrasing) was
fully autonomous, in-jail, $0, no human contact needed. WebFetch outage confirmed persistent a 29th consecutive
cycle. **Still the highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-7 (`vsce
publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).** 30 days since Day 0 (07-13), 2 days past the
original 28-day window close (08-10); at $0 collected, the gap math is unchanged — none of the core-batch items
show any observed signal of having been actioned yet.

## Cycle 2026-08-13 (cloud routine) — Day 31
No new items added — this cycle's ship (a free-tool cross-link added to `launch/gumroad/LISTING-COPY.md`, closing
a 3-cycle-old open item) was fully autonomous, in-jail, $0, no human contact needed. WebFetch outage confirmed
persistent a 30th consecutive cycle. **Still the highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′
(Gumroad, ~10 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App).** 31 days since Day 0
(07-13), 3 days past the original 28-day window close (08-10); at $0 collected, the gap math is unchanged — none
of the core-batch items show any observed signal of having been actioned yet. This cycle's content/truth sweeps
found nothing new beyond the one closed item — the agent-side autonomous levers keep getting thinner; the owner
batch above remains the only thing that can move the $4,000 gap.

## Cycle 2026-08-14 (cloud routine) — Day 32
**New, elevated-priority item: HQ-5b item 0 — deactivate the `drift_watch` Stripe Price in the dashboard today
(~2 min, no VPS needed).** This cycle found the `/api/drift/checkout` backend endpoint (not just the frontend
form D14 already fixed) was still live and would open a real $19/mo subscription for a product with zero
fulfillment — closed in code this cycle (see DECISIONS D42), but the fix needs the same VPS redeploy as HQ-5b
item 2 (org_license) to take effect in production. The Stripe-dashboard deactivation is the only way to close the
live exposure before that VPS visit happens — do it first, it's faster than everything else in this queue. **Still
the highest-ROI owner clicks otherwise, unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-7 (`vsce
publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App, which also carries the org_license + drift_watch code
fixes to production on the same VPS trip).** WebFetch outage confirmed persistent a 31st consecutive cycle. 32
days since Day 0 (07-13), 4 days past the original 28-day window close (08-10); at $0 collected, the gap math is
unchanged.

## Cycle 2026-08-15 (cloud routine) — Day 33
No new items added — this cycle's ships (a stale-EOL-framing truth fix on 2 SEO landing pages, commit pending, and
an ASSETS.md internal-record correction) were fully autonomous, in-jail, $0, no human contact needed. This cycle
also traced the remaining paid/webhook endpoints for a repeat of yesterday's drift-checkout bug class — clean, no
new finding, no new queue item. WebFetch outage confirmed persistent a 32nd consecutive cycle. **Still the
highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-5b item 0 (deactivate the
`drift_watch` Stripe Price — the fastest close on yesterday's finding, ~2 min), HQ-7 (`vsce publish`), HQ-10
(GitHub Action listing), HQ-4 (GitHub App, which also carries the org_license + drift_watch code fixes to
production).** 33 days since Day 0 (07-13), 5 days past the original 28-day window close (08-10); at $0 collected,
the gap math is unchanged.

## Cycle 2026-08-16 (cloud routine) — Day 34
No new items added — this cycle's ships (a truth fix in the shared `rules/public/deprecations.yml` data field, plus
a 6-file sweep fixing the same stale-EOL-tense bug in `README.md`, `launch/DISTRIBUTION-KIT.md`,
`launch/distribution/fast-cash/README.md`, 2 dev.to article sources, and `launch/show-hn-final.md`) were fully
autonomous, in-jail, $0, no human contact needed. WebFetch outage confirmed persistent a 33rd consecutive cycle.
**Still the highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-5b item 0
(deactivate the `drift_watch` Stripe Price, ~2 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing), HQ-4
(GitHub App, which also carries the org_license + drift_watch code fixes to production).** 34 days since Day 0
(07-13), 6 days past the original 28-day window close (08-10); at $0 collected, the gap math is unchanged.

## Cycle 2026-08-17 (cloud routine) — Day 35
No new items added — this cycle's ship (fixing a self-contradictory "Live deadline" label for the already-passed
AL2 date, found in `README.md` — the repo's most-visible file, where it directly contradicted the page's own
correct "already passed" hero line — plus the same bug in `launch/social.md` and `launch/outreach.md`) was fully
autonomous, in-jail, $0, no human contact needed. WebFetch outage confirmed persistent a 34th consecutive cycle.
**Still the highest-ROI owner clicks, unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-5b item 0
(deactivate the `drift_watch` Stripe Price, ~2 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing), HQ-4
(GitHub App, which also carries the org_license + drift_watch code fixes to production).** 35 days since Day 0
(07-13), 7 days past the original 28-day window close (08-10); at $0 collected, the gap math is unchanged.

## Cycle 2026-08-18 (cloud routine) — Day 36
No new items added — this cycle's ship (a citation-integrity fix on dev.to article 25's 2 unverifiable specific
claims, found while verifying a separate process's unlogged articles 24/25) was fully autonomous, in-jail, $0, no
human contact needed. WebFetch outage confirmed persistent a 35th consecutive cycle. **Still the highest-ROI owner
clicks, unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-5b item 0 (deactivate the `drift_watch` Stripe
Price, ~2 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App, which also carries the
org_license + drift_watch code fixes to production).** 36 days since Day 0 (07-13), 8 days past the original 28-day
window close (08-10); at $0 collected, the gap math is unchanged.

## Cycle 2026-08-19 (cloud routine) — Day 37
No new items added — this cycle's ship (reframing `launch/DISTRIBUTION-KIT.md` + `launch/distribution/email/
template.md` from pre-AL2-deadline to honest post-deadline copy, see DECISIONS D47) was fully autonomous, in-jail,
$0, no human contact needed. WebFetch outage confirmed persistent a 36th consecutive cycle. **Still the highest-ROI
owner clicks, unactioned as of this cycle: HQ-1′/2′ (Gumroad, ~10 min), HQ-5b item 0 (deactivate the `drift_watch`
Stripe Price, ~2 min), HQ-7 (`vsce publish`), HQ-10 (GitHub Action listing), HQ-4 (GitHub App, which also carries
the org_license + drift_watch code fixes to production).** 37 days since Day 0 (07-13), 9 days past the original
28-day window close (08-10); at $0 collected, the gap math is unchanged — none of the core-batch items show any
observed signal of having been actioned yet.

## Running total (post-pivot)
Everything here is now **one-time setup, no ongoing owner time.** Core ≈ **30 min** (HQ-1′+2′,4,5,6). The COMPOUNDING
batch below is now the **primary growth engine** (outreach is off the table), so those publishes matter more than
before — but each is still a one-time click. **Highest-ROI now: HQ-7 (`vsce publish`) + HQ-10 (GitHub Action listing)
+ HQ-4 (GitHub App) + HQ-1′/2′ (Gumroad, now fully built)** — they turn on the discovery flywheel and the first
low-ticket SKU.
