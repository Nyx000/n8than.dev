-- 0001_multi_source.sql
-- Migrate sdseed_products from single-source (id integer PK) to multi-source
-- (composite PK (source, source_id)). Data-preserving; HNSW index unaffected.
--
-- Apply atomically (psql wraps the whole file in one transaction):
--   psql "$CONN" --single-transaction -v ON_ERROR_STOP=1 -f 0001_multi_source.sql
-- Dry-run without persisting (validate against the live schema):
--   psql "$CONN"   then:  BEGIN; \i 0001_multi_source.sql  \d sdseed_products  ROLLBACK;
-- (No BEGIN/COMMIT inside this file so the dry-run wrapper above can ROLLBACK.)

ALTER TABLE sdseed_products RENAME COLUMN id TO source_id;
ALTER TABLE sdseed_products ALTER COLUMN source_id TYPE bigint;
ALTER TABLE sdseed_products ADD COLUMN source text;
UPDATE sdseed_products SET source = 'sandiegoseed' WHERE source IS NULL;
ALTER TABLE sdseed_products ALTER COLUMN source SET NOT NULL;
ALTER TABLE sdseed_products DROP CONSTRAINT sdseed_products_pkey;
ALTER TABLE sdseed_products ADD PRIMARY KEY (source, source_id);
