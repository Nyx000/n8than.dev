# SD Seed — Semantic Catalog Search

Natural-language search over the full San Diego Seed Company catalog, served at
[n8than.dev/sdsb](https://n8than.dev/sdsb). Part of the n8than.dev monorepo so it
versions and deploys alongside the site.

```
sdsb/
  sdseed_catalog.py   Scraper: WooCommerce Store API -> catalog JSON/MD
  sdseed_common.py    Shared: .env, SSH tunnel / no-tunnel, Voyage embed + rerank, DB
  load_pgvector.py    Embed + upsert into Postgres/pgvector (smart change-detection)
  refresh.py          Scrape + smart-load in one step (used by the weekly timer)
  search_service.py   FastAPI search API + demo page (two-stage: pgvector -> rerank)
  sdseed_mcp.py       MCP server exposing the catalog as AI tools
  demo_page.html      The public search UI
  requirements.txt
  deploy/
    sdseed-search.service     systemd unit (uvicorn on 127.0.0.1:3002)
    sdseed-refresh.service    oneshot refresh
    sdseed-refresh.timer      weekly schedule
    install.sh                one-time server bootstrap
    sync.sh                   update running service from this checkout
```

The Caddy route lives in the site's `deploy/Caddyfile` (`/sdsb` -> `127.0.0.1:3002`).

## Architecture

- **Postgres 16 + pgvector** on the same host (localhost-only). Table
  `sdseed_products` has a `vector(1024)` embedding column + HNSW cosine index.
- **Voyage AI** `voyage-3.5` for embeddings, `rerank-2.5` for second-stage ranking.
- The service runs co-located with Postgres (`SDSEED_NO_TUNNEL=1`, direct
  `localhost:5432`). Off-server (local dev), the same code reaches the DB over an
  SSH tunnel via the `hetzner` host in `~/.ssh/config`.

## Deploy

Update flow (after editing code here and pushing):

```bash
# on the server, in the site checkout
git pull
sudo bash sdsb/deploy/sync.sh     # syncs code to /opt/sdseed, installs deps, restarts
```

`sync.sh` keeps runtime in `/opt/sdseed` (where `.env` and the venv live) so secrets
never enter the repo. First-time setup on a fresh box: `sudo bash sdsb/deploy/install.sh`.

## Secrets

`/opt/sdseed/.env` (chmod 600, owner `sdseed`) holds `VOYAGE_API_KEY` and the
`sdseed` DB credentials. It is **not** in the repo. See `install.sh` for the keys.

## Database schema

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE sdseed_products (
  id integer PRIMARY KEY, name text NOT NULL, sku text, type text,
  categories text[], primary_category text,
  price numeric(10,2), regular_price numeric(10,2), sale_price numeric(10,2),
  on_sale boolean, is_in_stock boolean, permalink text, image text,
  attributes jsonb, variations jsonb, short_description text, description text,
  embed_text text, embedding vector(1024), content_hash text,
  status text NOT NULL DEFAULT 'active', updated_at timestamptz DEFAULT now()
);
CREATE INDEX ON sdseed_products USING hnsw (embedding vector_cosine_ops);
```

## MCP server

`sdseed_mcp.py` exposes `search_products`, `keyword_search`, `get_product`, and
`list_categories` over stdio. Point a client at it with:

```json
{ "command": "python", "args": ["<path>/sdsb/sdseed_mcp.py"] }
```
