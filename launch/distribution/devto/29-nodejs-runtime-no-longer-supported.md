---
title: '"The runtime parameter of nodejs18.x is no longer supported" — fixing the AWS Lambda deploy block'
canonical_url: https://eolkits.com/fix/lambda-nodejs-runtime-no-longer-supported/
description: Hitting "The runtime parameter of nodejs18.x is no longer supported"? Node.js 16, 18, and 20 share the same AWS Lambda block dates. Here's the one-line fix and three breaking changes to catch before you flip to nodejs24.x.
tags: aws, lambda, node, serverless
---

Your CI pipeline just failed. The deploy step threw:

```
ResourceConflictException: The runtime parameter of nodejs18.x is no longer
supported for creating or updating AWS Lambda functions.
```

Nothing changed in your code. The runtime was fine last month. Here's why it broke and how to fix it in one IaC change.

## Why this error fires

AWS deprecates Lambda runtimes in three phases:

1. **Phase 1** — Security patches stop (the runtime still runs and deploys).
2. **Phase 2** — Creating new functions with that runtime is blocked.
3. **Phase 3** — Updating existing functions on that runtime is blocked.

The error above fires at Phase 2/3. When a `terraform apply`, SAM deploy, CDK synth, or Serverless `deploy` targets a runtime past its Phase 2 date, AWS returns this exception and the deploy fails — even though the function is still running fine in production.

## The nodejs16/18/20 block cluster

Node.js 16, 18, and 20 share the same block dates. So do python3.8, python3.9, python3.10, ruby3.2, and dotnet6 — AWS batched them all together:

| Runtime | Security patches stopped | Create blocked | Update blocked |
|---|---|---|---|
| nodejs16.x | March 2026 | 2027-02-01 | 2027-03-03 |
| nodejs18.x | March 2026 | 2027-02-01 | 2027-03-03 |
| nodejs20.x | April 30, 2026 | 2027-02-01 | 2027-03-03 |

Security patches stopped months ago. The deploy block is what surfaces this exact error. If you're already past the block date and your function hasn't been deployed since, the next deploy will fail with this message.

## The one-line fix

Change the runtime to a currently supported version. `nodejs24.x` (GA November 2025, Amazon Linux 2023, security support through April 2028) is the current long-runway target:

**SAM / CloudFormation:**
```yaml
Runtime: nodejs24.x
```

**CDK:**
```typescript
runtime: lambda.Runtime.NODEJS_24_X
```

**Terraform:**
```hcl
runtime = "nodejs24.x"
```

**Serverless Framework:**
```yaml
runtime: nodejs24.x
```

**AWS CLI:**
```bash
aws lambda update-function-configuration \
  --function-name my-function \
  --runtime nodejs24.x
```

Recheck the [AWS Lambda runtimes table](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) before scheduling work — AWS has moved dates before; the table is authoritative.

## Three breaking changes to fix before you flip

Changing the runtime label is one line. Making the function work on it is the rest. Three things break most often when moving from nodejs16.x/18.x to nodejs24.x:

### 1. `aws-sdk` v2 is not bundled (nodejs18.x and later)

From nodejs18.x onward, Lambda preinstalls only the modular AWS SDK v3 (`@aws-sdk/*`). The v2 package (`aws-sdk`) is gone from the runtime layer:

```js
// Breaks on nodejs18.x+
const AWS = require('aws-sdk');
const s3 = new AWS.S3();

// Fix: migrate to v3 modular clients
const { S3Client, GetObjectCommand } = require('@aws-sdk/client-s3');
const s3 = new S3Client({});
```

v3 clients also change the call pattern — commands return promises directly, no `.promise()` suffix needed. Bundle the old `aws-sdk` v2 in the deployment package as a stopgap if you need more time, but plan the migration.

### 2. Native addons need to be rebuilt for the new ABI

Packages like `sharp`, `bcrypt`, `better-sqlite3`, and `canvas` compile against the Node.js ABI of the version they were built on. Upgrading the runtime without rebuilding triggers:

```
Error: The module was compiled against a different Node.js version using NODE_MODULE_VERSION
```

Rebuild by deleting `node_modules` and reinstalling on the exact target version, or build your deployment ZIP inside the matching Lambda base image:

```bash
docker run --rm -v "$PWD":/var/task \
  public.ecr.aws/lambda/nodejs:24 \
  npm ci --omit=dev
```

### 3. Callback-based handlers are removed in nodejs24.x

`nodejs24.x` drops the legacy callback pattern for Lambda handlers. The three-argument form now emits `Runtime.CallbackHandlerDeprecated` and the function cannot execute:

```js
// Breaks on nodejs24.x
exports.handler = function(event, context, callback) {
  callback(null, { statusCode: 200 });
};
```

Convert to `async/await`:

```js
// Works on nodejs24.x
exports.handler = async function(event) {
  return { statusCode: 200 };
};
```

`context.succeed`, `context.fail`, and `context.done` are also removed. If you're moving from nodejs18.x or earlier, audit your handlers and any middleware libraries before flipping the runtime. If `nodejs22.x` is an intermediate step without callback removal, it can serve as a stepping stone to validate other breaking changes first.

## Confirm the fix

After redeploying, verify the runtime actually changed:

```bash
aws lambda get-function-configuration \
  --function-name my-function \
  --query Runtime
```

Expected output: `"nodejs24.x"`. Then invoke the function once and check CloudWatch Logs for cold-start errors before marking the migration complete.

## Related errors

- `Error: Cannot find module 'aws-sdk'` — [see the /fix page](https://eolkits.com/fix/node-cannot-find-module-aws-sdk/)
- `Error: The module was compiled against a different Node.js version` — [see the /fix page](https://eolkits.com/fix/node-module-version-mismatch/)
- `Runtime.CallbackHandlerDeprecated` — upgrade to `async/await` as above

---

The free **[EOLkits scanner](https://eolkits.com/scan)** detects deprecated Lambda runtimes across your Terraform, SAM, CDK, or Serverless config and returns a severity-sorted list of every blocked runtime and known dependency break in under 60 seconds. Nothing is uploaded.
