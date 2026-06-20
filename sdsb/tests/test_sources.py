import pytest

from sources import SOURCES, VALID_TYPES, VALID_KINDS, get_source, source_name, source_kind

REQUIRED_KEYS = {"slug", "name", "type", "base", "kind"}
ALLOWED_KEYS = REQUIRED_KEYS | {"collection"}


def test_slugs_are_unique():
    slugs = [s["slug"] for s in SOURCES]
    assert len(slugs) == len(set(slugs))


def test_every_source_has_required_keys_and_valid_shape():
    for s in SOURCES:
        assert REQUIRED_KEYS <= set(s) <= ALLOWED_KEYS
        assert s["type"] in VALID_TYPES
        assert s["kind"] in VALID_KINDS
        assert s["base"].startswith("https://")
        assert not s["base"].endswith("/")
        if "collection" in s:
            assert s["type"] == "shopify"
            assert s["collection"]


def test_existing_three_sources_are_seeds():
    by_slug = {s["slug"]: s for s in SOURCES}
    assert by_slug["sandiegoseed"]["kind"] == "seed"
    assert by_slug["plantgoodseed"]["kind"] == "seed"
    assert by_slug["theodorepayne"]["kind"] == "seed"


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


def test_source_kind_known_and_fallback():
    assert source_kind("sandiegoseed") == "seed"
    assert source_kind("unknown-slug") == "seed"


PLANT_SLUGS = {"ricardos", "plantsexpress", "neelsnursery", "livelyroot",
               "gosucculent", "wallaceranch", "planetdesert"}


def test_seven_plant_sources_present_and_shaped():
    by_slug = {s["slug"]: s for s in SOURCES}
    assert PLANT_SLUGS <= set(by_slug)
    for slug in PLANT_SLUGS:
        s = by_slug[slug]
        assert s["kind"] == "plant"
        assert s["type"] in VALID_TYPES
        assert s["base"].startswith("https://") and not s["base"].endswith("/")
    # the verified host gotcha: Ricardo's must use the store. subdomain
    assert by_slug["ricardos"]["base"] == "https://store.ricardosnursery.com"
    assert by_slug["gosucculent"]["type"] == "woocommerce"
