#!/usr/bin/env bash
#
# Install the unitalk_voice plugin (Voxo/Lexi audio co-pilot) into a Hermes
# profile. Idempotent. Run inside the instance:
#
#   ./setup.sh          # installs for the 'voxo' profile (default)
#   ./setup.sh <profile>
#
# This script bakes in EVERY lesson we learned provisioning unitalk_design:
#
#  1. The runtime scans the PROFILE's plugins dir:
#        /opt/data/profiles/<profile>/plugins/<name>/
#     NOT ~/.hermes/plugins, NOT $HERMES_HOME/plugins (/opt/data/plugins),
#     NOT the profile *home* (/opt/data/profiles/<profile>/home/plugins).
#  2. `hermes plugins enable` reports "not installed or bundled" even when the
#     code is correct — so we write the enabled flag DIRECTLY into config.yaml.
#  3. Only a gateway RESTART makes the runtime rescan + register — "enabled" in
#     config alone does nothing until then.
#  4. tools.py must import with stdlib only (HERMES_DISABLE_LAZY_INSTALLS=1) — we
#     verify the import.
#  5. We clean up the WRONG locations (never the correct profile/plugins one).
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR"

PLUGIN="unitalk_voice"
PROFILE="${1:-voxo}"
PROFILE_ROOT="/opt/data/profiles/$PROFILE"

# THE correct dir (proven on the working instance): the profile's plugins dir.
PLUGIN_DEST="$PROFILE_ROOT/plugins/$PLUGIN"
SKILL_DEST="$PROFILE_ROOT/skills"
CONFIG="$PROFILE_ROOT/config.yaml"
FILES=(__init__.py plugin.yaml schemas.py tools.py)

echo "==> Installing $PLUGIN for profile '$PROFILE'"
echo "    plugin code -> $PLUGIN_DEST"

# 1. Clean up WRONG locations only (leave the correct profile/plugins dir alone).
rm -rf \
  "$PROFILE_ROOT/home/plugins/$PLUGIN" \
  "/opt/data/plugins/$PLUGIN" \
  "/opt/data/plugins/hermes-plugins/$PLUGIN" \
  "$HOME/plugins/$PLUGIN" \
  "/root/plugins/$PLUGIN" \
  "$HOME/.hermes/plugins/$PLUGIN" 2>/dev/null || true

# 2. Copy the plugin into the profile plugins dir.
mkdir -p "$PLUGIN_DEST"
for f in "${FILES[@]}"; do
  cp "$SRC/$f" "$PLUGIN_DEST/$f"
done

# 3. Copy the managed skill (per-profile).
mkdir -p "$SKILL_DEST"
cp -r "$SRC/skills/voice-workflow" "$SKILL_DEST/"

# 4. Import check (stdlib only — must succeed under the gateway's Python too).
echo "==> Import check"
python3 -c "import sys; sys.path.insert(0, '$PROFILE_ROOT/plugins'); import $PLUGIN; print('    register OK:', hasattr($PLUGIN, 'register'))"

# 5. Enable the plugin DIRECTLY in config.yaml (the CLI enable is unreliable).
echo "==> Enabling $PLUGIN in $CONFIG"
python3 - "$CONFIG" "$PLUGIN" <<'PY'
import sys
cfg, plugin = sys.argv[1], sys.argv[2]
try:
    text = open(cfg).read()
except FileNotFoundError:
    text = ""

if plugin in text:
    print("    already referenced — nothing to do")
    raise SystemExit

lines = text.split("\n")

# No plugins section at all → append a fresh, correctly-indented block.
if not any(l.rstrip() == "plugins:" for l in lines):
    if text and not text.endswith("\n"):
        text += "\n"
    text += "plugins:\n  enabled:\n    - %s\n  disabled:\n" % plugin
    open(cfg, "w").write(text)
    print("    added plugins section + enabled")
    raise SystemExit

# Has a plugins section → insert under the first 'enabled:' that follows it.
out, seen_plugins, done = [], False, False
for l in lines:
    out.append(l)
    if l.rstrip() == "plugins:":
        seen_plugins = True
    elif seen_plugins and not done and l.strip() == "enabled:":
        out.append("    - %s" % plugin)
        done = True
open(cfg, "w").write("\n".join(out))
print("    enabled" if done else "    WARNING: 'enabled:' not found — add '- %s' manually" % plugin)
PY

cat <<EOF

==> Done. NOW RESTART THE GATEWAY so the runtime rescans + registers the plugin.
    Then, in a fresh session, /plugins should show '$PLUGIN' and the voice_* tools.

    Per-user prerequisites on this profile (same as the design profile):
      • env: IRIS_WORKSPACE_URL (Convex .site) + LITELLM_KEY_ID
             (that key's /key/info metadata.userId == the signed-in Clerk id)
      • model: gpt-5.6-luna (so the agent tool_searches the deferred voice_* tools)
EOF
