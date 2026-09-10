// Example Lambda handler with selected Node.js migration checks.
import config from './config.json' with { type: 'json' };
import settings from './settings.json' with { type: 'json' };

// Modern dynamic import attribute — this one should not be flagged.
async function loadFeatureFlags() {
  const flags = await import('./flags.json', { with: { type: 'json' } });
  return flags.default;
}

// Buffer.toString with a negative end index — throws RangeError on Node.js 22+
export function decodeLastByte(buf) {
  return buf.toString('utf8', 0, -1);
}

// Stream constructor with no explicit highWaterMark — lint warning
import { Readable } from 'node:stream';
export function makeStream(data) {
  return new Readable({
    read() { this.push(data); this.push(null); }
  });
}

export const handler = async (event) => {
  const flags = await loadFeatureFlags();
  return {
    statusCode: 200,
    body: JSON.stringify({ config, settings, flags, event }),
  };
};
