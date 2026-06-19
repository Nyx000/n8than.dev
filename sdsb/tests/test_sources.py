import pytest

from sources import SOURCES, VALID_TYPES, get_source, source_name

REQUIRED_KEYS = {"slug", "name", "type", "base"}
ALLOWED_KEYS = REQUIRED_KEYS | {"collection"}


def test_slugs_are_unique():
    slugs = [s["slug"] for s in SOURCES]
    assert len(slugs) == len(set(slugs))


def test_every_source_has_required_keys_and_valid_shape():
    for s in SOURCES:
        assert REQUIRED_KEYS <= set(s) <= ALLOWED_KEYS
        assert s["type"] in VALID_TYPES
        assert s["base"].startswith("https://")
        assert not s["base"].endswith("/")
        if "collection" in s:
            assert s["type"] == "shopify"
            assert s["collection"]  # non-empty handle


def test_curated_socal_sources():
    by_slug = {s["slug"]: s for s in SOURCES}
    # kept SoCal growers
    assert by_slug["sandiegoseed"]["type"] == "woocommerce"
    assert by_slug["plantgoodseed"]["type"] == "shopify"
    # added: Theodore Payne, scoped to its seeds collection
    assert by_slug["theodorepayne"]["type"] == "shopify"
    assert by_slug["theodorepayne"]["collection"] == "seeds-1"
    # cut non-SoCal / national sources
    assert "marysheirloom" not in by_slug
    assert "seedsnow" not in by_slug


def test_get_source_roundtrip_and_unknown():
    assert get_source("theodorepayne")["name"] == "Theodore Payne Foundation"
    with pytest.raises(KeyError):
        get_source("nope")


def test_source_name_known_and_fallback():
    assert source_name("plantgoodseed") == "The Plant Good Seed Company"
    assert source_name("unknown-slug") == "unknown-slug"
