#!/usr/bin/env bash

set -euo pipefail

HERE=$(dirname "$0")
cd "$HERE/.." || exit 1

uv run python src/download.py
uv run python src/generate.py
./hugo.sh build
