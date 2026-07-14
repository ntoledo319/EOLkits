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

### 🟢 HQ-5 — Verify the Pack PR path once (after HQ-4)  *(Bet B · ~5 min, agent-assisted)*
- Run `sandbox_e2e.py` against a throwaway repo with the real App creds → confirm a clean, CI-passing PR opens.
  **Do not sell the $1,499 Pack until this is green** (the auto-refund guarantee must be honest, §2.5).

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
- PyPI: https://pypi.org/account/register/ → verify email → enable 2FA → create an API token →
  `python3 -m build && TWINE_USERNAME=__token__ TWINE_PASSWORD=<token> twine upload dist/*` in each Python kit.
- npm: `npm adduser` → `npm publish` in `kits/lambda-lifeline`. (Update the AL2 pyproject "before Jun 30 2026" copy
  first — it's now post-EOL; the agent will prep this.)

### ⚪ HQ-10 — List the GitHub Action on Marketplace  *(~8 min · free; peak-intent funnel)*
- The Action must live in a **dedicated public repo** (Marketplace can't list a monorepo action). Agent will prep a
  `eolkits-action` repo layout; you then: repo → "Draft a release" → check "Publish this Action to the GitHub
  Marketplace" → accept the developer agreement → pick categories → publish.

### ⚪ HQ-11 — Confirm DEVTO_API_KEY is on the box  *(~1 min · likely already done)*
- Prior handoff says the key is at `/home/ubuntu/.eolkits-dist.env`. Verify the daily cron is auto-publishing dev.to
  articles; if not, drop/rotate the key. Unblocks autonomous backlink publishing.

---

## Running total (post-pivot)
Everything here is now **one-time setup, no ongoing owner time.** Core ≈ **20 min** (HQ-1′,4,5,6). The COMPOUNDING
batch below is now the **primary growth engine** (outreach is off the table), so those publishes matter more than
before — but each is still a one-time click. **Highest-ROI now: HQ-7 (`vsce publish`) + HQ-10 (GitHub Action listing)
+ HQ-4 (GitHub App)** — they turn on the discovery flywheel that feeds every sale.
