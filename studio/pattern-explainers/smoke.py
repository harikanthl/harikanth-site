#!/usr/bin/env python3
"""
Smoke-test one scene without synthesizing narration — the fast authoring loop.

    python3 smoke.py p01_two_pointers

Copies the scene + shared modules into an isolated work dir, writes a stub narration
manifest sized to the scene's own beat count, renders at preview quality, and prints the
deterministic layout QA (off-frame / text-overlap) the render recorded. Iterate on the
scene until this exits 0 with no layout issues.

Must be run with manim's interpreter, e.g.

    ~/.local/share/uv/tools/manim/bin/python smoke.py p01_two_pointers
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE / "scripts"
SMOKE_ROOT = HERE / "work" / "_smoke"

STUB_BEAT_SECONDS = 5.0  # representative of the real piper narration


def load_module(slug: str):
    path = SCRIPTS / f"{slug}.py"
    if not path.exists():
        raise SystemExit(f"no scene module at {path}")
    spec = importlib.util.spec_from_file_location(slug, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[slug] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: smoke.py <slug>")
    slug = sys.argv[1]

    mod = load_module(slug)
    beats = list(getattr(mod, "BEATS", []))
    scene_class = getattr(mod, "SCENE_CLASS", None)
    if not beats or not scene_class:
        raise SystemExit(f"{slug}: needs both BEATS and SCENE_CLASS")

    work = SMOKE_ROOT / slug
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)
    for name in ("house.py", "shots.py", "prebaked_voice.py"):
        shutil.copy2(HERE / name, work / name)
    shutil.copy2(SCRIPTS / f"{slug}.py", work / "scene.py")
    (work / "voice_manifest.json").write_text(
        json.dumps([STUB_BEAT_SECONDS] * len(beats))
    )

    print(f"smoke: {slug} — {len(beats)} beats, class {scene_class}")
    res = subprocess.run(
        ["manim", "render", "-ql", "--disable_caching", "--media_dir", "media",
         "scene.py", scene_class],
        cwd=str(work), capture_output=True, text=True,
    )
    if res.returncode != 0:
        tail = (res.stdout + res.stderr)[-3000:]
        print(tail)
        raise SystemExit(f"✗ render failed for {slug}")

    report = work / "layout_report.json"
    if report.exists():
        issues = json.loads(report.read_text())
        if issues:
            print(f"! layout QA flagged {len(issues)} beat(s):")
            for entry in issues:
                for iss in entry["issues"][:5]:
                    print(f"    beat {entry['index']} @{entry['start']}s: {iss}")
            print("  (fix these, then re-run — off-frame or overlapping text is a bug)")
        else:
            print("✓ layout clean")
    else:
        print("✓ layout clean (nothing flagged)")

    vids = [p for p in (work / "media").rglob("*.mp4") if "partial_movie_files" not in p.parts]
    if vids:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(vids[0])],
            capture_output=True, text=True,
        )
        print(f"✓ rendered {out.stdout.strip()}s of video")
    print(f"  work dir: {work}")


if __name__ == "__main__":
    main()
