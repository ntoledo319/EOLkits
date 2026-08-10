# EOLkits — Autopsy & 14-Day Revenue Plan

_Authored 2026-06-21 through a dual lens: master systems engineer + master business consultant.
Scope: why this project has earned $0, and one master plan — executable almost entirely by
Claude Code — to make it earn money inside 14 days (Day 1 = Sun Jun 22 → Day 14 = Sat Jul 5)._

---

## 0. Verdict in one sentence

**EOLkits did not fail in the market — it never reached the market.** It is a technically
excellent, fully-built, live storefront that no human being has ever been driven to, wrapped
around a product that — even if traffic arrived — could not convert because the brand is
anonymous and the one urgent catalyst (Amazon Linux 2 EOL, **Jun 30 — 9 days away**) is about
to expire into a 7-month demand desert.

This is not a product problem. **It is a distribution problem stacked on a trust problem,
both caused by the same root: two months of building was used as a sophisticated way to avoid
the scary act of putting it in front of people and asking for money.**

---

## 1. TL;DR

**The autopsy (why $0):**
1. **The launch never happened.** The Show HN — the *only* primary distribution channel — was rejected by HN's new-account policy gate on Jun 12 and **never resubmitted**. `launch/launched.txt` still reads `status: not yet submitted`. Every other channel (X, LinkedIn, cold email, Reddit/SO/re:Post answers, the 2,500-word blog post) is a polished **draft sitting in the repo, never sent**. GitHub: **0 stars, 0 forks**. The site has **no analytics** — it is blind.
2. **Build-as-procrastination.** 1,546 commits, ~2 months, repeated "hardening" passes, pricing churned twice ($499/$999/$2,499 → $299/$1,499/$14,999), three launch-copy rewrites, and self-congratulatory `MISSION_COMPLETE.md` / `FINAL_STATE.md` files that confused *shipping code* with *making money*. Even the fix for distribution ("Marketing Machine v2") became another build project — **40% live, 60% stuck unmerged on a branch.**
3. **It wouldn't convert anyway.** Anonymous founder (no name, no face, no company — the repo's own Terms say legal entity is "to be formed"). Zero social proof, zero testimonials, zero example PRs. Asking strangers to wire **$1,499** to an unknown GitHub handle. **No email capture** for the 99% who aren't ready to buy — and the lead-capture that did exist was silently broken (dead FormSubmit).
4. **The catalyst is expiring.** AL2 EOL (Jun 30) is the *only* severity-critical, near-term deadline. After it, nothing bites until **Feb 2027**. The whole near-term urgency window is 9 days wide — and the product is in front of nobody.
5. **Wrong hero SKU + untested fulfillment.** The flagship is positioned as the $1,499 Migration Pack with an auto-refund-on-CI-failure promise that has **never been run with a single real customer** (the go-live checklist's "run one live payment" is still unchecked). High operational risk, premature for a zero-trust brand.

**The fix (what changes):**
- **Stop building features. Start shipping demand.** Pivot the business from *deadline-spike, HN-launch-dependent, high-ticket* to **evergreen AI-search demand capture → free tool → low-friction $299 wedge → lead nurture for the next wave** — a *compounding machine* Claude can build and run, instead of a one-shot launch that depends on a human's nerve.
- **Make Nicholas Toledo visible** and add the trust layer, so traffic that arrives converts.
- **Actually execute distribution** — the part that was never done — squeezing the 9-day AL2 window while standing up the evergreen engine behind it.

**Honest target (Day 14):** _First paying customer(s)_ + a fully instrumented, repeatable funnel + a real lead pipeline. **Base case $300–$3,000** (1–6 audit sales from the AL2 window + early AI-search pickup). **Stretch $5K+** if one community post hits. The bigger payoff — evergreen traffic + the Feb-2027 Lambda wave — lands in weeks 3–8, but **the money machine is built, instrumented, and running in 14 days.** Any plan promising a windfall is the same fantasy that wrote `FINAL_STATE.md`; this one refuses to.

---

## PART I — THE AUTOPSY

### Cause of death

> A storefront in the desert. Beautiful, fully stocked, lights on, card reader live — built on a
> road no one was ever sent down, and the one festival that would have brought a crowd is leaving town in 9 days.

### Finding 1 — The launch was drafted, rehearsed, and never fired

Every primary and secondary channel exists as a **finished artifact** and was **never executed**:

| Channel | Artifact in repo | Actually executed? | Evidence |
|---|---|---|---|
| Show HN (primary) | `launch/show-hn-final.md` | ❌ Rejected Jun 12 by HN new-account gate; never resubmitted | `launch/launched.txt`: `status: not yet submitted` |
| X / Twitter thread | `launch/social.md` | ❌ | 0 posts |
| LinkedIn | `launch/social.md` | ❌ | 0 posts |
| Cold email | `launch/outreach.md` (3 variants) | ❌ | 0 sends, 0 reply logs |
| SO / GitHub / AWS re:Post answers | `launch/thread-answers.md` (10 templates) | ❌ | 0 posted |
| Blog post (2,500 words) | `launch/blog-post.md` | ❌ | Not on dev.to / Medium / anywhere |
| GitHub organic | repo + README | ⚠️ exists | **0 stars, 0 forks** after 54 days |
| Web analytics | — | ❌ never built | No GA4/Plausible/PostHog on the live site |

**The single point of failure:** the entire plan routed through one Show HN submission. It hit a
policy wall, and there was no plan B. Nine days later, the drawer of finished launch materials
is still closed.

### Finding 2 — Building became the place to hide

The commit history tells a story a consultant has seen a hundred times: **the founder kept
returning to the safe, controllable, ego-protecting work (code) and kept deferring the unsafe,
uncontrollable, ego-exposing work (selling).**

- 1,546 commits in ~8 weeks; the most recent work is *still* backend hardening and SEO determinism, not a single act of distribution.
- Pricing was redesigned at least twice; the product was "finished" (`MISSION_COMPLETE.md`) months before it had a customer.
- The cure for the disease — "Marketing Machine v2" — was itself turned into a **build project** and left **unmerged on a branch**. The instinct was right; the execution recreated the same avoidance.

> Systems-dev translation: the team optimized a service to five-nines before it had one nine of
> traffic. Test coverage is 172 passing; customer coverage is 0. **You cannot harden your way to revenue.**

### Finding 3 — Even with traffic, the funnel leaks at every trust gate

If 100 visitors arrived tomorrow, near-zero would pay. Not because the tech is broken (it works
end-to-end), but because the **buyer's nervous system says "scam" before their brain reads the offer**:

- **Anonymous brand.** No founder name, no face, no company. The repo's own `legal/terms.md` defers the legal entity to "upon formation." You are asking a stranger to send **$1,499** to a handle.
- **Zero proof.** No testimonials, no case study, no example PR, no logos, no "1,000+ audits." The strongest claim ("we open a real PR, auto-refund if CI fails") reads as *too good to be true* with nothing to anchor it.
- **No value gap articulated.** Why pay $299 for a PDF when the CLI is free and MIT? The answer (5 minutes vs. 2 hours; severity scoring; a roadmap) exists in reality but is not on the page.
- **No email capture.** The ~99% not ready to buy today leave **forever** — no list, no nurture, no second touch. And the lead-capture that was wired pointed at a **dead FormSubmit endpoint**: any lead that *had* come in would have been **silently dropped.**

> **Remedy chosen (not identity):** the owner has opted for a *faceless, proof-led* fix rather than
> putting a face on it — free try-before-buy, a real case-study PR, and verifiable/cited reports.
> Anonymity is only fatal when *nothing* carries trust; here, proof carries it.

### Finding 4 — The catalyst is expiring into a 7-month desert

From `rules/public/deprecations.yml`:

| Deadline | Date | Severity | Days from today | Revenue weight |
|---|---|---|---|---|
| **Amazon Linux 2 EOL** | **2026-06-30** | **critical** | **9** | **The entire near-term window** |
| IMDSv1 enforcement | 2025-12-31 | high | *already passed* | none (and no kit exists) |
| Lambda Node 18/20, Python 3.8/3.9/3.10 | **2027-02-01** | high | ~225 | future |
| Lambda Python 3.11 | 2027-07-31 | medium | ~405 | distant |

The surge-pricing, deadline-urgency business model has **exactly one live deadline**, and it
leaves in 9 days. After Jun 30 there is **nothing urgent to sell for ~7 months.** A business whose
demand arrives in 9-day spikes separated by multi-month deserts is not a business — it's a series
of lottery tickets. **The durable demand is evergreen** (developers Google `No module named
'distutils'` every single day), and the model wasn't built around it.

### Finding 5 — Wrong hero SKU, untested high-risk fulfillment

- The **$1,499 Migration Pack** (and the fantasy **$14,999 Org License**) are positioned as the
  flagships. Both require trust the brand has not earned and a sales motion that does not exist.
- The Pack's **auto-refund-on-CI-failure** + **GitHub-App-opens-a-PR-on-your-repo** machinery is
  operationally heavy and **has never been exercised by a real paying customer** (go-live checklist
  item "run one live Stripe payment" is unchecked). First real customer = first live fire test of a
  refund-bot on someone else's production repo. That is a frightening place to discover a bug.
- The **right wedge** is the **$299 Audit PDF**: low buyer risk, fast automated fulfillment, no
  write access to the customer's repo, and a natural upsell into the Pack once trust exists.

### The joint diagnosis (both lenses agree)

| Lens | What it sees |
|---|---|
| **Master systems engineer** | A robust, well-tested, deterministic system with *zero observability at the top of the funnel* and *60% of the growth subsystem unmerged*. The pipeline is production-grade; it has never carried a single packet of real demand. |
| **Master business consultant** | A classic **first-time-founder build-trap**: world-class preparation, zero go-to-market execution, an anonymous brand, a mispriced hero offer, and a perishable catalyst being wasted. The fix is not more product — it is **traffic, trust, and a repeatable funnel.** |

---

## PART II — THE STRATEGIC REFRAME

Before the day-by-day, the business has to change shape. Three shifts:

**1. From deadline-spike to evergreen AI-search demand capture.**
The asset that matters is the `/fix/<error>` corpus (`apps/web/content/fixes.yml`) — pages keyed
to the *verbatim error strings developers paste into Google, ChatGPT, Perplexity, and Claude*.
These are searched **every day, forever**, independent of any deadline. In 2026, AI answer engines
are a primary discovery channel, and these pages — sourced, schema-marked (FAQPage/HowTo), citation-
ready — are **purpose-built to be the answer an LLM returns.** This is distribution that *compounds*
and that **Claude can manufacture at a scale and quality a human cannot match quickly.** It is the
engine; the deadlines are just the marketing calendar on top.

**2. From high-ticket-first to a low-friction wedge.**
Lead with the **$299 Audit PDF** (consider an optional **$49 instant mini-report tripwire** to buy
first-dollar trust — Claude can create the Stripe price via the Stripe MCP). Earn the right to sell
the $1,499 Pack with proof, later. Kill the $14,999 Org License from the hero entirely until there
is a logo wall.

**3. From one-shot launch to an always-on machine.**
The Show HN was a single die roll. Replace it with a **standing system**: evergreen pages that index
and accrue, a free tool that captures emails, a lead list that gets nurtured into every future
deadline wave, and `Drift Watch ($19/mo)` as the recurring revenue that survives the desert. Launch
*events* (HN, Reddit, outreach) become *fuel injected into a running engine*, not the engine itself.

---

### The Faceless Conversion System (locked 2026-06-22)

Because the brand is faceless, conversion runs on two principles: **proof precedes payment** (let
buyers verify the truth of their *own* situation for free) and **risk is removed** (an iron-clad
guarantee makes trusting the seller unnecessary). Locked decisions:

| Decision | Locked choice | Why |
|---|---|---|
| **Guarantee** | **Iron-clad, no-questions: 100% money-back, 30 days + "beat Jun 30 or it's free"** | Biggest faceless lever; abuse is negligible on a $299 deterministic digital report, and a deadline buyer wants the fix, not a refund |
| **Free reveal** | **Full findings free; pay for the cure** — `/scan` shows every finding + severity + deadline; $299 buys remediation + IaC patches + roll-forward plan + hash-anchored PDF | Proof-precedes-payment; self-servers were never buyers; converts *seen pain → paid cure* |
| **Tripwire** | **None for now** — the free scanner *is* the tripwire; one clear $299 wedge | Simplicity converts; don't fragment the offer (revisit only if data shows price resistance) |
| **Discounting** | **Never** (surge pricing *up* toward the deadline is fine) | For a faceless brand a discount signals "low value / desperate"; a guarantee signals confidence |

Supporting levers (built in Sprint 1, all identity-free): redacted **sample audit PDF**, **cost-of-
inaction** value math, **verifiability** headlines (every fact cited to its AWS source + hash-anchored
+ open rule-pack), **instant automated delivery** messaging, **works-with logos** (AWS, Terraform,
SAM, CDK, Serverless, GitHub Actions), honest **live usage counters** (from the events table), and a
**"Secure checkout · Stripe"** signal.

---

## PART III — THE 14-DAY MASTER PLAN

### The "5-minute human unlocks" (everything else is Claude Code)

This plan is engineered so Claude executes ~90% autonomously. A handful of actions legally or
practically require the owner. Each is **one action, ≤5 minutes**, and Claude does all surrounding work:

> **Trust decision (set 2026-06-21): proof-led & faceless.** No personal name, no founder page, no
> headshot. Trust is carried entirely by levers that need no identity — *try-before-you-buy* (free
> CLI + free scanner), a *real case-study PR + sample audit*, and *verifiability* (every audit fact
> cited to a primary source; reports hash-anchored). This **removes the old "U1 — use your name"
> unlock**; Claude builds the proof stack with no human action required.

| # | Unlock | Why a human | Claude does everything else |
|---|---|---|---|
| U2 | **One deploy mechanism to the GRACE box** — either run one `git pull && build && rsync` cron setup once, or run the rsync when Claude says "batch ready" | SSH key lives on your machine | Builds everything, batches changes, hands you the exact command; controls the GitHub Pages mirror fully via `git push` |
| U3 | **Click "post"** on the HN / Reddit / X / LinkedIn drafts from your accounts (or authorize the Gmail MCP for outreach sends) | Account ownership / anti-spam | Writes every post + reply, schedules, builds the target list, drafts every personalized email |
| U4 | **(Optional) A real notification inbox** for leads (e.g., your email) in `.env.production` `LEAD_NOTIFY_TO` | It's your inbox | Wires capture → store → notify → retry |

Everything below that is **not** tagged `[U#]` is pure Claude Code execution.

---

### SPRINT 0 — SEE & SHIP (Days 1–2)
_You cannot fix a funnel you can't see, and you can't sell a machine that's stuck on a branch._

**Day 1 — Sun Jun 22 · Instrument the funnel + open the deploy lane**
- [ ] **Make the funnel visible (first-party, no third-party account).** The backend already has an
      events table + `/api/events` + `/status` funnel counts. Claude: ensure **every** page fires
      pageview + CTA-click + checkout-start beacons; add a simple `/status` ops view that reads
      `funnel_7d`. Acceptance: a manual click-through registers events end-to-end.
- [ ] **Establish a deploy lane Claude can drive.** [U2] Set up pull-based deploy on GRACE (one-time)
      **or** agree a "batch-ready → owner runs one rsync" cadence. Confirm `deploy-pages.yml`
      (`workflow_dispatch`) as the always-available GitHub Pages mirror Claude controls via `git push`.
      Acceptance: a trivial content change reaches the live site through the agreed lane.
- [ ] **Snapshot today's zero** for honest before/after: stars, leads, funnel counts, revenue = 0.

**Day 2 — Mon Jun 23 · Ship the 60% that's stuck on the branch**
- [ ] **Review, fix, and merge `marketing-machine-v2` → `main`.** This single act ships `/fix` (8
      pages), `/scan` (free browser tool), `feed.xml`, badges, first-touch attribution, and the
      repaired `/api/v1/lead` capture. Run the full test suite first (172 passing).
- [ ] **Wire lead capture for real.** [U4] Point `LEAD_NOTIFY_TO` at a live inbox; confirm the
      hourly retry sweep is running; add the email-capture form to the site (it has a working
      endpoint and *no form pointing at it*). Acceptance: a test submission lands in the inbox + DB.
- [ ] **Deploy everything live** via the Day-1 lane. Acceptance: `https://eolkits.com/fix/`,
      `/scan/`, `/feed.xml` all return **200** (today they are **404**).

> End of Sprint 0: the machine is live and you can finally *see* what visitors do.

---

### SPRINT 1 — TRUST (Days 3–4)
_So the traffic Sprint 3 brings doesn't bounce at the "is this a scam?" gate._

**Day 3 — Tue Jun 24 · Build the faceless proof stack**
- [ ] **Make "don't trust me — run it yourself" the hero.** Surface the free MIT CLI + free `/scan`
      browser tool front-and-center as the primary trust signal: a dev who watches the free scanner
      correctly flag their *own* AL2 usage now believes the paid audit. This replaces founder identity.
- [ ] **Make verifiability the reputation substitute.** Headline the audit's "every fact cited to its
      AWS primary source + hash-anchored, verifiable report" — you don't have to trust the seller, you
      can check every claim and verify the hash. (For a faceless brand, verifiability *is* reputation.)
- [ ] **Manufacture real proof.** Claude performs an **actual migration on a public repo it controls**
      (or a realistic fixture repo), opens a **real PR** with the kit, screenshots the PR + green CI +
      rollback plan → publish as a **case study** and a **redacted sample Audit PDF** ("see exactly
      what you get"). This converts "vaporware?" into "oh, it's real."
- [ ] **Add a money-back guarantee badge** + a plain-English **refund-mechanism FAQ** on `/pack`
      (turn the too-good-to-be-true auto-refund into a *trust asset* by explaining how it works).

**Day 4 — Wed Jun 25 · Fix the conversion copy**
- [ ] **Homepage value-gap section + comparison table** (DIY CLI vs Audit vs Pack: time, risk, cost).
- [ ] **Reframe the hero SKU** to the **$299 Audit** wedge; demote Org License from the hero. Add the
      **iron-clad guarantee** badge + **sample audit PDF** + **cost-of-inaction** math + **verifiability**
      headlines + **works-with logos** near every CTA (see *The Faceless Conversion System* above).
      No tripwire, no discounts.
- [ ] **Reduce form friction:** add a "view a sample before you upload" peek on `/audit`; reorder
      fields; add objection-handling FAQ + an exit-intent email capture on commerce pages.
- [ ] Acceptance: a cold reader of the home + `/audit` + `/pack` pages can answer "why trust this
      (proof + guarantee), why pay vs. the free CLI, and what's my risk (none — guaranteed)" — all on-page.

> End of Sprint 1: the brand is a person, the product has proof, the offer is legible and low-risk.

---

### SPRINT 2 — SCALE THE EVERGREEN ENGINE (Days 5–8)
_The compounding asset. This is the highest-leverage thing Claude can do that a human cannot do fast._

**Days 5–6 — Thu Jun 26 / Fri Jun 27 · 8 → 60+ sourced `/fix` pages**
- [ ] Expand `apps/web/content/fixes.yml` from 8 → **60+ entries**, each a **real, sourced** error
      string developers actually paste (e.g. `No module named 'distutils'`, `amazon-linux-extras:
      command not found`, `yum: command not found`, `aws-sdk is not defined`, `ntpd: command not
      found`, OpenSSL-3 hash errors, native-wheel `cp312` failures, `imp module removed`, etc.).
      **Integrity rule (from the file's own header):** every error string must be genuine and
      every fix cited to a primary source — no fabricated strings, no scaled-content abuse. Quality
      is the moat; spam gets de-indexed and torches the brand.
- [ ] Regenerate via `apps/web/build.py`; verify determinism + valid JSON-LD on every page.
- [ ] **Optimize for AI-citation:** crisp question-as-H1, a direct answer in the first 60 words,
      FAQPage/HowTo schema, a sources block, and a cross-link to the relevant `/migrate` deadline +
      the kit that automates it. Update `llms.txt` to surface the full corpus.

**Days 7–8 — Sat Jun 28 / Sun Jun 29 · Complete coverage + force indexing**
- [ ] Fill `/migrate` coverage for every tracked runtime; build/refresh `/vs` competitor pages
      (HeroDevs, CloudQuery, "DIY") — these capture high-intent comparison searches.
- [ ] **Make the free `/scan` tool a lead magnet:** show partial results free, **email-gate the full
      report**, then upsell to the $299 audit. Every scan = a captured lead.
- [ ] **Force discovery:** submit sitemap to Google Search Console + Bing; ping **IndexNow** for
      instant crawl; verify the AI-search surfaces. Acceptance: 60+ `/fix` + full `/migrate` + `/vs`
      live and submitted; `/scan` capturing emails.

> End of Sprint 2: a compounding, machine-built demand surface aimed squarely at evergreen +
> AI-search traffic — the engine that makes month 2+ inevitable.

---

### SPRINT 3 — ACTUALLY DISTRIBUTE (Days 6–12, overlapping)
_The thing that was never done. Fuel injected into the now-running engine — and the only way to
catch the AL2 window before Jun 30, since fresh SEO won't index fast enough on its own._

- [ ] **AL2-window blitz (must land before Jun 30).** Claude drafts; owner clicks post [U3]:
      - **HN Show HN relaunch** — the account has aged past the Jun 12 new-account gate; if still
        gated, post as a regular link + a Reddit-first strategy.
      - **Reddit** `r/aws`, `r/devops`, `r/aws` deadline threads; **lobste.rs**; **dev.to** (cross-post
        the existing 2,500-word blog — it's written, just unpublished).
      - **X + LinkedIn** from `launch/social.md` (written, never posted).
- [ ] **Precision cold outreach.** Claude uses **GitHub code search** to find *public* repos still
      referencing AL2 AMIs / `nodejs18.x` / `python3.9` in their IaC, and drafts **hyper-personalized**
      messages citing the *specific* finding (not a blast). Send via owner inbox or the Gmail MCP [U3].
      Respect the repo's own anti-spam rule: one touch per maintainer, something true and specific.
- [ ] **Answer real questions** on StackOverflow / AWS re:Post / GitHub issues that match the
      `/fix` corpus — link the free fix page (value first), kit mention second. Max 3/day, no spam.
- [ ] **Directory + newsletter seeding:** AlternativeTo (vs HeroDevs), relevant AWS/DevOps
      newsletters, awesome-lists.
- [ ] Acceptance: ≥1 community post with real engagement; ≥25 personalized outreach touches sent;
      first non-zero traffic and first leads visible in the Day-1 funnel view.

---

### SPRINT 4 — DEADLINE BLITZ, NURTURE & DOUBLE-DOWN (Days 9–14)

**Day 9 — Tue Jun 30 · The AL2 EOL deadline (exploit it, then survive it)**
- [ ] Maximize urgency while it's live: countdown, surge pricing correct, AL2 `/migrate` + `/fix`
      pages front-and-center across every channel.
- [ ] **Pre-stage the post-deadline pivot:** the moment Jun 30 passes, pain *increases* (orgs now
      running **unpatched** AL2 in prod). Flip the copy from "beat the deadline" to **"still on AL2?
      you're now unpatched — here's the cleanup path."** Claude has this ready to deploy at 00:01.

**Days 10–12 — Jul 1–3 · Capture the recurring + nurture the list**
- [ ] **Email nurture sequence** for every captured lead: immediate AL2/cleanup value now, and a
      tee-up for the **Feb-2027 Lambda wave** (this is where the list pays off big later).
- [ ] **Push `Drift Watch ($19/mo)`** as the recurring revenue that survives the desert — the
      subscription that turns one-time deadline panic into a standing relationship.

**Days 13–14 — Jul 4–5 · Measure, kill, double down**
- [ ] Read the funnel: which channel produced the first dollar / the most leads / the best
      conversion? **Cut what didn't work, pour the remaining time into what did.**
- [ ] Write a real, numbers-based retro (revenue, leads, traffic by source, conversion at each step)
      — replacing the fantasy `FINAL_STATE.md` math with ground truth — and set the 30-day plan.

---

## PART IV — TARGETS & METRICS

**Instrument first (Day 1), then these become real instead of imagined:**

| Checkpoint | Metric | Base target | Stretch |
|---|---|---|---|
| Day 2 | Funnel observable; machine live (`/fix`,`/scan`,`/feed` = 200) | done | — |
| Day 4 | Brand de-anonymized; proof + guarantee live | done | — |
| Day 8 | Evergreen pages live & submitted | 60+ `/fix` + `/scan` capturing | 100+ |
| Day 12 | Distribution executed | ≥1 post w/ traction; ≥25 outreach; first leads | front-page / viral |
| **Day 14** | **Revenue** | **$300–$3,000 (1–6 audits)** | **$5,000+** |
| Day 14 | Leads captured | **50+** | 200+ |
| Day 14 | Recurring | ≥1 Drift Watch sub | 5+ |

**North-star reframe:** the 14-day win is **two things at once** — (1) the immediate AL2 cash
attempt, and (2) a **built, instrumented, compounding machine + a nurtured list** that makes the
Feb-2027 wave a layup. Judge success on *both*, not on a single windfall number.

---

## PART V — RISKS & HONEST CAVEATS

- **SEO indexing lag is real.** Fresh `/fix` pages mostly pay off in **weeks 3–8**, not in 14 days.
  The 14-day cash therefore comes mainly from **direct distribution into the AL2 window + early
  AI-search pickup**, not from organic Google. The plan builds the long-term engine *and* makes the
  short-term sales; it does **not** manufacture a windfall. Beware repeating the `$25K-in-7-days`
  fantasy.
- **The human unlocks are load-bearing.** If the owner never clicks "post" (U3) or never opens the
  deploy lane (U2), the machine stays in the garage — exactly the failure that caused $0. The whole
  point is to make distribution *happen*, not to draft it again.
- **Content integrity is the moat.** Scaling `/fix` only works if every error string is genuine and
  every fix is sourced. Fabricated/spun pages get de-indexed and burn the brand — the opposite of
  the goal. Quality > quantity.
- **First real fulfillment is untested.** Before promoting the $1,499 Pack hard, run **one** live
  end-to-end payment + PR + (deliberate) CI-fail to prove the refund bot. Lead with the **$299 Audit**
  wedge precisely to avoid betting the launch on the heaviest, least-tested path.
- **Don't relapse into building.** If a day's work drifts back into "one more hardening pass," that
  is the disease, not the cure. The rule for 14 days: **if it doesn't put the product in front of a
  human or help that human trust/buy, it waits.**

---

## APPENDIX — Master checklist (copy into your tracker)

**Sprint 0 — See & Ship**
- [ ] D1: First-party funnel beacons on every page + `/status` view
- [ ] D1: [U2] Deploy lane established (pull-deploy or batch-rsync) + Pages `workflow_dispatch` confirmed
- [ ] D1: Snapshot the zero (stars/leads/funnel/revenue)
- [ ] D2: Merge `marketing-machine-v2` → `main` (tests green)
- [ ] D2: [U4] Lead capture wired (inbox + form + retry sweep verified)
- [ ] D2: Deploy live — `/fix`, `/scan`, `/feed.xml` return 200

**Sprint 1 — Trust**
- [ ] D3: Free-tool-forward hero + verifiability as trust (proof-led, faceless — no identity)
- [ ] D3: Real PR case study + redacted sample Audit PDF
- [ ] D3: Money-back badge + refund-mechanism FAQ on `/pack`
- [ ] D4: Homepage value-gap + comparison table
- [ ] D4: Reframe to $299 wedge; demote Org License; [optional] $49 tripwire via Stripe MCP
- [ ] D4: Form-friction fixes + exit-intent email capture

**Sprint 2 — Evergreen engine**
- [ ] D5–6: `fixes.yml` 8 → 60+ sourced entries; regenerate; AI-citation optimized
- [ ] D7–8: `/migrate` + `/vs` complete; `/scan` email-gated lead magnet
- [ ] D7–8: Sitemap → GSC + Bing + IndexNow

**Sprint 3 — Distribute**
- [ ] [U3] HN/Reddit/lobste.rs/dev.to/X/LinkedIn posts (before Jun 30)
- [ ] [U3] 25+ precision cold-outreach touches (GitHub code search targets)
- [ ] SO / re:Post / GH issue answers (value-first, ≤3/day)
- [ ] Directory + newsletter seeding

**Sprint 4 — Blitz, nurture, double-down**
- [ ] D9: AL2 urgency max; post-deadline "unpatched" pivot pre-staged
- [ ] D10–12: Email nurture sequence live; Drift Watch pushed
- [ ] D13–14: Funnel read; cut losers; numbers-based retro + 30-day plan

---

_This document supersedes the "mission complete" narrative. The mission was never complete —
it was never started, in the one dimension that makes money: getting the product in front of
humans and helping them trust it enough to pay. The next 14 days fix exactly that._
