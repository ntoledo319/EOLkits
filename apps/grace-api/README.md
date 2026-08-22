# EOLkits grace-api

FastAPI service intended for `eolkits.com` (Caddy → `127.0.0.1:8120`). It can
fulfill one product: the Audit v2 static repository evidence report. Checkout
defaults to disabled and remains unavailable until the real deployment passes
the test-mode operational gate in `deploy/grace/README.md`.

- **Runtime:** FastAPI + Uvicorn (Python 3.12), container `eolkits-api`.
- **State:** SQLite at `EOLKITS_DATA_DIR/state.sqlite3` (WAL); see `store.py`.
- **Email:** Resend (`email.py`), from `noreply@eolkits.com`.
- **Deploy:** use `deploy/grace/docker-compose.eolkits-api.yml` and the exact
  closed-checkout rollout in `deploy/grace/README.md`.

## Key endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health`, `/status` | public liveness + component readiness; detailed counts require `X-Admin-Token` |
| POST | `/api/events` | bounded first-party aggregate events (no visitor ID or third-party tracker) |
| GET | `/api/capabilities` | fail-closed storefront readiness handshake |
| POST | `/upload/presign`, `PUT /upload/{id}` | bounded, immutable Audit input |
| POST | `/api/audit/checkout` | Stripe checkout, when explicitly enabled and ready |
| POST | `/webhook/stripe` | idempotent payment/refund events |
| GET | `/verify/{fingerprint}` | report evidence lookup |
| POST | `/api/v1/lead` | bounded product-research lead capture |

Migration Pack, Drift Watch, organization-license, GitHub App, and partner
commerce routes are closed. Legacy events are retained only so stale payments
can enter the refund/reconciliation path.

Browser telemetry stays dormant until `/api/capabilities` proves report version
2.0. The API accepts only an exact CORS origin, allowlisted event names, canonical
page categories, and compact non-PII attribution tokens. Raw events expire after
30 days, abuse-rate keys after two days, and event ingestion stops at a bounded
SQLite/WAL size. Public status never exposes funnel, commerce, or per-order data.

## `POST /api/v1/lead` — the studio lead bus

Stores explicitly submitted research/contact requests durably before attempting
email notification.

- **Durable-first:** writes accepted submissions to the `leads` table before
  attempting notification. Storage failure returns an error; no system can
  promise that a lead is never lost.
- **Notifies on a working path:** Resend → `LEAD_NOTIFY_TO` (comma-separated;
  defaults to `hello@toledotechnologies.com`; set it to an operator-verified
  inbox in production. Best-effort; the DB row is the source of truth.
- **Generic** across heterogeneous forms: accepts native form-POST
  (urlencoded/multipart) **or** JSON. Non-`_`-prefixed fields are captured
  verbatim (checkbox arrays joined); `email`/`name` are sniffed from common keys.
- **Response:** native forms 303-redirect to `_next` — absolute (allow-listed
  origin) or site-relative (`/path` resolved against the request `Origin`, also
  allow-listed, so it can never open-redirect). No redirect target → JSON
  `{ok, lead_id}` (the AJAX path, e.g. SiteLift).
- **Spam:** the `_honey` honeypot field, when filled, is accepted silently and
  recorded as nothing.

Origins (CORS + redirect allowlist) are the `_SITE_ORIGINS` tuple in `app.py`.

```bash
python3 -m venv tmp/grace-venv
tmp/grace-venv/bin/pip install -r apps/grace-api/requirements-dev.txt
tmp/grace-venv/bin/pytest -q apps/grace-api
```
