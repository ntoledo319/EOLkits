#!/usr/bin/env bash
# Build, preflight, snapshot, and deploy the reviewed Audit v2 API with checkout
# forced closed. Caddy, test checkout, refunds, indexing, and live enablement are
# deliberately outside this boundary.

set -Eeuo pipefail

readonly EXPECTED_REPO_ROOT="/home/ubuntu/sites/eolkits-api"
readonly SERVICE_NAME="eolkits-api"
readonly CONTAINER_NAME="eolkits-api"

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 2
}

usage() {
  cat <<'EOF'
Usage: deploy/grace/deploy-api-closed.sh --sha <40-hex-commit> [--apply]

Without --apply, validates the host/repository/current deployment and prints the
bounded mutation plan. --apply builds, runs the no-volume production preflight,
snapshots the current volume, deploys checkout-closed, and verifies all loopback
health gates. It never edits Caddy or enables checkout.
EOF
}

apply=false
reviewed_sha=""
while (($#)); do
  case "$1" in
    --apply)
      apply=true
      shift
      ;;
    --sha)
      (($# >= 2)) || die "--sha requires a value"
      reviewed_sha="$2"
      shift 2
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[[ "$reviewed_sha" =~ ^[a-f0-9]{40}$ ]] || die "--sha must be one full lowercase commit SHA"
[[ "$(id -u)" != "0" ]] || die "run as the unprivileged GRACE deploy user, not root"

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || die "not inside a Git checkout"
repo_root="$(readlink -f -- "$repo_root")"
[[ "$repo_root" == "$EXPECTED_REPO_ROOT" ]] || die "repository must resolve to $EXPECTED_REPO_ROOT"
cd "$repo_root"

[[ "$(git rev-parse HEAD)" == "$reviewed_sha" ]] || die "HEAD does not match --sha"
[[ -z "$(git status --porcelain --untracked-files=normal)" ]] || die "working tree is not clean"

readonly COMPOSE_FILE="$repo_root/deploy/grace/docker-compose.eolkits-api.yml"
readonly ENV_FILE="$repo_root/deploy/grace/.env.production"
readonly SNAPSHOT_SCRIPT="$repo_root/deploy/grace/snapshot-api-volume.sh"
[[ -f "$COMPOSE_FILE" && ! -L "$COMPOSE_FILE" ]] || die "unsafe or missing Compose file"
[[ -f "$ENV_FILE" && ! -L "$ENV_FILE" ]] || die "unsafe or missing .env.production"
[[ -f "$SNAPSHOT_SCRIPT" && ! -L "$SNAPSHOT_SCRIPT" ]] || die "unsafe or missing snapshot script"
[[ "$(readlink -f -- "$ENV_FILE")" == "$ENV_FILE" ]] || die ".env.production resolved unexpectedly"
[[ "$(stat -c '%u' "$ENV_FILE")" == "$(id -u)" ]] || die ".env.production is not owned by the deploy user"
env_mode="$(stat -c '%a' "$ENV_FILE")"
env_mode="${env_mode: -3}"
(( (8#$env_mode & 077) == 0 )) || die ".env.production must not be group/world accessible"

previous_image_id="$(docker inspect --format '{{.Image}}' "$CONTAINER_NAME" 2>/dev/null)" ||
  die "current $CONTAINER_NAME container is unavailable"
previous_running="$(docker inspect --format '{{.State.Running}}' "$CONTAINER_NAME")"
previous_project="$(docker inspect --format '{{index .Config.Labels "com.docker.compose.project"}}' "$CONTAINER_NAME")"
previous_service="$(docker inspect --format '{{index .Config.Labels "com.docker.compose.service"}}' "$CONTAINER_NAME")"
volume_name="$(
  docker inspect "$CONTAINER_NAME" | jq -er '
    [.[0].Mounts[] | select(.Type == "volume" and .Destination == "/data/eolkits")]
    | if length == 1 then .[0].Name else error("expected one data volume") end
  '
)" || die "could not resolve exactly one /data/eolkits volume"

[[ "$previous_image_id" =~ ^sha256:[a-f0-9]{64}$ ]] || die "current image ID is not immutable"
[[ "$previous_running" == "true" ]] || die "current API container is not running"
[[ "$previous_project" =~ ^[a-z0-9][a-z0-9_.-]{0,62}$ ]] ||
  die "current container has an unsafe Compose project identity"
[[ "$previous_service" == "$SERVICE_NAME" ]] || die "current container belongs to unexpected Compose service"
[[ "$volume_name" =~ ^[A-Za-z0-9_.-]+$ ]] || die "unsafe production volume name"
readonly PROJECT_NAME="$previous_project"

compose_with_sha() {
  local build_sha="$1"
  shift
  env EOLKITS_BUILD_SHA="$build_sha" EOLKITS_AUDIT_CHECKOUT_ENABLED=0 \
    docker compose --project-name "$PROJECT_NAME" --file "$COMPOSE_FILE" \
    --env-file "$ENV_FILE" "$@"
}

compose_with_sha "$reviewed_sha" config --quiet
rendered_config="$(compose_with_sha "$reviewed_sha" config --format json)"
rendered_image="$(jq -er '.services["eolkits-api"].image' <<<"$rendered_config")"
[[ "$rendered_image" == "eolkits-api:$reviewed_sha" ]] || die "Compose did not render the reviewed image tag"
jq -e --arg sha "$reviewed_sha" --arg project "$PROJECT_NAME" '
  (.name == $project) and
  (.services["eolkits-api"] as $service |
    $service.user == "10001:10001" and
    $service.read_only == true and
    ($service.cap_drop | index("ALL")) != null and
    ($service.security_opt | index("no-new-privileges:true")) != null and
    $service.environment.EOLKITS_AUDIT_CHECKOUT_ENABLED == "0" and
    $service.environment.EOLKITS_BUILD_SHA == $sha and
    any($service.ports[];
      .host_ip == "127.0.0.1" and .published == "8120" and .target == 8080))
' <<<"$rendered_config" >/dev/null || die "Compose security/checkout/loopback invariants did not render"
unset rendered_config

rollback_suffix="rollback-${previous_image_id#sha256:}"
rollback_suffix="${rollback_suffix:0:21}"
rollback_image="eolkits-api:$rollback_suffix"
deployment_started=false
rollback_ready=false

# shellcheck disable=SC2317  # invoked from the EXIT/signal trap
rollback() {
  local original_status="$1"
  trap - EXIT INT TERM
  set +e
  printf 'Deployment gate failed; recreating the prior image with checkout closed.\n' >&2
  compose_with_sha "$rollback_suffix" up -d --no-build --force-recreate "$SERVICE_NAME"
  rollback_status=$?
  if ((rollback_status == 0)); then
    printf 'Prior image restored as %s. Emergency Caddy containment must remain active.\n' \
      "$rollback_image" >&2
  else
    printf 'Automatic image rollback failed; keep emergency containment active and use the printed snapshot.\n' >&2
  fi
  exit "$original_status"
}

# shellcheck disable=SC2317  # registered dynamically below
on_exit() {
  status=$?
  trap - EXIT INT TERM
  if ((status != 0)) && [[ "$deployment_started" == "true" && "$rollback_ready" == "true" ]]; then
    rollback "$status"
  fi
  exit "$status"
}
trap on_exit EXIT
# Normalize signals to non-zero exits so the EXIT trap cannot inherit a prior
# successful command status and accidentally skip an in-progress rollback.
trap 'exit 130' INT
trap 'exit 143' TERM

if [[ "$apply" != "true" ]]; then
  cat <<EOF
Dry-run passed. --apply will perform only this sequence:
  1. Preserve prior image $previous_image_id as $rollback_image.
  2. Preserve Compose project $PROJECT_NAME and build eolkits-api:$reviewed_sha
     from the digest-pinned Dockerfile.
  3. Run checkout-closed production preflight with no network or data volume.
  4. Snapshot production volume $volume_name with snapshot-api-volume.sh.
  5. Deploy with checkout forced to 0 and no image rebuild.
  6. Require exact SHA, production, inline runner, report v2, healthy status,
     and checkout-disabled loopback responses; roll back the image on failure.

No Caddy, Stripe catalog, email, refund, volume-restore, or indexing mutation is included.
EOF
  exit 0
fi

if docker image inspect "$rollback_image" >/dev/null 2>&1; then
  [[ "$(docker image inspect --format '{{.Id}}' "$rollback_image")" == "$previous_image_id" ]] ||
    die "rollback tag already points at a different image"
else
  docker image tag "$previous_image_id" "$rollback_image"
fi
rollback_ready=true

compose_with_sha "$reviewed_sha" build --pull "$SERVICE_NAME"
new_image_id="$(docker image inspect --format '{{.Id}}' "eolkits-api:$reviewed_sha")"
[[ "$new_image_id" =~ ^sha256:[a-f0-9]{64}$ ]] || die "reviewed image was not built"
[[ "$new_image_id" != "$previous_image_id" ]] || die "reviewed build unexpectedly equals the prior image"

docker run --rm --read-only --network none \
  --cap-drop ALL --security-opt no-new-privileges --pids-limit 64 --memory 512m \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m,mode=1777 \
  --env-file "$ENV_FILE" \
  --env ENVIRONMENT=production \
  --env EOLKITS_AUDIT_CHECKOUT_ENABLED=0 \
  --env EOLKITS_BUILD_SHA="$reviewed_sha" \
  "eolkits-api:$reviewed_sha" python -m eolkits_grace.preflight

snapshot_output="$(bash "$SNAPSHOT_SCRIPT")"
printf '%s\n' "$snapshot_output"

deployment_started=true
compose_with_sha "$reviewed_sha" up -d --no-build "$SERVICE_NAME"

health_json=""
status_json=""
capabilities_json=""
probe_deadline=$((SECONDS + 60))
while ((SECONDS < probe_deadline)); do
  health_json="$(curl --fail --silent --show-error --max-time 1 http://127.0.0.1:8120/health 2>/dev/null || true)"
  status_json="$(curl --fail --silent --show-error --max-time 1 http://127.0.0.1:8120/api/status 2>/dev/null || true)"
  capabilities_json="$(curl --fail --silent --show-error --max-time 1 http://127.0.0.1:8120/api/capabilities 2>/dev/null || true)"
  if jq -e --arg sha "$reviewed_sha" '
      .ok == true and .env == "production" and .runner == "inline" and
      .build_sha == $sha and .audit_report_version == "2.0"
    ' <<<"$health_json" >/dev/null 2>&1 &&
    jq -e '
      .overall == "healthy" and .environment == "production" and
      .components.storage.ok == true and .components.stripe.ok == true and
      .components.email.ok == true and .components.runner.ok == true
    ' <<<"$status_json" >/dev/null 2>&1 &&
    jq -e '
      .audit.checkout_enabled == false and .audit.report_version == "2.0"
    ' <<<"$capabilities_json" >/dev/null 2>&1; then
    deployment_started=false
    trap - EXIT INT TERM
    printf 'Checkout-closed Audit v2 deployment verified at %s.\n' "$reviewed_sha"
    printf '%s\n' "$snapshot_output"
    exit 0
  fi
  sleep 1
done

die "loopback deployment gates did not pass within 60 seconds"
