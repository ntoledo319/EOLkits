# DECISIONS — pivots and reasoning (§8)

## 2026-07-13 · Cycle 0

### D0 — Jail resolved; state files created inside WORKSPACE_ROOT
WORKSPACE_ROOT = `/Users/nicholastoledo/Development/active/Rupture`. The system scratchpad (`/private/tmp/...`) and
the auto-memory dir (`~/.claude/...`) are **outside** the jail (§1.2/§1.7) → all state lives in `revenue/`, temp in
`WORKSPACE_ROOT/tmp/`. Did **not** read the workflow's output file under `/private/tmp/`; instead re-ran the workflow
with a compact `return` to bring the full synthesis back in-jail (§1.7 "redesign it inside the jail").

### D1 — Ship channel = `git push`, not SSH
The agent cannot SSH to the GRACE VPS (key in `$HOME/.grace-keys/`, outside jail). But the box auto-deploys
`marketing-machine-v2` daily, so `git push` is a legal, in-jail ship channel (§1.6 "remote is open").

### D2 — Portfolio: Upwork gig (A) + Migration Pack (B) + marketplace flywheel (C)
Chose the 3 bets in PLAN.md over "just run more SEO." Reasoning: §5 ranking law puts built-in-distribution +
built-in-payments frames first. Upwork/Fiverr is the *only* channel with built-in **demand** (not just payment) →
fastest confirmed path to a real dollar. The $1,499 Pack is the only frame where a handful of closes reaches $4k.
VS Code/Open VSX/registries are compounding, not in-window. Owned-audience organic (the prior sole focus) is
correctly demoted (§5: disqualified unless the audience exists — it doesn't).

### D3 — VERIFICATION SAVE: did NOT "fix" `deprecations.yml`; fixed `lambda-lifeline` instead
The Cycle-0 synthesis (and popular blogs: HeroDevs, CloudQuery) claimed AWS blocks nodejs20.x on **Aug 31 / Sep 30
2026** and flagged the site's data as stale. **Verified at the source (AWS Lambda runtime deprecation table):** those
blogs cite the *superseded* 30/60-day schedule. AWS **delayed** the blocks "in response to customer feedback" to a
synchronized **Q1-2027 cluster: block-create Feb 1 2027, block-update Mar 3 2027** (nodejs16/18/20, python3.8/3.9/3.10,
ruby3.2, dotnet6). Therefore:
- `rules/public/deprecations.yml` was **correct** → left unchanged. (Prevented shipping a wrong date to a live
  commerce site whose audience are AWS engineers who know the schedule.)
- `kits/lambda-lifeline` was **wrong** (Sep 30 2026 in `src/scan`, banner, README, and a brittle test) → corrected to
  Feb 1 / Mar 3 2027. This *overstated* urgency by ~5 months = a §2.5 truth violation. Tests now 24/24.
- **Lesson (logged for future cycles):** trust the AWS docs table over blogs *and* over a plausible-sounding synthesis;
  §8 verify-before-ship is load-bearing.

### D4 — Truth fixes shipped this cycle (§2.5 pre-publish, §9)
1. `lambda-lifeline`: dates → AWS-authoritative Feb 1 / Mar 3 2027; brittle `>100`-day test → finite-number check (24/24).
2. `apps/vscode-extension/src/scanner.ts`: wrong Python EOL dates (`2026-10-31/2027-04-30/2027-10-31`) → AWS Lambda
   deprecation dates (`2025-12-15 / 2026-10-31 / 2027-06-30`); Node20 message now names the real 2027-03-03 block.
3. Made the VS Code extension marketplace-ready (icon, README, metadata) so Bet C's only remaining step is the owner's
   `vsce publish`.

### D5 — Deferred (not done this cycle, with reasons)
- **Did not mass-edit** other `deprecations.yml` runtimes — all cross-checked correct against the AWS table.
- **Did not publish** anything to a marketplace/registry — all first-publish steps are KYC/account-gated (HUMAN_QUEUE).
- **Did not build** the Gumroad/Lemon Squeezy bundle or the "Node 20 deadline everyone gets wrong" dev.to article yet —
  queued as the next cycle's ships to keep Cycle 0 focused on audit + truth-integrity + state.
- **AL2 post-EOL reframe** (pyproject/copy still say "before Jun 30 2026") — flagged for next cycle; the live site
  already renders past-deadline framing dynamically (verified via `test_surge.py`), so it is not a live falsehood today.

### D7 — PIVOT (2026-07-14): Bet A (Upwork/Fiverr) is DEAD — owner constraint
Owner answered the Bet-A distribution question: **no Upwork** ("we don't do platforms I have to spend my own time
on") and **no Fiverr** ("they won't verify me to get an account"). Saved as a cross-project preference (global
`~/.claude/CLAUDE.md` + project memory `owner-distribution-constraints`). Consequences:
- **Bet A removed.** There is no owner-driven outreach and no "fast gig" shortcut. The fastest-dollar lever is gone.
- **The compounding flywheel (Bet C) becomes the PRIMARY engine** — it is the only distribution the owner tolerates:
  one-time publishes (VS Code/Open VSX/PyPI/npm/GitHub Action) + fully-autonomous content (dev.to/SEO). It feeds the
  $299 audit and the $1,499 Pack (Bet B) via *discovery*, not outreach.
- **New fast-first-dollar candidate:** a **Gumroad digital-product bundle** ("AWS Runtime EOL Migration Toolkit" =
  packaging + playbook + templates around the free CLIs) — one-time setup, built-in payments, no per-job time.
  Caveat: Gumroad/Lemon Squeezy do their own KYC; the owner's Fiverr verification failure means this may also reject
  them — flag, don't assume. Gumroad's onboarding is the lightest; try it first.
- **Honest timeline shifts out:** with zero owner outreach + a cold start, **$4,000 by Day 28 is now very unlikely.**
  The flywheel compounds over **months**, not weeks; the real inflection is the correctly-dated **Q1-2027 Lambda block
  wave (Feb 1 / Mar 3 2027)**. Realistic collected-by-Day-28 ≈ $0–600 unless a marketplace publish goes live fast and
  a cold-discovery audit lands. Recorded honestly per §8 gap law rather than riding an impossible plan.

### D8 — Continued cycle (2026-07-14): scheduled loop + authority content ship
- **Stood up the recurring engine:** cloud routine `eolkits-revenue-loop` (`trig_012izHpubRLjE946gBC1BzeN`), daily 06:00
  UTC (2 AM ET), runs the AGENTS.md cycle on `marketing-machine-v2` (headless; no VPS/local access; sonnet-5). This is
  a *remote/managed* Claude Code routine, not local OS cron — jail-compliant (§1.6).
- **Shipped an authority article** (`launch/distribution/devto/07-nodejs20-lambda-real-deadline.md`): corrects the
  widespread "Node 20 blocks Sep 30 2026" myth (the superseded 30/60-day math) with the AWS-verified real dates
  (Feb 1 / Mar 3 2027) + the Q1-2027 cluster. Canonical → the live `/migrate/lambda-node.js-20-phase-1/` page (verified
  live, showing the correct dates). Auto-publishes via the box cron = a real backlink + authority for the now-primary
  flywheel. Distinct from article 02 (which is the how-to-migrate piece), so no thin/duplicate SEO risk.
- **Closed the last flagged §2.5 truth item:** reframed `al2023-gate` README + pyproject from now-false future-deadline
  copy ("before Jun 30 2026", "63 days out", "support ends") to post-EOL reality (AL2 support **ended** 2026-06-30; now
  unpatched) — truthful and a stronger hook. 48/48 tests still green.
- **De-risked the flywheel publishes (HQ-9):** verified (jail-local venv) that all 3 registry names are free
  (al2023-gate/python-pivot on PyPI, lambda-lifeline on npm), both Python wheels build + pass `twine check` + install
  clean into a fresh venv + run their console scripts, and lambda-lifeline `npm pack`s cleanly. Wrote
  `launch/PUBLISH-CHECKLIST.md` — verified copy-paste commands for every one-time publish (PyPI/npm/VS Code/Open VSX)
  so the owner's flywheel activation is friction-minimal and guaranteed to work. GitHub Action still needs a dedicated
  public repo (scaffold = next cycle).

### D6 — Honest gate posture
$4,000 by Day 28 from $0/$0 is **owner-labor-gated, not agent-gated.** The agent will keep shipping in-jail
improvements (packages, content, truth), but the needle moves only when the owner burns down the CORE BATCH in
HUMAN_QUEUE — above all **HQ-1 (Upwork) + "Upwork yes."** This is recorded honestly rather than papered over with
optimistic projections.
