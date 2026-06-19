from sdseed_catalog import normalize, scrape_woocommerce
from sources import get_source

SAMPLE = {
    "id": 12345,
    "name": "Genovese Basil",
    "sku": "HERB-BAS-GEN",
    "type": "variable",
    "categories": [{"name": "Herbs"}, {"name": "Basil"}],
    "prices": {"price": "350", "regular_price": "350", "sale_price": "",
               "currency_minor_unit": 2, "currency_symbol": "$"},
    "on_sale": False,
    "is_in_stock": True,
    "attributes": [{"name": "Packet Size",
                    "terms": [{"name": "100 seeds"}, {"name": "500 seeds"}]}],
    "variations": [{"id": 1, "attributes": [{"name": "Packet Size", "value": "100 seeds"}]}],
    "permalink": "https://sandiegoseedcompany.com/product/genovese-basil/",
    "images": [{"src": "https://img/basil.jpg"}],
    "short_description": "<p>Classic Italian basil.</p>",
    "description": "<p>Sweet, aromatic leaves.</p>",
}


def test_normalize_emits_source_and_source_id_not_id():
    rec = normalize(SAMPLE, "sandiegoseed")
    assert rec["source"] == "sandiegoseed"
    assert rec["source_id"] == 12345
    assert "id" not in rec


def test_normalize_price_from_minor_units():
    assert normalize(SAMPLE, "sandiegoseed")["price"] == 3.5


def test_normalize_categories_and_attributes():
    rec = normalize(SAMPLE, "sandiegoseed")
    assert rec["categories"] == ["Herbs", "Basil"]
    assert rec["attributes"] == [{"name": "Packet Size", "values": ["100 seeds", "500 seeds"]}]


def test_normalize_strips_html_descriptions():
    rec = normalize(SAMPLE, "sandiegoseed")
    assert rec["short_description"] == "Classic Italian basil."
    assert rec["description"] == "Sweet, aromatic leaves."


def test_normalize_defaults_slug_to_sandiegoseed():
    assert normalize(SAMPLE)["source"] == "sandiegoseed"


def test_scrape_woocommerce_wires_probe_and_fetch(monkeypatch):
    import sdseed_catalog as m
    monkeypatch.setattr(m, "probe", lambda url: True)
    monkeypatch.setattr(m, "fetch_all_products", lambda url: [SAMPLE])
    recs = m.scrape_woocommerce(get_source("sandiegoseed"))
    assert len(recs) == 1
    assert recs[0]["source_id"] == 12345 and recs[0]["source"] == "sandiegoseed"
