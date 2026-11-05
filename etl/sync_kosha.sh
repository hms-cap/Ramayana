#!/usr/bin/env bash
# Copy the Śabdārtha Kaustubha dictionary app and its data from a clone of hms-cap/VedaAlokana into vendor/kosha/
# (same layout as its web/ folder, so the app runs unchanged). The build puts it at dist/dict/.
#   git clone --depth 1 https://github.com/hms-cap/VedaAlokana.git sources/vedaalokana
#   bash etl/sync_kosha.sh sources/vedaalokana
set -euo pipefail
src="${1:?path to a VedaAlokana clone}"
dst="$(cd "$(dirname "$0")/.." && pwd)/vendor/kosha"
rm -rf "$dst"; mkdir -p "$dst/data" "$dst/fonts"
for f in styles.css kosha-ui.js kosha.js translit.js search-key.js common.js lipi.js; do cp "$src/web/$f" "$dst/"; done
cp -r "$src/web/kosha" "$dst/kosha"
cp "$src/web/fonts/"* "$dst/fonts/"
cp -r "$src/web/data/kosha" "$dst/data/kosha"
python3 - "$src" "$dst" <<'PY'
import json, sys
src, dst = sys.argv[1:]
off = json.load(open(f"{src}/web/data/offline.json", encoding="utf-8"))
pack = [p for p in off["packs"] if p["id"] == "kosha"]
json.dump({"built": off.get("built"), "packs": pack}, open(f"{dst}/data/offline.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
PY
{ echo "Source: https://github.com/hms-cap/VedaAlokana (web/)"; echo "Commit: $(git -C "$src" rev-parse HEAD)"; echo "Dictionary app version: $(grep -o "version: '[^']*'" "$src/web/kosha/version.js")"; } > "$dst/SOURCE.txt"
du -sh "$dst"; cat "$dst/SOURCE.txt"
