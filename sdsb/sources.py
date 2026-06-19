"""Source registry for the multi-source seed catalog.

Each source is a dict: slug (stable id + DB partition key), human name,
platform type ('woocommerce' | 'shopify'), and base URL (no trailing slash).
Adding a store later is one entry here — no code change elsewhere.
"""

from __future__ import annotations

SOURCES = [
    {"slug": "sandiegoseed",  "name": "San Diego Seed Company",      "type": "woocommerce", "base": "https://sandiegoseedcompany.com"},
    {"slug": "marysheirloom", "name": "Mary's Heirloom Seeds",       "type": "shopify",     "base": "https://www.marysheirloomseeds.com"},
    {"slug": "seedsnow",      "name": "SeedsNow",                    "type": "shopify",     "base": "https://www.seedsnow.com"},
    {"slug": "plantgoodseed", "name": "The Plant Good Seed Company", "type": "shopify",     "base": "https://www.plantgoodseed.com"},
]

VALID_TYPES = {"woocommerce", "shopify"}


def get_source(slug: str) -> dict:
    """Return the source descriptor for a slug, or raise KeyError."""
    for s in SOURCES:
        if s["slug"] == slug:
            return s
    raise KeyError(f"unknown source slug: {slug}")
