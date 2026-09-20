# Current evidence ledger

The complete dated observations, including contradictory historical readings,
are preserved in [the archived ledger](archive/2026-09-10/METRICS.md). Append only
observed results here; forecasts belong in [PLAN](PLAN.md).

| Observed date | Evidence | Limit |
|---|---|---|
| Through September 10, 2026 | Last workspace-recorded collected revenue/profit $0; purchases 0; paid reports 0; last target gap $4,000. | No fresh payment-account reconciliation was performed. This is not a claim about account-wide Stripe balances. |
| September 4, 2026 | Five-sample Gallery lower bound 104 installs/226 downloads, versus baseline 103/199; public extension 1.3.0. | A dated acquisition reading, not a current counter, distinct users or revenue. |
| September 5, 2026 | Last recorded v2 capability/status probes returned 404; env inbox contained no usable credentials. | Not re-probed by this documentation pass; later static-site success does not establish API deployment. |
| September 10, 2026, 08:28:37 UTC | Root operator recorded 65 repaired HTML files, 67 timestamped backups, a no-change rerun, and healthy neighboring sites. | Authorized first-party analytics repair only. |
| September 10, 2026 | [Static guard 34455421385](https://github.com/ntoledo319/EOLkits/actions/runs/34455421385) and [IndexNow 34455467762](https://github.com/ntoledo319/EOLkits/actions/runs/34455467762) succeeded. Browser check at 08:33:11 UTC: tracker script/event HTTP 200, no CSP violation. | One synthetic pageview; no inference of indexing, ranking, external visitors or purchases. |
| September 10, 2026 | [PR #59](https://github.com/ntoledo319/EOLkits/pull/59) merged; #32/#36/#37 closed for compatibility. Local API 95 tests, runner 45 tests, four Python lock audits, 98 Node license records, PDF/preflight smoke and Wrangler dry-run passed. | Remaining dependency PRs, new Python 3.14 behavior checks and PR #63's refreshed CI are pending publication. |
| September 10, 2026 | Reviewed maintenance commit 190e6432 remains local; push rejected before execution despite existing owner authorization. | No focused maintenance PR or completed emergency publication is claimed. See [maintenance](../docs/MAINTENANCE.md). |
| September 10, 2026, cleanup completion | All 13 local verification groups passed: Python 130, AL2023 92, API 95, runner 45, web 79, Worker 39; browser/packaging/types/history checks; four Python audits and three full Node audits clean. Parent Python 3.14.7 API 95/runner 45 plus real PDF/preflight/native-image checks passed. | Local working-tree evidence; exact container CI, twelve dependency merges, PR #63 refresh and publication remain blocked. No revenue or production migration implied. |
| September 20, 2026 | `eolkits.com/api/capabilities` returns `audit.checkout_enabled: true, reason: "ready"`; `/api/status` returns `stripe: {ok: true, mode: "live"}`. Production checkout is open on live keys. | A readable capability signal, not a sale. Collected revenue is still $0.00 and no purchase has ever been made. |
| September 20, 2026 | First end-to-end fulfillment run in this product's history: `generate_audit_package` executed inside the live container and produced a real 21,624-byte PDF carrying an evidence hash. | Report generation only. Checkout, webhook, email delivery, signed download, refund reconciliation and retention sweeps remain unrecorded (see [HANDOFF](../HANDOFF.md)). |
| September 20, 2026 | A trivial input yields 0 findings and a 2-page report. | Recorded as a live commercial risk: a buyer with nothing wrong pays $299 for an empty report. Unfixed at this date. |
| September 20, 2026 | The GitHub Pages mirror `ntoledo319.github.io/EOLkits/` was disabled; `/scan/` and `/audit/` now return 404 (verified by request). | It had been a genuine second checkout against the same backend (`const API='https://eolkits.com'`, same $299 form). `eolkits.com` is now the single till. |
| September 20, 2026 | 30-day refund policy published for the paid report. | Publication observed; no refund has been processed, because no purchase has been made. |

The [emergency history event](../.project-history/events/2026/eolkits-2026-09-10-emergency-maintenance.md)
links the maintenance evidence to its source and commit anchors. Documentation
consolidation and tests are engineering evidence, not collected money. Production
checkout remains closed, and the seven-step fulfillment gate is still unrecorded.

## September 20, 2026 — correction to this ledger's closing note

The paragraph above ends with "Production checkout remains closed, and the
seven-step fulfillment gate is still unrecorded." That was true when written and
is **no longer true of checkout**. As of 2026-09-20 production checkout is open
on live Stripe keys. The second half still holds: the seven-step gate is not
fully recorded — only the report-rendering half of step 3 is, and that was
verified in the live container on the same date. Prior entries are left exactly
as written.
