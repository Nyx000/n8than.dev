import json

import pytest

import refresh
from sources import get_source


def test_scrape_source_dispatches_by_type(monkeypatch):
    monkeypatch.setattr(refresh, "scrape_woocommerce", lambda s: ["woo"])
    monkeypatch.setattr(refresh, "scrape_shopify", lambda s: ["shop"])
    assert refresh.scrape_source(get_source("sandiegoseed")) == ["woo"]
    assert refresh.scrape_source(get_source("seedsnow")) == ["shop"]


def test_scrape_source_unknown_type_raises():
    with pytest.raises(ValueError):
        refresh.scrape_source({"slug": "x", "type": "etsy", "base": "https://x"})


def test_build_catalog_doc_shape_and_json_roundtrip():
    doc = refresh.build_catalog_doc("seedsnow", [{"source_id": 1}], "2026-06-19 00:00:00 UTC")
    assert doc == {"source": "seedsnow", "fetched_utc": "2026-06-19 00:00:00 UTC",
                   "records": [{"source_id": 1}]}
    assert json.loads(json.dumps(doc))["records"][0]["source_id"] == 1
