# teslablog.eu News Aggregator + Social Distribution — Design Spec

**Date:** 2026-03-19
**Status:** Approved by Carlo (brainstorming session)
**Scope:** Transform teslablog.eu from a Tesla EU referral blog into a Tesla news aggregator with automated social distribution

---

## 1. Vision

teslablog.eu becomes a **Tesla news aggregator** covering the full Tesla ecosystem — vehicles, FSD, Optimus, Energy, Robo-taxi, earnings, regulatory — with automated distribution to social channels. The existing 60+ blog posts remain as anchor SEO content. A new `/news/` section provides high-frequency aggregated content.

**Monetization path:** Volume + freshness → traffic growth → Ezoic (10K sessions) → Mediavine (50K) + newsletter (Beehiiv Boost) + affiliate.

## 2. Architecture

### Content model: Hybrid (agreed)

- **Auto-publish tier:** News headlines with 2-3 sentence summaries + source links. Factual, low-risk, high-volume. No approval needed.
- **Approval tier:** Original analysis, opinion, referral-focused content. Goes through Carlo's review.

### Infrastructure (no changes to existing stack)

| Component | Location | Role |
|---|---|---|
| Site HTML | GitHub `salvaticarlo2/tesla-referral-eu` → Netlify | Static hosting, auto-deploy |
| Aggregator scripts | VPS `/root/scripts/` | Pull RSS, generate summaries, build HTML |
| Agent config | VPS `/root/.openclaw/workspace-tesla/` | Strategy, memory, skills |
| News data | VPS `/root/tesla-data/news.json` (not in git) | Source of truth for news items |
| Cron scheduler | VPS crontab | Orchestrates pipeline 3-4x/day |
| Social posting | VPS `/root/scripts/` | X (free API), Telegram bot |

### Data flow

```
RSS sources (Electrek, Tesla IR, Reddit, etc.)
        ↓
   aggregate.py (VPS cron, 3-4x/day)
        ↓
   news.json (deduped, scored, categorized)
        ↓
   generate-news.py (builds /news/ HTML pages)
        ↓
   generate-indexes.py (updates homepage with "Latest News" section)
        ↓
   git push → Netlify auto-deploy
        ↓
   distribute.py (posts to X + Telegram + future channels)
```

## 3. New components to build

### 3.1 RSS feed for teslablog.eu (`/feed.xml`)

Auto-generated from blog posts + news items. Serves two purposes:
- Helps Google discover and crawl pages faster (fixes indexing gap: 24/69 pages indexed)
- Standard format for downstream consumers and cross-posting

### 3.2 News aggregator script (`aggregate.py`)

- Pulls from configured RSS feeds (Electrek, InsideEVs, Tesla Investor Relations, Reddit r/tesla, r/TeslaMotors)
- Deduplicates by exact URL match + title similarity (normalized Levenshtein distance > 0.85 = duplicate)
- Categorizes: Vehicles, FSD/Autopilot, Optimus, Energy, Business/Earnings, Regulatory
- **Summary generation (v1):** Extract lead paragraph from RSS `<description>` or `<content:encoded>`, trim to 2-3 sentences. No AI, no external API. Fast and reliable.
- **Summary generation (v2, optional upgrade):** Use Claude API via existing OAuth on VPS for higher-quality rewrites. Cost: ~$0.001/item, ~$0.30/month at 10 items/day. VPS already has Claude OAuth credentials at `/root/openclaw-data/`. Ollama skipped — VPS RAM (7.6GB) too tight alongside existing services.
- Stores in `news.json` with: title, summary, source_url, source_name, category, timestamp, slug

### 3.3 News page generator (`generate-news.py`)

- Reads `news.json`
- Generates `/news/index.html` — latest 20 items, with static pagination pages at `/news/page/2/index.html`, `/news/page/3/index.html`, etc. (20 items per page). Older pages beyond 90 days are archived — HTML kept but removed from pagination nav.
- Generates individual news pages `/news/[slug]/index.html` — for SEO indexing of each item
- Uses same HTML template pattern as existing blog posts (header, footer, sidebar, schema markup)
- Includes Article schema, Open Graph, Twitter Card meta tags
- Links back to source with `rel="nofollow"` on external links

### 3.4 Social distributor (`distribute.py`)

- Reads new items from `news.json` (tracks last-distributed timestamp)
- Generates platform-specific snippets:
  - **X/Twitter:** Title + 1-line summary + link + hashtags (free API tier, 1,500 tweets/mo)
  - **Telegram:** Formatted message with title, summary, source, link (free bot API)
- Posts via respective APIs
- Logs what was posted to avoid duplicates

### 3.5 Homepage update

- `generate-indexes.py` updated to add a "Latest Tesla News" section above existing blog post cards
- Shows 5-10 most recent news items
- Links to `/news/` for full feed

### 3.6 Cron orchestrator

VPS crontab entry running 3-4x/day:
1. `aggregate.py` — fetch new items into `/root/tesla-data/news.json`
2. `generate-news.py` — build `/news/` HTML pages in local repo clone
3. `generate-indexes.py` — update homepage + blog index
4. `generate-feed.py` — update `/feed.xml`
5. `generate-sitemap.sh` — regenerate sitemap including new `/news/` pages
6. `git add + commit + push` — deploy to Netlify
7. Wait for deploy verification — poll `https://teslablog.eu/news/` for 200 OK (timeout 120s, Netlify typically deploys in <30s)
8. `distribute.py` — post to social channels (only runs after deploy confirmed)

**Error handling:** Each step logs to `/root/tesla-data/pipeline.log`. On failure, the pipeline halts and sends a Telegram notification to Carlo. No partial deploys — if `generate-news.py` fails, nothing gets pushed.

## 4. Indexing fixes (Phase 1 priority)

Before the aggregator adds more pages, fix crawl rate for existing 45 stuck pages:

- **Re-auth Google Indexing API** — token expired Mar 18 on VPS
- **Add RSS feed** (`/feed.xml`) — improves Google crawl discovery
- **IndexNow pings** — already set up, just needs to run on deploy
- **Internal linking audit** — add links from indexed pages to stuck pages
- **Sitemap cleanup** — remove stale `sitemap.xml` entry in GSC, keep `sitemap-min.xml`

## 5. Topic coverage (expanded from EU-only)

| Category | Example topics |
|---|---|
| Vehicles | Model Y Juniper, Model 3, Cybertruck, Roadster, Semi |
| FSD / Autopilot | FSD releases, regulatory approvals, unsupervised driving |
| Optimus | Robot demos, production timelines, capabilities |
| Energy | Powerwall, Megapack, Solar, Virtual Power Plant |
| Business | Earnings, deliveries, factory updates, stock |
| Regulatory | EU regulations, NHTSA, tariffs, subsidies |
| Robo-taxi | Robotaxi launches, regulatory approvals |

## 6. Social channels

| Channel | API cost | Automation | Priority |
|---|---|---|---|
| X / Twitter | Free tier (1,500 posts/mo) | `tweet.py` on VPS | High — already have @TeslablogEU |
| Telegram | Free (bot API) | New bot, trivial | High — Tesla community active |
| RSS feed | N/A | Auto-generated | High — feeds everything else |
| Bluesky | Free API | Easy to add later | Medium |
| LinkedIn | Manual | Agent drafts, Carlo posts | Low |

## 7. What stays unchanged

- All 60+ existing blog posts (HTML files untouched)
- CSS / design system
- Referral code integration (`carlo719460`)
- Netlify deployment pipeline
- Google Analytics (GA4)
- Privacy policy, language landing pages
- Build validation script (`check-site.py` — updated to skip `/news/` pages or validate them with relaxed rules)

### Navigation update

- Add "News" link to site header nav (between "Blog" and "Referral")
- News pages include cross-links to related blog posts by category matching

## 8. Success criteria

- **Indexing:** 90%+ of pages indexed within 4 weeks (up from 35%)
- **Content volume:** 5-10 news items/day within 2 weeks of launch
- **Social:** Automated posting to X + Telegram with zero manual intervention
- **Traffic:** 750+ monthly sessions at 4 weeks, 2,500+ at 8 weeks (up from ~250)
- **Monetization ready:** Ezoic application at 10K sessions milestone

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| AI summaries contain errors | Auto-publish only for factual headlines; analysis requires approval |
| Google penalizes thin aggregated content | Each news page has unique summary + schema markup + internal links |
| RSS sources change format | Source config in JSON; easy to update/add/remove |
| X free tier gets restricted further | Telegram as primary channel; RSS feed as universal fallback |
| Netlify build minutes exhausted | 4 deploys/day × 10 sec = ~20 min/month (well within 300 min free tier) |

## 10. Not in scope

- Database or CMS migration
- Framework migration (no Next.js, Hugo, etc.)
- Paid API subscriptions
- Mobile app
- User accounts or comments
