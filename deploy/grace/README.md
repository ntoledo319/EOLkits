# EOLkits audit deployment on GRACE

This deployment serves one paid capability: the $299 Audit v2 repository evidence report. Migration Pack, Drift Watch, organization licenses, GitHub App flows, and partner fulfillment are closed and return `410` or research-only responses.

## Safe rollout order

1. Import `Caddyfile.eolkits-emergency-containment.block` before the existing
   EOLKits proxy rules and reload Caddy. Prove upload GET/POST/PUT and every
   checkout/event mutation return `503`, `/pack/install` and `/pack/setup`
   return `410`, and `/webhook/stripe` still reaches the legacy process. This
   immediately closes the unauthenticated legacy upload surface while preserving
   refund/reconciliation webhooks.
2. Build the exact reviewed image and run the mutation-free preflight without
   mounting the production volume. With checkout closed, this validates the
   production secret modes without contacting Stripe or touching SQLite.
3. Run `snapshot-api-volume.sh` on GRACE. It stops the current container, archives
   the exact read-only data volume to a mode-0600 file under
   `/home/ubuntu/backups/eolkits`, verifies the archive contains `state.sqlite3`,
   records a SHA-256, and restarts the prior container even on failure. Do not
   inspect customer files. Keep the snapshot only for the bounded rollback
   window, then delete it deliberately after v2 is stable.
4. Deploy the API with `EOLKITS_AUDIT_CHECKOUT_ENABLED=0`. Runtime preflight now
   completes before the application creates directories, migrates SQLite, or
   redacts historical event payloads.
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
   loopback v2 probes pass. Verify `/health`, `/api/status`, and
   `/api/capabilities`; checkout must still report disabled.
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
```

Generate secrets on the deployment host with `openssl rand -hex 32`. GitHub App credentials are not used by Audit v2 and must not be added.

## Deploy checkout closed

Use the checked-in compose file from a reviewed clone. Build and preflight the
exact image with no production volume attached before running the snapshot:

```bash
export EOLKITS_BUILD_SHA=<reviewed-full-commit-sha>
docker compose -f deploy/grace/docker-compose.eolkits-api.yml \
  --env-file deploy/grace/.env.production build eolkits-api
docker run --rm --read-only --network none \
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
