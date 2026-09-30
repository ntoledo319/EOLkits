# Ideology

"Ideology" here means the project's governing worldview: its theory of the problem, its theory of change, whom it meant to serve, what it valued and refused, what it feared, and how those beliefs moved. Nothing in this chapter is a slogan copied from a README; every principle listed was defended — or visibly failed — in code, configuration, process or copy, and each is versioned in [`.project-history/doctrine/principles.yml`](../../.project-history/doctrine/principles.yml) with `supersedes` links so that drift cannot be laundered into timeless doctrine.

## The theory of the problem

The founding theory (2026-04-28) was that **a platform deadline is a market**: AWS announces an end-of-support date; teams that ignore it face broken production; the days before the date create "panic buyers" with budget authority and no integrated tool (CLM-E1-005). The product's name was the event itself — a "rupture" — and its price rose as the date approached (CLM-E1-018, CLM-E1-061). This theory was restated for a second date in May (CLM-E2-001) and disowned on 2026-06-21: "demand arrives in 9-day spikes separated by multi-month deserts" (CLM-E2-063).

The second theory (June–July 2026) was that **the product worked and distribution was the whole problem**: "The bottleneck is DISTRIBUTION, not the product" (CLM-E3-010). Under this theory the loop published content and drafted answers while the paid path went untested.

The third theory (2026-08-22 onward) was that **the problem was truth**: the site "still advertised unavailable products and unsafe claims", and "only one paid deliverable can be made truthful and bounded today" (CLM-E4A-014, CLM-E4A-015). Under this theory nothing is sold that cannot be proven, and demand is a hypothesis to be falsified, not assumed. The historian notes the sequence is itself the project's education: market → channel → self.

## The theory of change

How the project believed value would arrive changed less than what it believed the problem was. Throughout, the mechanism was **autonomous, zero-budget, self-serve commerce operated by agents**: a webhook business in April (CLM-E1-017), a "compounding flywheel" of marketplace listings and search content in July (CLM-E3-008), an evidence-gated single product in August. The owner's role was always the last click. The recurring failure of the theory was that the last click was never taken; the project's response was not to change the theory but to shrink the click — from a fifteen-item handoff to a queue timed in minutes (P-02 → P-02.2).

## Intended beneficiaries over time

| Era | Who it was for (as stated) | What they were offered |
|---|---|---|
| April | "Panic buyers": senior engineers facing an imminent AWS deadline | per-kit support tiers, then five self-serve SKUs |
| May–June | Teams on Amazon Linux 2 with weeks to go; HN readers | deadline-priced audits; a bot-opened migration PR |
| June (autopsy) | A visitor who gets full findings free and then pays for the audit | a faceless, proof-led funnel |
| July | Engineers asking questions on re:Post; dev.to readers; $79 bundle buyers | drafted answers; articles; a bundle never listed |
| August–September | Users of the free scanners; one buyer of a bounded $299 report | corrected scanners; an evidence report behind a closed gate |
| Throughout, unstated | The owner's portfolio (a shared lead bus, a shared Stripe account, a shared host) | infrastructure |

No buyer was ever interviewed, as far as the evidence shows; the beneficiary was always inferred from the deadline and then from the search query. The most durable intended beneficiary turned out to be the stranger the project refused to harm: the one who must not be charged for nothing, whose code must not be modified without `--apply`, whose browser must not load a script the policy denies.

## Principles, in lineage

The lineage below is abridged from the doctrine file; ids are stable.

**Kept from the first day and never breached.** P-01 (zero seed money) and P-06 (safe by default for the stranger's infrastructure: dry-run, opt-in bot, no telemetry, minimal retention). Every hosting choice, every cut channel and every hardening pass extended these.

**Declared early, verified late.** P-03 ("if a rule cannot cite a public source, it does not ship", 2026-04-29) was not checked against AWS until 2026-07-13 and became P-03.2 (AWS source only; two-source bar; parity test) only in September. P-07 (no fabricated copy, 2026-04-29) was strained within days, became P-07.2 ("truth only", 2026-07-13) as a nightly discipline, and P-07.3 ("truthful by construction", 2026-08-22) as a catalogue cut to what the rule could cover.

**Installed as intent, corrected by evidence.** P-05 ("every trust signal terminates in a verifiable hash", 2026-04-29) produced placeholder jobs and a benchmark that counted empty output as clean; it was replaced by P-05.2 ("tests and commits are release evidence, not market signal", 2026-08-22). P-16 (fail closed on configuration, 2026-06-08) trusted its own success signals and became P-16.2 (fail closed before money: checkout off, mutation-free preflight, a seven-step gate) in August.

**Born in the July operating document and held since.** P-08 (do no harm; never fake-fulfil), P-09 (no autonomous contact with real humans; drafts only), P-10 (the jail outranks the mission), P-11 (dollars > signups > visits > stars; only observed numbers), P-02.2 (owner labour as a budget). Of these, P-09 was weakened once — by a publisher that treated own-content posting as not contact (CON-013) — and restored; P-10 was enforced on 2026-09-04 at the cost of three working cycles.

**Born of the market question.** P-12 (deadline-tiered, never discount-tiered, displayed price equals charged price) became P-12.2 (one artifact, one price, one gate; free tools are distribution, not SKUs) on 2026-08-22. P-13 (faceless and proof-led, 2026-06-22) held; naming a business entity in September is compatible with it. P-17 (open core) was reinforced from outside by the June board's verdict that only the free CLI survives.

**The one strengthened rather than weakened.** P-18 (public content is deterministic and sourced; no LLM prose; byte-identical rebuilds) was introduced on 2026-05-31, enforced against its own author on 2026-06-22 when a candidate page was dropped as not real, and tightened on 2026-09-04 when daily date bumps were reversed as false publication churn.

**Added by governance.** P-15 (preserve history: no force pushes; retire rather than rewrite; one-use authorisations are one-use), first practised on 2026-08-22 and corroborated by GitHub's activity log, which shows no force push by any non-dependabot actor ever. P-14 (this history system) is its documentary form.

## Non-goals and the negative space

The project was more consistent about what it refused than about what it achieved. The refusals, with their provenance:

- **No paid acquisition.** Cut in the April runbook (CLM-E1-020); a $1,500 ads plan prepared in June was never activated; "$0 budget. Free tiers only" in July.
- **No cold outreach, no spam, no vote rings.** Forbidden "per user directive" on day one (CLM-E1-011), breached in May's launch kit and June's five cold emails (CLM-E1-058, CLM-EXT-009), then hardened into "no autonomous contact with real humans" (CLM-E3-004). Reddit "policy-dead"; HN never gamed after two policy rejections.
- **No freelance platforms.** Upwork and Fiverr ruled out by the owner on 2026-07-14 as a cross-project preference (CLM-E3-008), re-rejected with Contra in September (CLM-E4B-064).
- **No fake fulfilment, no fake metrics, no fabricated testimonials or capabilities.** The truth rule's explicit list (CLM-E3-004); the status page's constants were the last fake metric, removed 2026-08-22 (CLM-E4A-059).
- **No telemetry; no storage of buyer code beyond delivery; no session ids in URLs.** From the Action README (CLM-E1-064) to the August retention limits (CLM-E4A-057).
- **No consultancy, no managed cutover, no enterprise platform sales** (owner documents, June); **no migration PR against a stranger's production** (the board, 2026-06-29); in the repository, the Migration Pack and GitHub App are "closed research" (CLM-E4A-011).
- **No LLM-generated public pages** (CLM-E2-004); **no fabricated error strings** (CLM-E2-035).
- **No new SKU or price rise without buyer evidence** (CLM-E4B-064); **no registry pipeline** ("registry theater"); **no keyword-only releases, sponsor-link advertising or duplicate hosted sites** (CLM-E4B-053).
- **No force pushes; no rewriting of the audited history** (P-15).
- **No leaving the jail** — not for a credential, not for a device path, not for the owner's own env files (CLM-E4B-055, CLM-E4B-056).

What the negative space reveals: a solo owner who would not trade personal time, reputation or platform standing for revenue, and agents that took those refusals more literally than the goals.

## Recurring tensions

**Autonomy versus the owner's click.** "If a step needs a human, it does not exist" was written on the second day and contradicted by the first handoff (CON-001). Every era's definition of success ended at an owner action the owner did not take; the operating documents responded by budgeting the action in minutes rather than removing it.

**The ship law versus the truth rule.** "An analysis-only cycle is a failed cycle" produced a week of one-line commits and a corpus of unreviewed articles; "truth only" produced a month of sweeps that found the corpus wrong. The August regime resolved this by deleting the publishers and keeping the sweeps.

**Containment versus the mission.** "One command outside the jail is a worse outcome than earning $0" was tested literally on 2026-09-04 and won three times (CLM-E4B-055). The cost is visible in the ledgers; the rule did not bend.

**Deadline versus evergreen.** The founding market theory against the autopsy's "deserts". Surge pricing made the price a function of the date table, so the date corpus's errors were pricing errors (CLM-E1-061); the single-price August catalogue removed the dependency.

**Verifiability versus verification.** The April trust signals were a belief that hashes substitute for reputation; the signals were placeholders (CON-004). The August evidence gates keep the belief and demand that the measurement be real, conservative and repeatable (five Gallery samples, the lowest value).

**Openness versus revenue.** The free surfaces carried every real signal the project ever had — a hundred installs, seventy-two page views — while every paid surface was closed or untested. The project chose, by September, to treat that as the correct order rather than a failure (P-17, P-12.2).

**Code versus deployment.** What the repository said and what the host did diverged for the entire life of the paid product (CON-018). The tension is structural: the code is the agents'; the host is the owner's.

## Stated ideals and revealed behaviour

| Stated | Revealed by behaviour | Reading |
|---|---|---|
| "Every trust signal terminates in a verifiable hash" | 2,949 status commits probing a retired Worker; a benchmark counting empty output as clean | Visible motion was valued over verified truth until 2026-08-22 |
| "Fully autonomous fulfilment" | Every launch gate operator-only; five marketplace publishes never clicked | Autonomy governed design, not launch |
| "No autonomous contact with real humans" | A cron publishing agent-written articles under the owner's account | The rule was read to exclude own-content publishing, then re-read to include it |
| "Truth only" | The same date bug found one layer deeper five cycles running | The rule was enforced as repair, not as a gate, until the catalogue was cut |
| "Don't relapse into building" (autopsy) | A rebuild of 338 files eight weeks later | Building continued; what changed is that it built removal |
| "The jail is total" | Three cycles terminated over `/dev/null` | Taken literally, at cost |
| "$0 seed" | No spend recorded in any era | Held absolutely |

None of these divergences is presented as hypocrisy; each is a place where a written rule met a situation its author had not imagined, and the record shows which way the project leaned. Where motive would be needed to say more, this chapter does not say more.
