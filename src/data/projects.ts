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
    tags: ['Claude Code', 'TypeScript', 'Agent Orchestration', 'CLI'],
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
        <h4>sage8</h4>
        <p>Philosophical analysis through 8 perspectives — Stoicism, Existentialism, Socratic dialogue, Strategy, Taoism, Buddhism, Logotherapy, and Absurdism.</p>
      </div>
      <div class="detail-section">
        <h4>Under the Hood</h4>
        <ul class="tech-list">
          <li>Parallel agent coordination (up to 3 concurrent)</li>
          <li>Two-stage quality gates: spec compliance + code quality</li>
          <li>File ownership boundaries prevent merge conflicts</li>
          <li>Evidence-driven — never trusts self-reports, reads actual diffs</li>
        </ul>
        <p class="stats">6 skills · 13 files · ~1,300 lines</p>
      </div>`,
  },
  {
    title: 'Cafe Nightclub',
    description:
      'Full-stack app for browsing menus and placing orders in real time, with user accounts, live updates, and a custom admin dashboard',
    url: 'https://cafenightclub.com',
    tags: ['Next.js', 'React', 'Supabase', 'Tailwind CSS'],
  },
  {
    title: 'n8than.dev',
    description: 'Personal portfolio built with Astro 5 and vanilla CSS',
    url: 'https://n8than.dev',
    tags: ['Astro', 'TypeScript', 'CSS'],
  },
];
