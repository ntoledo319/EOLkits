import { afterEach, describe, expect, it, vi } from 'vitest';
import worker, { type Env } from '../src/stripe_retirement';

interface Target {
  amount: number;
  interval: 'month' | 'year' | null;
  product: string;
  type: 'one_time' | 'recurring';
}

interface MockOptions {
  checkoutSessions?: Array<Record<string, unknown>>;
  completedCheckoutSessions?: Array<Record<string, unknown>>;
  corruptPrice?: { id: string; patch: Record<string, unknown> };
  failPricePost?: string;
  links?: Array<{
    active: boolean;
    id: string;
    price: Record<string, unknown>;
    url: string;
  }>;
  schedules?: Array<Record<string, unknown>>;
  subscriptions?: Record<string, Array<Record<string, unknown>>>;
  unexpectedPrices?: Array<Record<string, unknown>>;
}

const TARGETS: Record<string, Target> = {
  price_1TRoEZDL3cQl851o9DFh1DIz: {
    amount: 59_900,
    interval: null,
    product: 'prod_UQfZgo3c4gEjGT',
    type: 'one_time',
  },
  price_1TRoGiDL3cQl851ouqnljzMx: {
    amount: 39_900,
    interval: null,
    product: 'prod_UQfZgo3c4gEjGT',
    type: 'one_time',
  },
  price_1TRoGjDL3cQl851oiIWR5JIa: {
    amount: 29_900,
    interval: null,
    product: 'prod_UQfZgo3c4gEjGT',
    type: 'one_time',
  },
  price_1TRoGkDL3cQl851oMA2B4JgA: {
    amount: 149_900,
    interval: null,
    product: 'prod_UQfbuGhdZM8Qt0',
    type: 'one_time',
  },
  price_1TRoGlDL3cQl851oruV2iGTl: {
    amount: 1_499_900,
    interval: 'year',
    product: 'prod_UQfbikYoNBAPIJ',
    type: 'recurring',
  },
  price_1TRoGmDL3cQl851ofGZyxs6q: {
    amount: 1_900,
    interval: 'month',
    product: 'prod_UQfcRdVw0BeJCK',
    type: 'recurring',
  },
};

const TOKEN = `${Math.floor(Date.now() / 1000) + 600}.${'a'.repeat(64)}`;
const ENV: Env = { RETIRE_TOKEN: TOKEN, STRIPE_KEY: 'sk_live_test_retirement_key' };
const CONFIRMATION = 'deactivate_exact_eolkits_prices_2026_08_22';

function list<T>(data: T[], hasMore = false): Response {
  return response({ data, has_more: hasMore, object: 'list' });
}

function response(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function priceObject(
  id: string,
  active: boolean,
  patch: Record<string, unknown> = {}
): Record<string, unknown> {
  const target = TARGETS[id];
  return {
    active,
    currency: 'usd',
    id,
    livemode: true,
    object: 'price',
    product: target.product,
    recurring:
      target.interval === null ? null : { interval: target.interval, interval_count: 1 },
    type: target.type,
    unit_amount: target.amount,
    ...patch,
  };
}

function lineItems(price: Record<string, unknown>): Record<string, unknown> {
  return { data: [{ id: 'li_safe', price }], has_more: false, object: 'list' };
}

function paymentLink(
  link: { active: boolean; id: string; price: Record<string, unknown>; url: string }
): Record<string, unknown> {
  return {
    active: link.active,
    id: link.id,
    line_items: lineItems(link.price),
    livemode: true,
    object: 'payment_link',
    url: link.url,
  };
}

function adminRequest(body: Record<string, unknown>, token = TOKEN): Request {
  return new Request('https://worker.test/internal/retire-exact-eolkits-prices', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
}

function requestDetails(input: string | URL | Request): { path: string; url: URL } {
  const url = new URL(typeof input === 'string' ? input : input instanceof URL ? input : input.url);
  return { path: url.pathname.replace('/v1', ''), url };
}

function stripeMock(options: MockOptions = {}) {
  const activePrices = new Map(Object.keys(TARGETS).map((id) => [id, true]));
  const links = (options.links ?? []).map((link) => ({ ...link }));
  const fetchMock = vi.fn(
    async (input: string | URL | Request, init?: RequestInit): Promise<Response> => {
      const { path, url } = requestDetails(input);
      const method = init?.method ?? 'GET';

      if (path.startsWith('/prices/')) {
        const id = decodeURIComponent(path.slice('/prices/'.length));
        if (!TARGETS[id]) return response({ error: 'unknown test price' }, 404);
        if (method === 'POST') {
          if (id === options.failPricePost) return response({ error: 'forced' }, 500);
          expect(String(init?.body)).toBe('active=false');
          expect(new Headers(init?.headers).get('Idempotency-Key')).toMatch(/^eolkits-retire-/);
          activePrices.set(id, false);
        }
        const patch = options.corruptPrice?.id === id ? options.corruptPrice.patch : {};
        return response(priceObject(id, activePrices.get(id) ?? false, patch));
      }

      if (path === '/prices') {
        const product = url.searchParams.get('product') ?? '';
        const known = Object.keys(TARGETS)
          .filter((id) => TARGETS[id].product === product && activePrices.get(id))
          .map((id) => priceObject(id, true));
        const unexpected = (options.unexpectedPrices ?? []).filter(
          (item) => item.product === product
        );
        return list([...known, ...unexpected]);
      }

      if (path === '/payment_links') {
        return list(links.filter((link) => link.active).map(paymentLink));
      }

      if (path.startsWith('/payment_links/')) {
        const id = decodeURIComponent(path.slice('/payment_links/'.length));
        const link = links.find((candidate) => candidate.id === id);
        if (!link) return response({ error: 'unknown test link' }, 404);
        expect(method).toBe('POST');
        expect(String(init?.body)).toBe('active=false');
        expect(new Headers(init?.headers).get('Idempotency-Key')).toMatch(
          /^eolkits-retire-link-[a-f0-9]{24}$/
        );
        link.active = false;
        return response(paymentLink(link));
      }

      if (path === '/checkout/sessions') {
        return list(
          url.searchParams.get('status') === 'complete'
            ? options.completedCheckoutSessions ?? []
            : options.checkoutSessions ?? []
        );
      }
      if (path === '/subscriptions') {
        const price = url.searchParams.get('price') ?? '';
        return list(options.subscriptions?.[price] ?? []);
      }
      if (path === '/subscription_schedules') return list(options.schedules ?? []);
      return response({ error: `unhandled ${path}` }, 500);
    }
  );
  return { activePrices, fetchMock, links };
}

function expectSanitized(raw: string): void {
  expect(raw).not.toContain('price_');
  expect(raw).not.toContain('prod_');
  expect(raw).not.toContain('plink_');
  expect(raw).not.toContain('sk_live_');
  expect(raw).not.toContain('RETIRE_TOKEN');
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('exact Stripe retirement tool', () => {
  it('keeps public and wrong-method admin routes fail-closed', async () => {
    const publicResponse = await worker.fetch(new Request('https://worker.test/checkout'), ENV);
    const wrongMethod = await worker.fetch(
      new Request('https://worker.test/internal/retire-exact-eolkits-prices'),
      ENV
    );

    expect(publicResponse.status).toBe(410);
    expect(wrongMethod.status).toBe(410);
    expect(await publicResponse.json()).toMatchObject({
      error: 'This legacy commerce service is retired.',
    });
  });

  it.each([
    ['missing', undefined],
    ['short', 'short'],
    ['expired', `${Math.floor(Date.now() / 1000) - 1}.${'b'.repeat(64)}`],
  ])('rejects a %s configured token without calling Stripe', async (_label, configured) => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    const result = await worker.fetch(adminRequest({ mode: 'audit' }), {
      ...ENV,
      RETIRE_TOKEN: configured,
    });

    expect(result.status).toBe(401);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('rejects a wrong bearer token without calling Stripe', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    const wrong = `${Math.floor(Date.now() / 1000) + 600}.${'c'.repeat(64)}`;

    const result = await worker.fetch(adminRequest({ mode: 'audit' }, wrong), ENV);

    expect(result.status).toBe(401);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('rejects an oversized body before calling Stripe', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    const result = await worker.fetch(adminRequest({ mode: 'x'.repeat(600) }), ENV);

    expect(result.status).toBe(413);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('audits exact Prices and all bounded charging surfaces without exposing IDs', async () => {
    const { fetchMock } = stripeMock();
    vi.stubGlobal('fetch', fetchMock);

    const result = await worker.fetch(adminRequest({ mode: 'audit' }), ENV);
    const raw = await result.text();
    const body = JSON.parse(raw) as Record<string, unknown>;

    expect(result.status).toBe(200);
    expect(body).toMatchObject({
      active_payment_links: 0,
      containment_complete: false,
      future_subscription_schedules: 0,
      future_subscriptions: 0,
      mode: 'audit',
      ok: true,
      open_checkout_sessions: 0,
      recent_completed_checkout_sessions: 0,
      unexpected_active_prices: 0,
    });
    expect(body.prices).toHaveLength(6);
    expect(fetchMock).toHaveBeenCalledTimes(16);
    const checkoutStatuses = fetchMock.mock.calls
      .filter((call) => requestDetails(call[0]).path === '/checkout/sessions')
      .map((call) => requestDetails(call[0]).url.searchParams.get('status'));
    expect(checkoutStatuses).toEqual(['open', 'complete']);
    const auditedPaths = fetchMock.mock.calls.map((call) => requestDetails(call[0]).path);
    expect(auditedPaths.indexOf('/subscription_schedules')).toBeLessThan(
      auditedPaths.indexOf('/subscriptions')
    );
    expectSanitized(raw);
  });

  it.each([
    ['object', { object: 'coupon' }],
    ['id', { id: 'price_wrong' }],
    ['product', { product: 'prod_wrong' }],
    ['livemode', { livemode: false }],
    ['amount', { unit_amount: 1 }],
    ['currency', { currency: 'eur' }],
    ['type', { type: 'one_time', recurring: null }],
    ['interval', { recurring: { interval: 'week', interval_count: 1 } }],
  ])('makes zero writes when exact Price %s validation fails', async (_label, patch) => {
    const { fetchMock } = stripeMock({
      corruptPrice: { id: 'price_1TRoGmDL3cQl851ofGZyxs6q', patch },
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await worker.fetch(
      adminRequest({ confirm: CONFIRMATION, mode: 'deactivate' }),
      ENV
    );
    const raw = await result.text();

    expect(result.status).toBe(409);
    expect(fetchMock.mock.calls.every((call) => (call[1]?.method ?? 'GET') === 'GET')).toBe(true);
    expectSanitized(raw);
  });

  it('closes exact Prices but flags an unexpected active Price for review', async () => {
    const { fetchMock } = stripeMock({
      unexpectedPrices: [
        {
          active: true,
          currency: 'usd',
          id: 'price_unexpected',
          livemode: true,
          object: 'price',
          product: 'prod_UQfZgo3c4gEjGT',
          recurring: null,
          type: 'one_time',
          unit_amount: 12_300,
        },
      ],
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await worker.fetch(
      adminRequest({ confirm: CONFIRMATION, mode: 'deactivate' }),
      ENV
    );
    const raw = await result.text();

    expect(result.status).toBe(200);
    expect(fetchMock.mock.calls.filter((call) => call[1]?.method === 'POST')).toHaveLength(6);
    expect(raw).toContain('"unexpected_active_prices":1');
    expect(raw).toContain('"containment_complete":false');
    expectSanitized(raw);
  });

  it('closes exact Prices but never cancels future recurring billing', async () => {
    const recurringPrice = 'price_1TRoGmDL3cQl851ofGZyxs6q';
    const { fetchMock } = stripeMock({
      subscriptions: {
        [recurringPrice]: [
          { id: 'sub_private', livemode: true, object: 'subscription', status: 'active' },
        ],
      },
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await worker.fetch(
      adminRequest({ confirm: CONFIRMATION, mode: 'deactivate' }),
      ENV
    );
    const raw = await result.text();

    expect(result.status).toBe(200);
    expect(fetchMock.mock.calls.filter((call) => call[1]?.method === 'POST')).toHaveLength(6);
    expect(raw).toContain('"future_subscriptions":1');
    expect(raw).toContain('"containment_complete":false');
    expectSanitized(raw);
  });

  it('flags future schedule invoice items without changing the schedule', async () => {
    const { fetchMock } = stripeMock({
      schedules: [
        {
          id: 'sub_sched_private',
          livemode: true,
          object: 'subscription_schedule',
          phases: [
            {
              add_invoice_items: [
                { price: 'price_1TRoGkDL3cQl851oMA2B4JgA' },
              ],
              items: [],
            },
          ],
          status: 'not_started',
        },
      ],
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await worker.fetch(
      adminRequest({ confirm: CONFIRMATION, mode: 'deactivate' }),
      ENV
    );
    const raw = await result.text();

    expect(result.status).toBe(200);
    expect(fetchMock.mock.calls.filter((call) => call[1]?.method === 'POST')).toHaveLength(6);
    expect(raw).toContain('"future_subscription_schedules":1');
    expect(raw).toContain('"preflight_future_subscription_schedules":1');
    expect(raw).toContain('"containment_complete":false');
    expectSanitized(raw);
  });

  it('carries a preflight schedule through execution with delayed subscription visibility', async () => {
    const base = stripeMock();
    let scheduleReads = 0;
    const schedule = {
      id: 'sub_sched_transition_private',
      livemode: true,
      object: 'subscription_schedule',
      phases: [{ items: [{ price: 'price_1TRoGmDL3cQl851ofGZyxs6q' }] }],
      status: 'active',
    };
    const transitionFetch = vi.fn(
      async (input: string | URL | Request, init?: RequestInit): Promise<Response> => {
        if (requestDetails(input).path === '/subscription_schedules') {
          scheduleReads += 1;
          return list(scheduleReads === 1 ? [schedule] : []);
        }
        return base.fetchMock(input, init);
      }
    );
    vi.stubGlobal('fetch', transitionFetch);

    const result = await worker.fetch(
      adminRequest({ confirm: CONFIRMATION, mode: 'deactivate' }),
      ENV
    );
    const raw = await result.text();

    expect(result.status).toBe(200);
    expect(raw).toContain('"future_subscription_schedules":0');
    expect(raw).toContain('"preflight_future_subscription_schedules":1');
    expect(raw).toContain('"containment_complete":false');
    expectSanitized(raw);
  });

  it('deactivates only a matching Payment Link and all exact Prices, then verifies', async () => {
    const targetPrice = priceObject('price_1TRoGjDL3cQl851oiIWR5JIa', true);
    const unrelatedPrice = {
      id: 'price_unrelated',
      product: 'prod_unrelated',
    };
    const { activePrices, fetchMock, links } = stripeMock({
      links: [
        {
          active: true,
          id: 'plink_target',
          price: targetPrice,
          url: 'https://buy.stripe.com/3cIeVd4nYfRK4td4AQ87K02',
        },
        {
          active: true,
          id: 'plink_unrelated',
          price: unrelatedPrice,
          url: 'https://buy.stripe.com/unrelated',
        },
      ],
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await worker.fetch(
      adminRequest({ confirm: CONFIRMATION, mode: 'deactivate' }),
      ENV
    );
    const raw = await result.text();
    const body = JSON.parse(raw) as Record<string, unknown>;

    expect(result.status).toBe(200);
    expect(body).toMatchObject({
      active_payment_links: 0,
      changed_payment_links: 1,
      containment_complete: true,
      open_checkout_sessions: 0,
    });
    expect(body.changed_prices).toHaveLength(6);
    expect([...activePrices.values()].every((active) => !active)).toBe(true);
    expect(links.find((link) => link.id === 'plink_target')?.active).toBe(false);
    expect(links.find((link) => link.id === 'plink_unrelated')?.active).toBe(true);
    const posts = fetchMock.mock.calls.filter((call) => call[1]?.method === 'POST');
    expect(posts).toHaveLength(7);
    expect(requestDetails(posts[0][0]).path).toBe('/prices/price_1TRoGjDL3cQl851oiIWR5JIa');
    expectSanitized(raw);
  });

  it('fails before every mutation when an unknown Payment Link uses a target Product', async () => {
    const targetPrice = priceObject('price_1TRoGjDL3cQl851oiIWR5JIa', true);
    const { activePrices, fetchMock, links } = stripeMock({
      links: [
        {
          active: true,
          id: 'plink_unknown_target',
          price: targetPrice,
          url: 'https://buy.stripe.com/not-on-the-six-url-allowlist',
        },
      ],
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await worker.fetch(
      adminRequest({ confirm: CONFIRMATION, mode: 'deactivate' }),
      ENV
    );
    const raw = await result.text();

    expect(result.status).toBe(409);
    expect(fetchMock.mock.calls.filter((call) => call[1]?.method === 'POST')).toHaveLength(0);
    expect([...activePrices.values()].every((active) => active)).toBe(true);
    expect(links[0].active).toBe(true);
    expect(raw).toContain('"mutation_blocked":true');
    expect(raw).toContain('"changed_payment_links":0');
    expect(raw).toContain('"changed_prices":[]');
    expect(raw).toContain('"unexpected_active_payment_links":1');
    expect(raw).toContain('"containment_complete":false');
    expectSanitized(raw);
  });

  it('reports the exact open-Session hold while still closing reversible surfaces', async () => {
    const expiresAt = Math.floor(Date.now() / 1000) + 3_600;
    const targetPrice = priceObject('price_1TRoGjDL3cQl851oiIWR5JIa', true);
    const { fetchMock } = stripeMock({
      checkoutSessions: [
        {
          expires_at: expiresAt,
          id: 'cs_private',
          line_items: lineItems(targetPrice),
          livemode: true,
          metadata: {},
          object: 'checkout.session',
          payment_status: 'unpaid',
          status: 'open',
          success_url: null,
          cancel_url: null,
        },
      ],
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await worker.fetch(
      adminRequest({ confirm: CONFIRMATION, mode: 'deactivate' }),
      ENV
    );
    const raw = await result.text();
    const body = JSON.parse(raw) as Record<string, unknown>;

    expect(result.status).toBe(200);
    expect(body).toMatchObject({
      containment_complete: false,
      open_checkout_hold_until: expiresAt,
      open_checkout_sessions: 1,
      preflight_open_checkout_hold_until: expiresAt,
      preflight_open_checkout_sessions: 1,
    });
    expectSanitized(raw);
  });

  it('flags a recent completed live Session and refuses a containment claim', async () => {
    const targetPrice = priceObject('price_1TRoGjDL3cQl851oiIWR5JIa', true);
    const { fetchMock } = stripeMock({
      completedCheckoutSessions: [
        {
          cancel_url: null,
          expires_at: Math.floor(Date.now() / 1000),
          id: 'cs_completed_private',
          line_items: lineItems(targetPrice),
          livemode: true,
          metadata: {},
          object: 'checkout.session',
          payment_status: 'paid',
          status: 'complete',
          success_url: null,
        },
      ],
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await worker.fetch(
      adminRequest({ confirm: CONFIRMATION, mode: 'deactivate' }),
      ENV
    );
    const raw = await result.text();

    expect(result.status).toBe(200);
    expect(raw).toContain('"recent_completed_checkout_sessions":1');
    expect(raw).toContain('"preflight_recent_completed_checkout_sessions":1');
    expect(raw).toContain('"containment_complete":false');
    expectSanitized(raw);
  });

  it('cannot miss an open-to-complete transition through response reordering', async () => {
    const base = stripeMock();
    const targetPrice = priceObject('price_1TRoGjDL3cQl851oiIWR5JIa', true);
    let sessionState: 'complete' | 'open' = 'open';
    const common = {
      cancel_url: null,
      expires_at: Math.floor(Date.now() / 1000) + 3_600,
      id: 'cs_transition_private',
      line_items: lineItems(targetPrice),
      livemode: true,
      metadata: {},
      object: 'checkout.session',
      success_url: null,
    };
    const raceFetch = vi.fn(
      async (input: string | URL | Request, init?: RequestInit): Promise<Response> => {
        const { path, url } = requestDetails(input);
        if (path !== '/checkout/sessions') return base.fetchMock(input, init);
        const status = url.searchParams.get('status');
        if (status === 'open') {
          if (sessionState === 'complete') return list([]);
          // If completed were queried concurrently, it would flip the state
          // during this delay and both endpoint snapshots would return empty.
          await new Promise((resolve) => setTimeout(resolve, 10));
          if (sessionState === 'complete') return list([]);
          sessionState = 'complete';
          return list([{ ...common, payment_status: 'unpaid', status: 'open' }]);
        }
        if (sessionState === 'open') {
          sessionState = 'complete';
          return list([]);
        }
        return list([{ ...common, payment_status: 'paid', status: 'complete' }]);
      }
    );
    vi.stubGlobal('fetch', raceFetch);

    const result = await worker.fetch(
      adminRequest({ confirm: CONFIRMATION, mode: 'deactivate' }),
      ENV
    );
    const raw = await result.text();

    expect(result.status).toBe(200);
    expect(raw).toContain('"preflight_open_checkout_sessions":1');
    expect(raw).toContain('"recent_completed_checkout_sessions":1');
    expect(raw).toContain('"containment_complete":false');
    expectSanitized(raw);
  });

  it('detects a legacy inline-price Session by exact SKU and return URLs', async () => {
    const expiresAt = Math.floor(Date.now() / 1000) + 7_200;
    const { fetchMock } = stripeMock({
      checkoutSessions: [
        {
          cancel_url: 'https://ntoledo319.github.io/Rupture/audit',
          expires_at: expiresAt,
          id: 'cs_legacy_inline_private',
          line_items: lineItems({ id: 'price_inline', product: 'prod_inline' }),
          livemode: true,
          metadata: { sku: 'audit' },
          object: 'checkout.session',
          payment_status: 'unpaid',
          status: 'open',
          success_url:
            'https://ntoledo319.github.io/Rupture/verify?session_id={CHECKOUT_SESSION_ID}',
        },
      ],
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await worker.fetch(
      adminRequest({ confirm: CONFIRMATION, mode: 'deactivate' }),
      ENV
    );
    const raw = await result.text();

    expect(result.status).toBe(200);
    expect(raw).toContain(`"open_checkout_hold_until":${expiresAt}`);
    expect(raw).toContain('"open_checkout_sessions":1');
    expect(raw).toContain('"containment_complete":false');
    expectSanitized(raw);
  });

  it('is idempotent when the exact Prices are already inactive', async () => {
    const state = stripeMock();
    for (const id of state.activePrices.keys()) state.activePrices.set(id, false);
    vi.stubGlobal('fetch', state.fetchMock);

    const result = await worker.fetch(
      adminRequest({ confirm: CONFIRMATION, mode: 'deactivate' }),
      ENV
    );
    const body = (await result.json()) as Record<string, unknown>;

    expect(result.status).toBe(200);
    expect(body).toMatchObject({
      changed_payment_links: 0,
      containment_complete: true,
    });
    expect(body.changed_prices).toEqual([]);
    expect(state.fetchMock.mock.calls.every((call) => (call[1]?.method ?? 'GET') === 'GET')).toBe(
      true
    );
  });

  it('attempts every Price sequentially and performs a final audit after one POST fails', async () => {
    const failedId = 'price_1TRoGiDL3cQl851ouqnljzMx';
    const { fetchMock } = stripeMock({ failPricePost: failedId });
    vi.stubGlobal('fetch', fetchMock);

    const result = await worker.fetch(
      adminRequest({ confirm: CONFIRMATION, mode: 'deactivate' }),
      ENV
    );
    const raw = await result.text();
    const posts = fetchMock.mock.calls.filter((call) => call[1]?.method === 'POST');
    const individualReads = fetchMock.mock.calls.filter((call) => {
      const { path } = requestDetails(call[0]);
      return path.startsWith('/prices/') && (call[1]?.method ?? 'GET') === 'GET';
    });

    expect(result.status).toBe(409);
    expect(posts).toHaveLength(6);
    expect(individualReads).toHaveLength(12);
    expect(raw).toContain('reversible postcondition');
    expectSanitized(raw);
  });

  it('converts a Stripe timeout into a sanitized fail-closed response', async () => {
    const fetchMock = vi.fn(async (_input: unknown, init?: RequestInit) => {
      expect(init?.signal).toBeInstanceOf(AbortSignal);
      throw new Error('network detail that must not escape');
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await worker.fetch(adminRequest({ mode: 'audit' }), ENV);
    const raw = await result.text();

    expect(result.status).toBe(409);
    expect(raw).toContain('Stripe request failed or timed out');
    expect(raw).not.toContain('network detail');
    expectSanitized(raw);
  });

  it('acknowledges retained Queue messages without fulfillment', async () => {
    const ackOne = vi.fn();
    const ackTwo = vi.fn();
    await worker.queue({ messages: [{ ack: ackOne }, { ack: ackTwo }] } as unknown as MessageBatch<unknown>);

    expect(ackOne).toHaveBeenCalledOnce();
    expect(ackTwo).toHaveBeenCalledOnce();
  });
});
