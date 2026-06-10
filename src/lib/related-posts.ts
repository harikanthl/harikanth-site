import type { CollectionEntry } from 'astro:content';

type BlogEntry = CollectionEntry<'blog'>;

export function relatedPosts(
  current: BlogEntry,
  all: BlogEntry[],
  limit = 3,
): BlogEntry[] {
  const currentTags = new Set(current.data.tags);

  return all
    .filter((post) => post.id !== current.id && !post.data.draft)
    .map((post) => {
      const overlap = post.data.tags.filter((tag) => currentTags.has(tag)).length;
      return { post, overlap };
    })
    .filter(({ overlap }) => overlap > 0)
    .sort((a, b) => b.overlap - a.overlap || b.post.data.date.getTime() - a.post.data.date.getTime())
    .slice(0, limit)
    .map(({ post }) => post);
}
