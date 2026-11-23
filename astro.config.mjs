// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import { existsSync, readdirSync } from 'node:fs';

// /blog stays out of the sitemap while it has no post, and returns with the first one.
const BLOG_DIR = './src/data/blog';
const blogIsEmpty = !existsSync(BLOG_DIR) || readdirSync(BLOG_DIR).length === 0;

// https://astro.build/config
export default defineConfig({
  site: 'https://n8than.dev',
  integrations: [
    sitemap({
      filter: (page) => !(blogIsEmpty && new URL(page).pathname.replace(/\/$/, '') === '/blog'),
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
