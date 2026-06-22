#!/usr/bin/env bash
# Ship the EOLkits static site (docs/) to the GRACE VPS static web root.
#
# Closes the "deploy gap" (SEO-GRACE-HANDOFF.md §7.1): the static `eolkits`
# satellite is served by host Caddy from /var/www/eolkits and was deployed by
# hand. This is the ONE step Claude Code can't do itself (no SSH from the dev
# env) — run it from your workstation, which has the VPS key.
#
# Usage (run from repo root):
#   deploy/grace/ship-web.sh            # build + DRY-RUN rsync (shows the diff, changes nothing)
#   deploy/grace/ship-web.sh --apply    # build + snapshot the live root + real rsync
#
# Overrides (defaults from HANDOFF-2026-06-08.md):
#   GRACE_HOST=ubuntu@15.204.209.97 GRACE_WEBROOT=/var/www/eolkits deploy/grace/ship-web.sh --apply
#
# The API satellite (eolkits-api / apps/grace-api) is already live and is NOT
# touched here — this ships only the static site.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
GRACE_HOST="${GRACE_HOST:-ubuntu@15.204.209.97}"
GRACE_WEBROOT="${GRACE_WEBROOT:-/var/www/eolkits}"

echo "==> Building site (deterministic; targets eolkits.com by default)"
python3 apps/web/build.py
if [ -f feed/publish.py ]; then python3 feed/publish.py; fi

echo "==> Pre-flight gate: no un-interpolated {API_URL} placeholders in docs/"
if grep -rq "{API_URL}" docs --include='*.html'; then
  echo "ERROR: {API_URL} placeholder found in docs/ — refusing to ship a broken commerce page." >&2
  grep -rl "{API_URL}" docs --include='*.html' >&2
  exit 1
fi

if [ "${1:-}" != "--apply" ]; then
  echo "==> DRY RUN — no changes will be made. Re-run with --apply to deploy."
  echo "    Target: $GRACE_HOST:$GRACE_WEBROOT/"
  rsync -avn --delete docs/ "$GRACE_HOST:$GRACE_WEBROOT/"
  exit 0
fi

echo "==> Snapshotting current web root (fast rollback: untar this if needed)"
ssh "$GRACE_HOST" "sudo tar czf /tmp/eolkits-webroot-backup-\$(date +%F-%H%M).tgz -C \"\$(dirname '$GRACE_WEBROOT')\" \"\$(basename '$GRACE_WEBROOT')\"" || \
  echo "  (snapshot skipped — continuing)"

echo "==> Deploying docs/ -> $GRACE_HOST:$GRACE_WEBROOT/  (Caddy serves files directly; no reload needed)"
rsync -av --delete docs/ "$GRACE_HOST:$GRACE_WEBROOT/"

echo "==> Verifying live site"
curl -sI "https://eolkits.com/audit/" | head -1
if curl -s "https://eolkits.com/audit/" | grep -q "money-back"; then
  echo "  ✓ new conversion audit page is live"
else
  echo "  (audit page served but marker not seen — may be a CDN/cache delay)"
fi
echo "Done."
