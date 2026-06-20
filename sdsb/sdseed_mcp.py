#!/usr/bin/env python3
"""
sdseed_mcp.py — MCP server for the SeedSearch catalog (San Diego & SoCal seed growers).

Exposes the pgvector-backed catalog as MCP tools any client (Claude Desktop,
Claude Code, etc.) can call:

  * search_products   — semantic (vector) search over product descriptions
  * keyword_search    — plain substring search by name/SKU
  * get_product       — full details for one product (by id or exact-ish name)
  * list_categories   — categories with product counts

On startup it opens an SSH tunnel to the Hetzner Postgres (localhost-only) and
keeps it alive for the process lifetime. Embeddings use Voyage AI (voyage-3.5).

Run (stdio):  python sdseed_mcp.py
"""

from __future__ import annotations

import atexit
import json

import sdseed_common as c
from load_pgvector import vec_literal
from mcp.server.fastmcp import FastMCP
from sources import source_name

c.load_env()
mcp = FastMCP("seedsearch")

# --- persistent SSH tunnel + connection -------------------------------------- #
_tunnel_cm = None
_tunnel_port = None
_conn = None


def _ensure_tunnel() -> int:
    global _tunnel_cm, _tunnel_port
    if _tunnel_port is None:
        _tunnel_cm = c.ssh_tunnel()
        _tunnel_port = _tunnel_cm.__enter__()
        atexit.register(_close)
    return _tunnel_port


def _close():
    global _conn, _tunnel_cm
    if _conn is not None:
        try:
            _conn.close()
        except Exception:
            pass
        _conn = None
    if _tunnel_cm is not None:
        try:
            _tunnel_cm.__exit__(None, None, None)
        except Exception:
            pass
        _tunnel_cm = None


def _get_conn():
    """Return a live connection, (re)opening the tunnel/connection as needed."""
    global _conn
    port = _ensure_tunnel()
    if _conn is None or _conn.closed:
        _conn = c.connect(port)
        _conn.autocommit = True
    else:
        # cheap liveness check; reconnect on failure
        try:
            with _conn.cursor() as cur:
                cur.execute("SELECT 1;")
        except Exception:
            _conn = c.connect(port)
            _conn.autocommit = True
    return _conn


def _row_to_dict(row, cols) -> dict:
    return {col: val for col, val in zip(cols, row)}


def _format_money(v):
    return None if v is None else float(v)


# --- tools ------------------------------------------------------------------- #
@mcp.tool()
def search_products(
    query: str,
    k: int = 5,
    in_stock_only: bool = False,
    category: str | None = None,
    kind: str | None = None,
) -> str:
    """
    Semantic search over the SeedSearch catalog (San Diego & SoCal seed growers).

    Finds products whose descriptions are most semantically similar to `query`
    (meaning-based, not keyword). Good for natural-language requests like
    "drought tolerant flowers for pollinators" or "peppers for hot sauce".

    Args:
        query: Natural-language description of what you're looking for.
        k: Number of results to return (default 5, max 25).
        in_stock_only: If true, only return products currently in stock.
        category: Optional category name to restrict results (e.g. "Tomatoes").
        kind: Optional 'plant' or 'seed' filter.

    Returns: JSON list of matches with name, category, price, stock, similarity,
    permalink, and a short description snippet.
    """
    k = max(1, min(int(k), 25))
    qvec = vec_literal(c.embed_query(query))

    where = []
    params: list = [qvec]
    if in_stock_only:
        where.append("is_in_stock = true")
    if category:
        where.append("%s = ANY(categories)")
        params.append(category)
    if kind:
        where.append("kind = %s")
        params.append(kind)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    params.append(qvec)
    params.append(k)

    sql = f"""
        SELECT source, source_id, name, primary_category, categories, price, sale_price, on_sale,
               is_in_stock, kind, permalink, short_description,
               1 - (embedding <=> %s::vector) AS similarity
        FROM sdseed_products
        {where_sql}
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """
    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [d.name for d in cur.description]
        rows = [_row_to_dict(r, cols) for r in cur.fetchall()]

    for r in rows:
        r["price"] = _format_money(r["price"])
        r["sale_price"] = _format_money(r["sale_price"])
        r["similarity"] = round(float(r["similarity"]), 4)
        r["source_name"] = source_name(r["source"])
        sd = r.get("short_description") or ""
        r["short_description"] = (sd[:300] + "…") if len(sd) > 300 else sd
    return json.dumps(rows, ensure_ascii=False, indent=2)


@mcp.tool()
def keyword_search(text: str, k: int = 10) -> str:
    """
    Plain substring search by product name or SKU (case-insensitive).
    Use when you know part of the exact product name. For meaning-based
    discovery, use search_products instead.

    Args:
        text: Substring to look for in the name or SKU.
        k: Max results (default 10, max 50).
    """
    k = max(1, min(int(k), 50))
    like = f"%{text.lower()}%"
    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT source, source_id, name, primary_category, price, is_in_stock, permalink
            FROM sdseed_products
            WHERE lower(name) LIKE %s OR lower(coalesce(sku,'')) LIKE %s
            ORDER BY name
            LIMIT %s;
        """, (like, like, k))
        cols = [d.name for d in cur.description]
        rows = [_row_to_dict(r, cols) for r in cur.fetchall()]
    for r in rows:
        r["price"] = _format_money(r["price"])
    return json.dumps(rows, ensure_ascii=False, indent=2)


@mcp.tool()
def get_product(source: str | None = None, source_id: int | None = None,
                name: str | None = None) -> str:
    """
    Get full details for a single product, including the complete description.

    Provide either (`source` AND `source_id`) for an exact lookup, or `name`
    for a best case-insensitive match.

    Returns: JSON object with all catalog fields, or an error message if not found.
    """
    conn = _get_conn()
    with conn.cursor() as cur:
        if source is not None and source_id is not None:
            cur.execute("SELECT * FROM sdseed_products WHERE source=%s AND source_id=%s;",
                        (source, source_id))
        elif name:
            cur.execute(
                "SELECT * FROM sdseed_products "
                "WHERE lower(name) = lower(%s) "
                "OR lower(name) LIKE lower(%s) ORDER BY length(name) LIMIT 1;",
                (name, f"%{name}%"),
            )
        else:
            return json.dumps({"error": "Provide either (source and source_id) or name."})
        row = cur.fetchone()
        if not row:
            return json.dumps({"error": "Product not found."})
        cols = [d.name for d in cur.description]
        rec = _row_to_dict(row, cols)

    for key in ("price", "regular_price", "sale_price"):
        rec[key] = _format_money(rec.get(key))
    rec.pop("embedding", None)  # don't dump the raw vector
    if rec.get("updated_at"):
        rec["updated_at"] = str(rec["updated_at"])
    return json.dumps(rec, ensure_ascii=False, indent=2)


@mcp.tool()
def list_categories() -> str:
    """
    List all product categories with how many catalog products fall under each
    (based on the loaded products). Useful for browsing or scoping a search.
    """
    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT cat, count(*) AS n
            FROM sdseed_products, unnest(categories) AS cat
            GROUP BY cat
            ORDER BY n DESC, cat;
        """)
        rows = [{"category": r[0], "product_count": r[1]} for r in cur.fetchall()]
    return json.dumps(rows, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()
