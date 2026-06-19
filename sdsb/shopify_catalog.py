"""shopify_catalog.py — adapter for any Shopify store's public products.json.

Pages through {base}/products.json and maps each product to the normalized
record contract shared with the WooCommerce adapter. Shopify prices are decimal
dollar strings (no minor-units conversion). Shopify has no short-description
field, so we derive one from the first paragraph of body_html.
"""

from __future__ import annotations

import sys
import time

from scrape_common import SLEEP_BETWEEN, fetch, html_to_text

SHOPIFY_LIMIT = 250   # max page size Shopify allows for products.json
MAX_PAGES = 50        # infinite-loop backstop (50 * 250 = 12,500 products)


def _first_paragraph(text: str | None, cap: int = 300) -> str:
    """First paragraph of cleaned text, capped at ~`cap` chars with an ellipsis."""
    if not text:
        return ""
    para = text.strip().split("\n\n", 1)[0].strip()
    if len(para) > cap:
        para = para[:cap].rstrip() + "…"
    return para


def normalize_shopify_product(product: dict, source: dict) -> dict:
    """Map one Shopify products.json product to a normalized catalog record."""
    base = source["base"].rstrip("/")
    variants = product.get("variants") or []

    # Price from the lowest-priced variant; sale fields from that same variant.
    priced = [(float(v["price"]), v) for v in variants
              if v.get("price") not in (None, "")]
    if priced:
        price, min_v = min(priced, key=lambda pv: pv[0])
        cap_raw = min_v.get("compare_at_price")
        cap = float(cap_raw) if cap_raw not in (None, "") else None
        if cap is not None and cap > price:
            on_sale, regular_price, sale_price = True, cap, price
        else:
            on_sale, regular_price, sale_price = False, price, None
    else:
        price = regular_price = sale_price = None
        on_sale = False

    sku = ""
    for v in variants:
        if v.get("sku"):
            sku = v["sku"]
            break

    # categories: product_type first, then tags (array OR comma-string); dedupe, drop empties.
    tags = product.get("tags") or []
    if isinstance(tags, str):
        tags = tags.split(",")
    categories: list[str] = []
    for raw in [product.get("product_type")] + list(tags):
        c = (raw or "").strip()
        if c and c not in categories:
            categories.append(c)

    # attributes: product options, minus Shopify's default "Title" / "Default Title".
    attributes = []
    for opt in product.get("options") or []:
        name = (opt.get("name") or "").strip()
        values = [str(x).strip() for x in (opt.get("values") or []) if str(x).strip()]
        if name and name.lower() != "title" and values != ["Default Title"]:
            attributes.append({"name": name, "values": values})

    variations = [v["title"] for v in variants
                  if v.get("title") and v["title"] != "Default Title"]

    images = product.get("images") or []
    image = images[0].get("src") if images else None

    handle = product.get("handle") or ""
    description = html_to_text(product.get("body_html"))

    return {
        "source": source["slug"],
        "source_id": product.get("id"),
        "name": (product.get("title") or "").strip(),
        "sku": sku,
        "type": product.get("product_type") or "",
        "categories": categories,
        "price": price,
        "regular_price": regular_price,
        "sale_price": sale_price,
        "currency_symbol": "$",
        "on_sale": on_sale,
        "is_in_stock": any(v.get("available") for v in variants),
        "attributes": attributes,
        "variations": variations,
        "permalink": f"{base}/products/{handle}" if handle else base,
        "image": image,
        "short_description": _first_paragraph(description),
        "description": description,
    }


def paginate_shopify(fetch_page, limit: int = SHOPIFY_LIMIT, max_pages: int = MAX_PAGES) -> list:
    """Collect products across pages. Stop on an empty/short batch; cap at max_pages."""
    products: list = []
    hit_cap = True
    for page in range(1, max_pages + 1):
        batch = fetch_page(page)
        if not batch:
            hit_cap = False
            break
        products.extend(batch)
        if len(batch) < limit:
            hit_cap = False
            break
    if hit_cap:
        print(f"  ! pagination hit the {max_pages}-page cap "
              f"({len(products)} products) — store may have more", file=sys.stderr)
    return products


def scrape_shopify(source: dict) -> list[dict]:
    """Scrape a Shopify store's full catalog into normalized records."""
    base = source["base"].rstrip("/")

    def fetch_page(page: int) -> list:
        if page > 1:
            time.sleep(SLEEP_BETWEEN)
        resp = fetch(f"{base}/products.json", params={"limit": SHOPIFY_LIMIT, "page": page})
        resp.raise_for_status()
        return resp.json().get("products", [])

    raw = paginate_shopify(fetch_page)
    records = [normalize_shopify_product(p, source) for p in raw]
    return [r for r in records if r["name"]]
