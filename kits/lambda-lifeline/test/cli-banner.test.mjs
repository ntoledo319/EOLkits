import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { join, dirname } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CLI = join(__dirname, '..', 'bin', 'cli.mjs');
const FIXTURE = join(__dirname, 'fixtures', 'lambda-inventory.json');
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function run(args) {
  return spawnSync('node', [CLI, ...args], { encoding: 'utf8' });
}

// '2027-08-31' -> 'Aug 31, 2027'. Keeps the two-digit day so the banner box keeps its width.
function bannerDate(iso) {
  const [y, m, d] = iso.split('-');
  return `${MONTHS[Number(m) - 1]} ${d}, ${y}`;
}

test('--help banner shows the nodejs20.x dates the scanner uses', () => {
  const scan = run(['scan', '--fixture', FIXTURE, '--json']);
  assert.equal(scan.status, 0, scan.stderr);
  const node20 = JSON.parse(scan.stdout).find(fn => fn.runtime === 'nodejs20.x');
  assert.ok(node20, 'fixture has a nodejs20.x function');
  const { phase1, block_update } = node20.deprecation_dates;

  const help = run(['--help']);
  assert.equal(help.status, 0, help.stderr);
  const patches = `${bannerDate(phase1)} (patches)`;
  const updates = `${bannerDate(block_update)} (updates)`;
  assert.ok(help.stdout.includes(patches), `banner should say "${patches}"`);
  assert.ok(help.stdout.includes(updates), `banner should say "${updates}"`);
});

test('--help banner box lines all have the same width', () => {
  const help = run(['--help']);
  assert.equal(help.status, 0, help.stderr);
  const box = help.stdout.split('\n').filter(line => /^ [╔║╚]/.test(line));
  assert.equal(box.length, 5);
  const widths = new Set(box.map(line => [...line].length));
  assert.equal(widths.size, 1, `box widths differ: ${box.map(line => [...line].length).join(', ')}`);
});
