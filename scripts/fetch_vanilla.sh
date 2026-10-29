#!/bin/bash
# Extract vanilla 1.20.1 textures/models (input for build.py).
# Uses a local client jar if given, otherwise downloads it from Mojang.
set -e
cd "$(dirname "$0")/.."
JAR="${1:-}"
if [ -z "$JAR" ]; then
  JAR=/tmp/mc-1.20.1-client.jar
  if [ ! -f "$JAR" ]; then
    URL=$(curl -s https://piston-meta.mojang.com/mc/game/version_manifest_v2.json \
      | python3 -c "import json,sys;print([v['url'] for v in json.load(sys.stdin)['versions'] if v['id']=='1.20.1'][0])")
    CLIENT=$(curl -s "$URL" | python3 -c "import json,sys;print(json.load(sys.stdin)['downloads']['client']['url'])")
    curl -sL -o "$JAR" "$CLIENT"
  fi
fi
rm -rf vanilla && mkdir -p vanilla
unzip -oq "$JAR" 'assets/minecraft/textures/*' 'assets/minecraft/models/*' 'assets/minecraft/blockstates/*' -d vanilla
echo "vanilla assets extracted from $JAR"
