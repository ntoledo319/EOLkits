// Roll a function alias back to its previous version.
// Lists published versions and chooses the greatest one below the current alias.
// This is not deployment history; operators may select an explicit known target.

import { parseArgs, isDryRun, requireFlag } from '../util/args.mjs';
import { log, color } from '../util/log.mjs';

export async function rollbackCommand(argv, dependencies = {}) {
  const { flags } = parseArgs(argv);
  const apply = !isDryRun(flags);
  const fn = requireFlag(flags, 'function');
  const aliasName = flags.alias || 'live';
  const region = flags.region || process.env.AWS_REGION || 'us-east-1';
  const toVersion = flags['to-version']; // optional explicit version
  if (toVersion !== undefined && !/^[1-9]\d*$/.test(String(toVersion))) {
    throw new Error('--to-version must be a positive numbered published version.');
  }

  log.hdr(`Rollback · ${fn} alias ${aliasName} · ${apply ? color.red('APPLY') : color.yellow('DRY-RUN')}`);

  const Lambda = dependencies.Lambda || await import('@aws-sdk/client-lambda');
  const client = dependencies.client || new Lambda.LambdaClient({ region });

  const alias = await client.send(new Lambda.GetAliasCommand({ FunctionName: fn, Name: aliasName }));
  const current = alias.FunctionVersion;
  if (!/^[1-9]\d*$/.test(String(current))) {
    throw new Error('Alias must point to a positive numbered published version.');
  }
  log.info(`current alias → version ${current}`);

  let target = toVersion;
  if (!target) {
    // enumerate versions, pick the one just below current
    const versions = [];
    let Marker;
    do {
      const resp = await client.send(new Lambda.ListVersionsByFunctionCommand({ FunctionName: fn, Marker }));
      for (const v of resp.Versions || []) {
        if (/^[1-9]\d*$/.test(String(v.Version)) && BigInt(v.Version) < BigInt(current)) {
          versions.push(BigInt(v.Version));
        }
      }
      Marker = resp.NextMarker;
    } while (Marker);
    if (versions.length === 0) throw new Error('No prior numbered version exists — cannot rollback.');
    target = String(versions.reduce((older, version) => version > older ? version : older));
  }
  log.info(`target version → ${target}`);

  if (!apply) {
    log.warn('Dry-run. Pass --apply to roll back.');
    return;
  }

  await client.send(new Lambda.UpdateAliasCommand({
    FunctionName: fn, Name: aliasName, FunctionVersion: target, RoutingConfig: {},
    ...(alias.RevisionId ? { RevisionId: alias.RevisionId } : {}),
  }));
  log.ok(`rolled ${fn}@${aliasName} → ${target}`);
}
