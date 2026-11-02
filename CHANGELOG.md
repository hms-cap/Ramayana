# Changelog

## 0.4.5 — 2026-11-02
- Word-by-word icon (`.wbw-ic`) under each verse number; `aria-disabled` and dimmed when the verse has no analysis.

## 0.4.4 — 2026-11-02
- Clicking a verse's text opens the word-by-word panel under it (also keyboard: Enter / Space). Traditional verses with a single Baroda counterpart that is a variant, partial or regrouped match show that verse's analysis with a warning note. Verses with no counterpart have no analysis.

## 0.4.3 — 2026-11-02
- Traditional Text (`vu`) is the default edition; Baroda Text (`ce`) is off until enabled in Options (`prefs.off` defaults to `["ce"]`). Editions listed vu first.
- Home: removed the Editions strips and the My list button. Tab bar: Home, Search, My.
- Word by word on matched Traditional verses reads the Baroda sarga's `words.json`. Daily cards are limited to Baroda verses with a one-to-one Traditional match, so Open works with either text.

## 0.4.2 — 2026-11-02
- Light theme is the default; Options → Theme: Light / Dark / Same as device (`data-theme` on `<html>`: `light`, `dark`, `system`).

## 0.4.1 — 2026-11-02
- Editions renamed in the interface: Baroda Text (Critical Edition) and Traditional Text (Vulgate). Options → "Texts to show" switches either off (pref `off`, applied as `data-off` on `<html>`).

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
