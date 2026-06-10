# harikanth.site

Personal site and blog — Astro, MDX, Tailwind v4, deployed on Cloudflare Pages.

## Development

```bash
npm install
npm run dev
```

Open [http://localhost:4321](http://localhost:4321).

## Build

```bash
npm run build   # astro build + pagefind index
npm run preview
```

## Adding a blog post

1. Create `src/content/blog/your-slug.mdx`
2. Add illustrations to `public/images/blog/your-slug/`
3. Set `theme` in frontmatter (accent, paper, illustration paths)
4. See `.cursor/rules/design.md` for the full theme schema

## Deployment (Cloudflare Pages)

1. Push to GitHub
2. Connect repo in Cloudflare Pages
3. Build command: `npm run build`
4. Output directory: `dist`
5. Add custom domain `harikanth.site`
6. Enable Cloudflare Web Analytics and paste token in `BaseLayout.astro`

## Stack

- Astro 6 + TypeScript
- MDX content collections
- Tailwind CSS v4
- Shiki, KaTeX, Mermaid
- Pagefind search
- View Transitions
