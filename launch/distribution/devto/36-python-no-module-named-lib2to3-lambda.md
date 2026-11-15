---
title: '"ModuleNotFoundError: No module named ''lib2to3''" — fixing the Python 3.13 Lambda cold-start crash'
canonical_url: https://eolkits.com/fix/python-no-module-named-lib2to3/
description: Upgraded Lambda to python3.13 and hitting a lib2to3 cold-start crash? Python 3.13 removed the module entirely. Here's which packages trigger it and the exact fix for each.
tags: python, aws, lambda, serverless
---

Switch a Lambda function to `python3.13` and you may see this in CloudWatch Logs on the first cold start:

```
[ERROR] Runtime.ImportModuleError: Unable to import module 'lambda_function':
No module named 'lib2to3'
```

or, coming through a dependency:

```
ModuleNotFoundError: No module named 'lib2to3'
```

The module has been part of Python since version 2.6. It is gone in Python 3.13. Here is why, and what to do about it.

## Why lib2to3 is gone

`lib2to3` was the library that powered `2to3` — the CLI tool that mechanically rewrote Python 2 source code to Python 3. It was deprecated in Python 3.11 and **completely removed in Python 3.13**. The removal is distinct from PEP 594's "dead batteries" batch; it has its own ticket ([gh-104780](https://github.com/python/cpython/issues/104780), contributed by Victor Stinner) in the CPython changelog.

The `python3.13` Lambda runtime (running on Amazon Linux 2023, available since November 2024) has no `lib2to3`. Every import of `lib2to3` or any of its sub-packages fails immediately at cold-start — before your handler logic runs.

## Which packages trigger this

**autopep8 ≤ 2.0.x** — The W690 fixer range in older autopep8 builds imports from `lib2to3`. This manifests in Lambda functions that run autopep8 as a code-formatting step or bundle it as a utility dependency. **autopep8 2.3.2** added explicit Python 3.13 support and removed the lib2to3 dependency. Upgrade first.

**python-future (futurize / pasteurize)** — `python-future`'s `futurize` and `pasteurize` tools are architecturally built on lib2to3 fixers. The 1.0.0 release (the final upstream release) does not support Python 3.13. If your Lambda bundles `future` and imports from `futurize` or `pasteurize`, it will crash on 3.13.

**Custom code using lib2to3 directly** — Any code that does `from lib2to3.pygram import python_grammar` or similar to parse or transform Python source (CI tooling, linters, code-generation scripts) will also break.

## Find every import

Before fixing, locate every importer — including transitive ones inside your installed packages:

```bash
# Your own code
grep -rn 'import lib2to3\|from lib2to3' .

# Inside installed packages (adjust the path to your virtualenv)
grep -rn 'import lib2to3\|from lib2to3' \
  "$(pip show pip | awk '/Location:/{print $2}')" 2>/dev/null | head -30
```

If the grep points into a dependency, check that dependency's release history for a Python 3.13-compatible version before writing workaround code.

## Fix 1: Upgrade autopep8 to 2.3.2+

```bash
pip install "autopep8>=2.3.2"
```

Confirm Python 3.13 support in the installed version before rebuilding the Lambda package:

```bash
python3.13 -c "import autopep8; print(autopep8.__version__)"
```

Rebuild the deployment ZIP or container image on the target runtime after upgrading.

## Fix 2: Replace python-future with a maintained alternative

The `python-future` package (and its `futurize`/`pasteurize` commands) have no upstream Python 3.13 fix. Options:

**Run conversion tools under Python 3.12 only.** `2to3`-style code conversion is a build-time step, not a runtime step. If your Lambda runs the converted output (not the converter), pin the build toolchain to Python 3.12 and run `futurize` there. The Lambda function itself can still target `python3.13`.

**Migrate to LibCST.** [`LibCST`](https://libcst.readthedocs.io/) is a concrete syntax tree library that supports Python 3.13 source and is the modern replacement for lib2to3-based code transformation:

```python
# Replace lib2to3-based AST fixers with LibCST
# pip install libcst
import libcst as cst

tree = cst.parse_module(source_code)
```

**Migrate to python-modernize.** For one-off Python 2→3 conversions, `python-modernize` (a wrapper around `2to3`) can be run under Python ≤ 3.12 for the conversion step itself.

## Fix 3: Replace custom lib2to3 usage

If your code uses lib2to3 directly for Python source parsing or transformation, switch to [`LibCST`](https://libcst.readthedocs.io/) or [`parso`](https://parso.readthedocs.io/). Both support current Python grammar and are actively maintained.

## Managed stopgap: pin to python3.12

If you need more time to audit all dependencies:

```yaml
# SAM / CloudFormation
Runtime: python3.12

# Terraform
runtime = "python3.12"
```

`lib2to3` still exists on python3.12. Treat this as a time-boxed transition: python3.12 is deprecated on **2027-07-31** (AWS blocks updates on **2027-09-01**). Record the reason for the pin so it doesn't get forgotten.

## Before you redeploy

1. Run the grep commands above to find every importer.
2. Upgrade `autopep8` to 2.3.2+ if it appears.
3. For `python-future`: move `futurize`/`pasteurize` to a build-only Python 3.12 environment, or replace with LibCST for runtime use.
4. For custom lib2to3 usage: migrate to LibCST or parso.
5. Smoke-test before deploying: `python3.13 -c "import <your_handler_module>"` — the import error fires before any Lambda logic, so this catches it locally.

lib2to3 is one of several modules removed in Python 3.13. The same runtime bump can also surface `cgi`, `crypt`, `telnetlib`, `aifc`, `audioop`, `pipes`, or others — they all fail at import time on the first cold start.

---

The free **[EOLkits scanner](https://eolkits.com/scan)** detects deprecated Lambda runtimes and flags packages known to import removed modules — in your browser, nothing uploaded. Full per-error fix guides and the migration deadline timeline: **[eolkits.com/fix/python-no-module-named-lib2to3](https://eolkits.com/fix/python-no-module-named-lib2to3/)**.
