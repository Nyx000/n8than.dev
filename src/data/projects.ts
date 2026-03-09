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
      'A custom skill system for Claude Code that orchestrates development through structured pipelines — from brainstorming through implementation to verified, reviewable results',
    tags: ['Claude Code', 'Claude Opus 4.6', 'TypeScript', 'Agent Orchestration', 'CLI'],
    expandable: true,
    details: `
      <div class="detail-section">
        <h4>The Pipeline</h4>
        <p class="pipeline">brainstorm → research → plan → execute → review → verify → finish</p>
      </div>
      <div class="detail-section">
        <h4>Skills</h4>
        <ul class="skills-list">
          <li><code>/dev</code> Full development pipeline orchestration</li>
          <li><code>/plan</code> Structured implementation planning</li>
          <li><code>/research</code> Parallel codebase exploration</li>
          <li><code>/review</code> Two-stage code review</li>
          <li><code>/debug</code> Root cause analysis</li>
        </ul>
      </div>
      <div class="detail-section">
        <h4>Under the Hood</h4>
        <ul class="tech-list">
          <li>Parallel agent coordination (up to 3 concurrent)</li>
          <li>Two-stage quality gates: spec compliance + code quality</li>
          <li>File ownership boundaries prevent merge conflicts</li>
          <li>Evidence-driven — never trusts self-reports, reads actual diffs</li>
        </ul>
        <p class="stats">5 skills · 13 files · ~1,300 lines</p>
      </div>`,
  },
  {
    title: 'CafeNightclub',
    description:
      'Full-stack ordering platform built for real clients. Real-time order tracking via WebSockets, push notifications, and an admin dashboard for managing menus, users, and operating hours. Runs on Supabase with row-level security and atomic transactions.',
    url: 'https://cafenightclub.com',
    tags: ['Next.js', 'React 19', 'Supabase', 'Tailwind CSS', 'TypeScript'],
    expandable: true,
    details: `
      <div class="detail-section">
        <h4>Features</h4>
        <ul class="skills-list">
          <li>Menu browsing with ingredient customization and whitelisted specials</li>
          <li>Database-backed cart with checkout, pickup time slots, and capacity limits</li>
          <li>Live order tracking — status updates push instantly via Supabase Realtime</li>
          <li>Admin dashboard for orders, menu, users, and operating hours</li>
          <li>Arcade games (Flappy Burger, Tendie Snake) with leaderboards</li>
          <li>Spotify integration — search, queue, and now-playing widget</li>
        </ul>
      </div>
      <div class="detail-section">
        <h4>Real-Time Architecture</h4>
        <ul class="tech-list">
          <li>Supabase Realtime WebSocket with exponential backoff retry</li>
          <li>Visibility-aware reconnection — auto-recovers when tab regains focus</li>
          <li>Silent auth token refresh prevents 1-hour expiration disconnects</li>
          <li>Push notifications via Service Worker and VAPID for order-ready alerts</li>
        </ul>
      </div>
      <div class="detail-section">
        <h4>Under the Hood</h4>
        <ul class="tech-list">
          <li>Role-based access control (user, admin, owner) with server-side checks</li>
          <li>Atomic order creation via Supabase RPC — no partial writes</li>
          <li>Row-Level Security on all tables, rate limiting on cart operations</li>
          <li>WebGL mesh gradient background responsive to club state</li>
          <li>Demo mode for portfolio showcasing without auth</li>
        </ul>
      </div>`,
  },
  {
    title: 'n8than.dev',
    description: 'Personal portfolio built with Astro 5 and vanilla CSS',
    url: 'https://n8than.dev',
    tags: ['Astro 5', 'TypeScript', 'CSS'],
    expandable: true,
    details: `
      <div class="detail-section">
        <h4>Design</h4>
        <ul class="tech-list">
          <li>Half-Life 2 inspired aesthetic — industrial orange on dark</li>
          <li>CRT scanline overlay and animated film grain via canvas</li>
          <li>Share Tech Mono display font, Outfit body, JetBrains Mono code</li>
          <li>Staggered fade-in animations with prefers-reduced-motion support</li>
        </ul>
      </div>
      <div class="detail-section">
        <h4>Built With</h4>
        <ul class="tech-list">
          <li>Astro 5 static site generation — zero client JS by default</li>
          <li>File-based routing with content collections for blog posts</li>
          <li>RSS feed and sitemap generation</li>
          <li>Vanilla CSS with custom properties — no frameworks</li>
        </ul>
      </div>`,
  },
];
