import { test } from 'node:test';
import assert from 'node:assert/strict';
import { rollbackCommand } from '../src/rollback/index.mjs';

function fixture(current, pages) {
  class GetAliasCommand { constructor(input) { this.input = input; } }
  class ListVersionsByFunctionCommand { constructor(input) { this.input = input; } }
  class UpdateAliasCommand { constructor(input) { this.input = input; } }
  const Lambda = { GetAliasCommand, ListVersionsByFunctionCommand, UpdateAliasCommand };
  const calls = [];
  let page = 0;
  const client = { send: async command => {
    calls.push(command);
    if (command instanceof GetAliasCommand) return { FunctionVersion: current, RevisionId: 'fixture-revision' };
    if (command instanceof ListVersionsByFunctionCommand) {
      const Versions = pages[page++].map(Version => ({ Version }));
      return { Versions, ...(page < pages.length ? { NextMarker: String(page) } : {}) };
    }
    if (command instanceof UpdateAliasCommand) return {};
    throw new Error('Unexpected fixture command');
  } };
  return { Lambda, client, calls, updates: () => calls.filter(call => call instanceof UpdateAliasCommand) };
}

test('rollback refuses a newer fallback when the alias is already oldest', async () => {
  for (const apply of [false, true]) {
    const sdk = fixture('1', [['$LATEST', '1', '2', '3']]);
    await assert.rejects(rollbackCommand(['--function', 'fixture-only', ...(apply ? ['--apply'] : [])], sdk), /No prior numbered version/);
    assert.equal(sdk.updates().length, 0);
  }
});

test('rollback dry-run reads all pages and never updates an alias', async () => {
  const sdk = fixture('7', [['$LATEST', '9', '7'], ['2', '6']]);
  await rollbackCommand(['--function', 'fixture-only'], sdk);
  assert.equal(sdk.calls.length, 3);
  assert.equal(sdk.updates().length, 0);
});

test('rollback applies the highest existing older version with revision guard', async () => {
  const sdk = fixture('7', [['$LATEST', '9', '7'], ['2', '6']]);
  await rollbackCommand(['--function', 'fixture-only', '--apply'], sdk);
  assert.deepEqual(sdk.updates().map(command => command.input), [{
    FunctionName: 'fixture-only', Name: 'live', FunctionVersion: '6', RoutingConfig: {}, RevisionId: 'fixture-revision',
  }]);
});

test('rollback validates published version identifiers before mutation', async () => {
  for (const version of ['$LATEST', 'bad', '0']) {
    const sdk = fixture('7', []);
    await assert.rejects(rollbackCommand(['--function', 'fixture-only', '--to-version', version, '--apply'], sdk), /published version/);
    assert.equal(sdk.updates().length, 0);
  }
});
