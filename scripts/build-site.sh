#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 scripts/refresh-site-content.py
bash scripts/generate-sitemap.sh
python3 scripts/check-site.py
