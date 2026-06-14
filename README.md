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

### Lighthouse / SEO: robots.txt (Cloudflare zone setting)

PageSpeed may report **robots.txt is not valid** when Cloudflare injects a `Content-Signal` directive. That happens on your **custom domain** (`harikanth.site`), not on `*.pages.dev`. Cloudflare prepends managed rules at the **zone edge** before your origin file — code in this repo cannot override that merge.

Your origin `public/robots.txt` is already valid (verified on [harikanth-site.pages.dev/robots.txt](https://harikanth-site.pages.dev/robots.txt)).

**To fix the Lighthouse SEO audit on `harikanth.site`**, change a zone setting in the dashboard ([managed robots.txt docs](https://developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/)):

1. [Cloudflare Dashboard](https://dash.cloudflare.com) → select account → zone **harikanth.site**
2. **Security** → **Settings** (or go directly to **Security settings**)
3. Filter by **Bot traffic**
4. Find **Instruct AI bot traffic with robots.txt** → turn **Off**

That stops Cloudflare from prepending managed `Content-Signal` rules. Your deployed `public/robots.txt` is then served as-is.

**Optional:** If you still want AI crawler policies, use [**AI Crawl Control**](https://developers.cloudflare.com/ai-crawl-control/) (allow/block per crawler at the edge). Cloudflare notes that `robots.txt` is voluntary; AI Crawl Control enforces blocks. Managed `robots.txt` and AI Crawl Control can be used together, but managed `robots.txt` will break strict Lighthouse robots parsing until PageSpeed adopts the `Content-Signal` directive.

**Do not rely on** unchecking “Display Content Signals Policy” alone — that only removes the comment preamble; the `Content-Signal:` line remains while managed robots.txt is enabled.

After toggling, wait ~30 seconds and verify:

```bash
curl -s https://harikanth.site/robots.txt
# Should match public/robots.txt (~74 bytes), with no "BEGIN Cloudflare Managed content"
```

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
