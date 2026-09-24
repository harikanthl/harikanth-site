#!/usr/bin/env python3
"""
Build one pattern explainer end to end.

    python3 build.py p01_two_pointers            # render
    python3 build.py p01_two_pointers --voice-only
    python3 build.py --all

Pipeline (mirrors MuseDrop's host-TTS + prebaked-voice architecture):

  1. import the scene module and read its `BEATS` narration list (single source of truth —
     the words and the animation live in one file and cannot drift apart);
  2. synthesize each beat's line to a levelled 48 kHz mono WAV and measure its true spoken
     duration -> `voice_manifest.json`;
  3. render the scene with manim at 1920x1080/30, locked to those durations;
  4. read `beat_timings.json` — the ACTUAL rendered beat boundaries — and lay the voice
     lines onto the video at their measured starts, so sync survives a beat whose
     animation overran its narration;
  5. emit the muxed MP4, a WebVTT caption track, a poster frame, and the site manifest row.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX
    fcntl = None

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE / "scripts"
WORK = HERE / "work"
OUT = HERE / "out"
SITE = HERE.parent.parent
MANIFEST = SITE / "src" / "data" / "pattern-explainers.json"

RESOLUTION = "1920,1080"
FRAME_RATE = 30

# Render tiers. `preview` is for fast visual iteration — narration durations are real, so
# the layout you inspect is the layout you ship.
QUALITY = {
    "preview": ("854,480", 15),
    "720p30": ("1280,720", 30),
    "1080p30": (RESOLUTION, FRAME_RATE),
}
QUALITY_CHOICE = "1080p30"

sys.path.insert(0, str(HERE))
from tts import Voice, synth_beats  # noqa: E402


# --------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------
def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def load_scene_module(slug: str):
    path = SCRIPTS / f"{slug}.py"
    if not path.exists():
        raise SystemExit(f"no scene module for '{slug}' at {path}")
    spec = importlib.util.spec_from_file_location(slug, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[slug] = mod
    spec.loader.exec_module(mod)
    if not getattr(mod, "BEATS", None):
        raise SystemExit(f"{path} defines no BEATS narration list")
    cls = getattr(mod, "SCENE_CLASS", None)
    if cls is None:
        raise SystemExit(f"{path} defines no SCENE_CLASS")
    return mod, cls


def ffprobe_duration(path: Path) -> float:
    out = _run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(path),
    ])
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def ts(seconds: float) -> str:
    """WebVTT timestamp."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


# --------------------------------------------------------------------------------------
# pipeline stages
# --------------------------------------------------------------------------------------
def prepare(slug: str, voice: Voice | None = None) -> tuple[Path, list[str], list[float]]:
    mod, _ = load_scene_module(slug)
    beats = list(mod.BEATS)
    work = WORK / slug
    work.mkdir(parents=True, exist_ok=True)

    for name in ("house.py", "shots.py", "prebaked_voice.py"):
        shutil.copy2(HERE / name, work / name)
    shutil.copy2(SCRIPTS / f"{slug}.py", work / "scene.py")

    (work / "voice_manifest.json").unlink(missing_ok=True)
    (work / "beat_timings.json").unlink(missing_ok=True)
    (work / "layout_report.json").unlink(missing_ok=True)

    durations = synth_beats(beats, work, voice=voice)
    total = sum(durations)
    print(f"  narration: {len(beats)} beats, {total:.1f}s ({voice.describe if voice else 'auto'})")
    return work, beats, durations


def render(work: Path, scene_class: str, quality: str = "1080p30") -> Path:
    media = work / "media"
    if media.exists():
        shutil.rmtree(media)
    resolution, fps = QUALITY[quality]
    cmd = [
        "manim", "render", "--disable_caching",
        "--resolution", resolution, "--frame_rate", str(fps),
        "--media_dir", str(media),
        str(work / "scene.py"), scene_class,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(work))
    if res.returncode != 0:
        print(res.stdout[-2500:])
        print(res.stderr[-2500:])
        raise SystemExit(f"manim render failed for {scene_class}")

    # The render is done; surface the deterministic layout QA if it flagged anything.
    report = work / "layout_report.json"
    if report.exists():
        try:
            issues = json.loads(report.read_text())
            if issues:
                print(f"  ! layout QA flagged {len(issues)} beat(s):")
                for entry in issues[:8]:
                    for iss in entry["issues"][:4]:
                        print(f"      beat {entry['index']}: {iss}")
        except Exception:
            pass

    vids = [
        p for p in media.rglob("*.mp4")
        if "partial_movie_files" not in p.parts
    ]
    if not vids:
        raise SystemExit("manim produced no mp4 (see output above)")
    vids.sort(key=lambda p: p.stat().st_size, reverse=True)
    return vids[0]


def build_audio(work: Path, beats: list[str], video: Path) -> Path | None:
    """Lay each beat's voice line at its MEASURED rendered start and concat to one track."""
    timing_file = work / "beat_timings.json"
    if not timing_file.exists():
        print("  ! no beat_timings.json — skipping narration mux")
        return None
    timings = json.loads(timing_file.read_text())

    vdir = work / "voice"
    clips = []
    for i, text in enumerate(beats):
        wav = vdir / f"{i:03d}.wav"
        if not wav.exists():
            continue
        entry = next((t for t in timings if t["index"] == i), None)
        start = float(entry["start"]) if entry else 0.0
        clips.append((start, wav, ffprobe_duration(wav)))

    if not clips:
        return None

    # Silence to pad between beats; one file reused via the concat demuxer.
    silence = work / "silence.wav"
    _run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
          "anullsrc=r=48000:cl=mono", "-t", "0.01", str(silence)])

    seq = work / "audio_seq"
    if seq.exists():
        shutil.rmtree(seq)
    seq.mkdir(parents=True, exist_ok=True)

    lines = []
    cursor = 0.0
    pad_index = 0
    for start, wav, dur in clips:
        gap = start - cursor
        if gap > 0.02:
            pad = seq / f"pad{pad_index:03d}.wav"
            _run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                  "anullsrc=r=48000:cl=mono", "-t", f"{gap:.3f}", str(pad)])
            lines.append(f"file '{pad.name}'")
            pad_index += 1
        lines.append(f"file '{wav.name}'")
        cursor = start + dur
        # A short breath between beats so lines don't butt together.
        tail = seq / f"tail{pad_index:03d}.wav"
        _run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
              "anullsrc=r=48000:cl=mono", "-t", "0.28", str(tail)])
        lines.append(f"file '{tail.name}'")
        pad_index += 1
        cursor += 0.28

    # Copy the audio into the concat dir so the list can use bare filenames.
    for _, wav, _d in clips:
        shutil.copy2(wav, seq / wav.name)
    (seq / "list.txt").write_text("\n".join(lines) + "\n")

    track = work / "narration.wav"
    res = subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
        "-i", str(seq / "list.txt"), "-c:a", "pcm_s16le", str(track),
    ], capture_output=True, text=True, cwd=str(seq))
    if res.returncode != 0:
        print(f"  ! audio concat failed: {res.stderr[-400:]}")
        return None

    final = work / "final.mp4"
    res = subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(video), "-i", str(track),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(final),
    ], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"  ! mux failed: {res.stderr[-400:]}")
        return None
    return final


def write_captions(work: Path, beats: list[str], dest: Path) -> None:
    timing_file = work / "beat_timings.json"
    timings = json.loads(timing_file.read_text()) if timing_file.exists() else []
    rows = ["WEBVTT", ""]
    for i, text in enumerate(beats):
        entry = next((t for t in timings if t["index"] == i), None)
        if entry is None:
            continue
        start, end = float(entry["start"]), float(entry["end"])
        # Split long lines into readable caption cues of ~64 chars on word boundaries.
        words, line, chunks = text.split(), "", []
        for w in words:
            if len(line) + len(w) + 1 > 64:
                chunks.append(line)
                line = w
            else:
                line = f"{line} {w}".strip()
        if line:
            chunks.append(line)
        total = sum(len(c) for c in chunks) or 1
        t = start
        for c in chunks:
            share = (len(c) / total) * max(end - start, 0.8)
            rows.append(f"{ts(t)} --> {ts(min(t + share, end))}")
            rows.append(c)
            rows.append("")
            t += share
    dest.write_text("\n".join(rows))


def write_poster(video: Path, dest: Path, at: float) -> None:
    _run([
        "ffmpeg", "-y", "-v", "error", "-ss", f"{at:.2f}", "-i", str(video),
        "-frames:v", "1", "-q:v", "3", str(dest),
    ])


def chapter_rows(mod, timings: list[dict]) -> list[dict]:
    labels = getattr(mod, "CHAPTERS", {})
    rows = []
    for idx, label in sorted(labels.items()):
        entry = next((t for t in timings if t["index"] == idx), None)
        if entry is None:
            continue
        rows.append({"at": round(float(entry["start"]), 2), "label": label})
    return rows


def update_manifest(slug: str, mod, work: Path, video: Path, poster: Path,
                    vtt: Path, base_url: str) -> None:
    """Write the per-pattern metadata the site reads.

    Asset URLs are deliberately NOT stored here: `src/lib/explainers.ts` composes them from
    `src/data/pattern-explainers.config.json`, so re-pointing at a different host is a config
    edit rather than a re-render.
    """
    timing_file = work / "beat_timings.json"
    timings = json.loads(timing_file.read_text()) if timing_file.exists() else []
    duration = ffprobe_duration(video)

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    # Parallel builds each merge one row; take an exclusive lock so a concurrent
    # read-modify-write can never drop another worker's entry.
    lock_path = MANIFEST.with_suffix('.lock')
    lock = open(lock_path, 'w')
    try:
        if fcntl:
            fcntl.flock(lock, fcntl.LOCK_EX)
        data = {}
        if MANIFEST.exists():
            try:
                data = json.loads(MANIFEST.read_text())
            except Exception:
                data = {}

        key = mod.PATTERN_SLUG
        data[key] = {
            "title": mod.TITLE,
            "summary": getattr(mod, "SUMMARY", ""),
            "duration": round(duration, 1),
            "beats": len(mod.BEATS),
            "chapters": chapter_rows(mod, timings),
        }
        MANIFEST.write_text(json.dumps(dict(sorted(data.items())), indent=2) + "\n")
    finally:
        if fcntl:
            fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


# --------------------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------------------
def build(slug: str, voice: Voice | None = None, base_url: str = "",
          quality: str = "1080p30") -> str:
    print(f"\n▶ {slug}")
    mod, scene_class = load_scene_module(slug)
    work, beats, durations = prepare(slug, voice=voice)

    print(f"  rendering {QUALITY[quality][0]} @ {QUALITY[quality][1]}fps …")
    video = render(work, scene_class, quality)
    print(f"  video: {video.name} ({ffprobe_duration(video):.1f}s, "
          f"{video.stat().st_size / 1e6:.1f} MB)")

    final = build_audio(work, beats, video) or video

    # Assets are named by the pattern slug (not the file stem) so the site can compose
    # predictable URLs from the manifest key.
    name = mod.PATTERN_SLUG
    OUT.mkdir(parents=True, exist_ok=True)
    public = SITE / "public" / "media" / "pattern-explainers"
    public.mkdir(parents=True, exist_ok=True)

    dest_video = public / f"{name}.mp4"
    shutil.copy2(final, dest_video)
    shutil.copy2(final, OUT / f"{name}.mp4")

    poster = public / f"{name}.jpg"
    poster_at = getattr(mod, "POSTER_AT", ffprobe_duration(final) * 0.35)
    write_poster(dest_video, poster, poster_at)
    shutil.copy2(poster, OUT / f"{name}.jpg")

    vtt = public / f"{name}.vtt"
    write_captions(work, beats, vtt)
    shutil.copy2(vtt, OUT / f"{name}.vtt")

    update_manifest(slug, mod, work, dest_video, poster, vtt, base_url)
    print(f"  ✓ {ffprobe_duration(dest_video):.1f}s → public/media/pattern-explainers/{name}.mp4")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", nargs="*", help="one or more scene file stems")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--voice-only", action="store_true",
                    help="synthesize narration + write the manifest, skip rendering")
    ap.add_argument("--voice", default=None, help="voice name override")
    ap.add_argument("--length-scale", type=float, default=1.3,
                    help="narration pace: 1.0 is native (~193 wpm), 1.3 is ~160 wpm "
                         "(the default), 1.4 is ~151 wpm")
    ap.add_argument("--quality", default="1080p30", choices=sorted(QUALITY),
                    help="render tier (preview is fast, for layout iteration)")
    ap.add_argument("--base-url", default="", help="accepted for compatibility; unused")
    ap.add_argument("--jobs", type=int, default=1,
                    help="render N scenes concurrently (manifest writes are locked)")
    args = ap.parse_args()

    if args.all:
        slugs = sorted(p.stem for p in SCRIPTS.glob("p*.py"))
    elif args.slug:
        slugs = list(args.slug)
    else:
        raise SystemExit("pass one or more slugs, or --all")

    voice = Voice(args.voice, length_scale=args.length_scale)
    print(f"voice: {voice.describe}")
    if args.voice_only:
        for slug in slugs:
            work, beats, durations = prepare(slug, voice=voice)
            print(f"  narration total {sum(durations):.1f}s")
        return
    jobs = max(1, args.jobs)
    if jobs == 1:
        for slug in slugs:
            try:
                build(slug, voice=voice, base_url=args.base_url, quality=args.quality)
            except SystemExit as exc:
                # One bad scene should not abandon the rest of a batch.
                print(f"  ✗ {slug}: {exc}")
    else:
        # Rendering is subprocess-bound, so threads are enough. Each scene writes its own
        # work dir; the only shared write is the manifest, which is locked.
        print(f"rendering {len(slugs)} scene(s), {jobs} at a time")
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = {
                pool.submit(build, s, voice, args.base_url, args.quality): s for s in slugs
            }
            for future in concurrent.futures.as_completed(futures):
                slug = futures[future]
                try:
                    future.result()
                except SystemExit as exc:
                    print(f"  ✗ {slug}: {exc}")
                except Exception as exc:  # noqa: BLE001
                    print(f"  ✗ {slug}: unexpected {type(exc).__name__}: {exc}")
    print("\ndone.")


if __name__ == "__main__":
    main()
