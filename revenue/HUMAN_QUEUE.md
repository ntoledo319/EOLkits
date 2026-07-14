# HUMAN_QUEUE — batched owner actions (§10)

Every item: **what / why human-only / click-by-click / link / minutes.** The agent cannot legally or
technically do these (KYC, marketplace publish, VPS SSH, sending messages). **Do the CORE BATCH first** —
it is the only thing standing between "$0" and real revenue. Running total kept lean (§3: ≤60 min for the run).

Legend: 🔴 KYC-latency (start first) · 🟢 minutes of clicking · ⚪ optional/compounding.

---

## CORE BATCH — unlocks the $4k paths (~30 min active)

### 🔴 HQ-1 — Create + ID-verify an Upwork seller account  *(Bet A · ~10 min + verification wait)*
- **Why human-only:** identity/KYC verification; the agent may not create accounts or transact.
- **Steps:** 1) https://www.upwork.com/signup/ → "I'm a freelancer." 2) Fill profile (title: "AWS Lambda / Amazon
  Linux runtime EOL migration — automated, guaranteed"). 3) Complete ID verification. 4) Add a payout method.
- **Then tell the agent "Upwork yes"** → it re-runs the live demand search and drafts one tailored proposal per
  matching job (you paste + send — HQ-3).
- **Link:** https://www.upwork.com/signup/ · **~10 min** (+ async verification).

### 🟢 HQ-2 — Publish the fixed-scope gig  *(Bet A · ~5 min)*
- **Why human-only:** listing goes live under your identity.
- **Steps:** Upwork "Project Catalog" (or Fiverr Gig) → title/description/pricing the agent drafts in
  `launch/distribution/fast-cash/`. Price **$499**, scope = one runtime family (Node **or** Python **or** AL2).
- **~5 min** (after the agent hands you the copy).

### 🔴 HQ-4 — Register the GitHub App + put creds on the GRACE box  *(Bet B · ~10 min)*
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

## Running total
Core batch ≈ **30 min active** (HQ-1,2,4,5,6). Optional batch ≈ 33 min if all done. Keep the whole run ≤60 min by
doing the core batch now and the compounding batch opportunistically. **The single highest-ROI action is HQ-1 (Upwork)
+ telling the agent "Upwork yes."**
