#!/bin/bash
set -euo pipefail

# Toggle maintenance mode for n8than.dev
# Usage: bash deploy/maintenance.sh [on|off|status]

SITE_CONFIG="/etc/caddy/sites/n8than.dev"
# Backup MUST live outside sites/ — `import /etc/caddy/sites/*` would otherwise load
# the .bak as a second n8than.dev ("ambiguous site definition").
BAK="/etc/caddy/n8than.dev.maint.bak"
APP_DIR="/var/www/n8than.dev"
CADDY_CONFIG="/etc/caddy/Caddyfile"

case "${1:-status}" in
  on)
    [ -f "$SITE_CONFIG" ] && cp "$SITE_CONFIG" "$BAK"
    cp "$APP_DIR/deploy/Caddyfile.maintenance" "$SITE_CONFIG"
    if ! caddy validate --config "$CADDY_CONFIG"; then
      [ -f "$BAK" ] && mv "$BAK" "$SITE_CONFIG"
      echo "ERROR: caddy validate failed; previous config restored." >&2
      exit 1
    fi
    rm -f "$BAK"
    systemctl reload caddy
    echo "Maintenance mode ON — n8than.dev now shows maintenance page"
    ;;
  off)
    [ -f "$SITE_CONFIG" ] && cp "$SITE_CONFIG" "$BAK"
    cp "$APP_DIR/deploy/Caddyfile" "$SITE_CONFIG"
    if ! caddy validate --config "$CADDY_CONFIG"; then
      [ -f "$BAK" ] && mv "$BAK" "$SITE_CONFIG"
      echo "ERROR: caddy validate failed; previous config restored." >&2
      exit 1
    fi
    rm -f "$BAK"
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
