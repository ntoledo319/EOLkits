---
title: "AttributeError: module 'asyncio' has no attribute 'coroutine'" — fixing the Python 3.11 removal
canonical_url: https://eolkits.com/fix/python-asyncio-has-no-attribute-coroutine/
description: Python 3.11 removed the legacy @asyncio.coroutine decorator. Why old code (or a stale dependency) breaks on upgrade, and how to migrate to native async/await.
tags: python, aws, lambda, asyncio
---

You bumped a Lambda function (or any service) to Python 3.11 or later and something that used to run now dies on import or at call time with:

```
AttributeError: module 'asyncio' has no attribute 'coroutine'
```

Nothing about your business logic changed. A decorator your code — or a dependency your code imports — relies on simply isn't there anymore.

## Why this happens

`@asyncio.coroutine` was the generator-based way to write coroutines before Python got native `async`/`await` syntax in 3.5. It let a regular generator function (using `yield from` instead of `await`) act like a coroutine for the event loop.

Once `async def` became the standard, `@asyncio.coroutine` was kept around for backward compatibility, but it was **deprecated in Python 3.8** with an explicit `DeprecationWarning`, and then **removed outright in Python 3.11**. Calling `asyncio.coroutine` on 3.11+ doesn't warn — it fails immediately, because the attribute no longer exists on the module.

This tends to surface in two places:

1. **Old code in your own repo** written before `async`/`await` syntax was idiomatic, or copy-pasted from a pre-2018 tutorial.
2. **A dependency** that still ships generator-based coroutines internally and hasn't been updated for years.

Either way, it's a runtime-upgrade trigger, not a logic bug: the code was already deprecated-but-working on 3.8–3.10, and the 3.11 bump is what turns the warning into a hard failure.

## Fix — rewrite as native async/await

The generator-based pattern and the native one map directly onto each other.

**Before (removed in 3.11):**

```python
import asyncio

@asyncio.coroutine
def fetch_data(url):
    response = yield from some_legacy_fetch(url)
    return response
```

**After (native coroutine):**

```python
async def fetch_data(url):
    response = await some_legacy_fetch(url)
    return response
```

The mechanical rule: `@asyncio.coroutine` + `def` becomes `async def`; every `yield from` inside becomes `await`. If the function being awaited is itself still generator-based (`yield from` all the way down), it needs the same treatment — the conversion has to reach the bottom of the call chain, not just the outer function, or you'll hit a `TypeError` for awaiting a non-awaitable instead.

## If the code isn't yours

Run:

```bash
python3 -c "import asyncio; print(asyncio.__file__)"
grep -rn "asyncio.coroutine\|@coroutine" $(python3 -c "import site; print(site.getsitepackages()[0])")
```

or more simply, install the dependency into a Python 3.11+ virtualenv and see which import fails first — that's usually the exact package to upgrade. Most actively maintained async libraries dropped `@asyncio.coroutine` years before 3.11 removed it, so this is almost always solved by a `pip install --upgrade <package>`, not a patch you have to write yourself. Genuinely abandoned dependencies are the harder case: fork-and-fix, or find a maintained replacement before the runtime upgrade, not after.

## Catch it before the deploy, not after

Because the failure only fires when the affected code path actually runs, a quick smoke test on 3.11+ locally (or in CI, before flipping the Lambda runtime label) catches it long before a cold start does it for you in production:

```bash
python3.11 -W error::DeprecationWarning -c "import your_module"
```

Running with `-W error::DeprecationWarning` on your **current** runtime (3.9/3.10) first will also surface this and similar removals as warnings before you ever touch 3.11 — turning a hard failure after upgrade into a fixable warning before it.

---

This is one of several stdlib removals that show up as cryptic `AttributeError`s the moment a Lambda function moves off an EOL Python runtime — the free **[EOLkits scanner](https://eolkits.com/scan)** flags every deprecated runtime in an account in about 30 seconds, nothing uploaded, and I maintain it. Full reference for this exact error: **[eolkits.com/fix/python-asyncio-has-no-attribute-coroutine](https://eolkits.com/fix/python-asyncio-has-no-attribute-coroutine/)**.
