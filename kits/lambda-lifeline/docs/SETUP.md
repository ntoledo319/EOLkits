# Setup guide — target time: 30 minutes

This walks you from zero to first deployed Node 24 function. It assumes you have:
- Node.js 18+ installed locally
- AWS CLI configured with credentials that have `lambda:*` and `cloudwatch:DescribeAlarms` permissions
- A Lambda function using `nodejs16.x`, `nodejs18.x`, `nodejs20.x`, or `nodejs22.x`

## Step 1 · Install (2 min)

```bash
git clone https://github.com/ntoledo319/EOLkits.git
cd EOLkits/kits/lambda-lifeline
npm ci                # installs the exact checked-in dependency graph
npm test              # verify the current checkout
```

The kit is not published to the npm registry. Run `./bin/cli.mjs` from this
checkout, or use the repository's root GitHub Action in CI.

## Step 2 · Inventory (5 min)

```bash
./bin/cli.mjs scan \
  --regions us-east-1,us-west-2,eu-west-1 \
  --format md \
  --out scan.md
```

Open `scan.md`. You now know:
- Which functions are EOL
- Which region they live in
- Days until hard deadline
- Recommended target runtime

Share this file with your team before touching anything.

## Step 3 · Fix code (5 min per repo)

```bash
# Dry-run (writes nothing)
./bin/cli.mjs codemod --path ./src

# Review output. If happy:
./bin/cli.mjs codemod --path ./src --apply

# Check the diff
git diff
```

Lint findings (`buffer-negative-index`, `streams-hwm`) are not auto-fixed — review and fix manually. They are rare enough that we prefer a human reads the context.

## Step 4 · Fix native deps (5 min)

```bash
./bin/cli.mjs audit --path . --strict
```

For each flagged dep, bump the version in `package.json` to the listed minimum. Then:

```bash
npm install
npm rebuild    # rebuilds native bindings against new Node version
npm test       # run your existing test suite on Node 24
```

Install Node 24 locally to match Lambda:

```bash
nvm install 24 && nvm use 24
npm test
```

## Step 5 · Fix CA certs (only if you touch RDS) (2 min)

Node 20+ no longer auto-loads Amazon CA certs. If your function connects to RDS over TLS, you need `NODE_EXTRA_CA_CERTS`:

```bash
./bin/cli.mjs certs --function my-api-fn --apply
# Or for everything:
./bin/cli.mjs certs --all --apply
```

## Step 6 · Patch IaC (3 min)

```bash
./bin/cli.mjs iac --path . --apply
git diff
```

This rewrites `Runtime: nodejs20.x` to `Runtime: nodejs24.x` in SAM / CloudFormation / CDK / Terraform / Serverless Framework files.

## Step 7 · Plan + deploy (8 min)

Create a CloudWatch alarm for errors on the target function (one-time setup):

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name my-api-errors \
  --metric-name Errors --namespace AWS/Lambda \
  --statistic Sum --period 60 --evaluation-periods 2 \
  --threshold 5 --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=my-api-fn
```

Preview the deploy:

```bash
./bin/cli.mjs plan --function my-api-fn
```

Execute:

```bash
./bin/cli.mjs deploy --function my-api-fn --apply \
  --alarm arn:aws:cloudwatch:us-east-1:123456789012:alarm:my-api-errors \
  --stages 5,25,50,100 \
  --wait-minutes 10
```

This:
1. Snapshots the current live version
2. Updates runtime to `nodejs24.x`
3. Publishes a new version
4. Weights the alias `live` at 5% → 25% → 50% → 100% over 40 minutes
5. Checks the alarm every minute — auto-rollbacks if it trips
6. Cuts alias to 100% new version once stable

## Troubleshooting

**A target runtime is rejected on apply** — recheck the current [AWS Lambda runtimes table](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) and the function's region. Choose an AWS-supported target explicitly, then rerun the full target-runtime test and packaging path before deployment.

**`NODE_MODULE_VERSION` mismatch at runtime** — you didn't `npm rebuild` after upgrading Node locally. Re-package and redeploy.

**"Could not call STS"** on scan — your credentials don't have `sts:GetCallerIdentity`. Scan still works, but accountId will be "unknown".

**Alarm ARN rejected** — the ARN format is `arn:aws:cloudwatch:REGION:ACCOUNT:alarm:NAME`. No trailing slash.

## CI

Drop [`src/ci-template/github-actions.yml`](../src/ci-template/github-actions.yml) into `.github/workflows/` to gate PRs on codemod + audit + IaC freshness.
