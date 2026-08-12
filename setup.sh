#!/usr/bin/env bash
#
# Install the unitalk_design plugin + design-workflow skill for the Iris profile.
# Idempotent: safe to re-run. Run inside a Hermes instance.
#
#   ./setup.sh
#
# Per the Hermes docs, plugin CODE is loaded only from the global user plugins
# dir (`~/.hermes/plugins/`), NOT from per-profile dirs — so the plugin files go
# there. The per-profile `plugins enable` then gates whether register() runs for
# the iris profile. (Override the plugins dir with HERMES_PLUGINS_DIR if needed.)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/unitalk_design"

PROFILE="iris"
PROFILE_ROOT="/opt/data/profiles/$PROFILE"

# Global user plugins dir — where Hermes actually discovers/loads plugin code.
PLUGINS_DIR="${HERMES_PLUGINS_DIR:-$HOME/.hermes/plugins}"
PLUGIN_DEST="$PLUGINS_DIR/unitalk_design"

# Skills still load per-profile (that part already works).
SKILL_DEST="$PROFILE_ROOT/skills"

PLUGIN_FILES=(__init__.py plugin.yaml schemas.py tools.py)

echo "==> Installing unitalk_design"
echo "    plugin code -> $PLUGIN_DEST   (global plugins dir)"
echo "    skill       -> $SKILL_DEST"

# 0. Clean up any previous installs (old hyphen name + the per-profile location
#    that Hermes never loaded from).
hermes -p "$PROFILE" plugins disable unitalk-design >/dev/null 2>&1 || true
rm -rf "$PROFILE_ROOT/plugins/unitalk-design" "$PROFILE_ROOT/plugins/unitalk_design"
rm -rf "$PLUGINS_DIR/unitalk-design"

# 1. Ensure the Iris profile exists.
if ! hermes profile show "$PROFILE" >/dev/null 2>&1; then
  echo "    profile '$PROFILE' not found — creating it"
  hermes profile create "$PROFILE" --no-alias
fi

# 2. Copy the plugin files into the GLOBAL plugins dir.
mkdir -p "$PLUGIN_DEST"
for f in "${PLUGIN_FILES[@]}"; do
  cp "$SRC/$f" "$PLUGIN_DEST/$f"
done

# 3. Copy the managed skill (per-profile).
mkdir -p "$SKILL_DEST"
cp -r "$SRC/skills/design-workflow" "$SKILL_DEST/"

# 4. Enable the plugin for the iris profile.
echo "==> Enabling plugin 'unitalk_design' on profile '$PROFILE'"
hermes -p "$PROFILE" plugins enable unitalk_design

echo "==> Done. Restart the gateway, then in a session run '/plugins' — you should"
echo "    see 'unitalk_design' as LOADED, and the design_draft_* tools available."
