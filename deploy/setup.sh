#!/bin/bash
set -euo pipefail

# =============================================================================
# One-time server setup for n8than.dev on Hetzner
# Run as root: bash deploy/setup.sh
#
# Prerequisites: Node.js, bun, and Caddy should already be installed
# (handled by cafenightclub's setup.sh or manually).
# =============================================================================

APP_DIR="/var/www/n8than.dev"

echo "=== Setting up app directory ==="
mkdir -p "$APP_DIR"

if [ ! -d "$APP_DIR/.git" ]; then
  echo "Clone your repo into $APP_DIR:"
  echo "  git clone git@github.com:Nyx000/n8than.dev.git $APP_DIR"
  echo ""
  echo "Then re-run this script."
  exit 1
fi

cd "$APP_DIR"

echo "=== Installing dependencies ==="
bun install --frozen-lockfile

echo "=== Building ==="
bun run build

echo "=== Setting up Caddy site config ==="
mkdir -p /etc/caddy/sites
cp deploy/Caddyfile /etc/caddy/sites/n8than.dev

# Ensure main Caddyfile imports site configs
if ! grep -q 'import /etc/caddy/sites/\*' /etc/caddy/Caddyfile 2>/dev/null; then
  echo 'import /etc/caddy/sites/*' > /etc/caddy/Caddyfile
  echo "Updated /etc/caddy/Caddyfile to import site configs."
  echo "WARNING: If cafenightclub config was in /etc/caddy/Caddyfile, move it to /etc/caddy/sites/cafenightclub.com"
fi

caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy

echo ""
echo "=== Setup complete ==="
echo ""
echo "Verify:"
echo "  curl -I https://n8than.dev"
echo "  caddy validate --config /etc/caddy/Caddyfile"
echo "  systemctl status caddy"
echo ""
echo "Next steps:"
echo "  1. Add GitHub secrets to Nyx000/n8than.dev: HETZNER_HOST, HETZNER_USER, HETZNER_SSH_KEY"
echo "  2. Move cafenightclub's Caddy config to /etc/caddy/sites/cafenightclub.com"
