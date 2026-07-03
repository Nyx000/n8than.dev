// Generates public/og-default.png (1200×630) — the default social share card.
// On-brand: Half-Life 2 palette, a pixel Citadel skyline band, orange sun glow,
// faint λ watermark, and the wordmark. Run: `bun scripts/make-og.mjs`
// One-shot build asset; re-run only if the brand card should change.
import sharp from 'sharp';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const out = resolve(__dirname, '../public/og-default.png');

const W = 1200;
const H = 630;
const bg = '#0a0a0a';
const accent = '#ff6600';
const text = '#d4d0c8';
const muted = '#8a8a92';

// λ glyph (Half-Life lambda) from the site's hero, used as a faint watermark.
const lambda =
  'M47.243238 12.929372v25.907582h21.335657l8.762858 27.050564-65.14995 100.963372h32.003485l46.48125-68.578894 30.479512 76.960764 48.00522-15.23976-7.61987-23.62162-22.09765 6.85789L87.628587 12.929372H47.243238z';

// Skyline: a row of silhouetted buildings + one tall Citadel tower with a red beacon.
const groundY = 470;
const buildings = [
  [40, 90, 70],
  [140, 60, 110],
  [210, 110, 60],
  [330, 70, 95],
  [410, 95, 55],
  [520, 60, 130],
  [600, 130, 70],
  [740, 80, 100],
  [830, 60, 60],
  [900, 110, 85],
  [1020, 70, 120],
  [1100, 100, 65],
];
const bars = buildings
  .map(([x, w, h]) => `<rect x="${x}" y="${groundY - h}" width="${w}" height="${h + 30}" fill="#050505"/>`)
  .join('');

// The Citadel: a tall narrow tower rising above the skyline with a red beacon.
const citadel = `
  <rect x="270" y="150" width="34" height="${groundY - 150 + 30}" fill="#060606"/>
  <rect x="278" y="130" width="18" height="24" fill="#0a0a0a" stroke="#161616" stroke-width="1"/>
  <rect x="283" y="120" width="8" height="14" fill="#b3404a"/>
`;

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <defs>
    <radialGradient id="sun" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="${accent}" stop-opacity="0.85"/>
      <stop offset="45%" stop-color="${accent}" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="${accent}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="haze" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1a0f04" stop-opacity="0"/>
      <stop offset="100%" stop-color="#1f1206" stop-opacity="0.9"/>
    </linearGradient>
    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="2" fill="#000000" fill-opacity="0"/>
      <rect y="2" width="4" height="2" fill="#000000" fill-opacity="0.18"/>
    </pattern>
  </defs>

  <rect width="${W}" height="${H}" fill="${bg}"/>

  <!-- sun glow behind the skyline, right of centre (echoes the homepage hero) -->
  <circle cx="880" cy="470" r="300" fill="url(#sun)"/>
  <rect x="0" y="300" width="${W}" height="200" fill="url(#haze)"/>

  <!-- faint λ watermark, far right -->
  <g transform="translate(980,150) scale(1.9)" fill="${accent}" fill-opacity="0.06">
    <path d="${lambda}"/>
  </g>

  ${bars}
  ${citadel}

  <!-- scanline overlay -->
  <rect width="${W}" height="${H}" fill="url(#scan)"/>

  <!-- wordmark + tagline -->
  <text x="80" y="250" font-family="'Share Tech Mono','Consolas','DejaVu Sans Mono',monospace" font-size="110" fill="${accent}" letter-spacing="2">n8than.dev</text>
  <rect x="84" y="278" width="150" height="4" fill="${accent}"/>
  <text x="86" y="330" font-family="'Outfit','Segoe UI','DejaVu Sans',sans-serif" font-size="40" fill="${text}">software engineer — san diego</text>
  <text x="86" y="384" font-family="'Share Tech Mono','Consolas','DejaVu Sans Mono',monospace" font-size="26" fill="${muted}"># i build software people actually use</text>
</svg>`;

await sharp(Buffer.from(svg)).png().toFile(out);
console.log('wrote', out);
