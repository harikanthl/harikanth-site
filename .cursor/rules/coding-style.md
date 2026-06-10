# Coding Style

## TypeScript

- Strict mode enabled
- Prefer explicit types for public APIs and content schemas
- Use Zod in `content.config.ts` for all frontmatter validation

## Astro components

- Functional `.astro` components with typed `Props`
- Import shared styles in `BaseLayout` only (not every page)
- Use `class:list` for conditional classes
- Prefer `define:vars` for per-post CSS variable injection

## Accessibility

- Semantic HTML (`nav`, `article`, `main`, `time`)
- `aria-label` on navigation and icon-only controls
- Alt text required for all illustration frontmatter fields
- `prefers-reduced-motion` respected in global CSS

## Performance

- No unnecessary client islands
- Lazy-load images below the fold (`loading="lazy"`)
- Hero images use `fetchpriority="high"`
- Keep pages under 200KB transferred where possible

## Content

- Write blog posts as `.mdx` in `src/content/blog/`
- Set `draft: true` to exclude from build
- Add hand-drawn assets to `public/images/blog/{slug}/`
- Sample colors from art into `theme.accent` and `theme.paper`
