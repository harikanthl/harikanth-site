import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

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

export const collections = { blog, projects, notes };
