#!/usr/bin/env bash
# Install or update the MediaMTX live relay on the Hetzner box. Idempotent.
#
# Run as root from the repo checkout on the box:
#   bash /var/www/n8than.dev/deploy/live/setup.sh
#
# The GitHub deploy workflow ships the Caddy routes for /live, not this relay:
# rerun this script whenever mediamtx.yml, mediamtx.service or the pinned
# version below changes.
set -euo pipefail

VERSION=v1.21.1
SHA256=653abc672a3e693f8d3b2717752492fdcfb8072291ec108d03d3dd857411b0ee # linux_amd64 tarball, from the release's checksums.sha256
HERE="$(cd "$(dirname "$0")" && pwd)"

id mediamtx >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin mediamtx

# Binary, pinned and checksummed. Skip the download when already on VERSION.
if ! /opt/mediamtx/mediamtx --version 2>/dev/null | grep -qx "$VERSION"; then
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  curl -fsSL -o "$tmp/mtx.tar.gz" \
    "https://github.com/bluenviron/mediamtx/releases/download/$VERSION/mediamtx_${VERSION}_linux_amd64.tar.gz"
  echo "$SHA256  $tmp/mtx.tar.gz" | sha256sum -c -
  tar -xzf "$tmp/mtx.tar.gz" -C "$tmp" mediamtx
  install -D -m 0755 "$tmp/mediamtx" /opt/mediamtx/mediamtx
fi

install -d -m 0750 -o root -g mediamtx /etc/mediamtx
install -m 0640 -o root -g mediamtx "$HERE/mediamtx.yml" /etc/mediamtx/mediamtx.yml

# Publish password: generated once, never in the repo. systemd reads the file as
# root before dropping to the mediamtx user, so it stays root-only.
if [ ! -f /etc/mediamtx/secret.env ]; then
  umask 077
  echo "MTX_AUTHINTERNALUSERS_0_PASS=$(openssl rand -hex 24)" > /etc/mediamtx/secret.env
  echo "Generated a new publish password in /etc/mediamtx/secret.env"
fi

install -m 0644 "$HERE/mediamtx.service" /etc/systemd/system/mediamtx.service
systemctl daemon-reload
systemctl enable mediamtx >/dev/null
systemctl restart mediamtx

# WebRTC media is the only new public port. 8889 (WHIP/WHEP signalling) stays
# closed on eth0: ufw's default deny covers it, and tailscale0 is already allowed.
ufw allow 8189/udp comment 'MediaMTX WebRTC ICE (n8than.dev/live)' >/dev/null

sleep 2
systemctl --no-pager --lines=8 status mediamtx
