# Development

Run commands from the repository root. Use **Python 3.12**, **Node.js 24**, npm,
and Git for the standard local checks. The API and runner also have a Python
3.14 CI matrix. This development toolchain does not change the runtime versions
supported by each shipped scanner or the VS Code extension. Lambda Lifeline
requires Node.js 20+ to match its AWS SDK dependencies; the Python kits retain
Python 3.9+ support and the extension retains VS Code 1.85+.

## Verify a checkout

```bash
python3 scripts/verify.py all
```

The repository-owned verifier prepares project-local environments and runs
component checks. Temporary files, dependency caches, reports, and virtual
environments belong under `tmp/`; dependencies are not installed globally.
See [scripts/verify.py](../scripts/verify.py) for the executable contract and
[the CI workflow](../.github/workflows/test.yml) for hosted checks.

Use a smaller group while working:

| Group | Surface |
|---|---|
| `web` | Generated site and browser scanner |
| `api` | GRACE API |
| `runner` | Evidence/PDF runner and fictional sample |
| `python` | Python Pivot |
| `al2023` | AL2023 Gate |
| `node` | Lambda Lifeline |
| `worker` | Retired Worker tombstone |
| `editor` | VS Code extension |
| `action` | GitHub Action fixtures and acquisition-evidence reduction |
| `lint` | Python lint, format, type and deployment-shell checks |
| `history` | Living-history validation and tool tests |
| `maintenance` | Deployment/tooling regression tests and task inventory |
| `audit` | Python vulnerability audits and Node dependency/license checks |
| `all` | All local groups |

For example, `python3 scripts/verify.py web` checks a web change, and
`python3 scripts/verify.py api runner` checks both report services. Use
`python3 scripts/verify.py --list` to inspect current groups without installing or
running checks. The latest execution status and command/output fingerprints are
written to `tmp/verify/last-run.json`. Read failures before rerunning; a missing
tool or unsuccessful check is not a pass.

After preparing a group, `--offline` reuses its fingerprinted dependencies and
refuses missing or stale environments. The `action` group refuses offline mode
because it provisions its own dependencies. Vulnerability audits still require
registry access; the flag controls installation, not network isolation.

PDF rendering needs the native libraries used in the
[runner Dockerfile](../apps/runner/Dockerfile), including Pango, HarfBuzz and
fonts. Browser verification needs installed Chrome or Chromium; set
`EOLKITS_CHROME` to an available executable when automatic detection cannot find
it. The local lint group also requires ShellCheck. Vulnerability audits need
registry access and npm 11 or newer. Container builds and host deployment checks need
Docker/Compose and the additional tools named in [the deployment guide](../deploy/grace/README.md).
Use the existing host toolchain; avoid changing unrelated machine configuration.

## Install a kit for interactive development

The verifier covers tests. For an editable Python CLI, create a local environment:

```bash
mkdir -p tmp/runtime-tmp tmp/pip-cache
export TMPDIR="$PWD/tmp/runtime-tmp"
export PIP_CACHE_DIR="$PWD/tmp/pip-cache"
python3 -m venv tmp/kits-venv
tmp/kits-venv/bin/pip install -e 'kits/python-pivot[dev]' -e 'kits/al2023-gate[dev]'
tmp/kits-venv/bin/python-pivot --help
tmp/kits-venv/bin/al2023-gate --help
```

For the Node kit:

```bash
mkdir -p tmp/npm-cache
export npm_config_cache="$PWD/tmp/npm-cache"
npm ci --prefix kits/lambda-lifeline --no-audit
node kits/lambda-lifeline/bin/cli.mjs --help
```

Live AWS modes require the relevant kit's optional AWS dependencies and your own
least-privilege credentials. Follow each kit's command reference and inspect its
dry-run before any apply operation. Provider access is not required for fixture
checks.

## Where to change things

Edit site templates and assets under `apps/web/`, then use the web verification
group to rebuild and check `docs/`. Generated HTML is not the source of truth.
The Markdown maintenance and development guides under `docs/` are maintained by
hand; `docs/history/` follows its own deterministic history renderer.

Public lifecycle data lives in `rules/public/deprecations.yml`. API behavior
lives in `apps/grace-api/eolkits_grace/`; report extraction/rendering lives in
`apps/runner/`. Keep browser, editor and CLI behavior within their documented
scope rather than assuming every surface implements every rule.

Before a PR, follow [CONTRIBUTING](../CONTRIBUTING.md), review the diff, and record
verification and [history impact](history/ORIENTATION.md). Engineering work is
tracked in [MAINTENANCE](MAINTENANCE.md); production and paid-product prerequisites
are in [HANDOFF](../HANDOFF.md) and [the owner queue](../revenue/HUMAN_QUEUE.md).

## Dependency maintenance

Security audits include development tools in all three Node lockfiles. The Worker
currently scopes a `sharp` override to Miniflare because its pinned 0.35.2 image
library was vulnerable; 0.35.4 passes native AVIF decoding/PNG conversion and the
Worker's build, tests and dry-run bundle. Remove that override only when the
upstream graph resolves a patched version and those checks pass. Keep extension
TypeScript below 6.1 until its parser/plugin peer range changes; updating the
Worker's TypeScript does not require the same editor update.
