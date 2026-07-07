#!/usr/bin/env python3
"""
generate_news.py — generates static HTML pages for the /news/ section
from /root/tesla-data/news.json. Produces individual article pages and
paginated index pages matching the TeslaBlog.eu site structure.
"""

import json
import os
import shutil
from datetime import datetime
from html import escape
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────
# Script lives at <repo>/tools/news-pipeline/; data sits alongside it.
REPO_DIR = str(Path(__file__).resolve().parents[2])
NEWS_FILE = str(Path(__file__).resolve().parent / 'data' / 'news.json')
SITE_URL = 'https://teslablog.eu'
GA_ID = 'G-VCL5P0HLMR'
REFERRAL_CODE = 'carlo719460'
ITEMS_PER_PAGE = 20

NEWS_DIR = os.path.join(REPO_DIR, 'news')

# ── HTML fragments ─────────────────────────────────────────────────────────

GA_SNIPPET = f'''<!-- Google Analytics GA4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag("js", new Date());
  gtag("config", "{GA_ID}");
</script>'''

NAV_HEADER_NEWS = '''<header>
  <div class="tb-masthead">
    <a href="/" class="tb-logo">TESLABLOG<span>.EU</span></a>
    <nav class="tb-nav">
      <a href="/news/">News</a>
      <a href="/blog/">Blog</a>
      <a href="/gear/">Gear</a>
      <a href="/referral/">Referral</a>
      <details class="tb-lang"><summary>EN ⌄</summary>
      <div class="tb-lang-menu">
      <a href="/de/">DE</a>
      <a href="/fr/">FR</a>
      <a href="/nl/">NL</a>
      <a href="/no/">NO</a>
      <a href="/it/">IT</a>
      <a href="/es/">ES</a>
      </div>
      </details>
    </nav>
  </div>
</header>'''

FOOTER_CTA = '''<div class="footer-cta">
  <p>Thinking about a Tesla? Read our <a href="/referral/">guide to how Tesla referrals work in Europe</a> and always verify an active referral link before ordering.</p>
</div>'''

FOOTER = '''<footer>
  <div class="tb-footer">
    <div class="tb-flinks">
      <span>Guides:</span>
      <a href="/de/">DE</a>
      <a href="/fr/">FR</a>
      <a href="/nl/">NL</a>
      <a href="/no/">NO</a>
      <a href="/it/">IT</a>
      <a href="/es/">ES</a>
      <span>·</span>
      <a href="/gear/">Gear</a>
      <span>·</span>
      <a href="/referral/">Referral</a>
      <span>·</span>
      <a href="/about/">About</a>
      <span>·</span>
      <a href="/privacy/">Privacy</a>
      <span>·</span>
      <a href="/feed.xml">RSS</a>
    </div>
    <p class="tb-legal">Independent website, not affiliated with Tesla, Inc. "Tesla", "Model 3", "Model Y", "Model S", "Model X", "Supercharger" and "Autopilot" are trademarks of Tesla, Inc. © 2026 TeslaBlog.eu</p>
  </div>
</footer>'''


# ── Helpers ────────────────────────────────────────────────────────────────

def category_class(category):
    """Convert category to CSS class: lowercase, / -> -, space -> -."""
    return category.lower().replace('/', '-').replace(' ', '-')


def format_date(timestamp_str):
    """Parse ISO timestamp and return (human_date, iso_date)."""
    try:
        dt = datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError):
        dt = datetime.now()
    human = dt.strftime('%b %d, %Y')
    iso = dt.strftime('%Y-%m-%d')
    return human, iso


def truncate(text, max_len=180):
    """Truncate text to max_len chars, adding ellipsis if needed."""
    if not text:
        return ''
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(' ', 1)[0] + '\u2026'


# ── Page generators ────────────────────────────────────────────────────────

def render_article_page(item):
    """Generate full HTML for an individual news article page."""
    title_safe = escape(item.get('title', 'Untitled'))
    summary_safe = escape(item.get('summary', ''))
    source_name_safe = escape(item.get('source_name', ''))
    source_url = item.get('source_url', '#')
    slug = item.get('slug', '')
    category = item.get('category', 'News')
    cat_cls = category_class(category)
    category_safe = escape(category)
    timestamp = item.get('timestamp', '')
    human_date, iso_date = format_date(timestamp)

    page_url = f'{SITE_URL}/news/{slug}/'

    # JSON-LD with json.dumps for safe values
    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": item.get('title', 'Untitled'),
        "description": item.get('summary', ''),
        "url": page_url,
        "datePublished": iso_date,
        "publisher": {
            "@type": "Organization",
            "name": "TeslaBlog.eu",
            "url": SITE_URL
        },
        "mainEntityOfPage": page_url
    }, indent=4)

    breadcrumb_jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "News", "item": f"{SITE_URL}/news/"},
            {"@type": "ListItem", "position": 3, "name": item.get('title', 'Untitled'), "item": page_url}
        ]
    }, indent=4)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_safe} | TeslaBlog.eu</title>
  <meta name="description" content="{escape(truncate(item.get('summary', ''), 160))}">
  <meta name="robots" content="noindex, follow">
  <link rel="canonical" href="{page_url}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{page_url}">
  <meta property="og:title" content="{title_safe} | TeslaBlog.eu">
  <meta property="og:description" content="{escape(truncate(item.get('summary', ''), 200))}">
  <meta property="og:site_name" content="TeslaBlog.eu">
  <meta property="og:image" content="{SITE_URL}/assets/teslablog-og-default.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title_safe} | TeslaBlog.eu">
  <meta name="twitter:description" content="{escape(truncate(item.get('summary', ''), 200))}">
  <meta name="twitter:image" content="{SITE_URL}/assets/teslablog-og-default.jpg">
  <link rel="stylesheet" href="/css/style.css">
  <script type="application/ld+json">
  {jsonld}
  </script>
  <script type="application/ld+json">
  {breadcrumb_jsonld}
  </script>
  {GA_SNIPPET}
</head>
<body>

{NAV_HEADER_NEWS}

<nav class="breadcrumb" aria-label="Breadcrumb">
  <a href="/">Home</a>
  <span class="sep">\u203a</span>
  <a href="/news/">News</a>
  <span class="sep">\u203a</span>
  <span>{title_safe}</span>
</nav>

<main>
  <div class="layout-cols">
    <div class="main-col">

      <article class="news-article">
        <span class="category-tag {cat_cls}">{category_safe}</span>
        <h1>{title_safe}</h1>
        <div class="article-meta">
          <time datetime="{iso_date}">{human_date}</time>
          \u00b7 Source: <a href="{escape(source_url)}" target="_blank" rel="nofollow noopener">{source_name_safe}</a>
        </div>
        <p class="news-summary">{summary_safe}</p>
        <p class="news-source-link">
          <a href="{escape(source_url)}" target="_blank" rel="nofollow noopener">Read full article at {source_name_safe} \u2192</a>
        </p>
      </article>

    </div>
  </div>
</main>

{FOOTER_CTA}

{FOOTER}

</body>
</html>'''


def render_news_card(item):
    """Render a single news card for the index page."""
    title_safe = escape(item.get('title', 'Untitled'))
    summary_safe = escape(truncate(item.get('summary', ''), 180))
    source_name_safe = escape(item.get('source_name', ''))
    slug = item.get('slug', '')
    category = item.get('category', 'News')
    cat_cls = category_class(category)
    category_safe = escape(category)
    human_date, _ = format_date(item.get('timestamp', ''))

    return f'''    <article class="news-card">
      <div class="news-card-content">
        <span class="category-tag {cat_cls}">{category_safe}</span>
        <h2><a href="/news/{slug}/">{title_safe}</a></h2>
        <div class="article-meta">{human_date} \u00b7 {source_name_safe}</div>
        <p>{summary_safe}</p>
      </div>
    </article>'''


def render_index_page(items, page_num, total_pages):
    """Render a paginated news index page."""
    cards_html = '\n'.join(render_news_card(item) for item in items)

    if page_num == 1:
        canonical = f'{SITE_URL}/news/'
    else:
        canonical = f'{SITE_URL}/news/page/{page_num}/'
    robots_meta = 'index, follow' if page_num == 1 else 'noindex, follow'

    # Pagination links
    pagination_parts = []
    if page_num > 1:
        if page_num == 2:
            pagination_parts.append('<a href="/news/" class="pagination-link">\u2190 Newer</a>')
        else:
            pagination_parts.append(f'<a href="/news/page/{page_num - 1}/" class="pagination-link">\u2190 Newer</a>')

    pagination_parts.append(f'<span class="pagination-info">Page {page_num} of {total_pages}</span>')

    if page_num < total_pages:
        pagination_parts.append(f'<a href="/news/page/{page_num + 1}/" class="pagination-link">Older \u2192</a>')

    pagination_html = '\n        '.join(pagination_parts)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tesla News \u2014 Latest EV &amp; Tesla Updates | TeslaBlog.eu</title>
  <meta name="description" content="Latest Tesla and EV news curated for European drivers. Software updates, vehicle releases, charging infrastructure, and more.">
  <meta name="robots" content="{robots_meta}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{canonical}">
  <meta property="og:title" content="Tesla News \u2014 Latest EV &amp; Tesla Updates | TeslaBlog.eu">
  <meta property="og:description" content="Latest Tesla and EV news curated for European drivers.">
  <meta property="og:site_name" content="TeslaBlog.eu">
  <meta property="og:image" content="{SITE_URL}/assets/teslablog-og-default.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Tesla News | TeslaBlog.eu">
  <meta name="twitter:description" content="Latest Tesla and EV news curated for European drivers.">
  <meta name="twitter:image" content="{SITE_URL}/assets/teslablog-og-default.jpg">
  <link rel="stylesheet" href="/css/style.css">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": "Tesla News",
    "url": "{canonical}",
    "description": "Latest Tesla and EV news curated for European drivers.",
    "publisher": {{ "@type": "Organization", "name": "TeslaBlog.eu", "url": "{SITE_URL}/" }}
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{ "@type": "ListItem", "position": 1, "name": "Home", "item": "{SITE_URL}/" }},
      {{ "@type": "ListItem", "position": 2, "name": "News", "item": "{SITE_URL}/news/" }}
    ]
  }}
  </script>
  {GA_SNIPPET}
</head>
<body>

{NAV_HEADER_NEWS}

<nav class="breadcrumb" aria-label="Breadcrumb">
  <a href="/">Home</a>
  <span class="sep">\u203a</span>
  <span>News</span>
</nav>

<main>

  <div class="page-header">
    <span class="label">News Feed</span>
    <h1>Tesla News</h1>
    <p class="lead">Latest Tesla and EV news curated for European drivers.</p>
  </div>

  <div class="layout-cols">
    <div class="main-col">
      <div class="article-list">

{cards_html}

      </div>

      <div class="pagination">
        {pagination_html}
      </div>
    </div>
  </div>

</main>

{FOOTER_CTA}

{FOOTER}

</body>
</html>'''


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    # Load news data
    if not os.path.exists(NEWS_FILE):
        print(f"Error: {NEWS_FILE} not found")
        return

    with open(NEWS_FILE, 'r', encoding='utf-8') as f:
        news_items = json.load(f)

    if not news_items:
        print("No news items found")
        return

    # Sort by timestamp descending (newest first)
    news_items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    print(f"Loaded {len(news_items)} news items")

    # Clean old news directory
    if os.path.exists(NEWS_DIR):
        shutil.rmtree(NEWS_DIR)
        print(f"Cleaned {NEWS_DIR}")

    os.makedirs(NEWS_DIR, exist_ok=True)

    # Generate individual article pages
    article_count = 0
    for item in news_items:
        slug = item.get('slug', '')
        if not slug:
            continue

        article_dir = os.path.join(NEWS_DIR, slug)
        os.makedirs(article_dir, exist_ok=True)

        html = render_article_page(item)
        with open(os.path.join(article_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
        article_count += 1

    print(f"Generated {article_count} article pages")

    # Generate paginated index pages
    total_pages = max(1, -(-len(news_items) // ITEMS_PER_PAGE))  # ceil division

    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        page_items = news_items[start:end]

        html = render_index_page(page_items, page_num, total_pages)

        if page_num == 1:
            # news/index.html
            with open(os.path.join(NEWS_DIR, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(html)
        else:
            # news/page/N/index.html
            page_dir = os.path.join(NEWS_DIR, 'page', str(page_num))
            os.makedirs(page_dir, exist_ok=True)
            with open(os.path.join(page_dir, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(html)

    print(f"Generated {total_pages} index page(s)")
    print("Done.")


if __name__ == '__main__':
    main()
