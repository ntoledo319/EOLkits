import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { alarmProblem, deployStages, stableAliasProblem } from '../src/deploy/index.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CLI = join(__dirname, '..', 'bin', 'cli.mjs');

function run(args) {
  return spawnSync('node', [CLI, ...args], { encoding: 'utf8' });
}

test('plan --function prints a numbered deployment plan', () => {
  const r = run(['plan', '--function', 'my-fn']);
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /Deploy plan for my-fn/);
  assert.match(r.stdout, /Verify alias "live"/);
  assert.match(r.stdout, /Publish new version/);
  assert.match(r.stdout, /weighted routing/);
  assert.match(r.stdout, /rollback/i);
});

test('plan honors custom stages', () => {
  const r = run(['plan', '--function', 'x', '--alias', 'canary', '--stages', '10,50,100', '--wait-minutes', '5']);
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /alias "canary"/);
  assert.match(r.stdout, /Shift 10%/);
  assert.match(r.stdout, /Shift 50%/);
  assert.match(r.stdout, /hold 5 min/);
});

test('deploy stage validation rejects unsafe sequences', () => {
  assert.deepEqual(deployStages(undefined), [5, 25, 50, 100]);
  assert.throws(() => deployStages('5,101'), /1 through 100/);
  assert.throws(() => deployStages('50,25,100'), /strictly increasing/);
  assert.throws(() => deployStages('5,50'), /final deploy stage must be 100/);
  assert.throws(() => deployStages('5,nope,100'), /integers/);
});

test('deploy preflight requires a stable alias and healthy named alarms', async () => {
  assert.equal(stableAliasProblem({ FunctionVersion: '7' }), null);
  assert.match(stableAliasProblem({ FunctionVersion: '$LATEST' }), /published/);
  assert.match(
    stableAliasProblem({
      FunctionVersion: '7',
      RoutingConfig: { AdditionalVersionWeights: { 8: 0.1 } },
    }),
    /canary/
  );

  class DescribeAlarmsCommand {
    constructor(input) { this.input = input; }
  }
  const CW = { DescribeAlarmsCommand };
  const healthy = {
    send: async command => ({
      MetricAlarms: command.input.AlarmNames.map(AlarmName => ({ AlarmName, StateValue: 'OK' })),
    }),
  };
  assert.equal(await alarmProblem(healthy, CW, ['alarm-a', 'alarm-b']), null);

  const missing = { send: async () => ({ MetricAlarms: [] }) };
  assert.match(await alarmProblem(missing, CW, ['alarm-a']), /not found/);

  const alarming = {
    send: async () => ({ MetricAlarms: [{ AlarmName: 'alarm-a', StateValue: 'ALARM' }] }),
  };
  assert.match(await alarmProblem(alarming, CW, ['alarm-a']), /not OK/);
});

test('deploy without --apply stays in dry-run (no AWS calls)', () => {
  const r = run(['deploy', '--function', 'my-fn']);
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /DRY-RUN/);
});

test('deploy --apply without --alarm throws', () => {
  const r = run(['deploy', '--function', 'x', '--apply']);
  assert.notEqual(r.status, 0);
  assert.match(r.stderr + r.stdout, /--alarm/);
});
