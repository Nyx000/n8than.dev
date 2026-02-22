import type { APIContext } from 'astro';
import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export async function GET(context: APIContext) {
  if (!context.site) {
    return new Response('Site URL is not configured in astro.config.mjs', { status: 500 });
  }
  const posts = (await getCollection('journal')).sort(
    (a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf()
  );
  return rss({
    title: 'n8than.dev',
    description: 'Journal',
    site: context.site,
    items: posts.map((post) => ({
      title: post.data.title,
      pubDate: post.data.pubDate,
      description: post.data.description,
      link: `/journal/${post.id}/`,
    })),
  });
}
