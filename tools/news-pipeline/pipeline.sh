#!/usr/bin/env bash
# News pipeline — GitHub Actions version of the old VPS /root/scripts/pipeline.sh.
# Build steps only: commit/push and deploy-verify are handled by the workflow.
# Runs from any checkout; all paths are repo-relative.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"

# ---------------------------------------------------------------------------
# RETIRED 2026-07-24. The /news/ section was removed after Search Console showed
# the site under a scaled-content demotion: 988 indexed pages against ~75 real
# ones, nothing crawled since 2026-07-04, and 0 clicks from the news layer in
# July. This script now exits without generating anything, so the scheduled
# workflow is a harmless no-op.
#
# To reverse: delete this block, restore the news/ directory from tag
# pre-news-removal-2026-07-24, remove the 410 rule from netlify.toml, and put
# the News nav item back in scripts/generate-indexes.py.
# ---------------------------------------------------------------------------
echo "[pipeline] RETIRED 2026-07-24: /news/ removed, nothing to do."
exit 0

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
