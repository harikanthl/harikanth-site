#!/usr/bin/env bash
#
# Publish the rendered pattern explainers to external hosting.
#
# The videos are deliberately kept out of git (they are gitignored), so the site needs them
# served from somewhere. `src/lib/explainers.ts` composes asset URLs from
# `src/data/pattern-explainers.config.json`, so publishing is:
#
#   1. upload out/<slug>.{mp4,jpg,vtt} somewhere public
#   2. put that prefix in pattern-explainers.config.json -> hostedBaseUrl
#   3. rebuild + deploy
#
# Two backends, both driven from `out/`:
#
#   ./publish.sh github <owner/repo> [tag]     # GitHub Releases (needs `gh auth login`)
#   ./publish.sh r2 <bucket> [prefix]          # Cloudflare R2 (needs `wrangler login`)
#
# GitHub Releases is the zero-setup option; R2 is the better long-term CDN if the site is
# already on Cloudflare Pages.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$HERE/out"
CONFIG="$HERE/../../src/data/pattern-explainers.config.json"

if [[ ! -d "$OUT" ]]; then
  echo "no $OUT — run: \$PY build.py --all" >&2
  exit 1
fi

shopt -s nullglob
ASSETS=("$OUT"/*.mp4 "$OUT"/*.jpg "$OUT"/*.vtt)
if [[ ${#ASSETS[@]} -eq 0 ]]; then
  echo "no assets in $OUT — run: \$PY build.py --all" >&2
  exit 1
fi

MODE="${1:-}"
case "$MODE" in
  github)
    REPO="${2:?usage: publish.sh github <owner/repo> [tag]}"
    TAG="${3:-pattern-explainers-v1}"

    echo "→ GitHub Releases: $REPO @ $TAG"
    echo "  ${#ASSETS[@]} assets from $OUT"

    if ! gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
      gh release create "$TAG" --repo "$REPO" \
        --title "Pattern explainers" \
        --notes "Animated ~2-minute explainers for the LeetCode patterns track, rendered with Manim."
    fi

    gh release upload "$TAG" "${ASSETS[@]}" --repo "$REPO" --clobber

    BASE="https://github.com/$REPO/releases/download/$TAG"
    echo
    echo "✓ uploaded. Set hostedBaseUrl to:"
    echo "    $BASE"
    echo
    echo "  note: GitHub release asset URLs redirect (302) to objects.githubusercontent.com."
    echo "  Browsers follow that fine; if you want a clean CDN prefix, use the r2 mode."
    ;;

  r2)
    BUCKET="${2:?usage: publish.sh r2 <bucket> [prefix]}"
    PREFIX="${3:-pattern-explainers}"

    echo "→ Cloudflare R2: $BUCKET/$PREFIX"
    for f in "${ASSETS[@]}"; do
      n="$(basename "$f")"
      echo "  uploading $n"
      npx wrangler r2 object put "$BUCKET/$PREFIX/$n" --file "$f" --remote
    done

    echo
    echo "✓ uploaded. Set hostedBaseUrl to your bucket's public prefix, e.g."
    echo "    https://media.example.com/$PREFIX"
    ;;

  *)
    cat >&2 <<EOF
usage:
  publish.sh github <owner/repo> [tag]     upload to a GitHub release
  publish.sh r2 <bucket> [prefix]          upload to a Cloudflare R2 bucket

Then set hostedBaseUrl in:
  $CONFIG
and rebuild the site.
EOF
    exit 1
    ;;
esac
