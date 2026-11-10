# ಇತಿಹಾಸ (Itihāsa) — handoff for agents

Browsable Sanskrit epics: Vālmīki Rāmāyaṇa (site root) and Mahābhārata (`/mbh/`), with Kannada / Devanāgarī / IAST scripts, two editions of each, word-by-word analysis, a built-in dictionary, and an appendix of metres. Static site, built by Python, no server.
Repo `hms-cap/Ramayana` · live (GitHub Pages) https://hms-cap.github.io/Ramayana/ · version in `site/static/version.js` (now 0.9.0) · owner: Hemanth.

## How it is built and shipped
- `python site/build.py` (Jinja2 + lxml, `requirements.txt`) reads `data/` and writes `dist/` (~600 MB, 100k+ files, ~5,500 chapter pages). `python site/build.py` takes a few minutes.
- CI (`.github/workflows`): unittest → build → deploy to GitHub Pages, ~3–5 min. The deploy step has timed out once on size; `gh run rerun <id> --failed` fixed it.
- `vercel.json` (installs into a venv because the image's Python is externally managed; output `dist/`) is pushed. The Vercel import itself is the owner's to do in the dashboard; size limits on his plan are untested. A Vercel MCP server is available in some sessions.
- Run locally: `python site/build.py && python -m http.server 8765 --directory dist`.
- Tests: `python -m unittest discover -s tests` (42) and Playwright scripts in `tests/e2e/` (`home swipe chant pwa mbh mbh_words dict chandas`; see its README). Run the e2e ones against the local server with `service_workers="block"`.
- **Every release needs** a bump of `site/static/version.js`, a `CHANGELOG.md` entry and a `data/changes.json` entry (a test fails otherwise). Commit trailer: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## Layout
- `data/normalized/{ce,vu}.jsonl` (Rāmāyaṇa) and `data/normalized/mbh/{ce,vu}.jsonl` (Mahābhārata): one record per verse `{uid,k,s,v,lines:[[pāda…]],meter,…}` in IAST. `ce` = critical (Baroda / Pune), `vu` = Traditional (Vulgate / Kumbakonam). **The Traditional text is the default shown**; critical is off by default.
- `data/crosswalk/…` verse alignment between editions (Rāmāyaṇa, and Mahābhārata Pune↔Kumbakonam: 84% of Pune verses match). `data/normalized/mbh/words.jsonl.gz` DCS word analysis (72,711 of 73,821 Pune verses; none for Gītā 6.23–40, 7.173 and ~300 others). `data/lexicon/` glosses.
- `etl/`: one-off pipelines (ingest GRETIL / Wikisource / DCS, `crosswalk.py`, `build_lexicon.py`, `meter.py`, `chandas.py`, `translit.py` with SLP1 pivot, `grammar.py`, `card_art.py` icons, `daily.py`/`mbh_art.py` for home cards, `sync_kosha.sh`). `etl/sources.json` lists every source and licence.
- `site/build.py` (the generator; per-work `WORKS` dict, ram prefix `""`, mbh prefix `mbh/`), `site/templates/` (`base, home, sarga, edition, kanda, about, my, appendix, chandas, metre, _art, _strip`), `site/static/` (`app.js` reader and word panel, `lean.js` builds Mahābhārata text in the browser, `home.js`, `dict.js`, `read.js`, `style.css`, service worker, `version.js`).
- `vendor/kosha/`: copy of the Śabdārtha Kaustubha dictionary app (VedaAlokana, pinned commit, see `SOURCE.txt`); `build_dict()` copies it to `dist/dict/` and patches it. Refresh with `etl/sync_kosha.sh <VedaAlokana clone>`.

## What exists (v0.9.0)
Reader with three scripts + scansion + chant; two editions per work with edition badges and crosswalk links; Mahābhārata lean pages (IAST in data, other scripts built client-side); word by word (Rāmāyaṇa and Mahābhārata) with English (Apte + ~600 overrides, 94% of tokens) and Kannada glosses (503 lemmas, ~47% of tokens); tap a word → dictionary card, Full entry / more senses go to `dict/kosha/` and Back restores the verse, word panel and card; dictionary follows light/dark; daily home cards (random mix) for both works; search; offline PWA; names, chips and headings follow the script choice (`sx()` in `build.py`, `.sx-*` CSS); Pariśiṣṭa chip → `appendix/` → Chandas index (`appendix/chandas/` + a page per metre, 15 metres, counts per kāṇḍa/parva, 8 script-aware examples each, all references for rare metres). Labels use Parva (not "parvan").

## Gotchas
- Rāmāyaṇa and Mahābhārata uids collide (`CE-k-sss-vvv`): Rāmāyaṇa words live in `WORDS`; Mahābhārata words are streamed into `MBH_WORDS` / `MBH_WORD_UIDS`.
- Mahābhārata pages are "lean": do not add per-verse markup to the template without a matching `lean.js` change.
- Prefs live in `localStorage "vr-prefs"` (`script`, `theme` "" = light, `off`, `offMbh`, …); `vr.work` is the last work (never "app"); `sessionStorage "vr.ret"` carries the dictionary return state.
- Installed service workers cache the shell: patch `version.js` when shell files change; the vendored Kosha `version.js` is patched to `…-itihasa.N` for the same reason.
- Do not use `.wbw-list li` selectors broadly (the dictionary card list reuses the markup). Long `sleep` chains are blocked in the sandbox: use `timeout … until` loops.
- The sandbox cannot reach the live site or the Vercel API; test on a local build.

## Known limits and open work
1. **Kannada glosses and Kannada grammar terms are written by Claude and unreviewed** (About page says so). Next: have a Kannada reader review `etl/gloss_kn.json`; then extend to the next ~1,000 frequent words.
2. **Chandas descriptions, gaṇa formulas and names are unchecked** by a Sanskrit-metrics reader. Metre labels come from `meter.identify`: Anuṣṭubh is by 16 syllables per half-verse only (5th–7th syllable rule not checked); ~7,700 Rāmāyaṇa Traditional and ~20k Mahābhārata Traditional verses are "not identified" (mostly one-syllable irregularities). Idea: classify pathyā/vipulā variants, detect Triṣṭubh–Jagatī mixtures.
3. Dictionary: Kosha's first sense is not always the best (e.g. *tapas*); text licence "not stated, shown on the owner's decision"; Kosha keeps its own teal palette, only light/dark is shared. Possible: choose the sense by context/lemma POS.
4. No word analysis for the Gītā and Droṇa 173; no Kannada for ~half of tokens.
5. Mahābhārata Pune text: permission from BORI not checked. Licences are in `etl/sources.json` and the About page.
6. Possible appendix sections beyond Chandas (alaṅkāra, glossary, name index), Back behaviour that skips in-dictionary steps, the Vercel deployment (size limits unknown).
