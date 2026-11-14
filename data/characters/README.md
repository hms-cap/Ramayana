# Characters (Pariśiṣṭa → Characters)

`seed_ram.json` and `seed_mbh.json` fix the list: ids, names, groups. The character data lives in
`ram.json` and `mbh_*.json` (any file named `<work>*.json` other than the seed), each
`{"work": "...", "characters": [ ... ]}`. `python etl/check_characters.py` must pass.

One character:

```json
{
  "id": "vibhishana",                       // from the seed, ASCII
  "name": "Vibhīṣaṇa",                      // IAST, as in the seed
  "group": "rakshasa",                      // from the seed
  "gender": "m",                            // m | f | n (groups such as the Aśvins: "n")
  "rank": 1,                                // 1 main, 2 important, 3 minor (sets order and size in graphs)
  "epithets": ["Rāvaṇānuja"],               // other names used in the text, IAST; only ones that refer to this person
  "match": [],                              // optional extra stems used only for checking citations
  "role_en": "Rāvaṇa's younger brother, who leaves Laṅkā and joins Rāma",   // one line, under 90 characters
  "role_kn": "…",                           // the same in plain modern Kannada
  "desc_en": "…",                           // 3–5 sentences, plain English, no spoilers kept back
  "desc_kn": "…",                           // the same in plain modern Kannada
  "relations": [
    {"type": "sibling", "to": "ravana"},    // type: parent | spouse | sibling | teacher | ally | enemy | friend | serves | killed_by | other
    {"type": "ally", "to": "rama", "ref": "6.12.1", "ed": "vu"}            // optional verse for the relation
  ],
  "moments": [                              // 2–6 key moments, in story order
    {"en": "Advises Rāvaṇa to return Sītā", "kn": "…", "ref": "6.9.1", "ed": "vu", "with": ["ravana"]}
  ]
}
```

Rules
- Relations are stored once, from the person it is about: `parent` points to the parent (the child gets
  it from the parent's side automatically), `teacher` points to the teacher, `serves` points to the master,
  `killed_by` points to the killer. `spouse`, `sibling`, `ally`, `enemy`, `friend` are symmetric: store
  them on one of the two only. Full siblings are derived from shared parents, so `sibling` is only for
  people whose shared parent is not in the list (e.g. Vālin and Sugrīva). `other` needs `note_en`/`note_kn`.
- Only list relations to ids in the seed.
- `ref` is `kāṇḍa/parvan.sarga/adhyāya.verse` in edition `ed` ("vu" Traditional, the text shown by
  default; "ce" critical). The cited verse must name the person (or someone in `with`); if it does not,
  pick a verse that does, or add `"check": "skip", "why": "…"`.
- Kannada: plain modern Kannada, names in their usual Kannada spelling (ರಾಮ, ಸೀತೆ, ಹನುಮಂತ). Written by
  Claude and marked unreviewed on the site.
