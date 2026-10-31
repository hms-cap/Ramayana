"""Grammar labels for the DCS morphological tags, in Kannada and English.

Single source of truth: build.py writes this table to dist/data/grammar.json
and the reader's JavaScript looks labels up there, so Python and the browser
can never disagree. tests/test_words.py checks that every tag value found in
the DCS file has a label here.

Kannada terms follow the traditional Sanskrit-grammar vocabulary used in
Karnataka (ಪ್ರಥಮಾ, ದ್ವಿತೀಯಾ ..., ಲಟ್, ಲಙ್ ...). They have not yet been
reviewed by a Kannada grammarian; corrections are welcome as merge requests.
"""
from __future__ import annotations

# part of speech (DCS `pos`), with the participle / verbal-indeclinable sub-kinds
POS = {
    "n": {"kn": "ನಾಮಪದ", "en": "noun or pronoun"},
    "a": {"kn": "ವಿಶೇಷಣ", "en": "adjective"},
    "i": {"kn": "ಅವ್ಯಯ", "en": "indeclinable"},
    "v": {"kn": "ತಿಙಂತ ಕ್ರಿಯಾಪದ", "en": "finite verb"},
    "va": {"kn": "ಕೃದಂತ ವಿಶೇಷಣ", "en": "participle"},
    "vi": {"kn": "ಕೃದವ್ಯಯ", "en": "verbal indeclinable (infinitive or gerund)"},
}
VFORM = {  # DCS `f` on pos=va
    "part": {"kn": "ಕೃದಂತ", "en": "participle"},
    "krtya": {"kn": "ಕೃತ್ಯಪ್ರತ್ಯಯಾಂತ", "en": "gerundive"},
}
GENDER = {
    "m": {"kn": "ಪುಲ್ಲಿಂಗ", "en": "masculine"},
    "f": {"kn": "ಸ್ತ್ರೀಲಿಂಗ", "en": "feminine"},
    "n": {"kn": "ನಪುಂಸಕಲಿಂಗ", "en": "neuter"},
}
CASE = {
    "1": {"kn": "ಪ್ರಥಮಾ", "en": "nominative"},
    "2": {"kn": "ದ್ವಿತೀಯಾ", "en": "accusative"},
    "3": {"kn": "ತೃತೀಯಾ", "en": "instrumental"},
    "4": {"kn": "ಚತುರ್ಥೀ", "en": "dative"},
    "5": {"kn": "ಪಂಚಮೀ", "en": "ablative"},
    "6": {"kn": "ಷಷ್ಠೀ", "en": "genitive"},
    "7": {"kn": "ಸಪ್ತಮೀ", "en": "locative"},
    "8": {"kn": "ಸಂಬೋಧನೆ", "en": "vocative"},
}
NUMBER = {
    "s": {"kn": "ಏಕವಚನ", "en": "singular"},
    "d": {"kn": "ದ್ವಿವಚನ", "en": "dual"},
    "p": {"kn": "ಬಹುವಚನ", "en": "plural"},
}
PERSON = {  # Kannada counts the third person as ಪ್ರಥಮ
    "1": {"kn": "ಉತ್ತಮ ಪುರುಷ", "en": "first person"},
    "2": {"kn": "ಮಧ್ಯಮ ಪುರುಷ", "en": "second person"},
    "3": {"kn": "ಪ್ರಥಮ ಪುರುಷ", "en": "third person"},
}
TENSE = {  # DCS `l`
    "lat": {"kn": "ಲಟ್ (ವರ್ತಮಾನ)", "en": "present"},
    "lan": {"kn": "ಲಙ್ (ಅನದ್ಯತನ ಭೂತ)", "en": "imperfect"},
    "lan_unaug": {"kn": "ಲಙ್ (ಆಗಮರಹಿತ)", "en": "imperfect without augment"},
    "lit": {"kn": "ಲಿಟ್ (ಪರೋಕ್ಷ ಭೂತ)", "en": "perfect"},
    "lot": {"kn": "ಲೋಟ್ (ಆಜ್ಞಾರ್ಥ)", "en": "imperative"},
    "lrt": {"kn": "ಲೃಟ್ (ಭವಿಷ್ಯತ್)", "en": "future"},
    "lrn": {"kn": "ಲೃಙ್ (ಕ್ರಿಯಾತಿಪತ್ತಿ)", "en": "conditional"},
    "lun": {"kn": "ಲುಙ್ (ಸಾಮಾನ್ಯ ಭೂತ)", "en": "aorist"},
    "lun_unaug": {"kn": "ಲುಙ್ (ಆಗಮರಹಿತ)", "en": "aorist without augment"},
    "vidhilin": {"kn": "ವಿಧಿಲಿಙ್ (ವಿಧ್ಯರ್ಥ)", "en": "optative"},
    "ashirlin": {"kn": "ಆಶೀರ್ಲಿಙ್", "en": "benedictive"},
}
COMPOUND = {"kn": "ಸಮಾಸದ ಪೂರ್ವಪದ", "en": "first member of a compound"}

TABLES = {"pos": POS, "f": VFORM, "g": GENDER, "c": CASE, "n": NUMBER, "p": PERSON, "l": TENSE}


def as_json() -> dict:
    out = {k: v for k, v in TABLES.items()}
    out["comp"] = COMPOUND
    return out


def check_tags(tags: dict) -> list[str]:
    """Return a list of 'key=value' pairs that have no label (empty = all covered)."""
    missing = []
    for key, val in tags.items():
        if key in ("comp",) or val == "":
            continue
        if key in TABLES and val not in TABLES[key]:
            missing.append(f"{key}={val}")
        elif key not in TABLES:
            missing.append(f"{key}={val}")
    return missing
