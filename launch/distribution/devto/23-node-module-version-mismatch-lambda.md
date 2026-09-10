---
title: "Error: The module was compiled against a different Node.js version using NODE_MODULE_VERSION — fixing native addon failures after a Lambda upgrade"
canonical_url: https://eolkits.com/fix/node-module-version-mismatch/
description: A native addon (sharp, bcrypt, better-sqlite3, grpc) fails to load on Lambda after bumping the runtime to nodejs22.x. What NODE_MODULE_VERSION 127 means, why your Node 20 binary is now incompatible, and the right fix for each scenario.
tags: aws, lambda, node, javascript
---

> [!CAUTION]
> Archived launch copy — do not publish or reuse. This draft predates the current
> bounded browser scanner, telemetry disclosure, lifecycle-date corrections, and
> readiness-gated paid scope; claims and `eolkits.com` links below may be false or stale.
> Use the [current README](../../../README.md) and
> [verified public site](https://ntoledo319.github.io/EOLkits/) instead.

You upgrade a Lambda function from `nodejs20.x` to `nodejs22.x`, redeploy, and the first cold start dies with something like this:

```
Error: The module '/var/task/node_modules/sharp/build/Release/sharp-linux-x64-115.node'
was compiled against a different Node.js version using
NODE_MODULE_VERSION 115. This version of Node.js requires
NODE_MODULE_VERSION 127. Please try re-compiling or re-installing
the module (for instance, using `npm rebuild` or `npm install`).
```

The numbers vary by package (`115` and `127` are Node 20 and Node 22 respectively), but the shape is always the same: a `.node` binary was compiled for one ABI and the runtime is now a different one.

## Why this happens

Every Node.js major version assigns a new **NODE_MODULE_VERSION** — an integer baked into compiled `.node` files that the runtime checks at load time:

| Node.js version | NODE_MODULE_VERSION |
|---|---|
| Node.js 20 | 115 |
| Node.js 22 | 127 |

Native addons — `sharp`, `bcrypt`, `better-sqlite3`, `canvas`, `grpcio`, and anything else that ships a precompiled `.node` file — link against the ABI of the Node version they were built on. When the runtime changes, the loader reads the embedded version, sees it doesn't match the running Node, and refuses to load the binary.

This is intentional: the ABI mismatch means the binary literally cannot be safely loaded. The error is a hard stop at cold-start time, not a warning.

The problem surfaces specifically after a Lambda runtime bump because your CI pipeline typically builds the deployment package once (on Node 20, say) and keeps redeploying the same artifact. The binary in `/var/task/node_modules/<pkg>/build/Release/*.node` was compiled for Node 20's ABI and the new `nodejs22.x` runtime won't touch it.

## The fix

### 1. Rebuild the deployment package on the target Node version

The root fix is always: **build where you deploy**. Tear down `node_modules` and reinstall on a machine (or container) running Node 22:

```bash
rm -rf node_modules
npm install
```

Or, if you can't change the build machine, force a rebuild:

```bash
npm rebuild
```

Then re-bundle and redeploy. Crucially, do this inside the Lambda base image if you have native dependencies, so the binary also links against the right glibc:

```bash
docker run --rm -v "$PWD":/var/task \
  public.ecr.aws/lambda/nodejs:22 \
  npm install
```

This produces a binary that is both the right ABI *and* linked against the right glibc — avoiding a second failure down the line.

### 2. If the package has no Node 22 prebuilt, upgrade it

Some packages ship prebuilt binaries keyed to specific Node major versions. If your pinned version has no Node 22 prebuild, the install falls back to compiling from source — which can fail in a CI environment without the right build toolchain. The fix is to upgrade to a version that does ship Node 22 prebuilts:

- **sharp**: upgrade to `>= 0.33.0` (moved to Node-API, no longer tied to a specific ABI)
- **bcrypt**: `>= 5.1.1` has Node 22 prebuilt support
- **better-sqlite3**: `>= 11.0.0` for Node 22; consider `>= 13.0.0` which switched to N-API for future-proof ABI compatibility

### 3. For dead packages, replace them — don't rebuild them

Some native packages have no Node 22 build and no intention of shipping one:

| Dead package | Replacement |
|---|---|
| `node-sass` | `sass` (Dart Sass — pure JS, no native build needed) |
| `fibers` | Remove it; Node's async primitives have superseded it |
| `grpc` | `@grpc/grpc-js` (pure JS gRPC client) |

These replacements are also smaller and faster in Lambda cold-start terms because they have no native compilation step.

### 4. Lock your build Node version in CI

Add an explicit engine constraint so a future CI runner upgrade can't silently produce an incompatible artifact:

```json
"engines": {
  "node": "22.x"
}
```

Or pin the Node version in your CI environment file (`.nvmrc`, `.node-version`, GitHub Actions `node-version: '22'`). The goal: whatever Node version runs `npm install` in CI must match the Lambda runtime.

## Catching it before the cold start

The mismatch is silent until a cold start fires in production. The fastest way to surface it earlier: **import the native module in a smoke test that runs inside the Lambda base image** (`public.ecr.aws/lambda/nodejs:22`), not just on your developer machine.

---

If you'd rather get a full picture of which Lambda functions carry native-addon ABI risk — alongside deprecated-runtime exposure — without auditing each deployment package by hand, the free **[EOLkits scanner](https://eolkits.com/scan)** checks an account in about 30 seconds, nothing uploaded. Full reference: **[eolkits.com/fix/node-module-version-mismatch](https://eolkits.com/fix/node-module-version-mismatch/)**.
