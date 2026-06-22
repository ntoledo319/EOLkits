#!/usr/bin/env bash
# Self-running daily deploy of the EOLkits static site on the GRACE VPS.
#
# Installed at /home/ubuntu/bin/deploy-eolkits-web and run by cron. It pulls the
# latest marketing-machine-v2, rebuilds docs/ (deterministic), rsyncs to the
# static web root /var/www/eolkits, and pings IndexNow. This keeps the deadline
# countdowns accurate day-to-day and auto-ships committed content WITHOUT anyone
# touching the box — the "it runs itself" piece of the inbound engine.
#
# Safe by construction: `set -e` aborts before the rsync if the build fails, so a
# bad commit can never leave a half-written or broken webroot live.
#
# Build workspace is a dedicated clone (NOT a prod tree), so `git reset --hard`
# is safe here — unlike the GRACE backend tree (see docs/OPERATOR_RUNBOOK.md §13).
set -euo pipefail

REPO="/home/ubuntu/sites/eolkits-build"
BRANCH="marketing-machine-v2"
WEBROOT="/var/www/eolkits"
KEY="0c7a25ebf8815c561ded8ab9a156dfb5"

cd "$REPO"
git fetch --quiet origin "$BRANCH"
git reset --hard --quiet "origin/$BRANCH"

python3 apps/web/build.py  >/tmp/eolkits-web-build.log 2>&1
if [ -f feed/publish.py ]; then python3 feed/publish.py >>/tmp/eolkits-web-build.log 2>&1 || true; fi

# Pre-flight gate: never ship an un-interpolated commerce page.
if grep -rq "{API_URL}" docs --include='*.html'; then
  echo "$(date -u +%FT%TZ) ABORT: {API_URL} leak in docs/ — not shipping" >&2
  exit 1
fi

sudo rsync -a --delete docs/ "$WEBROOT/"

# IndexNow ping (best-effort; Bing/Yandex + AI engines that consume it)
URLS=$(grep -oE '<loc>[^<]+' docs/sitemap.xml | sed 's/<loc>//')
PAYLOAD=$(python3 -c "import sys,json; u=[x for x in sys.stdin.read().split() if x]; print(json.dumps({'host':'eolkits.com','key':'$KEY','keyLocation':'https://eolkits.com/$KEY.txt','urlList':u}))" <<<"$URLS")
curl -s -m 25 -o /dev/null -X POST "https://api.indexnow.org/indexnow" \
  -H "Content-Type: application/json; charset=utf-8" --data "$PAYLOAD" || true

echo "$(date -u +%FT%TZ) deployed $(echo "$URLS" | wc -l | tr -d ' ') urls @ $(git rev-parse --short HEAD)"
