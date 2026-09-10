import { describe, expect, it } from 'vitest';
import worker from '../src/index';

describe('retired worker tombstone', () => {
  it('reports unhealthy retirement status without exposing old capabilities', async () => {
    const response = await worker.fetch(new Request('https://worker.test/health'));

    expect(response.status).toBe(200);
    expect(response.headers.get('Cache-Control')).toBe('no-store');
    expect(await response.json()).toEqual({
      ok: false,
      retired: true,
      replacement: 'https://eolkits.com/api/capabilities',
    });
  });

  it.each([
    ['/api/audit/checkout', 'POST'],
    ['/api/pack/checkout', 'POST'],
    ['/api/drift/checkout', 'POST'],
    ['/webhook/stripe', 'POST'],
    ['/webhook/github', 'POST'],
    ['/upload/presign', 'POST'],
    ['/api/license/verify', 'GET'],
    ['/partners/signup', 'POST'],
  ])('returns 410 for retired route %s', async (path, method) => {
    const response = await worker.fetch(
      new Request(`https://worker.test${path}`, { method })
    );

    expect(response.status).toBe(410);
    expect(await response.json()).toMatchObject({
      error: 'This legacy commerce service is retired.',
    });
  });

  it('acknowledges legacy queue events without running fulfillment', async () => {
    const acknowledged: string[] = [];
    const batch = {
      messages: [
        { ack: () => acknowledged.push('first') },
        { ack: () => acknowledged.push('second') },
      ],
    } as unknown as Parameters<typeof worker.queue>[0];

    await worker.queue(batch);

    expect(acknowledged).toEqual(['first', 'second']);
  });
});
