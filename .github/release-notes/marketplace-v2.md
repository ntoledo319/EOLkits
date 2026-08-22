## Rupture AWS Deprecation Check v2.0.0

This release replaces the stale v1 Marketplace surface with the bounded,
path-confined EOLkits repository check.

### What changed

- Checks selected source and infrastructure-as-code paths for configured AWS
  runtime, dependency, and Amazon Linux migration concerns.
- Runs dry by default and does not change AWS resources.
- Supports explicit `auto`, `all`, `lambda-lifeline`, `python-pivot`, and
  `al2023-gate` modes.
- Writes a Markdown job summary and exposes machine-readable finding/failure
  outputs.
- Posts a pull-request comment only when the caller explicitly enables it and
  grants the required permission.
- Uses Python 3.12 and Node.js 24 for the bundled scanners.

The free Action does not inspect every AWS resource or guarantee a complete
migration inventory. EOLkits' only optional paid offer is a capability-gated
$299 static repository evidence report; checkout remains hidden whenever the
fulfillment service is not ready.

Install the stable major release channel with:

```yaml
- uses: ntoledo319/EOLkits@v2
  with:
    kit: auto
    path: .
    fail-on: any
```
