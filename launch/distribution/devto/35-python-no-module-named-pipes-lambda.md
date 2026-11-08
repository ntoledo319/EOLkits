---
title: '"ModuleNotFoundError: No module named ''pipes''" — fixing the Python 3.13 Lambda cold-start crash'
canonical_url: https://eolkits.com/fix/python-no-module-named-pipes/
description: Bumped your Lambda to python3.13 and seeing a cold-start crash about pipes? PEP 594 removed it in Python 3.13. The fix is usually a one-liner — here's what to do.
tags: python, aws, lambda, serverless
---

Switch a Lambda function to `python3.13` and you may see this in CloudWatch Logs the moment the first cold start runs:

```
[ERROR] Runtime.ImportModuleError: Unable to import module 'lambda_function':
No module named 'pipes'
```

or, if the import reaches you through a dependency:

```
ModuleNotFoundError: No module named 'pipes'
```

The module existed since Python 2. It disappeared in Python 3.13 without a stdlib replacement. Here is why, and what to do about it.

## Why pipes is gone

`pipes` was a thin wrapper that let you assemble shell pipelines by chaining strings around `os.system`. Its most-used feature was the `pipes.quote` function, which shell-escaped a single argument. Its second feature was `pipes.Template`, which built a pipeline from a list of commands.

[PEP 594](https://peps.python.org/pep-0594/) deprecated `pipes` (and 18 other "dead batteries") in Python 3.11 and removed all 19 in Python 3.13. The module was superseded long before the removal:

- `pipes.quote` was moved to `shlex.quote` in **Python 3.3** (over a decade ago).
- Shell pipeline construction was superseded by `subprocess` in Python 2.4.

The `python3.13` Lambda runtime (available since November 2024, running on Amazon Linux 2023) has no `pipes`. The error fires at import time — before any of your handler logic runs.

## Find every import

Before fixing, find every place `pipes` is imported — including inside your dependencies:

```bash
# Your own code
grep -rn 'import pipes\|from pipes' .

# Inside installed packages
grep -rn 'import pipes\|from pipes' \
  "$(pip show pip | awk '/Location:/{print $2}')" 2>/dev/null | head -30
```

If a third-party package is the importer, check its release history for a version that dropped the dependency. A quick `pip index versions <package>` lists available releases; look for a changelog entry around the Python 3.13 support window. Upgrading the package is the cleanest fix when it is available.

## Fix 1: Replace pipes.quote with shlex.quote

This covers the vast majority of real-world cases. `shlex.quote` has been the documented location since Python 3.3 and is a **drop-in replacement**:

```python
# Before (Python 3.12 and earlier)
from pipes import quote
safe = quote(user_provided_filename)

# After (Python 3.3+)
from shlex import quote
safe = quote(user_provided_filename)
```

If your code uses the full module path:

```python
# Before
import pipes
safe = pipes.quote(filename)

# After
import shlex
safe = shlex.quote(filename)
```

That is the entire change. No behavior difference, no new dependency, no native extension to rebuild.

## Fix 2: Replace pipes.Template with subprocess

`pipes.Template` allowed code like:

```python
import pipes
t = pipes.Template()
t.append("gzip -c", "--")
t.append("base64", "--")
t.copy(src_file, dst_file)
```

The `subprocess` module is the right replacement. The equivalent using a pipeline:

```python
import subprocess

with open(src_file, "rb") as src, open(dst_file, "w") as dst:
    gzip = subprocess.Popen(["gzip", "-c"], stdin=src, stdout=subprocess.PIPE)
    b64 = subprocess.Popen(["base64"], stdin=gzip.stdout, stdout=dst)
    gzip.stdout.close()  # allow gzip to receive SIGPIPE if b64 exits
    b64.communicate()
```

`subprocess` is safer: you pass arguments as a list (no shell injection), handle errors explicitly, and control stdin/stdout/stderr per process. It has been part of the standard library since Python 2.4.

## Before you redeploy

1. Search the codebase with the grep commands above.
2. Apply the `shlex.quote` rename for every `pipes.quote` or `pipes.quote` usage.
3. Rewrite any `pipes.Template` chains with `subprocess`.
4. For third-party packages that import `pipes`, upgrade to a version that supports Python 3.13.
5. Test locally: `python3.13 -c "import <your_handler_module>"` — the cold-start error surfaces at import time, so this smoke test catches it without a Lambda deploy.

This is one of 19 modules removed in Python 3.13 by PEP 594. The same runtime bump may also surface `audioop`, `cgi`, `crypt`, `telnetlib`, `aifc`, or others from the same batch — they all fail at import time in one cold start.

---

The free **[EOLkits scanner](https://eolkits.com/scan)** detects deprecated Lambda runtimes and flags known packages that still import removed modules — in your browser, nothing uploaded. Full per-error fixes and the migration deadline timeline: **[eolkits.com/fix/python-no-module-named-pipes](https://eolkits.com/fix/python-no-module-named-pipes/)**.
