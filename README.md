# harikanth.site

Personal site and blog built with Astro, MDX, and Tailwind v4, deployed on Cloudflare Pages.

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

**Repo:** [github.com/harikanthl/harikanth-site](https://github.com/harikanthl/harikanth-site)  
**Pages project:** `harikanth-site` → [harikanth-site.pages.dev](https://harikanth-site.pages.dev)

### Connect GitHub (auto-deploy on push)

1. [Cloudflare Dashboard](https://dash.cloudflare.com) → **Workers & Pages** → **harikanth-site**
2. **Settings** → **Builds** → **Connect to Git**
3. Select **harikanthl/harikanth-site**, branch **main**
4. Build settings:
   - Build command: `npm run build`
   - Build output directory: `dist`
   - Environment variable: `NODE_VERSION` = `22`

### Custom domain

1. Same project → **Custom domains** → **Set up a custom domain**
2. Enter `harikanth.site` (DNS is auto-configured if the zone is on Cloudflare)
3. Optionally add `www.harikanth.site`

### Lighthouse / SEO: robots.txt

If PageSpeed reports **robots.txt is not valid**, Cloudflare is likely injecting a non-standard `Content-Signal` directive via **Managed robots.txt**.

This repo serves a clean `robots.txt` through `functions/robots.txt.ts` on Cloudflare Pages. If the audit still fails after deploy, disable the extra policy in the dashboard:

1. [Cloudflare Dashboard](https://dash.cloudflare.com) → your zone → **Security** → **Bots**
2. Under **AI Crawl Control** / **robots.txt**, turn off **Display Content Signals Policy** (or disable managed `robots.txt` if you prefer your static rules only)

See [Cloudflare managed robots.txt docs](https://developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/).

### Manual deploy (optional)

```bash
npm run build
npx wrangler pages deploy dist --project-name=harikanth-site --branch=main
```

## Stack

- Astro 6 + TypeScript
- MDX content collections
- Tailwind CSS v4
- Shiki, KaTeX, Mermaid
- Pagefind search
- View Transitions
