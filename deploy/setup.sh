#!/bin/bash
set -euo pipefail

# =============================================================================
# One-time server setup for n8than.dev on Hetzner
# Run as root: bash deploy/setup.sh
#
# Prerequisites: Node.js, bun, git and Caddy should already be installed.
# =============================================================================

APP_DIR="/var/www/n8than.dev"

echo "=== Setting up app directory ==="
mkdir -p "$APP_DIR"

if [ ! -d "$APP_DIR/.git" ]; then
  echo "Clone your repo into $APP_DIR:"
  echo "  git clone https://github.com/Nyx000/n8than.dev.git $APP_DIR"
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
# here would wipe whatever else the box's main Caddyfile already holds).
touch /etc/caddy/Caddyfile
if ! grep -qE '^\s*import /etc/caddy/sites/\*' /etc/caddy/Caddyfile; then
  printf '\nimport /etc/caddy/sites/*\n' >> /etc/caddy/Caddyfile
  echo "Appended sites import to /etc/caddy/Caddyfile."
fi

# Staged install: back up, install, validate the assembled config, restore on failure.
# Backup MUST live outside sites/ — `import /etc/caddy/sites/*` would otherwise load
# the .bak as a second n8than.dev ("ambiguous site definition").
SITE=/etc/caddy/sites/n8than.dev
BAK=/etc/caddy/n8than.dev.deploy.bak
[ -f "$SITE" ] && cp "$SITE" "$BAK"
cp deploy/Caddyfile "$SITE"
if ! caddy validate --config /etc/caddy/Caddyfile; then
  [ -f "$BAK" ] && mv "$BAK" "$SITE"
  echo "ERROR: caddy validate failed; previous site config restored." >&2
  exit 1
fi
rm -f "$BAK"
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
echo "  1. Add GitHub Actions secrets to Nyx000/n8than.dev: TS_OAUTH_CLIENT_ID and TS_OAUTH_SECRET"
echo "     (a Tailscale OAuth client tagged tag:ci) and HETZNER_HOST (the box's tailnet address)."
echo "     The deploy uses Tailscale SSH, so there is no SSH key or user secret."
echo "  2. In the tailnet ACL, let tag:ci reach tag:server over SSH as root."
