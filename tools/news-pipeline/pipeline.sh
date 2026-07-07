#!/usr/bin/env bash
# News pipeline — GitHub Actions version of the old VPS /root/scripts/pipeline.sh.
# Build steps only: commit/push and deploy-verify are handled by the workflow.
# Runs from any checkout; all paths are repo-relative.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"

echo "[pipeline] Step 1: aggregate news"
python3 tools/news-pipeline/aggregate.py

echo "[pipeline] Step 2: generate news pages"
python3 tools/news-pipeline/generate_news.py

echo "[pipeline] Step 3: generate homepage + blog index"
python3 scripts/generate-indexes.py

echo "[pipeline] Step 4: generate feed.xml"
python3 tools/news-pipeline/generate_feed.py

echo "[pipeline] Step 5: generate sitemap"
bash scripts/generate-sitemap.sh

echo "[pipeline] Build complete"
