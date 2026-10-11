---
title: '"ModuleNotFoundError: No module named ''audioop''" — fixing pydub and audio code on Python 3.13 Lambda'
canonical_url: https://eolkits.com/fix/python-no-module-named-audioop/
description: Bumped your Lambda to python3.13 and seeing a cold-start crash about audioop? PEP 594 removed it in Python 3.13. Here's why pydub and similar libraries break, and the exact fix.
tags: python, aws, lambda, serverless
---

The first cold start after you switch a Lambda function to `python3.13` can produce this:

```
[ERROR] Runtime.ImportModuleError: Unable to import module 'lambda_function':
No module named 'audioop'
```

Your handler never imported `audioop` directly. Neither did you, probably. But one of your dependencies did — and on the `python3.13` runtime, that module no longer exists.

## Why Python 3.13 removed audioop

`audioop` was a C extension in the Python standard library for manipulating raw audio data: rate conversion, μ-law encoding, companding. It was useful in the 1990s. By 2025 it was unmaintained, platform-specific, and had better replacements.

[PEP 594](https://peps.python.org/pep-0594/) ("Remove dead batteries from the standard library") deprecated `audioop` in Python 3.11 and removed it in Python 3.13, along with 18 other long-abandoned modules. The removal is documented directly in the Python 3.13 changelog: the module is simply absent on any `python3.13` runtime, including Lambda's.

## Why the error usually comes from pydub, not your code

[pydub](https://github.com/jiaaro/pydub) is the most-reached-for Python library for audio format conversion and simple manipulation. It's frequently used in Lambda functions that process voice recordings, podcast uploads, transcription inputs, or media pipelines.

pydub's `utils.py` imports `audioop` at module load time, not lazily — meaning the import fails the moment pydub itself is imported, before your handler runs a single line:

```python
# Inside pydub/utils.py — runs at import time
import audioop
```

pydub 0.25.1 (its most recent release, from 2021) has no Python 3.13 support. The maintainers have a closed PR that adds conditional `audioop-lts` support, but it hasn't shipped in a release. The net effect: `import pydub` on a `python3.13` runtime crashes with `No module named 'audioop'`, regardless of what your handler actually does with audio.

The same applies to any other library that imports `audioop` transitively — though pydub is by far the most common offender in Lambda workloads.

## The 30-second fix: audioop-lts

The Python community published [`audioop-lts`](https://pypi.org/project/audioop-lts/) specifically to backport the removed module to Python 3.13+. It's a maintained C extension port licensed under PSF-2.0, currently at version 0.2.2 (released August 5, 2025).

Add it to your `requirements.txt` with a version marker so it only installs on Python 3.13 and above:

```
audioop-lts; python_version>='3.13'
```

This is the safest form: it installs on the `python3.13` Lambda runtime, and does nothing on `python3.12` or earlier (where the stdlib module is still present).

Then rebuild your deployment package:

```bash
pip install --target ./package -r requirements.txt
```

That's it. pydub resolves `audioop` through `audioop-lts` and your function starts normally.

**One caveat:** `audioop-lts` requires `python>=3.13` — you cannot install it on 3.12 to pre-test 3.13 behavior. Use a `python3.13` Lambda base image locally (`public.ecr.aws/lambda/python:3.13`) to verify before deploying.

## If you want a durable fix instead

`audioop-lts` is a shim that keeps pydub running. If you want to remove the dependency on a removed stdlib module entirely, switch to a maintained audio library:

- **[soundfile](https://python-soundfile.readthedocs.io/)** — reads and writes most audio formats via libsndfile; pure Python wrapper, well-maintained.
- **[pydub with soundfile backend](https://github.com/jiaaro/pydub#getting-more-formats-with-ffmpeg)** — pydub can use ffmpeg/avconv for format conversion without ever calling `audioop`; for Lambda this means bundling a static ffmpeg binary.
- **[librosa](https://librosa.org/)** — if you're doing signal processing or feature extraction, librosa handles the audio I/O and DSP without `audioop`.

For straightforward format conversion in a Lambda, bundling a static ffmpeg binary (via a Lambda layer) and calling it via `subprocess` also works and removes pydub as a dependency entirely.

## The Lambda-specific checklist

Before you redeploy:

1. Add `audioop-lts; python_version>='3.13'` to `requirements.txt`.
2. Rebuild the deployment package on the `python3.13` base image or architecture that matches your Lambda.
3. Confirm with `python3 -c "import audioop; print(audioop.__file__)"` inside the build environment — you should see the `audioop_lts` path, not a stdlib path.
4. Watch the first cold start in CloudWatch Logs to confirm the `Runtime.ImportModuleError` is gone.

If you're running other Lambda functions still on `python3.11`, its block dates are **Jul 29, 2027** (create) and **Aug 31, 2027** (update) — you have runway, but the `audioop` breakage is a preview of what PEP 594 does on every 3.13 upgrade.

---

[EOLkits](https://eolkits.com/scan) can scan your Lambda functions and flag runtimes and dependencies with known compatibility issues before you flip the runtime switch.
