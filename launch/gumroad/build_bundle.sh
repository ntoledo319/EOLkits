#!/usr/bin/env bash
# Builds the Gumroad "AWS Runtime EOL Migration Toolkit" bundle zip from the
# already-verified in-repo sources. Run from anywhere; paths are resolved
# relative to this script. Output is NOT committed to git (dist/ is
# gitignored) — regenerate with this script whenever the kits change.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DIST_DIR="$SCRIPT_DIR/dist"
STAGE_DIR="$(mktemp -d)"
BUNDLE_NAME="eolkits-migration-toolkit"

trap 'rm -rf "$STAGE_DIR"' EXIT

mkdir -p "$DIST_DIR"
mkdir -p "$STAGE_DIR/$BUNDLE_NAME"

# --- Playbook + attributions (the added value beyond the free GitHub repo) ---
cp "$SCRIPT_DIR/MIGRATION-PLAYBOOK.md" "$STAGE_DIR/$BUNDLE_NAME/"
cp "$SCRIPT_DIR/ATTRIBUTIONS.md" "$STAGE_DIR/$BUNDLE_NAME/"

# --- The three kits (source only — no node_modules/venv/build artifacts) ---
for kit in al2023-gate python-pivot lambda-lifeline; do
  src="$REPO_ROOT/kits/$kit"
  dst="$STAGE_DIR/$BUNDLE_NAME/kits/$kit"
  mkdir -p "$dst"
  cp -R "$src/." "$dst/"
  # Keep test/ dirs in the bundle deliberately — a buyer can run the test suite
  # themselves to verify the "N/N passing" claims made in each kit's README.
  find "$dst" -depth \( \
    -name 'node_modules' -o \
    -name '__pycache__' -o \
    -name '.pytest_cache' -o \
    -name 'dist' -o \
    -name 'build' -o \
    -name '*.egg-info' \
  \) -exec rm -rf {} +
  find "$dst" -name '*.pyc' -delete
done

# --- Top-level bundle README ---
cat > "$STAGE_DIR/$BUNDLE_NAME/README.md" <<'EOF'
# AWS Runtime EOL Migration Toolkit

Start with `MIGRATION-PLAYBOOK.md` — it walks through all three tools and the exact AWS deadlines they address.

## Contents
- `MIGRATION-PLAYBOOK.md` — the guide (start here)
- `ATTRIBUTIONS.md` — license + provenance disclosure
- `kits/al2023-gate/` — Amazon Linux 2 → AL2023 migration CLI (Python)
- `kits/python-pivot/` — Python Lambda runtime migration CLI (Python)
- `kits/lambda-lifeline/` — Node.js Lambda runtime migration CLI (Node)

## Install
Each kit has its own README with install instructions (`pip install -e .` or `npm install` from source — these are
not yet on PyPI/npm, so install from the included source). Each kit also runs entirely offline in fixture mode if
you want to see the output shape before pointing it at a live AWS account.

## Support
Toolkit questions / refunds: hello@toledotechnologies.com
Want the scan run for you, or a real PR opened on your repo? See https://eolkits.com/audit and https://eolkits.com/pack
EOF

# --- Zip it deterministically (no host-specific timestamps/permissions noise) ---
OUT_ZIP="$DIST_DIR/${BUNDLE_NAME}.zip"
rm -f "$OUT_ZIP"
(
  cd "$STAGE_DIR"
  find "$BUNDLE_NAME" -exec touch -t 202601010000 {} +
  zip -X -r -q "$OUT_ZIP" "$BUNDLE_NAME"
)

echo "Built: $OUT_ZIP"
du -h "$OUT_ZIP"
unzip -l "$OUT_ZIP" | tail -5
