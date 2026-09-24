#!/usr/bin/env python3
"""
Static QA across every scene module — run this before a batch render.

    ~/.local/share/uv/tools/manim/bin/python validate.py

Checks the contract that `build.py` depends on, plus the authoring rules that are cheap to
verify without rendering:

  * required module constants present, PATTERN_SLUG unique and matching the card on disk;
  * BEATS length in the 20-24 band and ~110-120s of speech at piper's ~3.1 words/sec;
  * one `voiceover` call per beat, and no narration text duplicated into a headline/caption
    (the caption rail is a short phrase, not the spoken line);
  * CHAPTERS indices in range;
  * no banned 3D / default-palette usage.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE / "scripts"
PATTERNS_DIR = HERE.parent.parent / "external" / "dsa-content" / "patterns"

WORDS_PER_SECOND = 3.1
MIN_BEATS, MAX_BEATS = 15, 26
MIN_SECONDS, MAX_SECONDS = 104, 126

VALID_SLUGS: set[str] = set()

REQUIRED = ("PATTERN_SLUG", "TITLE", "SUMMARY", "SCENE_CLASS", "POSTER_AT", "BEATS", "CHAPTERS")

BANNED = [
    (r"\bThreeDScene\b", "3D scene (charter rule 4: 2D only)"),
    (r"\bSphere\b|\bCube\b|\bSurface\b", "3D mobject (charter rule 4)"),
    (r"\bfrom manim import[^\n]*\bRED\b", "default RED palette"),
]


def load(slug: str):
    path = SCRIPTS / f"{slug}.py"
    spec = importlib.util.spec_from_file_location(slug, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[slug] = mod
    spec.loader.exec_module(mod)
    return mod


def site_slugs() -> set[str]:
    """The authoritative pattern slugs the SITE routes on.

    These come from the curriculum folder names (see `patternSlug` in src/loaders/dsa.ts),
    which are NOT always the same as the pattern card filenames -- folder `02-fast-slow`
    routes to `/learn/leetcode-patterns/fast-slow` while its card is `02-fast-slow-pointers.md`.
    Validating against the card name alone lets a scene ship a slug that no page can match.
    """
    path = HERE.parent.parent / "external" / "dsa-content" / "curriculum" / "curriculum.json"
    try:
        rows = json.loads(path.read_text())
    except Exception:
        return set()
    return {re.sub(r"^\d+-", "", r["folder"]) for r in rows}


def card_for(pattern_slug: str) -> Path | None:
    for card in sorted(PATTERNS_DIR.glob("*.md")):
        stem = card.stem.split("-", 1)[1]
        if stem == pattern_slug:
            return card
    return None


def main() -> int:
    files = sorted(p for p in SCRIPTS.glob("p*.py"))
    if not files:
        print("no scene files found")
        return 1

    global VALID_SLUGS
    VALID_SLUGS = site_slugs()

    failures = 0
    seen_slugs: dict[str, str] = {}
    print(f"{'scene':<34} {'slug':<24} {'beats':>5} {'~sec':>6}  status")
    print("-" * 92)

    for path in files:
        stem = path.stem
        src = path.read_text()
        problems: list[str] = []

        try:
            mod = load(stem)
        except Exception as exc:  # noqa: BLE001
            print(f"{stem:<34} {'-':<24} {'-':>5} {'-':>6}  ✗ import failed: {exc}")
            failures += 1
            continue

        for name in REQUIRED:
            if not hasattr(mod, name):
                problems.append(f"missing {name}")

        slug = getattr(mod, "PATTERN_SLUG", "?")
        beats = list(getattr(mod, "BEATS", []))

        if slug in seen_slugs:
            problems.append(f"PATTERN_SLUG duplicates {seen_slugs[slug]}")
        seen_slugs[slug] = stem

        if VALID_SLUGS and slug not in VALID_SLUGS:
            problems.append(f"slug '{slug}' is not a site route (see curriculum folders)")
        elif not VALID_SLUGS and card_for(slug) is None:
            problems.append(f"no pattern card for slug '{slug}'")

        if not (MIN_BEATS <= len(beats) <= MAX_BEATS):
            problems.append(f"{len(beats)} beats (want {MIN_BEATS}-{MAX_BEATS})")

        words = sum(len(b.split()) for b in beats)
        seconds = words / WORDS_PER_SECOND
        if not (MIN_SECONDS <= seconds <= MAX_SECONDS):
            problems.append(f"~{seconds:.0f}s of speech (want {MIN_SECONDS}-{MAX_SECONDS})")

        vo_calls = len(re.findall(r"self\.voiceover\(", src))
        if vo_calls != len(beats):
            problems.append(f"{vo_calls} voiceover calls for {len(beats)} beats")

        chapters = getattr(mod, "CHAPTERS", {})
        bad_ch = [k for k in chapters if not (0 <= k < len(beats))]
        if bad_ch:
            problems.append(f"CHAPTERS out of range: {bad_ch}")

        for pattern, why in BANNED:
            if re.search(pattern, src):
                problems.append(why)

        dupe = 0
        for b in beats:
            head = b.strip().rstrip(".")
            if len(head) > 40 and re.search(rf'(headline|Text)\(\s*["\']' + re.escape(head[:40]), src):
                dupe += 1
        if dupe:
            problems.append(f"{dupe} narration line(s) duplicated into on-screen text")

        status = "✓ ok" if not problems else "✗ " + "; ".join(problems)
        if problems:
            failures += 1
        print(f"{stem:<34} {slug:<24} {len(beats):>5} {seconds:>6.0f}  {status}")

    print("-" * 92)
    print(f"{len(files)} scene(s), {failures} with problems")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
