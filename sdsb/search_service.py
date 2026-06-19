#!/usr/bin/env python3
"""
search_service.py — HTTP search API for the San Diego Seed catalog demo.

Two-stage retrieval: pgvector ANN recall -> Voyage rerank-2.5 precision.
Co-located with Postgres on the Hetzner box (set SDSEED_NO_TUNNEL=1 there);
runs locally over the SSH tunnel otherwise.

Endpoints (served at service root; Caddy mounts these under /seedsearch/):
    GET  /              -> demo HTML page
    GET  /health        -> {"ok": true, ...}
    GET  /search        -> ?q=&k=&in_stock=&category=&rerank=
    GET  /product/{id}  -> full product record
    GET  /categories    -> [{category, product_count}]

Run:  uvicorn search_service:app --host 127.0.0.1 --port 3002
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse

import sdseed_common as c
from load_pgvector import vec_literal

c.load_env()
app = FastAPI(title="San Diego Seed — Semantic Catalog Search")

RECALL = 50  # vector candidates pulled before reranking
_conn = None


def _get_conn():
    global _conn
    if _conn is None or _conn.closed:
        # SDSEED_NO_TUNNEL=1 on the server makes ssh_tunnel a no-op.
        port = c._env("PGPORT", "5432" if c._no_tunnel() else "6543")
        if not c._no_tunnel():
            # local dev: ensure a tunnel exists (reused if already open)
            global _tunnel
            _tunnel = c.ssh_tunnel()
            port = _tunnel.__enter__()
        _conn = c.connect(int(port))
        _conn.autocommit = True
    return _conn


def _money(v):
    return None if v is None else float(v)


@app.get("/health")
def health():
    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FILTER (WHERE status='active') FROM sdseed_products;")
        active = cur.fetchone()[0]
    return {"ok": True, "active_products": active,
            "embed_model": c.EMBED_MODEL, "rerank_model": c.RERANK_MODEL}


@app.get("/search")
def search(
    q: str = Query(..., min_length=1, description="natural-language query"),
    k: int = Query(8, ge=1, le=25),
    in_stock: bool = Query(False),
    category: str | None = Query(None),
    rerank: bool = Query(True),
):
    conn = _get_conn()
    qvec = vec_literal(c.embed_query(q))

    where = ["status='active'"]
    params: list = [qvec]
    if in_stock:
        where.append("is_in_stock=true")
    if category:
        where.append("%s = ANY(categories)")
        params.append(category)
    params.append(qvec)
    params.append(RECALL if rerank else k)

    sql = f"""
        SELECT id, name, primary_category, categories, price, regular_price,
               sale_price, on_sale, is_in_stock, permalink, image, short_description,
               1 - (embedding <=> %s::vector) AS vec_score
        FROM sdseed_products
        WHERE {' AND '.join(where)}
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [d.name for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    if rerank and rows:
        docs = [f"{r['name']}. {r['short_description'] or ''}" for r in rows]
        ranked = c.rerank(q, docs, top_k=k)
        out = []
        for idx, score in ranked:
            r = rows[idx]
            r["rerank_score"] = round(float(score), 4)
            out.append(r)
        rows = out
    else:
        rows = rows[:k]

    for r in rows:
        r["price"] = _money(r["price"])
        r["regular_price"] = _money(r["regular_price"])
        r["sale_price"] = _money(r["sale_price"])
        r["vec_score"] = round(float(r["vec_score"]), 4)
        sd = r.get("short_description") or ""
        r["short_description"] = (sd[:280] + "…") if len(sd) > 280 else sd

    return {"query": q, "count": len(rows), "reranked": rerank, "results": rows}


@app.get("/product/{pid}")
def product(pid: int):
    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM sdseed_products WHERE id=%s;", (pid,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Product not found")
        rec = dict(zip([d.name for d in cur.description], row))
    for key in ("price", "regular_price", "sale_price"):
        rec[key] = _money(rec.get(key))
    rec.pop("embedding", None)
    rec["updated_at"] = str(rec.get("updated_at"))
    return JSONResponse(rec)


@app.get("/categories")
def categories():
    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT cat, count(*) AS n
            FROM sdseed_products, unnest(categories) AS cat
            WHERE status='active'
            GROUP BY cat ORDER BY n DESC, cat;
        """)
        return [{"category": r[0], "product_count": r[1]} for r in cur.fetchall()]


@app.get("/", response_class=HTMLResponse)
def index():
    page = Path(__file__).resolve().parent / "demo_page.html"
    if page.exists():
        return page.read_text(encoding="utf-8")
    return "<h1>San Diego Seed — Semantic Search</h1><p>Demo page not found.</p>"
