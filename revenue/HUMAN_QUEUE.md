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

### 🟡 HQ-5b — org_license / drift_watch fulfillment gaps (§2.5) — **drift_watch self-serve checkout pulled 2026-07-16**
**UPDATE 2026-07-16:** the site-side fix is shipped (commit `2a843b9`, deploys via the daily box cron) — `/drift/`
no longer offers a live checkout, the homepage card says "coming soon," and the audit-success upsell soliciting it
is removed. **What's still open, human-only:**
1. **Deactivate the `drift_watch` Stripe Price/Payment Link** in the Stripe dashboard (or leave it — with the site no
   longer linking to `/api/drift/checkout`, the residual exposure is only someone hitting a stale/shared URL
   directly). ~2 min, optional but tidy. Link: https://dashboard.stripe.com/prices → find "Drift Watch."
2. **org_license ($14,999/yr) email-delivery gap — FIXED IN CODE 2026-07-19 (commit `edfba40`), NEEDS A VPS REDEPLOY
   TO GO LIVE.** `_store_license` in `grace-api/app.py` used to generate and store a real license key but never
   email it to the buyer; it now sends it via the existing Resend path (same as audit-PDF delivery), tested
   (38/38 green — see DECISIONS D16). **Why this is still a queue item:** `apps/grace-api` is not on the git-push
   auto-deploy path (only `apps/web`/the static site is) — this fix sits in the repo but does nothing in production
   until you next redeploy `eolkits-api` on the VPS. **Action:** next time you SSH in for any reason (e.g. HQ-4's
   GitHub App creds), redeploy `eolkits-api` too so this lands — no separate trip needed, just don't skip it.
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

## Running total (post-pivot)
Everything here is now **one-time setup, no ongoing owner time.** Core ≈ **30 min** (HQ-1′+2′,4,5,6). The COMPOUNDING
batch below is now the **primary growth engine** (outreach is off the table), so those publishes matter more than
before — but each is still a one-time click. **Highest-ROI now: HQ-7 (`vsce publish`) + HQ-10 (GitHub Action listing)
+ HQ-4 (GitHub App) + HQ-1′/2′ (Gumroad, now fully built)** — they turn on the discovery flywheel and the first
low-ticket SKU.
