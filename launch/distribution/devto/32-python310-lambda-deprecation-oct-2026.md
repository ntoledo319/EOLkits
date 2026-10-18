---
title: "python3.10 Lambda deprecated October 31, 2026 — the exact upgrade path to python3.12"
canonical_url: https://eolkits.com/migrate/lambda-python-3.10-eol/
description: python3.10 Lambda deprecates Oct 31, 2026 — security patches stop, but create-block isn't until Jul 29, 2027. Here's what breaks upgrading to python3.12, and the one stdlib error that won't hit 3.10 teams.
tags: python, aws, lambda, serverless
---

AWS Lambda's `python3.10` runtime reaches deprecation on **October 31, 2026**. Here's what actually changes, what breaks on the upgrade to `python3.12`, and one piece of the standard "upgrade from Python 3.x" advice that doesn't apply if you're starting from 3.10.

## What "deprecated" means (and doesn't mean)

Deprecation is not a deploy block. Per the [AWS Lambda runtime deprecation table](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html):

| Phase | python3.10 date |
|---|---|
| Deprecation (security patches stop) | **Oct 31, 2026** |
| Block function create | **Jul 29, 2027** |
| Block function update | **Aug 31, 2027** |

After October 31 you can still invoke, create, and update `python3.10` functions — you just won't receive security patches for the Python runtime or its underlying Amazon Linux 2 OS. That unpatched exposure is the real cost, not an immediate API rejection.

## The target: python3.12

`python3.12` is the recommended upgrade target: it runs on Amazon Linux 2023, and its own deprecation isn't scheduled until October 2028. The one-line change is `Runtime: python3.12` (SAM/CloudFormation), `lambda.Runtime.PYTHON_3_12` (CDK), or `runtime = "python3.12"` (Terraform). The harder part is the imports that break after.

## What breaks on the python3.10 → python3.12 jump

These are hard `ModuleNotFoundError` crashes at cold start, not warnings. They fire the first time the function is invoked after the runtime label changes.

**`ModuleNotFoundError: No module named 'distutils'`**
Removed in Python 3.12 (PEP 632). The source is almost always a transitive dependency, not code you wrote directly. Durable fix: replace `distutils` APIs with `setuptools` and the `packaging` library (`packaging.version.Version` instead of `distutils.version.LooseVersion`). Upgrade any dependency that still imports it. [Full fix →](https://eolkits.com/fix/python-no-module-named-distutils/)

**`ModuleNotFoundError: No module named 'imp'`**
Removed in Python 3.12. Replace with `importlib`: `importlib.util.find_spec`, `importlib.import_module`, and `importlib.machinery` cover the common `imp` entry points. Upgrade stale dependencies that still import `imp`. [Full fix →](https://eolkits.com/fix/python-no-module-named-imp/)

**`ModuleNotFoundError: No module named 'smtpd'`**
Removed in Python 3.12 (PEP 594). If your code (or a dependency) used `smtpd.DebuggingServer` or a similar class, replace with [`aiosmtpd`](https://pypi.org/project/aiosmtpd/) — an asyncio-native drop-in that the Python docs point to as the maintained successor. [Full fix →](https://eolkits.com/fix/python-no-module-named-smtpd/)

**`ModuleNotFoundError: No module named 'asyncore'`**
Removed in Python 3.12 (PEP 594), typically alongside `asynchat`. The intended replacement is `asyncio` transports and protocols. If a third-party library is the importer, check whether it has an asyncio-based release before patching around it. [Full fix →](https://eolkits.com/fix/python-no-module-named-asyncore/)

**`DeprecationWarning: datetime.datetime.utcnow() is deprecated`**
New in Python 3.12 — not a crash, but it logs on every invocation. Replace with `datetime.datetime.now(datetime.timezone.utc)`. Worth fixing in the same pass before it becomes a hard error on a future runtime. [Full fix →](https://eolkits.com/fix/datetime-utcnow-deprecated/)

## The one error that won't hit python3.10 teams

Most Python → 3.12 upgrade guides lead with this:

```
AttributeError: module 'collections' has no attribute 'Mapping'
```

That was a **Python 3.10** removal. The abstract base class aliases (`collections.Mapping`, `collections.Sequence`, and others) were removed from `collections` in 3.10, moved to `collections.abc`. If you've been running `python3.10` in production, you already dealt with this — either your code was migrated, or it was already broken and has been fixed. It won't surface again on the jump to 3.12. Skip that step.

(It *will* hit teams upgrading directly from `python3.9` to `python3.12`, which is why most upgrade guides list it prominently. The guides are written for the combined audience.)

## The glibc change: native dependencies need a rebuild

`python3.10` runs on Amazon Linux 2, which ships `glibc 2.26`. `python3.12` runs on Amazon Linux 2023, which ships `glibc 2.34`. If your deployment package includes any native extension — `cryptography`, `numpy`, `psycopg2-binary`, `pydantic-core`, `grpcio`, `Pillow` — and it was built against AL2, it won't load on the new base:

```
/lib64/libc.so.6: version `GLIBC_2.28' not found
```

Fix: rebuild for the AL2023 target. The most portable approach:

```bash
pip install \
  --platform manylinux2014_x86_64 \
  --only-binary=:all: \
  --target ./package \
  <package>
```

Or build inside the official Lambda image:

```bash
docker run --rm \
  -v $(pwd):/var/task \
  public.ecr.aws/lambda/python:3.12 \
  pip install -r requirements.txt -t /var/task/package
```

Match the architecture too — an x86_64 wheel won't load on an arm64 function and vice versa. [Full fix →](https://eolkits.com/fix/lambda-glibc-version-not-found/)

## Check your functions before the deprecation date

Run `python3.12 -c "import your_handler_module"` locally with your packages installed before you change the runtime label. Every `ModuleNotFoundError` above surfaces at import time — you'll see all of them in one shot instead of fixing them one cold-start at a time in production.

The free **[EOLkits scanner](https://eolkits.com/scan)** flags every deprecated Lambda runtime across your account in about 30 seconds — nothing uploaded. Full migration timeline and per-error fix index: **[eolkits.com/migrate/lambda-python-3.10-eol](https://eolkits.com/migrate/lambda-python-3.10-eol/)**.
