import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

function requiredIntegerStatistic(extension, name, sampleIndex) {
  const matches = (extension.statistics || []).filter(
    statistic => statistic.statisticName === name
  );
  if (
    matches.length !== 1 ||
    typeof matches[0].value !== 'number' ||
    !Number.isSafeInteger(matches[0].value) ||
    matches[0].value < 0
  ) {
    throw new Error(
      `sample ${sampleIndex + 1}: missing or invalid ${name} statistic`
    );
  }
  return matches[0].value;
}

function parseSample(sample, sampleIndex, expectedId, expectedVersion) {
  const extensions = sample?.results?.[0]?.extensions;
  if (!Array.isArray(extensions) || extensions.length !== 1) {
    throw new Error(
      `sample ${sampleIndex + 1}: expected one exact VS Marketplace result`
    );
  }

  const extension = extensions[0];
  const extensionId = `${extension?.publisher?.publisherName}.${extension?.extensionName}`;
  const version = extension?.versions?.[0]?.version;
  if (extensionId !== expectedId || version !== expectedVersion) {
    throw new Error(
      `sample ${sampleIndex + 1}: expected ${expectedId}@${expectedVersion}, ` +
      `observed ${extensionId}@${String(version)}`
    );
  }
  if (typeof extension.lastUpdated !== 'string' || !extension.lastUpdated) {
    throw new Error(`sample ${sampleIndex + 1}: missing lastUpdated`);
  }

  return {
    extensionId,
    version,
    lastUpdated: extension.lastUpdated,
    installs: requiredIntegerStatistic(extension, 'install', sampleIndex),
    downloads: requiredIntegerStatistic(extension, 'downloadCount', sampleIndex)
  };
}

function allEqual(values) {
  return values.every(value => value === values[0]);
}

export function summarizeGallerySamples(samples, expectedId, expectedVersion) {
  if (!Array.isArray(samples) || samples.length < 3) {
    throw new Error('at least three independent Gallery samples are required');
  }
  if (!expectedId || !expectedVersion) {
    throw new Error('expected extension identity and version are required');
  }

  const parsed = samples.map((sample, index) =>
    parseSample(sample, index, expectedId, expectedVersion)
  );
  const installs = parsed.map(sample => sample.installs);
  const downloads = parsed.map(sample => sample.downloads);
  const lastUpdated = parsed.map(sample => sample.lastUpdated);

  return {
    extension_id: expectedId,
    version: expectedVersion,
    last_updated: lastUpdated[0],
    sample_count: parsed.length,
    replication_consistent:
      allEqual(installs) && allEqual(downloads) && allEqual(lastUpdated),
    samples: { installs, downloads },
    lower_bound: {
      installs: Math.min(...installs),
      downloads: Math.min(...downloads)
    },
    upper_bound: {
      installs: Math.max(...installs),
      downloads: Math.max(...downloads)
    }
  };
}

export function evaluateSignalGate({
  lowerBoundInstalls,
  upperBoundInstalls,
  baselineInstalls,
  externalAuthors,
  observedAt,
  gateAt
}) {
  for (const [name, value] of Object.entries({
    lowerBoundInstalls,
    upperBoundInstalls,
    baselineInstalls,
    externalAuthors
  })) {
    if (!Number.isSafeInteger(value) || value < 0) {
      throw new Error(`${name} must be a non-negative integer`);
    }
  }
  const observedEpoch = Date.parse(observedAt);
  const gateEpoch = Date.parse(gateAt);
  if (!Number.isFinite(observedEpoch) || !Number.isFinite(gateEpoch)) {
    throw new Error('observedAt and gateAt must be valid timestamps');
  }

  if (lowerBoundInstalls > baselineInstalls || externalAuthors > 0) return 'passed';
  if (observedEpoch < gateEpoch) return 'pending';
  if (upperBoundInstalls > baselineInstalls) return 'inconclusive_gallery_replication';
  return 'failed_reposition_required';
}

function requiredEnvironmentInteger(name) {
  const value = process.env[name];
  if (!/^\d+$/.test(value || '')) {
    throw new Error(`${name} must be a non-negative integer`);
  }
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed)) {
    throw new Error(`${name} exceeds the safe integer range`);
  }
  return parsed;
}

function runCli() {
  const [samplesPath] = process.argv.slice(2);
  const expectedId = process.env.VSCODE_EXTENSION_ID;
  const expectedVersion = process.env.VSCODE_RELEASE_VERSION;
  if (!samplesPath) {
    throw new Error('usage: node scripts/vscode-gallery-evidence.mjs <samples.json>');
  }
  const samples = JSON.parse(readFileSync(samplesPath, 'utf8'));
  const summary = summarizeGallerySamples(samples, expectedId, expectedVersion);
  const baselineInstalls = requiredEnvironmentInteger('VSCODE_BASELINE_INSTALLS');
  const baselineDownloads = requiredEnvironmentInteger('VSCODE_BASELINE_DOWNLOADS');
  const externalAuthors = requiredEnvironmentInteger('VSCODE_EXTERNAL_AUTHORS');
  const observedAt = process.env.VSCODE_OBSERVED_AT;
  const gateAt = process.env.VSCODE_SIGNAL_GATE_AT;
  if (!observedAt || !gateAt) {
    throw new Error('VSCODE_OBSERVED_AT and VSCODE_SIGNAL_GATE_AT are required');
  }
  const evidence = {
    ...summary,
    release_baseline: {
      installs: baselineInstalls,
      downloads: baselineDownloads
    },
    delta_from_release_baseline: {
      installs: summary.lower_bound.installs - baselineInstalls,
      downloads: summary.lower_bound.downloads - baselineDownloads
    },
    signal_gate_at: gateAt,
    signal_gate: evaluateSignalGate({
      lowerBoundInstalls: summary.lower_bound.installs,
      upperBoundInstalls: summary.upper_bound.installs,
      baselineInstalls,
      externalAuthors,
      observedAt,
      gateAt
    })
  };
  process.stdout.write(
    `${JSON.stringify(evidence, null, 2)}\n`
  );
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    runCli();
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}
