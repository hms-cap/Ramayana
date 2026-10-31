# ವಾಲ್ಮೀಕಿ ರಾಮಾಯಣ — Vālmīki Rāmāyaṇa reader

A static, browsable edition of the Vālmīki Rāmāyaṇa in Sanskrit, readable in
Kannada script, Devanāgarī and IAST, with cross-script search.

## What's in it

- **Baroda Critical Edition**: 7 kāṇḍas, 606 sargas, 18,761 verses, from GRETIL.
- One page per sarga; each verse pre-rendered in Kannada script, Devanāgarī and IAST.
- Script modes: Kannada, Devanāgarī, IAST, Kannada + Devanāgarī side by side, or all three.
- Optional homorganic nasals (ಪುಙ್ಗವ instead of ಪುಂಗವ) for pārāyaṇa-style printing.
- Metre identification and laghu/guru scansion for every verse.
- Search in any script or plain English letters (ಮಾರೀಚ, मारीच, mārīca, maricha all match).
- Per-verse permalinks and copyable citations with GRETIL identifiers.
- No server, no build-time network access: the site is plain HTML, CSS and a little JavaScript.

## Layout

```
etl/            source ingestion, transliteration, metre (Python)
  translit.py   IAST / Devanāgarī / Kannada <-> SLP1, search keys
  meter.py      laghu/guru scansion and metre names
  ingest_gretil.py
  sources.json  pinned upstream commits and licences
data/           generated, normalized text (see data/README.md)
site/           static site generator (Jinja2), templates and assets
  static/translit.js   browser mirror of translit.py (kept identical by tests)
tests/
```

## Build and run locally

```sh
pip install -r requirements.txt
python -m unittest discover -s tests     # includes a Python/JS parity test (needs node)
python site/build.py                      # writes dist/
python -m http.server -d dist 8000
```

To regenerate the normalized text from upstream:

```sh
etl/fetch_sources.sh
python etl/ingest_gretil.py sources/gretil/gretil.sub.uni-goettingen.de/gretil/corpustei/sa_rAmAyaNa.xml
```

## Deployment

`.github/workflows/pages.yml` runs the tests, builds the site and publishes it
to GitHub Pages on every push to `main`. In the repository settings, set
Pages → Source to **GitHub Actions**.

## Licences

- Code: MIT (see `LICENSE`).
- Critical Edition text: CC BY-NC-SA 4.0 (GRETIL). The site as a whole is
  therefore non-commercial.
- Fonts: Tiro Kannada, Tiro Devanagari Sanskrit, Alegreya, Alegreya Sans —
  SIL Open Font License, subset and self-hosted.

## Roadmap

1. ~~Critical Edition reader with script modes, search, citations~~ (done)
2. Traditional Vulgate as a second edition, verse cross-walk to the CE, recension badges
3. Word-by-word Kannada meanings (DCS + Shabdārthakaustubha), pending licence checks
4. Aligned Kannada prose translation with per-verse provenance
