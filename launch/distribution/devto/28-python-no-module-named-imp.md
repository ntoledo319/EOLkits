---
title: '"ModuleNotFoundError: No module named ''imp''" — fixing the Python 3.12 removal in AWS Lambda'
canonical_url: https://eolkits.com/fix/python-no-module-named-imp/
description: Moved your Lambda to python3.12 and seeing ModuleNotFoundError for imp? Python 3.12 removed it after 8 years of deprecation. Here's the importlib migration table and the two-minute fix.
tags: python, aws, lambda, serverless
---

The moment you flip a Lambda function to `python3.12`, CloudWatch Logs can show a cold-start crash like this:

```
[ERROR] Runtime.ImportModuleError: Unable to import module 'lambda_function':
No module named 'imp'
```

Your handler code never imported `imp` directly. Neither did you. But somewhere in your deployment package, a dependency did — and on the `python3.12` runtime, that module no longer exists.

## Why Python 3.12 removed imp

`imp` was Python's original low-level interface for the import system: functions like `imp.find_module`, `imp.load_source`, and `imp.reload` predated the modern `importlib` infrastructure by more than a decade.

Python deprecated `imp` in Python 3.4. Every import from Python 3.4 through 3.11 emitted a `DeprecationWarning`:

```
DeprecationWarning: the imp module is deprecated in favour of importlib and slated
for removal in Python 3.12; see the module's documentation for alternative uses
```

Python 3.12 made good on that warning. The module was fully removed — it is not present in any form on the `python3.12` Lambda runtime. The Python 3.12 changelog documents the removal directly:

> *imp* module — Use importlib instead.

Lambda's `python3.12` runtime reflects this: `import imp` throws `ModuleNotFoundError` at import time, and any function that pulls in `imp` through a dependency crashes before your handler code ever runs.

## Why the error comes from dependencies, not your code

Code you write today almost never calls `imp` — the DeprecationWarning has been present since Python 3.4 and modern tutorials use `importlib`. The imports that survive into production packages are in older third-party libraries:

- **Older testing or plugin frameworks** that dynamically loaded modules using `imp.load_source` or `imp.find_module`.
- **Legacy build tooling** such as older `setuptools` hooks, older `pytest` plugins, and older `distlib` versions that called `imp.get_magic()` to check bytecode headers.
- **Database migration tools** (Alembic, Django management commands) in very old pinned versions that used `imp.load_source` to load migration files by path.
- **Apache mod_python** and its derivatives, which use `imp` for module loading internally.
- **pywin32 and platform-specific helpers** that historically queried `imp.is_builtin`.

The pattern is always the same: a dependency was pinned to a version that was written before the 3.4 deprecation warning or never updated to resolve it.

## Find every imp import in your package

Run this from your project root or the unzipped deployment ZIP:

```bash
grep -r "import imp\b\|from imp import" . --include="*.py"
```

A match under `site-packages/` shows you which package to upgrade. The package directory name directly above the offending file is the one you need.

To confirm the import chain at runtime, set this Lambda environment variable temporarily:

```
PYTHONWARNINGS=error::DeprecationWarning
```

On a Python 3.11 or earlier environment this turns `imp` imports into hard errors immediately, giving you a full traceback that traces the import chain from your handler down to the exact offending file before you upgrade the runtime.

## The importlib migration table

If your own code (or a dependency you maintain) calls `imp`, here are the exact replacements:

| Old (`imp`) | New (`importlib`) |
|---|---|
| `import imp; imp.reload(module)` | `import importlib; importlib.reload(module)` |
| `imp.find_module(name)` | `importlib.util.find_spec(name)` (returns `ModuleSpec` or `None`) |
| `imp.load_source(name, path)` | `spec = importlib.util.spec_from_file_location(name, path)`<br>`mod = importlib.util.module_from_spec(spec)`<br>`spec.loader.exec_module(mod)` |
| `imp.new_module(name)` | `import types; types.ModuleType(name)` |
| `imp.get_magic()` | `importlib.util.MAGIC_NUMBER` |
| `imp.get_suffixes()` | `importlib.machinery.all_suffixes()` |
| `imp.is_builtin(name)` | `importlib.util.find_spec(name)` and check `spec.origin == 'built-in'` |

The `imp.load_source` → `spec_from_file_location` migration is the most common rewrite. The full three-line pattern looks like this in practice:

```python
import importlib.util

def load_module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
```

This is a direct drop-in for the old `imp.load_source(name, path)` call.

## For dependencies: upgrade them

If the offending import comes from a third-party package in `site-packages`, the fix is to upgrade it:

```bash
pip list --outdated              # find packages with newer releases
pip install --upgrade <package>  # upgrade the specific offender
```

Most actively maintained libraries patched their `imp` usage when Python 3.12 entered its release candidate phase. If a dependency still imports `imp` in its current release, check its issue tracker — there is often a PR or a fork that has resolved it.

After upgrading, rebuild and re-zip the deployment package and redeploy. Lambda reads the package you upload; it does not pick up `pip` changes made to a local environment.

## Confirm the fix before deploying

Test on a local Python 3.12 interpreter:

```bash
python3.12 -c "import lambda_function"
```

Or using the Lambda base image directly:

```bash
docker run --rm -v "$PWD":/var/task public.ecr.aws/lambda/python:3.12 \
  python3.12 -c "import lambda_function"
```

A clean import — no `ModuleNotFoundError` — means the package is ready to deploy.

## The broader context: python3.12 is the migration target

Lambda's `python3.9` runtime is deprecated (security patches stopped December 2025). `python3.10` and `python3.11` are on the path with create-block dates of 2027-02-01 and 2027-07-31 respectively, subject to AWS's standard extension policy. The `python3.12` runtime (Amazon Linux 2023, glibc 2.34) is the recommended upgrade target.

The `imp` removal is part of a cluster of breaking changes that land when you cross from `python3.9` to `python3.12`: `distutils` is also gone, the `collections` ABCs were moved to `collections.abc` in Python 3.10, and `asyncore`/`asynchat` are removed. Running a full upgrade sweep against a local Python 3.12 environment catches all of them in a single pass, rather than chasing one `ModuleNotFoundError` at a time after the runtime flip.

---

**Discovering deprecated runtimes across your whole AWS account?**  
The free **[EOLkits scanner](https://eolkits.com/scan)** checks your Terraform, SAM, CDK, or Serverless config and returns a severity-sorted list of every deprecated runtime and known dependency break in under 60 seconds. Nothing is uploaded.
