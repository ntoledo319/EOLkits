#!/usr/bin/env bash
# Optional manual deployment of docs/ to a user-writable GRACE web root.
#
# Usage (run from repo root):
#   deploy/grace/ship-web.sh            # build + DRY-RUN rsync (shows the diff, changes nothing)
#   deploy/grace/ship-web.sh --apply    # build + snapshot the live root + real rsync
#
# Required variables:
#   GRACE_HOST=ubuntu@example-host
#   GRACE_WEBROOT=/home/ubuntu/sites/eolkits-webroot
# The target must already be writable by the SSH user. This script never uses
# elevated privileges and never changes API services.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
: "${GRACE_HOST:?Set GRACE_HOST to the reviewed SSH host}"
: "${GRACE_WEBROOT:?Set GRACE_WEBROOT to the reviewed, user-writable web root}"
if [[ ! "$GRACE_HOST" =~ ^[A-Za-z0-9._@:-]+$ ]]; then
  echo "ERROR: GRACE_HOST contains unsupported characters" >&2
  exit 2
fi
if [[ ! "$GRACE_WEBROOT" =~ ^/[A-Za-z0-9._/-]+$ ]]; then
  echo "ERROR: GRACE_WEBROOT must be an absolute path containing only safe path characters" >&2
  exit 2
fi
case "$GRACE_WEBROOT" in
  /|""|*/../*|*/..) echo "ERROR: unsafe GRACE_WEBROOT" >&2; exit 2 ;;
esac

mkdir -p "$ROOT/tmp/runtime-tmp" "$ROOT/tmp/web-deploy-venv" "$ROOT/tmp/pip-cache"
export TMPDIR="$ROOT/tmp/runtime-tmp"
export PIP_CACHE_DIR="$ROOT/tmp/pip-cache"
if [ ! -x "$ROOT/tmp/web-deploy-venv/bin/python" ]; then
  python3 -m venv "$ROOT/tmp/web-deploy-venv"
fi
"$ROOT/tmp/web-deploy-venv/bin/pip" install -r apps/web/requirements-dev.txt

echo "==> Building site (deterministic; targets eolkits.com by default)"
"$ROOT/tmp/web-deploy-venv/bin/python" apps/web/build.py

echo "==> Pre-flight gate: no un-interpolated {API_URL} placeholders in docs/"
if grep -rq "{API_URL}" docs --include='*.html'; then
  echo "ERROR: {API_URL} placeholder found in docs/ — refusing to ship a broken commerce page." >&2
  grep -rl "{API_URL}" docs --include='*.html' >&2
  exit 1
fi

if [ "${1:-}" != "--apply" ]; then
  echo "==> DRY RUN — no changes will be made. Re-run with --apply to deploy."
  echo "    Target: $GRACE_HOST:$GRACE_WEBROOT/"
  rsync -avn --delete -e "ssh -o BatchMode=yes -o ConnectTimeout=15" docs/ "$GRACE_HOST:$GRACE_WEBROOT/"
  exit 0
fi

echo "==> Snapshotting current web root beside the target"
ssh -o BatchMode=yes -o ConnectTimeout=15 "$GRACE_HOST" \
  "test -d '$GRACE_WEBROOT' && tar czf '${GRACE_WEBROOT}.rollback.tgz' -C '$GRACE_WEBROOT' ."

echo "==> Deploying docs/ -> $GRACE_HOST:$GRACE_WEBROOT/  (Caddy serves files directly; no reload needed)"
rsync -av --delete -e "ssh -o BatchMode=yes -o ConnectTimeout=15" docs/ "$GRACE_HOST:$GRACE_WEBROOT/"

echo "==> Verifying live site"
curl -sI "https://eolkits.com/audit/" | head -1
if curl -fsS "https://eolkits.com/audit/" | grep -q "Repository evidence report"; then
  echo "  ✓ new conversion audit page is live"
else
  echo "  (audit page served but marker not seen — may be a CDN/cache delay)"
fi
echo "Done."
