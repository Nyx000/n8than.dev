# SeedSearch — Semantic Catalog Search

Natural-language search over seed and live-plant catalogs from curated San Diego & SoCal
seed growers and nurseries, served at [n8than.dev/seedsearch](https://n8than.dev/seedsearch). Part
of the n8than.dev monorepo so it versions and deploys alongside the site.

```
sdsb/
  sources.py          Source registry (slug, name, platform, base URL)
  scrape_common.py    Shared HTTP session + retry/backoff + HTML→text + price helpers
  sdseed_catalog.py   WooCommerce adapter: Store API -> normalized records (+ MD deliverable)
  shopify_catalog.py  Shopify adapter: products.json -> normalized records
  sdseed_common.py    Shared: .env, SSH tunnel / no-tunnel, Voyage embed + rerank, DB
  load_pgvector.py    Embed + upsert into pgvector (smart, per-source change-detection)
  refresh.py          Scrape every source -> catalog_<slug>.json -> smart-load (weekly timer)
  search_service.py   FastAPI search API + demo page (two-stage: pgvector -> rerank)
  sdseed_mcp.py       MCP server exposing the catalog as AI tools
  demo_page.html      The public search UI
  requirements.txt
  requirements-dev.txt  Dev/test deps (pytest); conftest.py + tests/ hold unit tests
  deploy/
    sdseed-search.service     systemd unit (uvicorn on 127.0.0.1:3002)
    sdseed-refresh.service    oneshot refresh
    sdseed-refresh.timer      weekly schedule
    install.sh                one-time server bootstrap
    sync.sh                   update running service from this checkout
    migrations/
      0001_multi_source.sql   one-time: single-source -> composite (source, source_id) key
```

The Caddy route lives in the site's `deploy/Caddyfile` (`/seedsearch` -> `127.0.0.1:3002`).

## Architecture

- **Postgres 16 + pgvector** on the same host (localhost-only). Table
  `sdseed_products` has a `vector(1024)` embedding column + HNSW cosine index.
- **Voyage AI** `voyage-3.5` for embeddings, `rerank-2.5` for second-stage ranking.
- The service runs co-located with Postgres (`SDSEED_NO_TUNNEL=1`, direct
  `localhost:5432`). Off-server (local dev), the same code reaches the DB over an
  SSH tunnel via the `hetzner` host in `~/.ssh/config`.

### Search response

`GET /search?q=&k=&in_stock=&category=&rerank=&kind=` returns two sections:

```json
{ "query": "...", "reranked": true,
  "counts": { "plants": 9, "seeds": 4 },
  "plants": [ ...rows... ], "seeds": [ ...rows... ] }
```

`kind` ∈ `all|plant|seed` (default `all`). Recall is kind-aware (25 candidates per kind),
then a single rerank orders the combined pool before it is split into the two sections.
Each row carries `kind` and `source_name`.

## Deploy

Update flow (after editing code here and pushing):

```bash
# on the server, in the site checkout
git pull
sudo bash sdsb/deploy/sync.sh     # syncs code to /opt/sdseed, installs deps, restarts
```

`sync.sh` keeps runtime in `/opt/sdseed` (where `.env` and the venv live) so secrets
never enter the repo. First-time setup on a fresh box: `sudo bash sdsb/deploy/install.sh`.

**First multi-source deploy (one-time):** after `git pull` and before/at the
first `sync.sh`, apply the composite-key migration once. `sync.sh` does not run
it automatically (the column renames are not safely repeatable). From the site
checkout on the server:

```bash
sudo -u sdseed bash -lc 'set -a; . /opt/sdseed/.env; set +a; \
  psql "host=127.0.0.1 port=${PGPORT:-5432} dbname=$PGDATABASE user=$PGUSER" \
  --single-transaction -v ON_ERROR_STOP=1 \
  -f sdsb/deploy/migrations/0001_multi_source.sql'
```

## Secrets

`/opt/sdseed/.env` (chmod 600, owner `sdseed`) holds `VOYAGE_API_KEY` and the
`sdseed` DB credentials. It is **not** in the repo. See `install.sh` for the keys.

## Database schema

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE sdseed_products (
  source text NOT NULL, source_id bigint NOT NULL,
  name text NOT NULL, sku text, type text,
  kind text NOT NULL DEFAULT 'seed',
  categories text[], primary_category text,
  price numeric(10,2), regular_price numeric(10,2), sale_price numeric(10,2),
  on_sale boolean, is_in_stock boolean, permalink text, image text,
  attributes jsonb, variations jsonb, short_description text, description text,
  embed_text text, embedding vector(1024), content_hash text,
  status text NOT NULL DEFAULT 'active', updated_at timestamptz DEFAULT now(),
  PRIMARY KEY (source, source_id)
);
CREATE INDEX ON sdseed_products USING hnsw (embedding vector_cosine_ops);
```

Rows are keyed by `(source, source_id)` — the store slug plus that store's native
product id. An existing single-source DB is migrated in place (no data loss) with
`deploy/migrations/0001_multi_source.sql`; see **Deploy**. The `kind` column (added
in migration `0002`) distinguishes seed from live-plant products.

### Sources

Curated to San Diego / SoCal seed growers and nurseries:

| slug | platform | store | kind |
|---|---|---|---|
| `sandiegoseed`  | woocommerce | San Diego Seed Company      | seed |
| `plantgoodseed` | shopify     | The Plant Good Seed Company | seed |
| `theodorepayne` | shopify     | Theodore Payne Foundation   | seed |
| `ricardos`  | shopify | Ricardo's Nursery | plant |
| `plantsexpress` | shopify | Plants Express | plant |
| `neelsnursery` | shopify | Neel's Nursery | plant |
| `livelyroot` | shopify | Lively Root | plant |
| `gosucculent` | woocommerce | Daniel's Specialty Nursery | plant |
| `wallaceranch` | shopify | Wallace Ranch Dragon Fruit | plant |
| `planetdesert` | shopify | Planet Desert | plant |

Add a store by appending one entry to `sources.py` (`shopify` or `woocommerce`).
A Shopify source may set an optional `collection` handle to index only that
collection's products instead of the whole store.

## MCP server

`sdseed_mcp.py` exposes `search_products`, `keyword_search`, `get_product`, and
`list_categories` over stdio. Point a client at it with:

```json
{ "command": "python", "args": ["<path>/sdsb/sdseed_mcp.py"] }
```
