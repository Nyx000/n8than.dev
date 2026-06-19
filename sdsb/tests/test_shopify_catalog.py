from shopify_catalog import normalize_shopify_product, paginate_shopify, _first_paragraph


class _FakeResp:
    def __init__(self, data):
        self._d = data
    def raise_for_status(self):
        pass
    def json(self):
        return self._d


SRC = {"slug": "marysheirloom", "name": "Mary's Heirloom Seeds",
       "type": "shopify", "base": "https://www.marysheirloomseeds.com"}

PRODUCT = {
    "id": 123456789,
    "title": "Cherokee Purple Tomato",
    "handle": "cherokee-purple-tomato",
    "body_html": "<p>An heirloom beefsteak with rich flavor.</p><p>Indeterminate. 80 days.</p>",
    "product_type": "Vegetables",
    "tags": ["Tomato", "Heirloom", "Full Sun"],
    "variants": [
        {"title": "100 seeds", "sku": "TOM-CP-100", "price": "3.95",
         "compare_at_price": "4.95", "available": True},
        {"title": "500 seeds", "sku": "TOM-CP-500", "price": "12.95",
         "compare_at_price": None, "available": False},
    ],
    "options": [{"name": "Size", "values": ["100 seeds", "500 seeds"]}],
    "images": [{"src": "https://cdn.example.com/cp.jpg"}],
}


def test_identity_fields():
    r = normalize_shopify_product(PRODUCT, SRC)
    assert r["source"] == "marysheirloom"
    assert r["source_id"] == 123456789
    assert r["name"] == "Cherokee Purple Tomato"
    assert r["permalink"] == "https://www.marysheirloomseeds.com/products/cherokee-purple-tomato"
    assert r["image"] == "https://cdn.example.com/cp.jpg"
    assert "id" not in r


def test_price_is_min_variant_with_sale_from_same_variant():
    r = normalize_shopify_product(PRODUCT, SRC)
    assert r["price"] == 3.95
    assert r["on_sale"] is True
    assert r["regular_price"] == 4.95
    assert r["sale_price"] == 3.95


def test_sku_first_variant_and_stock_any_available():
    r = normalize_shopify_product(PRODUCT, SRC)
    assert r["sku"] == "TOM-CP-100"
    assert r["is_in_stock"] is True


def test_categories_product_type_first_then_tags():
    assert normalize_shopify_product(PRODUCT, SRC)["categories"] == \
        ["Vegetables", "Tomato", "Heirloom", "Full Sun"]


def test_descriptions_full_and_derived_short():
    r = normalize_shopify_product(PRODUCT, SRC)
    assert r["description"] == "An heirloom beefsteak with rich flavor.\n\nIndeterminate. 80 days."
    assert r["short_description"] == "An heirloom beefsteak with rich flavor."


def test_attributes_and_variations():
    r = normalize_shopify_product(PRODUCT, SRC)
    assert r["attributes"] == [{"name": "Size", "values": ["100 seeds", "500 seeds"]}]
    assert r["variations"] == ["100 seeds", "500 seeds"]


def test_tags_as_comma_string_dedup_with_product_type():
    p = dict(PRODUCT, product_type="Tomato", tags="Tomato, Heirloom , ")
    assert normalize_shopify_product(p, SRC)["categories"] == ["Tomato", "Heirloom"]


def test_default_title_option_and_variation_dropped():
    p = dict(PRODUCT,
             options=[{"name": "Title", "values": ["Default Title"]}],
             variants=[{"title": "Default Title", "sku": "X", "price": "5.00",
                        "compare_at_price": None, "available": True}])
    r = normalize_shopify_product(p, SRC)
    assert r["attributes"] == []
    assert r["variations"] == []
    assert r["sku"] == "X"
    assert r["price"] == 5.0 and r["on_sale"] is False and r["sale_price"] is None


def test_no_variants_or_images():
    r = normalize_shopify_product(dict(PRODUCT, variants=[], images=[]), SRC)
    assert r["price"] is None and r["sku"] == "" and r["is_in_stock"] is False
    assert r["image"] is None


def test_first_paragraph_caps_with_ellipsis():
    out = _first_paragraph("x" * 500, cap=300)
    assert len(out) == 301 and out.endswith("…")


def test_paginate_stops_on_short_batch():
    batches = [[{"id": i} for i in range(250)], [{"id": i} for i in range(10)]]
    fetch_page = lambda page: batches[page - 1] if page - 1 < len(batches) else []
    assert len(paginate_shopify(fetch_page, limit=250, max_pages=50)) == 260


def test_paginate_stops_on_empty_batch():
    fetch_page = lambda page: [{"id": 1}] if page == 1 else []
    assert len(paginate_shopify(fetch_page, limit=250, max_pages=50)) == 1


def test_paginate_respects_cap(capsys):
    fetch_page = lambda page: [{"id": page}, {"id": page}]  # always full
    assert len(paginate_shopify(fetch_page, limit=2, max_pages=3)) == 6
    assert "3-page cap" in capsys.readouterr().err


def test_non_title_option_with_default_title_value_is_kept():
    p = dict(PRODUCT, options=[{"name": "Finish", "values": ["Default Title"]}])
    r = normalize_shopify_product(p, SRC)
    assert r["attributes"] == [{"name": "Finish", "values": ["Default Title"]}]


def test_scrape_shopify_reads_products_key(monkeypatch):
    import shopify_catalog as m

    class FakeResp:
        def __init__(self, data):
            self._d = data
        def raise_for_status(self):
            pass
        def json(self):
            return self._d

    def fake_fetch(url, params=None, **kw):
        return FakeResp({"products": [PRODUCT]}) if params["page"] == 1 else FakeResp({"products": []})

    monkeypatch.setattr(m, "fetch", fake_fetch)
    monkeypatch.setattr(m, "SLEEP_BETWEEN", 0)
    recs = m.scrape_shopify(SRC)
    assert len(recs) == 1 and recs[0]["source_id"] == 123456789


def test_scrape_shopify_uses_collection_when_present(monkeypatch):
    import shopify_catalog as m
    seen = {}

    def fake_fetch(url, params=None, **kw):
        seen["url"] = url
        return _FakeResp({"products": []})

    monkeypatch.setattr(m, "fetch", fake_fetch)
    monkeypatch.setattr(m, "SLEEP_BETWEEN", 0)
    src = {"slug": "theodorepayne", "name": "Theodore Payne Foundation",
           "type": "shopify", "base": "https://store.theodorepayne.org",
           "collection": "seeds-1"}
    m.scrape_shopify(src)
    assert seen["url"] == "https://store.theodorepayne.org/collections/seeds-1/products.json"


def test_scrape_shopify_uses_products_json_without_collection(monkeypatch):
    import shopify_catalog as m
    seen = {}

    def fake_fetch(url, params=None, **kw):
        seen["url"] = url
        return _FakeResp({"products": []})

    monkeypatch.setattr(m, "fetch", fake_fetch)
    monkeypatch.setattr(m, "SLEEP_BETWEEN", 0)
    src = {"slug": "plantgoodseed", "name": "The Plant Good Seed Company",
           "type": "shopify", "base": "https://www.plantgoodseed.com"}
    m.scrape_shopify(src)
    assert seen["url"] == "https://www.plantgoodseed.com/products.json"
