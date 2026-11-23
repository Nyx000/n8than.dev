/**
 * Where a project stands. Each word is a public claim, so it has to match the record:
 *   live        running somewhere a visitor can open and use (a repo link alone doesn't count)
 *   delivered   client work, built and handed to the client; says nothing about whether it is in use
 *   maintained  public code that still gets updates
 *   retired     finished its run; the repository is archived, read-only
 */
export type ProjectStatus = 'live' | 'delivered' | 'maintained' | 'retired';

export interface Project {
  title: string;
  description: string;
  url?: string;
  tags: string[];
  kind: 'work' | 'tools';
  status: ProjectStatus;
  /** Shown beside `delivered` and `retired`. */
  statusYear?: number;
  /** Real counts only; rendered as readouts at the foot of the detail panel. */
  stats?: { label: string; value: string }[];
  /** HTML for the detail panel. A project without it does not expand. */
  details?: string;
}

export function statusLabel({ status, statusYear }: Project): string {
  return statusYear ? `${status} ${statusYear}` : status;
}

/**
 * Depth is deliberately uneven. The project with the most behind it gets a full
 * detail panel; the next few get one bullet — the single non-obvious thing; the
 * rest carry everything in the description and don't expand at all. Giving every
 * entry equal airtime flattened the ranking and buried the good ones.
 *
 * Order within a kind is the order shown; retired work goes last.
 */
export const projects: Project[] = [
  {
    title: 'Build Sheet Studio',
    kind: 'work',
    status: 'delivered',
    statusYear: 2026,
    description:
      'Client work for Solid Woodworx, delivered and paid July 2026. They sell CNC-cut plywood drawer kits for overland vehicles through Shopify, and turning an order into a build meant an experienced person deducing the parts, counts, and hardware by hand. The tool does that deduction from a versioned catalog and prints the sheet.',
    tags: ['Python', 'FastAPI', 'Uvicorn', 'Jinja2', 'YAML', 'pdfplumber', 'OCR'],
    stats: [{ label: 'Catalogs', value: '9' }],
    details: `
      <p class="hook">A 4Runner generation change moves the part-number series, the slide length, and the turnbuckle. That mapping lived in one senior builder's head and on hand-maintained paper checklists. It now lives in a versioned catalog that can be diffed, linted, and reviewed.</p>
      <ul class="highlights">
        <li><strong>Adding a kit means adding a file.</strong> Every vehicle-specific fact — parts, rules, sheet layout, provenance — lives in a versioned YAML catalog. Nine catalogs ship today and none of them needed code.</li>
        <li><strong>It says when it doesn't know.</strong> An order it can't fully resolve produces a gap report naming exactly what it couldn't work out. Two lint gates check every catalog before it ships, and the sheet renderer is pinned to golden files so printed output can't quietly drift.</li>
        <li><strong>Built to be self-hosted.</strong> Intake reads order PDFs and screenshots through one deterministic parser (pdfplumber plus platform OCR), with optional Shopify pull by order number. Handed over as source, built to run on their own hardware with no vendor account and no dependency on me.</li>
      </ul>`,
  },
  {
    title: 'CafeNightClub',
    kind: 'work',
    status: 'live',
    description:
      'A full-stack ordering platform I built for the 80+ night-shift staff I worked alongside at Scripps Health, in production January–March 2026 with real orders flowing through it every shift. It runs today as a public demo: no sign-in, no account, just order from it.',
    url: 'https://cafenightclub.com',
    tags: ['Next.js', 'React 19', 'Supabase', 'Tailwind CSS', 'TypeScript'],
  },
  {
    title: 'Claude Conformance',
    kind: 'tools',
    status: 'maintained',
    description:
      'A model-conformance layer for Claude Code. It detects installed instructions — plugin skills, agents, CLAUDE.md — that current Anthropic guidance says to remove, and injects the doctrine matching the running model at session start. MIT licensed.',
    url: 'https://github.com/Nyx000/claude-conformance',
    tags: ['Claude Code', 'Python', 'PowerShell', 'Bash', 'Prompt Engineering'],
    stats: [{ label: 'Instruction classes', value: '7' }],
    details: `
      <p class="hook">Claude Code gives a plugin no way to know which model it runs against, so instructions written for older models quietly degrade newer ones: mandatory verification steps, standing review gates, delegate-by-default. This layer measures that drift and corrects it from the one layer that outranks every plugin. <a href="https://github.com/Nyx000/claude-conformance" target="_blank" rel="noopener noreferrer">Read the source</a></p>
      <ul class="highlights">
        <li><strong>Classes, not plugin names.</strong> Seven superseded instruction classes, each traceable to a specific line of Anthropic guidance. The scanner matches on what an instruction does rather than who ships it, so a plugin installed tomorrow is already covered.</li>
      </ul>`,
  },
  {
    title: 'WarmupTS',
    kind: 'tools',
    status: 'maintained',
    description:
      "A TypeScript framework for Counter-Strike 2 gamemodes written with Valve's cs_script. The engine lets a script register each callback only once; WarmupTS registers all of them and hands every event to every plugin, so a headshot rule and a weapon ladder can both react to the same kill without knowing about each other. Plugins hot-reload in the local game client, and the built script runs on Windows and Linux dedicated servers. Early, MIT.",
    url: 'https://github.com/Nyx000/warmup-ts',
    tags: ['TypeScript', 'Bun', 'CS2', 'cs_script'],
  },
  {
    title: 'n8than.dev',
    kind: 'tools',
    status: 'live',
    description:
      'This site. Astro 7 and hand-written CSS, static-first with JavaScript only where it earns it — the procedural film-grain hero, view transitions. Enforced Content-Security-Policy and a full security-header set, on Caddy on a Hetzner VPS with CI deploys.',
    tags: ['Astro 7', 'TypeScript', 'CSS'],
  },
  {
    title: 'acinfinity-ble',
    kind: 'tools',
    status: 'retired',
    statusYear: 2026,
    description:
      'A clean-room Bluetooth LE implementation of the AC Infinity UIS grow-controller protocol: read sensors and write settings directly, with no vendor cloud account and no network dependency. Extracted from my grow tent system, where it drove live hardware from June to October 2026. The project is finished and the repository is archived, read-only. MIT licensed.',
    url: 'https://github.com/Nyx000/acinfinity-ble',
    tags: ['TypeScript', 'BLE', 'Reverse Engineering', 'Protocols', 'Node'],
    stats: [
      { label: 'Tests', value: '165' },
      { label: 'CRC vectors', value: '20,000' },
      { label: 'Runtime dependencies', value: '0' },
    ],
    details: `
      <p class="hook">The wire protocol isn't published and the official app mirrors everything through the vendor's cloud. This repository is that protocol, written down with the provenance of each finding, plus a tested implementation of it. <a href="https://github.com/Nyx000/acinfinity-ble" target="_blank" rel="noopener noreferrer">Read the source</a></p>
      <ul class="highlights">
        <li><strong>It documents the trap.</strong> Controller settings only apply as one bundled write — a lone single-field write sends zero bytes and reports no error. That is the class of bug a unit test against your own encoder can never catch, because your encoder is correct and the device simply ignores it.</li>
      </ul>`,
  },
  {
    title: 'Arenula',
    kind: 'tools',
    status: 'retired',
    statusYear: 2026,
    description:
      'MCP tooling for the s&box game engine, built three months before the engine shipped its own. Three servers gave an AI coding assistant real hands inside the editor: manipulating scenes, compiling code, managing assets, and reading an offline type reference covering ~1,800 types and ~15,000 members. Retired November 2026; the repository is archived.',
    url: 'https://github.com/Nyx000/arenula-mcp',
    tags: ['C#', 'TypeScript', 'Node', 'MCP', 'SSE', 's&box'],
    stats: [
      { label: 'Servers', value: '3' },
      { label: 'Types indexed', value: '~1,800' },
    ],
    details: `
      <p class="hook">An assistant that can only write code into a file is guessing about the result. Arenula let it change the scene, compile, and read back what actually happened. <a href="https://nyx000.github.io/arenula-mcp/" target="_blank" rel="noopener noreferrer">Read the docs</a></p>
      <ul class="highlights">
        <li><strong>Every write proved itself.</strong> Mutations returned a <code>verified</code> read-back of engine state, so the caller could tell a real change from a silent no-op. Anything that didn't resolve to a real engine resource errored with a usable suggestion.</li>
      </ul>`,
  },
];
