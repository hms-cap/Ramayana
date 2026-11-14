#!/usr/bin/env bash
# Rebuild site/static/fonts/*.woff from Google Fonts (OFL): sparse shallow clone, pin extra axes, limit wght, subset.
# Usage: etl/make_fonts.sh [workdir]   (default: a temp dir). Needs git + fontTools (pyftsubset); brotli not needed (woff, not woff2).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/site/static/fonts"
WORK="${1:-$(mktemp -d)}"
mkdir -p "$WORK" "$OUT"
if [ ! -d "$WORK/gfonts/ofl" ]; then
  git clone --depth 1 --filter=blob:none --sparse https://github.com/google/fonts "$WORK/gfonts"
  git -C "$WORK/gfonts" sparse-checkout set ofl/notoserifkannada ofl/notosanskannada ofl/notoserifdevanagari ofl/cormorantgaramond ofl/plusjakartasans
fi
G="$WORK/gfonts/ofl"
KN="U+0C80-0CFF,U+0964-0965,U+200C-200D,U+25CC,U+0020-007E,U+00A0,U+2010-2027"
DV="U+0900-097F,U+A8E0-A8FF,U+1CD0-1CFF,U+200C-200D,U+25CC,U+0020-007E,U+00A0,U+2010-2027"
LT="U+0000-024F,U+1E00-1EFF,U+0300-036F,U+2000-206F,U+20B9,U+2190-21FF"

# make <src ttf> <out name> <unicodes> <instancer axes...>
make() {
  local src="$1" name="$2" uni="$3"; shift 3
  local tmp="$WORK/$name.ttf"
  python3 -I -m fontTools.varLib.instancer "$src" "$@" -o "$tmp" --quiet
  python3 -I -m fontTools.subset "$tmp" --unicodes="$uni" --layout-features='*' --flavor=woff \
      --no-hinting --desubroutinize --output-file="$OUT/$name.woff"
}
make "$G/notoserifkannada/NotoSerifKannada[wght].ttf"        NotoSerifKannada      "$KN" wght=400:700
make "$G/notosanskannada/NotoSansKannada[wdth,wght].ttf"     NotoSansKannada       "$KN" wdth=100 wght=400:700
make "$G/notoserifdevanagari/NotoSerifDevanagari[wdth,wght].ttf" NotoSerifDevanagari "$DV" wdth=100 wght=400:700
make "$G/cormorantgaramond/CormorantGaramond[wght].ttf"      CormorantGaramond     "$LT" wght=400:700
make "$G/cormorantgaramond/CormorantGaramond-Italic[wght].ttf" CormorantGaramond-Italic "$LT" wght=400:700
make "$G/plusjakartasans/PlusJakartaSans[wght].ttf"          PlusJakartaSans       "$LT" wght=400:700
for d in notoserifkannada:NotoSerifKannada notosanskannada:NotoSansKannada notoserifdevanagari:NotoSerifDevanagari cormorantgaramond:CormorantGaramond plusjakartasans:PlusJakartaSans; do
  cp "$G/${d%%:*}/OFL.txt" "$OUT/OFL-${d##*:}.txt"
done
ls -l "$OUT"
