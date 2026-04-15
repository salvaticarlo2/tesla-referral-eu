#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Generate sitemap (the only build step needed — content is pre-built in repo)
bash scripts/generate-sitemap.sh

# Note: refresh-site-content.py and check-site.py removed from build on 2026-04-15.
# They were tied to the March 31 referral countdown (now obsolete).
# Content updates are handled by Paperclip agents committing directly to the repo.
