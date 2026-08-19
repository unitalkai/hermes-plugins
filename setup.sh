#!/usr/bin/env bash
#
# Install the unitalk_design plugin + design-workflow skill for the Iris profile.
# Idempotent: safe to re-run. Run inside a Hermes instance (typically as root).
#
#   ./setup.sh
#
# CRITICAL: Hermes scans the PROFILE's home for plugins, i.e.
#   /opt/data/profiles/<profile>/home/plugins/<name>/
# NOT the invoking user's ~/plugins (when run as root that is /root/plugins,
# which the runtime never scans → "Plugin ... is not installed or bundled" and
# 0 tools load). We resolve the dir from the profile, not from $HOME.
# Override with HERMES_PLUGINS_DIR if your instance differs.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/unitalk_design"

PROFILE="iris"
PROFILE_ROOT="/opt/data/profiles/$PROFILE"

# The plugin dir Hermes actually scans = the PROFILE's home /plugins.
# (Resolved from the profile, so it's correct no matter which user runs this.)
PROFILE_HOME="${IRIS_PROFILE_HOME:-$PROFILE_ROOT/home}"
PLUGINS_DIR="${HERMES_PLUGINS_DIR:-$PROFILE_HOME/plugins}"
PLUGIN_DEST="$PLUGINS_DIR/unitalk_design"

# Skills load per-profile.
SKILL_DEST="$PROFILE_ROOT/skills"

PLUGIN_FILES=(__init__.py plugin.yaml schemas.py tools.py)

echo "==> Installing unitalk_design"
echo "    plugin code -> $PLUGIN_DEST"
echo "    skill       -> $SKILL_DEST"

# 0. Clean up any install in a location the runtime does NOT scan: the invoking
#    user's ~/plugins (e.g. /root/plugins), ~/.hermes/plugins, the profile's own
#    plugins/ dir, and the old hyphen name — all dead ends that hide the code.
hermes -p "$PROFILE" plugins disable unitalk-design >/dev/null 2>&1 || true
rm -rf "$HOME/plugins/unitalk_design" "$HOME/plugins/unitalk-design"
rm -rf "/root/plugins/unitalk_design" "/root/plugins/unitalk-design"
rm -rf "$HOME/.hermes/plugins/unitalk_design" "$HOME/.hermes/plugins/unitalk-design"
rm -rf "$PROFILE_ROOT/plugins/unitalk_design" "$PROFILE_ROOT/plugins/unitalk-design"
rm -rf "$PLUGINS_DIR/unitalk-design"

# 1. Ensure the Iris profile exists.
if ! hermes profile show "$PROFILE" >/dev/null 2>&1; then
  echo "    profile '$PROFILE' not found — creating it"
  hermes profile create "$PROFILE" --no-alias
fi

# 2. Copy the plugin files into the dir Hermes scans (the profile's home).
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

# 5. Enable the plugin for the iris profile. Best-effort: the dashboard install
#    may have already set the enabled flag in config.yaml, and a stale CLI can
#    report "not installed or bundled" even when the code is now in place — the
#    RESTART below is what actually makes the runtime scan + register it.
echo "==> Enabling plugin 'unitalk_design' on profile '$PROFILE'"
hermes -p "$PROFILE" plugins enable unitalk_design || \
  echo "    (enable returned non-zero — flag may already be set; the restart is what matters)"

cat <<EOF

==> Plugin code is now in $PLUGIN_DEST (the dir Hermes scans).
    You MUST restart the gateway for the runtime to scan + register it:
        dashboard → System → Restart Gateway   (or restart the gateway process)

    Also make sure, per user:
    • Profile env: IRIS_WORKSPACE_URL = https://<convex-deployment>.convex.site
                   LITELLM_KEY_ID     = this container's key, whose /key/info
                   metadata.userId == the signed-in user's Clerk userId.
    • Profile model = gpt-5.6-luna (vision + strong tool calls).

    After restart, in a session run '/plugins' — 'unitalk_design' should be
    loaded with the design_draft_* tools.
EOF
