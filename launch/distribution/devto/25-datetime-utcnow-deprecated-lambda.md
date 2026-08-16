---
title: "DeprecationWarning: datetime.datetime.utcnow() is deprecated" — fixing the Python 3.12 warning in AWS Lambda
canonical_url: https://eolkits.com/fix/datetime-utcnow-deprecated/
description: Bumped your Lambda to python3.12 and now CloudWatch Logs is full of utcnow() DeprecationWarnings? Here's why it fires from boto3 even when you didn't write utcnow(), and the one-line fix.
tags: python, aws, lambda, serverless
---

The moment you bump a Lambda function to the `python3.12` runtime, CloudWatch Logs often starts showing warnings like this — once per cold start, or during your test suite against a Python 3.12 environment:

```
DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled
for removal in a future version. Use timezone-aware objects to represent
datetimes in UTC: datetime.datetime.now(datetime.UTC).
```

It doesn't crash your function. But it adds noise to every execution log, buries real errors, and points at a method that _will_ eventually be removed from the language. Here's the full picture — including why it often fires from `boto3` rather than your own code.

## Why Python 3.12 deprecated utcnow()

`datetime.datetime.utcnow()` returns a *naive* datetime — one with no timezone information attached (`tzinfo` is `None`). That sounds harmless until you try to compare it with an aware datetime, which most modern libraries return:

```python
import datetime

naive = datetime.datetime.utcnow()          # tzinfo=None
aware = datetime.datetime.now(datetime.timezone.utc)  # tzinfo=UTC

naive < aware  # TypeError: can't compare offset-naive and offset-aware datetimes
```

The naive result also serializes to JSON or a database without any indication that it represents UTC, making it indistinguishable from local time for downstream consumers.

Python 3.12 added the DeprecationWarning to every `utcnow()` and `utcfromtimestamp()` call. The exact removal version hasn't been announced, but the path is clear — Lambda runtimes track CPython releases, and deprecated functions get removed.

## The fix: one replacement per call site

| Old call | Python 3.9+ replacement | Python 3.11+ shorthand |
|---|---|---|
| `datetime.datetime.utcnow()` | `datetime.datetime.now(datetime.timezone.utc)` | `datetime.datetime.now(datetime.UTC)` |
| `datetime.datetime.utcfromtimestamp(ts)` | `datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)` | `datetime.datetime.fromtimestamp(ts, datetime.UTC)` |

`datetime.UTC` (the shorthand) was added in Python 3.11. If your package must stay compatible with Python 3.9 or 3.10 for local testing, use `datetime.timezone.utc` — it works identically everywhere Python 3.2+.

Both replacements return an *aware* datetime with `tzinfo=UTC`, so they compare correctly with any other aware datetime, serialize unambiguously, and pass ISO 8601 validation.

## Find every call in your deployment package

```bash
grep -r "utcnow\(\)\|utcfromtimestamp" . --include="*.py"
```

Run from your Lambda project root (or unzipped deployment package) to surface every call site — in your code and in vendored dependencies.

## Why the warning fires from boto3 even if you didn't write utcnow()

This is the part that surprises most developers. **botocore** — the low-level AWS SDK library that boto3 wraps — called `datetime.utcnow()` internally in several places, most visibly in its request-signing code (`auth.py`). Multiple GitHub issues tracked this across botocore versions (boto/botocore#3038, #3088, #3201, #3374).

AWS has shipped patches for these across botocore releases. The fastest fix is to upgrade:

```bash
pip install --upgrade boto3 botocore
```

Lambda's managed runtime bundles a pinned boto3/botocore. To get the newer version, include boto3 in your deployment package or a Lambda layer — it takes precedence over the bundled copy.

**If you use AWS Lambda Powertools**, the library fixed its own internal `utcnow()` calls. Upgrade to get the clean version:

```bash
pip install --upgrade aws-lambda-powertools
```

## Tracing which file is generating the warning

To get a full traceback pointing to the exact caller, set this Lambda environment variable:

```
PYTHONWARNINGS=error::DeprecationWarning
```

This turns every DeprecationWarning into an exception, so the next cold start logs a complete stack trace identifying the file and line. Remove the variable once you've traced and fixed the source.

## After the fix: confirm it's gone

The cleanest validation is to run your test suite with warnings promoted to errors:

```bash
python -W error::DeprecationWarning -m pytest
```

A clean run means no remaining `utcnow()` or `utcfromtimestamp()` calls in your code or vendored packages. If pytest surfaces new ones from a transitive dependency, open an upstream issue — or vendor a patched copy while the fix propagates.

## The broader context: python3.12 is the upgrade target

Lambda runtimes `python3.8`, `python3.9`, and `python3.10` are all deprecated and on track for create/update blocks in Q1 2027. The `python3.12` runtime is the recommended migration target — and the `utcnow()` warning is one of the cleanup items that comes with that upgrade, alongside the `distutils`, `imp`, and `asyncore` removals covered in separate guides.

Fixing it now is a one-liner per call site and leaves your logs clean for the signals that actually matter.

---

**Discovering deprecated runtimes across your whole AWS account?**  
[Run a free EOL scan at eolkits.com/scan](https://eolkits.com/scan) — paste your Terraform, SAM, CDK, or Serverless config and get a severity-sorted list of every deprecated runtime, AMI, and OS in under 60 seconds.
