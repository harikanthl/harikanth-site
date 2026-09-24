/**
 * Pattern explainers — the ~2-minute animated Manim film that accompanies each pattern card.
 *
 * The videos are rendered by `studio/pattern-explainers` (see that directory's README) and
 * are kept OUT of git: only the metadata in `src/data/pattern-explainers.json` is committed.
 * Asset URLs are composed here from `pattern-explainers.config.json`, so pointing the site at
 * a different host is a config edit rather than a re-render.
 *
 * Read with `node:fs` rather than `import ... from '*.json'` so this works identically in
 * `astro dev`, `astro build`, and any TS strictness setting.
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';

export type Chapter = {
  /** Seconds from the start of the film. */
  at: number;
  label: string;
};

export type ExplainerMeta = {
  title: string;
  summary: string;
  /** Total runtime in seconds. */
  duration: number;
  /** How many narration beats the film has. */
  beats: number;
  chapters: Chapter[];
};

export type Explainer = ExplainerMeta & {
  slug: string;
  video: string;
  poster: string;
  captions: string;
};

type Config = {
  hostedBaseUrl?: string;
  localBaseUrl?: string;
};

const DATA_DIR = path.resolve('src/data');

function readJson<T>(file: string, fallback: T): T {
  try {
    return JSON.parse(readFileSync(path.join(DATA_DIR, file), 'utf8')) as T;
  } catch {
    return fallback;
  }
}

const meta = readJson<Record<string, ExplainerMeta>>('pattern-explainers.json', {});
const config = readJson<Config>('pattern-explainers.config.json', {});

/** Hosted assets win when configured; otherwise fall back to the local public/ copies. */
const BASE = (config.hostedBaseUrl || config.localBaseUrl || '/media/pattern-explainers').replace(
  /\/+$/,
  '',
);

export function explainerFor(patternSlug: string): Explainer | undefined {
  const entry = meta[patternSlug];
  if (!entry) return undefined;
  return {
    ...entry,
    slug: patternSlug,
    video: `${BASE}/${patternSlug}.mp4`,
    poster: `${BASE}/${patternSlug}.jpg`,
    captions: `${BASE}/${patternSlug}.vtt`,
  };
}

/** `110.6` → `1:51` */
export function formatRuntime(seconds: number): string {
  const total = Math.round(seconds);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

/** Every rendered explainer, keyed by pattern slug — for index pages that list patterns. */
export function allExplainers(): Record<string, Explainer> {
  const out: Record<string, Explainer> = {};
  for (const slug of Object.keys(meta)) {
    const entry = explainerFor(slug);
    if (entry) out[slug] = entry;
  }
  return out;
}

/** How many explainers have been rendered so far (drives the track index copy). */
export function explainerCount(): number {
  return Object.keys(meta).length;
}
