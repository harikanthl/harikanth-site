import { readdirSync } from 'node:fs';
import path from 'node:path';

const PAPERWEIGHT_DIR = path.join(process.cwd(), 'public/images/paperweight');
const IMAGE_EXT = /\.(avif|gif|jpe?g|png|svg|webp)$/i;

export type PaperweightImage = {
  src: string;
  title: string;
  alt: string;
  funFact: string;
};

/** Fun facts keyed by image filename without extension. */
const PAPERWEIGHT_FACTS: Record<string, { title: string; funFact: string }> = {
  spider: {
    title: 'Spider',
    funFact:
      'Spider blood uses hemocyanin (copper-based), which turns blue when oxygenated. That is why their hemolymph looks nothing like ours.',
  },
  matiseyes: {
    title: 'Mantis Eyes',
    funFact:
      'Praying mantises are the only insects that can turn their heads about 180 degrees. Those big compound eyes give them stereo vision for hunting.',
  },
  tardigrade: {
    title: 'Tardigrade',
    funFact:
      'Tardigrades can survive the vacuum of space, crushing pressure, and years frozen solid by entering a tun state where they lose almost all their body water.',
  },
  pistolshrimp: {
    title: 'Pistol Shrimp',
    funFact:
      'The pistol shrimp snaps its claw so fast it creates a cavitation bubble that briefly reaches temperatures hotter than the surface of the sun and stuns prey with a mini shockwave.',
  },
  psilocybincubensis: {
    title: 'Psilocybe Cubensis',
    funFact:
      'Psilocybe cubensis gets its kick from psilocybin, which your body converts to psilocin. That molecule is close enough to serotonin that it can bind the same receptors in your brain.',
  },
  prayingmantis: {
    title: 'Praying Mantis',
    funFact:
      'Praying mantises can strike prey in about 50 milliseconds. The famous post-mating cannibalism happens, but field studies suggest it is rarer than the myth makes it sound.',
  },
};

function listPaperweightFilenames(): string[] {
  try {
    return readdirSync(PAPERWEIGHT_DIR)
      .filter((file) => IMAGE_EXT.test(file))
      .sort((a, b) => a.localeCompare(b));
  } catch {
    return [];
  }
}

function basenameFromSrc(src: string): string {
  return path.basename(src, path.extname(src)).toLowerCase();
}

function labelFromFilename(filename: string): string {
  return filename
    .replace(/[-_]+/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function resolvePaperweightMeta(src: string): { title: string; alt: string; funFact: string } {
  const key = basenameFromSrc(src);
  const known = PAPERWEIGHT_FACTS[key];

  if (known) {
    return {
      title: known.title,
      alt: known.title,
      funFact: known.funFact,
    };
  }

  const title = labelFromFilename(key);
  return {
    title,
    alt: title,
    funFact: `A paperweight sketch of a ${title.toLowerCase()}. Add a fun fact for "${key}" in src/lib/paperweight.ts.`,
  };
}

function toPaperweightImage(filename: string): PaperweightImage {
  const src = `/images/paperweight/${filename}`;
  return { src, ...resolvePaperweightMeta(src) };
}

/** Resolved once at build time so every page shares the same ordered pool. */
const PAPERWEIGHT_POOL: PaperweightImage[] = listPaperweightFilenames().map(toPaperweightImage);

export function getAllPaperweights(): PaperweightImage[] {
  return PAPERWEIGHT_POOL;
}

function hashPostId(postId: string, size: number): number {
  if (size === 0) return 0;

  let hash = 0;
  for (let i = 0; i < postId.length; i += 1) {
    hash = (hash * 31 + postId.charCodeAt(i)) >>> 0;
  }

  return hash % size;
}

/** Starting index for a post in the paperweight rotation. */
export function getPaperweightStartIndex(postId: string, chronologicalIndex: number): number {
  const size = PAPERWEIGHT_POOL.length;
  if (size === 0) return 0;

  if (chronologicalIndex >= 0) {
    return chronologicalIndex % size;
  }

  return hashPostId(postId, size);
}

/** @deprecated Use getAllPaperweights + getPaperweightStartIndex instead. */
export function getPaperweightForPost(postIndex: number): PaperweightImage | null {
  const pool = getAllPaperweights();
  if (pool.length === 0) return null;

  return pool[((postIndex % pool.length) + pool.length) % pool.length];
}
