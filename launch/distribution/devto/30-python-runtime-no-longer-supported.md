---
title: '"The runtime parameter of python3.9 is no longer supported" — fixing the AWS Lambda Python deploy block'
canonical_url: https://eolkits.com/fix/lambda-python-runtime-no-longer-supported/
description: CI failing with "runtime parameter of python3.9 is no longer supported"? Python 3.8, 3.9, and 3.10 share the same AWS Lambda block dates. Here's the one-line IaC fix and the five Python 3.12 breaking changes to catch before you flip.
tags: python, aws, lambda, serverless
---

Your deployment pipeline just stopped cold:

```
ResourceConflictException: The runtime parameter of python3.9 is no longer
supported for creating or updating AWS Lambda functions.
```

Nothing changed in your code. The function is still running in production. Here's exactly why it broke and how to fix it.

## Why this error fires

AWS deprecates Lambda runtimes in three phases:

1. **Phase 1** — Security patches stop. The runtime keeps running and deploying.
2. **Phase 2** — Creating new functions with that runtime is blocked.
3. **Phase 3** — Updating existing functions on that runtime is blocked.

This error fires at Phase 2/3. When your IaC deploy targets a runtime past its Phase 2 date, AWS throws this exception and the deploy fails — even though the live function is still executing normally.

## The Python 3.8 / 3.9 / 3.10 block cluster

AWS batched several runtimes together with the same block dates:

| Runtime | Security patches stopped | Create blocked | Update blocked |
|---|---|---|---|
| python3.8 | October 2024 | 2027-02-01 | 2027-03-03 |
| python3.9 | 2025-12-15 | 2027-02-01 | 2027-03-03 |
| python3.10 | 2026-10-31 | 2027-02-01 | 2027-03-03 |

All three share the same 2027 block dates — AWS pushed them beyond the typical 30/60-day window in a single cluster with nodejs16.x, nodejs18.x, nodejs20.x, and dotnet6. Check the [AWS Lambda runtimes table](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) before scheduling work — it's the authoritative source and dates have shifted before.

## The one-line fix

Change the runtime to `python3.12`. It targets Amazon Linux 2023 (glibc 2.34), has security support well into 2028, and is the current recommended upgrade target.

**SAM / CloudFormation:**
```yaml
Runtime: python3.12
```

**CDK:**
```python
runtime=lambda_.Runtime.PYTHON_3_12
```

**Terraform:**
```hcl
runtime = "python3.12"
```

**Serverless Framework:**
```yaml
runtime: python3.12
```

**AWS CLI (for a single function):**
```bash
aws lambda update-function-configuration \
  --function-name my-function \
  --runtime python3.12
```

## Five breaking changes to verify before you flip

Changing the runtime label is one line. Making the function actually work on it takes a compatibility pass. These are the five things that break most often when moving from python3.9 to python3.12.

### 1. `distutils` is removed

`distutils` was removed from the standard library in Python 3.12 (PEP 632). If your code or a dependency imports it, you'll see `ModuleNotFoundError: No module named 'distutils'` at cold start. Replace direct uses with `setuptools` and `packaging`; upgrade any dependency that imports distutils transitively. [Full fix →](https://eolkits.com/fix/python-no-module-named-distutils/)

### 2. `imp` is removed

The `imp` module was removed in Python 3.12. Replace it with `importlib` — `importlib.util.find_spec`, `importlib.import_module`, and `importlib.machinery` cover every `imp` use case. [Full fix →](https://eolkits.com/fix/python-no-module-named-imp/)

### 3. `asyncore` and `asynchat` are removed

Both were removed in Python 3.12. Rewrite them as `asyncio` protocols and transports, or upgrade the dependency that still imports them. [Full fix →](https://eolkits.com/fix/python-no-module-named-asyncore/)

### 4. `collections.Mapping` and friends moved (Python 3.10)

If you're jumping from python3.9, you're also crossing the Python 3.10 line where `collections.Mapping`, `collections.Callable`, `collections.Sequence`, and a dozen other ABCs were removed from the top-level `collections` namespace. They've lived in `collections.abc` since Python 3.3. Old pyyaml, jsonschema 3.x, and other libraries trigger this. Upgrade to PyYAML ≥ 6.0 and jsonschema ≥ 4.0. [Full fix →](https://eolkits.com/fix/collections-has-no-attribute-mapping/)

### 5. `datetime.utcnow()` is deprecated

Not a hard crash, but Python 3.12 added a `DeprecationWarning` to every `utcnow()` call. Left unfixed, it floods your CloudWatch Logs and buries real errors. Replace with `datetime.datetime.now(datetime.timezone.utc)`. This warning fires from boto3/botocore too — upgrade both to clear it from the SDK layer. [Full fix →](https://eolkits.com/fix/datetime-utcnow-deprecated/)

## Find everything before redeploying

Scan your deployment package for removed modules before the deploy catches it:

```bash
# From the unzipped package root
grep -r "import distutils\|from distutils\|import imp\b\|from imp \
         \|import asyncore\|from asyncore\|import asynchat\|from asynchat" \
         . --include="*.py"
```

For the `collections.Mapping` pattern:
```bash
grep -r "collections\.Mapping\|collections\.Callable\|collections\.Sequence\
         \|collections\.Iterable\|collections\.MutableMapping" \
         . --include="*.py"
```

Also run your test suite with warnings promoted to errors to surface deprecation warnings in one pass:

```bash
python -W error::DeprecationWarning -m pytest
```

## Confirm the fix

After redeploying, verify the runtime changed and invoke the function to catch cold-start errors before they reach production:

```bash
aws lambda get-function-configuration \
  --function-name my-function \
  --query Runtime
```

Expected: `"python3.12"`. Then trigger one invocation and check CloudWatch Logs for any `ModuleNotFoundError` or stack traces from the compatibility items above.

---

To find every deprecated Python and Node.js runtime across your Terraform, SAM, CDK, or Serverless config in one pass, try the free **[EOLkits scanner → eolkits.com/scan](https://eolkits.com/scan)**. It returns a severity-sorted list with the per-error fix links, client-side, nothing uploaded.
