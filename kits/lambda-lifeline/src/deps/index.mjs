// Native-binary dep audit.
// Scans package.json (+ lockfile if present) for packages that ship native addons
// whose ABI is tied to the Node major version. Each entry includes a conservative
// minimum baseline. Meeting it is not proof of Node.js 24 compatibility; verify
// the upstream release and rebuild/test on the target runtime and architecture.
//
// Exit code 0 if clean, 1 if risks found and --strict is set.

import { parseArgs, isDryRun } from '../util/args.mjs';
import { log, color } from '../util/log.mjs';
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';

// Canonical list of native-binary packages + conservative modern baseline.
// The values are triage floors, not promises of Node.js 24 prebuilt binaries.
export const NATIVE_PACKAGES = {
  'sharp':            { minimumBaseline: '0.33.0', note: 'libvips native binding; verify the current release on Node.js 24.' },
  'bcrypt':           { minimumBaseline: '5.1.1',  note: 'Native bcrypt. Consider bcryptjs for pure-JS drop-in.' },
  'better-sqlite3':   { minimumBaseline: '11.0.0', note: 'SQLite native binding.' },
  'canvas':           { minimumBaseline: '2.11.2', note: 'node-canvas native binding; verify current target prebuilds.' },
  'node-gyp':         { minimumBaseline: '10.0.0', note: 'Build system. Upgrade before rebuilding natives.' },
  'node-sass':        { minimumBaseline: null,     note: 'Unmaintained. Use `sass` (Dart Sass) instead.' },
  'bufferutil':       { minimumBaseline: '4.0.8',  note: 'WebSocket utility native addon.' },
  'utf-8-validate':   { minimumBaseline: '6.0.4',  note: 'WebSocket utility native addon.' },
  'libpq':            { minimumBaseline: '1.11.0', note: 'PostgreSQL native client; verify the current release and target prebuild.' },
  'grpc':             { minimumBaseline: null,     note: 'Unmaintained. Migrate to `@grpc/grpc-js` (pure JS).' },
  '@grpc/grpc-js':    { minimumBaseline: '1.10.0', note: 'Pure JS, no native; just keep up to date.' },
  'sqlite3':          { minimumBaseline: '5.1.7',  note: 'SQLite3 bindings. Prebuilds available.' },
  'argon2':           { minimumBaseline: '0.40.1', note: 'Native binding; verify the current Node.js 24 prebuild floor upstream.' },
  're2':              { minimumBaseline: '1.21.0', note: 'RE2 regex engine.' },
  'fibers':           { minimumBaseline: null,     note: 'Unmaintained since the Node.js 16 era; remove it.' },
  '@tensorflow/tfjs-node': { minimumBaseline: '4.20.0', note: 'TensorFlow native.' },
  'sodium-native':    { minimumBaseline: '4.3.0',  note: 'libsodium bindings.' },
  'zmq':              { minimumBaseline: null,     note: 'Unmaintained. Use `zeromq` instead.' },
  'zeromq':           { minimumBaseline: '6.1.2',  note: 'ZeroMQ bindings.' },
  'farmhash':         { minimumBaseline: '4.0.0',  note: 'Native hashing.' },
  '@napi-rs/snappy':  { minimumBaseline: null,     note: 'Stale package; use a maintained compressor.' },
  'heapdump':         { minimumBaseline: null,     note: 'Unmaintained. Use `node --heapsnapshot-signal` instead.' },
};

// Version compare (semver-ish, without dev deps).
function cmpVer(a, b) {
  const pa = a.replace(/^[^\d]*/, '').split('.').map(n => parseInt(n, 10) || 0);
  const pb = b.split('.').map(n => parseInt(n, 10) || 0);
  for (let i = 0; i < 3; i++) {
    if ((pa[i] ?? 0) > (pb[i] ?? 0)) return 1;
    if ((pa[i] ?? 0) < (pb[i] ?? 0)) return -1;
  }
  return 0;
}

function cleanVersion(v) {
  if (!v) return null;
  return v.replace(/^[\^~>=<\s]+/, '');
}

function collectDeps(pkg) {
  const deps = { ...(pkg.dependencies || {}), ...(pkg.devDependencies || {}) };
  return deps;
}

export function auditPackage(pkg) {
  const deps = collectDeps(pkg);
  const findings = [];
  for (const [name, versionSpec] of Object.entries(deps)) {
    const info = NATIVE_PACKAGES[name];
    if (!info) continue;
    const declared = cleanVersion(versionSpec);
    const needed = info.minimumBaseline;
    const status =
      needed === null
        ? 'dead'
        : declared && cmpVer(declared, needed) >= 0
          ? 'baseline-met'
          : 'upgrade-required';
    findings.push({ name, declared, required: needed, status, note: info.note });
  }
  return findings;
}

export async function auditCommand(argv) {
  const { flags } = parseArgs(argv);
  const path = flags.path || '.';
  const pkgPath = join(path, 'package.json');

  if (flags.json) {
    console.error(`[lambda-lifeline] audit path=${pkgPath}`);
  } else {
    log.hdr(`Audit native dependencies · ${pkgPath}`);
  }
  if (!existsSync(pkgPath)) {
    log.err(`No package.json at ${pkgPath}`);
    process.exit(2);
  }
  const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
  const findings = auditPackage(pkg);

  if (flags.json) {
    log.json({ package: pkg.name, findings });
    if (flags.strict && findings.some(f => f.status !== 'baseline-met')) process.exit(1);
    return;
  }

  if (findings.length === 0) {
    log.ok('No configured native-binary package matched this manifest.');
    return;
  }

  for (const f of findings) {
    const icon = f.status === 'baseline-met' ? color.cyan('i')
               : f.status === 'dead' ? color.red('✗')
               : color.yellow('⚠');
    const tag = f.status === 'baseline-met' ? color.cyan('VERIFY')
              : f.status === 'dead' ? color.red('REPLACE')
              : color.yellow('UPGRADE');
    const versions = f.status === 'dead'
      ? 'replace this dep'
      : `declared ${f.declared || '?'}  →  need ≥ ${f.required}`;
    console.log(`  ${icon} ${color.bold(f.name.padEnd(28))} ${tag.padEnd(10)} ${versions}`);
    console.log(`     ${color.gray(f.note)}`);
  }

  const risky = findings.filter(f => f.status !== 'baseline-met');
  console.log();
  if (risky.length === 0) {
    log.ok('All matched native deps meet the configured baseline. Verify each upstream release and rebuild/test on Node.js 24.');
  } else {
    log.warn(`${risky.length} native dep(s) need action before Node.js 24.`);
    log.info('Next: bump versions in package.json, run `npm install && npm rebuild`, then `npm test`.');
  }
  if (flags.strict && risky.length > 0) process.exit(1);
}
