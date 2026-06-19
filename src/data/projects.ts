export interface Project {
  title: string;
  description: string;
  url?: string;
  tags: string[];
  image?: string;
  expandable?: boolean;
  details?: string;
}

export const projects: Project[] = [
  {
    title: 'SeedSearch — Semantic Catalog Search',
    description:
      'Natural-language search across catalogs from three San Diego & SoCal seed growers. Describe a garden in plain English — "low-water flowers for pollinators" — and the right seeds surface from ~1,000 varieties, ranked by meaning. Built on pgvector + Voyage AI, with an MCP server and a self-maintaining ingest pipeline.',
    url: '/seedsearch',
    tags: ['Python', 'FastAPI', 'PostgreSQL', 'pgvector', 'Voyage AI', 'MCP', 'Caddy'],
    expandable: true,
    details: `
      <p class="hook">Keyword search makes you know the variety name. This doesn't: it reads what you mean and finds the seeds that fit. <a href="/seedsearch">Try it live →</a></p>
      <ul class="highlights">
        <li><strong>Two-stage retrieval.</strong> pgvector runs an approximate-nearest-neighbor recall over Voyage embeddings, then rerank-2.5 re-reads your full request against the finalists for precision. A live toggle lets you feel the reranker reorder results.</li>
        <li><strong>Self-maintaining catalog.</strong> A polite scraper pulls live WooCommerce and Shopify product feeds across three SoCal seed growers, a content-hash diff re-embeds only what actually changed, vanished products are retired, and a weekly systemd timer keeps it current — at near-zero embedding cost.</li>
        <li><strong>Two front doors, one engine.</strong> The same vector store powers a public search UI and an MCP server that exposes the catalog as tools (search, lookup, categories) to any AI assistant.</li>
      </ul>
      <p class="stats">~1,000 varieties · 3 SoCal seed growers · voyage-3.5 + rerank-2.5 · live at /seedsearch</p>`,
  },
  {
    title: 'Grow Tent Telemetry',
    description:
      'Live environmental monitoring for an automated grow tent — and it streams to this site. A read-only TypeScript poller captures three climate probes into Postgres, with a deterministic alert engine, an MCP server for AI-assisted queries, and a weekly LLM advisory analyst.',
    url: '/grow',
    tags: ['TypeScript', 'Node', 'PostgreSQL', 'Drizzle ORM', 'Next.js', 'IoT', 'MCP'],
    expandable: true,
    details: `
      <p class="hook">A 24/7 telemetry stack where the hardware is the source of truth: the controller is never written to — every adjustment is a human decision informed by data. <a href="/grow">Watch it live →</a></p>
      <ul class="highlights">
        <li><strong>Multi-probe climate model.</strong> Canopy, lower-tent, and intake probes drive VPD targeting, stratification detection, and a night dew-point sentinel that guards against condensation.</li>
        <li><strong>Deterministic alert engine.</strong> Pure, unit-tested rules with sustain windows and reconciliation — alerts raise and resolve from data, not vibes.</li>
        <li><strong>AI advisory layer.</strong> An MCP server exposes the tent to AI assistants, and a weekly analyst turns 30-day aggregates into reviewable recommendations. Advisory only — no write path to hardware exists.</li>
      </ul>
      <p class="stats">180+ tests · 10s poll cadence · live at /grow</p>`,
  },
  {
    title: 'OrderKit',
    description:
      'Self-hosted ordering platform for small venues. Extracted from CafeNightClub, rebuilt with a modern self-contained stack: Next.js 16, SQLite, Drizzle ORM, and Docker. No cloud dependencies, no vendor lock-in.',
    tags: ['Next.js 16', 'React', 'SQLite', 'Drizzle ORM', 'Bun', 'Docker', 'TypeScript'],
    expandable: true,
    details: `
      <p class="hook">CafeNightClub proved the concept. OrderKit is the product: a self-hosted ordering platform that any small venue can deploy with a single Docker command.</p>
      <ul class="highlights">
        <li><strong>Cloud-free by design.</strong> SQLite replaces Supabase, better-auth replaces cloud auth, Server-Sent Events replace WebSockets. The entire system runs on one VPS with no external service dependencies.</li>
        <li><strong>Venue-agnostic.</strong> Refactored all "club" terminology to "venue." Configurable operating hours, pickup slots, menu categories, and capacity limits adapt to any food service operation.</li>
        <li><strong>Docker-first deployment.</strong> Multi-stage Dockerfile, docker-compose with optional Caddy sidecar, and a demo mode that lets the app run as a portfolio piece.</li>
      </ul>
      <p class="stats">v0.1.0 · MIT licensed · Active development</p>`,
  },
  {
    title: 'Sage8',
    description:
      'Eight philosophical perspectives analyzed in parallel through dedicated AI agents. Full council, single philosopher, and structured debate modes, each voice encoded with its own reasoning method, vocabulary, and blind spots.',
    tags: ['Claude Code', 'Multi-Agent', 'Philosophy', 'Prompt Engineering'],
    expandable: true,
    details: `
      <p class="hook">Eight philosophers analyze simultaneously, each with their own encoded reasoning method and voice. Not summaries, but distinct intellectual perspectives.</p>
      <ul class="highlights">
        <li><strong>Voice integrity.</strong> Each philosopher has encoded biography, framework, vocabulary, reasoning method, and blind spots. Nietzsche writes aphorisms, Lao Tzu speaks in paradoxes, Sun Tzu issues strategic imperatives.</li>
        <li><strong>Three modes.</strong> Full council with roundtable synthesis, single philosopher deep-dive, or structured debate where two philosophers respond to each other across rounds.</li>
        <li><strong>Curated tension.</strong> Recommended pairings exploit genuine philosophical disagreements like Camus vs. Frankl on meaning, Nietzsche vs. Buddha on desire, and Sun Tzu vs. Lao Tzu on action.</li>
      </ul>
      <p class="stats">~610 lines · 8 philosophers · 3 execution modes</p>`,
  },
  {
    title: 'CafeNightclub',
    description:
      'The project that started it all. Full-stack ordering platform built for 80+ night-shift hospital staff at Scripps Health. Real-time order tracking, push notifications, role-based access control. Ran in production Jan–Mar 2026.',
    tags: ['Next.js', 'React 19', 'Supabase', 'Tailwind CSS', 'TypeScript'],
    expandable: true,
    details: `
      <p class="hook">Built to solve a real problem at my night job. 80+ registered users, real orders flowing through it every shift. This is where the architecture was battle-tested.</p>
      <ul class="highlights">
        <li><strong>Real-time order tracking.</strong> Supabase Realtime pushes status updates instantly. The connection handles tab visibility changes, exponential backoff on failure, and silent auth token refresh to prevent 1-hour expiration disconnects.</li>
        <li><strong>Atomic transactions.</strong> Order creation runs as a single Supabase RPC call. No partial writes, no race conditions between cart validation and inventory checks.</li>
        <li><strong>Row-level security everywhere.</strong> Every table has RLS policies. Role-based access (user, admin, owner) is enforced server-side, not just in the UI. Rate limiting on cart operations prevents abuse.</li>
      </ul>
      <p class="stats">Predecessor to OrderKit · Production Jan–Mar 2026 · 80+ users</p>`,
  },
  {
    title: 'n8than.dev',
    description: 'Personal portfolio built with Astro 5 and vanilla CSS',
    tags: ['Astro 5', 'TypeScript', 'CSS'],
    expandable: true,
    details: `
      <p class="hook">A portfolio that practices what it preaches. Static by default, zero client JavaScript, built with the same attention to craft it showcases.</p>
      <ul class="highlights">
        <li><strong>Half-Life 2 aesthetic.</strong> Industrial orange on dark, CRT scanline overlay, animated film grain via canvas. Not a template.</li>
        <li><strong>Zero JS by default.</strong> Astro 5 ships pure HTML/CSS. Interactive bits hydrate only where needed.</li>
        <li><strong>Content collections.</strong> Journal posts live in markdown with type-safe frontmatter. RSS feed and sitemap generate automatically.</li>
      </ul>`,
  },
];
