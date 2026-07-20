---
title: "/lib64/libc.so.6: version `GLIBC_2.28' not found — fixing native Lambda dependency errors after a runtime upgrade"
canonical_url: https://eolkits.com/fix/lambda-glibc-version-not-found/
description: A native dependency (cryptography, numpy, pydantic-core, grpcio, psycopg2, or a Go/Rust binary) fails to import on Lambda with a GLIBC version error. Why it happens after a runtime bump and how to actually fix it.
tags: aws, lambda, python, node
---

You upgraded a Lambda runtime, redeployed, and a cold start now dies with something like:

```
/lib64/libc.so.6: version `GLIBC_2.28' not found (required by /var/task/some_native_lib.so)
```

or the Node equivalent through a native addon (`.node` file) failing to load. Nothing in your code changed — the error is coming from a compiled binary somewhere in your dependency tree, and it's a glibc mismatch, not a bug.

## Why this happens

Native extensions — `cryptography`, `numpy`, `pydantic-core`, `grpcio`, `psycopg2`, plus any Go or Rust binary bundled as a Lambda layer — link against the glibc of whatever machine built them. Lambda doesn't let you choose glibc independently; it's fixed by the runtime's base OS:

| Runtime family | Base OS | glibc |
|---|---|---|
| Amazon Linux 2 (`python3.9` and earlier, `nodejs16.x` and earlier) | AL2 | 2.26 |
| Amazon Linux 2023 (`python3.12`+, `nodejs18.x`+) | AL2023 | 2.34 |

If a wheel or `.so`/`.node` file was built on a newer box (a modern CI runner, a recent manylinux image, your own AL2023-based dev machine) and you deploy it to a function still running an AL2-based runtime, the loader looks for `GLIBC_2.28` (or whatever version the binary was linked against) and the AL2 base doesn't have it. Downgrading isn't possible — glibc is backward-compatible, not forward-compatible.

This shows up most often in exactly the situation a Lambda deprecation forces: you're mid-migration, some functions are already on `python3.12`/`nodejs22.x` and some aren't, dependencies get rebuilt/reinstalled by CI against the newer environment, and the *older* functions start failing on the next cold start even though you didn't touch their code.

## The fix

**Best fix — finish the runtime migration.** Move the function to an AL2023-based runtime (`python3.12`+, `nodejs20.x`+, `nodejs22.x`) so its glibc 2.34 satisfies modern wheels. This also gets the function off a runtime that's already deprecated or heading toward the block window — the actual root problem, not just this symptom.

**If you need one function to keep working on an older runtime for now:**

Build the dependency for the exact target instead of whatever your CI runner happens to ship:

```bash
pip install \
  --platform manylinux2014_x86_64 \
  --only-binary=:all: \
  --target ./package \
  <package>
```

`manylinux2014` targets glibc 2.17 — old enough to run on both AL2 (2.26) and AL2023 (2.34) runtimes, so this is the safe default when you need one build to work across both.

**Or build inside the actual Lambda base image**, so the binary links against the runtime's real glibc instead of a guess:

```bash
docker run --rm -v "$PWD":/var/task public.ecr.aws/lambda/python:3.9 \
  pip install -r requirements.txt -t /var/task/package
```

(swap the image tag for your target runtime — `python:3.12`, `nodejs:22`, etc.)

**Match the architecture, too.** `x86_64` and `arm64`/Graviton wheels are not interchangeable — a correct-glibc, wrong-architecture binary fails with a different but equally opaque error. If your function's `Architectures` is `arm64`, build for `arm64`.

## Finding every function affected before it happens in prod

Because this only shows up at import/cold-start time, it's easy to ship it and only find out when a cold Lambda instance spins up in production. Two ways to catch it ahead of time:

1. **Cold-start test locally against the exact base image** you deploy to (`docker run public.ecr.aws/lambda/<runtime> ...`), not just your dev machine's Python/Node.
2. **Audit for it at scan time.** If you're already tracking which functions sit on deprecated runtimes, the same pass can flag native-dependency ABI mismatches before a redeploy trips this — that's the kind of check that's more useful run across an account than one function at a time.

---

If you'd rather see which Lambda functions in your account carry this kind of native-dependency risk (plus deprecated-runtime exposure generally) without eyeballing every deployment package, the free **[EOLkits scanner](https://eolkits.com/scan)** checks an account in about 30 seconds — nothing uploaded, and I maintain it. Full reference for this exact error: **[eolkits.com/fix/lambda-glibc-version-not-found](https://eolkits.com/fix/lambda-glibc-version-not-found/)**.
