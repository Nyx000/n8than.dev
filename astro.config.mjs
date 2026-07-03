// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
  site: 'https://n8than.dev',
  integrations: [sitemap()],
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
