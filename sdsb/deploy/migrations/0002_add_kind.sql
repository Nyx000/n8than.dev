-- 0002_add_kind.sql — add the seed|plant facet to the catalog.
-- Idempotent (IF NOT EXISTS). Applied MANUALLY on the server; sync.sh does not run it.
-- Existing rows back-fill to 'seed' via the column default, which is correct
-- (the three original sources are all seed growers).

ALTER TABLE sdseed_products
    ADD COLUMN IF NOT EXISTS kind text NOT NULL DEFAULT 'seed';

CREATE INDEX IF NOT EXISTS sdseed_products_kind_idx
    ON sdseed_products (kind);
