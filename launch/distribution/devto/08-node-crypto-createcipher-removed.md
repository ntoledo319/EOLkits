---
title: "TypeError: crypto.createCipher is not a function — migrating to createCipheriv on Node.js 22 Lambda"
canonical_url: https://eolkits.com/fix/node-crypto-createcipher-is-not-a-function/
description: crypto.createCipher and crypto.createDecipher were removed in Node.js 22 (DEP0106). The exact error, why it happened, and a complete migration to crypto.createCipheriv with proper key derivation.
tags: aws, lambda, node, javascript
---

If you bumped a Lambda function to `nodejs22.x` and your handler now dies on the first crypto call, this is the wall:

```
TypeError: crypto.createCipher is not a function
```

The function is simply gone from the `crypto` object in Node.js 22. Here is the full story and the migration path.

## Why it was removed

`crypto.createCipher(algorithm, password)` derived the encryption key internally using OpenSSL's `EVP_BytesToKey`: MD5 digest, one iteration, no salt. That's broken in two ways:

- **No salt** — the same password always produces the same key, enabling precomputation and dictionary attacks.
- **One MD5 iteration** — passwords can be tested at billions of guesses per second on commodity hardware.

The deprecation warning (DEP0106) started in Node.js v10 as docs-only and became a runtime `DeprecationWarning` in v11. Node.js 22.0.0 made it end-of-life — the function was deleted. `crypto.createDecipher` went with it for the same reason.

The deprecation schedule:

| Node.js version | Status |
|---|---|
| v10.0.0 | Documentation-only deprecation |
| v11.0.0 | Runtime `DeprecationWarning` |
| **v22.0.0** | **Removed (End-of-Life)** |

Lambda runtimes that hit this removal: anything moved to `nodejs22.x`. The Lambda deprecation timeline: `nodejs20.x` is already deprecated (April 30, 2026, no more security patches); create-block and update-block land on **February 1, 2027** and **March 3, 2027** respectively — so teams upgrading ahead of Q1-2027 are hitting this now.

## The fix: crypto.createCipheriv with explicit key derivation

The replacement is `crypto.createCipheriv(algorithm, key, iv)`, which requires you to supply a key and IV explicitly. That forces proper key derivation.

**Before (broken on Node.js 22):**

```javascript
const crypto = require('crypto');

function encrypt(text, password) {
  const cipher = crypto.createCipher('aes-256-cbc', password);
  return cipher.update(text, 'utf8', 'hex') + cipher.final('hex');
}

function decrypt(ciphertext, password) {
  const decipher = crypto.createDecipher('aes-256-cbc', password);
  return decipher.update(ciphertext, 'hex', 'utf8') + decipher.final('utf8');
}
```

**After (Node.js 22 compatible):**

```javascript
const crypto = require('crypto');

const ALGORITHM = 'aes-256-cbc';
const KEY_LEN = 32;  // 256 bits
const IV_LEN = 16;   // 128 bits

function encrypt(text, password) {
  const salt = crypto.randomBytes(16);
  const iv = crypto.randomBytes(IV_LEN);
  // scrypt is the recommended key derivation function
  const key = crypto.scryptSync(password, salt, KEY_LEN);
  const cipher = crypto.createCipheriv(ALGORITHM, key, iv);
  const ciphertext = cipher.update(text, 'utf8', 'hex') + cipher.final('hex');
  // Store salt + iv + ciphertext so we can decrypt later
  return `${salt.toString('hex')}:${iv.toString('hex')}:${ciphertext}`;
}

function decrypt(payload, password) {
  const [saltHex, ivHex, ciphertext] = payload.split(':');
  const salt = Buffer.from(saltHex, 'hex');
  const iv = Buffer.from(ivHex, 'hex');
  const key = crypto.scryptSync(password, salt, KEY_LEN);
  const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);
  return decipher.update(ciphertext, 'hex', 'utf8') + decipher.final('utf8');
}
```

Key differences:

1. **Random salt per encryption** — `crypto.randomBytes(16)` prevents precomputation.
2. **`crypto.scryptSync` for key derivation** — memory-hard, resistant to GPU/ASIC brute-force. `crypto.pbkdf2Sync` is an acceptable alternative if you need async-friendly code.
3. **Explicit IV** — passed to `createCipheriv`; stored alongside the ciphertext so decryption works.

For async-heavy Lambda handlers, use `crypto.scrypt` (callback) or wrap `scryptSync` in a non-blocking path — `scryptSync` is CPU-intensive and can block the event loop on weak runtimes if called for every request.

## Decrypting data encrypted with the old API

The harder case is existing ciphertext produced by `createCipher`. `EVP_BytesToKey` used MD5 with an 8-byte salt (OpenSSL's magic: the first 8 bytes of the ciphertext after the `Salted__` prefix, if the `-p` flag was used, or just MD5 otherwise). You need to reproduce that derivation once to read old data.

If you control the old data and can re-encrypt it, do that now:

1. Read existing ciphertext using an older Node.js version (≤21) or a temporary environment with the old function.
2. Decrypt to plaintext.
3. Re-encrypt with the new `createCipheriv` pattern above.
4. Replace stored ciphertext with the new form.

This is the durable path. The `--openssl-legacy-provider` flag does not restore `createCipher` — it only re-enables the legacy hash provider for build tools; the removed function is gone regardless.

## Check for it in dependencies

Your own code may not call `createCipher` directly, but a dependency might. Find it:

```bash
grep -r "createCipher\b\|createDecipher\b" node_modules/ --include="*.js" -l
```

Upgrade any hit to a current release. If no upgrade exists, vendor a patched copy or open an issue — this has been a known removal since 2019.

## Confirm the runtime before deploying

```bash
aws lambda get-function-configuration \
  --function-name <your-function-name> \
  --query Runtime
```

If it still says `nodejs20.x` — already deprecated, no security patches since April 30, 2026 — plan the move to `nodejs22.x` now, not on the block date.

---

If you're not sure which Lambda functions in your account are on deprecated runtimes or have crypto issues like this one, the free **[EOLkits scanner](https://eolkits.com/scan)** flags them across all regions in about 30 seconds — nothing uploaded. Full per-error fix reference: **[eolkits.com/fix/node-crypto-createcipher-is-not-a-function](https://eolkits.com/fix/node-crypto-createcipher-is-not-a-function/)**.
