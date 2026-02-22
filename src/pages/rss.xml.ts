import type { APIContext } from 'astro';
import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export async function GET(context: APIContext) {
  const posts = await getCollection('journal');
  return rss({
    title: 'n8than.dev',
    description: 'Journal',
    site: context.site!,
    items: posts.map((post) => ({
      title: post.data.title,
      pubDate: post.data.pubDate,
      description: post.data.description,
      link: `/journal/${post.id}/`,
    })),
  });
}
