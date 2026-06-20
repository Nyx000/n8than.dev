from scrape_common import is_listable_plant  # noqa: F401  (ensures shared import path)
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

PLANT_SRC = {"slug": "gosucculent", "name": "Daniel's Specialty Nursery",
             "type": "woocommerce", "base": "https://gosucculent.com", "kind": "plant"}


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


def test_normalize_kind_defaults_seed():
    assert normalize(SAMPLE, "sandiegoseed")["kind"] == "seed"
    assert normalize(SAMPLE)["kind"] == "seed"


def test_normalize_kind_explicit_plant():
    assert normalize(SAMPLE, "gosucculent", "plant")["kind"] == "plant"


def test_scrape_woocommerce_filters_merch_for_plant_source(monkeypatch):
    import sdseed_catalog as m
    gift = dict(SAMPLE, id=1, name="Gift Card",
                prices={"price": "2500", "regular_price": "2500", "sale_price": "",
                        "currency_minor_unit": 2, "currency_symbol": "$"})
    plant = dict(SAMPLE, id=2, name="Echeveria subsessilis",
                 prices={"price": "400", "regular_price": "400", "sale_price": "",
                         "currency_minor_unit": 2, "currency_symbol": "$"})
    free = dict(SAMPLE, id=3, name="Display Only",
                prices={"price": "0", "regular_price": "0", "sale_price": "",
                        "currency_minor_unit": 2, "currency_symbol": "$"})
    monkeypatch.setattr(m, "probe", lambda url: True)
    monkeypatch.setattr(m, "fetch_all_products", lambda url: [gift, plant, free])
    recs = m.scrape_woocommerce(PLANT_SRC)
    assert [r["source_id"] for r in recs] == [2]      # gift card + $0 dropped
    assert recs[0]["kind"] == "plant"


def test_scrape_woocommerce_reclassifies_seed_named_for_plant_source(monkeypatch):
    import sdseed_catalog as m
    seed = dict(SAMPLE, id=10, name="California Wildflower Mix - Seed",
                prices={"price": "500", "regular_price": "500", "sale_price": "",
                        "currency_minor_unit": 2, "currency_symbol": "$"})
    plant = dict(SAMPLE, id=11, name="Echeveria subsessilis",
                 prices={"price": "400", "regular_price": "400", "sale_price": "",
                         "currency_minor_unit": 2, "currency_symbol": "$"})
    monkeypatch.setattr(m, "probe", lambda url: True)
    monkeypatch.setattr(m, "fetch_all_products", lambda url: [seed, plant])
    recs = m.scrape_woocommerce(PLANT_SRC)
    by_id = {r["source_id"]: r["kind"] for r in recs}
    assert by_id == {10: "seed", 11: "plant"}         # 'Seed' in name -> seed inventory
