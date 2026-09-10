#!/usr/bin/env bash
# Create a restricted, consistent archive of the stopped production data volume.
# The container is restarted automatically, including after a failed snapshot.

set -euo pipefail

readonly CONTAINER_NAME="eolkits-api"
readonly BACKUP_DIR="/home/ubuntu/backups/eolkits"

if [[ "$(id -u)" == "0" ]]; then
  echo "ERROR: run as the unprivileged GRACE deploy user, not root" >&2
  exit 2
fi
if [[ -L "$BACKUP_DIR" ]]; then
  echo "ERROR: backup directory must not be a symlink" >&2
  exit 2
fi
install -d -m 0700 "$BACKUP_DIR"
if [[ "$(readlink -f -- "$BACKUP_DIR")" != "$BACKUP_DIR" ]]; then
  echo "ERROR: backup directory resolved outside the approved path" >&2
  exit 2
fi

image_id="$(docker inspect --format '{{.Image}}' "$CONTAINER_NAME")"
was_running="$(docker inspect --format '{{.State.Running}}' "$CONTAINER_NAME")"
volume_name="$(
  docker inspect --format \
    '{{range .Mounts}}{{if eq .Destination "/data/eolkits"}}{{.Name}}{{end}}{{end}}' \
    "$CONTAINER_NAME"
)"
if [[ ! "$image_id" =~ ^sha256:[a-f0-9]{64}$ ]]; then
  echo "ERROR: could not resolve the exact deployed image" >&2
  exit 2
fi
if [[ ! "$volume_name" =~ ^[A-Za-z0-9_.-]+$ ]]; then
  echo "ERROR: could not resolve one safe /data/eolkits volume name" >&2
  exit 2
fi

restart_if_needed() {
  if [[ "$was_running" == "true" ]]; then
    docker start "$CONTAINER_NAME"
  fi
}
trap restart_if_needed EXIT

if [[ "$was_running" == "true" ]]; then
  docker stop --time 30 "$CONTAINER_NAME"
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive="$BACKUP_DIR/eolkits-api-pre-v2-$timestamp.tgz"
partial="$archive.partial.$$"
listing="$archive.contents.$$"
if [[ -e "$archive" || -e "$partial" || -e "$listing" ]]; then
  echo "ERROR: refusing to overwrite an existing snapshot artifact" >&2
  exit 2
fi
umask 077
docker run --rm --network none --read-only \
  --volume "$volume_name:/data/eolkits:ro" \
  --entrypoint tar "$image_id" \
  -czf - -C /data/eolkits . >"$partial"
test -s "$partial"
tar -tzf "$partial" >"$listing"
grep -qx './state.sqlite3' "$listing"
mv "$partial" "$archive"
sha256sum "$archive" >"$archive.sha256"
chmod 0600 "$archive" "$archive.sha256" "$listing"

printf 'Created restricted rollback snapshot: %s\n' "$archive"
printf 'Snapshot checksum: '
cut -d' ' -f1 "$archive.sha256"
