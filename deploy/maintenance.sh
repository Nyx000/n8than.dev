#!/bin/bash
set -euo pipefail

# Toggle maintenance mode for n8than.dev
# Usage: bash deploy/maintenance.sh [on|off|status]

SITE_CONFIG="/etc/caddy/sites/n8than.dev"
APP_DIR="/var/www/n8than.dev"
CADDY_CONFIG="/etc/caddy/Caddyfile"

case "${1:-status}" in
  on)
    cp "$APP_DIR/deploy/Caddyfile.maintenance" "$SITE_CONFIG"
    caddy validate --config "$CADDY_CONFIG"
    systemctl reload caddy
    echo "Maintenance mode ON — n8than.dev now shows maintenance page"
    ;;
  off)
    cp "$APP_DIR/deploy/Caddyfile" "$SITE_CONFIG"
    caddy validate --config "$CADDY_CONFIG"
    systemctl reload caddy
    echo "Maintenance mode OFF — n8than.dev is live"
    ;;
  status)
    if grep -q "maintenance.html" "$SITE_CONFIG" 2>/dev/null; then
      echo "Maintenance mode is ON"
    else
      echo "Maintenance mode is OFF"
    fi
    ;;
  *)
    echo "Usage: bash deploy/maintenance.sh [on|off|status]"
    exit 1
    ;;
esac
