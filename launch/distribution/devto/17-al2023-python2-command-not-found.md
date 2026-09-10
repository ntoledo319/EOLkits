---
title: "/usr/bin/env: 'python2': No such file or directory — Amazon Linux 2023 has no Python 2"
canonical_url: https://eolkits.com/fix/amazon-linux-2023-python2-command-not-found/
description: Amazon Linux 2 shipped Python 2.7 by default; Amazon Linux 2023 removed it entirely. Here's why your script broke and the actual migration steps, not a workaround.
tags: aws, python, linux, devops
---

> [!CAUTION]
> Archived launch copy — do not publish or reuse. This draft predates the current
> bounded browser scanner, telemetry disclosure, lifecycle-date corrections, and
> readiness-gated paid scope; claims and `eolkits.com` links below may be false or stale.
> Use the [current README](../../../README.md) and
> [verified public site](https://ntoledo319.github.io/EOLkits/) instead.

You moved an instance, AMI, or launch template from Amazon Linux 2 to Amazon Linux 2023, and something that used to run cleanly now fails on first boot:

```
/usr/bin/env: 'python2': No such file or directory
```

Or, if the script called the interpreter directly:

```
-bash: /usr/bin/python2: No such file or directory
```

`dnf` works, the instance is healthy, but any script with a `#!/usr/bin/python2` shebang, a `python2 script.py` invocation, or a tool that shells out to `python2`/`pip2` under the hood has nothing to run against.

## Why this happens

Amazon Linux 2 shipped Python 2.7 as part of the base image, because plenty of legacy system tooling and older cloud-init modules still expected it. Amazon Linux 2023 made a clean break: **there is no Python 2 package at all** — not `python2`, not `python27`, nothing installable via `dnf`. AL2023 ships Python 3 (currently 3.9 as the default `python3`, with versioned packages like `python3.11`/`python3.12` available) and nothing older.

This isn't a deprecation warning you can silence — the interpreter binary simply isn't in the AL2023 package repos. Anything that assumes it exists breaks the moment you provision on the new AMI:

- A user-data script with a `#!/usr/bin/env python2` shebang
- A legacy cron job or systemd unit calling `python2 /opt/app/run.py`
- Config management (Ansible, Chef, Puppet) with a module that shells out to `python2`/`pip2` internally
- A vendored tool or SDK that was never ported off Python 2

## The fix

There is no supported way to install Python 2 on Amazon Linux 2023 — the only real path is porting the code to Python 3.

**Step 1 — point the shebang/interpreter at Python 3:**

```bash
# before
#!/usr/bin/python2

# after
#!/usr/bin/env python3
```

**Step 2 — install a specific Python 3 minor version if your code depends on one:**

```bash
sudo dnf install -y python3.11
# or: python3.12, depending on what you've tested against
```

**Step 3 — update anything that invokes `python2`/`pip2` explicitly:**

```bash
grep -rl "python2\|pip2" user-data/ cron.d/ ansible/ systemd/
```

Replace each hit with `python3`/`pip3` (or the versioned binary from step 2), and re-test — Python 2→3 porting issues (print statements, `unicode` vs `str`, `dict.iteritems()`, integer division) are a separate, well-documented migration, not an AL2023-specific one; the [Python 3 porting guide](https://docs.python.org/3/howto/pyporting.html) covers the language-level changes.

**Step 4 — check for silent failures, not just missing-binary errors:**

If the Python-2-dependent step is wrapped in a script that swallows its exit code (`|| true`, a bare `except:`), you may not see the "No such file" error at all — just a feature that quietly stopped working. Grep first, don't wait for a support ticket.

---

This is one piece of the broader Amazon Linux 2 → 2023 migration (package manager, firewall, time sync, and Python version all shift at once) — the full checklist is at **[eolkits.com/fix/amazon-linux-2-eol](https://eolkits.com/fix/amazon-linux-2-eol/)**. If you want to know which instances in your account are still on AL2 before support ends, the free **[EOLkits scanner](https://eolkits.com/scan)** checks in about 30 seconds — nothing uploaded, and I maintain it.
