#!/usr/bin/env python3
"""
load_pgvector.py — Embed the San Diego Seed catalog and load it into Postgres/pgvector.

Reads sdseed_catalog.json (produced by sdseed_catalog.py), builds a rich text blob
per product, embeds it with Voyage AI (voyage-3.5, 1024-dim), and upserts into the
`sdseed_products` table on the Hetzner Postgres (reached via SSH tunnel).

Idempotent: re-running re-embeds and upserts by product id (ON CONFLICT UPDATE).
Use --only-missing to embed just rows that don't have an embedding yet.

Run:  python load_pgvector.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys

import sdseed_common as c
from sdseed_catalog import normalize

JSON_PATH = "sdseed_catalog.json"
BATCH_SIZE = 100              # texts per Voyage request
BATCH_CHAR_CAP = 380_000     # ~rough token guard per request


def build_embed_text(item: dict) -> str:
    """Compose the text that gets embedded — the semantic fingerprint of a product."""
    parts = [item["name"]]
    if item["categories"]:
        parts.append("Categories: " + ", ".join(item["categories"]))
    if item["attributes"]:
        parts.append(
            "Attributes: "
            + "; ".join(f"{a['name']}: {', '.join(a['values'])}" for a in item["attributes"])
        )
    if item["short_description"]:
        parts.append(item["short_description"])
    if item["description"]:
        parts.append(item["description"])
    return "\n\n".join(p for p in parts if p).strip()


def vec_literal(vec: list[float]) -> str:
    """pgvector text input format: [v1,v2,...]."""
    return "[" + ",".join(f"{x:.7f}" for x in vec) + "]"


def content_hash(item: dict) -> str:
    """Hash of the text that determines the embedding — used to skip unchanged rows."""
    return hashlib.sha256(item["embed_text"].encode("utf-8")).hexdigest()


def batched(items: list, size: int, char_cap: int):
    """Yield batches bounded by count AND total embed-text length."""
    batch, chars = [], 0
    for it in items:
        t_len = len(it["embed_text"])
        if batch and (len(batch) >= size or chars + t_len > char_cap):
            yield batch
            batch, chars = [], 0
        batch.append(it)
        chars += t_len
    if batch:
        yield batch


UPSERT_SQL = """
INSERT INTO sdseed_products (
    id, name, sku, type, categories, primary_category,
    price, regular_price, sale_price, on_sale, is_in_stock,
    permalink, image, attributes, variations,
    short_description, description, embed_text, embedding,
    content_hash, status, updated_at
) VALUES (
    %(id)s, %(name)s, %(sku)s, %(type)s, %(categories)s, %(primary_category)s,
    %(price)s, %(regular_price)s, %(sale_price)s, %(on_sale)s, %(is_in_stock)s,
    %(permalink)s, %(image)s, %(attributes)s, %(variations)s,
    %(short_description)s, %(description)s, %(embed_text)s, %(embedding)s::vector,
    %(content_hash)s, 'active', now()
)
ON CONFLICT (id) DO UPDATE SET
    name=EXCLUDED.name, sku=EXCLUDED.sku, type=EXCLUDED.type,
    categories=EXCLUDED.categories, primary_category=EXCLUDED.primary_category,
    price=EXCLUDED.price, regular_price=EXCLUDED.regular_price,
    sale_price=EXCLUDED.sale_price, on_sale=EXCLUDED.on_sale,
    is_in_stock=EXCLUDED.is_in_stock, permalink=EXCLUDED.permalink,
    image=EXCLUDED.image, attributes=EXCLUDED.attributes,
    variations=EXCLUDED.variations, short_description=EXCLUDED.short_description,
    description=EXCLUDED.description, embed_text=EXCLUDED.embed_text,
    embedding=EXCLUDED.embedding, content_hash=EXCLUDED.content_hash,
    status='active', updated_at=now();
"""

# Cheap refresh for products whose embed-text is unchanged: update mutable fields
# (price/stock/links/etc.) WITHOUT re-embedding.
META_UPDATE_SQL = """
UPDATE sdseed_products SET
    name=%(name)s, sku=%(sku)s, type=%(type)s,
    categories=%(categories)s, primary_category=%(primary_category)s,
    price=%(price)s, regular_price=%(regular_price)s, sale_price=%(sale_price)s,
    on_sale=%(on_sale)s, is_in_stock=%(is_in_stock)s, permalink=%(permalink)s,
    image=%(image)s, attributes=%(attributes)s, variations=%(variations)s,
    short_description=%(short_description)s, status='active', updated_at=now()
WHERE id=%(id)s;
"""


def primary_category(item: dict) -> str | None:
    return item["categories"][0] if item["categories"] else None


def upsert_params(item: dict, vec: list[float]) -> dict:
    return {
        "id": item["id"],
        "name": item["name"],
        "sku": item["sku"],
        "type": item["type"],
        "categories": item["categories"],
        "primary_category": primary_category(item),
        "price": item["price"],
        "regular_price": item["regular_price"],
        "sale_price": item["sale_price"],
        "on_sale": item["on_sale"],
        "is_in_stock": item["is_in_stock"],
        "permalink": item["permalink"],
        "image": item["image"],
        "attributes": json.dumps(item["attributes"]),
        "variations": json.dumps(item["variations"]),
        "short_description": item["short_description"],
        "description": item["description"],
        "embed_text": item["embed_text"],
        "embedding": vec_literal(vec),
        "content_hash": item["content_hash"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=JSON_PATH)
    ap.add_argument("--force", action="store_true",
                    help="re-embed every product, ignoring content hashes")
    ap.add_argument("--mark-discontinued", action="store_true",
                    help="set status='discontinued' for DB rows absent from this scrape")
    ap.add_argument("--limit", type=int, default=0, help="cap products (for testing)")
    args = ap.parse_args()

    c.load_env()
    with open(args.json, encoding="utf-8") as f:
        raw = json.load(f)
    products = raw["products"]
    items = [normalize(p) for p in products]
    items = [it for it in items if it["name"] and it["id"] is not None]
    for it in items:
        it["embed_text"] = build_embed_text(it)
        it["content_hash"] = content_hash(it)
    if args.limit:
        items = items[: args.limit]
    print(f"Loaded {len(items)} products from {args.json}")

    with c.ssh_tunnel() as port:
        conn = c.connect(port)
        conn.autocommit = False

        # Existing state: id -> (content_hash, has_embedding)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, content_hash, embedding IS NOT NULL FROM sdseed_products;"
            )
            existing = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

        # Partition: re-embed new/changed/embedding-missing; else metadata-only refresh.
        to_embed, to_refresh = [], []
        for it in items:
            prev = existing.get(it["id"])
            if (args.force or prev is None
                    or prev[0] != it["content_hash"] or not prev[1]):
                to_embed.append(it)
            else:
                to_refresh.append(it)
        print(f"Change-detection: {len(to_embed)} to (re)embed, "
              f"{len(to_refresh)} metadata-only, "
              f"{len(existing)} already in DB")

        # Cheap metadata refresh (no Voyage calls).
        if to_refresh:
            with conn.cursor() as cur:
                for it in to_refresh:
                    cur.execute(META_UPDATE_SQL, upsert_params(it, [0.0]))
            conn.commit()
            print(f"  refreshed {len(to_refresh)} rows (price/stock/etc.)")

        # Embed + upsert the changed/new ones.
        total, done = len(to_embed), 0
        for batch in batched(to_embed, BATCH_SIZE, BATCH_CHAR_CAP):
            vectors = c.embed_documents([it["embed_text"] for it in batch])
            with conn.cursor() as cur:
                for it, vec in zip(batch, vectors):
                    cur.execute(UPSERT_SQL, upsert_params(it, vec))
            conn.commit()
            done += len(batch)
            print(f"  embedded + upserted {done}/{total}")

        # Discontinued handling.
        if args.mark_discontinued:
            current_ids = [it["id"] for it in items]
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE sdseed_products SET status='discontinued', updated_at=now() "
                    "WHERE id <> ALL(%s) AND status <> 'discontinued';",
                    (current_ids,),
                )
                gone = cur.rowcount
            conn.commit()
            print(f"  marked {gone} products discontinued")

        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*), count(embedding), "
                "count(*) FILTER (WHERE status='active') FROM sdseed_products;"
            )
            rows, embedded, active = cur.fetchone()
        conn.close()

    print(f"\nDone. Table: {rows} rows, {embedded} embedded, {active} active.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
