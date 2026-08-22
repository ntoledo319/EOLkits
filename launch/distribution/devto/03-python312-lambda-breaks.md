---
title: Python 3.12 on AWS Lambda — distutils, imp, and collections are gone
canonical_url: https://eolkits.com/migrate/lambda-python-3.9-eol/
description: Moving AWS Lambda to python3.12? distutils, imp, and the collections ABCs were removed. The exact errors and the fixes, plus the native-wheel/glibc gotcha.
tags: aws, lambda, python, serverless
---

AWS Lambda's `python3.9`, `3.10`, and `3.11` runtimes are on the deprecation track; `python3.12` (on Amazon Linux 2023) is the target. The runtime swap is one line — but Python 3.12 itself removed a pile of long-deprecated stdlib, so code that ran on 3.9 throws on import.

## The removals you'll hit

**`ModuleNotFoundError: No module named 'distutils'`** — removed in 3.12 (PEP 632). Replace with `setuptools` + `packaging` (e.g. `packaging.version.Version` instead of `distutils.version.LooseVersion`). Interim: `pip install 'setuptools<81'` (still vendors a shim).

**`ModuleNotFoundError: No module named 'imp'`** — removed in 3.12. Use `importlib` (`importlib.util.find_spec`, `import_module`).

**`AttributeError: module 'collections' has no attribute 'Mapping'`** — the ABCs moved to `collections.abc` (removed from `collections` in 3.10). `from collections.abc import Mapping`.

**`DeprecationWarning: datetime.datetime.utcnow() is deprecated`** — use `datetime.now(datetime.timezone.utc)`.

## The one that isn't in your code

```
/lib64/libc.so.6: version `GLIBC_2.28' not found
```

Native wheels (cryptography, numpy, pydantic-core…) link against the glibc of the box that built them. AL2 runtimes ship glibc 2.26; AL2023 (python3.12) ships 2.34. Build for the target: `pip install --platform manylinux2014_x86_64 --only-binary=:all: --target ./package <pkg>`, or build inside `public.ecr.aws/lambda/python:3.12`. Match the arch (x86_64 vs arm64) too.

## When AWS blocks you

```
The runtime parameter of python3.9 is no longer supported for creating or updating AWS Lambda functions
```

That's the block date. Set `Runtime: python3.12` (SAM/CFN), `lambda.Runtime.PYTHON_3_12` (CDK), or `runtime = "python3.12"` (Terraform), fix the imports above, redeploy.

---

The free **[EOLkits scanner](https://eolkits.com/scan)** flags every deprecated runtime and the dependency breaks above from your `requirements.txt` / `pyproject.toml` / IaC — in your browser, nothing uploaded. There's an MIT CLI (`python-pivot`) that codemods most of it, and a hash-anchored audit if you want it scored and done for you.

Cited deadlines + per-error fixes: **[eolkits.com/migrate](https://eolkits.com/migrate/)** · **[eolkits.com/fix](https://eolkits.com/fix/)**
