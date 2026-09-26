# EOLkits audit deployment on GRACE

This deployment serves one paid capability: the $299 Audit v2 repository evidence report. Migration Pack, Drift Watch, organization licenses, GitHub App flows, and partner fulfillment are closed and return `410` or research-only responses.

## Safe rollout order

1. Import `Caddyfile.eolkits-emergency-containment.block` before the existing
   EOLKits proxy rules and reload Caddy. Prove upload GET/POST/PUT and every
   checkout/event mutation return `503`, `/pack/install` and `/pack/setup`
   return `410`, and `/webhook/stripe` still reaches the legacy process. This
   immediately closes the unauthenticated legacy upload surface while preserving
   refund/reconciliation webhooks.
2. Run `deploy-api-closed.sh --sha <reviewed-full-commit-sha>` first. Its default
   dry-run refuses the wrong path, user, tree, SHA, env-file permissions,
   Compose identity, image, volume, loopback binding, security settings, or
   checkout state. It preserves the exact live Compose project label so an
   older directory-derived deployment is adopted and rolled back under its own
   identity. Review the bounded plan, then repeat with `--apply`. It builds the
   digest-pinned image and runs the mutation-free preflight without mounting the
   production volume.
3. The guarded deployment script invokes `snapshot-api-volume.sh` before replacing
   the container. That helper stops the current container, archives the exact
   read-only data volume to a mode-0600 file under
   `/home/ubuntu/backups/eolkits`, verifies the archive contains `state.sqlite3`,
   records a SHA-256, and restarts the prior container even on failure. Do not
   inspect customer files. Keep the snapshot only for the bounded rollback
   window, then delete it deliberately after v2 is stable.
4. The script deploys with `EOLKITS_AUDIT_CHECKOUT_ENABLED=0`, verifies the exact
   build SHA plus all three loopback endpoints, and recreates the prior image if
   a gate fails. It deliberately does not restore a volume automatically:
   restoring old SQLite after a new payment could discard customer state.
5. Bootstrap the static target once, then deploy the reviewed `docs/` tree with
   `ship-web.sh` after inspecting its default dry-run; verify the public domain
   serves the repaired claims. The deploy script accepts only
   `/home/ubuntu/sites/eolkits-webroot`, resolves and validates that directory
   over SSH, and refuses to run unless its deployment sentinel is present:

   ```bash
   install -d -m 0755 /home/ubuntu/sites/eolkits-webroot
   printf '%s\n' 'eolkits-static-site-v1' > \
     /home/ubuntu/sites/eolkits-webroot/.eolkits-static-deploy-target
   chmod 0644 /home/ubuntu/sites/eolkits-webroot/.eolkits-static-deploy-target
   ```

   Run those bootstrap commands as the same unprivileged `ubuntu` account used
   for deployment. The sentinel is protected from `rsync --delete`; do not copy
   it into `docs/` or reuse it for another directory.
6. Replace the emergency block with `Caddyfile.eolkits-api.block` only after the
   loopback v2 probes pass. Validate the complete Caddyfile before reloading;
   the reviewed block uses Caddy 2.8+'s `log_skip` to prevent bearer-equivalent
   upload/report query values from entering access logs. Verify `/health`,
   `/api/status`, and `/api/capabilities`; checkout must still report disabled.
7. Run a complete Stripe **test-mode** checkout → signed webhook → real PDF render → Resend delivery → signed download → evidence lookup exercise. Do not self-charge in live mode; Stripe does not return processing fees on refunds.
8. Archive every legacy Stripe Payment Link. The exact pre-rename Cloudflare
   Worker already serves the tested retirement tombstone; do not restore its
   bindings or commerce code. An exact stale route may be removed later as
   hygiene, but public DNS bypasses Cloudflare and route cleanup is not a launch
   gate.
9. Create a new v2-only Stripe Product and one-time $299 USD Price. Never
   reactivate or reuse the retired v1 $299 Price. Put their exact IDs into
   `EOLKITS_AUDIT_PRODUCT_ID` and `EOLKITS_AUDIT_PRICE_ID`, set checkout to `1`,
   and run `python -m eolkits_grace.preflight` in the image **without the data
   volume**. The GET-only attestation requires the exact objects, active live
   mode, one-time USD 29900 amount, and matching Product before startup can
   mutate state or advertise readiness.
10. Set the repository variables `AUDIT_CHECKOUT_EXPECTED=true` and the exact
    `EOLKITS_BUILD_SHA`; redeploy and
    reopen commerce only after every preceding gate passes.

## Required environment

Create `.env.production` beside the compose file. Never commit it.

```dotenv
STRIPE_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
RESEND_API_KEY=re_...
EOLKITS_INTERNAL_URL_SECRET=<32-or-more-random-bytes>
EOLKITS_ADMIN_TOKEN=<optional-32-or-more-random-bytes>
EOLKITS_AUDIT_CHECKOUT_ENABLED=0
# Required only when changing checkout to 1; both must be new v2-only objects.
# EOLKITS_AUDIT_PRODUCT_ID=prod_...
# EOLKITS_AUDIT_PRICE_ID=price_...
EOLKITS_BUILD_SHA=<deployed-git-commit>
EOLKITS_API_PORT=8120

# Lead retention: two years. Production only: leave it out of any other
# environment's file (unset keeps leads). Read only at startup; see below.
EOLKITS_LEAD_RETENTION_DAYS=730

# Optional. Uncomment to change the default.
# LEAD_NOTIFY_TO=hello@toledotechnologies.com  # where /api/v1/lead alerts go (comma-separated)
```

`EOLKITS_LEAD_RETENTION_DAYS` is checked at startup: anything other than a whole
number from 0 to 36500 stops the API with a message naming the variable, rather
than silently turning retention off. The code default is still `0` (off: leads
are kept until deleted by hand), so an environment that does not set it keeps
everything. **Production sets `EOLKITS_LEAD_RETENTION_DAYS=730`** in
`.env.production`: lead rows older than two years are deleted at startup and
then hourly, spam included (see the lead-deletion runbook). The API reads the
value only when it starts, so if the line is not in `.env.production` yet,
adding it takes effect at the next `eolkits-api` restart, and that restart, like
any other, waits for the owner's go-ahead. Preview what it will delete first:
`docker exec eolkits-api python -m eolkits_grace.lead_admin purge --days 730 --dry-run`.

Generate secrets on the deployment host with `openssl rand -hex 32`. GitHub App credentials are not used by Audit v2 and must not be added.

## Deploy checkout closed

Use the checked-in compose file from a reviewed clone. The normal path is the
guarded dry-run followed by the same command with `--apply`:

```bash
export EOLKITS_BUILD_SHA=<reviewed-full-commit-sha>
deploy/grace/deploy-api-closed.sh --sha "$EOLKITS_BUILD_SHA"
deploy/grace/deploy-api-closed.sh --sha "$EOLKITS_BUILD_SHA" --apply
```

The wrapper consolidates and verifies the following underlying sequence. These
commands are documented for incident diagnosis, not as an alternate unchecked
rollout:

```bash
docker compose -f deploy/grace/docker-compose.eolkits-api.yml \
  --env-file deploy/grace/.env.production build eolkits-api
docker run --rm --read-only --network none \
  --cap-drop ALL --security-opt no-new-privileges --pids-limit 64 --memory 512m \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m,mode=1777 \
  --env-file deploy/grace/.env.production \
  --env ENVIRONMENT=production \
  --env EOLKITS_AUDIT_CHECKOUT_ENABLED=0 \
  "eolkits-api:$EOLKITS_BUILD_SHA" python -m eolkits_grace.preflight
bash deploy/grace/snapshot-api-volume.sh
docker compose -f deploy/grace/docker-compose.eolkits-api.yml \
  --env-file deploy/grace/.env.production up -d --no-build
curl -fsS http://127.0.0.1:8120/health | jq
curl -fsS http://127.0.0.1:8120/api/capabilities | jq -e '.audit.checkout_enabled == false and .audit.report_version == "2.0"'
```

The Compose service runs as numeric UID/GID 10001, with a read-only root
filesystem, all capabilities dropped, `no-new-privileges`, bounded resources,
a private temporary filesystem, and loopback-only publication. Customer-data
directories are tightened to mode 0700 and SQLite/uploads/reports to mode 0600.
Do not relax those settings to make a failed rollout start.

Expected closed-preflight output contains only mode and booleans:

```json
{"catalog_attested": false, "checkout_enabled": false, "environment": "production", "ok": true}
```

Before enabling checkout, repeat the `docker run` command with network access,
the new v2 Product/Price variables present, and
`EOLKITS_AUDIT_CHECKOUT_ENABLED=1`. Do not attach `eolkits_api_data` to that
preflight container. A catalog mismatch or Stripe error must stop the rollout.

Validate the final public surface:

```bash
curl -fsS https://eolkits.com/health | jq
curl -fsS https://eolkits.com/api/status | jq -e '.overall == "healthy"'
curl -fsS https://eolkits.com/api/capabilities | jq
```

## Active public endpoints

- `GET /health`, `/api/status`, `/api/capabilities`
- `POST /upload/presign`, `PUT /upload/{upload_id}`
- signed `GET /upload/{upload_id}` and `/upload/report/{report_id}`
- `POST /api/audit/checkout`
- `POST /api/events` for bounded, allowlisted, non-commerce funnel events
- `POST /webhook/stripe`
- `GET /verify/{fingerprint}` and `/api/verify/{fingerprint}`
- `POST /api/v1/lead` for honest research requests
- authenticated `POST /admin/reconcile-refund`

## Lead bus (`/api/v1/lead`)

The Toledo sites post their contact forms here, as native HTML forms or with
`fetch`.

- Fetch/JSON clients (for example SiteLift's Fit Check), curl and
  server-to-server callers get `{"ok": true, "lead_id": N}`,
  `{"detail": "..."}` on errors, or a 303 to an allow-listed `_next`. These
  responses are pinned byte for byte by `apps/grace-api/test/test_lead_json_contract.py`.
- A native browser form submission (form body sent as a navigation) gets a
  small HTML page instead of raw JSON when it fails (400, 413, 429, 5xx) or
  succeeds without a usable `_next`. The page keeps the status code, runs no
  script, loads nothing, and links back only to an allow-listed studio site.
- Owner alerts: a lead counts as alerted only when Resend accepts the email.
  Unalerted `ok` and `suspect` leads are re-sent at startup and hourly, with
  the contact details even when a long message was shortened in storage.
- Spam screening (below) decides which leads alert the owner. It never changes
  what is stored or what the visitor sees.
- Deleting one person's data, and the optional retention period:
  [`runbooks/lead-deletion.md`](runbooks/lead-deletion.md). The CLI cannot
  delete the owner-notification emails; those are removed from the
  `LEAD_NOTIFY_TO` mailbox by hand.

### Lead spam screening

Almost everything the forms received from June to September 2026 was spam, and
every piece of it alerted the owner. Each submission is now stored exactly as
before and gets exactly the same response (JSON, redirect or page, pinned by
`test_lead_json_contract.py`), plus a `status` and a short `status_reason` in the
`leads` table:

| Status | Owner alert | When |
|---|---|---|
| `ok` | `New lead: ...` | everything else |
| `suspect` | `Likely spam: New lead: ...`, with a line saying why | a spam campaign's own phrase (such as "the $27,000,000 jackpot" or "... BTC is yours for withdrawal") with a link after it, where the link does not go to a listed spam host; a one-line "what is your price" message in any language; sales-pitch wording (at least one phrase a prospect does not write, such as "no cost, no obligation", plus one more outreach cue); an empty or one-word message; sent from a toledotechnologies.com or eolkits.com address |
| `spam` | none, never re-sent | a link to one of the listed shorteners or Telegraph hosts, which carried only spam (a link: naming the site in a sentence does not count); HTML or forum link markup pointing at another site |
| `duplicate` | none, never re-sent | the same address sent the same message, or a message with no text of its own, within the previous 10 minutes |

The rules are in `apps/grace-api/eolkits_grace/store.py`, section "lead
screening". Wording never stops an alert by itself: a genuine inquiry can
mention a raffle's jackpot, a casino promo, a loan offer or a crypto wallet, or
quote a scam, next to a link to its own site. The campaign phrases only make a
lead `suspect`, so it is still alerted. They follow the campaigns' own phrasing
(every jackpot the campaigns named was in the millions), so ordinary inquiries
on those topics, like the examples in `test_lead_screening.py`, stay `ok`.

`spam` and `duplicate` cost an alert, never the lead: the row is kept and
`list` shows it. `spam` needs a listed host or link markup, and that has a
price: a genuine visitor who links through one of those shorteners or a
Telegraph page, or pastes HTML such as `<a href="https://...">`, gets no alert.
On the 248 submissions from June to September these rules mark 205 as `spam`,
including all 189 prize and crypto link spams; one fake exchange transfer on an
unlisted host is `suspect`. When the campaigns move to a new shortener, the
first submission of a burst from one address alerts as `Likely spam:` and its
repeats are `duplicate`. To stop alerts from a new host, add it to
`SPAM_LINK_HOSTS` in store.py, deploy, and run `reclassify`.

A real follow-up from the same address with a different message is never a
duplicate. If screening itself fails, the lead is alerted as `ok`. Do not
filter `Likely spam:` alerts out of the inbox: real leads land there too, for
example a Discovery Routing or Care Plan form sent with only its options
picked, which counts as an empty message.

Review what screening decided, without printing what visitors wrote:

```bash
docker exec eolkits-api python -m eolkits_grace.lead_admin list --since 2026-09-01
docker exec eolkits-api python -m eolkits_grace.lead_admin list --status spam
docker exec eolkits-api python -m eolkits_grace.lead_admin list --status spam --show-message
```

If a real lead turns up as `spam` or `duplicate`, reply to it from your own
mailbox; the owner alert for it was not sent.

**Deploying screening.** The API adds the two columns when it starts (an
additive `ALTER TABLE`, run by the normal startup migration; no step to run by
hand, nothing is rewritten, and the previous image still runs against the
migrated table if you roll back). Rows captured before the deploy read as `ok`.

Expect up to one more batch of old alerts at the restart. The re-send sweep runs
as the API starts, before you can reclassify anything, and until you do, every
old row with `notified = 0` (for example spam the mailbox rejected) reads as `ok`
and is re-sent, as the current image already does each hour: at most 50 per
sweep, within the daily alert limit (`EOLKITS_LEAD_NOTIFICATION_DAILY_LIMIT`,
20 by default). That limit is shared with new leads: a large batch can use it
up, and alerts for new leads then wait (stored, `notified = 0`) until its
24-hour window, which starts at the first alert counted, runs out. So
reclassify straight after the restart, first as a preview:

```bash
docker exec eolkits-api python -m eolkits_grace.lead_admin reclassify --dry-run
docker exec eolkits-api python -m eolkits_grace.lead_admin reclassify
```

`reclassify` changes the status only (never deletes or edits a row), prints each
change with its reason, and is safe to run while the API serves and to repeat.
Rows it moves to `spam` or `duplicate` leave the re-send queue; a row that was
never alerted and moves back to `ok` or `suspect` is alerted by the next re-send
sweep (it says how many). `list` and `reclassify` refuse to run until the API
has added the columns.

Rolling back to an image without screening is safe for the data, but that image
ignores `status`: its re-send sweep would alert the owner about the spam and
duplicates captured since this deploy (they are stored with `notified = 0`,
because no alert went out), within the daily lead alert budget
(`EOLKITS_LEAD_NOTIFICATION_DAILY_LIMIT`).

The server-side checkout switch defaults to off. The static page independently keeps its form hidden unless the live capability handshake reports Audit report version `2.0` and checkout enabled.

## Test-mode E2E deployment

Production startup deliberately rejects Stripe test keys. Use the staging override and a separate Compose project/volume instead of weakening that guard:

```bash
EOLKITS_ENV_FILE=.env.test EOLKITS_API_PORT=8121 docker compose -p eolkits-api-test \
  -f deploy/grace/docker-compose.eolkits-api.yml \
  -f deploy/grace/docker-compose.eolkits-api.test.yml \
  --env-file deploy/grace/.env.test up -d --build
curl -fsS http://127.0.0.1:8121/api/capabilities | jq -e '.audit.checkout_enabled == true'
```

`deploy/grace/.env.test` must contain Stripe test credentials, a test webhook secret, Resend credentials for an owned delivery address, and a distinct internal URL secret. The service env-file selector above prevents `.env.production` from being loaded. Non-production startup also rejects live Stripe keys. Inspect `docker compose ... config` before launch, tear the test project down after evidence is captured, and never point public Caddy at it.

The staging service overrides both public URLs to `http://127.0.0.1:8121` and
does not restart automatically. Forward that port to the operator workstation so
Stripe's success redirect and signed report link resolve against the test volume:

```bash
ssh -L 8121:127.0.0.1:8121 <grace-host>
```

In a second host shell, run Stripe CLI test-mode webhook forwarding and put the
fresh `whsec_...` it prints into `deploy/grace/.env.test` before recreating the
container:

```bash
stripe listen --forward-to http://127.0.0.1:8121/webhook/stripe
```

The API container does not serve the static `/audit/` page. Exercise the exact
presign → immutable upload → checkout sequence from the repository root instead:

```bash
AUDIT_FILE=rules/public/deprecations.yml
AUDIT_SIZE="$(wc -c < "$AUDIT_FILE")"
PRESIGN="$(jq -n --arg filename "$(basename "$AUDIT_FILE")" --argjson size "$AUDIT_SIZE" \
  '{filename:$filename,size:$size}' | \
  curl -fsS -H 'Content-Type: application/json' --data-binary @- \
  http://127.0.0.1:8121/upload/presign)"
UPLOAD_ID="$(jq -er '.uploadId' <<<"$PRESIGN")"
UPLOAD_URL="$(jq -er '.uploadUrl' <<<"$PRESIGN")"
curl -fsS -X PUT -H 'Content-Type: text/yaml' --data-binary @"$AUDIT_FILE" "$UPLOAD_URL"
CHECKOUT="$(curl -fsS -H 'Accept: application/json' \
  --data-urlencode 'email=owned-delivery-address@example.com' \
  --data-urlencode "upload_id=$UPLOAD_ID" \
  --data-urlencode 'source=staging-e2e' \
  http://127.0.0.1:8121/api/audit/checkout)"
jq -er '.url' <<<"$CHECKOUT"
```

Replace the example email with an address the operator owns, open the returned
Stripe test Checkout URL in a browser, and use Stripe's documented test card.
Verify that the delivered signed PDF link opens through the tunnel and that
`/api/verify/<evidence-fingerprint>` matches the report metadata. The staging
checkout uses inline Stripe test `price_data`; it never tries to reuse the
production Price object.
