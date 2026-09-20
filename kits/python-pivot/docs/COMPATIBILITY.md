# Python migration compatibility evidence

All commands below are read-only unless the Action generator receives `--apply`.
No archive is extracted, imported or executed. Findings distinguish observed
incompatibilities (`high`) from evidence needing manual review (`review`). Both
count for `--strict`: exit 0 means no findings within the reported coverage,
exit 1 means findings, and exit 2 means invalid input or an operational error.
Machine output is one JSON object with `schema_version`, `kind`, `findings` and
`coverage`; errors go to stderr without a clean JSON report.

## Lambda layers

```bash
python-pivot layers --archive layer.zip --runtime python3.12 --architecture arm64 --format json --strict
python-pivot layers --fixture examples/layer-metadata.json --runtime python3.12 --strict
```

The ZIP scan checks the top-level `python/` directory, versioned site-packages
paths, CPython version names in compiled-library filenames, and 64-bit ELF
machine type against `x86_64` or `arm64`. A matching ELF header does not validate
GLIBC symbols, transitive shared libraries, wheel availability or successful
imports. The rules follow [AWS Python layer packaging guidance](https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html).

Metadata fixtures contain a `layers` array of objects with `LayerVersionArn`,
`CompatibleRuntimes` and `CompatibleArchitectures`, as in the fictional example.
Missing declarations produce review findings. Runtime declarations are optional
publisher metadata used for filtering; they do not guarantee compatibility.
An empty layer list reports zero layers checked, without inventing a failure.

For an existing function, select AWS access explicitly:

```bash
python-pivot layers --live --function example --region us-east-1 --profile migration-review --runtime python3.12 --architecture arm64 --format json
```

Install the existing `python-pivot[aws]` extra for this mode. It uses only
[GetFunctionConfiguration](https://docs.aws.amazon.com/lambda/latest/api/API_GetFunctionConfiguration.html)
and [GetLayerVersionByArn](https://docs.aws.amazon.com/lambda/latest/api/API_GetLayerVersionByArn.html).
The target runtime and architecture describe the planned migration, rather than
being inferred from the current function. Required IAM actions are
`lambda:GetFunctionConfiguration` and `lambda:GetLayerVersion` for the selected
resources. Only layer identity and compatibility arrays enter the report;
environment variables and signed archive download URLs are discarded. The
archive is never downloaded. Authentication or API failure exits 2.

## Lambda extension Python versions

```bash
python-pivot extensions --archive extension.zip --runtime python3.12 --architecture x86_64 --format json --strict
```

The scanner inspects direct `extensions/` entrypoints, executable permission
bits and shebangs. An explicit Python 3.9 launcher without a bundled interpreter
is flagged against target 3.12. Unversioned Python, shell launchers and matching
native binaries require review. An interpreter included under the exact `/opt/`
path requested by the shebang is treated separately; its version is not inferred
from its filename. Wrong native architecture is still an incompatibility.

External extensions run in a separate process and need not use the function's
Python version. AWS recommends packaging a compatible runtime for interpreted
extensions. See the [Extensions API guide](https://docs.aws.amazon.com/lambda/latest/dg/runtimes-extensions-api.html)
and [extension configuration](https://docs.aws.amazon.com/lambda/latest/dg/extensions-configuration.html).
This command does not resolve internal extensions, wrapper environment variables,
shell script evaluation, dynamically selected interpreters or container images.

ZIP limits: 32 MiB input, 10,000 entries, 250 MiB declared expanded content,
and compression ratio at most 200:1 per entry. Stored/deflated regular files and
directories are supported; links, special files, duplicate names, ambiguous or
traversing paths and encrypted entries are rejected. Only bounded member
prefixes are read. Large legitimate archives may need a smaller inspection
artifact; rejection is not a compatibility finding.

## Powertools release matrix

```bash
python-pivot powertools --matrix --runtime python3.12 --format json
python-pivot powertools --package-version 3.34.0 --runtime python3.9 --strict
python-pivot powertools requirements.txt --runtime python3.12 --strict
```

The publisher metadata snapshot, checked on September 10, 2026, records exact
releases. It does not generalize one release's compatibility to a whole major:

| Exact release | Requires-Python | Advertised minor versions |
| --- | --- | --- |
| [2.43.1](https://pypi.org/project/aws-lambda-powertools/2.43.1/) | >=3.8, <4.0.0 | 3.8–3.12 |
| [3.0.0](https://pypi.org/project/aws-lambda-powertools/3.0.0/) | >=3.8, <4.0.0 | 3.8–3.12 |
| [3.15.1](https://pypi.org/project/aws-lambda-powertools/3.15.1/) | >=3.9, <4.0.0 | 3.9–3.13 |
| [3.34.0](https://pypi.org/project/aws-lambda-powertools/3.34.0/) | >=3.10, <4.0.0 | 3.10–3.14 |

The dependency-file form accepts the same flat requirements, PEP 621 pyproject
and Pipfile inputs as `audit`, but needs an exact `==X.Y.Z` Powertools pin.
Ranges, unknown releases and missing declarations produce review findings.
Metadata that permits a Python version without advertising its classifier also
produces a review finding. Extras and native dependencies are outside this
matrix. A passing metadata check does not cover
[Powertools v3 API migration changes](https://docs.aws.amazon.com/powertools/python/latest/upgrade/).

To inspect another release without changing the snapshot, save that release's
PyPI JSON response from `https://pypi.org/pypi/aws-lambda-powertools/VERSION/json`
and pass `--metadata release.json --package-version VERSION`. The command makes
no network request and trusts the supplied publisher metadata file. It accepts
stable numeric versions and numeric comparison clauses in `Requires-Python`;
unsupported specifiers fail clearly instead of being treated as compatible.
Patch-specific bounds within the selected minor version also fail: a target
such as `python3.12` does not identify its exact interpreter patch version.

## boto3 changes from service-model evidence

```bash
python-pivot boto3 src/ --models vendor/target-botocore/data --baseline-models vendor/previous-botocore/data --format json --strict
python-pivot boto3 src/ --installed-models --format json
```

Supply [botocore model directories](https://docs.aws.amazon.com/botocore/latest/reference/loaders.html)
with `SERVICE/YYYY-MM-DD/service-2.json` or `service-2.json.gz` files. Target
models describe the SDK you intend to use; the optional baseline describes the
SDK you currently use. `--installed-models` reads the installed botocore package
data directly, without loading user override models, creating a client, or
contacting AWS. Install `python-pivot[aws]` if botocore is not available.

The AST scanner recognizes literal `boto3.client`, imported/aliased `client`,
and `boto3.Session().client` assignments and chained calls. It checks direct
keyword parameters against the operation input shape, including modeled
`deprecated` flags. Missing operations, parameters or explicitly selected API
versions are called **removed** only if the supplied baseline contains them.
Otherwise findings describe absence from the selected target model set. Neither
result proves AWS retired a running service or invalidated older clients.

Dynamic service names/API versions, expanded `**kwargs`, resource construction
and unmodeled helpers receive review findings. Nested dictionaries, resource
actions, paginators, SDK customizations/extras, cross-module object flow and
dynamic control flow are not resolved. Loop targets, context-manager targets,
exception targets and conditional assignments that can replace an SDK binding
produce a manual-review finding; ambiguous calls are not classified as AWS
operations. Function-local assignments and import aliases shadow module bindings
throughout that function. The report counts recognized clients
and calls so zero coverage is visible. Syntax errors, unsafe model/source paths,
models over 32 MiB, more than 1,000 Python files or files over 1 MiB exit 2.
Tests use deliberately fictional service models to prove the comparison
algorithm; no AWS deprecation is invented to populate a demo.

## GitHub Actions template

```bash
python-pivot --no-banner action
python-pivot --no-banner action --out .github/workflows/python-compatibility.yml
python-pivot --no-banner action --out .github/workflows/python-compatibility.yml --apply
```

Preview prints the entire workflow and writes nothing, including when `--out`
is supplied. `--apply` exclusively creates a new file: it refuses existing
files, symlinks, missing parent directories and paths outside the current
directory. It does not commit, publish or
enable any automation remotely.

The [example workflow](../examples/github-actions/python-compatibility.yml)
expects this reviewed kit vendored into the application repository. Configure
`TOOLKIT_PATH`, `SOURCE_PATH` and `DEPENDENCY_FILE` for that repository before
enabling it. It installs the local toolkit, previews source changes and checks
dependency declarations with strict exit codes. It uses `contents: read`,
disables persisted checkout credentials, and contains no AWS authentication or
deploy/apply step. Installation uses the package index for build tooling; the
scanning steps do not access AWS. A review finding intentionally fails the job.
