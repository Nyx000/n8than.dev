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
    title: 'Claude Skills Framework',
    description:
      'A custom skill system for Claude Code that orchestrates development through structured pipelines, from brainstorming through implementation to verified, reviewable results',
    tags: ['Claude Code', 'Claude Opus 4.6', 'TypeScript', 'Agent Orchestration', 'CLI'],
    expandable: true,
    details: `
      <p class="hook">Claude Code generates code in unpredictable bursts with no quality control. This framework turns it into a disciplined engineering pipeline where every change is researched, planned, reviewed, and verified before it ships.</p>
      <ul class="highlights">
        <li><strong>Two-session architecture.</strong> Research and planning consume context, then get saved to disk and wiped. Execution starts fresh with just the plan file. If context runs out mid-build, you resume from where you left off.</li>
        <li><strong>Evidence-driven verification.</strong> The system never trusts agent self-reports. Every research finding needs a file:line citation. Every review verdict references actual code. Every debug hypothesis gets a specific test.</li>
        <li><strong>Parallel execution with file ownership.</strong> Independent tasks run concurrently (up to 3), but each file is owned by exactly one task. Shared files get special handling after each batch. Zero merge conflicts by design.</li>
      </ul>
      <p class="stats">6 skills · ~1,300 lines</p>`,
  },
  {
    title: 'Claude Job Search',
    description:
      'Open-source job search toolkit built on Claude Code. Drop in source materials, generate a verified profile and resume, then tailor application materials for each posting. Strict anti-hallucination rules prevent fabrication.',
    url: 'https://github.com/Nyx000/claude-job-search',
    tags: ['Claude Code', 'Claude Opus 4.6', 'Agent Orchestration', 'HTML/CSS', 'Open Source'],
    expandable: true,
    details: `
      <p class="hook">AI tools fabricate credentials. This one structurally can't. Every claim in your resume traces back to a source file you provided.</p>
      <ul class="highlights">
        <li><strong>Immutable fields.</strong> Names, dates, job titles, and metrics are locked at extraction. The AI rephrases around them but can never change the facts.</li>
        <li><strong>Tone spectrum.</strong> Each application adapts between assertive and humble based on role fit. A strong match gets confident language; a stretch role gets honest framing.</li>
        <li><strong>Mandatory verification pass.</strong> Before any document is presented, a separate step checks every claim against source materials. Fabricated experience gets caught and removed.</li>
      </ul>
      <p class="stats">6 skills · MIT licensed</p>`,
  },
  {
    title: 'CafeNightclub',
    description:
      'Full-stack ordering platform built for real clients. Real-time order tracking via WebSockets, push notifications, and an admin dashboard for managing menus, users, and operating hours. Runs on Supabase with row-level security and atomic transactions.',
    url: 'https://cafenightclub.com',
    tags: ['Next.js', 'React 19', 'Supabase', 'Tailwind CSS', 'TypeScript'],
    expandable: true,
    details: `
      <p class="hook">A real ordering system for real customers, not a demo. Live in production for a café with orders flowing through it.</p>
      <ul class="highlights">
        <li><strong>Real-time order tracking.</strong> Supabase Realtime pushes status updates instantly. The connection handles tab visibility changes, exponential backoff on failure, and silent auth token refresh to prevent 1-hour expiration disconnects.</li>
        <li><strong>Atomic transactions.</strong> Order creation runs as a single Supabase RPC call. No partial writes, no race conditions between cart validation and inventory checks.</li>
        <li><strong>Row-level security everywhere.</strong> Every table has RLS policies. Role-based access (user, admin, owner) is enforced server-side, not just in the UI. Rate limiting on cart operations prevents abuse.</li>
      </ul>`,
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
