---
title: Migrating AWS Lambda from Node.js 20 to 22 — every breaking change
canonical_url: https://eolkits.com/blog/migrating-lambda-nodejs-20-to-22/
description: Node.js 20 Lambda is deprecated. The exact breaking changes moving to nodejs22.x — aws-sdk v2, import assertions, native addons, OpenSSL 3 — and how to automate it.
tags: aws, lambda, node, serverless
---

AWS deprecates Lambda runtimes on a 3-phase schedule: Phase 1 ends security patches, Phase 2 blocks **creating** new functions, Phase 3 blocks **updating** existing ones. Once Phase 3 hits, a frozen function's only path forward is a full redeploy on a new runtime. `nodejs20.x` is on that track; `nodejs22.x` is the target (LTS, maintained into 2027).

Most code moves cleanly. Here's the set that doesn't.

## 1. `aws-sdk` v2 is no longer bundled

On `nodejs16.x` and earlier, AWS preinstalled the v2 SDK. From `nodejs18.x` onward, only **v3** (`@aws-sdk/*`) is bundled. So:

```
Error: Cannot find module 'aws-sdk'
```

Fix: migrate to modular v3 clients, e.g. `const { S3Client } = require('@aws-sdk/client-s3')`. v3 also returns promises directly (no `.promise()`), and response shapes differ. Quick unblock: bundle `aws-sdk` in your package (adds cold-start weight).

## 2. Import assertions → import attributes

Node 22 ships the finalized spec, which renamed `assert` to `with`:

```javascript
// Node 20 (valid)  -> Node 22 (broken)
import cfg from './config.json' assert { type: 'json' };
// Node 22 (valid)
import cfg from './config.json' with { type: 'json' };
```

## 3. Native addons must be rebuilt

```
Error: The module was compiled against a different Node.js version using NODE_MODULE_VERSION
```

Native modules (sharp, bcrypt, better-sqlite3…) are tied to the Node ABI. Rebuild on the target version, or bump to a release with a Node 22 prebuild. Dead packages (node-sass, fibers) must be replaced.

## 4. OpenSSL 3

Node 17+ ships OpenSSL 3, which rejects legacy hashing some older tooling relies on:

```
Error: error:0308010C:digital envelope routines::unsupported
```

Fix: upgrade the tool (webpack 5, react-scripts 5+). `--openssl-legacy-provider` is a stopgap only.

## 5. `crypto.createCipher` removed

`crypto.createCipher` / `createDecipher` were removed in Node 22 — switch to `createCipheriv` with an explicit key + IV (`scrypt`/`pbkdf2` + `randomBytes`).

---

I wrote an open-source CLI (`lambda-lifeline`) that scans for all of these, codemods what's mechanical, patches your IaC, and stages a canary with rollback — plus a **free browser scanner** that flags them in your config in ~30 seconds, nothing uploaded: **[eolkits.com/scan](https://eolkits.com/scan)**.

Full guide with every case + captured output: **[eolkits.com/blog/migrating-lambda-nodejs-20-to-22](https://eolkits.com/blog/migrating-lambda-nodejs-20-to-22/)**
