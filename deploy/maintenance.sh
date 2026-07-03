#!/bin/bash
set -euo pipefail

# Toggle maintenance mode for n8than.dev
# Usage: bash deploy/maintenance.sh [on|off|status]

SITE_CONFIG="/etc/caddy/sites/n8than.dev"
APP_DIR="/var/www/n8than.dev"
CADDY_CONFIG="/etc/caddy/Caddyfile"

case "${1:-status}" in
  on)
    [ -f "$SITE_CONFIG" ] && cp "$SITE_CONFIG" "$SITE_CONFIG.bak"
    cp "$APP_DIR/deploy/Caddyfile.maintenance" "$SITE_CONFIG"
    if ! caddy validate --config "$CADDY_CONFIG"; then
      [ -f "$SITE_CONFIG.bak" ] && mv "$SITE_CONFIG.bak" "$SITE_CONFIG"
      echo "ERROR: caddy validate failed; previous config restored." >&2
      exit 1
    fi
    rm -f "$SITE_CONFIG.bak"
    systemctl reload caddy
    echo "Maintenance mode ON — n8than.dev now shows maintenance page"
    ;;
  off)
    [ -f "$SITE_CONFIG" ] && cp "$SITE_CONFIG" "$SITE_CONFIG.bak"
    cp "$APP_DIR/deploy/Caddyfile" "$SITE_CONFIG"
    if ! caddy validate --config "$CADDY_CONFIG"; then
      [ -f "$SITE_CONFIG.bak" ] && mv "$SITE_CONFIG.bak" "$SITE_CONFIG"
      echo "ERROR: caddy validate failed; previous config restored." >&2
      exit 1
    fi
    rm -f "$SITE_CONFIG.bak"
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
