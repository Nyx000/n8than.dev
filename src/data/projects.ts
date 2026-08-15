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

export const projects: Project[] = [
  {
    title: 'Build Sheet Studio',
    description:
      'Client work for Solid Woodworx, shipped and in beta on their shop floor. They sell CNC-cut plywood drawer kits for overland vehicles through Shopify. Turning an order into a build used to mean someone reading it and working out the parts, counts, and hardware by hand. Now the order goes in and a printable build sheet comes out.',
    tags: ['Python', 'FastAPI', 'Uvicorn', 'Jinja2', 'YAML', 'pdfplumber', 'OCR'],
    expandable: true,
    details: `
      <p class="hook">The paperwork was never the hard part. The deduction behind it was. A senior builder had to know that a 4Runner generation changes the part-number series, the slide length, and the turnbuckle. Now the catalog knows.</p>
      <ul class="highlights">
        <li><strong>The engine knows nothing about drawers.</strong> Every vehicle-specific fact (parts, rules, sheet layout, provenance) lives in a versioned YAML catalog, so adding a kit means adding a file and writing no code. Nine catalogs ship today.</li>
        <li><strong>It says when it doesn't know.</strong> An order it can't fully resolve produces a gap report naming exactly what it couldn't work out, instead of a plausible guess. Two lint gates check every catalog before it ships, and the sheet renderer is locked against golden files so the printed output can't quietly drift.</li>
        <li><strong>Runs on the shop floor.</strong> Intake reads order PDFs and screenshots through one deterministic parser (pdfplumber plus platform OCR), with optional Shopify pull by order number. Delivered as source for the client to self-host: a FastAPI app they run on their own hardware, no vendor account and no dependency on me to keep it running.</li>
      </ul>
      <p class="stats">Shipped July 2026 · 9 catalogs · in shop-floor beta</p>`,
  },
  {
    title: 'Grow Tent Telemetry',
    live: true,
    description:
      'Live environmental monitoring for an automated grow tent, streaming to this site. A read-only TypeScript poller captures three climate probes into Postgres, with a deterministic alert engine, an MCP server for AI-assisted queries, and a weekly LLM advisory analyst.',
    url: '/grow',
    tags: ['TypeScript', 'Node', 'PostgreSQL', 'Drizzle ORM', 'Next.js', 'IoT', 'MCP'],
    expandable: true,
    details: `
      <p class="hook">A 24/7 telemetry stack where the hardware stays the source of truth. The controller is never written to, so every adjustment is a human decision informed by data. <a href="/grow">Watch it live →</a></p>
      <ul class="highlights">
        <li><strong>Multi-probe climate model.</strong> Canopy, lower-tent, and intake probes drive VPD targeting, stratification detection, and a night dew-point sentinel that guards against condensation.</li>
        <li><strong>Deterministic alert engine.</strong> Pure, unit-tested rules with sustain windows and reconciliation. Alerts raise and resolve from data, not vibes.</li>
        <li><strong>AI advisory layer.</strong> An MCP server exposes the tent to AI assistants, and a weekly analyst turns 30-day aggregates into reviewable recommendations. Advisory only. No write path to the hardware exists.</li>
      </ul>
      <p class="stats">10s poll cadence · live at /grow</p>`,
  },
  {
    title: 'CafeNightClub',
    live: true,
    description:
      'The project that started it all. A full-stack ordering platform built for 80+ night-shift hospital staff at Scripps Health, in production Jan–Mar 2026. It runs now as a live, cyberpunk-themed demo that is open to anyone: no sign-in, no account, just order from it.',
    url: 'https://cafenightclub.com',
    tags: ['Next.js', 'React 19', 'Supabase', 'Tailwind CSS', 'TypeScript'],
    expandable: true,
    details: `
      <p class="hook">Built to solve a real problem at my night job. 80+ registered users, real orders flowing through it every shift. This is where the architecture got tested. <a href="https://cafenightclub.com" target="_blank" rel="noopener noreferrer">Explore the live demo →</a></p>
      <ul class="highlights">
        <li><strong>Real-time order tracking.</strong> Supabase Realtime pushes status updates instantly. The connection handles tab visibility changes, exponential backoff on failure, and silent auth token refresh to prevent 1-hour expiration disconnects.</li>
        <li><strong>Atomic transactions.</strong> Order creation runs as a single Supabase RPC call. No partial writes, no race conditions between cart validation and inventory checks.</li>
        <li><strong>Row-level security everywhere.</strong> Every table has RLS policies. Role-based access (user, admin, owner) is enforced server-side, not just in the UI. Rate limiting on cart operations prevents abuse.</li>
      </ul>
      <p class="stats">Live demo at cafenightclub.com · Production Jan–Mar 2026 · 80+ users</p>`,
  },
  {
    title: 'Arenula',
    description:
      'Three MCP servers that give an AI coding assistant real hands inside the s&box game engine: manipulating scenes, compiling code, managing assets, and reading an offline type reference covering ~1,800 types and ~15,000 members.',
    tags: ['C#', 'TypeScript', 'Node', 'MCP', 'SSE', 's&box'],
    expandable: true,
    details: `
      <p class="hook">An assistant that can only write code into a file is guessing. Arenula lets it change the scene, compile, and read back what actually happened. <a href="https://nyx000.github.io/arenula-mcp/" target="_blank" rel="noopener noreferrer">Read the docs →</a></p>
      <ul class="highlights">
        <li><strong>Every write proves itself.</strong> Mutations return a <code>verified</code> read-back of engine state, so the caller can tell a real change from a silent no-op. Anything that doesn't resolve to a real engine resource errors with a usable suggestion instead of quietly doing nothing.</li>
        <li><strong>Three servers, three jobs.</strong> A C# plugin inside the s&box editor handles live scene work over SSE. Two Node servers handle the offline type reference and the narrative docs, so the expensive live connection only gets used when it has to be.</li>
        <li><strong>Written for agents to use.</strong> Omnibus tools with action enums, descriptions that say what not to do, trimmed responses, and per-field warnings when only part of a call succeeds. It follows Anthropic's guidance on writing tools for agents instead of just exposing a raw API surface.</li>
      </ul>
      <p class="stats">3 servers · ~1,800 types indexed · C# editor plugin + Node</p>`,
  },
  {
    title: 'acinfinity-ble',
    description:
      'A clean-room Bluetooth LE implementation of the AC Infinity UIS grow-controller protocol: read sensors and write settings directly, with no vendor cloud account and no network dependency. Extracted from the grow tent system above, where it has driven live hardware continuously since June 2026.',
    url: 'https://github.com/Nyx000/acinfinity-ble',
    tags: ['TypeScript', 'BLE', 'Reverse Engineering', 'Protocols', 'Node'],
    expandable: true,
    details: `
      <p class="hook">The official app mirrors everything through the vendor's cloud, and the wire protocol isn't published. This repository is that protocol, written down with its provenance, plus a tested implementation of it. <a href="https://github.com/Nyx000/acinfinity-ble" target="_blank" rel="noopener noreferrer">Read the source →</a></p>
      <ul class="highlights">
        <li><strong>Every claim carries its provenance.</strong> The protocol docs record how each finding was established, and known-unresolved items are listed as unresolved — including one capture attempt that failed, and why.</li>
        <li><strong>Verified against the vendor's own code.</strong> The frame envelope and CRC16 are confirmed bit-identical to the app's implementation across 20,000 random vectors and every captured reference frame.</li>
        <li><strong>It documents the trap.</strong> Controller settings only apply as one bundled write — a lone single-field write sends zero bytes and reports no error. That is the class of bug a unit test against your own encoder can never catch, because your encoder is correct and the device simply ignores it.</li>
      </ul>
      <p class="stats">Zero runtime dependencies · 165 tests · MIT</p>`,
  },
  {
    title: 'Claude Conformance',
    description:
      'A model-conformance layer for Claude Code. It detects installed instructions (plugin skills, agents, CLAUDE.md) that current Anthropic guidance says to remove, and injects the doctrine matching the running model at session start.',
    url: 'https://github.com/Nyx000/claude-conformance',
    tags: ['Claude Code', 'Python', 'PowerShell', 'Bash', 'Prompt Engineering'],
    expandable: true,
    details: `
      <p class="hook">Claude Code gives plugins no way to know which model they run against, so instructions written for older models quietly degrade newer ones: mandatory verification steps, standing review gates, delegate-by-default. This layer measures that drift and corrects it from the one layer that outranks every plugin. <a href="https://github.com/Nyx000/claude-conformance" target="_blank" rel="noopener noreferrer">Read the source →</a></p>
      <ul class="highlights">
        <li><strong>Classes, not plugin names.</strong> Six superseded instruction classes, each traceable to a specific line of Anthropic guidance. The scanner covers 42 instruction units across plugin caches, local skills, agents, and CLAUDE.md itself, matching on what an instruction does rather than who ships it, so plugins installed tomorrow are covered today.</li>
        <li><strong>It refuses to guess.</strong> A SessionStart hook injects the doctrine profile matching the running model and survives compaction. An unrecognized model gets an "audit needed" nudge instead of silently applied wrong rules.</li>
        <li><strong>Audits you can disagree with.</strong> A dated per-machine ledger records three verdicts: conform, deliberate override with the reason, or drift. Overrides are version-gated and expire the day upstream ships a model-aware release.</li>
      </ul>
      <p class="stats">6 instruction classes · 42 units scanned · MIT</p>`,
  },
  {
    title: 'n8than.dev',
    description: 'Personal portfolio built with Astro 5 and vanilla CSS',
    tags: ['Astro 5', 'TypeScript', 'CSS'],
    expandable: true,
    details: `
      <p class="hook">This site was designed rather than templated, and it gets run like the production systems it documents.</p>
      <ul class="highlights">
        <li><strong>Half-Life 2 aesthetic.</strong> Industrial orange on dark, a CRT scanline overlay, and an animated film-grain canvas on the homepage. Not a template.</li>
        <li><strong>Static-first, JavaScript only where it earns it.</strong> Astro ships HTML and CSS by default. The procedural hero canvas, the live /grow telemetry, and view transitions are the deliberate exceptions.</li>
        <li><strong>Run like production.</strong> An enforced Content-Security-Policy, a full security-header set, Caddy on a VPS, and CI deploys. It gets treated as infrastructure, not as a static dump.</li>
      </ul>`,
  },
];
