import type { MDXComponents } from 'mdx/types';
import Callout from './components/mdx/Callout.astro';
import CodeGroup from './components/mdx/CodeGroup.astro';
import Figure from './components/mdx/Figure.astro';
import Mermaid from './components/mdx/Mermaid.astro';
import YouTube from './components/mdx/YouTube.astro';

export const components: MDXComponents = {
  Callout,
  CodeGroup,
  Figure,
  Mermaid,
  YouTube,
};
