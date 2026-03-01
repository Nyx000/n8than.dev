export interface Project {
  title: string;
  description: string;
  url: string;
  tags: string[];
  image?: string;
}

export const projects: Project[] = [
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
