"""Source registry for the multi-source seed catalog.

Each source is a dict: slug (stable id + DB partition key), human name,
platform type ('woocommerce' | 'shopify'), and base URL (no trailing slash).
Shopify sources may add an optional 'collection' handle to scrape only that
collection's products.json instead of the whole store.
Adding a store later is one entry here — no code change elsewhere.
"""

from __future__ import annotations

SOURCES = [
    {"slug": "sandiegoseed",  "name": "San Diego Seed Company",      "type": "woocommerce", "base": "https://sandiegoseedcompany.com"},
    {"slug": "plantgoodseed", "name": "The Plant Good Seed Company", "type": "shopify",     "base": "https://www.plantgoodseed.com"},
    {"slug": "theodorepayne", "name": "Theodore Payne Foundation",   "type": "shopify",     "base": "https://store.theodorepayne.org", "collection": "seeds-1"},
]

VALID_TYPES = {"woocommerce", "shopify"}


def get_source(slug: str) -> dict:
    """Return the source descriptor for a slug, or raise KeyError."""
    for s in SOURCES:
        if s["slug"] == slug:
            return s
    raise KeyError(f"unknown source slug: {slug}")


def source_name(slug: str) -> str:
    """Human-readable grower name for a slug; falls back to the slug itself."""
    for s in SOURCES:
        if s["slug"] == slug:
            return s["name"]
    return slug
