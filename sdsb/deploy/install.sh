#!/usr/bin/env bash
# One-time bootstrap for the SD Seed search service on a fresh server.
# Prereqs: PostgreSQL 16 + postgresql-16-pgvector installed; an `sdseed`
# Postgres role + database with the sdseed_products table already created
# (see sdsb/README.md for the schema). Run as root:  sudo bash sdsb/deploy/install.sh
set -euo pipefail

APP_DIR="/opt/sdseed"

echo "==> Creating system user 'sdseed'"
id sdseed >/dev/null 2>&1 || useradd --system --create-home --home-dir "$APP_DIR" \
  --shell /usr/sbin/nologin sdseed
install -d -o sdseed -g sdseed "$APP_DIR"

echo "==> Ensuring python venv tooling"
apt-get install -y python3-venv >/dev/null 2>&1 || true

# Code + venv + units + start:
bash "$(dirname "${BASH_SOURCE[0]}")/sync.sh" || true

cat <<'NOTE'

Next steps if this was a fresh box:
  1. Create /opt/sdseed/.env (chmod 600, owner sdseed) with:
       VOYAGE_API_KEY=...
       PGHOST=127.0.0.1
       PGPORT=5432
       PGDATABASE=sdseed
       PGUSER=sdseed
       PGPASSWORD=...
       SDSEED_NO_TUNNEL=1
  2. Seed the catalog:  sudo -u sdseed /opt/sdseed/.venv/bin/python /opt/sdseed/refresh.py
  3. Add the /sdsb route to Caddy (already in deploy/Caddyfile of the site repo).
  4. Re-run: sudo bash sdsb/deploy/sync.sh
NOTE
