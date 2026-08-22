#!/usr/bin/env node

import fs from 'node:fs';

const lockfiles = process.argv.slice(2);
if (!lockfiles.length) {
  console.error('usage: audit-node-locks.mjs <package-lock.json> [...]');
  process.exit(2);
}

const forbidden = /(?:^|\W)(?:AGPL|GPL|LGPL|SSPL|BUSL|BSL)(?:\W|$)/i;
let audited = 0;
const failures = [];

for (const lockfile of lockfiles) {
  const lock = JSON.parse(fs.readFileSync(lockfile, 'utf8'));
  for (const [path, metadata] of Object.entries(lock.packages || {})) {
    if (!path || metadata.dev === true || metadata.optional === true) continue;
    const name = metadata.name || path.split('node_modules/').at(-1);
    const license = String(metadata.license || '').trim();
    audited += 1;
    if (!license) failures.push(`${lockfile}: ${name}@${metadata.version || '?'} has no declared license`);
    if (forbidden.test(license)) {
      failures.push(`${lockfile}: ${name}@${metadata.version || '?'} declares ${license}`);
    }
  }
}

if (failures.length) {
  console.error(failures.join('\n'));
  process.exit(1);
}
console.log(`audited ${audited} non-dev Node package records; no forbidden or missing license declarations`);
