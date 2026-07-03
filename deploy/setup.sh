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

# Bootstrap the atomic-release layout Caddy serves from (/var/www/n8than.dev/current).
echo "=== Bootstrapping release symlink ==="
mkdir -p releases
cp -a dist releases/initial
ln -s releases/initial current.tmp && mv -Tf current.tmp current

echo "=== Setting up Caddy site config ==="
mkdir -p /etc/caddy/sites

# Ensure the main Caddyfile imports site configs — APPEND, never truncate (a `>`
# here would wipe the box's security_headers snippet and cafenightclub's import).
touch /etc/caddy/Caddyfile
if ! grep -qE '^\s*import /etc/caddy/sites/\*' /etc/caddy/Caddyfile; then
  printf '\nimport /etc/caddy/sites/*\n' >> /etc/caddy/Caddyfile
  echo "Appended sites import to /etc/caddy/Caddyfile."
fi

# Staged install: back up, install, validate the assembled config, restore on failure.
SITE=/etc/caddy/sites/n8than.dev
[ -f "$SITE" ] && cp "$SITE" "$SITE.bak"
cp deploy/Caddyfile "$SITE"
if ! caddy validate --config /etc/caddy/Caddyfile; then
  [ -f "$SITE.bak" ] && mv "$SITE.bak" "$SITE"
  echo "ERROR: caddy validate failed; previous site config restored." >&2
  exit 1
fi
rm -f "$SITE.bak"
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
