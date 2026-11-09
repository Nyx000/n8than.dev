# n8than.dev

Source for [n8than.dev](https://n8than.dev), the portfolio site of Nyx000: projects, an about page,
and a page of thank-you notes from a previous job. It is a static site, built with Astro and served
by Caddy from a Hetzner VPS.

## Routes

| Path                                            | Content                                                            |
| ----------------------------------------------- | ------------------------------------------------------------------ |
| `/`                                             | Home                                                               |
| `/projects`                                     | Project cards, from `src/data/projects.ts`                         |
| `/recognition`                                  | Thank-you notes, from `src/data/testimonials.ts`                   |
| `/about`                                        | About, skills, links                                               |
| `/blog`                                         | Blog index; no posts are published yet, so it shows an empty state |
| `/rss.xml`, `/sitemap-index.xml`, `/resume.pdf` | Feed, sitemap, résumé                                              |

`/api/*`, `/swx-demo*`, `/hub*`, `/seedsearch*` and `/sdsb*` belonged to features that have been
retired. `deploy/Caddyfile` answers all of them with the styled 404 page.

## Stack

- Astro 7.4 with `@astrojs/sitemap` and `@astrojs/rss`, TypeScript 5.9, hand-written CSS
- Bun for installs and scripts
- Fonts (Outfit, JetBrains Mono, Share Tech Mono) are self-hosted through `@fontsource`
- Prettier with `prettier-plugin-astro`

## Run it locally

```sh
bun install
bun run dev            # dev server
bun run build          # static output in dist/
bun run preview        # serve the built site
bun run check          # astro check (types)
bun run format:check   # prettier --check; `bun run format` writes
```

## Deploys

Every push to `main` runs `.github/workflows/deploy.yml`. Only one deploy runs at a time, and a
running deploy is never cancelled.

1. The runner joins the tailnet as an ephemeral node tagged `tag:ci`, using a Tailscale OAuth
   client. The box runs no OpenSSH and its public port 22 is closed; the runner reaches it over
   Tailscale SSH, authorized by tailnet identity, so the repo holds no SSH key.
2. On the box: `git pull`, `bun install --frozen-lockfile`, `bun run build`.
3. The build is copied to `releases/<timestamp>-<commit>`, and the `current` symlink is switched to
   it with `ln -s` plus `mv -Tf`, so the served site changes in one atomic step. Caddy serves
   `current`, never `dist`.
4. The three newest releases are kept. Rolling back means pointing `current` at an earlier one.
5. `deploy/Caddyfile` is copied over the box's site file and checked with `caddy validate`. If
   validation fails, the previous file is restored and the deploy fails; otherwise Caddy is
   reloaded.

`deploy/setup.sh` is the one-time server bootstrap. `deploy/maintenance.sh on|off|status` swaps in a
maintenance page, and the deploy leaves the Caddy config alone while that is active.

The workflow needs three repository secrets: `TS_OAUTH_CLIENT_ID`, `TS_OAUTH_SECRET` and
`HETZNER_HOST`.

## Security decisions

All of these are in `deploy/Caddyfile`.

- **Content-Security-Policy:** `default-src 'self'` with `script-src 'self'`, `font-src 'self'`,
  `connect-src 'self'`, `img-src 'self' data:`, `object-src 'none'`, `frame-ancestors 'self'`,
  `form-action 'self'` and `base-uri 'self'`. There is no inline script and no third-party host.
  `style-src` still allows `'unsafe-inline'`, because Astro inlines small stylesheets and the
  view-transition router injects styles.
- **No inline scripts by construction:** `assetsInlineLimit: 0` in `astro.config.mjs` forces every
  bundled script into a hashed file under `/_astro`.
- **Headers:** HSTS with `includeSubDomains`, `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: SAMEORIGIN`, a strict-origin-when-cross-origin referrer policy, and a
  Permissions-Policy that disables geolocation, microphone and camera. `Server` and `Via` are
  stripped. The headers are also set on 404 and 5xx responses, which Caddy treats as a separate code
  path.
- **Redirects:** HTTP goes to HTTPS and `www` goes to the apex in a single hop.
- **Caching:** files under `/_astro/` are content-hashed and cached as immutable; unhashed images
  and fonts are cached for a day; the résumé revalidates hourly; everything else is `no-cache`.
- **Disclosure:** `/.well-known/security.txt` lists a contact address.
