# tools/news-pipeline/

The teslablog.eu news pipeline, migrated off the Hetzner VPS on 2026-07-07.
Runs on GitHub Actions (`.github/workflows/news-pipeline.yml`) 4x/day at
00/06/12/18 UTC, same cadence as the old VPS cron.

## What it does

1. `aggregate.py` — fetches the RSS feeds in `data/sources.json`, filters for
   Tesla relevance, dedupes, and updates `data/news.json` (committed state).
2. `generate_news.py` — renders `/news/` article + index pages.
3. `scripts/generate-indexes.py` (repo root) — refreshes homepage + blog index.
4. `generate_feed.py` — renders `/feed.xml`.
5. `scripts/generate-sitemap.sh` (repo root) — regenerates sitemaps.

The workflow then commits and pushes; Netlify deploys on push.

## State

`data/news.json` is the pipeline's memory (dedup + article history). It is
committed on every run. `data/pipeline.log` is gitignored.

## Not ported

`distribute.py` (Twitter/Telegram posting) was left on the VPS and retired:
its Twitter credentials had been failing with 401 for a long time and
Telegram was never configured, so it did nothing.

## Monitoring

- GitHub emails on workflow failure.
- `.github/workflows/health-watchdog.yml` independently checks site
  availability and feed freshness every 30 minutes.
