#!/usr/bin/env bash
# Optional isolated static build and deployment to a user-writable GRACE root.
#
# Usage (run from repo root):
#   deploy/grace/ship-web.sh            # build + DRY-RUN rsync (shows the diff, changes nothing)
#   deploy/grace/ship-web.sh --apply    # build + snapshot the live root + real rsync
#
# Required variables:
#   GRACE_HOST=ubuntu@example-host
#   GRACE_WEBROOT=/home/ubuntu/sites/eolkits-webroot
# The target must be a real directory owned by this deployment, writable by the
# SSH user, and contain the sentinel documented in deploy/grace/README.md. This
# script never uses elevated privileges and never changes API services.
set -euo pipefail
# These are exclusively public assets; rsync -a preserves their permissions.
umask 022

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
if (( $# > 1 )); then
  echo "ERROR: expected at most one argument" >&2
  exit 2
fi
case "${1:-}" in
  -h|--help)
    printf '%s\n' 'Usage: deploy/grace/ship-web.sh [--apply]' \
      'Default: isolated build, remote target validation, and rsync dry run.' \
      'Requires GRACE_HOST and GRACE_WEBROOT; --apply snapshots and deploys.'
    exit 0
    ;;
  ""|--apply) ;;
  *) echo "ERROR: unknown argument: $1" >&2; exit 2 ;;
esac
: "${GRACE_HOST:?Set GRACE_HOST to the reviewed SSH host}"
: "${GRACE_WEBROOT:?Set GRACE_WEBROOT to the reviewed, user-writable web root}"
readonly EXPECTED_GRACE_WEBROOT="/home/ubuntu/sites/eolkits-webroot"
readonly DEPLOY_SENTINEL=".eolkits-static-deploy-target"
readonly DEPLOY_SENTINEL_VALUE="eolkits-static-site-v1"
if [[ ! "$GRACE_HOST" =~ ^[A-Za-z0-9][A-Za-z0-9._@:-]*$ ]]; then
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
if [ "$GRACE_WEBROOT" != "$EXPECTED_GRACE_WEBROOT" ]; then
  echo "ERROR: GRACE_WEBROOT must be exactly $EXPECTED_GRACE_WEBROOT" >&2
  exit 2
fi

validate_remote_target() {
  ssh -o BatchMode=yes -o ConnectTimeout=15 "$GRACE_HOST" sh -s -- \
    "$GRACE_WEBROOT" \
    "$EXPECTED_GRACE_WEBROOT" \
    "$DEPLOY_SENTINEL" \
    "$DEPLOY_SENTINEL_VALUE" <<'REMOTE_CHECK'
set -eu
target=$1
expected_target=$2
sentinel_name=$3
expected_value=$4

[ "$target" = "$expected_target" ] || {
  echo "ERROR: remote target does not match the approved path" >&2
  exit 1
}
[ -d "$target" ] && [ ! -L "$target" ] && [ -w "$target" ] || {
  echo "ERROR: remote target must be a writable, non-symlink directory" >&2
  exit 1
}
resolved_target=$(readlink -f -- "$target")
[ "$resolved_target" = "$expected_target" ] || {
  echo "ERROR: resolved remote target is not the approved path" >&2
  exit 1
}
sentinel="$target/$sentinel_name"
[ -f "$sentinel" ] && [ ! -L "$sentinel" ] || {
  echo "ERROR: deployment sentinel is missing or unsafe" >&2
  exit 1
}
actual_value=$(cat -- "$sentinel")
[ "$actual_value" = "$expected_value" ] || {
  echo "ERROR: deployment sentinel has the wrong identity" >&2
  exit 1
}
REMOTE_CHECK
}

create_remote_snapshot() {
  ssh -o BatchMode=yes -o ConnectTimeout=15 "$GRACE_HOST" sh -s -- \
    "$GRACE_WEBROOT" <<'REMOTE_SNAPSHOT'
set -eu
target=$1
timestamp=$(date -u +%Y%m%dT%H%M%SZ)
snapshot="${target}.rollback.${timestamp}.$$.tgz"
umask 077
[ ! -e "$snapshot" ] || {
  echo "ERROR: refusing to overwrite rollback snapshot $snapshot" >&2
  exit 1
}
tar czf "$snapshot" -C "$target" .
printf 'Created rollback snapshot: %s\n' "$snapshot"
REMOTE_SNAPSHOT
}

mkdir -p \
  "$ROOT/tmp/runtime-tmp" \
  "$ROOT/tmp/sample-deploy-venv" \
  "$ROOT/tmp/web-deploy-venv" \
  "$ROOT/tmp/pip-cache"
export TMPDIR="$ROOT/tmp/runtime-tmp"
export PIP_CACHE_DIR="$ROOT/tmp/pip-cache"
STAGE_DIR="$(mktemp -d "$TMPDIR/eolkits-web.XXXXXX")"
trap 'rm -rf -- "$STAGE_DIR"' EXIT
chmod 0755 "$STAGE_DIR"
if [ ! -x "$ROOT/tmp/sample-deploy-venv/bin/python" ]; then
  python3 -m venv "$ROOT/tmp/sample-deploy-venv"
fi
if [ ! -x "$ROOT/tmp/web-deploy-venv/bin/python" ]; then
  python3 -m venv "$ROOT/tmp/web-deploy-venv"
fi
"$ROOT/tmp/sample-deploy-venv/bin/pip" install --require-hashes -r apps/runner/requirements.lock
"$ROOT/tmp/web-deploy-venv/bin/pip" install --require-hashes -r apps/web/requirements-dev.lock

echo "==> Verifying the committed sample against the paid report engine"
"$ROOT/tmp/sample-deploy-venv/bin/python" apps/runner/build_sample_report.py --check

echo "==> Building site (deterministic; targets eolkits.com by default)"
EOLKITS_BASE_PATH='' EOLKITS_SITE_URL='https://eolkits.com' \
  EOLKITS_API_URL='https://eolkits.com' \
  "$ROOT/tmp/web-deploy-venv/bin/python" apps/web/build.py --output "$STAGE_DIR"
"$ROOT/tmp/web-deploy-venv/bin/python" scripts/verify_static_release.py \
  --directory "$STAGE_DIR"

echo "==> Pre-flight gate: release contains no symlinks"
if find "$STAGE_DIR" -type l -print -quit | grep -q .; then
  echo "ERROR: release contains a symlink — refusing to deploy." >&2
  find "$STAGE_DIR" -type l -print >&2
  exit 1
fi

echo "==> Pre-flight gate: no un-interpolated {API_URL} placeholders in release"
if grep -rq "{API_URL}" "$STAGE_DIR" --include='*.html'; then
  echo "ERROR: {API_URL} placeholder found in release — refusing to ship a broken commerce page." >&2
  grep -rl "{API_URL}" "$STAGE_DIR" --include='*.html' >&2
  exit 1
fi

if [ "${1:-}" != "--apply" ]; then
  echo "==> Validating the remote deployment identity"
  validate_remote_target
  echo "==> DRY RUN — no changes will be made. Re-run with --apply to deploy."
  echo "    Target: $GRACE_HOST:$GRACE_WEBROOT/"
  rsync -avn --delete \
    --filter="protect /$DEPLOY_SENTINEL" \
    -e "ssh -o BatchMode=yes -o ConnectTimeout=15" \
    "$STAGE_DIR/" "$GRACE_HOST:$GRACE_WEBROOT/"
  exit 0
fi

echo "==> Validating the remote deployment identity"
validate_remote_target
echo "==> Snapshotting current web root beside the target"
create_remote_snapshot
echo "==> Revalidating the remote deployment identity"
validate_remote_target

echo "==> Deploying verified release -> $GRACE_HOST:$GRACE_WEBROOT/  (Caddy serves files directly; no reload needed)"
rsync -av --delete \
  --filter="protect /$DEPLOY_SENTINEL" \
  -e "ssh -o BatchMode=yes -o ConnectTimeout=15" \
  "$STAGE_DIR/" "$GRACE_HOST:$GRACE_WEBROOT/"

echo "==> Verifying live site"
curl -fsSI --max-time 30 "https://eolkits.com/audit/"
live_audit="$(curl -fsS --max-time 30 "https://eolkits.com/audit/")"
if ! grep -Fq "Turn a repository into reviewable AWS migration evidence" <<<"$live_audit"; then
  echo "ERROR: live audit page is missing the expected release marker." >&2
  exit 1
fi
for artifact in \
  eolkits-sample-report.json \
  eolkits-sample-report.pdf \
  fictional-repository.zip
do
  local_hash="$(sha256sum "$STAGE_DIR/audit/sample/$artifact" | cut -d' ' -f1)"
  live_hash="$(
    curl -fsS --max-time 30 "https://eolkits.com/audit/sample/$artifact" |
      sha256sum |
      cut -d' ' -f1
  )"
  if [ "$local_hash" != "$live_hash" ]; then
    echo "ERROR: live $artifact hash does not match the verified local artifact." >&2
    exit 1
  fi
done
echo "  ✓ audit page and all sample artifacts match the verified release"
echo "Done."
