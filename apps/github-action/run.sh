#!/usr/bin/env bash
# Runs EOLkits' path-safe checks from the checked-out action directory.

set -uo pipefail

KIT="${INPUT_KIT:-auto}"
PATH_INPUT="${INPUT_PATH:-.}"
FAIL_ON="${INPUT_FAIL_ON:-any}"

ACTION_DIR="${GITHUB_ACTION_PATH:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
if [[ -d "$ACTION_DIR/kits" ]]; then
  RUPTURE_ROOT="$ACTION_DIR"
elif [[ -d "$ACTION_DIR/../../kits" ]]; then
  RUPTURE_ROOT="$(cd "$ACTION_DIR/../.." && pwd)"
else
  echo "::error::Could not locate EOLkits kits from action path: $ACTION_DIR"
  exit 1
fi

WORKSPACE="${GITHUB_WORKSPACE:-$PWD}"
if [[ "$PATH_INPUT" = /* ]]; then
  TARGET_CANDIDATE="$PATH_INPUT"
else
  TARGET_CANDIDATE="$WORKSPACE/$PATH_INPUT"
fi

WORKSPACE_REAL="$(realpath -e "$WORKSPACE")" || {
  echo "::error::GitHub workspace does not exist: $WORKSPACE"
  exit 1
}
TARGET="$(realpath -e "$TARGET_CANDIDATE")" || {
  echo "::error::Scan path does not exist: $PATH_INPUT"
  exit 1
}
case "$TARGET" in
  "$WORKSPACE_REAL"|"$WORKSPACE_REAL"/*) ;;
  *)
    echo "::error::Scan path must stay inside GITHUB_WORKSPACE: $PATH_INPUT"
    exit 1
    ;;
esac

REPORT_DIR="$WORKSPACE_REAL/tmp/eolkits-action"
mkdir -p "$REPORT_DIR"
RAW_REPORT="$REPORT_DIR/eolkits-action-raw.txt"
REPORT="$REPORT_DIR/eolkits-action-report.md"
: > "$RAW_REPORT"
PYTHON_BIN="python"

HAS_FINDINGS=false
TOOL_ERROR=false
CONFIG_ERROR=false

append_note() {
  printf "\n## %s\n\n%s\n" "$1" "$2" >> "$RAW_REPORT"
}

run_check() {
  local title="$1"
  shift

  printf "\n## %s\n\n\`\`\`text\n" "$title" >> "$RAW_REPORT"
  echo "::group::$title"

  set +e
  "$@" 2>&1 | tee -a "$RAW_REPORT"
  local rc=${PIPESTATUS[0]}
  set -u

  echo "::endgroup::"
  printf "\n\`\`\`\n" >> "$RAW_REPORT"

  if [[ "$rc" -eq 1 ]]; then
    HAS_FINDINGS=true
    echo "::warning::$title reported findings"
  elif [[ "$rc" -ne 0 ]]; then
    TOOL_ERROR=true
    echo "::error::$title failed to execute (exit code $rc)"
  fi
}

install_python_kits() {
  local action_venv="$REPORT_DIR/venv"
  python -m venv "$action_venv" || {
    echo "::error::Failed to create the project-local EOLkits Python environment."
    exit 1
  }
  PYTHON_BIN="$action_venv/bin/python"
  "$PYTHON_BIN" -m pip install --quiet --disable-pip-version-check \
    "$RUPTURE_ROOT/kits/al2023-gate" "$RUPTURE_ROOT/kits/python-pivot" || {
      echo "::error::Failed to install Python EOLkits kits."
      exit 1
    }
}

install_node_kit() {
  if [[ -f "$RUPTURE_ROOT/kits/lambda-lifeline/package-lock.json" ]]; then
    (cd "$RUPTURE_ROOT/kits/lambda-lifeline" && npm ci --omit=dev --quiet) || {
      echo "::error::Failed to install lambda-lifeline dependencies."
      exit 1
    }
  else
    (cd "$RUPTURE_ROOT/kits/lambda-lifeline" && npm install --omit=dev --quiet) || {
      echo "::error::Failed to install lambda-lifeline dependencies."
      exit 1
    }
  fi
}

install_kits() {
  echo "::group::Install EOLkits kits"
  case "$KIT" in
    auto|all) install_python_kits; install_node_kit ;;
    lambda-lifeline) install_node_kit ;;
    python-pivot|al2023-gate) install_python_kits ;;
  esac
  echo "::endgroup::"
}

find_files() {
  local name="$1"
  find "$TARGET" \
    -path "*/.git" -prune -o \
    -path "*/node_modules" -prune -o \
    -path "*/.venv" -prune -o \
    -path "*/venv" -prune -o \
    -path "*/__pycache__" -prune -o \
    -name "$name" -type f -print
}

run_lambda() {
  run_check "lambda-lifeline IaC runtime check" \
    node "$RUPTURE_ROOT/kits/lambda-lifeline/bin/cli.mjs" iac --path "$TARGET" --strict

  run_check "lambda-lifeline Node compatibility check" \
    node "$RUPTURE_ROOT/kits/lambda-lifeline/bin/cli.mjs" codemod --path "$TARGET" --strict

  local audited=false
  while IFS= read -r pkg; do
    audited=true
    run_check "lambda-lifeline native dependency audit: ${pkg#"$WORKSPACE"/}" \
      node "$RUPTURE_ROOT/kits/lambda-lifeline/bin/cli.mjs" audit --path "$(dirname "$pkg")" --strict
  done < <(find_files "package.json" | head -n 20)

  if [[ "$audited" = false ]]; then
    append_note "lambda-lifeline native dependency audit" "No package.json files found under \`$PATH_INPUT\`."
  fi
}

run_python() {
  run_check "python-pivot Python 3.12 compatibility check" \
    "$PYTHON_BIN" -m python_pivot.cli codemod "$TARGET" --strict

  run_check "python-pivot IaC runtime check" \
    "$PYTHON_BIN" -m python_pivot.cli iac "$TARGET" --strict

  local audited=false
  while IFS= read -r depfile; do
    audited=true
    run_check "python-pivot native wheel audit: ${depfile#"$WORKSPACE"/}" \
      "$PYTHON_BIN" -m python_pivot.cli audit "$depfile" --strict
  done < <(
    {
      find_files "requirements.txt"
      find_files "pyproject.toml"
      find_files "Pipfile"
    } | head -n 20
  )

  if [[ "$audited" = false ]]; then
    append_note "python-pivot native wheel audit" "No requirements.txt, pyproject.toml, or Pipfile found under \`$PATH_INPUT\`."
  fi
}

run_al2023() {
  run_check "al2023-gate Ansible AL2023 check" \
    "$PYTHON_BIN" -m al2023_gate.cli ansible "$TARGET" --strict

  run_check "al2023-gate cloud-init AL2023 check" \
    "$PYTHON_BIN" -m al2023_gate.cli cloudinit "$TARGET" --strict
}

case "$KIT" in
  auto|all|lambda-lifeline|python-pivot|al2023-gate) ;;
  *)
    CONFIG_ERROR=true
    append_note "Invalid kit" "Unknown kit \`$KIT\`. Use \`auto\`, \`all\`, \`lambda-lifeline\`, \`al2023-gate\`, or \`python-pivot\`."
    ;;
esac

case "$FAIL_ON" in
  any|none|off|false) ;;
  *)
    CONFIG_ERROR=true
    append_note "Invalid fail-on mode" "Unknown fail-on mode \`$FAIL_ON\`. Use \`any\` or \`none\`."
    ;;
esac

if [[ "$CONFIG_ERROR" = false ]]; then
  install_kits
  case "$KIT" in
    auto|all)
      run_lambda
      run_python
      run_al2023
      ;;
    lambda-lifeline) run_lambda ;;
    python-pivot) run_python ;;
    al2023-gate) run_al2023 ;;
  esac
fi

SHOULD_FAIL=false
if [[ "$CONFIG_ERROR" = true || "$TOOL_ERROR" = true ]]; then
  SHOULD_FAIL=true
elif [[ "$FAIL_ON" = "any" && "$HAS_FINDINGS" = true ]]; then
  SHOULD_FAIL=true
fi

STATUS="passed"
if [[ "$CONFIG_ERROR" = true || "$TOOL_ERROR" = true ]]; then
  STATUS="failed to run"
elif [[ "$SHOULD_FAIL" = true ]]; then
  STATUS="failed"
elif [[ "$HAS_FINDINGS" = true ]]; then
  STATUS="completed with findings"
fi

{
  echo "# EOLkits AWS Deprecation Check"
  echo
  echo "- Kit: \`$KIT\`"
  echo "- Path: \`$PATH_INPUT\`"
  echo "- Fail mode: \`$FAIL_ON\`"
  echo "- Status: \`$STATUS\`"
  echo
  echo "<details>"
  echo "<summary>Scan output</summary>"
  echo
  head -c 50000 "$RAW_REPORT"
  echo
  echo "</details>"
  echo
  echo "[See the one-repository evidence report (\$299)](https://ntoledo319.github.io/EOLkits/audit/?source=github_action&utm_source=github_action&utm_medium=ci&utm_campaign=$KIT)"
  if [[ "$HAS_FINDINGS" = true ]]; then
    echo
    echo "[Would this report be worth \$299? Record qualified public interest](https://github.com/ntoledo319/EOLkits/issues/new?template=audit-interest.yml)"
    echo
    echo "This is not an order or waitlist. GitHub issues are public; do not include repository details, code, secrets, company information, or personal data."
  fi
} > "$REPORT"

if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  cat "$REPORT" >> "$GITHUB_STEP_SUMMARY"
fi

{
  echo "report_path=$REPORT"
  echo "should_fail=$SHOULD_FAIL"
  echo "has_findings=$HAS_FINDINGS"
} >> "${GITHUB_OUTPUT:-/dev/null}"

if [[ "$CONFIG_ERROR" = true || "$TOOL_ERROR" = true ]]; then
  echo "::error::EOLkits could not complete every configured check."
elif [[ "$SHOULD_FAIL" = true ]]; then
  echo "::warning::EOLkits found one or more deprecation risks."
else
  echo "EOLkits check completed."
fi
