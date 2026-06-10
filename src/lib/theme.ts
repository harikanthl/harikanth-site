import type { CollectionEntry } from 'astro:content';

type BlogTheme = NonNullable<CollectionEntry<'blog'>['data']['theme']>;

export const DEFAULT_POST_THEME = {
  accent: '#1d4ed8',
  paper: '#f7f3eb',
  ink: '#1c1917',
  mood: 'neutral' as const,
  headingStyle: 'sans' as const,
};

export function resolvePostTheme(theme?: BlogTheme) {
  return {
    accent: theme?.accent ?? DEFAULT_POST_THEME.accent,
    paper: theme?.paper ?? DEFAULT_POST_THEME.paper,
    ink: theme?.ink ?? DEFAULT_POST_THEME.ink,
    mood: theme?.mood ?? DEFAULT_POST_THEME.mood,
    headingStyle: theme?.headingStyle ?? DEFAULT_POST_THEME.headingStyle,
    illustration: theme?.illustration,
  };
}

/** Text colors for the hero band — always tuned for light paper backgrounds. */
export function heroTextStyle(ink: string) {
  return {
    title: ink,
    meta: `color-mix(in srgb, ${ink} 50%, transparent)`,
    description: `color-mix(in srgb, ${ink} 72%, transparent)`,
  };
}
