#!/bin/bash
# Download all TruTopia mods (from the .mrpack index) and extract their textures to mods/ex.
set -e
cd "$(dirname "$0")/.."
mkdir -p dl mods/jars
if [ ! -f dl/x/modrinth.index.json ]; then
  URL=$(curl -s "https://api.modrinth.com/v2/project/yzxnGSON/version" | python3 -c "import json,sys;print(json.load(sys.stdin)[0]['files'][0]['url'])")
  curl -sL -o dl/pack.mrpack "$URL" && rm -rf dl/x && mkdir -p dl/x && unzip -oq dl/pack.mrpack -d dl/x
fi
python3 -c "
import json
d=json.load(open('dl/x/modrinth.index.json'))
for f in d['files']:
    p=f['path']
    if p.startswith('mods/') and p.endswith('.jar'): print(f['downloads'][0], p[5:])
" | xargs -P 6 -L 1 sh -c '[ -f "mods/jars/$1" ] || curl -sfL -o "mods/jars/$1" "$0"'
cp dl/x/overrides/mods/*.jar mods/jars/ 2>/dev/null || true
rm -rf mods/ex && mkdir -p mods/ex
for j in mods/jars/*.jar; do
  unzip -qo "$j" 'assets/*/textures/block/*' 'assets/*/textures/item/*' 'assets/*/textures/models/armor/*' -d mods/ex 2>/dev/null || true
done
rm -rf mods/ex/assets/minecraft
echo "mod textures in mods/ex"
