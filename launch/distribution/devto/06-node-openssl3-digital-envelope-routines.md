---
title: "error:0308010C:digital envelope routines::unsupported — why Lambda runtime upgrades break your webpack build"
canonical_url: https://eolkits.com/fix/node-error-digital-envelope-routines-unsupported/
description: Upgrading to nodejs18.x or nodejs22.x on AWS Lambda? This OpenSSL 3 error breaks webpack 4, react-scripts 4, and older Jest configs at build time. The exact cause and two durable fixes.
tags: aws, lambda, node, javascript
---

If you just bumped your CI pipeline — or your Lambda runtime — to Node.js 18 or 22 and your build step died, this is the wall:

```
Error: error:0308010C:digital envelope routines::unsupported
    at new Hash (node:internal/crypto/hash:67:19)
    at Object.createHash (node:crypto:130:10)
```

The stack trace points into webpack, `react-scripts`, or Jest. Your Lambda handler code is untouched. Here is why the runtime label change triggers a build failure.

## The cause in two sentences

Node.js 17 switched from OpenSSL 1.1.1 to OpenSSL 3.0. Every Node.js version since — 18, 20, 22 — runs OpenSSL 3. OpenSSL 3 puts legacy algorithms including **MD4** into a disabled-by-default "legacy provider." Webpack 4 calls `crypto.createHash('md4')` to fingerprint chunk content. On Node.js 18+, OpenSSL 3 refuses that call and throws `ERR_OSSL_EVP_UNSUPPORTED`, which surfaces as the `0308010C` error.

## Why Lambda teams hit this at runtime-upgrade time

The error lives in your **build step**, not inside the Lambda execution environment. The two are linked because of the deprecation schedule:

- `nodejs16.x` — the last Lambda runtime on OpenSSL 1.1 — is on the deprecation path. Teams moving to `nodejs18.x` or `nodejs22.x` naturally update their CI Node version to match.
- The Lambda runtime itself runs your handler fine. OpenSSL 3 does not break ES modules, `async`/`await`, or standard crypto like AES-256-GCM or SHA-256.
- It breaks **build tooling calling `createHash('md4')`** — tooling that runs on your CI machine, not inside Lambda. The runtime upgrade triggers the CI upgrade, which triggers the build failure.

Which Node.js version ships which OpenSSL:

| Lambda runtime | Node.js | OpenSSL | `createHash('md4')` |
|---|---|---|---|
| nodejs16.x | 16.x | 1.1.1 | Works |
| nodejs18.x | 18.x | 3.0 | Fails |
| nodejs20.x | 20.x | 3.0 | Fails |
| **nodejs22.x** | **22.x** | **3.0** | **Fails** |

## Fix 1 — upgrade webpack or react-scripts (durable)

Webpack 5 replaced the MD4 call with its own pure-JavaScript xxhash64 implementation that does not touch OpenSSL at all.

```bash
# webpack-only project
npm install --save-dev webpack@5 webpack-cli@5

# Create React App / react-scripts
npm install --save-dev react-scripts@5
```

If you cannot upgrade webpack itself, override the hash function in `webpack.config.js`:

```js
module.exports = {
  output: {
    hashFunction: 'sha256',
  },
};
```

SHA-256 is in OpenSSL 3's default provider, so this works on all supported Node.js versions without any environment variable changes.

For projects using **Jest**, the MD4 call was removed from `jest-haste-map` in 27.4.2. Upgrade your Jest version if the trace points there.

## Fix 2 — re-enable the legacy provider (stopgap only)

If you cannot touch the tooling today, set `NODE_OPTIONS` before running your build:

```bash
# .env / CI environment variable
NODE_OPTIONS=--openssl-legacy-provider

# Or inline in package.json scripts
"build": "NODE_OPTIONS=--openssl-legacy-provider react-scripts build"
```

In a Dockerfile building a Lambda deployment package:

```dockerfile
RUN NODE_OPTIONS=--openssl-legacy-provider npm run build
```

**Do not leave this in place permanently.** The flag re-enables deprecated algorithms across the entire Node.js process. It is also subject to removal in a future OpenSSL release, meaning it will silently stop working and break the build again.

## Confirm no legacy crypto calls remain

After the fix, verify clean with:

```bash
# Should print nothing OpenSSL-related
node --trace-deprecation -e "const w = require('webpack'); w({}, () => {})" 2>&1 | grep -i openssl
```

Check the Lambda runtime version you are targeting:

```bash
aws lambda get-function-configuration \
  --function-name <your-function-name> \
  --query Runtime
```

## The pattern to internalize

This error is not a crypto vulnerability — it is a dependency age signal. Webpack 4 and react-scripts 4 were released in 2020. The projects that hit this error in 2026 are the same ones that will hit `node-module-version-mismatch` (native addons), `Cannot find module 'aws-sdk'` (SDK v2 removal), and `crypto.createCipher is not a function` (removed in Node.js 22). An OpenSSL 3 error is a useful proxy for "this build pipeline has not been reviewed since the nodejs16.x era."

Fix the hash function, then audit the rest of the dependency tree before your next Lambda runtime deadline.

---

Not sure which of your Lambda functions are still on deprecated runtimes or blocked SDKs? [Run a free EOLkits scan](https://eolkits.com/scan) — it maps every function to its runtime deprecation date and flags the issues before AWS does.
