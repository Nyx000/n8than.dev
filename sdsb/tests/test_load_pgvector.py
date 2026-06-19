from load_pgvector import (
    build_embed_text, content_hash, primary_category, upsert_params, partition_items,
)

REC = {
    "source": "seedsnow", "source_id": 999, "name": "Detroit Dark Red Beet",
    "sku": "BEET-DDR", "type": "Vegetables",
    "categories": ["Vegetables", "Beets"],
    "price": 2.99, "regular_price": 2.99, "sale_price": None,
    "currency_symbol": "$", "on_sale": False, "is_in_stock": True,
    "attributes": [{"name": "Size", "values": ["1g", "5g"]}],
    "variations": ["1g", "5g"],
    "permalink": "https://www.seedsnow.com/products/beet", "image": None,
    "short_description": "Sweet heirloom beet.", "description": "Deep red roots.",
}


def _prepared():
    r = dict(REC)
    r["embed_text"] = build_embed_text(r)
    r["content_hash"] = content_hash(r)
    return r


def test_build_embed_text_includes_name_categories_attributes():
    t = build_embed_text(REC)
    assert "Detroit Dark Red Beet" in t
    assert "Categories: Vegetables, Beets" in t
    assert "Size: 1g, 5g" in t


def test_content_hash_is_text_based_and_stable():
    r = _prepared()
    assert r["content_hash"] == content_hash(r)


def test_primary_category_is_first_or_none():
    assert primary_category(REC) == "Vegetables"
    assert primary_category({"categories": []}) is None


def test_upsert_params_uses_composite_key():
    p = upsert_params(_prepared(), [0.1] * 1024)
    assert p["source"] == "seedsnow" and p["source_id"] == 999
    assert "id" not in p
    assert p["embedding"].startswith("[") and p["embedding"].endswith("]")


def test_partition_items_change_detection():
    r = _prepared()
    h = r["content_hash"]
    # unchanged + already embedded -> refresh only
    assert partition_items([r], {999: (h, True)}) == ([], [r])
    # changed hash -> embed
    assert partition_items([r], {999: ("other", True)}) == ([r], [])
    # embedding missing -> embed
    assert partition_items([r], {999: (h, False)}) == ([r], [])
    # absent from DB -> embed
    assert partition_items([r], {}) == ([r], [])
    # force -> embed even if unchanged
    assert partition_items([r], {999: (h, True)}, force=True) == ([r], [])


def test_loadable_records_keeps_only_named_int_ids():
    from load_pgvector import loadable_records
    recs = [
        {"name": "A", "source_id": 1},
        {"name": "B", "source_id": "sku-or-url"},   # woo fallback string id
        {"name": "C", "source_id": None},
        {"name": "", "source_id": 2},               # missing name
        {"name": "D", "source_id": 999},
    ]
    assert [r["source_id"] for r in loadable_records(recs)] == [1, 999]
