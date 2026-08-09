---
title: "401 from 169.254.169.254 — fixing EC2 instances after the IMDSv2 enforcement deadline"
canonical_url: https://eolkits.com/migrate/imdsv1-enforcement/
description: IMDSv1 is off by default on new EC2 instances. If you are seeing 401 Unauthorized from the metadata endpoint, or credential errors in containers, here is the exact fix.
tags: aws, ec2, security, devops
---

If your EC2 instance, CI runner, or Kubernetes node started returning credential errors or a bare `401` from `http://169.254.169.254/latest/meta-data/`, one of two things happened: you launched a new instance after December 31 2025 (when AWS flipped the default to IMDSv2-required), or you enforced IMDSv2 on an existing instance before auditing every workload that still used the old one-step token-free request.

Both produce the same symptoms. Here is how to triage and fix them.

## What the errors look like

**Bare curl to the metadata service:**

```
$ curl http://169.254.169.254/latest/meta-data/instance-id
<?xml version="1.0" encoding="iso-8859-1"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
 <body>
  <h1>401 - Unauthorized</h1>
 </body>
</html>
```

**AWS CLI or SDK unable to pick up the instance role:**

```
An error occurred (InvalidClientTokenId) when calling the ... operation:
The security token included in the request is invalid.
```

or (boto3, if the SDK retries and exhausts fallbacks):

```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

These look like IAM permission errors. They are not. The credentials are never fetched because the metadata service returned 401 before handing over the token.

## Why it happens — IMDSv1 vs IMDSv2 in one paragraph

IMDSv1 is a simple GET to `169.254.169.254` — no authentication, no token, one round trip. IMDSv2 requires a PUT first to get a short-lived session token, then a GET that includes `X-aws-ec2-metadata-token: <token>` in the header. When `HttpTokens=required` is set on the instance, the metadata service rejects any GET that arrives without a valid token — hence the 401.

## The correct curl for IMDSv2

```bash
# Step 1: get a session token (TTL in seconds, max 21600 = 6h)
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# Step 2: use the token in every subsequent request
curl -s "http://169.254.169.254/latest/meta-data/instance-id" \
  -H "X-aws-ec2-metadata-token: $TOKEN"
```

Modern AWS CLI (≥ 2.0) and boto3 (≥ 1.13.0) do this automatically. The most common cause of the 401 in tooling is a script that still constructs the raw curl command without the token, or an old SDK version that predates IMDSv2 support.

## The container gotcha: hop limit

If you are running Docker containers on EC2 and the instance is IMDSv2-required, you will hit a second problem: by default `HttpPutResponseHopLimit=1`, which means the PUT response for the token does not survive the extra network hop through the Docker bridge. The container times out waiting for the token and falls back to `NoCredentialsError`.

Check the current hop limit on your instances:

```bash
aws ec2 describe-instances \
  --query 'Reservations[].Instances[].[InstanceId,MetadataOptions.HttpPutResponseHopLimit,MetadataOptions.HttpTokens]' \
  --output table
```

Fix it — set the hop limit to 2 while also enforcing IMDSv2:

```bash
# For a running instance (no restart required):
aws ec2 modify-instance-metadata-options \
  --instance-id i-0123456789abcdef0 \
  --http-tokens required \
  --http-put-response-hop-limit 2
```

In a Launch Template (the right fix for scale):

```json
{
  "MetadataOptions": {
    "HttpTokens": "required",
    "HttpPutResponseHopLimit": 2,
    "HttpEndpoint": "enabled"
  }
}
```

In Terraform:

```hcl
resource "aws_launch_template" "app" {
  # ...
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }
}
```

## Finding every instance that still allows IMDSv1

Before enforcing org-wide, audit what you have. This query returns every instance where IMDSv1 is still permitted (i.e., `HttpTokens` is `optional` rather than `required`):

```bash
aws ec2 describe-instances \
  --filter "Name=metadata-options.http-tokens,Values=optional" \
  --query 'Reservations[].Instances[].[InstanceId,InstanceType,LaunchTime,MetadataOptions.HttpTokens]' \
  --output table
```

For accounts with many instances, paginate with `--max-items 200` and a `--starting-token` loop, or use AWS Config with the managed rule `ec2-imdsv2-check` — it flags every non-compliant instance automatically.

## EKS and managed node groups

EKS node groups have their own launch template. If you are using a self-managed launch template, add `MetadataOptions` there. If you are using the managed EKS launch template, set `metadataOptions` via the nodegroup API:

```bash
aws eks update-nodegroup-config \
  --cluster-name my-cluster \
  --nodegroup-name my-nodegroup \
  --update-config '{"launchTemplateSpecification":{"id":"lt-xxx"}}'
```

Or set it at node group creation with `--launch-template` pointing to a template that includes `HttpPutResponseHopLimit: 2`. Pod-level credential providers (IRSA, EKS Pod Identity) bypass IMDS entirely and are unaffected by the hop limit.

## The timeline

AWS started shipping new instance types and new accounts with `HttpTokens=required` by default in late 2024. As of December 31 2025 — the enforcement date for the transition — **new EC2 instances default to IMDSv2-required**. Existing instances that were already `optional` remain `optional` until you change them or they are replaced.

The safest path: audit with the query above, set `HttpPutResponseHopLimit=2` for any instance running containers, set `HttpTokens=required`, and redeploy via your launch template so new instances inherit the settings automatically.

---

To scan every EC2 instance, EKS node group, and Lambda function in your account for this and other AWS deprecation risks in about 30 seconds, try the free **[EOLkits scanner](https://eolkits.com/scan)** — client-side, nothing uploaded. Full deadline timeline and per-error fix index: **[eolkits.com/migrate/imdsv1-enforcement](https://eolkits.com/migrate/imdsv1-enforcement/)**.
