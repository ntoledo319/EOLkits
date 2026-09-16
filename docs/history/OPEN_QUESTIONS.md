# Open questions, gaps and low-confidence claims

"No evidence found" never means "did not happen." This chapter lists what the reconstruction could not settle, ranked by how much an answer would change the record, followed by the gap register (sparse periods, lost sources, suspected losses) and the claims and contradictions that remain below `strongly_supported`. Anyone who can answer an item should add the evidence as a new claim and an amendment to the affected capsule rather than editing the capsule's closed text.

## Ranked open questions

1. **What did the owner actually instruct at each regime change?** The day-one mission brief (2026-04-28), the runbook's adoption (04-29), the rename (late May), the autopsy (06-21), Cycle 0 of the revenue loop (07-13), the rebuild (08-22) and the "explicit owner direction" behind one-use authorisations (08-25, 08-31) are all known only through agent-written text that quotes or paraphrases the owner. Session transcripts are outside git. An answer would move most `credit`-kind contradictions (CON-020) and several `inferred` claims (CLM-E4A-041) to verified.
2. **Was any stranger ever charged?** No payment, refund or partner sign-up appears in any ledger, and the July "billing honesty" work implies the exposure was real for eleven weeks. A read-only Stripe export for 2026-04-30..2026-08-25 would close CON-015's outcome and confirm P-08 was never breached in fact.
3. **What ran on the GRACE host, and when?** The repository pins the deployed state on 2026-06-17 and 06-21 only (CLM-E2-040); every later statement about eolkits.com is a probe recorded in a ledger. The host's deploy log and Caddy configuration would settle CON-018 (code closed vs live host), CON-028 (the injected script) and whether the June email fix ever shipped.
4. **Which instruction set ran the Claude cycles after 2026-08-22?** They cite an AGENTS.md that is not the committed one (CLM-E4B-005; CON-022). The untracked file would let the record attribute the BUILD_DATE routine and the dev.to fallback to a document rather than to "the Claude line".
5. **How did owner-scope GitHub authority reach the jailed workspace on 2026-09-04?** D54 (08-31) and D70 (09-04) contradict each other; the ruleset creation is verified, the mechanism is not (CON-021). The answer bears on P-10's meaning.
6. **Were the dev.to articles live in July, and are they now?** The routine could not verify its own publications (CLM-E3-019); the August ledgers report 25 public posts with wrong dates still up (CLM-E4B-066). The dev.to account's publication dates would settle CON-013 and the exposure of P-07.2.
7. **Did any AWS date delivered to a user before 2026-07-13 turn out wrong?** The date corpus was inconsistent from day two and swept for a month (CON-003). Scan outputs or PDFs delivered to strangers, if any exist, would tell whether the truth problem ever reached a reader.
8. **Why did activity stop between 2026-05-04 and 05-15, and again between 06-30 and 07-13?** Both gaps follow a missed launch window. The owner's calendar or the portfolio's other project records for those weeks would explain the two most consequential silences in the history.
9. **Where and why was "EOLkits" chosen?** Only the domain-naming exercise survives (CLM-EXT-002); the repository states mechanical reasons only (CLM-E2-007). The owner could answer this in a sentence.
10. **Were the project's own runtime secrets rotated after the September sweep?** The sweep left the repository untouched and records no rotation for it (CLM-EXT-035; CON-026). The names are known; the rotation status is not.
11. **What did the 2026-09-05 gates emit?** The VS five-day gate and the Day-14 revenue gate both fall the day after this audit's HEAD (CLM-E4B-063). They are the first data points of the next era.
12. **Did the rupture-sandbox PR, the GitHub App secrets and the VS Code v1.0.0 publication of May actually happen as the internal ledgers reported?** The extension's publication was confirmed only in August (CLM-E4A-035); the sandbox PR and App secrets remain reported (CLM-E1-048, CLM-E1-049).
13. **Was the 2026-08-10 orphan merge a deliberate dry run or a mistake?** Its message says "NOT DEPLOYED"; it was never referenced again (CLM-E3-038).
14. **Was the 90-day free-CLI gate of the 2026-06-29 board ever checked?** G-11 has no external measurement; the repository's install count would satisfy one clause if the installs are genuine.
15. **Which of the ~38 unverified August mirror pairs differ from their originals?** Four were checked byte-identical; one known pair differed in ledger text (CLM-E4A-022, CLM-E4A-046).

## Gap register

| Gap | Period or object | What was searched | Status |
|---|---|---|---|
| Prehistory before the root commit | before 2026-04-28 | git (single-line root), untracked tool logs, owner notes | Only the 2026-05-05 owner note and the day-one ledger's mission name survive; the brief itself is absent |
| The off-repo operator handoff of 2026-04-30 | `RUPTURE_HANDOFF_OPERATOR.md` on a desktop | untracked aider logs reference it | Not found; content unknown |
| First silence | 2026-05-04 → 05-15 | all refs, PRs, owner notes | Bot commits only; no explanation |
| The "§2.1/§2.2 plan" and `business-ops/MARKETING-MACHINE-RUNBOOK.md` referenced by June commits | 2026-06-08 | business-ops corpus, toledo-command | Not found under those names |
| "the empire" | June distribution README | owner corpus | Undefined; an off-repo prior system |
| Second silence | 2026-06-30 → 07-13 | all refs | No commits; AL2 deadline passed unremarked in-repo |
| VPS deploy state | after 2026-06-21 | repository pins, ledgers | Reported probes only |
| GitHub Actions run logs | all eras | not retrieved (scope) | Run ids and success flags via the API; contents unknown |
| Marketplace and Gallery live state | May → September | prohibited (no browser) | Reported by ledgers; corroborated only by workflow run success |
| Nineteen remote-only commits | dependabot branches; PR heads 14, 15, 24, 31, 32; PR #43 head | ls-remote comparison | Not fetched (read-only audit); content is dependency bumps or merged trees |
| A GitHub workflow registered with no local ref | `temporary-sample-report-refresh.yml` | GitHub API, all refs | Origin unknown (CLM-E4B-068) |
| Stripe, Resend, Cloudflare dashboards | all eras | out of scope | No independent financial record examined |
| The Claude cycles' instruction file | 2026-08-22 → 09-04 | `.claude/` is git-ignored | Not in git |
| Owner-side measurements of G-11 | 2026-06-29 → 09-27 | toledo-command, marketing-arm, outreach records | None found |

## Claims below strongly_supported

Ten claims are `plausible`; none is `speculative`. They are listed so that readers weigh them accordingly:

- CLM-E1-049 — that the GitHub App key had been installed by 2026-05-04 (inferred from a script's requirements).
- CLM-E2-018 — that the 2026-06-09 deploy ran from a machine with VPS SSH access (inferred from documents that contradict each other).
- CLM-E2-060 — that dependabot handling was neglect-then-triage rather than policy.
- CLM-E3-019 — whether articles 05–24 were live on dev.to during July (unknown).
- CLM-E3-044 — the cause of the bot's `ok:false` status readings.
- CLM-E4B-020, CLM-E4B-033, CLM-E4B-039 — VS Code gate readings that rest on Gallery counters this audit could not query.
- CLM-E4B-066 — that 25 DEV posts remain public.
- CLM-EXT-036 — a one-line June note that a Stripe-key-shaped string was a dummy.

## Contradictions that remain open

Eleven of the twenty-eight registered contradictions are open: CON-003 (the date corpus), CON-010 (the June verdict sequence), CON-013 (autonomous publishing), CON-018 (code vs live host), CON-020 (authorship), CON-021 (admin authority), CON-022 (which operating doc), CON-023 (what remained autonomous), CON-024 (the noisy gate), CON-025 (the legal entity), CON-028 (the injected script). Each entry in [`.project-history/contradictions.yml`](../../.project-history/contradictions.yml) names the evidence that would close it.

## Evidence deliberately not read

For privacy: third-party lead names in `launch/distribution/email/targets.md`; contact data in the owner's outreach cockpit; family-facing notes; the values of any file under the credential vault. For scope: the source code of the other portfolio projects that share the lead bus and the host. These omissions are recorded in [`.project-history/sources.yml`](../../.project-history/sources.yml) and [`.project-history/state.yml`](../../.project-history/state.yml).

## Suspected lost history

- The planning corpus of 2026-04-29..05-02 and the narrative documents of June and July were deleted from the tree (2026-05-02, 2026-08-22). All are recovered by SHA in this history; nothing is known to be lost from git.
- Eve's launch pack exists only on an orphan branch and a local merge (CLM-E3-037, CLM-E3-038); it is reachable but was never deployed.
- The 2026-08-25 exact-tree merge dropped 211 lines of hand-drafted answers; they were restored the next day (CLM-E4A-043). No other silent drop is known.
- No rewrite of this repository's ancestry has occurred (CLM-EXT-029, CLM-E4B-027). If one ever does, `python3 scripts/project_history.py audit --full` will report the unreachable anchors and the affected claims must be rebound by amendment.
