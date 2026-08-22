// Staged canary deploy with rollback guard.
//   1. Publishes a new Lambda version with the new runtime
//   2. Routes traffic to it via a weighted alias
//   3. Steps through stages (e.g. 5% → 25% → 50% → 100%)
//   4. At each stage, verifies a CloudWatch alarm ARN is NOT in ALARM state
//   5. If any alarm trips, auto-rollback to previous version
//
// Dry-run prints the plan. --apply executes.

import { parseArgs, isDryRun, requireFlag, list } from '../util/args.mjs';
import { log, color } from '../util/log.mjs';
import { setTimeout as sleep } from 'node:timers/promises';

const DEFAULT_STAGES = [5, 25, 50, 100];

export function deployStages(value) {
  const raw = list(value);
  const stages = raw.length ? raw.map(Number) : DEFAULT_STAGES;
  if (stages.some(stage => !Number.isInteger(stage) || stage <= 0 || stage > 100)) {
    throw new Error('--stages must contain integers from 1 through 100.');
  }
  if (stages.some((stage, index) => index > 0 && stage <= stages[index - 1])) {
    throw new Error('--stages must be unique and strictly increasing.');
  }
  if (stages.at(-1) !== 100) {
    throw new Error('The final deploy stage must be 100.');
  }
  return stages;
}

function positiveWait(value) {
  const wait = Number(value ?? 10);
  if (!Number.isInteger(wait) || wait <= 0) {
    throw new Error('--wait-minutes must be a positive integer.');
  }
  return wait;
}

export function stableAliasProblem(alias) {
  const version = alias?.FunctionVersion;
  const weights = alias?.RoutingConfig?.AdditionalVersionWeights || {};
  if (!version || version === '$LATEST') return 'alias has no published stable version';
  if (Object.keys(weights).length > 0) return 'alias already has canary weights';
  return null;
}

export async function planCommand(argv) {
  const { flags } = parseArgs(argv);
  const fn = requireFlag(flags, 'function');
  const newRuntime = flags['new-runtime'] || 'nodejs24.x';
  const alias = flags.alias || 'live';
  const stages = deployStages(flags.stages);
  const plan = buildPlan({ fn, newRuntime, alias, stages, wait: positiveWait(flags['wait-minutes']) });
  log.hdr(`Deploy plan for ${color.bold(fn)}`);
  for (const step of plan) {
    console.log(`  ${color.cyan(String(step.n).padStart(2))}. ${step.desc}`);
  }
  log.info('Run with `deploy --apply` to execute.');
}

function buildPlan({ fn, newRuntime, alias, stages, wait }) {
  const steps = [];
  steps.push({ n: 1, desc: `Verify alias "${alias}" has one stable version and every alarm is OK` });
  steps.push({ n: 2, desc: `Update function runtime → ${newRuntime}` });
  steps.push({ n: 3, desc: `Publish new version (N+1)` });
  let s = 4;
  for (const weight of stages) {
    steps.push({
      n: s++,
      desc: weight === 100
        ? `Cut alias to N+1 · hold ${wait} min · check alarms`
        : `Shift ${weight}% of traffic to N+1 with weighted routing · hold ${wait} min · check alarms`,
    });
  }
  steps.push({ n: s, desc: `On any alarm trip: auto-rollback alias to LATEST_STABLE and halt` });
  return steps;
}

export async function deployCommand(argv) {
  const { flags } = parseArgs(argv);
  const apply = !isDryRun(flags);
  const fn = requireFlag(flags, 'function');
  const newRuntime = flags['new-runtime'] || 'nodejs24.x';
  const aliasName = flags.alias || 'live';
  const stagesList = deployStages(flags.stages);
  const waitMinutes = positiveWait(flags['wait-minutes']);
  const alarms = list(flags.alarm);
  const region = flags.region || process.env.AWS_REGION || 'us-east-1';

  log.hdr(`Deploy · ${fn} → ${newRuntime} · ${apply ? color.red('APPLY') : color.yellow('DRY-RUN')}`);
  if (!apply) {
    const plan = buildPlan({ fn, newRuntime, alias: aliasName, stages: stagesList, wait: waitMinutes });
    for (const p of plan) console.log(`  ${color.cyan(p.n)}. ${p.desc}`);
    log.warn('Dry-run complete. Pass --apply (and --alarm <cw-alarm-arn>) to execute.');
    return;
  }

  if (alarms.length === 0) {
    throw new Error('--apply requires at least one --alarm <CloudWatchAlarmArn> for the rollback guard.');
  }

  const Lambda = await import('@aws-sdk/client-lambda');
  const CW = await import('@aws-sdk/client-cloudwatch');
  const lambda = new Lambda.LambdaClient({ region });
  const cw = new CW.CloudWatchClient({ region });

  log.info('1. Verifying rollback target and alarms…');
  let currentAlias;
  try {
    currentAlias = await lambda.send(
      new Lambda.GetAliasCommand({ FunctionName: fn, Name: aliasName })
    );
  } catch (error) {
    if (error?.name === 'ResourceNotFoundException') {
      throw new Error(
        `Alias ${aliasName} does not exist on ${fn}. Create a published-version alias before deploying.`
      );
    }
    throw error;
  }
  const stableVersion = currentAlias?.FunctionVersion;
  const aliasProblem = stableAliasProblem(currentAlias);
  if (aliasProblem) {
    throw new Error(
      `Alias ${aliasName} is unsafe: ${aliasProblem}. It must point to one published stable version.`
    );
  }
  const initialAlarmProblem = await alarmProblem(cw, CW, alarms);
  if (initialAlarmProblem) {
    throw new Error(`${initialAlarmProblem}; refusing to mutate the function.`);
  }
  log.dim(`   LATEST_STABLE = ${stableVersion}`);

  log.info(`2. Updating function runtime → ${newRuntime}…`);
  await lambda.send(new Lambda.UpdateFunctionConfigurationCommand({
    FunctionName: fn,
    Runtime: newRuntime,
  }));
  await waitForUpdate(lambda, Lambda, fn);

  log.info('3. Publishing new version…');
  const published = await lambda.send(new Lambda.PublishVersionCommand({ FunctionName: fn }));
  const newVersion = published.Version;
  log.ok(`   Published version ${newVersion}`);

  for (const weight of stagesList) {
    const pct = weight / 100;
    log.info(`5. Shifting ${weight}% traffic to version ${newVersion}…`);
    try {
      if (weight === 100) {
        await lambda.send(new Lambda.UpdateAliasCommand({
          FunctionName: fn, Name: aliasName, FunctionVersion: newVersion, RoutingConfig: {},
        }));
        log.ok('   100% cutover complete.');
      } else {
        await lambda.send(new Lambda.UpdateAliasCommand({
          FunctionName: fn,
          Name: aliasName,
          FunctionVersion: stableVersion,
          RoutingConfig: { AdditionalVersionWeights: { [newVersion]: pct } },
        }));
      }
      log.dim(`   holding ${waitMinutes} min — checking alarms every minute…`);
      for (let minute = 0; minute < waitMinutes; minute++) {
        await sleep(60_000);
        const problem = await alarmProblem(cw, CW, alarms);
        if (problem) throw new Error(problem);
      }
    } catch (monitorError) {
      log.err(`CANARY MONITOR FAILED: ${monitorError.message} — rolling back to ${stableVersion}`);
      try {
        await lambda.send(new Lambda.UpdateAliasCommand({
          FunctionName: fn, Name: aliasName, FunctionVersion: stableVersion, RoutingConfig: {},
        }));
      } catch (rollbackError) {
        throw new Error(
          `Canary monitoring failed and alias rollback also failed: ${rollbackError.message}`
        );
      }
      log.ok('rollback complete');
      throw new Error(`Canary aborted and rolled back: ${monitorError.message}`);
    }
  }
  log.ok('Deployment complete. Run `lambda-lifeline rollback --function ' + fn + '` if issues surface later.');
}

export async function alarmProblem(cw, CW, arns) {
  const names = [...new Set(arns.map(a => a.split(':alarm:').pop()).filter(Boolean))];
  const resp = await cw.send(new CW.DescribeAlarmsCommand({ AlarmNames: names }));
  const alarms = [...(resp.MetricAlarms || []), ...(resp.CompositeAlarms || [])];
  const byName = new Map(alarms.map(alarm => [alarm.AlarmName, alarm.StateValue]));
  const missing = names.filter(name => !byName.has(name));
  if (missing.length) return `alarm not found: ${missing.join(', ')}`;
  const unhealthy = names.filter(name => byName.get(name) !== 'OK');
  if (unhealthy.length) {
    return `alarm not OK: ${unhealthy.map(name => `${name}=${byName.get(name)}`).join(', ')}`;
  }
  return null;
}

async function waitForUpdate(client, Lambda, fn) {
  for (let i = 0; i < 60; i++) {
    const cfg = await client.send(new Lambda.GetFunctionConfigurationCommand({ FunctionName: fn }));
    if (cfg.LastUpdateStatus === 'Successful') return;
    if (cfg.LastUpdateStatus === 'Failed') throw new Error(`Update failed: ${cfg.LastUpdateStatusReason}`);
    await sleep(2000);
  }
  throw new Error('Timed out waiting for function update to settle.');
}
