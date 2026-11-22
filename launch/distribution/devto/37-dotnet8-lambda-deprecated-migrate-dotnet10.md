---
title: "dotnet8 Lambda deprecated November 10, 2026 — exact steps to reach dotnet10"
canonical_url: https://eolkits.com/fix/lambda-dotnet8-runtime-deprecated/
description: AWS deprecated the dotnet8 Lambda runtime on November 10, 2026. Here's what that means, the create-block deadlines, and the exact .csproj and IaC changes to reach dotnet10 — plus the one gotcha that doesn't apply to .NET upgrades.
tags: dotnet, aws, lambda, serverless
---

AWS Lambda's `dotnet8` runtime reached end of support on **November 10, 2026**. If you haven't started the upgrade yet, here's what changes, what your deadlines look like, and how to reach `dotnet10` without surprises.

## What "deprecated" means (and doesn't mean)

Deprecation is not a deploy block. Per the [AWS Lambda runtime deprecation table](https://docs.aws.amazon.com/lambda/latest/dg/runtime-support-policy.html):

| Phase | dotnet8 date |
|---|---|
| Deprecation (security patches stop) | **Nov 10, 2026** |
| Block function create | **Jul 29, 2027** |
| Block function update | **Aug 31, 2027** |

After November 10 your `dotnet8` functions continue to invoke normally. You can still create and update them through the AWS CLI, SAM, CloudFormation, CDK, or Terraform — the Lambda console blocks creation, but the APIs don't, until July 2027. What *stopped* on November 10 is AWS applying security and runtime patches to the .NET 8 runtime. That unpatched exposure is the real cost of staying on `dotnet8`, not an immediate operational failure.

## The target: dotnet10

`dotnet10` (.NET 10 on Amazon Linux 2023) has been a supported managed Lambda runtime since January 2026 and is the natural upgrade target. Its deprecation isn't scheduled until November 2028 — two full years of patched runway.

One thing genuinely easier here than in a Python runtime upgrade: **both `dotnet8` and `dotnet10` run on Amazon Linux 2023**. There is no base OS change, no glibc version bump, and no native binary rebuild requirement. The entire upgrade is at the .NET target framework and NuGet package layer.

## The .csproj change

Each Lambda project file needs a one-line update:

```xml
<!-- Before -->
<TargetFramework>net8.0</TargetFramework>

<!-- After -->
<TargetFramework>net10.0</TargetFramework>
```

## The IaC change

**SAM / CloudFormation:**
```yaml
Runtime: dotnet10
```

**CDK (TypeScript):**
```typescript
runtime: lambda.Runtime.DOTNET_10
```

**Terraform:**
```hcl
runtime = "dotnet10"
```

**Serverless Framework:**
```yaml
runtime: dotnet10
```

If you deploy directly via `dotnet lambda deploy-function`, update `aws-lambda-tools-defaults.json` too:
```json
{
  "function-runtime": "dotnet10"
}
```

## NuGet package updates

Targeting `net10.0` requires current Amazon.Lambda NuGet packages. Upgrade to the latest compatible versions of everything your project references, in particular:

- `Amazon.Lambda.Core`
- `Amazon.Lambda.Serialization.SystemTextJson`
- `Amazon.Lambda.APIGatewayEvents` (for API Gateway integrations)
- `Amazon.Lambda.AspNetCoreServer` (for the ASP.NET Core adapter)
- Any `AWSSDK.*` packages in use

```bash
dotnet add package Amazon.Lambda.Core
dotnet add package Amazon.Lambda.Serialization.SystemTextJson
# add others as your project requires
```

After updating, run `dotnet build`. Most incompatibilities surface as compile-time errors or NuGet resolution warnings (NU1510), not cold-start crashes.

## Skipping .NET 9 — what to check

.NET 9 was a Standard-Term Support release; AWS Lambda never offered a managed `dotnet9` runtime (only a container-only one). Going directly from .NET 8 to .NET 10 means you inherit any .NET 9 breaking changes along the way.

The Lambda-impacting subset is small. The [Microsoft .NET 10 compatibility breaking changes](https://learn.microsoft.com/en-us/dotnet/core/compatibility/10) page lists them by area; the ones most likely to affect Lambda handlers are in the Runtime and Libraries sections. Run your test suite against `net10.0` before deploying — most breaks appear at compile time, not at cold start.

## Native AOT functions

If you're using .NET Native AOT for Lambda, compile inside the matching AL2023 container image for your target architecture:

```bash
# x86_64
docker run --rm \
  --platform linux/amd64 \
  -v "$(pwd)":/work \
  public.ecr.aws/lambda/dotnet:10 \
  dotnet publish /work -c Release --self-contained true

# arm64 / Graviton
docker run --rm \
  --platform linux/arm64 \
  -v "$(pwd)":/work \
  public.ecr.aws/lambda/dotnet:10 \
  dotnet publish /work -c Release --self-contained true
```

Building on macOS or Windows produces a Mach-O or Windows binary that cannot run on Lambda, regardless of the runtime version.

## Upgrade checklist

1. Update `<TargetFramework>net8.0</TargetFramework>` → `net10.0` in every Lambda `.csproj`.
2. Upgrade Amazon.Lambda and AWSSDK NuGet packages to current versions.
3. Run `dotnet build` — fix any compile errors or NuGet warnings.
4. Run your test suite against `net10.0`.
5. Update the runtime string in IaC (`Runtime: dotnet10` / `DOTNET_10` / `"dotnet10"`).
6. Deploy to a non-production alias first; invoke the function and confirm it succeeds.
7. Verify the runtime: `aws lambda get-function-configuration --function-name <name> --query Runtime`.

---

The free **[EOLkits scanner](https://eolkits.com/scan)** flags every deprecated Lambda runtime across your account in about 30 seconds — nothing uploaded. Full deprecation timeline and fix index: **[eolkits.com/fix/lambda-dotnet8-runtime-deprecated](https://eolkits.com/fix/lambda-dotnet8-runtime-deprecated/)**.
