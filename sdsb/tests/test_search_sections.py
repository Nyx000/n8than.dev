from search_sections import partition_sections


def test_partition_sections_caps_and_splits_by_kind():
    rows = [
        {"kind": "plant", "name": "p1"}, {"kind": "seed", "name": "s1"},
        {"kind": "plant", "name": "p2"}, {"kind": "plant", "name": "p3"},
        {"kind": "seed", "name": "s2"},
    ]
    out = partition_sections(rows, k=2)
    assert [r["name"] for r in out["plant"]] == ["p1", "p2"]   # order preserved, capped at 2
    assert [r["name"] for r in out["seed"]] == ["s1", "s2"]


def test_partition_sections_ignores_unknown_or_missing_kind():
    rows = [{"kind": "plant", "name": "p1"}, {"kind": None, "name": "x"}, {"name": "y"}]
    out = partition_sections(rows, k=5)
    assert [r["name"] for r in out["plant"]] == ["p1"]
    assert out["seed"] == []
