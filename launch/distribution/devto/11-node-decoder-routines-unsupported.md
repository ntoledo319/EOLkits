---
title: "error:1E08010C:DECODER routines::unsupported — why an old PEM key breaks after a Lambda Node.js upgrade"
canonical_url: https://eolkits.com/fix/node-error-decoder-routines-unsupported/
description: Upgraded to nodejs18.x, 20.x, or 22.x on AWS Lambda and a private key that worked fine on nodejs16.x now throws DECODER routines::unsupported? Here's the OpenSSL 3 cause and the real fix — re-encode the key, don't just add a flag.
tags: aws, lambda, node, security
---

You bump the Lambda runtime label from `nodejs16.x` to `nodejs18.x`, `20.x`, or `22.x`. The handler code doesn't change. The private key you've been loading for months — for signing a JWT, terminating TLS, or calling `crypto.createPrivateKey` — suddenly throws:

```
Error: error:1E08010C:DECODER routines::unsupported
    at new Sign (node:internal/crypto/sig:112:19)
    at Object.createPrivateKey (node:crypto:...)
```

No code changed. The runtime did. Here's why.

## The cause in two sentences

Node.js 17 and later bundle OpenSSL 3, and OpenSSL 3 disables a set of legacy key encodings and ciphers by default. If your private key is stored in an older format — a traditional PKCS#1 PEM, or a PEM encrypted with a weak/legacy cipher — OpenSSL 3's default provider refuses to decode it, and Node surfaces that refusal as `DECODER routines::unsupported`.

## Why this hits exactly at runtime-upgrade time

Lambda's Node.js runtimes map straight to OpenSSL versions:

| Lambda runtime | Node.js | OpenSSL | Legacy PKCS#1 key load |
|---|---|---|---|
| nodejs16.x | 16.x | 1.1.1 | Works |
| nodejs18.x | 18.x | 3.0 | Fails |
| nodejs20.x | 20.x | 3.0 | Fails |
| **nodejs22.x** | **22.x** | **3.0** | **Fails** |

`nodejs16.x` is on the deprecation path (block-create Feb 1 2027 / block-update Mar 3 2027, per AWS's Lambda runtime deprecation table). Every team moving off it lands on an OpenSSL-3 runtime and inherits this the first time the function touches an old-format key — JWT signing, an mTLS client cert, an SSH-style key stored as a secret.

## Fix 1 — re-encode the key to PKCS#8 (durable)

PKCS#8 is the modern, fully-supported container format. Converting is a one-time operation, not a runtime workaround:

```bash
# Unencrypted key
openssl pkcs8 -topk8 -nocrypt -in old-pkcs1.pem -out new-pkcs8.pem

# Keep it encrypted
openssl pkcs8 -topk8 -in old-pkcs1.pem -out new-pkcs8.pem
```

If the key itself uses a legacy cipher rather than just a legacy container:

```bash
openssl rsa -in old.pem -out new.pem
```

Store `new-pkcs8.pem` wherever the old key lived — Lambda environment variable, Secrets Manager, or Parameter Store — and point your code at it. No application code changes; `crypto.createPrivateKey` reads PKCS#8 natively.

## Fix 2 — the legacy provider flag (stopgap only)

If you can't rotate the key today:

```bash
node --openssl-legacy-provider index.js
```

Or as a Lambda environment variable:

```
NODE_OPTIONS=--openssl-legacy-provider
```

This re-enables OpenSSL's legacy algorithm set for the entire process — not just key loading. It weakens the runtime's default crypto posture, and the flag itself is not guaranteed to survive future OpenSSL major bumps. Treat it as a bridge to Fix 1, not a destination.

## Confirm the key format before you deploy

```bash
openssl asn1parse -in your-key.pem | head -5
```

`PKCS#1 RSA PRIVATE KEY` in the header line means you have the legacy format; `PRIVATE KEY` (no algorithm named) means it's already PKCS#8 and this error isn't about this key.

## The pattern to internalize

`DECODER routines::unsupported` is a credential-age signal, the same way `digital envelope routines::unsupported` is a build-tooling-age signal. Both come from OpenSSL 3 refusing something OpenSSL 1.1 allowed. If a Lambda function has been signing or decrypting with the same key since it was created on `nodejs12.x` or `nodejs14.x`, a runtime upgrade is the moment to rotate it into a modern format — not just patch around the error.

---

Not sure which of your Lambda functions still load a legacy-format key, or which runtimes they're on relative to AWS's actual block dates? [Run a free EOLkits scan](https://eolkits.com/scan) — it maps every function to its runtime deprecation date and flags native-dependency and crypto-compatibility issues before AWS does.
