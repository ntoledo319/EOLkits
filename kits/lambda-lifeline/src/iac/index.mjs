// IaC patcher for SAM template.yaml, CDK (TypeScript/JavaScript), and Terraform HCL.
// Pattern-based edits that preserve comments, indentation, and surrounding structure.
// Dry-run by default; --apply writes in place.

import { parseArgs, isDryRun, list } from '../util/args.mjs';
import { log, color } from '../util/log.mjs';
import { readFileSync, writeFileSync, statSync } from 'node:fs';
import { readdir } from 'node:fs/promises';
import { join, basename, relative } from 'node:path';
import { patchManifest } from './manifest.mjs';
import { patchTerraform } from './terraform.mjs';

const IGNORE_DIRS = new Set(['node_modules', '.git', 'dist', 'build', '.aws-sam', 'cdk.out', '.terraform', 'coverage']);

const DEFAULT_FROM = ['nodejs14.x', 'nodejs16.x', 'nodejs18.x', 'nodejs20.x', 'nodejs22.x'];
const DEFAULT_TO = 'nodejs24.x';

// File-type detectors
function isSAM(file, content) {
  if (!/\.(ya?ml|json)$/.test(file)) return false;
  return /AWS::Serverless(?:::|-)/.test(content);
}
function isCloudFormation(file, content) {
  if (!/\.(ya?ml|json)$/.test(file)) return false;
  if (file.endsWith('.json') || content.trimStart().startsWith('{')) {
    try {
      const root = JSON.parse(content);
      return root !== null && typeof root === 'object'
        && ('Resources' in root || ('Globals' in root && 'Transform' in root));
    } catch {
      // Known template structure must surface its parse error, never a clean scan.
      return /"Resources"\s*:|AWS::(?:Lambda|Serverless)/.test(content) || basename(file) === 'template.json';
    }
  }
  return /AWS::Lambda::Function|^\s*['"]?Resources['"]?\s*:/m.test(content);
}
function isCDK(file, content) {
  if (!/\.(ts|js|mjs)$/.test(file)) return false;
  return /lambda\.Runtime\.NODEJS_\d+_X/i.test(content) || /Runtime\.NODEJS_\d+_X/.test(content);
}
function isTerraform(file) {
  return /\.(tf|tf\.json)$/.test(file);
}

// CDK: lambda.Runtime.NODEJS_20_X → lambda.Runtime.NODEJS_24_X
function patchCDK(content, from, to) {
  const fromVers = from.map(r => r.match(/nodejs(\d+)/)[1]);
  const toVer = to.match(/nodejs(\d+)/)[1];
  let changed = content;
  const hits = [];
  for (const v of fromVers) {
    const re = new RegExp(`(Runtime\\.NODEJS_)${v}(_X)`, 'g');
    changed = changed.replace(re, (m, pre, suf) => {
      hits.push(`NODEJS_${v}_X`);
      return `${pre}${toVer}${suf}`;
    });
  }
  return { changed, hits };
}

async function walk(dir, files = []) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (IGNORE_DIRS.has(entry.name) || entry.name.startsWith('.')) continue;
    const full = join(dir, entry.name);
    if (entry.isDirectory()) await walk(full, files);
    else if (entry.isFile()) files.push(full);
  }
  return files;
}

export async function iacCommand(argv) {
  const { flags } = parseArgs(argv);
  const path = flags.path || '.';
  const apply = !isDryRun(flags);
  const fromRuntimes = list(flags.from).length ? list(flags.from) : DEFAULT_FROM;
  const toRuntime = flags.to || DEFAULT_TO;
  if (![...fromRuntimes, toRuntime].every(runtime => /^nodejs\d+\.x$/.test(runtime))) {
    throw new Error('--from and --to must be literal Node.js Lambda runtimes, such as nodejs20.x.');
  }

  log.hdr(`IaC patcher · ${path} · ${fromRuntimes.join(',')} → ${toRuntime} · ${apply ? color.red('APPLY') : color.yellow('DRY-RUN')}`);

  const files = statSync(path).isDirectory() ? await walk(path) : [path];
  const relevant = files.filter(f => /\.(ya?ml|json|ts|tsx|js|mjs|tf|tf\.json)$/.test(f));
  log.dim(`  scanning ${relevant.length} candidate file(s)`);

  let totalHits = 0;
  let filesChanged = 0;
  const pending = [];

  for (const file of relevant) {
    const original = readFileSync(file, 'utf8');
    let result = { changed: original, hits: [] };
    let kind = null;

    try {
      if (/\.tf\.json$/.test(file)) {
        result = patchManifest(original, { json: true, terraform: true, from: fromRuntimes, to: toRuntime });
        kind = 'Terraform';
      } else if (/^serverless\.(ya?ml|json)$/.test(basename(file))) {
        result = patchManifest(original, { json: file.endsWith('.json'), serverless: true, from: fromRuntimes, to: toRuntime });
        kind = 'Serverless';
      } else if (isSAM(file, original) || isCloudFormation(file, original)) {
        result = patchManifest(original, { json: file.endsWith('.json'), from: fromRuntimes, to: toRuntime });
        kind = 'SAM/CFN';
      } else if (isCDK(file, original)) {
        result = patchCDK(original, fromRuntimes, toRuntime);
        kind = 'CDK';
      } else if (isTerraform(file)) {
        result = patchTerraform(original, fromRuntimes, toRuntime);
        kind = 'Terraform';
      }
    } catch (error) {
      throw new Error(`${file}: ${error.message}`);
    }

    if (result.hits.length) {
      filesChanged++;
      totalHits += result.hits.length;
      const rel = relative(process.cwd(), file);
      log.info(`${color.green('[' + kind + ']')} ${rel} · ${result.hits.length} runtime ref(s): ${result.hits.join(', ')}`);
      pending.push({ file, changed: result.changed });
    }
  }
  // Parse the whole batch first, so a malformed later template cannot leave an
  // earlier one changed. Review remains required before infrastructure deploys.
  if (apply) for (const { file, changed } of pending) writeFileSync(file, changed);

  console.log();
  if (filesChanged === 0) {
    log.ok('No IaC runtime references needed patching.');
  } else {
    log.ok(`${filesChanged} file(s) · ${totalHits} runtime ref(s) ${apply ? color.green('updated') : color.yellow('would be updated')}.`);
    if (!apply) log.info('Re-run with --apply to write changes. Review diff with `git diff`.');
  }
  if (flags.strict && !apply && filesChanged > 0) process.exit(1);
}
