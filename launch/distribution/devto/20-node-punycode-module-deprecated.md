---
title: "[DEP0040] DeprecationWarning: The `punycode` module is deprecated — what to do about it on Node.js 22 Lambda"
canonical_url: https://eolkits.com/fix/node-punycode-module-deprecated/
description: Node.js 22 Lambda logs are suddenly full of DEP0040 punycode warnings. Where they come from, why they get loud on a runtime upgrade, and the actual fix (it's not your code).
tags: aws, lambda, node, serverless
---

> [!CAUTION]
> Archived launch copy — do not publish or reuse. This draft predates the current
> bounded browser scanner, telemetry disclosure, lifecycle-date corrections, and
> readiness-gated paid scope; claims and `eolkits.com` links below may be false or stale.
> Use the [current README](../../../README.md) and
> [verified public site](https://ntoledo319.github.io/EOLkits/) instead.

Upgrade a Lambda function to `nodejs22.x` and CloudWatch fills up with a warning that wasn't there before:

```
(node:8) [DEP0040] DeprecationWarning: The `punycode` module is deprecated. Please use a userland alternative instead.
```

Nobody on the team imports `punycode`. It's not in `package.json`. The warning still shows up on every cold start.

## Why it appears now

Node.js has shipped a built-in `punycode` module since 0.x — it converts internationalized domain names between Unicode and ASCII (`xn--`) form. Node deprecated the built-in copy in favor of the identical userland package back in Node 7, but the warning was quiet (`--pending-deprecation` only) for years. Node 22 raises the volume: `DEP0040` fires on stderr by default whenever anything in the process still resolves `require('punycode')` — and it usually isn't your code doing the requiring.

The most common source is a **transitive dependency** that hasn't been updated: older major versions of `whatwg-url` (used by `jsdom`, `node-fetch` polyfills, and various URL-parsing packages), some `url`-parsing utilities, and legacy AWS SDK v2 internals all `require('punycode')` directly instead of `require('punycode/')` (note the trailing slash — that one character routes to the npm package instead of the deprecated Node built-in).

## Finding the source

```bash
node --trace-deprecation your-handler.js
```

`--trace-deprecation` prints a full stack trace with the warning instead of just the one-line message, which usually points straight at the offending `require()` inside `node_modules`.

If you'd rather not run the handler locally, grep for the bare require:

```bash
grep -rn "require('punycode')" node_modules --include="*.js" | grep -v "punycode/"
```

Anything that matches without the trailing slash is pulling in the deprecated built-in.

## The fix

**If it's your own code:**

```bash
npm install punycode
```

```js
// Before — resolves to Node's deprecated built-in
const punycode = require('punycode');

// After — resolves to the maintained userland package
const punycode = require('punycode/');
```

The trailing slash is not a typo — it's how Node's module resolver distinguishes the userland package (`node_modules/punycode/`) from the built-in of the same name.

**If it's a dependency:** upgrade it. Recent major versions of `whatwg-url`, `jsdom`, and the AWS SDK v3 packages have all moved off the built-in. `npm ls punycode` (or `npm why punycode` on npm 9+) shows which installed package is pulling it in, so you know exactly what to bump.

**If you can't upgrade the dependency yet:** this is a warning, not a breaking error — the function still runs correctly. It's safe to ship a Node 22 migration with the warning present and clean it up separately. Don't let it block the runtime upgrade itself; deprecated-runtime block dates are the deadline that actually matters. But don't ignore it indefinitely either — `punycode` is a real removal candidate in a future Node major, at which point it stops being a warning and starts being a crash.

## Silencing it (not recommended as a permanent fix)

```bash
node --no-deprecation your-handler.js
```

or set `NODE_NO_WARNINGS=1` in the Lambda environment variables. This hides the *symptom* — the transitive dependency is unchanged and will eventually need upgrading regardless. Useful for keeping noisy logs quiet during a migration window; not a substitute for actually tracking down the source.

---

The free **[EOLkits scanner](https://eolkits.com/scan)** flags deprecated Lambda runtimes and known dependency-level breaks like this one from your `package.json` / lockfile — in your browser, nothing uploaded; I maintain it. Full reference: **[eolkits.com/fix/node-punycode-module-deprecated](https://eolkits.com/fix/node-punycode-module-deprecated/)**.
