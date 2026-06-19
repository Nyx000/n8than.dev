#!/usr/bin/env python3
"""
sdseed_catalog.py — Scrape the full public catalog of San Diego Seed Company
into a single LLM-context-ready markdown file (plus raw JSON).

Data source: the public, no-auth WooCommerce Store API.
    Products:   /wp-json/wc/store/v1/products
    Categories: /wp-json/wc/store/v1/products/categories

If the Store API is unreachable, falls back to the sitemap + schema.org JSON-LD.

Outputs (overwritten on each run):
    sdseed_catalog.md    — the deliverable, grouped by category
    sdseed_catalog.json  — full raw API objects, for re-processing

Run:  python sdseed_catalog.py
Deps: requests
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
import sys
import time
import xml.etree.ElementTree as ET

from scrape_common import PER_PAGE, SLEEP_BETWEEN, fetch, html_to_text, to_dollars

BASE = "https://sandiegoseedcompany.com"
PRODUCTS_URL = f"{BASE}/wp-json/wc/store/v1/products"
CATEGORIES_URL = f"{BASE}/wp-json/wc/store/v1/products/categories"
SITEMAP_URL = f"{BASE}/sitemap_index.xml"

MD_PATH = "sdseed_catalog.md"
JSON_PATH = "sdseed_catalog.json"


# --------------------------------------------------------------------------- #
# Price helpers
# --------------------------------------------------------------------------- #
def fmt_money(value: float | None, symbol: str = "$") -> str:
    if value is None:
        return "—"
    return f"{symbol}{value:,.2f}"


# --------------------------------------------------------------------------- #
# Store API fetchers
# --------------------------------------------------------------------------- #
def probe(products_url: str = PRODUCTS_URL) -> bool:
    """Return True if the Store API is live and serving JSON."""
    resp = fetch(products_url, {"per_page": 1})
    ctype = resp.headers.get("Content-Type", "")
    ok = resp.status_code == 200 and "json" in ctype.lower()
    print(
        f"Probe: HTTP {resp.status_code}, Content-Type={ctype!r} -> "
        f"{'Store API live' if ok else 'Store API unavailable'}"
    )
    return ok


def fetch_all_products(products_url: str = PRODUCTS_URL) -> list[dict]:
    """Page through every published product via X-WP-TotalPages."""
    first = fetch(products_url, {"per_page": PER_PAGE, "page": 1})
    first.raise_for_status()
    total_pages = int(first.headers.get("X-WP-TotalPages", "1"))
    total_items = int(first.headers.get("X-WP-Total", "0"))
    print(f"Products: {total_items} items across {total_pages} page(s) of {PER_PAGE}")

    products = list(first.json())
    for page in range(2, total_pages + 1):
        time.sleep(SLEEP_BETWEEN)
        resp = fetch(products_url, {"per_page": PER_PAGE, "page": page})
        resp.raise_for_status()
        batch = resp.json()
        products.extend(batch)
        print(f"  page {page}/{total_pages}: +{len(batch)} (total {len(products)})")
    return products


def fetch_all_categories(categories_url: str = CATEGORIES_URL) -> list[dict]:
    """Fetch all product categories (paginated, though usually one page)."""
    cats: list[dict] = []
    page = 1
    while True:
        resp = fetch(categories_url, {"per_page": PER_PAGE, "page": page})
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        cats.extend(batch)
        total_pages = int(resp.headers.get("X-WP-TotalPages", "1"))
        if page >= total_pages:
            break
        page += 1
        time.sleep(SLEEP_BETWEEN)
    print(f"Categories: {len(cats)} fetched")
    return cats


# --------------------------------------------------------------------------- #
# Fallback: sitemap + JSON-LD
# --------------------------------------------------------------------------- #
def fetch_via_sitemap(sitemap_url: str = SITEMAP_URL) -> list[dict]:
    """Fallback path: collect /product/ URLs from the sitemap, parse JSON-LD."""
    print("Falling back to sitemap + schema.org JSON-LD scraping...", file=sys.stderr)
    product_urls = _collect_product_urls(sitemap_url)
    print(f"Sitemap: {len(product_urls)} product URLs", file=sys.stderr)

    products: list[dict] = []
    for i, url in enumerate(product_urls, 1):
        time.sleep(SLEEP_BETWEEN)
        resp = fetch(url, expect_json=False)
        if resp.status_code != 200:
            continue
        obj = _parse_jsonld_product(resp.text, url)
        if obj:
            products.append(obj)
        if i % 25 == 0:
            print(f"  {i}/{len(product_urls)} pages parsed", file=sys.stderr)
    return products


def _collect_product_urls(sitemap_url: str, _seen: set | None = None) -> list[str]:
    _seen = _seen if _seen is not None else set()
    resp = fetch(sitemap_url, expect_json=False)
    if resp.status_code != 200:
        return []
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError:
        return []
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls: list[str] = []
    # Sub-sitemaps
    for loc in root.findall(".//sm:sitemap/sm:loc", ns):
        sub = (loc.text or "").strip()
        if sub and sub not in _seen:
            _seen.add(sub)
            urls.extend(_collect_product_urls(sub, _seen))
    # Page URLs
    for loc in root.findall(".//sm:url/sm:loc", ns):
        u = (loc.text or "").strip()
        if "/product/" in u:
            urls.append(u)
    return sorted(set(urls))


def _parse_jsonld_product(htmltext: str, url: str) -> dict | None:
    for m in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        htmltext,
        re.DOTALL | re.IGNORECASE,
    ):
        block = m.group(1).strip()
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        for node in _iter_jsonld_nodes(data):
            if node.get("@type") == "Product" or "Product" in (node.get("@type") or []):
                offers = node.get("offers") or {}
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                price = offers.get("price")
                return {
                    "id": node.get("sku") or url,
                    "name": node.get("name", ""),
                    "sku": node.get("sku", ""),
                    "categories": [],
                    "prices": {
                        "price": str(int(float(price) * 100)) if price else "",
                        "regular_price": "",
                        "sale_price": "",
                        "currency_code": offers.get("priceCurrency", "USD"),
                        "currency_symbol": "$",
                        "currency_minor_unit": 2,
                    },
                    "on_sale": False,
                    "is_in_stock": "InStock" in str(offers.get("availability", "")),
                    "attributes": [],
                    "variations": [],
                    "permalink": url,
                    "images": [{"src": node.get("image", "")}]
                    if node.get("image")
                    else [],
                    "short_description": "",
                    "description": node.get("description", ""),
                    "_source": "jsonld",
                }
    return None


def _iter_jsonld_nodes(data):
    if isinstance(data, dict):
        if "@graph" in data:
            yield from _iter_jsonld_nodes(data["@graph"])
        else:
            yield data
    elif isinstance(data, list):
        for item in data:
            yield from _iter_jsonld_nodes(item)


# --------------------------------------------------------------------------- #
# Normalization
# --------------------------------------------------------------------------- #
def normalize(product: dict, source_slug: str = "sandiegoseed") -> dict:
    prices = product.get("prices") or {}
    exp = prices.get("currency_minor_unit", 2)
    symbol = prices.get("currency_symbol", "$")

    cats = [
        html.unescape(c.get("name", ""))
        for c in (product.get("categories") or [])
        if c.get("name")
    ]

    images = product.get("images") or []
    first_image = images[0].get("src") if images else None

    attrs = []
    for a in product.get("attributes") or []:
        terms = [html.unescape(t.get("name", "")) for t in a.get("terms") or []]
        if a.get("name") and terms:
            attrs.append({"name": html.unescape(a["name"]), "values": terms})

    variations = []
    for v in product.get("variations") or []:
        attr_pairs = [
            f"{html.unescape(x.get('name') or '')}: {html.unescape(x.get('value') or '')}"
            for x in v.get("attributes") or []
        ]
        variations.append("; ".join(attr_pairs) or str(v.get("id", "")))

    return {
        "source": source_slug,
        "source_id": product.get("id"),
        "name": html.unescape((product.get("name") or "").strip()),
        "sku": product.get("sku") or "",
        "type": product.get("type", ""),
        "categories": cats,
        "price": to_dollars(prices.get("price"), exp),
        "regular_price": to_dollars(prices.get("regular_price"), exp),
        "sale_price": to_dollars(prices.get("sale_price"), exp),
        "currency_symbol": symbol,
        "on_sale": bool(product.get("on_sale")),
        "is_in_stock": bool(product.get("is_in_stock")),
        "attributes": attrs,
        "variations": variations,
        "permalink": product.get("permalink") or "",
        "image": first_image,
        "short_description": html_to_text(product.get("short_description")),
        "description": html_to_text(product.get("description")),
    }


def scrape_woocommerce(source: dict) -> list[dict]:
    """Scrape a WooCommerce store's full catalog into normalized records."""
    base = source["base"].rstrip("/")
    products_url = f"{base}/wp-json/wc/store/v1/products"
    sitemap_url = f"{base}/sitemap_index.xml"
    if probe(products_url):
        raw = fetch_all_products(products_url)
    else:
        raw = fetch_via_sitemap(sitemap_url)
    records = [normalize(p, source["slug"]) for p in raw]
    return [r for r in records if r["name"]]


# --------------------------------------------------------------------------- #
# Output writers
# --------------------------------------------------------------------------- #
UNCATEGORIZED = "Uncategorized"


def pick_primary_category(item: dict, leaf_cats: set[str]) -> str:
    """Choose the most specific (leaf) category for grouping, else first."""
    cats = item["categories"]
    if not cats:
        return UNCATEGORIZED
    for c in cats:
        if c in leaf_cats:
            return c
    return cats[0]


def build_markdown(items: list[dict], categories: list[dict], fetched_utc: str) -> str:
    # Determine leaf categories (those that are never a parent) for better grouping.
    by_id = {c["id"]: c for c in categories}
    parent_ids = {c.get("parent") for c in categories if c.get("parent")}
    leaf_cats = {c["name"] for c in categories if c["id"] not in parent_ids}

    # Group products by primary category.
    groups: dict[str, list[dict]] = {}
    for it in items:
        key = pick_primary_category(it, leaf_cats)
        groups.setdefault(key, []).append(it)

    lines: list[str] = []
    lines.append("# San Diego Seed Company — Full Product Catalog")
    lines.append("")
    lines.append(f"- **Source:** {BASE}")
    lines.append(f"- **Fetched (UTC):** {fetched_utc}")
    lines.append(f"- **Total products:** {len(items)}")
    lines.append(f"- **Categories:** {len(groups)} (grouping) / {len(categories)} (site total)")
    lines.append("")
    lines.append(
        "> Generated from the public WooCommerce Store API. "
        "Descriptions converted from HTML to plain text/light markdown. "
        "Intended as LLM reference context."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    for cat in sorted(groups, key=lambda k: (k == UNCATEGORIZED, k.lower())):
        prods = sorted(groups[cat], key=lambda p: p["name"].lower())
        lines.append(f"## {cat}  ({len(prods)} products)")
        lines.append("")
        for p in prods:
            lines.append(f"### {p['name']}")
            lines.append("")

            # Price line
            if p["on_sale"] and p["sale_price"] is not None:
                price_str = (
                    f"~~{fmt_money(p['regular_price'], p['currency_symbol'])}~~ "
                    f"{fmt_money(p['sale_price'], p['currency_symbol'])} (on sale)"
                )
            else:
                price_str = fmt_money(p["price"], p["currency_symbol"])
            stock = "In stock" if p["is_in_stock"] else "Out of stock"

            meta = [f"**Price:** {price_str}", f"**Stock:** {stock}"]
            if p["sku"]:
                meta.append(f"**SKU:** {p['sku']}")
            lines.append(" | ".join(meta))
            lines.append("")
            lines.append(f"**Permalink:** {p['permalink']}")

            if len(p["categories"]) > 1:
                lines.append("")
                lines.append(f"**Categories:** {', '.join(p['categories'])}")

            if p["attributes"]:
                lines.append("")
                attr_str = "; ".join(
                    f"{a['name']}: {', '.join(a['values'])}" for a in p["attributes"]
                )
                lines.append(f"**Attributes:** {attr_str}")

            if p["variations"]:
                lines.append("")
                lines.append(f"**Variations:** {', '.join(p['variations'])}")

            if p["image"]:
                lines.append("")
                lines.append(f"**Image:** {p['image']}")

            desc = p["description"] or p["short_description"]
            if desc:
                lines.append("")
                lines.append("**Description:**")
                lines.append("")
                lines.append(desc)

            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def validate(items: list[dict], categories: list[dict]) -> None:
    print("\n=== Validation ===")
    # Count products per category from scraped data.
    scraped_counts: dict[str, int] = {}
    for it in items:
        for c in it["categories"]:
            scraped_counts[c] = scraped_counts.get(c, 0) + 1

    mismatches = 0
    checked = 0
    for c in categories:
        name, advertised = c["name"], c.get("count", 0)
        got = scraped_counts.get(name, 0)
        if advertised:
            checked += 1
            if got != advertised:
                mismatches += 1
                if mismatches <= 15:
                    print(f"  ~ '{name}': API count={advertised}, scraped={got}")
    if mismatches == 0:
        print(f"  OK: all {checked} non-empty category counts match scraped totals.")
    else:
        print(
            f"  {mismatches}/{checked} categories differ "
            "(often due to private/hidden items or parent-category rollups)."
        )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    fetched_utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if probe():
        raw_products = fetch_all_products()
        categories = fetch_all_categories()
    else:
        raw_products = fetch_via_sitemap()
        categories = []

    if not raw_products:
        print("No products fetched — aborting.", file=sys.stderr)
        return 1

    items = [normalize(p) for p in raw_products]
    items = [it for it in items if it["name"]]

    # JSON: raw API objects for re-processing.
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": BASE,
                "fetched_utc": fetched_utc,
                "product_count": len(raw_products),
                "categories": categories,
                "products": raw_products,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"\nWrote {JSON_PATH} ({len(raw_products)} raw products)")

    # Markdown deliverable.
    md = build_markdown(items, categories, fetched_utc)
    with open(MD_PATH, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Wrote {MD_PATH}")

    if categories:
        validate(items, categories)

    # Token estimate.
    word_count = len(md.split())
    tokens = int(word_count * 1.3)
    print("\n=== Output ===")
    print(f"Products written : {len(items)}")
    print(f"Markdown words   : {word_count:,}")
    print(f"Approx tokens    : {tokens:,}  (~{tokens / 1000:.0f}k context)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
