# Retired Cloudflare worker

This minimal Worker exists only to replace an old deployed route with explicit
HTTP 410 responses. The former checkout, webhook, upload, subscription, license,
partner, and queue implementations were deleted; Git history is the archive.

The active service is `apps/grace-api`. The normal `npm run deploy` command fails
deliberately. `deploy:retired-tombstone` exists only to replace a previously
deployed Worker with the closed response while an operator removes its route and
Stripe webhook endpoint. It has no KV, R2, Queue, AI, Stripe, or GitHub bindings.
