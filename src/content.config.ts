import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';
import { dsaEpisodesLoader, dsaPatternsLoader } from './loaders/dsa';

const decorPosition = z.enum([
  'top-left',
  'top-right',
  'bottom-left',
  'bottom-right',
  'inline',
]);

const themeSchema = z
  .object({
    accent: z.string(),
    paper: z.string().optional(),
    ink: z.string().optional(),
    mood: z.enum(['warm', 'cool', 'earth', 'neutral']).default('neutral'),
    headingStyle: z.enum(['serif', 'sans']).default('serif'),
    illustration: z
      .object({
        hero: z.string().optional(),
        heroAlt: z.string().optional(),
        decor: z
          .array(
            z.object({
              src: z.string(),
              alt: z.string(),
              position: decorPosition,
              width: z.number().optional(),
            }),
          )
          .optional(),
      })
      .optional(),
  })
  .optional();

const blog = defineCollection({
  loader: glob({ base: './src/content/blog', pattern: '**/*.{md,mdx}' }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    description: z.string(),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
    featured: z.boolean().default(false),
    theme: themeSchema,
  }),
});

const projects = defineCollection({
  loader: glob({ base: './src/content/projects', pattern: '**/*.{md,mdx}' }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    description: z.string(),
    tags: z.array(z.string()).default([]),
    featured: z.boolean().default(false),
    tech: z.array(z.string()).default([]),
    github: z.string().url().optional(),
    demo: z.string().url().optional(),
    image: z.string().optional(),
    imageFit: z.enum(['cover', 'contain']).default('cover'),
    writeup: z.string().optional(),
  }),
});

const notes = defineCollection({
  loader: glob({ base: './src/content/notes', pattern: '**/*.{md,mdx}' }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    description: z.string(),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

const episodeStatus = z.enum(['planned', 'prep', 'solved', 'recorded', 'uploaded']);

// Learn-in-public tracks: one markdown file per course/series in src/content/tracks.
const tracks = defineCollection({
  loader: glob({ base: './src/content/tracks', pattern: '**/*.{md,mdx}' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    order: z.number(),
    status: z.enum(['planned', 'active', 'done']).default('planned'),
    source: z.string().url().optional(),
    sourceLabel: z.string().optional(),
    started: z.coerce.date().optional(),
    // Set for the track whose pages are generated from external data.
    dataDriven: z.boolean().default(false),
  }),
});

// LeetCode patterns: generated from the dsa-content submodule (see src/loaders/dsa.ts).
const dsaEpisodes = defineCollection({
  loader: dsaEpisodesLoader(),
  schema: z.object({
    ep: z.number(),
    code: z.string(),
    title: z.string(),
    difficulty: z.string().optional(),
    pattern: z.string(),
    patternSlug: z.string(),
    patternNo: z.number(),
    patternEp: z.number(),
    links: z.array(z.string()),
    status: episodeStatus,
    published: z.boolean(),
    youtubeUrl: z.string().optional(),
    youtubeId: z.string().optional(),
    reps: z.number(),
    solution: z.string().optional(),
    solutionPath: z.string(),
    prepPath: z.string(),
  }),
});

const dsaPatterns = defineCollection({
  loader: dsaPatternsLoader(),
  schema: z.object({
    no: z.number(),
    title: z.string(),
    folder: z.string(),
    episodeCount: z.number(),
    epStart: z.number(),
    epEnd: z.number(),
    counts: z.record(episodeStatus, z.number()),
    hasCard: z.boolean(),
  }),
});

export const collections = { blog, projects, notes, tracks, dsaEpisodes, dsaPatterns };
