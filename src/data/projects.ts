export interface Project {
  title: string;
  description: string;
  url: string;
  tags: string[];
  image?: string;
}

export const projects: Project[] = [
  {
    title: "Cafe Nightclub",
    description:
      "Website for a nightlife venue featuring events, gallery, and booking",
    url: "https://cafenightclub.com",
    tags: ["Next.js", "TypeScript", "Tailwind CSS"],
  },
  {
    title: "n8than.dev",
    description: "Personal portfolio built with Astro 5 and hand-crafted CSS",
    url: "https://n8than.dev",
    tags: ["Astro", "TypeScript", "CSS"],
  },
];
