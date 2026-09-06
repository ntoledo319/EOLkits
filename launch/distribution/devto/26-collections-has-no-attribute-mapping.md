---
title: '"AttributeError: module ''collections'' has no attribute ''Mapping''" — fixing the Python 3.10 removal in AWS Lambda'
canonical_url: https://eolkits.com/fix/collections-has-no-attribute-mapping/
description: Jumping from python3.9 to python3.12 on Lambda? The collections.Mapping alias was silently removed in Python 3.10 — here's which packages trigger it, how to find every call site, and the one-line fix.
tags: python, aws, lambda, serverless
---

The moment you bump a Lambda function from `python3.9` to `python3.12`, CloudWatch Logs can surface a traceback you didn't write and a module you've never imported directly:

```
AttributeError: module 'collections' has no attribute 'Mapping'
```

Your code didn't change. The error is coming from a vendored dependency. Here's what happened and how to fix it in minutes.

## Why this error exists

Python's abstract base classes — `Mapping`, `MutableMapping`, `Sequence`, `Iterable`, `Callable`, `Iterator`, and others — have lived in `collections.abc` since Python 3.3. For backward compatibility, Python also kept them accessible directly as `collections.Mapping`, `collections.MutableMapping`, and so on.

That backward compatibility was deprecated with a `DeprecationWarning` in Python 3.9 and **fully removed in Python 3.10**. Any code that still does `collections.Mapping` (instead of `collections.abc.Mapping`) throws an `AttributeError` at import time on any runtime at or above Python 3.10.

Python's own What's New for 3.10 documents this under "Removed":

> Removed deprecated aliases to Abstract Base Classes from the `collections` module.

Lambda's `python3.9` runtime was many teams' last stop before the deprecation warnings became errors. When you jump straight from `python3.9` to `python3.12`, you skip the 3.10 cutoff entirely — and the first you hear about it is a cold-start crash.

## Which packages trigger it

The error almost never comes from your own code. It most often surfaces from a **pinned transitive dependency** that was written before 3.10 and hasn't been upgraded:

- **PyYAML** — older pinned versions (typically `<= 5.3`) used `collections.Mapping`. Upgrading to current PyYAML resolves it.
- **jsonschema** — older major versions imported directly from `collections`. Current releases use `collections.abc`.
- **celery**, **pymongo**, **marshmallow**, and other foundational libraries all had similar call sites that were patched in later releases.

The pattern is always the same: a dependency was pinned to a version that predates the Python 3.10 removal.

## Find every offending import

Run this from your project root (or the unzipped deployment package):

```bash
grep -r "collections\.Mapping\|collections\.MutableMapping\|collections\.Sequence\|collections\.Iterable\|collections\.Callable\|collections\.Iterator\|collections\.OrderedDict" . --include="*.py"
```

The full list of removed aliases from `collections` (as documented in Python 3.10's changelog) covers all the classic ABCs: `Awaitable`, `Coroutine`, `AsyncIterable`, `AsyncIterator`, `AsyncGenerator`, `Hashable`, `Iterable`, `Iterator`, `Generator`, `Reversible`, `Container`, `Collection`, `Callable`, `Set`, `MutableSet`, `Mapping`, `MutableMapping`, `MappingView`, `KeysView`, `ItemsView`, `ValuesView`, `Sequence`, `MutableSequence`, `ByteString`.

A hit in `site-packages/` inside your deployment bundle confirms the dependency path.

## The fix

**In your own code**, the replacement is a one-word change:

```python
# Before (broken on Python 3.10+)
from collections import Mapping

# After
from collections.abc import Mapping
```

The same pattern applies to every alias that was removed: swap `collections.` for `collections.abc.`. `collections.abc` has existed since Python 3.3, so this change is safe even on very old runtimes.

**For a dependency**, the fix is to upgrade it:

```bash
pip install --upgrade pyyaml jsonschema   # upgrade specific offenders
```

Or, if you're managing a `requirements.txt` lockfile:

```bash
pip list --outdated   # find packages with newer releases
```

After upgrading, rebuild and re-zip the deployment package. Lambda doesn't pick up dependency changes in-place.

## Trace the exact call stack

If the import chain is deep and the grep doesn't point to an obvious file, turn the warning into a hard traceback:

```bash
PYTHONFAULTHANDLER=1 python -W error::DeprecationWarning -c "import <your_handler_module>"
```

Or add this Lambda environment variable (remove it after debugging):

```
PYTHONWARNINGS=error::DeprecationWarning
```

The next cold start will log a full stack trace pointing to the exact file and line inside the dependency.

## The broader context: python3.12 is the migration target

Lambda runtimes `python3.9`, `python3.10`, and `python3.11` are all deprecated. AWS begins blocking *create* calls for these runtimes on **2027-02-01** (python3.9, 3.10) and **2027-07-31** (python3.11), and blocks *updates* shortly after each. The `python3.12` runtime — based on Amazon Linux 2023 — is the recommended migration target.

The `collections` alias removal is one of a cluster of cleanups that land when you cross from 3.9 to 3.12: `distutils` removed, `imp` removed, `asyncore`/`asynchat` removed, and `datetime.utcnow()` deprecated (with removal coming). Fixing pinned dependencies now rather than at the deadline means you catch all of these in a single upgrade sweep.

---

**Discovering deprecated runtimes across your whole AWS account?**  
[Run a free EOL scan at eolkits.com/scan](https://eolkits.com/scan) — paste your Terraform, SAM, CDK, or Serverless config and get a severity-sorted list of every deprecated runtime, AMI, and OS in under 60 seconds.
