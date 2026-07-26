---
title: "Node Sass does not yet support your current environment — what breaks when you upgrade to nodejs22.x"
canonical_url: https://eolkits.com/fix/node-sass-deprecated-unsupported/
description: Upgrading a Lambda function or container to Node.js 18 or 22 and hitting "Node Sass does not yet support your current environment"? Here's why, and the definitive fix.
tags: aws, lambda, node, javascript
---

You upgrade a Lambda function, a Docker base image, or your CI pipeline to Node.js 18 or 22 — and the next `npm install` or Docker build dies like this:

```
Error: Node Sass does not yet support your current environment:
  Linux 64-bit with Unsupported runtime (v22)

For more information on which environments are supported please see:
https://github.com/sass/node-sass/releases/tag/v9.0.0
```

Or, if the binary was already installed on an older runtime and the container now runs Node 22:

```
Error: The module '/app/node_modules/node-sass/vendor/linux-x64-127/binding.node'
was compiled against a different Node.js version using
NODE_MODULE_VERSION 108. This version of Node.js requires
NODE_MODULE_VERSION 127.
```

Both are the same root cause. Here's what's happening and how to fix it permanently.

## Why this happens

`node-sass` is a Node.js wrapper around **LibSass** — a C++ implementation of the Sass compiler. Because it's a native addon, it must ship a precompiled binary for each Node.js major version and platform combination. When it can't find one at install time, it falls back to compiling from source with `node-gyp`, which usually fails in CI or Lambda build environments that don't have the right build tools.

The core problem: **LibSass and node-sass are end-of-life.** The Sass team deprecated LibSass in October 2020 and archived the `sass/node-sass` GitHub repository in July 2024. No new prebuilt binaries are released for Node.js 18, 20, or 22. The package is frozen.

This surfaces specifically during Lambda runtime upgrades because:
- `nodejs16.x` shipped Node.js 16 (ABI version 93) — old enough that node-sass had a prebuild.
- `nodejs18.x` ships Node.js 18 (ABI 108). No node-sass prebuild.
- `nodejs22.x` ships Node.js 22 (ABI 127). No node-sass prebuild, and the repo is archived.

The moment you flip the runtime and rebuild your deployment package, the install fails or the previously-built native binary refuses to load.

## The fix: migrate to Dart Sass

The `sass` package is **Dart Sass** — the official, actively-maintained Sass implementation. It compiles to pure JavaScript: no native addon, no prebuilt binary, no ABI mismatch, no node-gyp. It installs cleanly on every Node.js version from 12 onward.

**Step 1 — swap the package:**

```bash
npm uninstall node-sass
npm install --save-dev sass
```

That's the whole migration for most projects.

**Step 2 — update webpack's sass-loader (if you use it):**

Older `sass-loader` versions would try `node-sass` first. With `node-sass` removed, it auto-detects `sass` — but if you have an explicit `implementation` option in your webpack config, update it:

```js
// webpack.config.js — before
{
  loader: 'sass-loader',
  options: { implementation: require('node-sass') }
}

// webpack.config.js — after
{
  loader: 'sass-loader',
  options: { implementation: require('sass') }
}
```

**Step 3 — Angular CLI:**

Angular projects that specify `node-sass` in the `stylePreprocessorOptions` or have it as a dependency can swap to `sass` with no config change — Angular CLI auto-detects the installed implementation.

**Step 4 — react-scripts / Create React App:**

CRA uses `sass` as the recommended processor. Remove `node-sass`, install `sass`, and the build picks it up automatically.

## Compatibility: is it a drop-in?

For the overwhelming majority of real-world SCSS codebases, yes. The only behavioral differences you might hit:

- **`/` division in Sass** — Dart Sass warns that `/` is deprecated as a division operator inside calc-style expressions (use `math.div()` from `sass:math` instead). This is a deprecation warning, not a breakage — your build still works.
- **`!global` in nested scopes** — a rarely-used pattern; Dart Sass handles it consistently with the spec.
- **Indented syntax (`.sass` files)** — fully supported.

If your tests pass after the swap, you're done. Run `npx sass --version` to confirm you're on Dart Sass (it prints `X.Y.Z compiled with dart2js`).

## Lambda-specific check: build the package on the right runtime

After the migration, make sure your deployment package is built on the same Node.js version Lambda will run:

```bash
# Build inside the Lambda container image to guarantee ABI match
docker run --rm -v $(pwd):/app -w /app \
  public.ecr.aws/lambda/nodejs:22 \
  npm ci --production
```

Because `sass` is pure JS, this is less critical than before — but it's still good practice for any Lambda package containing native modules.

## Timeline: why this hits now

| Runtime | Node.js | Last node-sass prebuild | Phase 2 (create-block) |
|---|---|---|---|
| `nodejs16.x` | 16 | ✓ v9.0.0 | Blocked |
| `nodejs18.x` | 18 | ✗ archived | Blocked |
| `nodejs20.x` | 20 | ✗ archived | ~late 2026 |
| `nodejs22.x` | 22 | ✗ archived | — |

AWS blocks creating new functions on deprecated runtimes first, then blocks updating existing ones. `nodejs16.x` is already fully blocked. Teams migrating away from it are hitting this node-sass wall now.

---

The free **[EOLkits scanner](https://eolkits.com/scan)** detects deprecated Lambda runtimes and known packages that require rebuilt binaries after a runtime upgrade — in your browser, nothing uploaded. Full per-error fixes: **[eolkits.com/fix/node-sass-deprecated-unsupported](https://eolkits.com/fix/node-sass-deprecated-unsupported/)**.
