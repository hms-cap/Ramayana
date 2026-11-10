# Changelog

## 0.10.2 — 2026-11-10
- Chant view, Page layout (and its PDF/print export): each śloka is a block of its own (`.cv`, `.pv`, hanging indent) instead of verses flowing together in one paragraph, so a verse ending (॥ n ॥) no longer shares a line with the next verse's beginning.

## 0.10.1 — 2026-11-10
- Gītā text review. 228 typing slips in the Kumbakonam (SARIT) Gītā corrected in 186 verses (`data/gita/errata_vu.json`, applied to `data/normalized/mbh/vu.jsonl` by `etl/apply_errata.py`, so the Mahābhārata reader shows the same text): the systematic stray "ka" (`tattvadarśibhiḥka`), n/r (`aśrute`), vakra for vaktra (7×, ch. 11), sañjate for sajjate, dropped and swapped letters, missing half-verse breaks (5.28, 9.25, 9.31), 18.44 garbled. All 700 verses proofread by Sonnet agents, every correction checked by Opus against Pune and the vulgate; six proposals rejected as genuine readings or superseded. Verse details show what was corrected ("Corrected" row).
- Kumbakonam 13.26 was two printed verses keyed as one record: split again (`SPLIT` in `etl/extract_gita.py`), so Traditional ch. 13 runs 1–35 as printed and the Gītā cross-walk is complete (700/700 Pune; 700/701 Traditional, 13.1 has no Pune twin). Traditional verses that scan: 653 → 697.
- Speaker lines inside a verse (1.21, 1.28) are shown before the half-verse they introduce (`speaker_at`, `span.spk`, outside chant view's lines).
- Markup no longer reaches the page, in both epics: GRETIL's `;` between pādas (4,580 Pune Mahābhārata records) becomes a pāda break (`etl/fix_pada_markers.py`, `ingest_mbh.split_padas`); Kumbakonam words split across pādas with `- ` are joined and nukta letters ऩ ऱ read as न र (`ingest_mbh.join_split_words`; Kumbakonam re-ingested from SARIT at the pinned commit, 1,092 records changed, the rest byte-identical). With real pāda breaks 729 more Pune verses get a metre (Upajāti mixed, Puṣpitāgrā, Rucirā, Aparavaktra, Praharṣiṇī, Vasantatilakā); 12 irregular ones lose a label they only had by an arbitrary split. Chandas: Vasantatilakā added (16 metres).
- Kannada script: a nasal before a stop of its own class is shown as anusvāra (ಸಂಗ, ಪಂಚ, ಅಂತ), whatever the source spelling, inside a word only (`anusvara_before_stops` in `translit.py` and `translit.js`); the Homorganic nasals option still shows ಙ್ಗ etc.; Devanāgarī and IAST unchanged.
- Tests: `tests/test_gita.py` (counts, only Sanskrit letters, errata applied and idempotent, speaker placement, markup in both epics), `tests/test_translit.py` (anusvāra rule).

## 0.10.0 — 2026-11-10
- Bhagavadgītā as a third work (`gita/`, chip beside the two epics). `etl/extract_gita.py` takes it out of the Mahābhārata data (Kumbakonam Bhīṣma 25–42, Pune 23–40) into `data/normalized/gita/{vu,ce}.jsonl` (700 records each, uids `BG-VU-02-047`, with `speaker` and `mbh_uid`); `data/crosswalk/gita/` is the Mahābhārata cross-walk translated through `mbh_uid` and repaired (698 of 700 match). `WORKS["gita"]` in `site/build.py` has one unit (`single=True`): pages are `gita/<ed>/1/<adhyāya>/`, refs are adhyāya.verse, `load_recs()` maps `{ch, v}` onto k/s/v. Non-lean pages (all three scripts in the HTML).
- Speaker lines (arjuna uvāca …) are shown above the verse they introduce (Kumbakonam prints them at the end of the previous verse). Kumbakonam's chapter 13 has the extra verse 13.1 and prints 13.25–26 as one record (numbered to 35).
- Gītā Dhyāna: the nine verses as adhyāya 0 (`data/gita/dhyana.json`, readings cross-checked across several published texts, variants recorded). Adhyāya names from `data/gita/chapters.json`; home and Read show 18 adhyāya cards (`etl/gita_art.py`); 365 verse-of-the-day cards from the Traditional text (`build_daily_gita`, no words card yet).
- Links both ways: Mahābhārata Bhīṣma adhyāyas that hold the Gītā link to it; each Gītā verse's details link to its place in the Mahābhārata.
- Data fix: GRETIL's additions to Pune 6.23.1 (the Gītā nyāsa and dhyāna preface) and 6.40.78 (a 246-line appended dialogue) were not Mahābhārata text; `etl/fix_mbh_gita_preface.py` removes them (saved to `data/gita/`) and the four affected Mahābhārata cross-walk entries are now matches.
- JS: per-work keys generalised (`offGita`, `vr.last.gita`, save ids, share card title from `data-work-kn` / `data-site`). Chandas still counts the two epics only (`EPICS`).
- Tests: `tests/test_gita.py`, `tests/e2e/gita.py`.

## 0.9.0 — 2026-11-06
- Pariśiṣṭa (appendix): a third chip beside the two works, opening `appendix/`. First section: Chandas, an index of the 15 metres found in the two epics (`etl/chandas.py` counts the stored metre labels of all four texts; `build_appendix` in `site/build.py` writes `appendix/chandas/` and one page per metre). Each metre page has its pāda pattern, counts per kāṇḍa or parva in both editions, eight verses to read (script-aware, with scansion, linked into the reader) and, for rare metres, every verse reference.
- "Parvan" is now "Parva" everywhere it is shown (the Sanskrit word is parva; parvan is the stem).

## 0.8.2 — 2026-11-06
- Work chips, kāṇḍa/parvan cards and sheet title, headings, breadcrumbs, side rail and strips now follow the script choice (Kannada, Devanāgarī or IAST) instead of always showing Kannada: `sx()` in `build.py` writes all three, `.sx-*` rules in `style.css` show one.

## 0.8.1 — 2026-11-05
- Back from the dictionary: a card link saves `vr.ret` (page, verse, word) in sessionStorage and adds `?from=` to the dictionary URL; `dict.js` reopens the word panel and card when the page is reached by Back or from the dictionary. The dictionary's pill reads "← 1.1.1" and returns there.
- The dictionary follows Itihāsa's theme (`vr-prefs.theme`, also live through the `storage` event); its own Theme control is replaced by a note. `build_dict` patches `index.html`, `app.js` and the version (`1.1.4-itihasa.2`, so installed copies fetch the patched shell).

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
