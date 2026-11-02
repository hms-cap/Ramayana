# Changelog

## 0.4.0 — 2026-11-02
- Chant view (`site/static/chant.js`): book page and one-verse-at-a-time layouts, size / script / layout controls, swipes and keys, wake lock, overlay history entry; ✕ returns to where chanting started, system Back lands on the last work. Built from the verses in the page, so it needs no extra data.
- Print and PDF (`site/static/pdf.js`): library-free PDF made from page images; phones share the file.
- Home redesign: 365 automatic verse-of-the-day cards (`etl/daily.py`, prime-stride daily pick), Continue reading, kāṇḍa tiles with sarga chips, My list, share picture.
- PWA: `version.js`, versioned shell cache and unversioned data cache (`site/sw.js`), reload prompt, Check for updates, offline download packs (About).
- Chrome: bottom tab bar (< 900 px), side rail (≥ 900 px), Back button.

## 0.3.0 — 2026-10-31
Word-by-word analysis (DCS) with dictionary senses.

## 0.2.0 — 2026-10-30
Vulgate edition and cross-walk.

## 0.1.0 — 2026-10-29
Critical Edition reader.

### Release procedure
1. Make the change; run `python -m unittest discover -s tests`.
2. Bump `site/static/version.js`, add the entry to `data/changes.json` (plain language) and here.
3. Any new file in `site/static/` is added to the service worker's shell list automatically by `site/build.py`.
4. Push to `main`; Pages deploys; open clients show the reload prompt.
