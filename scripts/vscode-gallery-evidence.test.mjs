import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  evaluateSignalGate,
  summarizeGallerySamples
} from './vscode-gallery-evidence.mjs';

const EXPECTED_ID = 'rupture.rupture-vscode';
const EXPECTED_VERSION = '1.2.0';

function sample(installs, downloads, overrides = {}) {
  return {
    results: [
      {
        extensions: [
          {
            publisher: { publisherName: 'rupture' },
            extensionName: 'rupture-vscode',
            lastUpdated: '2026-08-31T23:27:55Z',
            versions: [{ version: EXPECTED_VERSION }],
            statistics: [
              { statisticName: 'install', value: installs },
              { statisticName: 'downloadCount', value: downloads }
            ],
            ...overrides
          }
        ]
      }
    ]
  };
}

test('uses the conservative lower bound when Gallery replicas disagree', () => {
  const result = summarizeGallerySamples(
    [sample(103, 223), sample(104, 223), sample(104, 224), sample(103, 224), sample(104, 224)],
    EXPECTED_ID,
    EXPECTED_VERSION
  );

  assert.equal(result.sample_count, 5);
  assert.equal(result.replication_consistent, false);
  assert.deepEqual(result.samples.installs, [103, 104, 104, 103, 104]);
  assert.deepEqual(result.lower_bound, { installs: 103, downloads: 223 });
  assert.deepEqual(result.upper_bound, { installs: 104, downloads: 224 });
});

test('marks matching replicas consistent', () => {
  const result = summarizeGallerySamples(
    [sample(105, 230), sample(105, 230), sample(105, 230)],
    EXPECTED_ID,
    EXPECTED_VERSION
  );

  assert.equal(result.replication_consistent, true);
  assert.equal(result.lower_bound.installs, 105);
  assert.equal(result.upper_bound.installs, 105);
});

test('fails closed on identity or version drift', () => {
  assert.throws(
    () => summarizeGallerySamples(
      [sample(103, 223), sample(103, 223), sample(103, 223, { extensionName: 'other' })],
      EXPECTED_ID,
      EXPECTED_VERSION
    ),
    /expected rupture\.rupture-vscode@1\.2\.0/
  );
});

test('fails closed on malformed counters or too few samples', () => {
  assert.throws(
    () => summarizeGallerySamples(
      [sample(103, 223), sample(103, 223), sample(103.5, 223)],
      EXPECTED_ID,
      EXPECTED_VERSION
    ),
    /invalid install statistic/
  );
  assert.throws(
    () => summarizeGallerySamples(
      [sample(103, 223), sample(103, 223)],
      EXPECTED_ID,
      EXPECTED_VERSION
    ),
    /at least three/
  );
});

test('signal gate passes only a conservative increase or qualified author', () => {
  const base = {
    lowerBoundInstalls: 103,
    upperBoundInstalls: 104,
    baselineInstalls: 103,
    externalAuthors: 0,
    observedAt: '2026-09-06T00:00:00Z',
    gateAt: '2026-09-05T23:27:55Z'
  };
  assert.equal(
    evaluateSignalGate(base),
    'inconclusive_gallery_replication'
  );
  assert.equal(
    evaluateSignalGate({ ...base, lowerBoundInstalls: 104 }),
    'passed'
  );
  assert.equal(
    evaluateSignalGate({ ...base, externalAuthors: 1 }),
    'passed'
  );
});

test('signal gate remains pending before its deadline and fails after stable zero signal', () => {
  const base = {
    lowerBoundInstalls: 103,
    upperBoundInstalls: 103,
    baselineInstalls: 103,
    externalAuthors: 0,
    observedAt: '2026-09-04T00:00:00Z',
    gateAt: '2026-09-05T23:27:55Z'
  };
  assert.equal(evaluateSignalGate(base), 'pending');
  assert.equal(
    evaluateSignalGate({ ...base, observedAt: '2026-09-06T00:00:00Z' }),
    'failed_reposition_required'
  );
});
