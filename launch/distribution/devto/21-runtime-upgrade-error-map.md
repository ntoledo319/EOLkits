---
title: "The AWS runtime-upgrade error map: which errors you'll hit, in what order, for each migration path"
canonical_url: https://eolkits.com/fix/
description: A single map from "which deprecated AWS runtime am I leaving" to "which errors will I hit, in what order" — Python 3.9→3.12, Python→3.13, Node 18/20→22, and Amazon Linux 2→2023, each with the verified fix.
tags: aws, lambda, devops, python
---

> [!CAUTION]
> Archived launch copy — do not publish or reuse. This draft predates the current
> bounded browser scanner, telemetry disclosure, lifecycle-date corrections, and
> readiness-gated paid scope; claims and `eolkits.com` links below may be false or stale.
> Use the [current README](../../../README.md) and
> [verified public site](https://ntoledo319.github.io/EOLkits/) instead.

Every deprecated-runtime migration produces the same shape of pain: you bump one version number, redeploy, and get hit with errors that look unrelated to each other but are all downstream of the same jump. The errors aren't random — for a given upgrade path, they show up in a fairly predictable order.

This is a map, not a new deep dive. Each line below is a real, verbatim error with its own fix already written up — this just sequences them by *which upgrade produces them*, so you know what's coming before you hit it instead of debugging one surprise at a time.

## Path 1: Python 3.9 (or earlier) → Python 3.12 on Lambda

You're doing this because AWS blocks `python3.9` creates/updates Feb 1 / Mar 3 2027 (and earlier versions are already blocked). Python 3.12 removed a batch of stdlib modules in one release (PEP 632/594), so this path front-loads the most breakage:

1. **`ModuleNotFoundError: No module named 'distutils'`** — removed in 3.12. [Fix →](https://eolkits.com/fix/python-no-module-named-distutils/)
2. **`ModuleNotFoundError: No module named 'imp'`** — removed in 3.12. [Fix →](https://eolkits.com/fix/python-no-module-named-imp/)
3. **`AttributeError: module 'collections' has no attribute 'Mapping'`** — moved to `collections.abc` (removed from `collections` in 3.10, so this can also hit on the way to 3.10/3.11). [Fix →](https://eolkits.com/fix/collections-has-no-attribute-mapping/)
4. **`ModuleNotFoundError: No module named 'smtpd'`** — removed in 3.12. [Fix →](https://eolkits.com/fix/python-no-module-named-smtpd/)
5. **`ModuleNotFoundError: No module named 'asyncore'`** — removed in 3.12, usually alongside `smtpd`. [Fix →](https://eolkits.com/fix/python-no-module-named-asyncore/)
6. **`DeprecationWarning: datetime.datetime.utcnow() is deprecated`** — not fatal, but noisy, and worth fixing in the same pass. [Fix →](https://eolkits.com/fix/datetime-utcnow-deprecated/)
7. **`/lib64/libc.so.6: version 'GLIBC_2.28' not found`** — if you ship any native dependency (`cryptography`, `numpy`, `psycopg2`, `pydantic-core`), moving to the AL2023-based Python 3.12 runtime (glibc 2.34) from an AL2-based one (glibc 2.26) can surface this separately from the stdlib removals above. [Fix →](https://eolkits.com/fix/lambda-glibc-version-not-found/)

## Path 2: Python 3.11/3.12 → Python 3.13

A second, smaller PEP 594 wave hits on the next hop:

1. **`ModuleNotFoundError: No module named 'cgi'`** — removed in 3.13. [Fix →](https://eolkits.com/fix/python-no-module-named-cgi/)
2. **`ModuleNotFoundError: No module named 'telnetlib'`** — removed in 3.13. [Fix →](https://eolkits.com/fix/python-no-module-named-telnetlib/)
3. **`ModuleNotFoundError: No module named 'crypt'`** — removed in 3.13. [Fix →](https://eolkits.com/fix/python-no-module-named-crypt/)
4. **`ModuleNotFoundError: No module named 'lib2to3'`** — removed in 3.13. [Fix →](https://eolkits.com/fix/python-no-module-named-lib2to3/)

And one that hits on the way *into* 3.11, if you skipped straight past it:

- **`AttributeError: module 'asyncio' has no attribute 'coroutine'`** — the legacy `@asyncio.coroutine` decorator, removed in 3.11. [Fix →](https://eolkits.com/fix/python-asyncio-has-no-attribute-coroutine/)

## Path 3: Node.js 16/18 → Node.js 20/22 on Lambda

This path is less about stdlib removals and more about what the runtime stopped bundling and what OpenSSL 3 stopped allowing:

1. **`Error: Cannot find module 'aws-sdk'`** — AWS SDK v2 stopped shipping preinstalled from `nodejs18.x` onward; only `@aws-sdk/*` v3 is preinstalled now. This is usually the *first* error you hit, at cold start. [Fix →](https://eolkits.com/fix/node-cannot-find-module-aws-sdk/)
2. **`Error: error:0308010C:digital envelope routines::unsupported`** — OpenSSL 3 (bundled from Node 17+) rejecting a legacy hash, often from an older build tool (webpack 4). [Fix →](https://eolkits.com/fix/node-error-digital-envelope-routines-unsupported/)
3. **`error:1E08010C:DECODER routines::unsupported`** — OpenSSL 3 refusing to load a private key stored in a legacy format (PKCS#1, or encrypted with a weak cipher). [Fix →](https://eolkits.com/fix/node-error-decoder-routines-unsupported/)
4. **`Error: The module was compiled against a different Node.js version using NODE_MODULE_VERSION`** — any native addon (`sharp`, `bcrypt`, `better-sqlite3`) needs a rebuild for the new ABI. [Fix →](https://eolkits.com/fix/node-module-version-mismatch/)
5. **`Node Sass does not yet support your current environment`** — node-sass specifically, since LibSass is dead and ships no Node 22 prebuild. [Fix →](https://eolkits.com/fix/node-sass-deprecated-unsupported/)
6. **`TypeError: crypto.createCipher is not a function`** — `createCipher`/`createDecipher` were removed outright in Node 22 (not just deprecated). [Fix →](https://eolkits.com/fix/node-crypto-createcipher-is-not-a-function/)
7. **`[DEP0040] DeprecationWarning: The 'punycode' module is deprecated`** — not fatal, usually from a transitive dependency, loudest on Node 22. [Fix →](https://eolkits.com/fix/node-punycode-module-deprecated/)

If none of the above matches and you're just staring at a bare `Runtime.ImportModuleError: Cannot find module`, the cause could be any of #1 or #4 above, an esbuild `0.22+` bundling default change, or a Lambda layer built on the wrong OS/arch — see the dedicated [triage guide](https://eolkits.com/fix/lambda-runtime-importmoduleerror-cannot-find-module/) to tell them apart before guessing.

## Path 4: Amazon Linux 2 → Amazon Linux 2023

AL2 reached end of life June 30, 2026. This path isn't a Lambda runtime change at all — it's the base OS on EC2/ECS/EKS nodes — but it produces the same "one version bump, five unrelated-looking failures" shape:

1. **`amazon-linux-extras: command not found`** — the Extras Library mechanism doesn't exist on AL2023 at all. [Fix →](https://eolkits.com/fix/amazon-linux-extras-command-not-found/)
2. **`Error: Unable to find a match: <package>`** — package renamed, version-namespaced, moved to SPAL, or dropped. [Fix →](https://eolkits.com/fix/amazon-linux-2023-dnf-unable-to-find-a-match/)
3. **`Failed to start ntpd.service: Unit ntpd.service not found`** — AL2023 uses `chronyd`. [Fix →](https://eolkits.com/fix/amazon-linux-2023-ntpd-service-not-found/)
4. **`Failed to start iptables.service: Unit iptables.service not found`** — AL2023 defaults to nftables. [Fix →](https://eolkits.com/fix/amazon-linux-2023-iptables-service-not-found/)
5. **`/usr/bin/env: 'python2': No such file or directory`** — AL2023 ships no Python 2 at all. [Fix →](https://eolkits.com/fix/amazon-linux-2023-python2-command-not-found/)

## Why this exists as one page

Each fix above already has its own full write-up — root cause, verified fix steps, primary source. What's usually missing when you're mid-migration isn't any single fix, it's *knowing what's coming next* so you can batch the work instead of playing whack-a-mole one redeploy at a time. Bookmark whichever path applies to you and work down it in order.

Not sure which path even applies to you? Paste your runtimes into the free **[EOL checker](https://eolkits.com/eol-checker/)** for a 10-second answer against the same table AWS enforces — nothing uploaded. If you'd rather have this run against your actual account instead of reading it, the free **[EOLkits scanner](https://eolkits.com/scan)** checks in about 30 seconds, nothing uploaded — I maintain both, disclosing that plainly since these are the two links in this piece that aren't fixes.
