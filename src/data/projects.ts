export interface Project {
  title: string;
  description: string;
  url: string;
  tags: string[];
}

export const projects: Project[] = [
  {
    title: "Portfolio Site",
    description: "Personal portfolio built with Astro",
    url: "https://n8than.dev",
    tags: ["Astro", "CSS"],
  },
  {
    title: "Side Project",
    description: "A cool side project",
    url: "#",
    tags: ["TypeScript", "React"],
  },
  {
    title: "CLI Tool",
    description: "A command-line utility for automating workflows",
    url: "#",
    tags: ["Node.js", "TypeScript"],
  },
];
