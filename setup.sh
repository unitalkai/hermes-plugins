#!/usr/bin/env bash
#
# Convenience wrapper — installs BOTH Unitalk Hermes plugins by delegating to the
# per-plugin scripts (the single source of truth):
#
#     unitalk_design/setup.sh <profile>   -> Iris / Lumi design & motion co-pilot
#     unitalk_voice/setup.sh  <profile>   -> Voxo / Lexi audio co-pilot
#
# Those scripts bake in every provisioning lesson (correct dir, ownership,
# config enable, import check). Do NOT reimplement install logic here — this
# file only loops over profiles. Run inside a Hermes instance:
#
#     ./setup.sh                      # design -> iris,lumi ; voice -> voxo
#     DESIGN_PROFILES="iris" ./setup.sh   # override which profiles get design
#     VOICE_PROFILES="" ./setup.sh        # skip voice entirely
#
# After it finishes, RESTART THE GATEWAY so the runtime rescans + registers.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The unitalk_design plugin powers both the image (iris) and video (lumi)
# profiles; unitalk_voice powers the audio profile (voxo). Override via env.
DESIGN_PROFILES="${DESIGN_PROFILES:-iris lumi}"
VOICE_PROFILES="${VOICE_PROFILES:-voxo}"

for p in $DESIGN_PROFILES; do
  echo "######## unitalk_design -> $p ########"
  "$SCRIPT_DIR/unitalk_design/setup.sh" "$p"
done

for p in $VOICE_PROFILES; do
  echo "######## unitalk_voice -> $p ########"
  "$SCRIPT_DIR/unitalk_voice/setup.sh" "$p"
done

cat <<'EOF'

######## All plugins installed ########
NOW RESTART THE GATEWAY (dashboard -> System -> Restart Gateway, or restart the
gateway process) so the runtime rescans + registers the plugins. Then verify:

    hermes -p iris plugins list      # unitalk_design -> enabled | user
    hermes -p voxo plugins list      # unitalk_voice  -> enabled | user
EOF
