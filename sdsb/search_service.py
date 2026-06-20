#!/usr/bin/env python3
"""
search_service.py — HTTP search API for the SeedSearch demo (San Diego & SoCal seed catalogs).

Two-stage retrieval: pgvector ANN recall -> Voyage rerank-2.5 precision.
Co-located with Postgres on the Hetzner box (set SDSEED_NO_TUNNEL=1 there);
runs locally over the SSH tunnel otherwise.

Endpoints (served at service root; Caddy mounts these under /seedsearch/):
    GET  /              -> demo HTML page
    GET  /health        -> {"ok": true, ...}
    GET  /search        -> ?q=&k=&in_stock=&category=&rerank=
    GET  /product/{source}/{source_id}  -> full product record
    GET  /categories    -> [{category, product_count}]

Run:  uvicorn search_service:app --host 127.0.0.1 --port 3002
"""

from __future__ import annotations

import json
from pathlib import Path

import time as _time
from collections import deque

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse

import sdseed_common as c
from load_pgvector import vec_literal
from sources import source_name
from search_sections import partition_sections

c.load_env()
app = FastAPI(title="SeedSearch — Semantic Catalog Search")

RECALL = 50  # vector candidates pulled before reranking
RECALL_PER_KIND = 25  # vector candidates pulled per kind before reranking
_conn = None

# --- Generous in-memory rate limiting on /search (it calls Voyage = costs money).
# Single uvicorn worker + async loop => plain dict/deque ops are atomic enough.
RL_PER_IP_PER_MIN = 40      # per client IP
RL_GLOBAL_PER_MIN = 600     # safety ceiling across all clients
_RL_WINDOW = 60.0
_ip_hits: dict[str, deque] = {}
_global_hits: deque = deque()


def _client_ip(request: Request) -> str:
    # Service is bound to 127.0.0.1 and only Caddy reaches it, so the
    # X-Forwarded-For Caddy sets is trustworthy.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limit(request: Request) -> None:
    now = _time.monotonic()
    while _global_hits and now - _global_hits[0] > _RL_WINDOW:
        _global_hits.popleft()
    if len(_global_hits) >= RL_GLOBAL_PER_MIN:
        raise HTTPException(429, "The demo is busy right now — try again in a minute.",
                            headers={"Retry-After": "60"})
    ip = _client_ip(request)
    dq = _ip_hits.get(ip)
    if dq is None:
        dq = _ip_hits[ip] = deque()
    while dq and now - dq[0] > _RL_WINDOW:
        dq.popleft()
    if len(dq) >= RL_PER_IP_PER_MIN:
        raise HTTPException(429, "Slow down a moment — too many searches. Try again shortly.",
                            headers={"Retry-After": "30"})
    dq.append(now)
    _global_hits.append(now)
    if len(_ip_hits) > 5000:  # occasional cleanup of idle entries
        for k in [k for k, v in _ip_hits.items() if not v]:
            _ip_hits.pop(k, None)


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


def _recall(conn, qvec, kind: str, in_stock: bool, category: str | None, limit: int) -> list[dict]:
    """Nearest `limit` active rows of one kind by cosine distance."""
    where = ["status='active'", "kind=%s"]
    params: list = [qvec, kind]
    if in_stock:
        where.append("is_in_stock=true")
    if category:
        where.append("%s = ANY(categories)")
        params.append(category)
    params.append(qvec)
    params.append(limit)
    sql = f"""
        SELECT source, source_id, name, primary_category, categories, price, regular_price,
               sale_price, on_sale, is_in_stock, permalink, image, short_description, kind,
               1 - (embedding <=> %s::vector) AS vec_score
        FROM sdseed_products
        WHERE {' AND '.join(where)}
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


@app.get("/search")
def search(
    request: Request,
    q: str = Query(..., min_length=1, description="natural-language query"),
    k: int = Query(8, ge=1, le=25),
    in_stock: bool = Query(False),
    category: str | None = Query(None),
    rerank: bool = Query(True),
    kind: str = Query("all"),
):
    _rate_limit(request)
    conn = _get_conn()
    qvec = vec_literal(c.embed_query(q))

    kinds = ["plant", "seed"] if kind == "all" else [kind]
    per_kind = RECALL_PER_KIND if rerank else k
    candidates: list = []
    for kd in kinds:
        candidates.extend(_recall(conn, qvec, kd, in_stock, category, per_kind))

    if rerank and candidates:
        docs = [f"{r['name']}. {r['short_description'] or ''}" for r in candidates]
        ranked = c.rerank(q, docs, top_k=len(candidates))
        ordered = []
        for idx, score in ranked:
            r = candidates[idx]
            r["rerank_score"] = round(float(score), 4)
            ordered.append(r)
        candidates = ordered

    sections = partition_sections(candidates, k)
    for bucket in sections.values():
        for r in bucket:
            r["price"] = _money(r["price"])
            r["regular_price"] = _money(r["regular_price"])
            r["sale_price"] = _money(r["sale_price"])
            r["vec_score"] = round(float(r["vec_score"]), 4)
            r["source_name"] = source_name(r["source"])
            sd = r.get("short_description") or ""
            r["short_description"] = (sd[:280] + "…") if len(sd) > 280 else sd

    return {"query": q, "reranked": rerank,
            "counts": {"plants": len(sections["plant"]), "seeds": len(sections["seed"])},
            "plants": sections["plant"], "seeds": sections["seed"]}


@app.get("/product/{source}/{source_id}")
def product(source: str, source_id: int):
    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM sdseed_products WHERE source=%s AND source_id=%s;",
                    (source, source_id))
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
    return "<h1>SeedSearch — Semantic Search</h1><p>Demo page not found.</p>"
