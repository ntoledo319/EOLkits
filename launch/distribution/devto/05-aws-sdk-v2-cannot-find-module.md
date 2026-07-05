---
title: "Error: Cannot find module 'aws-sdk'" on Lambda — migrating to @aws-sdk v3
canonical_url: https://eolkits.com/fix/node-cannot-find-module-aws-sdk/
description: Upgrading Lambda to nodejs18.x or later? AWS SDK v2 is no longer bundled. The exact error, why it happens, and a complete guide to migrating to @aws-sdk v3 modular clients.
tags: aws, lambda, node, javascript
---

If you upgraded a Lambda function from `nodejs16.x` to `nodejs18.x` (or `nodejs20.x` / `nodejs22.x`) and your logs now show:

```
Runtime.ImportModuleError: Error: Cannot find module 'aws-sdk'
```

you're not missing a locally installed package. AWS deliberately stopped bundling it.

## Why this happens

Until `nodejs16.x`, Lambda preinstalled **aws-sdk v2** (`require('aws-sdk')`) in every Node.js runtime. It was free — zero deployment overhead, no `package.json` entry needed.

From **`nodejs18.x` onwards** AWS replaced it: only **AWS SDK for JavaScript v3** (the `@aws-sdk/*` modular packages) is bundled. The monolithic `aws-sdk` v2 package is gone from the runtime environment entirely.

There is a second reason not to reach for the "just bundle v2" escape hatch: aws-sdk v2 reached **end-of-support on September 8, 2025** and no longer receives security patches.

## Fix A — Migrate to @aws-sdk v3 (durable)

v3 is modular: instead of one ~75 MB monolith, you install only the services you need. Each service lives in its own package.

**Before (v2 — S3):**

```javascript
const AWS = require('aws-sdk');
const s3 = new AWS.S3({ region: 'us-east-1' });
const result = await s3.getObject({ Bucket: 'my-bucket', Key: 'file.json' }).promise();
```

**After (v3 — S3):**

```javascript
const { S3Client, GetObjectCommand } = require('@aws-sdk/client-s3');
const s3 = new S3Client({ region: 'us-east-1' });
const result = await s3.send(new GetObjectCommand({ Bucket: 'my-bucket', Key: 'file.json' }));
```

Three things change in every service:

1. Import the specific **Client** and **Command** classes from `@aws-sdk/client-<service>`
2. Wrap parameters in a **Command** object and pass it to `client.send(...)`
3. Drop `.promise()` — v3 returns native promises directly

**DynamoDB DocumentClient (before / after):**

```javascript
// v2
const doc = new AWS.DynamoDB.DocumentClient();
const res = await doc.get({ TableName: 'users', Key: { id: '123' } }).promise();

// v3
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand } = require('@aws-sdk/lib-dynamodb');
const client = DynamoDBDocumentClient.from(new DynamoDBClient({ region: 'us-east-1' }));
const res = await client.send(new GetCommand({ TableName: 'users', Key: { id: '123' } }));
```

For DynamoDB, `@aws-sdk/lib-dynamodb` is the high-level v3 equivalent of `DocumentClient`. It marshals/unmarshals attribute types, so the call-site feels similar.

### Automate the mechanical rewrites with codemod

AWS ships a codemod that handles most of the straightforward conversions:

```bash
npm install -g aws-sdk-js-codemod

# Single file
npx aws-sdk-js-codemod -t v2-to-v3 src/handler.js

# Whole project
npx aws-sdk-js-codemod -t v2-to-v3 'src/**/*.js'
```

The codemod is reliable on simple patterns. Review the diff: dynamic service selection, callback-style calls, and chained middleware usually need manual cleanup.

## Fix B — Bundle aws-sdk v2 in your package (stopgap only)

If you cannot migrate immediately:

```json
{
  "dependencies": {
    "aws-sdk": "^2.1692.0"
  }
}
```

Include `node_modules` in your deployment ZIP or a Lambda layer. This unblocks deploys but adds ~25 MB of cold-start weight and leaves your functions on an end-of-support library. Treat it as a bridge, not a destination.

## What if the error comes from a dependency, not your code?

Run `npm ls aws-sdk` to find who imports it transitively. Most major packages (Amplify, CDK custom resources, Middy middleware) have published v3-compatible versions — upgrade first. If no upgrade exists, Fix B applies at the layer level until an upstream fix lands.

## Scan before you flip the runtime

Before changing `nodejs16.x` → `nodejs18.x` across your stack, find every v2 import:

```bash
grep -r "require('aws-sdk')\|require(\"aws-sdk\")\|from 'aws-sdk'" src/
```

Any hit needs to be migrated or bundled before the runtime label changes, or the function will fail its first invocation.

## Bundler gotcha: esbuild 0.22+

If you use esbuild to package your functions (SAM's default from v1.x), note that esbuild 0.22+ changed its default to treat `node_modules` as external — meaning even if you add `aws-sdk` to `package.json`, esbuild may exclude it from the ZIP. Force bundling:

```yaml
# SAM template.yaml
Metadata:
  BuildMethod: esbuild
  BuildProperties:
    Packages: bundle
```

Or with the CLI flag: `esbuild --packages=bundle`.

---

Every deprecated Lambda runtime across your account — including every function still wired to `nodejs16.x` — shows up in a free EOLkits scan. Run it before the next deploy, not after: **[eolkits.com/scan](https://eolkits.com/scan)**
