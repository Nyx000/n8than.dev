// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// /kit is unlinked until the pages are rebuilt from it; list it then.
const HIDDEN_FROM_SITEMAP = ['/blog/', '/kit/'];

// https://astro.build/config
export default defineConfig({
  site: 'https://n8than.dev',
  // /blog is empty until a first post exists; drop it from this list then.
  integrations: [
    sitemap({
      filter: (page) => !HIDDEN_FROM_SITEMAP.includes(new URL(page).pathname),
    }),
  ],
  // assetsInlineLimit: 0 forces every bundled script out to a hashed /_astro file
  // instead of being inlined into the HTML, so the CSP can drop script-src
  // 'unsafe-inline' (infra WS9 Flip A). Acceptance: no inline `<script type="module">`
  // survives in dist/**/*.html.
  vite: {
    build: {
      assetsInlineLimit: 0,
    },
  },
});
