import { afterEach, describe, expect, it, vi } from 'vitest';
import worker, { type Env } from '../src/index';
import { hmacSha256Hex } from '../src/http';

class MemKV {
  private m = new Map<string, string>();

  async get(k: string, t?: 'json') {
    const v = this.m.get(k);
    if (!v) return null;
    return t === 'json' ? JSON.parse(v) : v;
  }

  async put(k: string, v: string) {
    this.m.set(k, v);
  }

  async delete(k: string) {
    this.m.delete(k);
  }
}

class MemQueue {
  messages: Array<{ body: unknown; options?: QueueSendOptions }> = [];

  async send(body: unknown, options?: QueueSendOptions) {
    this.messages.push({ body, options });
  }
}

class MemR2 {
  private m = new Map<string, Uint8Array>();

  async put(k: string, v: ArrayBuffer | ArrayBufferView) {
    const bytes = v instanceof ArrayBuffer ? new Uint8Array(v) : new Uint8Array(v.buffer);
    this.m.set(k, bytes);
  }

  async get(k: string) {
    const bytes = this.m.get(k);
    if (!bytes) return null;
    return { body: bytes } as unknown as R2ObjectBody;
  }

  async list() {
    return { objects: [] };
  }
}

function env(): Env {
  const kv = new MemKV() as unknown as KVNamespace;
  return {
    IDEMPOTENCY: kv,
    RATE_LIMITS: kv,
    DAILY_CAPS: kv,
    AI: { run: async () => ({ response: 'https://eolkits.com' }) },
    STRIPE_KEY: 'sk_test_dummy',
    STRIPE_WEBHOOK_SECRET: 'whsec_test',
    GITHUB_APP_ID: '123',
    GITHUB_APP_PRIVATE_KEY: 'private',
    ENVIRONMENT: 'test',
  };
}

const ctx = {
  waitUntil() {},
  passThroughOnException() {},
} as unknown as ExecutionContext;

afterEach(() => {
  vi.restoreAllMocks();
});

async function stripeSignature(payload: string, secret: string): Promise<string> {
  const timestamp = Math.floor(Date.now() / 1000);
  const signature = await hmacSha256Hex(secret, `${timestamp}.${payload}`);
  return `t=${timestamp},v1=${signature}`;
}

describe('worker routes', () => {
  it('posts static audit checkout form to Stripe redirect', async () => {
    const request = new Request('https://worker.test/api/audit/checkout', {
      method: 'POST',
      headers: {
        Accept: 'text/html',
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: 'email=buyer%40example.com',
    });

    const response = await worker.fetch(request, env(), ctx);

    expect(response.status).toBe(303);
    expect(response.headers.get('Location')).toContain(
      'https://checkout.stripe.com/test?price=299&email=buyer%40example.com'
    );
  });

  it('queues audit checkout jobs with runner-compatible field names', async () => {
    const testEnv = env();
    const queue = new MemQueue();
    testEnv.JOBS = queue as unknown as Queue;
    const payload = JSON.stringify({
      id: 'evt_audit_completed',
      type: 'checkout.session.completed',
      data: {
        object: {
          id: 'cs_audit',
          customer_email: 'buyer@example.com',
          metadata: {
            sku: 'audit',
            upload_url: 'https://worker.test/upload/up_123',
            deadline: '2026-06-30',
          },
        },
      },
    });

    const response = await worker.fetch(
      new Request('https://worker.test/webhook/stripe', {
        method: 'POST',
        headers: {
          'stripe-signature': await stripeSignature(payload, testEnv.STRIPE_WEBHOOK_SECRET),
        },
        body: payload,
      }),
      testEnv,
      ctx
    );

    expect(response.status).toBe(200);
    expect(queue.messages[0].body).toMatchObject({
      type: 'audit_pdf',
      sessionId: 'cs_audit',
      email: 'buyer@example.com',
      upload_url: 'https://worker.test/upload/up_123',
      deadline: '2026-06-30',
    });
    expect((queue.messages[0].body as Record<string, unknown>).uploadUrl).toBeUndefined();
  });

  it('queues drift watch jobs with runner-compatible field names', async () => {
    const testEnv = env();
    const queue = new MemQueue();
    testEnv.JOBS = queue as unknown as Queue;
    const payload = JSON.stringify({
      id: 'evt_drift_completed',
      type: 'checkout.session.completed',
      data: {
        object: {
          id: 'cs_drift',
          customer_email: 'ops@example.com',
          metadata: {
            sku: 'drift_watch',
            repo: 'owner/repo',
            iam_role: 'arn:aws:iam::123456789012:role/eolkits-readonly',
          },
        },
      },
    });

    const response = await worker.fetch(
      new Request('https://worker.test/webhook/stripe', {
        method: 'POST',
        headers: {
          'stripe-signature': await stripeSignature(payload, testEnv.STRIPE_WEBHOOK_SECRET),
        },
        body: payload,
      }),
      testEnv,
      ctx
    );

    expect(response.status).toBe(200);
    expect(queue.messages[0].body).toMatchObject({
      type: 'drift_watch_setup',
      sessionId: 'cs_drift',
      email: 'ops@example.com',
      repo: 'owner/repo',
      iam_role: 'arn:aws:iam::123456789012:role/eolkits-readonly',
    });
    expect((queue.messages[0].body as Record<string, unknown>).iamRole).toBeUndefined();
  });

  it('queues partner audits using the same audit_pdf runner contract', async () => {
    const testEnv = env();
    const queue = new MemQueue();
    testEnv.JOBS = queue as unknown as Queue;
    await testEnv.IDEMPOTENCY.put(
      'partner:acme',
      JSON.stringify({
        slug: 'acme',
        email: 'partner@example.com',
        display_name: 'Acme',
        domain: 'example.com',
        domain_verified: true,
        stripe_account_id: 'acct_123',
        logo_url: null,
        created_at: new Date().toISOString(),
      })
    );

    const response = await worker.fetch(
      new Request('https://worker.test/partners/acme/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          buyer_email: 'buyer@example.com',
          upload_url: 'https://worker.test/upload/up_partner',
          stripe_session_id: 'cs_partner',
        }),
      }),
      testEnv,
      ctx
    );

    expect(response.status).toBe(200);
    expect(queue.messages[0].body).toMatchObject({
      type: 'audit_pdf',
      email: 'buyer@example.com',
      buyer_email: 'buyer@example.com',
      upload_url: 'https://worker.test/upload/up_partner',
      stripe_session_id: 'cs_partner',
    });
  });

  it('dispatches paid queue jobs to a configured runner endpoint', async () => {
    const testEnv = env();
    testEnv.RUNNER_URL = 'https://runner.test/job';
    testEnv.RUNNER_TOKEN = 'secret';
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response(JSON.stringify({ success: true }), { status: 200 }));

    await worker.queue(
      {
        messages: [
          {
            body: { type: 'audit_pdf', email: 'buyer@example.com', upload_url: 'https://worker.test/upload/u' },
            attempts: 1,
            ack: vi.fn(),
            retry: vi.fn(),
          },
        ],
      } as unknown as MessageBatch<any>,
      testEnv,
      ctx
    );

    expect(fetchMock).toHaveBeenCalledWith(
      'https://runner.test/job',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: 'Bearer secret',
          'Content-Type': 'application/json',
        }),
      })
    );
  });

  it('fulfills runner audit results with verification metadata and report download', async () => {
    const testEnv = env();
    testEnv.RUNNER_URL = 'https://runner.test/job';
    testEnv.RESEND_API_KEY = 're_test';
    testEnv.UPLOADS = new MemR2() as unknown as R2Bucket;
    const sha = 'a'.repeat(64);
    const pdfBytes = new TextEncoder().encode('%PDF-test');
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: true,
            result: {
              email: 'buyer@example.com',
              pdf_base64: btoa(String.fromCharCode(...pdfBytes)),
              input_hash: sha,
              generated_at: '2026-06-05T00:00:00Z',
              rule_pack_version: '2026.06.05',
            },
          }),
          { status: 200 }
        )
      )
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: 'email_123' }), { status: 200 }));

    await worker.queue(
      {
        messages: [
          {
            body: { type: 'audit_pdf', email: 'buyer@example.com', upload_url: 'https://worker.test/upload/u' },
            attempts: 1,
            ack: vi.fn(),
            retry: vi.fn(),
          },
        ],
      } as unknown as MessageBatch<any>,
      testEnv,
      ctx
    );

    const verification = await testEnv.IDEMPOTENCY.get(`verify:${sha}`, 'json') as {
      generatedAt: string;
      rulePackVersion: string;
    };
    expect(verification).toEqual({
      generatedAt: '2026-06-05T00:00:00Z',
      rulePackVersion: '2026.06.05',
    });

    const report = await worker.fetch(
      new Request(`https://worker.test/upload/report/${sha}`),
      testEnv,
      ctx
    );
    expect(report.status).toBe(200);
    expect(report.headers.get('Content-Type')).toBe('application/pdf');
    expect(await report.text()).toBe('%PDF-test');
  });
});
