---
title: '"ModuleNotFoundError: No module named ''distutils''" — fixing the Python 3.12 removal in AWS Lambda'
canonical_url: https://eolkits.com/fix/python-no-module-named-distutils/
description: Bumped your Lambda to python3.12 and seeing ModuleNotFoundError for distutils? PEP 632 removed it. Here's why it fires from dependencies you didn't write, and the two-step fix.
tags: python, aws, lambda, serverless
---

The moment you bump a Lambda function from `python3.9` or `python3.10` to `python3.12`, you may see this in CloudWatch Logs on the first cold start:

```
[ERROR] Runtime.ImportModuleError: Unable to import module 'lambda_function':
No module named 'distutils'
```

Your handler code never touched `distutils`. But a vendored dependency in your deployment package does — and on the `python3.12` runtime, that module is gone.

## Why Python 3.12 removed distutils

`distutils` was Python's original build system, part of the standard library since Python 1.6. PEP 632 deprecated it in Python 3.10 and removed it entirely in Python 3.12. The module is now completely absent from the CPython standard library — not in a deprecated state, not soft-deprecated with a warning, just gone.

The official Python 3.12 changelog documents the removal:

> *distutils* — the entire package was removed in Python 3.12 following its deprecation in 3.10.

Lambda's `python3.12` runtime reflects this: `import distutils` raises `ModuleNotFoundError`, and any package that does this import — directly or through a sub-import — kills your function at cold-start time.

## Why the error comes from dependencies, not your code

The imports that survive in production packages are almost always in vendored third-party dependencies, not code you wrote:

- **Older `setuptools` versions** used `distutils` internally; setuptools began shipping its own bundled copy of distutils, but the shim was dropped in setuptools 81.
- **Older numpy build tooling** (`numpy.distutils`) relied on the stdlib version.
- **`pkg_resources`** (part of setuptools ≤60) and some tools that introspect installed packages used `distutils.version.LooseVersion`.
- **Packaging scripts** copied before the 3.10 deprecation warning was added — things like `setup.py` files that ship with dependencies.

The pattern is always the same: a dependency was pinned to a version from before the removal, and nobody tested it on a Python 3.12 environment until the runtime flip.

## Find every distutils import in your package

Run this from your project root — or from the unzipped deployment ZIP or Lambda layer:

```bash
grep -r "import distutils\|from distutils" . --include="*.py"
```

A match under `site-packages/` confirms the dependency path. Use the enclosing directory name to identify which package to upgrade.

## Fix 1: Interim — bundle setuptools (for the shim)

If you can't immediately upgrade the offending dependency, the fastest unblock is to include an explicit `setuptools` pin in your deployment package. Setuptools shipped a bundled `distutils` shim for years; the shim was present up through setuptools 80.x:

```text
# requirements.txt
setuptools<81
```

Then rebuild and redeploy:

```bash
pip install -r requirements.txt --target ./package
zip -r function.zip ./package lambda_function.py
```

The bundled setuptools takes precedence over the absent stdlib distutils. **Treat this as temporary** — test the durable fix (upgrading the dependency) before the next deployment.

## Fix 2: Durable — upgrade or replace distutils call sites

**In your own code**, the replacements are direct:

| Old (`distutils`) | New (standard) |
|---|---|
| `distutils.version.LooseVersion` | `packaging.version.Version` (`pip install packaging`) |
| `distutils.version.StrictVersion` | `packaging.version.Version` |
| `distutils.spawn.find_executable` | `shutil.which` |
| `distutils.dir_util.copy_tree` | `shutil.copytree` |
| `distutils.util.strtobool` | `bool(s.lower() in ('y','yes','1','true','on'))` |

**For dependencies**, upgrade them:

```bash
pip list --outdated          # find packages with newer releases
pip install --upgrade numpy setuptools pkg_resources
```

Most maintained packages patched their `distutils` imports when Python 3.12 entered beta. If a dependency has no fix in a current release, open an issue — or replace it with a maintained alternative and rebuild.

## Confirm the fix before deploying

Test locally on a Python 3.12 interpreter:

```python
python3.12 -c "import lambda_function"
```

Or, if you use a Lambda-equivalent base image:

```bash
docker run --rm -v "$PWD":/var/task public.ecr.aws/lambda/python:3.12 \
  python3.12 -c "import lambda_function"
```

A clean import — no `ModuleNotFoundError` — means the package is safe to deploy.

## The broader context: python3.12 is the migration target

Lambda's `python3.9` and `python3.10` runtimes are deprecated; `python3.9` has no further security patches since December 2025. AWS is scheduled to block new function creation on deprecated runtimes in early 2027. The `python3.12` runtime (Amazon Linux 2023, glibc 2.34) is the recommended upgrade target.

The `distutils` removal is one of a cluster of breaking changes you'll hit when crossing from 3.9 to 3.12: `imp` is also gone, `asyncore` and `asynchat` are gone, and `datetime.utcnow()` is deprecated. Fixing pinned dependencies once — in a full upgrade sweep against a local Python 3.12 environment — is faster than chasing individual errors after the runtime flip.

---

**Discovering deprecated runtimes across your whole AWS account?**  
[Run a free EOL scan at eolkits.com/scan](https://eolkits.com/scan) — paste your Terraform, SAM, CDK, or Serverless config and get a severity-sorted list of every deprecated runtime and known dependency break in under 60 seconds.
