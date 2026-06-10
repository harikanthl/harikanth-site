# Architecture

## Stack

- **Astro 6** + TypeScript (strict)
- **MDX** content via Astro Content Collections (`src/content.config.ts`)
- **Tailwind CSS v4** via `@tailwindcss/vite`
- **Shiki** for syntax highlighting (configured in `astro.config.mjs`)
- **KaTeX** via remark-math + rehype-katex
- **Pagefind** for static search (runs after `astro build`)
- **Cloudflare Pages** deployment (`wrangler.toml`, output `dist`)

## Directory layout

```
src/
  content/          # MDX collections (blog, projects, notes)
  content.config.ts # Zod schemas
  layouts/          # BaseLayout, BlogPostLayout, etc.
  components/
    shell/          # Header, Footer, Seo
    blog/           # PostCard, TOC, ReadingProgress
    editorial/      # IllustrationScene, ProjectCard
    mdx/            # Callout, Figure, Mermaid, etc.
  pages/            # File-based routing
  lib/              # seo, format, theme, reading-time
  styles/           # global.css, prose.css
public/
  images/blog/{slug}/  # Per-post hand-drawn art assets
```

## Content collections

- `blog` — posts with optional `theme` block for per-post editorial skins
- `projects` — portfolio entries with tech stack and links
- `notes` — evergreen reference pages

## Key patterns

- Site shell uses global CSS variables; per-post themes scope to `.post-skin`
- View transitions via `ClientRouter` in `BaseLayout`
- Minimal client JS — only ReadingProgress, CodeGroup tabs, Mermaid, Pagefind
- No CMS — Markdown/MDX in repo is source of truth
