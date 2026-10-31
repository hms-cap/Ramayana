#!/usr/bin/env bash
# Fetch the pinned upstream sources into ./sources (git-ignored).
# Only needed to regenerate data/normalized/; the site builds without it.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p sources

pin() { python3 -c "import json,sys;print(json.load(open('etl/sources.json'))[sys.argv[1]][sys.argv[2]])" "$1" "$2"; }

# GRETIL mirror: sparse checkout of the Rāmāyaṇa TEI file only
if [ ! -d sources/gretil ]; then
  git clone --filter=blob:none --no-checkout https://github.com/INDOLOGY/GRETIL-mirror.git sources/gretil
fi
git -C sources/gretil sparse-checkout set --no-cone "/$(pin ce file)"
git -C sources/gretil checkout -q "$(pin ce commit)"
echo "CE source: sources/gretil/$(pin ce file)"

# Vulgate: Ramayana_Book (Sanskrit Wikisource text)
if [ ! -d sources/ramayana_book ]; then
  git clone --filter=blob:none --no-checkout https://github.com/svenkatreddy/Ramayana_Book.git sources/ramayana_book
fi
git -C sources/ramayana_book sparse-checkout set san
git -C sources/ramayana_book checkout -q "$(pin vu commit)"
echo "Vulgate source: sources/ramayana_book/san"
