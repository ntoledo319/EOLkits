/**
 * Tombstone for the retired EOLkits Cloudflare commerce Worker.
 *
 * The replacement Audit v2 service lives in apps/grace-api. Keeping this
 * deployment intentionally tiny prevents an old route or environment toggle
 * from reviving unfulfillable checkout and subscription handlers.
 */

export interface Env {
  ENVIRONMENT?: string;
}

const REPLACEMENT = 'https://eolkits.com/api/capabilities';

const HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Cache-Control': 'no-store',
  'Content-Type': 'application/json; charset=utf-8',
  'X-Content-Type-Options': 'nosniff',
};

function json(body: Record<string, unknown>, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: HEADERS });
}

export default {
  async fetch(request: Request): Promise<Response> {
    const path = new URL(request.url).pathname;
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: HEADERS });
    }
    if (path === '/health' || path === '/status' || path === '/status.json') {
      return json({ ok: false, retired: true, replacement: REPLACEMENT });
    }
    return json(
      {
        error: 'This legacy commerce service is retired.',
        replacement: REPLACEMENT,
      },
      410
    );
  },

  async queue(batch: MessageBatch<unknown>): Promise<void> {
    // The retired service still has a Cloudflare Queue consumer attached.
    // Acknowledge stale events without executing any former fulfillment path.
    for (const message of batch.messages) {
      message.ack();
    }
  },
};
