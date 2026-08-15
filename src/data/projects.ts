export interface Project {
  title: string;
  description: string;
  url?: string;
  tags: string[];
  image?: string;
  expandable?: boolean;
  details?: string;
  /** Running somewhere a visitor can click through and use — a GitHub link alone doesn't count. */
  live?: boolean;
}

/**
 * Depth is deliberately uneven. The two projects with the most behind them get a
 * full detail panel; the next three get one bullet — the single non-obvious thing;
 * the last two carry everything in the description and don't expand at all.
 * Giving all seven equal airtime flattened the ranking and buried the good ones.
 */
export const projects: Project[] = [
  {
    title: 'Build Sheet Studio',
    description:
      'Client work for Solid Woodworx, delivered and paid July 2026. They sell CNC-cut plywood drawer kits for overland vehicles through Shopify, and turning an order into a build meant an experienced person deducing the parts, counts, and hardware by hand. The tool does that deduction from a versioned catalog and prints the sheet.',
    tags: ['Python', 'FastAPI', 'Uvicorn', 'Jinja2', 'YAML', 'pdfplumber', 'OCR'],
    expandable: true,
    details: `
      <p class="hook">A 4Runner generation change moves the part-number series, the slide length, and the turnbuckle. That mapping lived in one senior builder's head and on hand-maintained paper checklists. It now lives in a versioned catalog that can be diffed, linted, and reviewed.</p>
      <ul class="highlights">
        <li><strong>Adding a kit means adding a file.</strong> Every vehicle-specific fact — parts, rules, sheet layout, provenance — lives in a versioned YAML catalog. Nine catalogs ship today and none of them needed code.</li>
        <li><strong>It says when it doesn't know.</strong> An order it can't fully resolve produces a gap report naming exactly what it couldn't work out. Two lint gates check every catalog before it ships, and the sheet renderer is pinned to golden files so printed output can't quietly drift.</li>
        <li><strong>Theirs to run.</strong> Intake reads order PDFs and screenshots through one deterministic parser (pdfplumber plus platform OCR), with optional Shopify pull by order number. Handed off as source they host on their own hardware — no vendor account, no dependency on me.</li>
      </ul>
      <p class="stats">Delivered July 2026 · 9 catalogs · pilot accepted and paid</p>`,
  },
  {
    title: 'Grow Tent Telemetry',
    live: true,
    description:
      'Live environmental monitoring for an automated grow tent, streaming to this site. A read-only TypeScript poller captures three climate probes into Postgres, backed by a deterministic alert engine, an MCP server for AI-assisted queries, and a weekly LLM advisory analyst.',
    url: '/grow',
    tags: ['TypeScript', 'Node', 'PostgreSQL', 'Drizzle ORM', 'Next.js', 'IoT', 'MCP'],
    expandable: true,
    details: `
      <p class="hook">Three probes, one reading every ten seconds, running since June 2026. The controller is only ever read, never written, so every adjustment stays a human decision made with better data. <a href="/grow">Watch it live →</a></p>
      <ul class="highlights">
        <li><strong>Multi-probe climate model.</strong> Canopy, lower-tent, and intake probes drive VPD targeting, stratification detection, and a night dew-point sentinel that guards against condensation.</li>
        <li><strong>Alerts raise and resolve from data.</strong> Pure, unit-tested rules with sustain windows and reconciliation, so a brief excursion never pages and a resolved one never lingers.</li>
        <li><strong>The AI layer is advisory by construction.</strong> An MCP server exposes the tent to assistants, and a weekly analyst turns 30-day aggregates into reviewable recommendations. There is no write path to the hardware for either of them to use.</li>
      </ul>
      <p class="stats">10s poll cadence · 3 probes · read-only by design</p>`,
  },
  {
    title: 'CafeNightClub',
    live: true,
    description:
      'The project that started it all — a full-stack ordering platform I built for the 80+ night-shift staff I worked alongside at Scripps Health, in production January–March 2026 with real orders flowing through it every shift. It runs today as a cyberpunk-themed public demo: no sign-in, no account, just order from it.',
    url: 'https://cafenightclub.com',
    tags: ['Next.js', 'React 19', 'Supabase', 'Tailwind CSS', 'TypeScript'],
  },
  {
    title: 'Arenula',
    description:
      'Three MCP servers that give an AI coding assistant real hands inside the s&box game engine: manipulating scenes, compiling code, managing assets, and reading an offline type reference covering ~1,800 types and ~15,000 members.',
    tags: ['C#', 'TypeScript', 'Node', 'MCP', 'SSE', 's&box'],
    expandable: true,
    details: `
      <p class="hook">An assistant that can only write code into a file is guessing about the result. Arenula lets it change the scene, compile, and read back what actually happened. <a href="https://nyx000.github.io/arenula-mcp/" target="_blank" rel="noopener noreferrer">Read the docs →</a></p>
      <ul class="highlights">
        <li><strong>Every write proves itself.</strong> Mutations return a <code>verified</code> read-back of engine state, so the caller can tell a real change from a silent no-op. Anything that doesn't resolve to a real engine resource errors with a usable suggestion.</li>
      </ul>
      <p class="stats">3 servers · ~1,800 types indexed · C# editor plugin over SSE</p>`,
  },
  {
    title: 'acinfinity-ble',
    description:
      'A clean-room Bluetooth LE implementation of the AC Infinity UIS grow-controller protocol: read sensors and write settings directly, with no vendor cloud account and no network dependency. Extracted from the grow tent system above, where it has driven live hardware continuously since June 2026.',
    url: 'https://github.com/Nyx000/acinfinity-ble',
    tags: ['TypeScript', 'BLE', 'Reverse Engineering', 'Protocols', 'Node'],
    expandable: true,
    details: `
      <p class="hook">The wire protocol isn't published and the official app mirrors everything through the vendor's cloud. This repository is that protocol, written down with the provenance of each finding, plus a tested implementation of it. <a href="https://github.com/Nyx000/acinfinity-ble" target="_blank" rel="noopener noreferrer">Read the source →</a></p>
      <ul class="highlights">
        <li><strong>It documents the trap.</strong> Controller settings only apply as one bundled write — a lone single-field write sends zero bytes and reports no error. That is the class of bug a unit test against your own encoder can never catch, because your encoder is correct and the device simply ignores it.</li>
      </ul>
      <p class="stats">Zero runtime dependencies · 165 tests · CRC16 verified across 20,000 vectors · MIT</p>`,
  },
  {
    title: 'Claude Conformance',
    description:
      'A model-conformance layer for Claude Code. It detects installed instructions — plugin skills, agents, CLAUDE.md — that current Anthropic guidance says to remove, and injects the doctrine matching the running model at session start.',
    url: 'https://github.com/Nyx000/claude-conformance',
    tags: ['Claude Code', 'Python', 'PowerShell', 'Bash', 'Prompt Engineering'],
    expandable: true,
    details: `
      <p class="hook">Claude Code gives a plugin no way to know which model it runs against, so instructions written for older models quietly degrade newer ones: mandatory verification steps, standing review gates, delegate-by-default. This layer measures that drift and corrects it from the one layer that outranks every plugin. <a href="https://github.com/Nyx000/claude-conformance" target="_blank" rel="noopener noreferrer">Read the source →</a></p>
      <ul class="highlights">
        <li><strong>Classes, not plugin names.</strong> Six superseded instruction classes, each traceable to a specific line of Anthropic guidance. The scanner matches on what an instruction does rather than who ships it, so a plugin installed tomorrow is already covered.</li>
      </ul>
      <p class="stats">6 instruction classes · 42 units scanned · MIT</p>`,
  },
  {
    title: 'n8than.dev',
    description:
      'This site. Astro 5 and hand-written CSS, static-first with JavaScript only where it earns it — the procedural film-grain hero, the live /grow telemetry, view transitions. Enforced Content-Security-Policy and a full security-header set, on Caddy with CI deploys.',
    tags: ['Astro 5', 'TypeScript', 'CSS'],
  },
];
