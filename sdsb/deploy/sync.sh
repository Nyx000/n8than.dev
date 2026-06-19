#!/usr/bin/env bash
# Update the running SD Seed service from this repo checkout.
# Run as root on the server after `git pull`:  sudo bash sdsb/deploy/sync.sh
set -euo pipefail

REPO_SDSB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="/opt/sdseed"
# NOTE: the first multi-source deploy needs a one-time DB migration that this
# script does NOT run — see deploy/migrations/0001_multi_source.sql and README.

echo "==> Syncing code from $REPO_SDSB -> $APP_DIR"
install -d -o sdseed -g sdseed "$APP_DIR"
for f in sources.py scrape_common.py sdseed_catalog.py shopify_catalog.py \
         sdseed_common.py load_pgvector.py refresh.py \
         search_service.py sdseed_mcp.py demo_page.html requirements.txt; do
  install -o sdseed -g sdseed -m 0644 "$REPO_SDSB/$f" "$APP_DIR/$f"
done

echo "==> Ensuring virtualenv + deps"
if [ ! -x "$APP_DIR/.venv/bin/python" ]; then
  sudo -u sdseed python3 -m venv "$APP_DIR/.venv"
fi
sudo -u sdseed "$APP_DIR/.venv/bin/pip" install --quiet --upgrade pip
sudo -u sdseed "$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

echo "==> Installing systemd units"
install -m 0644 "$REPO_SDSB/deploy/sdseed-search.service"  /etc/systemd/system/
install -m 0644 "$REPO_SDSB/deploy/sdseed-refresh.service" /etc/systemd/system/
install -m 0644 "$REPO_SDSB/deploy/sdseed-refresh.timer"   /etc/systemd/system/
systemctl daemon-reload

if [ ! -f "$APP_DIR/.env" ]; then
  echo "!! $APP_DIR/.env is missing — create it before starting (see sdsb/README.md)."
  exit 1
fi

echo "==> Restarting service + timer"
systemctl enable --now sdseed-refresh.timer >/dev/null
systemctl restart sdseed-search
sleep 2
systemctl is-active sdseed-search
curl -fsS http://127.0.0.1:3002/health && echo
echo "==> Done."
