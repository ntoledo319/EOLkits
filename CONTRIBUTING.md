# Contributing to EOLkits

EOLkits provides free AWS migration scanners and one optional, gated repository
evidence report. Start with the [project map](README.md#project-map),
[development guide](docs/development.md), and [current maintenance inventory](docs/MAINTENANCE.md).
Follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Bugs and changes

Search the [existing issues](https://github.com/ntoledo319/EOLkits/issues) before
opening one. Include the command or scanner used, a minimal non-sensitive input,
expected and actual results, and runtime/OS versions. Never attach credentials,
customer uploads, or account exports containing private data.

For a change, use a separate branch, preserve unrelated work, and run the relevant
verification group from the repository root:

```bash
python3 scripts/verify.py python
python3 scripts/verify.py node
```

Use `python3 scripts/verify.py all` for changes spanning components. The
[development guide](docs/development.md) explains prerequisites and the complete
set of groups. `lambda-lifeline` is a Node package installed with npm; the other
two kits are Python packages. There is no Audit-credit or cash bounty program.

A pull request should explain the affected behavior, supported scope, verification
results, and any remaining limits. Link the relevant maintenance item or issue.
Changes that affect durable product behavior, security, deployment, or project
direction also need the history declaration below.

## Rules and migration safety

Public lifecycle dates belong in `rules/public/deprecations.yml`. Cite primary AWS
sources, add fixtures for the affected scanners, and keep the cross-surface date
checks passing. Compatibility rules must identify their inputs and limitations;
a version floor or pattern match is not proof that a workload will run.

Preserve dry-run defaults and require explicit apply options for mutations. Use
synthetic fixtures and mocked providers in tests; no ordinary check should spend
money, contact customers, or modify a cloud account. Check dependency licenses
and update [attributions](ATTRIBUTIONS.md) when distributing new dependencies.

## History and review

Read [history orientation](docs/history/ORIENTATION.md) and obtain path-specific
context before changing a component:

```bash
python3 scripts/project_history.py context kits/python-pivot
python3 scripts/project_history.py assess
python3 scripts/verify.py history
```

Declare exactly one of `history:recorded <event-id>`,
`history:none — <specific reason>`, or
`history:defer — <issue, owner, deadline>` in the PR body. Material changes require
an evidence-linked event under `.project-history/events/`; follow the
[history contract](AGENTS.md#14-project-history--continuity-contract-all-agents-all-harnesses).
Keep historical contradictions and archive references intact.

Contributions are licensed under the repository's MIT license unless an affected
file states otherwise.
