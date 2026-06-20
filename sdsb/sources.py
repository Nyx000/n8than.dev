"""Source registry for the multi-source seed catalog.

Each source is a dict: slug (stable id + DB partition key), human name,
platform type ('woocommerce' | 'shopify'), and base URL (no trailing slash).
Shopify sources may add an optional 'collection' handle to scrape only that
collection's products.json instead of the whole store.
Adding a store later is one entry here — no code change elsewhere.
"""

from __future__ import annotations

SOURCES = [
    {"slug": "sandiegoseed",  "name": "San Diego Seed Company",      "type": "woocommerce", "base": "https://sandiegoseedcompany.com",   "kind": "seed"},
    {"slug": "plantgoodseed", "name": "The Plant Good Seed Company", "type": "shopify",     "base": "https://www.plantgoodseed.com",     "kind": "seed"},
    {"slug": "theodorepayne", "name": "Theodore Payne Foundation",   "type": "shopify",     "base": "https://store.theodorepayne.org", "collection": "seeds-1", "kind": "seed"},
    {"slug": "ricardos",      "name": "Ricardo's Nursery",          "type": "shopify",     "base": "https://store.ricardosnursery.com",     "kind": "plant"},
    {"slug": "plantsexpress", "name": "Plants Express",             "type": "shopify",     "base": "https://plantsexpress.com",             "kind": "plant"},
    {"slug": "neelsnursery",  "name": "Neel's Nursery",             "type": "shopify",     "base": "https://neelsnursery.com",              "kind": "plant"},
    {"slug": "livelyroot",    "name": "Lively Root",                "type": "shopify",     "base": "https://www.livelyroot.com",            "kind": "plant"},
    {"slug": "gosucculent",   "name": "Daniel's Specialty Nursery", "type": "woocommerce", "base": "https://gosucculent.com",               "kind": "plant"},
    {"slug": "wallaceranch",  "name": "Wallace Ranch Dragon Fruit", "type": "shopify",     "base": "https://wallaceranchdragonfruit.com",   "kind": "plant"},
    {"slug": "planetdesert",  "name": "Planet Desert",              "type": "shopify",     "base": "https://planetdesert.com",              "kind": "plant"},
]

VALID_TYPES = {"woocommerce", "shopify"}
VALID_KINDS = {"seed", "plant"}


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


def source_kind(slug: str) -> str:
    """'seed' or 'plant' for a slug; defaults to 'seed' for unknown slugs."""
    for s in SOURCES:
        if s["slug"] == slug:
            return s.get("kind", "seed")
    return "seed"
