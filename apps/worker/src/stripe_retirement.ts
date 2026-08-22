/**
 * One-time, authenticated retirement tool for the exact legacy EOLkits Stripe
 * surfaces. It is deployed briefly by a manual workflow and then replaced by
 * the normal HTTP 410 tombstone.
 *
 * Mutations are deliberately narrow and reversible: deactivate exact Prices
 * and active Payment Links whose expanded line items match the allowlist. The
 * tool never creates or expires Checkout Sessions, cancels subscriptions, or
 * changes subscription schedules. Those irreversible cases fail closed for
 * owner review.
 */

export interface Env {
  STRIPE_KEY?: string;
  RETIRE_TOKEN?: string;
}

type PriceKind = 'one_time' | 'recurring';

interface StripePrice {
  active: boolean;
  currency: string;
  id: string;
  livemode: boolean;
  object: 'price';
  product: string;
  recurring: { interval: string; interval_count: number } | null;
  type: PriceKind;
  unit_amount: number | null;
}

interface PriceTarget {
  alias: string;
  id: string;
  interval: 'month' | 'year' | null;
  product: string;
  type: PriceKind;
  unitAmount: number;
}

interface StripeList<T> {
  data: T[];
  has_more: boolean;
  object: 'list';
}

interface StripeLineItem {
  id?: string;
  price?: StripePriceReference | string | null;
}

interface StripePriceReference {
  id?: string;
  product?: { id?: string } | string | null;
}

interface StripePaymentLink {
  active: boolean;
  id: string;
  line_items?: StripeList<StripeLineItem>;
  livemode: boolean;
  object: 'payment_link';
  url: string;
}

interface StripeCheckoutSession {
  cancel_url: string | null;
  expires_at: number;
  id: string;
  line_items?: StripeList<StripeLineItem>;
  livemode: boolean;
  metadata: Record<string, string>;
  object: 'checkout.session';
  payment_status: string;
  status: string | null;
  success_url: string | null;
}

interface StripeSubscription {
  id: string;
  livemode: boolean;
  object: 'subscription';
  status: string;
}

interface StripeScheduleItem {
  plan?: StripePriceReference | string | null;
  price?: StripePriceReference | string | null;
}

interface StripeSchedulePhase {
  add_invoice_items?: StripeScheduleItem[];
  items?: StripeScheduleItem[];
}

interface StripeSubscriptionSchedule {
  id: string;
  livemode: boolean;
  object: 'subscription_schedule';
  phases?: StripeSchedulePhase[];
  status: string;
}

interface AuditState {
  activePaymentLinks: StripePaymentLink[];
  futureSchedules: number;
  futureSubscriptions: number;
  openCheckoutHoldUntil: number | null;
  openCheckoutSessions: number;
  prices: StripePrice[];
  recentCompletedCheckoutSessions: number;
  unexpectedActivePaymentLinks: number;
  unexpectedActivePrices: number;
}

interface PaymentLinkAudit {
  known: StripePaymentLink[];
  unexpected: number;
}

const PRICE_TARGETS: readonly PriceTarget[] = [
  {
    alias: 'audit-surge-599',
    id: 'price_1TRoEZDL3cQl851o9DFh1DIz',
    interval: null,
    product: 'prod_UQfZgo3c4gEjGT',
    type: 'one_time',
    unitAmount: 59_900,
  },
  {
    alias: 'audit-surge-399',
    id: 'price_1TRoGiDL3cQl851ouqnljzMx',
    interval: null,
    product: 'prod_UQfZgo3c4gEjGT',
    type: 'one_time',
    unitAmount: 39_900,
  },
  {
    alias: 'audit-standard-299',
    id: 'price_1TRoGjDL3cQl851oiIWR5JIa',
    interval: null,
    product: 'prod_UQfZgo3c4gEjGT',
    type: 'one_time',
    unitAmount: 29_900,
  },
  {
    alias: 'migration-pack-1499',
    id: 'price_1TRoGkDL3cQl851oMA2B4JgA',
    interval: null,
    product: 'prod_UQfbuGhdZM8Qt0',
    type: 'one_time',
    unitAmount: 149_900,
  },
  {
    alias: 'organization-14999',
    id: 'price_1TRoGlDL3cQl851oruV2iGTl',
    interval: 'year',
    product: 'prod_UQfbikYoNBAPIJ',
    type: 'recurring',
    unitAmount: 1_499_900,
  },
  {
    alias: 'drift-watch-19',
    id: 'price_1TRoGmDL3cQl851ofGZyxs6q',
    interval: 'month',
    product: 'prod_UQfcRdVw0BeJCK',
    type: 'recurring',
    unitAmount: 1_900,
  },
] as const;

const ADMIN_PATH = '/internal/retire-exact-eolkits-prices';
const CONFIRMATION = 'deactivate_exact_eolkits_prices_2026_08_22';
const REPLACEMENT = 'https://eolkits.com/api/capabilities';
const STRIPE_API = 'https://api.stripe.com/v1';
const MAX_LIST_PAGES = 1;
const MAX_PAYMENT_LINK_MUTATIONS = 6;
const REQUEST_TIMEOUT_MS = 12_000;
const MAX_TOKEN_LIFETIME_SECONDS = 20 * 60;
const COMPLETED_SESSION_WINDOW_SECONDS = 30 * 24 * 60 * 60;
const TERMINAL_SUBSCRIPTION_STATUSES = new Set(['canceled', 'incomplete_expired']);
const FUTURE_SCHEDULE_STATUSES = new Set(['active', 'not_started']);
const TARGET_PRICE_IDS = new Set(PRICE_TARGETS.map((target) => target.id));
const TARGET_PRODUCT_IDS = new Set(PRICE_TARGETS.map((target) => target.product));
const TARGET_PRODUCTS = [...TARGET_PRODUCT_IDS].sort();
const PRICE_MUTATION_ORDER = [2, 0, 1, 3, 4, 5] as const;
const KNOWN_PAYMENT_LINK_URLS = new Set([
  'https://buy.stripe.com/dRmbJ14nYgVO7Fp4AQ87K00',
  'https://buy.stripe.com/dRmbJ107I8pi6Bld7m87K01',
  'https://buy.stripe.com/3cIeVd4nYfRK4td4AQ87K02',
  'https://buy.stripe.com/cNi5kD07IbBu7Fp5EU87K03',
  'https://buy.stripe.com/bJe7sL5s2eNG2l52sI87K04',
  'https://buy.stripe.com/5kQeVd2fQ7le3p94AQ87K05',
]);
const LEGACY_INLINE_SESSION_ROUTES: Record<
  string,
  ReadonlyArray<{ cancel: string; success: string }>
> = {
  audit: [
    {
      cancel: 'https://ntoledo319.github.io/Rupture/audit',
      success:
        'https://ntoledo319.github.io/Rupture/verify?session_id={CHECKOUT_SESSION_ID}',
    },
    {
      cancel: 'https://ntoledo319.github.io/EOLkits/audit',
      success:
        'https://ntoledo319.github.io/EOLkits/verify?session_id={CHECKOUT_SESSION_ID}',
    },
    {
      cancel: 'https://eolkits.com/audit',
      success: 'https://eolkits.com/verify?session_id={CHECKOUT_SESSION_ID}',
    },
  ],
  migration_pack: [
    {
      cancel: 'https://ntoledo319.github.io/Rupture/pack',
      success:
        'https://ntoledo319.github.io/Rupture/status?session_id={CHECKOUT_SESSION_ID}',
    },
    {
      cancel: 'https://ntoledo319.github.io/EOLkits/pack',
      success:
        'https://ntoledo319.github.io/EOLkits/status?session_id={CHECKOUT_SESSION_ID}',
    },
    {
      cancel: 'https://eolkits.com/pack',
      success: 'https://eolkits.com/status?session_id={CHECKOUT_SESSION_ID}',
    },
  ],
};
const JSON_HEADERS = {
  'Cache-Control': 'no-store',
  'Content-Type': 'application/json; charset=utf-8',
  'X-Content-Type-Options': 'nosniff',
};

function json(body: Record<string, unknown>, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: JSON_HEADERS });
}

async function hashesMatch(left: string, right: string): Promise<boolean> {
  const encoder = new TextEncoder();
  const [leftHash, rightHash] = await Promise.all([
    crypto.subtle.digest('SHA-256', encoder.encode(left)),
    crypto.subtle.digest('SHA-256', encoder.encode(right)),
  ]);
  const leftBytes = new Uint8Array(leftHash);
  const rightBytes = new Uint8Array(rightHash);
  let difference = 0;
  for (let index = 0; index < leftBytes.length; index += 1) {
    difference |= leftBytes[index] ^ rightBytes[index];
  }
  return difference === 0;
}

function tokenIsCurrent(token: string): boolean {
  const separator = token.indexOf('.');
  if (separator < 1 || separator !== token.lastIndexOf('.')) return false;
  const expiresRaw = token.slice(0, separator);
  const nonce = token.slice(separator + 1);
  if (!/^\d{10}$/.test(expiresRaw) || !/^[a-f0-9]{64}$/.test(nonce)) return false;
  const expiresAt = Number(expiresRaw);
  const now = Math.floor(Date.now() / 1000);
  return expiresAt >= now && expiresAt - now <= MAX_TOKEN_LIFETIME_SECONDS;
}

async function authorized(request: Request, env: Env): Promise<boolean> {
  if (!env.RETIRE_TOKEN || !tokenIsCurrent(env.RETIRE_TOKEN)) return false;
  const header = request.headers.get('Authorization') ?? '';
  if (!header.startsWith('Bearer ')) return false;
  return hashesMatch(header.slice('Bearer '.length), env.RETIRE_TOKEN);
}

function requireLiveStripeKey(env: Env): string {
  if (!env.STRIPE_KEY || !/^(sk|rk)_live_/.test(env.STRIPE_KEY)) {
    throw new Error('The preserved Stripe credential is unavailable or not live-mode');
  }
  return env.STRIPE_KEY;
}

async function stripeApi(env: Env, path: string, init: RequestInit = {}): Promise<unknown> {
  const key = requireLiveStripeKey(env);
  let response: Response;
  try {
    response = await fetch(`${STRIPE_API}${path}`, {
      ...init,
      headers: {
        Authorization: `Bearer ${key}`,
        ...init.headers,
      },
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
  } catch {
    throw new Error('Stripe request failed or timed out');
  }
  if (!response.ok) {
    throw new Error(`Stripe returned HTTP ${response.status}`);
  }
  try {
    return await response.json();
  } catch {
    throw new Error('Stripe returned invalid JSON');
  }
}

function validateList<T>(value: unknown, label: string): StripeList<T> {
  if (!value || typeof value !== 'object') throw new Error(`Invalid ${label} list`);
  const candidate = value as Partial<StripeList<T>>;
  if (
    candidate.object !== 'list' ||
    !Array.isArray(candidate.data) ||
    typeof candidate.has_more !== 'boolean'
  ) {
    throw new Error(`Invalid ${label} list`);
  }
  return candidate as StripeList<T>;
}

async function listStripe<T>(
  env: Env,
  path: string,
  parameters: Record<string, string>,
  label: string
): Promise<T[]> {
  const values: T[] = [];
  let startingAfter: string | undefined;
  for (let page = 0; page < MAX_LIST_PAGES; page += 1) {
    const query = new URLSearchParams({ ...parameters, limit: '100' });
    if (startingAfter) query.set('starting_after', startingAfter);
    const current = validateList<T>(await stripeApi(env, `${path}?${query}`), label);
    values.push(...current.data);
    if (!current.has_more) return values;
    const last = current.data.at(-1) as { id?: unknown } | undefined;
    if (!last || typeof last.id !== 'string' || !last.id) {
      throw new Error(`Invalid ${label} pagination cursor`);
    }
    startingAfter = last.id;
  }
  throw new Error(`${label} exceeds the bounded audit window`);
}

function validatePrice(value: unknown, target: PriceTarget): StripePrice {
  if (!value || typeof value !== 'object') {
    throw new Error(`Invalid Stripe response for ${target.alias}`);
  }
  const candidate = value as Partial<StripePrice>;
  if (
    candidate.object !== 'price' ||
    candidate.id !== target.id ||
    candidate.product !== target.product ||
    candidate.currency !== 'usd' ||
    candidate.unit_amount !== target.unitAmount ||
    candidate.type !== target.type ||
    candidate.livemode !== true ||
    typeof candidate.active !== 'boolean'
  ) {
    throw new Error(`Target validation failed for ${target.alias}`);
  }
  if (
    (target.interval === null && candidate.recurring !== null) ||
    (target.interval !== null &&
      (candidate.recurring?.interval !== target.interval ||
        candidate.recurring.interval_count !== 1))
  ) {
    throw new Error(`Recurring terms validation failed for ${target.alias}`);
  }
  return candidate as StripePrice;
}

function validateListedPrice(value: unknown, product: string): StripePrice {
  if (!value || typeof value !== 'object') throw new Error('Invalid product Price response');
  const candidate = value as Partial<StripePrice>;
  if (
    candidate.object !== 'price' ||
    typeof candidate.id !== 'string' ||
    !candidate.id ||
    candidate.product !== product ||
    candidate.active !== true ||
    candidate.livemode !== true ||
    candidate.currency !== 'usd' ||
    typeof candidate.unit_amount !== 'number' ||
    (candidate.type !== 'one_time' && candidate.type !== 'recurring')
  ) {
    throw new Error('Product Price validation failed');
  }
  return candidate as StripePrice;
}

async function readPrice(env: Env, target: PriceTarget): Promise<StripePrice> {
  return validatePrice(await stripeApi(env, `/prices/${target.id}`), target);
}

async function deactivatePrice(env: Env, target: PriceTarget): Promise<StripePrice> {
  const value = await stripeApi(env, `/prices/${target.id}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Idempotency-Key': `eolkits-retire-${target.alias}-2026-08-22`,
    },
    body: new URLSearchParams({ active: 'false' }),
  });
  return validatePrice(value, target);
}

function referenceId(value: StripePriceReference | string | null | undefined): string | null {
  if (typeof value === 'string') return value;
  return value && typeof value.id === 'string' ? value.id : null;
}

function referenceProduct(value: StripePriceReference | string | null | undefined): string | null {
  if (!value || typeof value === 'string') return null;
  const product = value.product;
  if (typeof product === 'string') return product;
  return product && typeof product.id === 'string' ? product.id : null;
}

function lineItemsMatchTarget(lineItems: StripeList<StripeLineItem> | undefined): boolean {
  if (!lineItems || lineItems.object !== 'list' || !Array.isArray(lineItems.data)) {
    throw new Error('Expanded line items are missing');
  }
  if (lineItems.has_more) throw new Error('Expanded line items exceed the bounded audit window');
  return lineItems.data.some((item) => {
    const priceId = referenceId(item.price);
    const productId = referenceProduct(item.price);
    return (priceId !== null && TARGET_PRICE_IDS.has(priceId)) ||
      (productId !== null && TARGET_PRODUCT_IDS.has(productId));
  });
}

function validatePaymentLink(value: unknown): StripePaymentLink {
  if (!value || typeof value !== 'object') throw new Error('Invalid Payment Link response');
  const candidate = value as Partial<StripePaymentLink>;
  if (
    candidate.object !== 'payment_link' ||
    typeof candidate.id !== 'string' ||
    !candidate.id ||
    candidate.livemode !== true ||
    typeof candidate.active !== 'boolean' ||
    typeof candidate.url !== 'string' ||
    !candidate.url
  ) {
    throw new Error('Payment Link validation failed');
  }
  return candidate as StripePaymentLink;
}

async function auditPaymentLinks(env: Env): Promise<PaymentLinkAudit> {
  const links = await listStripe<StripePaymentLink>(
    env,
    '/payment_links',
    { active: 'true', 'expand[]': 'data.line_items' },
    'Payment Link'
  );
  const known: StripePaymentLink[] = [];
  let unexpected = 0;
  for (const link of links.map(validatePaymentLink)) {
    const targetLineItem = lineItemsMatchTarget(link.line_items);
    const knownUrl = KNOWN_PAYMENT_LINK_URLS.has(link.url);
    if (targetLineItem && knownUrl) known.push(link);
    else if (targetLineItem || knownUrl) unexpected += 1;
  }
  known.sort((left, right) => left.id.localeCompare(right.id));
  if (known.length > MAX_PAYMENT_LINK_MUTATIONS) {
    return { known: [], unexpected: unexpected + known.length };
  }
  return { known, unexpected };
}

async function idempotencySuffix(value: string): Promise<string> {
  const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return [...new Uint8Array(hash)]
    .slice(0, 12)
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('');
}

async function deactivatePaymentLink(env: Env, link: StripePaymentLink): Promise<void> {
  const suffix = await idempotencySuffix(link.id);
  const value = await stripeApi(env, `/payment_links/${link.id}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Idempotency-Key': `eolkits-retire-link-${suffix}`,
    },
    body: new URLSearchParams({ active: 'false' }),
  });
  const updated = validatePaymentLink(value);
  if (updated.id !== link.id || updated.active) {
    throw new Error('Stripe did not deactivate an exact Payment Link');
  }
}

async function countUnexpectedActivePrices(env: Env): Promise<number> {
  const lists = await Promise.all(
    TARGET_PRODUCTS.map(async (product) => {
      const prices = await listStripe<StripePrice>(
        env,
        '/prices',
        { active: 'true', product },
        'product Price'
      );
      return prices.map((price) => validateListedPrice(price, product));
    })
  );
  return lists.flat().filter((price) => !TARGET_PRICE_IDS.has(price.id)).length;
}

function validateCheckoutSession(value: unknown, expectedStatus: 'complete' | 'open'): StripeCheckoutSession {
  if (!value || typeof value !== 'object') throw new Error('Invalid Checkout Session response');
  const candidate = value as Partial<StripeCheckoutSession>;
  if (
    candidate.object !== 'checkout.session' ||
    typeof candidate.id !== 'string' ||
    !candidate.id ||
    candidate.livemode !== true ||
    candidate.status !== expectedStatus ||
    typeof candidate.payment_status !== 'string' ||
    !candidate.payment_status ||
    !candidate.metadata ||
    typeof candidate.metadata !== 'object' ||
    Array.isArray(candidate.metadata) ||
    typeof candidate.expires_at !== 'number' ||
    !Number.isSafeInteger(candidate.expires_at)
  ) {
    throw new Error('Checkout Session validation failed');
  }
  return candidate as StripeCheckoutSession;
}

function checkoutSessionMatchesTarget(session: StripeCheckoutSession): boolean {
  if (lineItemsMatchTarget(session.line_items)) return true;
  const sku = session.metadata.sku;
  const routes = LEGACY_INLINE_SESSION_ROUTES[sku];
  return Boolean(
    routes?.some(
      (route) => session.success_url === route.success && session.cancel_url === route.cancel
    )
  );
}

async function openTargetCheckoutSessions(
  env: Env
): Promise<{ count: number; holdUntil: number | null }> {
  const sessions = await listStripe<StripeCheckoutSession>(
    env,
    '/checkout/sessions',
    { status: 'open', 'expand[]': 'data.line_items' },
    'Checkout Session'
  );
  const matching = sessions
    .map((session) => validateCheckoutSession(session, 'open'))
    .filter(checkoutSessionMatchesTarget);
  return {
    count: matching.length,
    holdUntil: matching.length ? Math.max(...matching.map((session) => session.expires_at)) : null,
  };
}

async function countRecentCompletedTargetCheckoutSessions(env: Env): Promise<number> {
  const createdAfter = Math.floor(Date.now() / 1000) - COMPLETED_SESSION_WINDOW_SECONDS;
  const sessions = await listStripe<StripeCheckoutSession>(
    env,
    '/checkout/sessions',
    {
      'created[gte]': String(createdAfter),
      'expand[]': 'data.line_items',
      status: 'complete',
    },
    'completed Checkout Session'
  );
  return sessions
    .map((session) => validateCheckoutSession(session, 'complete'))
    .filter(checkoutSessionMatchesTarget).length;
}

function validateSubscription(value: unknown): StripeSubscription {
  if (!value || typeof value !== 'object') throw new Error('Invalid Subscription response');
  const candidate = value as Partial<StripeSubscription>;
  if (
    candidate.object !== 'subscription' ||
    typeof candidate.id !== 'string' ||
    !candidate.id ||
    candidate.livemode !== true ||
    typeof candidate.status !== 'string' ||
    !candidate.status
  ) {
    throw new Error('Subscription validation failed');
  }
  return candidate as StripeSubscription;
}

async function countFutureSubscriptions(env: Env): Promise<number> {
  const recurringTargets = PRICE_TARGETS.filter((target) => target.type === 'recurring');
  const lists = await Promise.all(
    recurringTargets.map((target) =>
      listStripe<StripeSubscription>(
        env,
        '/subscriptions',
        { price: target.id, status: 'all' },
        `Subscription ${target.alias}`
      )
    )
  );
  return lists
    .flat()
    .map(validateSubscription)
    .filter((subscription) => !TERMINAL_SUBSCRIPTION_STATUSES.has(subscription.status)).length;
}

function scheduleMatchesTarget(schedule: StripeSubscriptionSchedule): boolean {
  return (schedule.phases ?? []).some((phase) =>
    [...(phase.items ?? []), ...(phase.add_invoice_items ?? [])].some((item) => {
      const priceId = referenceId(item.price) ?? referenceId(item.plan);
      return priceId !== null && TARGET_PRICE_IDS.has(priceId);
    })
  );
}

function validateSchedule(value: unknown): StripeSubscriptionSchedule {
  if (!value || typeof value !== 'object') throw new Error('Invalid schedule response');
  const candidate = value as Partial<StripeSubscriptionSchedule>;
  if (
    candidate.object !== 'subscription_schedule' ||
    typeof candidate.id !== 'string' ||
    !candidate.id ||
    candidate.livemode !== true ||
    typeof candidate.status !== 'string' ||
    !Array.isArray(candidate.phases)
  ) {
    throw new Error('Subscription schedule validation failed');
  }
  return candidate as StripeSubscriptionSchedule;
}

async function countFutureSchedules(env: Env): Promise<number> {
  const schedules = await listStripe<StripeSubscriptionSchedule>(
    env,
    '/subscription_schedules',
    {},
    'Subscription schedule'
  );
  return schedules
    .map(validateSchedule)
    .filter(
      (schedule) => FUTURE_SCHEDULE_STATUSES.has(schedule.status) && scheduleMatchesTarget(schedule)
    ).length;
}

async function audit(env: Env): Promise<AuditState> {
  // Keep each stage within Cloudflare's six simultaneous outgoing-connection
  // ceiling. Every call is read-only until the complete preflight succeeds.
  const prices = await Promise.all(PRICE_TARGETS.map((target) => readPrice(env, target)));
  const [paymentLinks, unexpectedActivePrices] = await Promise.all([
    auditPaymentLinks(env),
    countUnexpectedActivePrices(env),
  ]);
  // Snapshot open Sessions before completed Sessions. Once the exact Prices
  // are inactive, an in-flight Session must appear in the first snapshot or,
  // if it transitions, the later completed snapshot.
  const checkout = await openTargetCheckoutSessions(env);
  const [recentCompletedCheckoutSessions, futureSubscriptions, futureSchedules] =
    await Promise.all([
      countRecentCompletedTargetCheckoutSessions(env),
      countFutureSubscriptions(env),
      countFutureSchedules(env),
    ]);
  return {
    activePaymentLinks: paymentLinks.known,
    futureSchedules,
    futureSubscriptions,
    openCheckoutHoldUntil: checkout.holdUntil,
    openCheckoutSessions: checkout.count,
    prices,
    recentCompletedCheckoutSessions,
    unexpectedActivePaymentLinks: paymentLinks.unexpected,
    unexpectedActivePrices,
  };
}

function containmentComplete(state: AuditState): boolean {
  return (
    state.prices.every((price) => !price.active) &&
    state.activePaymentLinks.length === 0 &&
    state.unexpectedActivePaymentLinks === 0 &&
    state.unexpectedActivePrices === 0 &&
    state.futureSubscriptions === 0 &&
    state.futureSchedules === 0 &&
    state.openCheckoutSessions === 0 &&
    state.recentCompletedCheckoutSessions === 0
  );
}

function publicState(state: AuditState): Record<string, unknown> {
  return {
    prices: state.prices.map((price, index) => ({
      alias: PRICE_TARGETS[index].alias,
      active: price.active,
      livemode: price.livemode,
      matched: true,
    })),
    active_payment_links: state.activePaymentLinks.length,
    unexpected_active_payment_links: state.unexpectedActivePaymentLinks,
    unexpected_active_prices: state.unexpectedActivePrices,
    future_subscriptions: state.futureSubscriptions,
    future_subscription_schedules: state.futureSchedules,
    open_checkout_sessions: state.openCheckoutSessions,
    open_checkout_hold_until: state.openCheckoutHoldUntil,
    recent_completed_checkout_sessions: state.recentCompletedCheckoutSessions,
    containment_complete: containmentComplete(state),
  };
}

async function handleAdmin(request: Request, env: Env): Promise<Response> {
  const declaredLength = Number(request.headers.get('Content-Length') ?? '0');
  if (Number.isFinite(declaredLength) && declaredLength > 512) {
    return json({ error: 'Request body too large' }, 413);
  }
  const raw = await request.text();
  if (raw.length > 512) return json({ error: 'Request body too large' }, 413);

  let body: { confirm?: unknown; mode?: unknown };
  try {
    body = JSON.parse(raw) as { confirm?: unknown; mode?: unknown };
  } catch {
    return json({ error: 'Invalid JSON' }, 400);
  }

  if (body.mode !== 'audit' && body.mode !== 'deactivate') {
    return json({ error: 'Unsupported mode' }, 400);
  }

  try {
    const before = await audit(env);
    if (body.mode === 'audit') {
      return json({ ok: true, mode: 'audit', ...publicState(before) });
    }
    if (body.confirm !== CONFIRMATION) {
      return json({ error: 'Exact confirmation required' }, 409);
    }
    let changedPaymentLinks = 0;
    const changedPrices: string[] = [];
    const mutationFailures: string[] = [];
    // Close the stale GRACE $299 path first, then every other exact Price.
    for (const index of PRICE_MUTATION_ORDER) {
      if (!before.prices[index].active) continue;
      const target = PRICE_TARGETS[index];
      try {
        const updated = await deactivatePrice(env, target);
        if (updated.active) throw new Error('Price remained active');
        changedPrices.push(target.alias);
      } catch {
        mutationFailures.push(target.alias);
      }
    }
    for (const link of before.activePaymentLinks) {
      try {
        await deactivatePaymentLink(env, link);
        changedPaymentLinks += 1;
      } catch {
        mutationFailures.push('payment-link');
      }
    }

    let after: AuditState;
    try {
      after = await audit(env);
    } catch {
      return json(
        {
          error: 'Final Stripe state could not be verified',
          mutation_failures: mutationFailures.length,
          changed_payment_links: changedPaymentLinks,
          changed_prices: changedPrices.sort(),
        },
        409
      );
    }
    if (
      mutationFailures.length > 0 ||
      after.prices.some((price) => price.active) ||
      after.activePaymentLinks.length > 0
    ) {
      return json(
        {
          error: 'Exact Stripe retirement did not reach its reversible postcondition',
          mutation_failures: mutationFailures.length,
          changed_payment_links: changedPaymentLinks,
          changed_prices: changedPrices.sort(),
          ...publicState(after),
        },
        409
      );
    }
    const preflightSettlementRequired =
      before.openCheckoutSessions > 0 || before.recentCompletedCheckoutSessions > 0;
    return json({
      ok: true,
      mode: 'deactivate',
      changed_payment_links: changedPaymentLinks,
      changed_prices: changedPrices.sort(),
      ...publicState(after),
      preflight_open_checkout_sessions: before.openCheckoutSessions,
      preflight_open_checkout_hold_until: before.openCheckoutHoldUntil,
      preflight_recent_completed_checkout_sessions: before.recentCompletedCheckoutSessions,
      containment_complete: containmentComplete(after) && !preflightSettlementRequired,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown retirement error';
    return json({ error: message }, 409);
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const path = new URL(request.url).pathname;
    if (path === '/health' || path === '/status' || path === '/status.json') {
      return json({ ok: false, retired: true, maintenance: true, replacement: REPLACEMENT });
    }
    if (path !== ADMIN_PATH || request.method !== 'POST') {
      return json(
        { error: 'This legacy commerce service is retired.', replacement: REPLACEMENT },
        410
      );
    }
    if (!(await authorized(request, env))) {
      return json({ error: 'Unauthorized' }, 401);
    }
    return handleAdmin(request, env);
  },

  async queue(batch: MessageBatch<unknown>): Promise<void> {
    for (const message of batch.messages) {
      message.ack();
    }
  },
};
