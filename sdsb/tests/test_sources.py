import pytest

from sources import SOURCES, VALID_TYPES, get_source


def test_slugs_are_unique():
    slugs = [s["slug"] for s in SOURCES]
    assert len(slugs) == len(set(slugs))


def test_every_source_has_required_keys_and_valid_shape():
    for s in SOURCES:
        assert set(s) >= {"slug", "name", "type", "base"}
        assert s["type"] in VALID_TYPES
        assert s["base"].startswith("https://")
        assert not s["base"].endswith("/")


def test_expected_v1_sources_present():
    by_slug = {s["slug"]: s for s in SOURCES}
    assert by_slug["sandiegoseed"]["type"] == "woocommerce"
    assert {"marysheirloom", "seedsnow", "plantgoodseed"} <= set(by_slug)
    assert all(by_slug[s]["type"] == "shopify"
               for s in ("marysheirloom", "seedsnow", "plantgoodseed"))


def test_get_source_roundtrip_and_unknown():
    assert get_source("seedsnow")["name"] == "SeedsNow"
    with pytest.raises(KeyError):
        get_source("nope")
