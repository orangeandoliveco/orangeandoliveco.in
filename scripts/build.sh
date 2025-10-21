#!/usr/bin/env bash

set -euo pipefail

HERE=$(dirname "$0")
cd "$HERE/.." || exit 1

changed=false
rm -rf data/menu.csv public/

uv run python src/download.py

if [[ -f data/menu.csv ]]; then
  uv run python src/generate.py
  ./hugo.sh build
  # If Hugo built a site, mark as changed
  if [[ -d public ]] && [[ -n "$(ls -A public 2>/dev/null || true)" ]]; then
    changed=true
  fi
else
  echo "No new menu file; skipping build."
fi

# Export for GitHub Actions
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  echo "changed=$changed" >> "$GITHUB_OUTPUT"
fi

echo "Build changed? $changed"
