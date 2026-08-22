# EOLkits AWS Deprecation Check

This free composite GitHub Action runs the repository's local AWS deprecation
checks and writes a bounded Markdown report to the job summary.

## Usage

```yaml
permissions:
  contents: read
  pull-requests: write # omit when comment-pr is false

steps:
  - uses: actions/checkout@v6
  - uses: ntoledo319/EOLkits@v2
    with:
      kit: auto
      path: .
      fail-on: any
      comment-pr: true
```

Inputs are documented in the root [`action.yml`](../../action.yml). The `path`
must resolve inside `GITHUB_WORKSPACE`; missing paths, traversal, and external
absolute paths fail closed.

## Boundaries

- The action checks source, dependency manifests, and supported IaC patterns. It
  does not inventory an AWS account or prove that a match is exploitable.
- Scan commands run without their apply flags and do not intentionally modify the
  checked-out repository.
- PR comments are off by default. `comment-pr: true` requires pull-request write
  permission; keep the default for a read-only or untrusted-fork workflow.
- Setup actions and package installation use the network. Repository contents are
  not sent to EOLkits.

The action is free. The only paid EOLkits product currently offered is the
server-gated [$299 repository evidence report](https://ntoledo319.github.io/EOLkits/audit/?utm_source=github_action&utm_medium=readme).
