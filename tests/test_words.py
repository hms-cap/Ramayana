import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "etl"))
import grammar  # noqa: E402

W = {}
for l in open(ROOT / "data/normalized/words.jsonl", encoding="utf-8"):
    r = json.loads(l)
    W[r["uid"]] = r["units"]
GLOSS = json.loads((ROOT / "data/lexicon/gloss.json").read_text(encoding="utf-8"))


def test_counts():
    assert len(W) == 18713
    assert sum(len(u) for u in W.values()) == 215824


def test_every_tag_labelled():
    for units in W.values():
        for u in units:
            assert not grammar.check_tags(u["t"]), u


def test_every_ce_uid_is_valid():
    ce = {json.loads(l)["uid"] for l in open(ROOT / "data/normalized/ce.jsonl", encoding="utf-8")}
    assert set(W) <= ce
    assert len(ce - set(W)) == 48


def test_golden_first_verse():
    units = W["CE-1-001-001"]
    assert units[0]["l"] == ["tapas", "svADyAya", "nirata"] or units[0]["f"][0] == "tapaH"
    assert len(units[0]["f"]) == len(units[0]["l"]) >= 2


def test_unit_shape():
    for units in W.values():
        for u in units:
            assert u["f"] and len(u["f"]) == len(u["l"])


def test_overrides_sane():
    ov = json.loads((ROOT / "etl/gloss_overrides.json").read_text(encoding="utf-8"))
    ov.pop("_comment")
    for k, v in ov.items():
        assert 2 <= len(v) <= 100, (k, v)
        assert GLOSS[k] == v
    assert GLOSS["ca"] == "and; also"


def test_gloss_hygiene():
    for k, v in GLOSS.items():
        assert "{" not in v and "}" not in v and "<" not in v, (k, v)
        assert len(v) <= 170, (k, v)
