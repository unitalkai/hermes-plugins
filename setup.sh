#!/usr/bin/env bash
#
# Install the unitalk_design plugin + design-workflow skill into the Iris
# Hermes profile. Idempotent: safe to re-run. Run inside a Hermes instance
# (Salif runs this after the repo is cloned into the shared volume).
#
#   ./setup.sh
#
# NOTE: the plugin dir/name uses an underscore (unitalk_design), not a hyphen —
# the directory name must be a valid Python module name for Hermes to import it.
#
set -euo pipefail

# Resolve the repo root so the script works from any cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/unitalk_design"

PROFILE="iris"
PROFILE_ROOT="/opt/data/profiles/$PROFILE"
PLUGIN_DEST="$PROFILE_ROOT/plugins/unitalk_design"
SKILL_DEST="$PROFILE_ROOT/skills"

# Only the plugin runtime files — not README, config.example.yaml, or skills/.
PLUGIN_FILES=(__init__.py plugin.yaml schemas.py tools.py)

echo "==> Installing unitalk_design into the '$PROFILE' profile"

# 0. Remove the old hyphenated plugin, which Hermes couldn't import.
echo "==> Removing the old 'unitalk-design' (hyphen) plugin if present"
hermes -p "$PROFILE" plugins disable unitalk-design >/dev/null 2>&1 || true
rm -rf "$PROFILE_ROOT/plugins/unitalk-design"

# 1. Ensure the Iris profile exists.
if hermes profile show "$PROFILE" >/dev/null 2>&1; then
  echo "    profile '$PROFILE' already exists"
else
  echo "    profile '$PROFILE' not found — creating it"
  hermes profile create "$PROFILE" --no-alias
fi

# 2. Copy only the plugin files.
echo "==> Copying plugin files to $PLUGIN_DEST"
mkdir -p "$PLUGIN_DEST"
for f in "${PLUGIN_FILES[@]}"; do
  cp "$SRC/$f" "$PLUGIN_DEST/$f"
done

# 3. Copy the managed skill.
echo "==> Copying design-workflow skill to $SKILL_DEST"
mkdir -p "$SKILL_DEST"
cp -r "$SRC/skills/design-workflow" "$SKILL_DEST/"

# 4. Enable the plugin via the CLI — writes plugins.enabled into iris's own
#    config.yaml, preserving the rest of the file (better than overwriting it).
echo "==> Enabling plugin 'unitalk_design' on profile '$PROFILE'"
hermes -p "$PROFILE" plugins enable unitalk_design

echo "==> Done. 'unitalk_design' is installed and enabled on the '$PROFILE' profile."
echo "    Restart the gateway, then check the startup log for:"
echo "      'unitalk_design' registered tools: design_draft_get, design_draft_upsert, design_generation_get"
