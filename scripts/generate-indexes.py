#!/usr/bin/env python3
"""
generate-indexes.py — auto-regenerates index.html and blog/index.html
from all post directories. Runs on the VPS in every pipeline cycle.

Design: Cold Minimal 5b (Cosmic Orange), Martin Magli handoff 2026-07.
Referral copy rule: the 2026 allocation for carlo719460 is used; never
promise buyer benefits through it until Tesla resets the limit.
"""
import os, re, json
from pathlib import Path
from datetime import datetime
from html import escape, unescape

SITE_ROOT = Path(__file__).parent.parent
BLOG_DIR = SITE_ROOT / 'blog'
GA_ID = 'G-VCL5P0HLMR'
REFERRAL_CODE = 'carlo719460'

LANGS = [('EN', '/'), ('DE', '/de/'), ('FR', '/fr/'), ('NL', '/nl/'),
         ('NO', '/no/'), ('IT', '/it/'), ('ES', '/es/')]

LANG_FLAGS = {'de': 'DE · Deutsch', 'fr': 'FR · Français', 'nl': 'NL · Nederlands',
              'no': 'NO · Norsk', 'it': 'IT · Italiano', 'es': 'ES · Español'}


def masthead(active='EN'):
    menu = '\n      '.join(
        f'<a href="{url}">{code}</a>' for code, url in LANGS if code != active
    )
    return f'''<header>
  <div class="tb-masthead">
    <a href="/" class="tb-logo">TESLABLOG<span>.EU</span></a>
    <nav class="tb-nav">
      <a href="/news/">News</a>
      <a href="/blog/">Blog</a>
      <a href="/gear/">Gear</a>
      <a href="/referral/">Referral</a>
      <details class="tb-lang"><summary>{active} ⌄</summary>
      <div class="tb-lang-menu">
      {menu}
      </div>
      </details>
    </nav>
  </div>
</header>'''


TB_FOOTER = '''<footer>
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

GA_SNIPPET = f'''<!-- Google Analytics GA4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag("js", new Date());
  gtag("config", "{GA_ID}");
</script>'''

COPY_SCRIPT = '''<script>
document.addEventListener('DOMContentLoaded', function () {
  var code = document.getElementById('refCode');
  var fb = document.getElementById('copyFeedback');
  if (!code) return;
  code.addEventListener('click', function () {
    navigator.clipboard.writeText('carlo719460').then(function () {
      if (fb) { fb.textContent = 'COPIED'; setTimeout(function () { fb.textContent = ''; }, 2000); }
    });
  });
});
</script>'''

REFBOX = f'''<div class="tb-refbox">
      <p>Ordering a Tesla? This site's referral code <span class="tb-code" id="refCode" title="Click to copy">{REFERRAL_CODE}</span><span class="copy-feedback" id="copyFeedback"></span> is capped for 2026 and currently gives buyers no benefits. <a href="/referral/">How Tesla referrals work</a>. Verify an active link before you configure. Reset expected: January 2027.</p>
    </div>'''


def mono_date(dt):
    return dt.strftime('%b %d').upper()


def render_news_rows(max_items=5):
    """News rows for the homepage + latest news datetime."""
    news_file = Path('/root/tesla-data/news.json')
    if not news_file.exists():
        news_file = SITE_ROOT / 'tools' / 'news-pipeline' / 'data' / 'news.json'
    if not news_file.exists():
        news_file = SITE_ROOT / 'news.json'
    if not news_file.exists():
        return '', None
    with open(news_file, 'r') as f:
        items = json.load(f)
    if not items:
        return '', None
    # Source diversity: never let one feed (Yahoo publishes 10x anyone else)
    # own the homepage. Max 2 items per source, chosen from the 25 newest.
    picked = []
    per_source = {}
    for it in items[:25]:
        src = it.get('source_name', '?')
        if per_source.get(src, 0) >= 2:
            continue
        picked.append(it)
        per_source[src] = per_source.get(src, 0) + 1
        if len(picked) >= max_items:
            break
    if len(picked) < max_items:
        seen = {i['slug'] for i in picked}
        picked += [i for i in items[:25] if i['slug'] not in seen][:max_items - len(picked)]
    latest_dt = None
    rows = ''
    for it in picked:
        title = escape(it['title'])
        slug = it['slug']
        try:
            dt = datetime.fromisoformat(it.get('timestamp', ''))
        except (ValueError, TypeError):
            dt = datetime.now()
        if latest_dt is None or dt.replace(tzinfo=None) > latest_dt:
            latest_dt = dt.replace(tzinfo=None)
        rows += f'''      <div class="tb-nrow">
        <span class="tb-date">{mono_date(dt)}</span>
        <a class="tb-ntitle" href="/news/{slug}/">{title}</a>
      </div>\n'''
    return rows, latest_dt


def extract_post(post_dir):
    html_file = post_dir / 'index.html'
    if not html_file.exists():
        return None
    html = html_file.read_text(encoding='utf-8')

    lang_m = re.search(r'<html[^>]+lang="([^"]+)"', html)
    lang = lang_m.group(1) if lang_m else 'en'

    date_m = re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})', html)
    if not date_m:
        return None
    date_str = date_m.group(1)

    title_m = re.search(r'<title>([^<]+)</title>', html)
    title = unescape(title_m.group(1).strip()) if title_m else post_dir.name
    title = re.sub(r'\s*[|—]\s*TeslaBlog\.eu$', '', title).strip()

    desc_m = re.search(r'<meta name="description" content="([^"]+)"', html)
    description = unescape(desc_m.group(1)) if desc_m else ''

    cat_m = re.search(r'class="category-tag"[^>]*>([^<]+)<', html)
    category = unescape(cat_m.group(1).strip()) if cat_m else 'Article'

    rt_m = re.search(r'(\d+)\s*min\s*read', html)
    read_time = int(rt_m.group(1)) if rt_m else None

    dt = datetime.strptime(date_str, '%Y-%m-%d')

    return {
        'slug': post_dir.name,
        'lang': lang,
        'date': date_str,
        'dt': dt,
        'date_label': mono_date(dt),
        'title': title,
        'description': description,
        'category': category,
        'read_time': read_time,
        'url': f'/blog/{post_dir.name}/',
    }


def render_article_row(p):
    title = escape(p['title'])
    cat = escape(p['category'])
    return f'''      <div class="tb-arow">
        <span class="tb-date">{p['date_label']}</span>
        <div class="tb-abody">
          <a class="tb-atitle" href="{p['url']}">{title}</a>
          <a class="tb-tag" href="{p['url']}">{cat} ↗</a>
        </div>
      </div>'''


def render_lang_row(p):
    title = escape(p['title'])
    label = LANG_FLAGS.get(p['lang'], p['lang'].upper())
    return f'''      <div class="tb-arow">
        <span class="tb-date">{p['date_label']}</span>
        <div class="tb-abody">
          <a class="tb-atitle" href="{p['url']}">{title}</a>
          <span class="tb-tag">{escape(label)}</span>
        </div>
      </div>'''


# ── Scan all posts ──────────────────────────────────────────────────────────
posts = []
for d in BLOG_DIR.iterdir():
    if not d.is_dir() or d.name == '':
        continue
    p = extract_post(d)
    if p:
        posts.append(p)

posts.sort(key=lambda x: x['date'], reverse=True)
en_posts = [p for p in posts if p['lang'] == 'en']
lang_posts = [p for p in posts if p['lang'] != 'en']

print(f"Found {len(posts)} posts: {len(en_posts)} EN, {len(lang_posts)} other languages")

# ── Build index.html ────────────────────────────────────────────────────────
top_home = en_posts[:6]
jsonld_posts = json.dumps([{
    "@type": "BlogPosting",
    "headline": p['title'],
    "url": f"https://teslablog.eu{p['url']}",
    "datePublished": p['date']
} for p in en_posts[:5]], indent=6)

news_rows, latest_news_dt = render_news_rows()
article_rows = '\n'.join(render_article_row(p) for p in top_home)

updated_dt = latest_news_dt or (en_posts[0]['dt'] if en_posts else datetime.now())
if en_posts and en_posts[0]['dt'] > updated_dt:
    updated_dt = en_posts[0]['dt']
updated_label = updated_dt.strftime('%b %d %Y').upper()

news_section = ''
if news_rows:
    news_section = f'''    <section class="tb-section">
      <div class="tb-sechead">
        <span class="tb-num">01</span>
        <span class="tb-seclabel">News</span>
        <a class="tb-all" href="/news/">ALL →</a>
      </div>
{news_rows}    </section>'''

home_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TeslaBlog.eu — Tesla News &amp; Guides for Europe</title>
  <meta name="description" content="Independent Tesla blog for European drivers. Software updates, buying guides, Grok AI coverage, and practical tips from a Tesla owner in Europe.">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://teslablog.eu/">
  <link rel="alternate" type="application/rss+xml" title="TeslaBlog.eu RSS Feed" href="https://teslablog.eu/feed.xml">
  <link rel="alternate" hreflang="en" href="https://teslablog.eu/">
  <link rel="alternate" hreflang="de" href="https://teslablog.eu/de/">
  <link rel="alternate" hreflang="fr" href="https://teslablog.eu/fr/">
  <link rel="alternate" hreflang="nl" href="https://teslablog.eu/nl/">
  <link rel="alternate" hreflang="no" href="https://teslablog.eu/no/">
  <link rel="alternate" hreflang="it" href="https://teslablog.eu/it/">
  <link rel="alternate" hreflang="x-default" href="https://teslablog.eu/">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://teslablog.eu/">
  <meta property="og:title" content="TeslaBlog.eu — Tesla News &amp; Guides for Europe">
  <meta property="og:description" content="Independent Tesla blog for European drivers. Practical tips, software updates, and buying guides.">
  <meta property="og:image" content="https://teslablog.eu/assets/og/home.png">
  <meta property="og:site_name" content="TeslaBlog.eu">
  <meta property="og:locale" content="en_US">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="TeslaBlog.eu — Tesla News &amp; Guides for Europe">
  <meta name="twitter:description" content="Independent Tesla blog for European drivers. Software updates, buying guides, and practical tips.">
  <meta name="twitter:image" content="https://teslablog.eu/assets/og/home.png">
  <link rel="stylesheet" href="/css/style.css">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Blog",
    "name": "TeslaBlog.eu",
    "url": "https://teslablog.eu/",
    "description": "Independent Tesla blog for European drivers",
    "inLanguage": "en",
    "publisher": {{ "@type": "Organization", "name": "TeslaBlog.eu" }},
    "blogPost": {jsonld_posts}
  }}
  </script>
  {GA_SNIPPET}
</head>
<body>

{masthead('EN')}

<div class="tb-wrap">

  <section class="tb-hero">
    <h1>Tesla news &amp; guides<br>for Europe<span class="tb-dot">.</span></h1>
    <p class="tb-intro">Independent coverage from an owner. Software updates, buying guides, EV news.</p>
    <div class="tb-status"><span class="tb-sq"></span>UPDATED {updated_label} · NOT AFFILIATED WITH TESLA, INC.</div>
  </section>

{news_section}

  <section class="tb-section">
    <div class="tb-sechead">
      <span class="tb-num">02</span>
      <span class="tb-seclabel">Articles</span>
      <a class="tb-all" href="/blog/">ALL →</a>
    </div>
{article_rows}
  </section>

  {REFBOX}

</div>

{TB_FOOTER}

{COPY_SCRIPT}
</body>
</html>
'''

(SITE_ROOT / 'index.html').write_text(home_html, encoding='utf-8')
print("✓ index.html written")

# ── Build blog/index.html ───────────────────────────────────────────────────
en_rows = '\n'.join(render_article_row(p) for p in en_posts)
lang_rows = '\n'.join(render_lang_row(p) for p in lang_posts)

blog_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Blog — Tesla News &amp; Guides for Europe | TeslaBlog.eu</title>
  <meta name="description" content="All TeslaBlog.eu articles: Tesla buying guides, software updates, FSD coverage, and referral explainers for European drivers.">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://teslablog.eu/blog/">
  <link rel="alternate" hreflang="en" href="https://teslablog.eu/blog/">
  <link rel="alternate" hreflang="x-default" href="https://teslablog.eu/">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://teslablog.eu/blog/">
  <meta property="og:title" content="Blog — Tesla News &amp; Guides for Europe | TeslaBlog.eu">
  <meta property="og:description" content="Independent Tesla blog for European drivers. Software updates, buying guides, and EV news.">
  <meta property="og:site_name" content="TeslaBlog.eu">
  <meta property="og:image" content="https://teslablog.eu/assets/og/blog.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="https://teslablog.eu/assets/og/blog.png">
  <link rel="stylesheet" href="/css/style.css">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Blog",
    "name": "TeslaBlog.eu",
    "url": "https://teslablog.eu/blog/",
    "description": "Independent Tesla blog for European drivers — software updates, buying guides, EV news.",
    "inLanguage": "en",
    "publisher": {{ "@type": "Organization", "name": "TeslaBlog.eu", "url": "https://teslablog.eu/" }}
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{ "@type": "ListItem", "position": 1, "name": "Home", "item": "https://teslablog.eu/" }},
      {{ "@type": "ListItem", "position": 2, "name": "Blog", "item": "https://teslablog.eu/blog/" }}
    ]
  }}
  </script>
  {GA_SNIPPET}
</head>
<body>

{masthead('EN')}

<div class="tb-wrap">

  <section class="tb-hero tb-hero-page">
    <h1>Articles<span class="tb-dot">.</span></h1>
    <p class="tb-intro">Buying guides, software coverage, and referral explainers for European Tesla drivers.</p>
    <div class="tb-status"><span class="tb-sq"></span>{len(en_posts)} ARTICLES · {len(lang_posts)} IN OTHER LANGUAGES</div>
  </section>

  <section class="tb-section">
    <div class="tb-sechead">
      <span class="tb-num">01</span>
      <span class="tb-seclabel">All articles</span>
    </div>
{en_rows}
  </section>

  <section class="tb-section">
    <div class="tb-sechead">
      <span class="tb-num">02</span>
      <span class="tb-seclabel">Other languages</span>
    </div>
{lang_rows}
  </section>

  {REFBOX}

</div>

{TB_FOOTER}

{COPY_SCRIPT}
</body>
</html>
'''

(BLOG_DIR / 'index.html').write_text(blog_html, encoding='utf-8')
print(f"✓ blog/index.html written ({len(en_posts)} EN posts, {len(lang_posts)} other language posts)")


# ── Share cards (og:image) — guarded so a missing Pillow never breaks the run
try:
    import subprocess
    subprocess.run(['python3', str(SITE_ROOT / 'scripts' / 'generate-og-images.py'), '--quiet'],
                   timeout=300, check=False)
except Exception as e:
    print(f'og-images skipped: {e}')
