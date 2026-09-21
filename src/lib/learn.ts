import type { CollectionEntry } from 'astro:content';

export type EpisodeStatus = CollectionEntry<'dsaEpisodes'>['data']['status'];

export const STATUS_ORDER: EpisodeStatus[] = ['planned', 'prep', 'solved', 'recorded', 'uploaded'];

export const STATUS_LABEL: Record<EpisodeStatus, string> = {
  planned: 'Planned',
  prep: 'Prep ready',
  solved: 'Solved',
  recorded: 'Recorded',
  uploaded: 'Published',
};

export const DSA_REPO = 'https://github.com/harikanthl/dsa-content';

export function episodeSlug(episode: CollectionEntry<'dsaEpisodes'>): string {
  return episode.id.split('/')[1];
}

export function patternHref(patternSlug: string): string {
  return `/learn/leetcode-patterns/${patternSlug}`;
}

export function episodeHref(episode: CollectionEntry<'dsaEpisodes'>): string {
  return `${patternHref(episode.data.patternSlug)}/${episodeSlug(episode)}`;
}

export function byEpisode(a: CollectionEntry<'dsaEpisodes'>, b: CollectionEntry<'dsaEpisodes'>) {
  return a.data.ep - b.data.ep;
}

export function countStatuses(episodes: CollectionEntry<'dsaEpisodes'>[]) {
  const counts: Record<EpisodeStatus, number> = {
    planned: 0,
    prep: 0,
    solved: 0,
    recorded: 0,
    uploaded: 0,
  };
  for (const e of episodes) counts[e.data.status] += 1;
  return counts;
}

/** "Done" for the LeetCode track means recorded or beyond. */
export function doneCount(counts: Record<EpisodeStatus, number>): number {
  return counts.recorded + counts.uploaded;
}

/** Progress of a markdown checklist track: counts `- [x]` vs `- [ ]` items. */
export function checklistProgress(body: string | undefined) {
  const done = (body?.match(/^\s*[-*] \[x\]/gim) ?? []).length;
  const todo = (body?.match(/^\s*[-*] \[ \]/gm) ?? []).length;
  return { done, total: done + todo };
}
