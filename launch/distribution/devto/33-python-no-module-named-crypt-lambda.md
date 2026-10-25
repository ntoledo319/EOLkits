---
title: '"ModuleNotFoundError: No module named ''crypt''" — fixing password hashing on Python 3.13 Lambda'
canonical_url: https://eolkits.com/fix/python-no-module-named-crypt/
description: Bumped your Lambda to python3.13 and seeing a cold-start crash about crypt? PEP 594 removed it in Python 3.13. Here's the exact replacement for each use case — and the native-wheel gotcha.
tags: python, aws, lambda, serverless
---

Switch a Lambda function to `python3.13` and the first cold start may produce this:

```
[ERROR] Runtime.ImportModuleError: Unable to import module 'lambda_function':
No module named 'crypt'
```

or, if the import is deeper in a dependency:

```
ModuleNotFoundError: No module named 'crypt'
```

Your handler probably never called `crypt` by name. But something in your dependency tree did — and on the `python3.13` runtime, the module is simply gone.

## Why Python 3.13 removed crypt

`crypt` was a thin wrapper around the Unix C library's `crypt(3)` function: it could hash a password with DES, MD5, SHA-256, SHA-512, or Blowfish, depending on what the host OS provided. Useful in 1998; dangerous in 2025. The algorithm selection was implicit, DES support was still present in some environments, and the module had no maintained upstream.

[PEP 594](https://peps.python.org/pep-0594/) deprecated `crypt` in Python 3.11 and removed it in Python 3.13, along with 18 other long-unmaintained standard library modules. Python 3.12 is the last release that ships it. The `python3.13` Lambda runtime (available since November 2024, running on Amazon Linux 2023) has no `crypt`.

There is no drop-in stdlib replacement. The Python core team's intent was to push code toward modern, maintained password-hashing libraries — the right call from a security standpoint.

## Which scenario are you in?

The fix differs depending on whether you are **creating new hashes** or **verifying old ones**.

### Scenario 1: You are creating new password hashes

If your code hashes passwords for storage, this is an opportunity to use a modern algorithm. Drop `crypt` entirely and pick one of these:

**`hashlib.scrypt` — zero new dependencies**

`hashlib.scrypt` is in the Python standard library and produces memory-hard hashes that resist GPU cracking. No pip install, no native extension, no Lambda packaging issue.

```python
import hashlib, os

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return salt.hex() + ":" + key.hex()

def verify_password(password: str, stored: str) -> bool:
    salt_hex, key_hex = stored.split(":")
    salt = bytes.fromhex(salt_hex)
    key = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return key.hex() == key_hex
```

Tune `n`, `r`, `p` for your workload; `n=2**14, r=8, p=1` is a reasonable Lambda-safe starting point. Raise `n` to `2**16` or `2**17` if you can afford the memory.

**`bcrypt` or `argon2-cffi` — if you want the ecosystem standard**

Both are mature and actively maintained. The tradeoff versus `hashlib.scrypt`: they are native C extensions that require a compiled wheel. On Lambda, that means building for Amazon Linux 2023 (the `python3.13` base OS). The most portable build approach:

```bash
pip install \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.13 \
  --only-binary=:all: \
  --target ./package \
  bcrypt
```

Or build inside the official Lambda container to be certain:

```bash
docker run --rm \
  -v $(pwd):/var/task \
  public.ecr.aws/lambda/python:3.13 \
  pip install -r requirements.txt -t /var/task/package
```

A wheel built on your developer machine (macOS or Ubuntu 22.04) will fail at Lambda cold start with a glibc mismatch — see [/fix/lambda-glibc-version-not-found/](https://eolkits.com/fix/lambda-glibc-version-not-found/) for detail.

### Scenario 2: You are verifying existing crypt(3) hashes

If you store hashes that `crypt` produced (typically `$6$...` SHA-512 or `$5$...` SHA-256 prefixed strings) and need to keep verifying them while migrating, `passlib` is the correct tool. It implements the crypt(3) hash schemes independently of the stdlib module:

```python
from passlib.hash import sha512_crypt

# Verify a stored crypt(3) hash
stored_hash = "$6$rounds=5000$salt$..."
is_valid = sha512_crypt.verify(plaintext_password, stored_hash)

# Hash a new password in the same scheme (during a migration window)
new_hash = sha512_crypt.hash(plaintext_password)
```

`passlib` is a pure-Python library — no native extension, no AL2023 build concern. Add it to `requirements.txt` and rebuild normally.

While `passlib` lets you keep verifying old hashes, plan to re-hash users to a stronger scheme (bcrypt or scrypt) on their next successful login. `sha512_crypt` hashes from the stdlib era are salted and slow-ish by crypt(3) standards, but bcrypt and scrypt are better choices going forward.

## The quick summary

| If you need to… | Use | Native? |
|---|---|---|
| Hash new passwords, zero deps | `hashlib.scrypt` | No |
| Verify existing `$5$` / `$6$` hashes | `passlib` | No |
| New hashing, bcrypt ecosystem | `bcrypt` | **Yes — build for AL2023** |
| New hashing, Argon2 | `argon2-cffi` | **Yes — build for AL2023** |

## Before you redeploy

1. Search your codebase and dependencies for `import crypt` or `from crypt import`.
2. Pick the replacement that matches your scenario above.
3. If you chose a native library, rebuild the deployment package inside the Lambda `python3.13` base image.
4. Run `python3 -c "import <your_handler_module>"` inside the build container before zipping — every cold-start crash in this class of errors is visible at import time.
5. Watch the first cold start in CloudWatch Logs to confirm the `Runtime.ImportModuleError` is gone.

This is one of 19 modules removed by PEP 594 in Python 3.13. If you also hit `audioop`, `telnetlib`, `cgitb`, `aifc`, or others from the same batch, they all land on the same `python3.13` runtime upgrade and surface in one shot when you import your handler.

---

[EOLkits](https://eolkits.com/scan) can scan your Lambda functions and flag runtimes and dependencies with known compatibility issues before you flip the runtime switch.
