/**
 * Content-layer loaders for the LeetCode-patterns track.
 *
 * Source of truth is the `dsa-content` repo, checked out as a git submodule at
 * `external/dsa-content`. Nothing is copied: the loaders read
 *
 *   curriculum/curriculum.json   one row per episode (186)
 *   curriculum/progress.csv      per-episode status flags + YouTube URL
 *   prep/<folder>/<nn>-<slug>.md the written companion to each video
 *   problems/<folder>/<nn>_<slug>.py  the solution
 *   patterns/<nn>-*.md           the pattern master card
 *
 * Publish gate: an episode's prep sheet and solution are only put in the store
 * once `recorded == Y` in progress.csv. Until then the page shows title + status.
 * Set LEARN_PREVIEW=1 to publish everything locally.
 */
import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import type { Loader } from 'astro/loaders';

export const DSA_ROOT = path.resolve('external/dsa-content');

type CurriculumRow = {
  ep: number;
  pattern: string;
  title: string;
  difficulty: string;
  slug: string;
  links: string[];
  pat_no: number;
  pat_ep: number;
  code: string;
  folder: string;
  prep: string;
};

type ProgressRow = Record<string, string>;

export type EpisodeStatus = 'planned' | 'prep' | 'solved' | 'recorded' | 'uploaded';

const PREVIEW = process.env.LEARN_PREVIEW === '1';

/** `01-two-pointers` → `two-pointers` */
export function patternSlug(folder: string): string {
  return folder.replace(/^\d+-/, '');
}

function parseCsv(text: string): ProgressRow[] {
  const lines = text.trim().split(/\r?\n/);
  const header = lines[0].split(',');
  return lines.slice(1).map((line) => {
    const cells: string[] = [];
    let cur = '';
    let quoted = false;
    for (const ch of line) {
      if (ch === '"') quoted = !quoted;
      else if (ch === ',' && !quoted) {
        cells.push(cur);
        cur = '';
      } else cur += ch;
    }
    cells.push(cur);
    return Object.fromEntries(header.map((key, i) => [key, cells[i] ?? '']));
  });
}

function youtubeId(url: string): string | undefined {
  const m = url.match(/(?:v=|youtu\.be\/|shorts\/)([\w-]{11})/);
  return m?.[1];
}

function statusOf(p: ProgressRow): EpisodeStatus {
  if (p.uploaded === 'Y') return 'uploaded';
  if (p.recorded === 'Y') return 'recorded';
  if (p.solved_clean === 'Y') return 'solved';
  if (p.prep_ready === 'Y') return 'prep';
  return 'planned';
}

/** Drop the H1 + meta line above the first `## `, and the production-only
 *  `## 📹 Metadata` section (title/thumbnail notes are not for readers). */
function publicPrepBody(md: string): string {
  const firstSection = md.indexOf('\n## ');
  let body = firstSection >= 0 ? md.slice(firstSection + 1) : md;
  const meta = body.indexOf('## 📹');
  if (meta >= 0) body = body.slice(0, meta);
  return body.trim();
}

/** Drop the H1 and the `**12 episodes · EP 1–12**` line from a pattern card. */
function publicPatternBody(md: string): string {
  return md
    .replace(/^# .*\n/, '')
    .replace(/^\*\*\d+ episodes[^\n]*\n/m, '')
    .replace(/^\s*---\s*\n/, '')
    .trim();
}

async function readOptional(file: string): Promise<string | undefined> {
  try {
    return await readFile(file, 'utf8');
  } catch {
    return undefined;
  }
}

async function loadSources() {
  const [curriculumJson, progressCsv] = await Promise.all([
    readFile(path.join(DSA_ROOT, 'curriculum/curriculum.json'), 'utf8'),
    readFile(path.join(DSA_ROOT, 'curriculum/progress.csv'), 'utf8'),
  ]);
  const curriculum = JSON.parse(curriculumJson) as CurriculumRow[];
  const progress = new Map(parseCsv(progressCsv).map((row) => [Number(row.ep), row]));
  return { curriculum, progress };
}

export function dsaEpisodesLoader(): Loader {
  return {
    name: 'dsa-episodes',
    async load({ store, parseData, generateDigest, renderMarkdown, logger, watcher }) {
      watcher?.add(DSA_ROOT);
      const { curriculum, progress } = await loadSources();
      store.clear();

      let published = 0;
      for (const row of curriculum) {
        const p = progress.get(row.ep) ?? {};
        const status = statusOf(p);
        const isPublished = PREVIEW || status === 'recorded' || status === 'uploaded';
        const pSlug = patternSlug(row.folder);
        const id = `${pSlug}/${row.slug}`;

        const solutionPath = path.posix.join(
          'problems',
          row.folder,
          `${String(row.pat_ep).padStart(2, '0')}_${row.slug.replace(/-/g, '_')}.py`,
        );
        const solutionFile = path.join(DSA_ROOT, solutionPath);
        const prepMd = isPublished ? await readOptional(path.join(DSA_ROOT, row.prep)) : undefined;
        const solution = isPublished ? await readOptional(solutionFile) : undefined;
        const url = p.youtube_url?.trim() ?? '';

        const data = await parseData({
          id,
          data: {
            ep: row.ep,
            code: row.code,
            title: row.title,
            difficulty: row.difficulty || undefined,
            pattern: row.pattern,
            patternSlug: pSlug,
            patternNo: row.pat_no,
            patternEp: row.pat_ep,
            links: row.links,
            status,
            published: isPublished,
            youtubeUrl: url || undefined,
            youtubeId: url ? youtubeId(url) : undefined,
            reps: Number(p.reps ?? 0),
            solution: solution ?? undefined,
            solutionPath,
            prepPath: row.prep,
          },
        });

        const body = prepMd ? publicPrepBody(prepMd) : undefined;
        const digest = generateDigest({ data, body });
        if (body) {
          const rendered = await renderMarkdown(body);
          store.set({ id, data, body, digest, rendered });
          published += 1;
        } else {
          store.set({ id, data, digest });
        }
      }
      logger.info(`loaded ${curriculum.length} episodes, ${published} published`);
    },
  };
}

export function dsaPatternsLoader(): Loader {
  return {
    name: 'dsa-patterns',
    async load({ store, parseData, generateDigest, renderMarkdown, logger, watcher }) {
      watcher?.add(DSA_ROOT);
      const { curriculum, progress } = await loadSources();
      const cardFiles = await readdir(path.join(DSA_ROOT, 'patterns'));
      store.clear();

      const byFolder = new Map<string, CurriculumRow[]>();
      for (const row of curriculum) {
        const list = byFolder.get(row.folder) ?? [];
        list.push(row);
        byFolder.set(row.folder, list);
      }

      for (const [folder, rows] of byFolder) {
        const first = rows[0];
        const id = patternSlug(folder);
        const prefix = `${String(first.pat_no).padStart(2, '0')}-`;
        const cardFile = cardFiles.find((f) => f.startsWith(prefix));
        const cardMd = cardFile
          ? await readOptional(path.join(DSA_ROOT, 'patterns', cardFile))
          : undefined;

        const counts = { planned: 0, prep: 0, solved: 0, recorded: 0, uploaded: 0 };
        for (const row of rows) counts[statusOf(progress.get(row.ep) ?? {})] += 1;

        const data = await parseData({
          id,
          data: {
            no: first.pat_no,
            title: first.pattern,
            folder,
            episodeCount: rows.length,
            epStart: rows[0].ep,
            epEnd: rows[rows.length - 1].ep,
            counts,
            hasCard: Boolean(cardMd),
          },
        });

        const body = cardMd ? publicPatternBody(cardMd) : undefined;
        const digest = generateDigest({ data, body });
        if (body) {
          store.set({ id, data, body, digest, rendered: await renderMarkdown(body) });
        } else {
          store.set({ id, data, digest });
        }
      }
      logger.info(`loaded ${byFolder.size} patterns`);
    },
  };
}
