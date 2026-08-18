#!/usr/bin/env bash
#
# Install the unitalk_design plugin + design-workflow skill for the Iris profile.
# Idempotent: safe to re-run. Run inside a Hermes instance.
#
#   ./setup.sh
#
# The Hermes runtime discovers user plugins from ~/plugins/ (= $HOME/plugins).
# NOT ~/.hermes/plugins, NOT the per-profile plugins/ dir — putting the code
# there means the tools never load (we lost hours to this). Override with
# HERMES_PLUGINS_DIR if your instance differs.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/unitalk_design"

PROFILE="iris"
PROFILE_ROOT="/opt/data/profiles/$PROFILE"

# The dir Hermes actually scans for user plugin code.
PLUGINS_DIR="${HERMES_PLUGINS_DIR:-$HOME/plugins}"
PLUGIN_DEST="$PLUGINS_DIR/unitalk_design"

# Skills load per-profile.
SKILL_DEST="$PROFILE_ROOT/skills"

PLUGIN_FILES=(__init__.py plugin.yaml schemas.py tools.py)

echo "==> Installing unitalk_design"
echo "    plugin code -> $PLUGIN_DEST"
echo "    skill       -> $SKILL_DEST"

# 0. Clean up any install in a location the runtime does NOT scan (old hyphen
#    name, ~/.hermes/plugins, the per-profile plugins/ dir).
hermes -p "$PROFILE" plugins disable unitalk-design >/dev/null 2>&1 || true
rm -rf "$PROFILE_ROOT/plugins/unitalk-design" "$PROFILE_ROOT/plugins/unitalk_design"
rm -rf "$HOME/.hermes/plugins/unitalk-design" "$HOME/.hermes/plugins/unitalk_design"
rm -rf "$PLUGINS_DIR/unitalk-design"

# 1. Ensure the Iris profile exists.
if ! hermes profile show "$PROFILE" >/dev/null 2>&1; then
  echo "    profile '$PROFILE' not found — creating it"
  hermes profile create "$PROFILE" --no-alias
fi

# 2. Copy the plugin files into the plugins dir Hermes scans.
mkdir -p "$PLUGIN_DEST"
for f in "${PLUGIN_FILES[@]}"; do
  cp "$SRC/$f" "$PLUGIN_DEST/$f"
done

# 3. Copy the managed skill (per-profile).
mkdir -p "$SKILL_DEST"
cp -r "$SRC/skills/design-workflow" "$SKILL_DEST/"

# 4. Sanity check: the plugin must import cleanly (stdlib only — no `requests`,
#    which is absent when HERMES_DISABLE_LAZY_INSTALLS=1 and crashes register()).
echo "==> Import check"
python3 -c "import sys; sys.path.insert(0, '$PLUGINS_DIR'); import unitalk_design; print('    register OK:', hasattr(unitalk_design, 'register'))"

# 5. Enable the plugin for the iris profile.
echo "==> Enabling plugin 'unitalk_design' on profile '$PROFILE'"
hermes -p "$PROFILE" plugins enable unitalk_design

cat <<EOF

==> Plugin installed. Before it works for THIS user, make sure:
    • Profile env has:
        IRIS_WORKSPACE_URL = https://<convex-deployment>.convex.site
        LITELLM_KEY_ID     = this container's LiteLLM key
      and that key's /key/info metadata.userId == the user's Clerk userId
      (required so the draft is owned by the signed-in user, else the panel
      shows nothing).
    • Profile model is a vision-capable one, e.g. gpt-5.6-luna (deepseek-v4-flash
      has no vision and breaks image critique + tool use).
    • Then RESTART the gateway. In a session run '/plugins' — 'unitalk_design'
      should be loaded and design_draft_* available.
EOF
