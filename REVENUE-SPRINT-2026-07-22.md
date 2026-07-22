# EOLkits — 4-Week Revenue Sprint

**Owner:** Nick · **Driver:** Eve (XO) · **Started:** 2026-07-22 · **Deadline:** 2026-08-19
**Goal:** ≥ **$4,000** collected in 4 weeks. Zero budget. No paid ads. No Upwork/Fiverr. No TOS/law breaks.

---

## The one-line thesis
The product works and has *never been distributed*. Its own autopsy: "a storefront in the desert."
The entire job of this sprint is **distribution + demand generation**, not building. Building is done.

## The honest number
- Product's own sober projection: **$1.5k–$5k for all of 2026**, first dollar ~Aug.
- $4k in 4 weeks = pulling the optimistic *annual* case into a month from a $0 standing start.
- **First-ever dollars: likely.** **Full $4k: a real but hard bet** — almost certainly needs
  ≥1 migration pack ($1,499) + a handful of audits ($299). => must *manufacture qualified demand*.

## The wedge / urgency
- **Amazon Linux 2 EOL = June 30, 2026** (3 weeks ago). Orgs getting AWS emails NOW. Hottest moment.
- Lambda runtime EOL waves (Node 18/20, Python 3.9–3.11) — rolling, hard AWS block dates.
- Every finding is cited to AWS's own primary docs → credibility is the product's edge.

## Pricing (live, real Stripe rails)
- CLI + browser scanner: **$0** (MIT) — the top of funnel.
- **Audit PDF: from $299** — hash-anchored cited report, ~5 min delivery, 30-day money-back.
- **Migration Pack: $1,499** — GitHub App PR w/ codemods, IaC patches, canary + rollback.
- Drift Watch $19/mo + Org License $14,999/yr = **coming-soon / contact only** (fulfillment not real → keep gated).

---

## Strategy — a barbell

### Arm A — Launch it loud (broad, compounding, ~free labor)
Coordinated, AL2-EOL-timed push that all points at the **free scanner** (no signup):
- **Show HN** (the never-retried channel) — the flagship shot.
- **r/aws + r/devops + r/aws_cdk** — genuinely-useful posts, transparent authorship.
- **dev.to / Hashnode** — "AL2 just hit EOL — here's how to find what it breaks, free" writeup.
- **X thread + LinkedIn** — dev/devops + CTO audiences (the pack buyer reads LinkedIn).
- **AWS re:Post** — continue the started help-first answer motion.
- **GitHub discoverability** — topics, README polish, awesome-aws / awesome-list PRs, npm/pip keywords.
Free usage → funnel → % convert to $299 audits. Compounds after the spike (SEO + GitHub).

### Arm B — Fix-first targeted outreach (narrow, high-conviction)
Where the $1,499 pack most likely comes from:
- Find orgs with **provable** AWS EOL exposure from *public* data (public IaC/repos w/ AL2 AMIs or
  legacy Lambda runtimes, job posts naming legacy runtimes, etc.).
- Lead with a **real free finding** (run the scanner), give value first, offer the free tool,
  then the done-for-you migration. Demand-proof, not spray-and-pray.
- TOS-clean, non-creepy, low-volume, high-relevance. NOT the dead 231-cold-blast motion.

### Under both — funnel + trust
- Finish/deploy the billing-honesty fixes (dead SKUs gated) so nothing blows up on traffic.
- AL2-EOL urgency on the landing page; crisp free→paid path; visible sample audit.

---

## What Eve drives autonomously (no owner labor)
- All launch copy/content, drafted to one-click-ready.
- Public-data lead list + fix-first outreach drafts (real scanner findings attached).
- GitHub discoverability PRs, README, packaging/keywords, SEO pages.
- Funnel tightening (urgency, clarity, sample report), re:Post answer drafts.

## What only the owner can unlock (minimal, high-leverage)
- **Accounts to post from** (HN / Reddit / X / LinkedIn / dev.to) + green light to fire the launch.
- **Deploy** the funnel/honesty fixes (I won't push deploy without you).
- Approve/send the fix-first outreach batch (external action).

## Scoreboard (update as we go)
| Metric | Start | Now | Target (4wk) |
|---|---|---|---|
| $ collected | $0 | $0 | $4,000 |
| GitHub stars | 1 | — | — |
| Free scanner runs | ~0 | — | (traffic proxy) |
| Audits sold ($299) | 0 | — | — |
| Migration packs ($1,499) | 0 | — | ≥1 |
| Qualified leads (fix-first) | 0 | — | — |

---

## Progress log — 2026-07-22 (Eve, "do it all" pass)
**PRE-FIRE checklist: fully closed. The launch pack is fact-checked and fire-ready.**
- **Node-20 dates corrected everywhere public** — README, published blog (regenerated), site `build.py`,
  both `lambda-lifeline` docs, re:Post answer bank, and every launch draft (social/outreach/hn-replies/show-hn).
  Was "Aug 31 / Sep 30, 2026" (a year wrong); now **Feb 1 / Mar 3, 2027**, verified against AWS's live doc.
  Zero stale dates remain in any shippable file.
- **Tests badge** corrected 172 → **168** (real count, all 6 suites re-run on Linux today).
- **All funnel links verified 200**; `@v1` action ref resolves on the remote; verify page live.
- **Receipts confirmed real + clickable** — latest release carries Sigstore `.sig` + CycloneDX SBOMs;
  added that receipt back into the Show HN body as a strength.
- **Reddit pack built** (`launch/reddit.md`) — the one genuine content gap. Everything else already existed.
- **Arm B leads refreshed** (`targets.md`) with today's `gh search code` run + honest verdict.

### ⛔ Blockers — OWNER ACTION (only Nick can clear these)
1. **GitHub App is a dead link.** `github.com/apps/eolkits-migration-bot/installations/new` → **404**
   (verified). This is the URL grace-api hands *paying pack customers* and the outreach CTA. → **Set the App
   to Public** in GitHub → Settings → Developer settings → GitHub Apps (or give me the real public slug).
   Nothing that references the App should fire until this is fixed.
2. **Deploy** the corrected site/docs so the live blog/README stop showing old dates (web cron auto-rebuilds
   on push; API needs `docker compose build && up -d` on the GRACE VPS). I won't push without you.
3. **Stripe** — archive the dead org_license/drift_watch Prices + raw Payment Links (from the billing-honesty branch).
4. **Accounts** to post from (HN/Reddit/X/LinkedIn/dev.to) + green light to fire Arm A.

*Living doc. Eve updates as the sprint runs.*
