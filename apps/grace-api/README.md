# EOLkits grace-api

FastAPI service behind `eolkits.com` (Caddy → `127.0.0.1:8120`). It powers the
EOLkits funnel — checkout, fulfilment, webhooks, first-party analytics — and the
shared **lead-capture bus** for the Toledo studio microsites.

- **Runtime:** FastAPI + Uvicorn (Python 3.12), container `eolkits-api`.
- **State:** SQLite at `EOLKITS_DATA_DIR/state.sqlite3` (WAL); see `store.py`.
- **Email:** Resend (`email.py`), from `noreply@eolkits.com`.
- **Deploy:** `docker compose up -d eolkits-api` from the repo root on the GRACE
  VPS (project `eolkits-api`, root `docker-compose.yml`; reuses volume
  `eolkits-api_eolkits_api_data`). Env: repo-root `.env.production`.

## Key endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health`, `/status` | liveness + component health |
| POST | `/api/events` | first-party funnel beacon (no third-party tracker) |
| POST | `/api/v1/lead` | **generic lead capture** (studio + any product) — see below |
| POST | `/api/audit/checkout`, `/api/pack/checkout` | Stripe checkout (drift retired 2026-07-22 → 410) |
| POST | `/webhook/stripe`, `/webhook/github` | webhooks (idempotent) |
| POST | `/api/license/inquiry`, `/partners/signup` | inquiry/partner forms |

## `POST /api/v1/lead` — the studio lead bus

Replaces FormSubmit (which was dead at mxroute and silently dropped every studio
submission). Built to be the durable capture for the whole portfolio.

- **Durable-first:** writes every submission to the `leads` table — the guarantee
  a lead is never lost, independent of email delivery.
- **Notifies on a working path:** Resend → `LEAD_NOTIFY_TO` (comma-separated;
  defaults to `hello@toledotechnologies.com`, set to a guaranteed-deliverable
  inbox in prod). Best-effort; the DB row is the source of truth.
- **Generic** across heterogeneous forms: accepts native form-POST
  (urlencoded/multipart) **or** JSON. Non-`_`-prefixed fields are captured
  verbatim (checkbox arrays joined); `email`/`name` are sniffed from common keys.
- **Response:** native forms 303-redirect to `_next` — absolute (allow-listed
  origin) or site-relative (`/path` resolved against the request `Origin`, also
  allow-listed, so it can never open-redirect). No redirect target → JSON
  `{ok, lead_id}` (the AJAX path, e.g. SiteLift).
- **Spam:** the `_honey` honeypot field, when filled, is accepted silently and
  recorded as nothing.

Origins (CORS + redirect allowlist) are the `_SITE_ORIGINS` tuple in `app.py`:
eolkits.com + the six `*.toledotechnologies.com` studio surfaces.

Tests: `test/test_lead.py` (7 cases — JSON, form-303, origin-relative redirect,
open-redirect rejection, honeypot, email-required, heterogeneous/checkbox fields).

```bash
cd apps/grace-api && python3 -m pytest test/ -q   # full suite
```
