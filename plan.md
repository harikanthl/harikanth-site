Since your goal is **credibility + discoverability + getting hired**, I'd optimize for:

* Fast loading
* Beautiful typography
* Writing-focused
* Easy to maintain
* SEO-friendly
* Deployable free on Cloudflare
* Markdown-based (so Cursor can generate content easily)
* Projects + blogs + resume in one place

Think:

* Karpathy's blog
* Simon Willison
* Sebastian Raschka
* Jay Alammar
* Andrej's style
* Paul Graham essays
* Simple, content-first websites

---

# Recommended Stack

## Frontend

### Astro + TypeScript

Why Astro?

* Extremely fast
* Great SEO
* Markdown native
* Content collections
* Syntax highlighting
* RSS feeds
* Zero JS by default
* Easy Cloudflare deployment

Directory:

```
harikanth.site/

src/
  pages/
  layouts/
  components/
  content/
      blog/
      projects/
      notes/
      talks/
public/
```

---

## Styling

### Tailwind CSS v4

Keep it minimal:

Typography:

* Inter
* Geist
* IBM Plex Sans

Code font:

* JetBrains Mono

Color palette:

```css
background: #fafafa
text: #111827

accent:
emerald
indigo
slate
```

Dark mode:

```css
bg-zinc-950
text-zinc-100
```

---

# Content Source

## Markdown (.mdx)

Write everything as markdown:

```
content/

blog/
  flash-attention-explained.mdx
  gpu-kernels-notes.mdx

projects/
  mandiledger.mdx
  vireeel.mdx
  farmdots.mdx

notes/
  transformer-notes.mdx
  pytorch-notes.mdx

resume/
```

Cursor can generate and edit these easily.

---

# Blog Engine

Astro Content Collections

Frontmatter:

```yaml
---
title:
date:
description:
tags:
draft:
---
```

Features:

* Tags
* Search
* Related posts
* Reading time
* Table of contents
* RSS feed

---

# Code Highlighting

Shiki

Supports:

* Python
* CUDA
* Triton
* TypeScript
* Bash

Perfect for GPU blogs.

---

# Image Hosting

Cloudflare R2

Store:

```
/images/blog/
/images/projects/
```

Cheap and scalable.

---

# Analytics

### Cloudflare Web Analytics

No cookies.

Shows:

* Visitors
* Referrers
* Countries
* Top pages

---

# Comments

Skip comments initially.

Use:

* Twitter/X
* LinkedIn discussions

instead.

---

# Search

Pagefind

Static search.

No backend needed.

---

# Deployment

Cloudflare Pages

GitHub →

```
main
   ↓
Cloudflare Pages
```

Every push redeploys automatically.

Cost:

Free.

---

# Project Showcase Structure

```
Projects

MandiLedger
-------------
Offline-first farm accounting app.

Tech:
Expo
SQLite
Cloudflare D1

Blog →
Github →

--------------------------------

Vireeel
--------
AI UGC ad generator

Tech:
Next.js
FastAPI
Gemini

--------------------------------

FarmDots
---------
Digital twin for farms

Tech:
MapLibre
PMTiles
Cloudflare Workers
```

---

# Resume

Generate automatically from markdown.

Buttons:

```
Resume (PDF)

LinkedIn

GitHub

Email
```

Single page.

---

# Essential Pages

### Home

Hero:

```
Harikanth Lingutla

AI/ML Engineer • Veteran • Builder

I build practical AI systems,
GPU projects and software tools.

Currently learning PyTorch, Triton,
CUDA and building AI products.
```

Featured:

* Latest blogs
* Featured projects
* Resume

---

### Blog

Reverse chronological.

Tags:

```
Deep Learning
CUDA
PyTorch
GPU Kernels
Leetcode
System Design
AI Agents
```

---

### Projects

Cards with:

* Screenshot
* Tech stack
* Demo
* Github
* Writeup

---

### Notes

Evergreen notes.

Examples:

```
Flash Attention
Transformers
MOE
CUDA Memory Hierarchy
Triton
PyTorch Internals
```

These pages rank well on Google.

---

### Resume

Single page + PDF.

---

### About

Your story:

```
MSEE
↓

SAP consultant

↓

US Army Veteran

↓

Returned to family farming

↓

Built software for agriculture

↓

Learning AI and GPU systems

↓

Seeking AI/ML opportunities
```

---

# SEO

Use:

```typescript
astro-seo
sitemap.xml
robots.txt
RSS feed
OpenGraph images
JSON-LD
```

---

# Nice Features

## Reading progress bar

Thin top line.

---

## Mermaid diagrams

For deep learning blogs.

```mermaid
Transformer
↓
Attention
↓
Flash Attention
↓
Paged Attention
```

---

## Math

KaTeX

For equations.

---

## MDX Components

Interactive:

```jsx
<Callout />
<CodeGroup />
<Figure />
<Youtube />
```

---

## Newsletter

Simple button:

"Follow on LinkedIn"

No need for email lists initially.

---

# GitHub Repo Structure

```
harikanth-site/

src/
 components/
 layouts/
 pages/

content/
 blog/
 projects/
 notes/

public/
 images/

astro.config.ts
tailwind.config.ts
```

---

# Use Cursor with These Rules

Create:

```
.cursor/rules/
```

Files:

### architecture.md

Explain:

* Astro
* Tailwind
* MDX
* Cloudflare Pages

### coding-style.md

Rules:

* Functional components
* TypeScript strict
* Accessibility
* No unnecessary JS

### design.md

Inspired by:

* Karpathy
* Sebastian Raschka
* Vercel
* Anthropic
* Linear

---

# My recommendation

**Astro + MDX + Tailwind v4 + Shiki + Pagefind + Cloudflare Pages + Cloudflare R2 + Cloudflare Analytics**

This stack gives you a website that looks modern, loads instantly, ranks well, and lets you focus on publishing GPU, PyTorch, AI, and project content—the kind of sites that frequently help engineers attract recruiters and opportunities.
