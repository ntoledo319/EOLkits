---
title: Python 3.13 on AWS Lambda — cgi, telnetlib, crypt, lib2to3 removed (PEP 594)
canonical_url: https://eolkits.com/migrate/lambda-python-3.11-eol/
description: Upgrading to python3.13 on Lambda? PEP 594 removed cgi, telnetlib, crypt, lib2to3, and 15 more stdlib modules in Python 3.13. The exact import errors and fixes.
tags: aws, python, lambda, serverless
---

AWS Lambda launched the `python3.13` runtime in November 2024 — Amazon Linux 2023, Python 3.13.x, LTS support through October 2029. If you're still on `python3.9` or `python3.10`, the create-block deadline hits **2027-02-01**; `python3.11` create-blocks at **2027-07-31**. Many teams are jumping straight to `python3.13` to bank the longest runway.

What bites them isn't the runtime label change. It's **PEP 594** — the "dead batteries" cleanup that deprecated 19 stdlib modules in Python 3.11 (warnings only) and **deleted all of them in Python 3.13**. Cold start, hard crash, `ModuleNotFoundError`. Here are the four that actually appear in Lambda functions and their transitive dependencies.

## `ModuleNotFoundError: No module named 'cgi'`

The `cgi` and `cgitb` modules are gone in Python 3.13.

```python
# Breaks on python3.13
from cgi import parse_qs, FieldStorage, escape
import cgitb; cgitb.enable()
```

**Fixes:**

- `cgi.parse_qs` / `cgi.parse_qsl` → `urllib.parse.parse_qs` / `urllib.parse.parse_qsl`
- `cgi.escape` → `html.escape`
- Multipart form parsing (`FieldStorage`) → `multipart` library, or your framework's built-in (`werkzeug.formparser`, `starlette.requests.Request.form()`, etc.)
- Drop `cgitb.enable()` — use structured logging (`logging.exception`) instead

The most common place this surfaces in Lambda is a dependency that still imports `cgi` for query-string parsing — `pip show -f <package>` to locate it, then upgrade.

## `ModuleNotFoundError: No module named 'telnetlib'`

```python
import telnetlib  # removed in Python 3.13
tn = telnetlib.Telnet("host", 23)
```

**Fixes:**

- **Network/device automation:** replace with [`telnetlib3`](https://pypi.org/project/telnetlib3/) (asyncio-native, maintained) or `Exscript`.
- **Better:** switch to SSH where the device supports it — `paramiko` or `netmiko`.
- Pinning to `python3.12` still includes `telnetlib`, but `python3.12` itself will eventually deprecate — treat that as a stopgap, not a fix.

## `ModuleNotFoundError: No module named 'crypt'`

The Unix password-hashing module was removed because its underlying algorithms (DES-crypt, MD5-crypt) are cryptographically broken and belong nowhere near new code.

```python
import crypt
hashed = crypt.crypt("password", crypt.mksalt(crypt.METHOD_SHA512))
```

**Fixes:**

- **New password hashing:** `passlib` (`bcrypt`, `argon2-cffi`) or `hashlib.scrypt` / `hashlib.pbkdf2_hmac`.
- **Verify existing `crypt(3)` hashes:** `passlib.hash.sha512_crypt.verify(password, stored_hash)` — it implements the same crypt(3) schemes so you can verify old hashes during a migration window.
- There is no stdlib drop-in replacement. Don't reach for `hashlib.md5` — that's not a password hash.

This one shows up most often in provisioning scripts and user-management Lambda functions inherited from old EC2 tooling.

## `ModuleNotFoundError: No module named 'lib2to3'`

`lib2to3` (and the `2to3` command-line tool) were removed because the internal grammar couldn't track new Python syntax — it was itself becoming obsolete.

```python
from lib2to3 import pygram, pytree  # gone in Python 3.13
```

**Fixes:**

- Code parsing/transformation: [`LibCST`](https://libcst.readthedocs.io/) or `parso`.
- If this comes from a dependency (build tools, older linters, `black < 24`), upgrade it — modern versions have already removed the `lib2to3` dependency.
- For a one-off Python 2→3 migration: run `2to3` from a Python ≤ 3.12 environment before upgrading the runtime.

## Grep your dependencies before deploying

PEP 594 removed 19 modules in total. The four above are the ones that appear in Lambda workloads, but also removed were: `aifc`, `audioop`, `chunk`, `cgitb`, `imghdr`, `mailcap`, `msilib`, `nis`, `nntplib`, `ossaudiodev`, `pipes`, `sndhdr`, `spwd`, `sunau`, `uu`, `xdrlib`.

A quick scan before you flip the runtime:

```bash
# Run from your virtualenv or package directory
python3.13 -c "
import importlib, sys
dead = ['cgi','cgitb','telnetlib','crypt','lib2to3','aifc','audioop',
        'chunk','imghdr','mailcap','nis','nntplib','ossaudiodev',
        'pipes','sndhdr','sunau','uu','xdrlib']
for m in dead:
    try:
        importlib.import_module(m)
        print(f'WARN: {m} somehow importable')
    except ModuleNotFoundError:
        pass
print('Scan complete')
"
```

Better yet, test your handler locally on a Python 3.13 environment before deploying to Lambda. The errors above are cold-start killers — they won't appear until the function is invoked.

## Timeline recap

| Runtime | Deprecated | Create blocked | Update blocked |
|---|---|---|---|
| `python3.9` | 2025-12-15 | 2027-02-01 | 2027-03-03 |
| `python3.10` | 2026-03-31 | 2027-02-01 | 2027-03-03 |
| `python3.11` | 2027-06-30 | 2027-07-31 | 2027-08-31 |
| `python3.12` | not yet deprecated | — | — |
| `python3.13` | not yet deprecated | — | — |

Sources: [AWS Lambda runtime deprecation table](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html), [Python 3.13 What's New](https://docs.python.org/3/whatsnew/3.13.html), [PEP 594](https://peps.python.org/pep-0594/).

---

The free **[EOLkits scanner](https://eolkits.com/scan)** detects deprecated Lambda runtimes and flags known packages that still import the removed modules — in your browser, nothing uploaded. Full per-error fixes and the migration deadline timeline: **[eolkits.com/migrate/lambda-python-3.11-eol](https://eolkits.com/migrate/lambda-python-3.11-eol/)**.
