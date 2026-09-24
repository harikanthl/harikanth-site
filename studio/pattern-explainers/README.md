# Pattern explainers — the Manim studio

Renders the ~2-minute animated explainer that sits at the top of each LeetCode-pattern page.

One film per pattern: 20–24 narration beats, a synthesised voiceover, burned-in headline and
caption rails, and a WebVTT caption track. The videos are **not committed** — only the
metadata in `src/data/pattern-explainers.json` is. See "Hosting" below.

## Why it works this way

The engine is MuseDrop's host-TTS + prebaked-voice architecture, lifted out of
`~/Desktop/All/MuseDrop/MuseDrop/Services/PrebakedVoiceScaffold.swift` into a real Python
module (`prebaked_voice.py`). MuseDrop's manim *composer* is GUI-bound and not automatable,
but its two reusable assets are its **cinematic charter** (the six taste rules below, from
`ManimCinematicCharter.swift`) and its **technical generation guide**
(`ManimCEGenerationGuide.swift`). Both are encoded here — the charter in `house.py` and the
layout/API rules in `house.py` + `shots.py`.

The timing trick that removes drift: narration is synthesised **first**, each beat's true
spoken duration is written to `voice_manifest.json`, and the scene sizes every animation
against `tracker.duration`. On beat exit the helper waits until that beat's *cumulative*
narration end time, so one slow beat is absorbed by later slack instead of pushing every
following beat late. The render then writes back `beat_timings.json` — the beat boundaries
it actually hit — and the mux lays the voice lines at those measured starts. Sync survives a
beat whose animation overran its line.

### The style contract

Every scene obeys MuseDrop's six charter rules:

1. **Headline before symbols** — each beat opens with a plain-language claim, then notation.
2. **Caption everything** — nothing is drawn that the narration hasn't named.
3. **Camera into the exact term** — zoom the thing being spoken about, then restore.
4. **Depth only when the idea is 3D** — 2D only; draw depth as a 2D sketch when needed.
5. **Nothing keyframed** — motion that represents dynamics comes from computed state.
6. **Visual continuity** — each beat ends on the object the next beat opens with.

## Layout

```
house.py            palette, rails (headline/caption), layout + safe-box helpers
shots.py            reusable animated primitives (ArrayRow, pointer, BarSet, TreeViz, …)
prebaked_voice.py   the vendored voiceover/timing engine
tts.py              narration synthesis (piper preferred, macOS `say` fallback)
build.py            orchestrator: TTS → render → mux → captions → poster → manifest
smoke.py            fast authoring loop: render at preview quality, print layout QA
scripts/pNN_*.py    one scene per pattern (BEATS + the animation, single source of truth)
work/               per-pattern render workdirs (gitignored)
out/                finished masters (gitignored)
```

## Running it

`build.py` and `smoke.py` must run under manim's interpreter, because the scene modules
import manim:

```sh
PY=~/.local/share/uv/tools/manim/bin/python

# fast loop while authoring a scene (stub narration, preview quality, layout QA)
$PY smoke.py p03_sliding_window

# full build of one pattern at 1080p30
$PY build.py p03_sliding_window

# every pattern that has a scene file
$PY build.py --all

# narration only (no render)
$PY build.py p03_sliding_window --voice-only
```

Outputs land in `public/media/pattern-explainers/<pattern-slug>.{mp4,jpg,vtt}` and the
metadata row is merged into `src/data/pattern-explainers.json`. `<pattern-slug>` is the
pattern card's slug with the leading `NN-` stripped (`03-sliding-window` → `sliding-window`),
which is the same id Astro uses for the route.

### Layout QA

`prebaked_voice.py` records off-frame and text-overlap problems at every beat boundary into
`layout_report.json`, with no vision model involved. `smoke.py` prints them, and `build.py`
surfaces them after a render. **Treat them as bugs** — off-frame or overlapping text is the
number-one failure mode for generated manim. Iterate until clean.

## Narration

`tts.py` picks a backend automatically:

* **piper** (preferred) when `.venv-tts/bin/piper` and a model under `voices/` both exist.
  The current voice is `en_US-ryan-high`. Install it with:
  ```sh
  export UV_CACHE_DIR="$PWD/.uvcache" PIP_CACHE_DIR="$PWD/.pipcache"
  python3 -m venv .venv-tts && ./.venv-tts/bin/pip install piper-tts
  mkdir -p voices && cd voices
  curl -sSLO https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx
  curl -sSLO https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx.json
  ```
* **macOS `say`** as the always-available fallback (Samantha / Alex / Daniel).

Every beat is levelled with `loudnorm` and normalised to 48 kHz mono PCM, so beats cut
together without audible jumps.

### Pace

Narration pace is `--length-scale` (piper's phoneme length). **The default is 1.3.** Measured
on a full 355-word film with `en_US-ryan-high`:

| `--length-scale` | pace | film length |
|---|---|---|
| 1.0 (piper native) | 193 wpm | 1:50 |
| 1.2 | 170 wpm | 2:05 |
| **1.3 (default)** | **160 wpm** | **2:13** |
| 1.4 | 151 wpm | 2:21 |

193 wpm is brisk for technical material; 150–165 wpm is the usual explainer pace.

```sh
$PY build.py --all --length-scale 1.4      # slower
$PY build.py p03_sliding_window --length-scale 1.2
```

**Changing the pace requires re-rendering**, because every animation's `run_time` is sized
against the measured narration duration — that is the mechanism that keeps the picture locked
to the voice, so the durations cannot be edited after the fact. A full 15-film re-render is
about 15 minutes.

## Adding a pattern

1. Copy `scripts/p01_two_pointers.py` as a starting point.
2. Write `BEATS` (~350–380 words total for ~2 minutes), then write each `_beatN()` against
   `tracker.duration`.
3. Iterate with `$PY smoke.py <file_stem>` until the layout QA is clean.
4. Build with `$PY build.py <file_stem>`.

A scene module must define: `PATTERN_SLUG`, `TITLE`, `SUMMARY`, `SCENE_CLASS`, `POSTER_AT`,
`BEATS`, `CHAPTERS`. Keep `BEATS` and the animation in the same file — that is what stops the
words and the picture from drifting apart.

## Hosting

Rendered assets are gitignored (`public/media/pattern-explainers/`). The site composes asset
URLs in `src/lib/explainers.ts` from `src/data/pattern-explainers.config.json`:

```json
{ "hostedBaseUrl": "", "localBaseUrl": "/media/pattern-explainers" }
```

Leave `hostedBaseUrl` empty to serve the locally rendered files (dev/preview). Set it to the
public bucket or CDN prefix for production — e.g.
`https://media.harikanth.site/pattern-explainers` — and re-deploy. **No re-render is needed
to move hosts.** Upload `<slug>.mp4`, `<slug>.jpg` and `<slug>.vtt` for each pattern.

## Requirements

* manim 0.20.1 (`~/.local/share/uv/tools/manim`), ffmpeg, and a LaTeX install (for `MathTex`)
* piper (optional, preferred) or macOS `say`
* Apple Container is **not** required — MuseDrop's container image is for sandboxed
  untrusted renders; these scenes are first-party and render directly.
