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

# Word-by-word analysis: Digital Corpus of Sanskrit (Rāmāyaṇa file)
if [ ! -d sources/dcs ]; then
  git clone --filter=blob:none --no-checkout https://github.com/ambuda-org/dcs.git sources/dcs
fi
git -C sources/dcs sparse-checkout set --no-cone "/$(pin dcs file)" "/$(pin dcs_mbh file)"
git -C sources/dcs checkout -q "$(pin dcs commit)"
echo "DCS source: sources/dcs/$(pin dcs file)  ->  python etl/ingest_dcs.py <that file>"
echo "DCS Mahabharata: sources/dcs/$(pin dcs_mbh file)  ->  python etl/ingest_dcs.py <that file> --work mbh"

# Apte dictionary (Cologne digital edition, via indic-dict)
if [ ! -d sources/apte ]; then
  git clone --filter=blob:none --no-checkout https://github.com/indic-dict/stardict-sanskrit.git sources/apte
fi
git -C sources/apte sparse-checkout set --no-cone "/$(pin apte file)"
git -C sources/apte checkout -q "$(pin apte commit)"
echo "Apte source: sources/apte/$(pin apte file)  ->  python etl/build_lexicon.py <that file>"

# Mahābhārata: Pune critical text (GRETIL, same mirror) and the Kumbakonam text (SARIT)
git -C sources/gretil sparse-checkout add --no-cone "/gretil.sub.uni-goettingen.de/gretil/1_sanskr/2_epic/mbh/"
git -C sources/gretil checkout -q "$(pin mbh_ce commit)" 2>/dev/null || true
echo "Pune text: sources/gretil/gretil.sub.uni-goettingen.de/gretil/1_sanskr/2_epic/mbh/  ->  python etl/ingest_mbh.py ce <that dir>"
if [ ! -d sources/sarit ]; then
  git clone --filter=blob:none --no-checkout https://github.com/sarit/SARIT-corpus.git sources/sarit
fi
git -C sources/sarit sparse-checkout set --no-cone "/mahabharata-devanagari.xml"
git -C sources/sarit checkout -q "$(pin mbh_vu commit)"
echo "Kumbakonam text: sources/sarit/mahabharata-devanagari.xml  ->  python etl/ingest_mbh.py vu <that file>"
