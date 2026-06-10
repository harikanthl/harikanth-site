# Design System

## Philosophy

Apple-inspired restraint for the site shell. Each blog post gets an editorial "skin" via frontmatter — your hand-drawn illustrations set the mood.

## Typography

- **Headings & body**: Geist Sans (`--font-sans`) — Apple-style, single family
- **Code**: JetBrains Mono (`--font-mono`)
- Fluid scale via `clamp()` in `@theme`
- `text-wrap: pretty` on prose, `balance` on headings
- Prose measure: `68ch` max

## Colors (global)

- Apple-inspired warm neutrals: `#f5f5f7` surface, `#1d1d1f` ink (light); `#000` surface, `#f5f5f7` ink (dark)
- Accent: system red `#e01e37` / `#ff453a` — use sparingly for nav active, links, CTAs
- Muted: `#6e6e73` / `#86868b`
- Per-post themes override via `--post-accent` in blog skins only

## Per-post theme

```yaml
theme:
  accent: "#3d5a40"
  paper: "#f7f3eb"
  ink: "#1c1917"
  mood: warm | cool | earth | neutral
  headingStyle: serif | sans
  illustration:
    hero: /images/blog/slug/hero-scene.webp
    heroAlt: Descriptive alt text
    decor:
      - src: /images/blog/slug/bird.png
        alt: Small bird sketch
        position: top-right
        width: 140
```

## Layout principles

- Generous whitespace — let content breathe
- Vertical blog list (not card grid) on index
- Magazine-style hero band with asymmetric illustration placement
- 2px reading progress bar in post accent color
- No carousels, no heavy parallax

## Inspiration

- Karpathy / Simon Willison — writing-first, fast
- Apple product pages — typography and restraint
- Lenny's Newsletter — warm hand-drawn editorial identity per article
