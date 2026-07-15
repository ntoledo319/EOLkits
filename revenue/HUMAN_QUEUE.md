# HUMAN_QUEUE — batched owner actions (§10)

Every item: **what / why human-only / click-by-click / link / minutes.** The agent cannot legally or
technically do these (KYC, marketplace publish, VPS SSH, sending messages). **Do the CORE BATCH first** —
it is the only thing standing between "$0" and real revenue. Running total kept lean (§3: ≤60 min for the run).

Legend: 🔴 KYC-latency (start first) · 🟢 minutes of clicking · ⚪ optional/compounding.

---

## ⛔ REMOVED 2026-07-14 (owner constraint — DECISIONS D7)
- ~~HQ-1 Upwork account~~, ~~HQ-2 publish Upwork/Fiverr gig~~, ~~HQ-3 send proposals~~ — owner won't do Upwork
  (ongoing personal time) or Fiverr (KYC won't clear). No outreach path. See `OPPORTUNITIES.md`.

## CORE BATCH — one-time setups, then autonomous forever (fits the "no ongoing time" constraint)

### 🟢 HQ-1′ — Create a Gumroad account for the digital bundle  *(Bet A′ · ~5 min, one-time)*
- **Why human-only:** account + payout/KYC (Merchant of Record). **Watch:** Fiverr wouldn't verify you — if Gumroad
  also rejects KYC, we sell the bundle via the existing eolkits.com Stripe rail instead (no new account).
- **Steps:** https://gumroad.com → sign up → add payout method. Then the agent builds the bundle zip + listing copy;
  you click publish (HQ-2′, next cycle). **~5 min.**

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

### 🔴 HQ-5b — org_license / drift_watch are purchasable but deliver NOTHING (§2.5)  *(~5 min decision)*
`org_license` ($14,999) and `drift_watch` ($19/mo) fulfillment is **stubbed** (returns a status string, does no work).
They are live on the pricing page. **Either implement them or remove them from the pricing page** — do not let anyone
buy a SKU that delivers nothing. (Not urgent while traffic ≈ 0, but a truth/do-no-harm blocker before any real push.)

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

## Running total (post-pivot)
Everything here is now **one-time setup, no ongoing owner time.** Core ≈ **20 min** (HQ-1′,4,5,6). The COMPOUNDING
batch below is now the **primary growth engine** (outreach is off the table), so those publishes matter more than
before — but each is still a one-time click. **Highest-ROI now: HQ-7 (`vsce publish`) + HQ-10 (GitHub Action listing)
+ HQ-4 (GitHub App)** — they turn on the discovery flywheel that feeds every sale.
