# Changelog

## 0.8.0 — 2026-11-05
- Dictionary inside the app: `vendor/kosha/` (copied from hms-cap/VedaAlokana at the commit in `SOURCE.txt` by `etl/sync_kosha.sh`) is built to `dist/dict/` unchanged apart from a back link to Itihāsa (`build_dict` in `site/build.py`). Bottom bar link `a.ext` → `dict/kosha/` (replaces the 0.7.1 external link). The app keeps its own service worker and offline download.
- Word look-up: tapping a word in the word-by-word panel opens a dictionary card under it (`site/static/dict.js`, loaded on sarga pages; reuses the app's `kosha.js` and `search-key.js` by dynamic import on first tap). Matching by sound key; about 83% of word occurrences have an entry.
- `.wbw-list li` rules are now `.wbw-list > li`. Tests: `tests/test_dict.py`, `tests/e2e/dict.py`.

## 0.7.1 — 2026-11-05
- Bottom bar: fifth link "Kosha" (`a.ext`, new tab) to https://hms-cap.github.io/VedaAlokana/web/kosha/ (Śabdārtha Kaustubha). Tab bar grid is 5 columns.

## 0.7.0 — 2026-11-03
- Mahābhārata word by word. `etl/ingest_dcs.py --work mbh` reads the DCS `mahabharatam.txt` into `data/normalized/mbh/words.jsonl.gz` (72,711 of 73,821 Pune verses; the Bhagavadgītā 6.23–40, 7.173 and about 300 scattered verses have none). `site/build.py` writes a `words.json` per Pune adhyāya (115 MB in all); Traditional verses that match a Pune verse use that verse's words. `lean.js` adds the word icon, the details link to the other text and the "Word by word" button; `app.js` takes the words URL relative to the work root (`data-wroot`).
- Kumbakonam-to-Pune cross-walk (`etl/crosswalk.py --work mbh`, `data/crosswalk/mbh/`): 62,574 of 96,415 Traditional verses match a Pune verse exactly. Badges, "also in the Pune text" links and the "only verses in the other text" filter are on for the Mahābhārata.
- Lexicon covers both epics (`etl/build_lexicon.py`): about 600 hand-written English glosses (names and epithets such as arjuna, karṇa, droṇa, whose first Apte sense misleads), 94% of word occurrences. New `etl/gloss_kn.json` / `data/lexicon/gloss_kn.json`: about 500 Kannada meanings, written by Claude and awaiting review; the panel shows them first in the Kannada script, English underneath. `words.json` has a `kn` map.
- Verse-of-the-day cards for the Mahābhārata now come only from Traditional verses that match a Pune verse exactly, and have a words card. `grammar.py`: label for `lun_imp`.
- Tests: `tests/test_mbh.py` (words, labels, glosses, cross-walk), `tests/e2e/mbh_words.py`.

## 0.6.2 — 2026-11-03
- Card art variants (`etl/card_art.py`): two extra motifs per kāṇḍa and parvan (Kalamkari A, Pattachitra B) and two extra chip icons per work. `app.js` picks one of three per card and chip from a per-session seed (`sessionStorage vr.art`); CSS shows the chosen `.kart[data-v]` / `.wico[data-v]`.

## 0.6.1 — 2026-11-03
- App renamed ಇತಿಹಾಸ (Itihāsa). The work chip and "Choose a work" sheet are replaced by two chips (`.wchip`, bow and arrow / Sudarśana chakra) at the top of Home and Read. Icon background blends indigo and maroon.

## 0.6.0 — 2026-11-03
- Mahābhārata as a second work under `/mbh/` (home, read, search, 18 parvans, two texts: Traditional / Kumbakonam from SARIT, CC BY-SA 3.0; Pune critical text from GRETIL, BORI copyright, non-commercial notice). `etl/ingest_mbh.py` writes `data/normalized/mbh/{ce,vu}.jsonl`; `data/editions_mbh.json`; parvan art in `etl/mbh_art.py`.
- `site/build.py` builds per work (`WORKS`). Mahābhārata pages are "lean": IAST only, with `site/static/lean.js` building Kannada, Devanāgarī, verse numbers and details in the browser (keeps the site small). No sarga.json, words or cross-walk for it.
- Work chip and "Choose a work" sheet on Home and Read; per-work place (`vr.last`, `vr.last.mbh`), texts switched on (`off`, `offMbh`) and daily cards; `vr.work` remembers the last-used work and a fresh launch returns to it. About and Saved follow it.

## 0.5.3 — 2026-11-03
- Sarga-level swipe: one finger on a sarga page (ignored on the word-by-word panel, scrollable areas, selections); two fingers in the chant view in either layout. `tests/e2e/swipe.py`.

## 0.5.2 — 2026-11-03
- Verse of the day: palm-leaf manuscript card; actions are icon buttons (`#votd-another`, `-today`, `-save`, `-words`, `-share`, `-open`). The word-by-word icon jumps to the words card and is dimmed when a verse has none.

## 0.5.1 — 2026-11-03
- Home: Continue and Begin merged into one card (`#continue`) with play / resume icons.

## 0.5.0 — 2026-11-03
- App look: greeting Home with Continue card, verse of the day and a kāṇḍa carousel; new Read tab (`/read/`); floating pill tab bar (Home, Read, Search, Saved) below 900 px.
- Kāṇḍa cards are Tanjore-style temple-niche paintings (`site/templates/_art.html`, motifs only); tapping one opens a bottom sheet with Start / Resume and sarga numbers (`site/static/read.js`).
- Script is chosen with one letter (ಅ / अ / A) in the header; reading settings (script, size, theme, texts, metre, nasals) open in a bottom sheet from the sliders button, replacing the Options menu.
- About shows version, release date and Check for updates in a card. New app icon (`site/static/icons/icon.svg`, rendered by `etl/make_icons.py`).

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
