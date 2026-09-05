# Decision map

Decision genealogies for the concepts that shaped EOLkits, each traced as *pressure or need → belief or goal → alternatives → decision → implementation → observable result → consequences → later revision*, with cross-links to the event capsules and claim ids. The generated index at the end lists every capsule with its `related`, `amends`, `supersedes` and `reversed_by` links and is rebuilt by `scripts/project_history.py render`.

## 1. The catalogue: what was for sale

- **Pressure.** A revenue target set before any product existed (CLM-E1-003).
- **Belief.** Deadline buyers will pay for a shortcut; every SKU must fulfil itself (CLM-E1-005, CLM-E1-017).
- **Alternatives.** Support tiers (day one) vs self-serve SKUs (day two); later, fixing fulfilment vs deleting the SKU vs marking it research (CON-015); 42 frames scored in August (CLM-E4A-016).
- **Decision.** Five SKUs with surge pricing on 2026-04-29 → [runbook](../../.project-history/events/2026/eolkits-2026-04-29-autonomy-runbook-five-skus.md).
- **Implementation.** Stripe products provisioned 04-30 (CLM-E1-032); a Worker that could sell what a stub runner could not deliver (CLM-E1-027); Drift Watch checkout 06-08 (CLM-E2-013).
- **Result.** Two SKUs with live checkout and no fulfilment for eleven weeks; no charge evidenced (CLM-E3-022, CLM-E3-023).
- **Consequences.** The billing-honesty arc → [SKU retirement](../../.project-history/events/2026/eolkits-2026-07-14-billing-honesty-sku-retirement.md); kit READMEs advertising tiers that did not exist (CON-002).
- **Revision.** One $299 report, three tombstones, checkout off → [rebuild](../../.project-history/events/2026/eolkits-2026-08-22-truthful-evidence-report-rebuild.md); prices archived → [legacy retirement](../../.project-history/events/2026/eolkits-2026-08-22-legacy-commerce-retirement.md); runtime-supplied price behind preflight → [recovery](../../.project-history/events/2026/eolkits-2026-08-30-fail-closed-relaunch-recovery.md). Principle lineage P-12 → P-12.2.

## 2. The deadline thesis

- **Pressure.** Node.js 20's deprecation two days away on the first day (CLM-E1-004).
- **Belief.** "The deadline is the news, not the product."
- **Alternatives.** Ship one kit (recommended) vs all three ("do em all").
- **Decision.** Build to dates; price by days-to-deadline (CLM-E1-061).
- **Implementation.** Countdown copy, surge tiers, an ICS feed, a README saying "EOL in 19 days" → [AL2 reframe](../../.project-history/events/2026/eolkits-2026-05-21-al2-deadline-reframe-and-hn-attempts.md).
- **Result.** Two dates passed with $0; six launch windows slipped (CLM-E2-036).
- **Consequences.** Stale countdowns became a class of truth bug (CLM-E3-009); the date table's errors became pricing errors (CON-003).
- **Revision.** Disowned by the [autopsy](../../.project-history/events/2026/eolkits-2026-06-21-autopsy-never-reached-market.md) in favour of evergreen search; single price removes the dependency (P-12.2). The next deadline the project watches is February–March 2027, from the sidelines.

## 3. Truth in public claims

- **Pressure.** Copy written by agents faster than code (CLM-E1-060, CLM-E1-059).
- **Belief.** Verifiability substitutes for reputation (CLM-E2-030).
- **Alternatives.** Fix copy as found vs cut the catalogue to what is provable.
- **Decision (three times).** "Hard removals" of fabricated history (04-29); "truth only" as a nightly discipline (07-13); "truthful by construction" (08-22).
- **Implementation.** Corrections on 06-11 (CLM-E2-025); a month of [date sweeps](../../.project-history/events/2026/eolkits-2026-07-13-node20-date-truth-sweeps.md); the not-for-sale list and `null` status counters (CLM-E4A-011, CLM-E4A-059).
- **Result.** Each regime found its predecessor's untruths (CON-004, CON-014); false negatives in the free scanner surfaced last (CLM-E4B-019).
- **Consequences.** The rules file guarded by a parity test (CLM-E4B-034); "unavailable evidence is never negative evidence".
- **Revision.** P-07 → P-07.2 → P-07.3; P-03 → P-03.2; P-05 → P-05.2.

## 4. The runtime and the host

- **Pressure.** R2 never enabled; checkout pages emitting template placeholders (CLM-E2-005, CLM-E2-011).
- **Belief.** $0 hosting on a box already paid for; fail closed on configuration.
- **Alternatives.** Enable R2 (abandoned) vs self-host; no written comparison.
- **Decision.** FastAPI on GRACE → [Cloudflare → GRACE](../../.project-history/events/2026/eolkits-2026-06-08-cloudflare-to-grace-runtime.md).
- **Implementation.** 129 files on 06-08; profit levers the same day; a lead bus on 06-17 → [branch and lead bus](../../.project-history/events/2026/eolkits-2026-06-16-marketing-machine-v2-branch-and-lead-bus.md).
- **Result.** Endpoints answered; email could not deliver until 06-23 (CON-007); the host later injected a script the policy denied → [incident](../../.project-history/events/2026/eolkits-2026-08-25-host-injected-analytics-contained.md).
- **Consequences.** Deployment only from the owner's machine; code and host diverged for the rest of the history (CON-018).
- **Revision.** Preflight, Caddy block, snapshot script, `deploy-api-closed.sh` → [recovery](../../.project-history/events/2026/eolkits-2026-08-30-fail-closed-relaunch-recovery.md), [September 4](../../.project-history/events/2026/eolkits-2026-09-04-evidence-gate-v13-and-closed-deployment-hardening.md). P-16 → P-16.2.

## 5. The name

- **Pressure.** A Marketplace slug that 404'd; docs pointing at a repository that did not exist (CLM-E2-007).
- **Belief.** Off-repo: a name "senior devs recognise" (CLM-EXT-002).
- **Alternatives.** DeprecationFix, RuptureKit and others in the owner's naming exercise; on 06-11, pointing everything back at Rupture (CLM-E2-024).
- **Decision.** EOLkits → [rename](../../.project-history/events/2026/eolkits-2026-06-11-rupture-renamed-eolkits.md).
- **Implementation.** 05-31 first files; 06-08 README; 06-11 GitHub rename between two contradictory commits (CON-008).
- **Result.** Redirect works; marketplace identities, Stripe metadata, the bot committer, the local path and a draft release keep "Rupture".
- **Consequences.** Two names for life; a new publisher id rejected twice (CLM-E4A-035, CLM-E4B-021).
- **Revision.** None; the residue is accepted.

## 6. Distribution and the launch

- **Pressure.** No traffic, ever.
- **Belief.** One Show HN would carry the launch (G-03).
- **Alternatives.** Cold outreach (cut, breached, re-cut); paid ads (never activated); Reddit (policy-dead); Upwork/Fiverr (ruled out by the owner); marketplaces (owner-gated); content (autonomous); forum answers (drafted).
- **Decision.** Prepare everything; let the owner post.
- **Implementation.** Launch kits in every era; two HN submissions (CLM-E2-031); three re:Post answers (CLM-E3-013) → [only demand test](../../.project-history/events/2026/eolkits-2026-07-15-repost-answers-only-demand-test.md); an issue form and IndexNow (CLM-E4A-032, CLM-E4A-033) → [free surfaces](../../.project-history/events/2026/eolkits-2026-08-22-free-surfaces-made-truthful.md).
- **Result.** HN rejected twice; zero replies to cold sends (CLM-EXT-009); ~100 extension installs and 72 page views are the only measured audience (CLM-E4A-035, CLM-E4B-052).
- **Consequences.** The autopsy's Finding 1; the operating document's Human Queue; launch copy archived as not approved (CLM-E4A-058).
- **Revision.** Free surfaces as the acquisition path with mechanical falsifiers (P-17, G-10) → [reposition](../../.project-history/events/2026/eolkits-2026-08-31-vscode-reposition-and-authorized-ops.md).

## 7. The operating model

- **Pressure.** A solo owner; agents as the only labour.
- **Belief.** Sessions are disposable; the ledger is the brain (AGENTS.md §13).
- **Alternatives.** Interactive sessions (April–June) vs a headless nightly routine (July) vs pull-request cycles publishing without credentials (August) vs two lines under two rulebooks (September).
- **Decision.** AGENTS.md → [Revenue Loop v2](../../.project-history/events/2026/eolkits-2026-07-13-revenue-loop-v2-operating-doc.md).
- **Implementation.** Six ledgers; a jail; a ship law; an evidence hierarchy; later one-use push authorisations (CLM-E4A-039) and the object-API transport (CLM-E4B-028).
- **Result.** Daily "$0 collected" every day from 2026-07-13 to 2026-09-04; self-recorded containment failures → [jail violations](../../.project-history/events/2026/eolkits-2026-09-04-jail-violations-and-env-recovery-scan.md); a branch absorbed and recreated → [absorption](../../.project-history/events/2026/eolkits-2026-08-29-marketing-machine-v2-absorbed.md).
- **Consequences.** Unstable decision numbering (CON-019); authorship not recoverable (CON-020); an instruction set outside git (CON-022).
- **Revision.** This history system (P-14) → [bootstrap](../../.project-history/events/2026/eolkits-2026-09-04-history-system-bootstrap.md).

## 8. The bots

- **Pressure.** Trust signals for a solo, anonymous vendor (P-05).
- **Belief.** A green status page and a nightly benchmark are proof.
- **Decision.** Fourteen workflows on 2026-04-29 (CLM-E1-029), a status synth every five minutes committing as `rupture-bot`.
- **Result.** 3,253 automation commits; a benchmark counting empty output as clean (CLM-E1-037); a status file reading `ok:false` for two months beneath a ledger saying "all systems ok" (CON-014).
- **Consequences.** Human history buried under noise; this reconstruction's exclusion counts.
- **Revision.** Every bot deleted or stripped of its commit step on 2026-08-22 (CLM-E4A-018); evidence gates replace signals (P-05.2).

## 9. History itself

- **Pressure.** Intent documents deleted twice (05-02, 08-22); a purge across the portfolio → [credential sweep](../../.project-history/events/2026/eolkits-2026-09-01-credential-sweep-left-repo-unrewritten.md).
- **Belief.** Rewriting the audited history is worse than carrying it (P-15).
- **Decision.** No force pushes; retire rather than rewrite; record events as capsules (P-14).
- **Result.** Every SHA cited here resolves; GitHub shows no force push by a person ever (CLM-EXT-033).
- **Consequences.** This document.

## Generated decision index

<!-- generated:decision-index -->
| Event | Kind | Related | Amends | Supersedes | Superseded by | Reversed by |
|---|---|---|---|---|---|---|
| [A one-day agent mission builds Rupture Kits: three deadline-driven AWS migration CLIs](../../.project-history/events/2026/eolkits-2026-04-28-rupture-mission-launch.md) `eolkits-2026-04-28-rupture-mission-launch` | origin | `eolkits-2026-04-29-autonomy-runbook-five-skus` | — | — | — | — |
| [The autonomy runbook: five self-serve SKUs, a Stripe-and-Worker fulfilment loop, and CI trust signals](../../.project-history/events/2026/eolkits-2026-04-29-autonomy-runbook-five-skus.md) `eolkits-2026-04-29-autonomy-runbook-five-skus` | operating-model | `eolkits-2026-04-28-rupture-mission-launch`, `eolkits-2026-05-02-v1-signed-release-and-marketplace` | — | — | `eolkits-2026-08-22-truthful-evidence-report-rebuild` | — |
| [Launch hardening, the signed v1.0.0 release, the Marketplace 'v1' tag — and a launch that never fired](../../.project-history/events/2026/eolkits-2026-05-02-v1-signed-release-and-marketplace.md) `eolkits-2026-05-02-v1-signed-release-and-marketplace` | release | `eolkits-2026-04-29-autonomy-runbook-five-skus`, `eolkits-2026-05-21-al2-deadline-reframe-and-hn-attempts` | — | — | — | — |
| [The launch re-aimed at the Amazon Linux 2 deadline, and the Show HN that HN would not accept](../../.project-history/events/2026/eolkits-2026-05-21-al2-deadline-reframe-and-hn-attempts.md) `eolkits-2026-05-21-al2-deadline-reframe-and-hn-attempts` | goal | `eolkits-2026-05-02-v1-signed-release-and-marketplace`, `eolkits-2026-06-21-autopsy-never-reached-market` | — | — | `eolkits-2026-06-21-autopsy-never-reached-market` | — |
| [Deterministic, zero-LLM deprecation pages: the rules file becomes the only source of public facts](../../.project-history/events/2026/eolkits-2026-05-31-deterministic-deprecation-seo.md) `eolkits-2026-05-31-deterministic-deprecation-seo` | architecture | `eolkits-2026-04-29-autonomy-runbook-five-skus`, `eolkits-2026-06-16-marketing-machine-v2-branch-and-lead-bus`, `eolkits-2026-07-13-node20-date-truth-sweeps` | — | — | — | — |
| [Rupture becomes EOLkits: a name chosen off-repo, executed by two agents nine minutes apart, and never fully applied](../../.project-history/events/2026/eolkits-2026-06-11-rupture-renamed-eolkits.md) `eolkits-2026-06-11-rupture-renamed-eolkits` | rename | `eolkits-2026-04-28-rupture-mission-launch`, `eolkits-2026-06-08-cloudflare-to-grace-runtime`, `eolkits-2026-08-22-free-surfaces-made-truthful` | — | — | — | — |
| [The paid runtime moves from Cloudflare Workers to the owner's GRACE VPS, and 'live' is declared before delivery could work](../../.project-history/events/2026/eolkits-2026-06-08-cloudflare-to-grace-runtime.md) `eolkits-2026-06-08-cloudflare-to-grace-runtime` | architecture | `eolkits-2026-04-29-autonomy-runbook-five-skus`, `eolkits-2026-06-11-rupture-renamed-eolkits`, `eolkits-2026-08-22-legacy-commerce-retirement`, `eolkits-2026-08-30-fail-closed-relaunch-recovery` | — | — | `eolkits-2026-08-30-fail-closed-relaunch-recovery` | — |
| [marketing-machine-v2: a long-lived branch that production deployed directly, and an API that became the studio's lead bus](../../.project-history/events/2026/eolkits-2026-06-16-marketing-machine-v2-branch-and-lead-bus.md) `eolkits-2026-06-16-marketing-machine-v2-branch-and-lead-bus` | operating-model | `eolkits-2026-05-31-deterministic-deprecation-seo`, `eolkits-2026-06-08-cloudflare-to-grace-runtime`, `eolkits-2026-07-13-revenue-loop-v2-operating-doc`, `eolkits-2026-08-29-marketing-machine-v2-absorbed` | — | — | `eolkits-2026-08-29-marketing-machine-v2-absorbed` | — |
| [Outside the repository: the owner's portfolio calls the paid arm a dead market, then a first wedge, then shelves it](../../.project-history/events/2026/eolkits-2026-06-20-portfolio-verdicts-dead-market-and-shelving.md) `eolkits-2026-06-20-portfolio-verdicts-dead-market-and-shelving` | external-constraint | `eolkits-2026-06-21-autopsy-never-reached-market`, `eolkits-2026-07-13-revenue-loop-v2-operating-doc`, `eolkits-2026-08-22-truthful-evidence-report-rebuild` | — | — | — | — |
| [The autopsy: '$0 because it never reached the market', the faceless conversion system, and a question the owner did not answer](../../.project-history/events/2026/eolkits-2026-06-21-autopsy-never-reached-market.md) `eolkits-2026-06-21-autopsy-never-reached-market` | reversal | `eolkits-2026-05-21-al2-deadline-reframe-and-hn-attempts`, `eolkits-2026-06-20-portfolio-verdicts-dead-market-and-shelving`, `eolkits-2026-07-13-revenue-loop-v2-operating-doc` | — | `eolkits-2026-05-21-al2-deadline-reframe-and-hn-attempts` | `eolkits-2026-07-13-revenue-loop-v2-operating-doc` | — |
| [One wrong date, twenty places: the superseded Node.js 20 block dates and the month it took to sweep them out](../../.project-history/events/2026/eolkits-2026-07-13-node20-date-truth-sweeps.md) `eolkits-2026-07-13-node20-date-truth-sweeps` | data | `eolkits-2026-05-31-deterministic-deprecation-seo`, `eolkits-2026-07-13-revenue-loop-v2-operating-doc`, `eolkits-2026-08-22-truthful-evidence-report-rebuild` | — | — | — | — |
| [REVENUE LOOP v2: an operating document installs a jailed nightly agent with a truth rule, a ship law and a $4,000 clock](../../.project-history/events/2026/eolkits-2026-07-13-revenue-loop-v2-operating-doc.md) `eolkits-2026-07-13-revenue-loop-v2-operating-doc` | operating-model | `eolkits-2026-06-21-autopsy-never-reached-market`, `eolkits-2026-06-16-marketing-machine-v2-branch-and-lead-bus`, `eolkits-2026-07-15-repost-answers-only-demand-test`, `eolkits-2026-08-22-truthful-evidence-report-rebuild`, `eolkits-2026-09-04-jail-violations-and-env-recovery-scan` | — | `eolkits-2026-06-21-autopsy-never-reached-market` | — | — |
| [Billing honesty: two SKUs that charged real money for nothing, three agents with three remedies, and a fix that reached production only by archiving the prices](../../.project-history/events/2026/eolkits-2026-07-14-billing-honesty-sku-retirement.md) `eolkits-2026-07-14-billing-honesty-sku-retirement` | pricing | `eolkits-2026-04-29-autonomy-runbook-five-skus`, `eolkits-2026-07-13-revenue-loop-v2-operating-doc`, `eolkits-2026-08-22-truthful-evidence-report-rebuild`, `eolkits-2026-08-22-legacy-commerce-retirement` | — | — | `eolkits-2026-08-22-truthful-evidence-report-rebuild` | — |
| [The only demand test: three answers on AWS re:Post, a content flywheel that could not verify itself, and a Day-28 window that closed at $0](../../.project-history/events/2026/eolkits-2026-07-15-repost-answers-only-demand-test.md) `eolkits-2026-07-15-repost-answers-only-demand-test` | experiment | `eolkits-2026-07-13-revenue-loop-v2-operating-doc`, `eolkits-2026-07-14-billing-honesty-sku-retirement`, `eolkits-2026-08-22-free-surfaces-made-truthful` | — | — | `eolkits-2026-08-22-free-surfaces-made-truthful` | — |
| [Free surfaces first: the v2 branch, a private Marketplace draft, Pages as the canonical host, a real sample report, and the extension that was public all along](../../.project-history/events/2026/eolkits-2026-08-22-free-surfaces-made-truthful.md) `eolkits-2026-08-22-free-surfaces-made-truthful` | interface | `eolkits-2026-08-22-truthful-evidence-report-rebuild`, `eolkits-2026-05-02-v1-signed-release-and-marketplace`, `eolkits-2026-06-11-rupture-renamed-eolkits`, `eolkits-2026-07-15-repost-answers-only-demand-test`, `eolkits-2026-08-31-vscode-reposition-and-authorized-ops` | `eolkits-2026-05-02-v1-signed-release-and-marketplace` | `eolkits-2026-07-15-repost-answers-only-demand-test` | — | — |
| [Retiring the legacy rails: a 410 tombstone over the Cloudflare Worker, six Stripe prices archived by an audited workflow, and the invention of one-use push authorisation](../../.project-history/events/2026/eolkits-2026-08-22-legacy-commerce-retirement.md) `eolkits-2026-08-22-legacy-commerce-retirement` | security | `eolkits-2026-04-29-autonomy-runbook-five-skus`, `eolkits-2026-06-08-cloudflare-to-grace-runtime`, `eolkits-2026-07-14-billing-honesty-sku-retirement`, `eolkits-2026-08-22-truthful-evidence-report-rebuild`, `eolkits-2026-08-30-fail-closed-relaunch-recovery` | — | — | — | — |
| [The truthful evidence report: one 338-file commit retires the five-SKU business, the bots and every prior handoff, and restarts the $4,000 clock behind a closed checkout](../../.project-history/events/2026/eolkits-2026-08-22-truthful-evidence-report-rebuild.md) `eolkits-2026-08-22-truthful-evidence-report-rebuild` | reversal | `eolkits-2026-04-29-autonomy-runbook-five-skus`, `eolkits-2026-07-13-revenue-loop-v2-operating-doc`, `eolkits-2026-07-14-billing-honesty-sku-retirement`, `eolkits-2026-06-21-autopsy-never-reached-market`, `eolkits-2026-08-22-free-surfaces-made-truthful`, `eolkits-2026-08-22-legacy-commerce-retirement`, `eolkits-2026-08-30-fail-closed-relaunch-recovery` | — | `eolkits-2026-04-29-autonomy-runbook-five-skus`, `eolkits-2026-07-14-billing-honesty-sku-retirement` | — | — |
| [Incident: the custom host injects a third-party analytics script into every page; contained by a content-security policy, never removed](../../.project-history/events/2026/eolkits-2026-08-25-host-injected-analytics-contained.md) `eolkits-2026-08-25-host-injected-analytics-contained` | incident | `eolkits-2026-06-08-cloudflare-to-grace-runtime`, `eolkits-2026-08-22-free-surfaces-made-truthful`, `eolkits-2026-08-30-fail-closed-relaunch-recovery` | — | — | — | — |
| [The end of marketing-machine-v2 as a distinct line: an exact-tree merge drops hand-written drafts, a reconciliation downgrades them to research, and PR #24 declares the branch superseded](../../.project-history/events/2026/eolkits-2026-08-29-marketing-machine-v2-absorbed.md) `eolkits-2026-08-29-marketing-machine-v2-absorbed` | operating-model | `eolkits-2026-06-16-marketing-machine-v2-branch-and-lead-bus`, `eolkits-2026-08-22-free-surfaces-made-truthful`, `eolkits-2026-08-30-fail-closed-relaunch-recovery` | — | `eolkits-2026-06-16-marketing-machine-v2-branch-and-lead-bus` | — | — |
| [Recovery from the top: PR #25 makes the only paid offer fail closed before any production mutation, and the one-use push trigger becomes a pattern](../../.project-history/events/2026/eolkits-2026-08-30-fail-closed-relaunch-recovery.md) `eolkits-2026-08-30-fail-closed-relaunch-recovery` | security | `eolkits-2026-06-08-cloudflare-to-grace-runtime`, `eolkits-2026-08-22-truthful-evidence-report-rebuild`, `eolkits-2026-08-22-legacy-commerce-retirement`, `eolkits-2026-08-25-host-injected-analytics-contained`, `eolkits-2026-09-04-evidence-gate-v13-and-closed-deployment-hardening` | — | `eolkits-2026-06-08-cloudflare-to-grace-runtime` | — | — |
| [The one permitted reposition: VS extension v1.2.0 as 'AWS Lambda EOL Scanner', a legal operator named, and an owner-authorised one-use platform-operations run that could not do the admin work](../../.project-history/events/2026/eolkits-2026-08-31-vscode-reposition-and-authorized-ops.md) `eolkits-2026-08-31-vscode-reposition-and-authorized-ops` | product | `eolkits-2026-08-22-free-surfaces-made-truthful`, `eolkits-2026-08-30-fail-closed-relaunch-recovery`, `eolkits-2026-09-04-evidence-gate-v13-and-closed-deployment-hardening`, `eolkits-2026-06-20-portfolio-verdicts-dead-market-and-shelving` | — | — | — | — |
| [The September 2026 credential purge: eighteen repositories rewritten, this one inventoried, scanned and left untouched](../../.project-history/events/2026/eolkits-2026-09-01-credential-sweep-left-repo-unrewritten.md) `eolkits-2026-09-01-credential-sweep-left-repo-unrewritten` | external-constraint | `eolkits-2026-08-22-legacy-commerce-retirement`, `eolkits-2026-09-04-jail-violations-and-env-recovery-scan`, `eolkits-2026-09-04-history-system-bootstrap` | — | — | — | — |
| [September 4: a five-sample evidence gate, v1.3.0, the reversal of daily date churn, admin authority found after all, and a closed deployment hardened for an owner who has not deployed it](../../.project-history/events/2026/eolkits-2026-09-04-evidence-gate-v13-and-closed-deployment-hardening.md) `eolkits-2026-09-04-evidence-gate-v13-and-closed-deployment-hardening` | release | `eolkits-2026-08-30-fail-closed-relaunch-recovery`, `eolkits-2026-08-31-vscode-reposition-and-authorized-ops`, `eolkits-2026-07-13-node20-date-truth-sweeps`, `eolkits-2026-05-31-deterministic-deprecation-seo`, `eolkits-2026-09-04-jail-violations-and-env-recovery-scan` | — | — | — | — |
| [Bootstrap of the living-history system (reconstruction of 2026-04-28 to 2026-09-04)](../../.project-history/events/2026/eolkits-2026-09-04-history-system-bootstrap.md) `eolkits-2026-09-04-history-system-bootstrap` | bootstrap | `eolkits-2026-09-01-credential-sweep-left-repo-unrewritten` | — | — | — | — |
| [Governance by self-termination: three cycles ended over /dev/null, /dev/stdout and /tmp, and an in-jail credential-surface scan that recovered nothing](../../.project-history/events/2026/eolkits-2026-09-04-jail-violations-and-env-recovery-scan.md) `eolkits-2026-09-04-jail-violations-and-env-recovery-scan` | governance | `eolkits-2026-07-13-revenue-loop-v2-operating-doc`, `eolkits-2026-09-04-evidence-gate-v13-and-closed-deployment-hardening`, `eolkits-2026-09-01-credential-sweep-left-repo-unrewritten`, `eolkits-2026-09-04-history-system-bootstrap` | — | — | — | — |
<!-- /generated:decision-index -->
