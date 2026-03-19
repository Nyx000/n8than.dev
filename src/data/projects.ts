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
    title: 'DevPipe',
    description:
      'Feature development pipeline for Claude Code. Takes a goal from brainstorming through parallel research, structured planning, concurrent execution, and two-stage code review. Coordinates research and review sub-skills across a 7-phase pipeline.',
    tags: ['Claude Code', 'Agent Orchestration', 'Prompt Engineering'],
    expandable: true,
    details: `
      <p class="hook">The /dev skill turns Claude Code into a disciplined engineering pipeline: Intent, Brainstorm, Research, Plan, Execute, Review, and Verify. Every phase has structured outputs that feed the next.</p>
      <ul class="highlights">
        <li><strong>Two-session architecture.</strong> Research and planning consume context, then get saved to disk and wiped. Execution starts fresh with just the plan file. If context runs out mid-build, you resume from where you left off.</li>
        <li><strong>Evidence-driven verification.</strong> The system never trusts agent self-reports. Every research finding needs a file:line citation. Every review verdict references actual code. Every debug hypothesis gets a specific test.</li>
        <li><strong>Parallel execution with file ownership.</strong> Independent tasks run concurrently (up to 4), but each file is owned by exactly one task. Shared files get special handling after each batch. Zero merge conflicts by design.</li>
      </ul>
      <p class="stats">3 skills · ~1,000 lines</p>`,
  },
  {
    title: 'Sage8',
    description:
      'Eight philosophical perspectives analyzed in parallel through dedicated AI agents. Full council, single philosopher, and structured debate modes — each voice encoded with its own reasoning method, vocabulary, and blind spots.',
    tags: ['Claude Code', 'Multi-Agent', 'Philosophy', 'Prompt Engineering'],
    expandable: true,
    details: `
      <p class="hook">Eight philosophers analyze simultaneously, each with their own encoded reasoning method and voice — not summaries, but distinct intellectual perspectives.</p>
      <ul class="highlights">
        <li><strong>Voice integrity.</strong> Each philosopher has encoded biography, framework, vocabulary, reasoning method, and blind spots. Nietzsche writes aphorisms, Lao Tzu speaks in paradoxes, Sun Tzu issues strategic imperatives.</li>
        <li><strong>Three modes.</strong> Full council with roundtable synthesis, single philosopher deep-dive, or structured debate where two philosophers respond to each other across rounds.</li>
        <li><strong>Curated tension.</strong> Recommended pairings exploit genuine philosophical disagreements — Camus vs. Frankl on meaning, Nietzsche vs. Buddha on desire, Sun Tzu vs. Lao Tzu on action.</li>
      </ul>
      <p class="stats">~610 lines · 8 philosophers · 3 execution modes</p>`,
  },
  {
    title: 'CafeNightclub',
    description:
      'The project that started it all. Full-stack ordering platform built for 80+ night-shift hospital staff at Scripps Health. Real-time order tracking, push notifications, role-based access control. Ran in production Jan–Mar 2026.',
    url: 'https://cafenightclub.com',
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
    url: 'https://n8than.dev',
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
