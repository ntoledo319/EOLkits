# Current asset map

Snapshot: September 10, 2026. Detailed prior audits and their changing test counts
are preserved in [the complete archive](archive/2026-09-10/ASSETS.md). Current
engineering work is in [MAINTENANCE](../docs/MAINTENANCE.md).

| Asset | What it does | Distribution/runtime | Commercial status |
|---|---|---|---|
| [Lambda Lifeline](../kits/lambda-lifeline/README.md) | Finds configured Lambda runtime/source/dependency/IaC risks and previews targeted changes. | Local Node CLI; GitHub Action. | Free, MIT. |
| [Python Pivot](../kits/python-pivot/README.md) | Checks Python/Lambda inputs, layers/extensions, Powertools and SDK models; proposes bounded changes. | Local Python CLI; GitHub Action. | Free, MIT. |
| [AL2023 Gate](../kits/al2023-gate/README.md) | Checks AWS Config/Terraform state and generates EKS, agent-config, migration and CI proposals. | Local Python CLI; GitHub Action. | Free, MIT. |
| [Browser scanner](https://ntoledo319.github.io/EOLkits/scan/) and static guidance | Performs local source checks and presents cited migration guidance. | Deterministic Python-generated site; GitHub Pages and existing custom host. | Free; no uploaded browser-scan source. |
| [VS Code extension](../apps/vscode-extension/README.md) | Displays local findings, diagnostics and coverage in the editor. | Existing `rupture.rupture-vscode` identity; last recorded public version 1.3.0. | Free, MIT; published version differs from unshipped local work. |
| [Audit v2](../HANDOFF.md) API and report runner | Turns one supported upload into a static evidence PDF with locations, hashes and limits. | FastAPI/WeasyPrint on existing GRACE infrastructure. | Planned $299 report; checkout closed; real fulfillment gate unverified. |
| Retired Worker and legacy commerce concepts | Reject legacy commerce requests; preserve safe tombstones. | Existing Worker/API surfaces. | No sale, subscription, App fulfillment or white-label offer. |

Run the relevant [verification groups](../docs/development.md) for the current
checkout. Earlier test counts describe their recorded revisions, not today's
coverage. CI and local fixtures do not prove a deployed purchase path.

The smallest intended sellable unit remains one static evidence report. The
free tools are independently useful; their correctness is not paywalled.
Dependencies/provenance are documented in [ATTRIBUTIONS](../ATTRIBUTIONS.md) and
the two resolved Python license inventories. Recheck licenses before packaging
any new artifact for sale. The existing host's incremental cost remains an
owner-supplied fact; no new infrastructure spend is permitted.
