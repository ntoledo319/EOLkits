---
title: "ModuleNotFoundError: No module named 'smtpd'" / "'asyncore'" — Python 3.12's PEP 594 stdlib cleanup
canonical_url: https://eolkits.com/fix/python-no-module-named-smtpd/
description: Python 3.12 removed smtpd, asyncore, and asynchat from the standard library. Why old Lambda code breaks on the runtime bump, and the replacement for each.
tags: python, aws, lambda, migration
---

You moved a Lambda function (or any service) to the python3.12 runtime and something that worked fine on 3.11 now dies at import time with one of:

```
ModuleNotFoundError: No module named 'smtpd'
```

```
ModuleNotFoundError: No module named 'asyncore'
```

Nothing in your code changed. These modules are just gone.

## Why this happens

`smtpd`, `asyncore`, and `asynchat` were all deprecated in Python 3.6 with explicit `DeprecationWarning`s, and all three were removed outright in Python 3.12 as part of [PEP 594](https://docs.python.org/3/whatsnew/3.12.html) — the standard library's long-running "dead batteries" cleanup (the same PEP that also dropped `distutils`, `imp`, and several others).

They tend to surface in a few specific places:

- **`smtpd`** — a local `DebuggingServer` or test SMTP server used in integration tests, or a script that fakes outbound mail for local development.
- **`asyncore` / `asynchat`** — older network code written before `asyncio` existed, or a dependency (often something mail- or FTP-related) that never migrated off the callback-based event loop these modules implemented.

Either way, the pattern is the same one behind most Python-3.12 Lambda breakage: code that was already deprecated-but-working for years suddenly hard-fails the moment the runtime bump turns the warning into a missing import.

## Fix — smtpd

Replace it with `aiosmtpd`, the maintained asyncio-based successor:

```bash
pip install aiosmtpd
```

```python
# Before (removed in 3.12)
from smtpd import DebuggingServer
import asyncore
server = DebuggingServer(('localhost', 1025), None)
asyncore.loop()

# After
import asyncio
from aiosmtpd.controller import Controller

class PrintHandler:
    async def handle_DATA(self, server, session, envelope):
        print(envelope.content.decode('utf8', errors='replace'))
        return '250 Message accepted for delivery'

controller = Controller(PrintHandler(), hostname='localhost', port=1025)
controller.start()
```

If you only need the removed module back verbatim rather than rewriting call sites, the `standard-smtpd` package on PyPI restores it as a drop-in shim — a faster stopgap, not the long-term fix.

## Fix — asyncore / asynchat

Port the code to `asyncio`, which is the supported replacement for the transport/protocol model `asyncore` implemented:

```python
# Before (removed in 3.12): asyncore.dispatcher subclass with handle_read/handle_write
# After: an asyncio.Protocol
import asyncio

class MyProtocol(asyncio.Protocol):
    def data_received(self, data):
        # equivalent to handle_read
        ...

    def connection_lost(self, exc):
        # equivalent to handle_close
        ...
```

If the import comes from a third-party dependency rather than your own code, upgrade it first — most actively maintained libraries that used `asyncore` shipped an asyncio-based release well before 3.12 removed it. For a genuinely unmaintained dependency, vendoring the pure-Python `asyncore.py`/`asynchat.py` from a Python 3.11 source tree is a working (if inelegant) stopgap while you plan the real port.

## Catch every PEP 594 removal before the deploy, not after

Both of these tend to arrive together, and rarely alone — a codebase old enough to import `smtpd` or `asyncore` is usually old enough to still import `imp` or rely on `distutils` too. Smoke-test the whole surface on 3.12 before flipping the runtime label:

```bash
python3.12 -c "import your_module"
```

Running that against every entry point (handler, layer, and any script the deploy pipeline invokes) surfaces the full removal list at once, instead of one `ModuleNotFoundError` per cold start.

---

Free **[EOLkits scanner](https://eolkits.com/scan)** flags every deprecated Python/Node Lambda runtime in an account in about 30 seconds, nothing uploaded — I maintain it. Full references: **[eolkits.com/fix/python-no-module-named-smtpd](https://eolkits.com/fix/python-no-module-named-smtpd/)** and **[eolkits.com/fix/python-no-module-named-asyncore](https://eolkits.com/fix/python-no-module-named-asyncore/)**.
