#!/usr/bin/env python3
"""
generate-indexes.py — auto-regenerates index.html and blog/index.html
from all post directories. Run by Netlify on every deploy.
"""
import os, re, json
from pathlib import Path
from datetime import datetime
from html import escape

SITE_ROOT = Path(__file__).parent.parent
BLOG_DIR = SITE_ROOT / 'blog'
GA_ID = 'G-VCL5P0HLMR'
REFERRAL_CODE = 'carlo719460'

NAV_HEADER_HOME = '''<header>
  <nav class="nav-inner">
    <a href="/" class="nav-logo">Tesla<span>Blog</span>.eu</a>
    <div class="nav-links">
      <a href="/" class="active">Home</a>
      <a href="/blog/">Blog</a>
      <a href="/referral/">Referral</a>
    </div>
    <div class="nav-langs">
      <a href="/" class="active" title="English">🇬🇧</a>
      <a href="/de/" title="Deutsch">🇩🇪</a>
      <a href="/fr/" title="Français">🇫🇷</a>
      <a href="/nl/" title="Nederlands">🇳🇱</a>
      <a href="/no/" title="Norsk">🇳🇴</a>
      <a href="/it/" title="Italiano">🇮🇹</a>
    </div>
  </nav>
</header>'''

NAV_HEADER_BLOG = '''<header>
  <nav class="nav-inner">
    <a href="/" class="nav-logo">Tesla<span>Blog</span>.eu</a>
    <div class="nav-links">
      <a href="/">Home</a>
      <a href="/blog/" class="active">Blog</a>
      <a href="/referral/">Referral</a>
    </div>
    <div class="nav-langs">
      <a href="/" class="active" title="English">🇬🇧</a>
      <a href="/de/" title="Deutsch">🇩🇪</a>
      <a href="/fr/" title="Français">🇫🇷</a>
      <a href="/nl/" title="Nederlands">🇳🇱</a>
      <a href="/no/" title="Norsk">🇳🇴</a>
      <a href="/it/" title="Italiano">🇮🇹</a>
    </div>
  </nav>
</header>'''

FOOTER_CTA = f'''<div class="footer-cta">
  <p>Ordering a Tesla? Use referral code <code>{REFERRAL_CODE}</code> to save up to €500 — <a href="https://www.tesla.com/referral/{REFERRAL_CODE}" target="_blank" rel="noopener">order with referral link</a> or <a href="/referral/">read the guide</a>.</p>
</div>'''

FOOTER = '''<footer>
  <div class="footer-inner">
    <nav class="footer-nav">
      <a href="/">Home</a>
      <a href="/blog/">Blog</a>
      <a href="/referral/">Referral Code</a>
      <a href="/blog/grok-ai-tesla-europe/">Grok AI</a>
      <a href="/de/">🇩🇪 DE</a>
      <a href="/fr/">🇫🇷 FR</a>
      <a href="/nl/">🇳🇱 NL</a>
      <a href="/no/">🇳🇴 NO</a>
      <a href="/it/">🇮🇹 IT</a>
    </nav>
    <p class="footer-meta">
      TeslaBlog.eu is an independent website not affiliated with Tesla, Inc. Referral benefits subject to change.
      "Tesla", "Model 3", "Model Y", "Model S", "Model X", "Supercharger" and "Autopilot" are trademarks of Tesla, Inc.
      © 2026 TeslaBlog.eu
    </p>
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

SIDEBAR = f'''<aside class="sidebar">
      <div class="sidebar-widget">
        <h3>Referral Code</h3>
        <div class="referral-box">
          <span class="code-label">Save up to €500 on your Tesla</span>
          <span class="referral-code-display" id="refCode" title="Click to copy">{REFERRAL_CODE}</span>
          <span class="copy-feedback" id="copyFeedback">&nbsp;</span>
          <a href="https://www.tesla.com/referral/{REFERRAL_CODE}" target="_blank" rel="noopener" class="btn-referral">Order with referral →</a>
          <p class="referral-note">Click the code to copy. Apply before ordering.</p>
        </div>
      </div>
      <div class="sidebar-widget">
        <h3>Country Guides</h3>
        <div class="sidebar-links">
          <a href="/de/">🇩🇪 Germany</a>
          <a href="/fr/">🇫🇷 France</a>
          <a href="/nl/">🇳🇱 Netherlands</a>
          <a href="/no/">🇳🇴 Norway</a>
          <a href="/it/">🇮🇹 Italy</a>
        </div>
      </div>
    </aside>'''

COPY_SCRIPT = '''<script>
  document.getElementById('refCode').addEventListener('click', function() {
    navigator.clipboard.writeText('carlo719460').then(function() {
      var fb = document.getElementById('copyFeedback');
      fb.textContent = '✓ Copied';
      setTimeout(function() { fb.innerHTML = '&nbsp;'; }, 2500);
    });
  });
</script>'''

LANG_FLAGS = {'de': '🇩🇪 Deutsch', 'fr': '🇫🇷 Français', 'nl': '🇳🇱 Nederlands',
              'no': '🇳🇴 Norsk', 'it': '🇮🇹 Italiano', 'es': '🇪🇸 Español'}

def extract_post(post_dir):
    html_file = post_dir / 'index.html'
    if not html_file.exists():
        return None
    html = html_file.read_text(encoding='utf-8')

    # Language
    lang_m = re.search(r'<html[^>]+lang="([^"]+)"', html)
    lang = lang_m.group(1) if lang_m else 'en'

    # Date from JSON-LD
    date_m = re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})', html)
    if not date_m:
        return None
    date_str = date_m.group(1)

    # Title from <title> tag (cleanest source)
    title_m = re.search(r'<title>([^<]+)</title>', html)
    title = title_m.group(1).strip() if title_m else post_dir.name
    # Remove site suffix if present
    title = re.sub(r'\s*[|—]\s*TeslaBlog\.eu$', '', title).strip()

    # Description from meta
    desc_m = re.search(r'<meta name="description" content="([^"]+)"', html)
    description = desc_m.group(1) if desc_m else ''

    # Category from first category-tag span
    cat_m = re.search(r'class="category-tag"[^>]*>([^<]+)<', html)
    category = cat_m.group(1).strip() if cat_m else 'Article'

    # Read time
    rt_m = re.search(r'(\d+)\s*min\s*read', html)
    read_time = int(rt_m.group(1)) if rt_m else None

    # Format date label
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    date_label = dt.strftime('%b %Y')

    return {
        'slug': post_dir.name,
        'lang': lang,
        'date': date_str,
        'date_label': date_label,
        'title': title,
        'description': description,
        'category': category,
        'read_time': read_time,
        'url': f'/blog/{post_dir.name}/',
    }

def read_more_text(category):
    c = category.lower()
    if 'guide' in c or 'buying' in c or 'country' in c:
        return 'Read guide →'
    return 'Read article →'

def render_post_item(p):
    """Homepage card format"""
    rm = read_more_text(p['category'])
    desc = escape(p['description'])
    title = escape(p['title'])
    cat = escape(p['category'])
    return f'''  <article class="post-item">
    <div class="post-item-date">{p['date_label']}</div>
    <div class="post-item-body">
      <div class="post-item-tag">{cat}</div>
      <h2><a href="{p['url']}">{title}</a></h2>
      <p>{desc}</p>
      <a href="{p['url']}" class="read-more">{rm}</a>
    </div>
  </article>'''

def render_blog_card(p):
    """Blog index card format"""
    rt = f' · {p["read_time"]} min' if p['read_time'] else ''
    desc = escape(p['description'])
    title = escape(p['title'])
    cat = escape(p['category'])
    return f'''    <article class="blog-card">
      <div class="blog-card-content">
        <span class="category-tag">{cat}</span>
        <h2><a href="{p['url']}">{title}</a></h2>
        <p>{desc}</p>
        <div class="article-meta">{p['date_label']}{rt}</div>
      </div>
    </article>'''

def render_lang_card(p):
    """Blog index other-language card"""
    flag_label = LANG_FLAGS.get(p['lang'], p['lang'].upper())
    title = escape(p['title'])
    return f'''        <article class="article-card">
          <div class="article-content">
            <span class="category-tag">{flag_label}</span>
            <h2><a href="{p['url']}">{title}</a></h2>
            <time>{p['date']}</time>
          </div>
        </article>'''

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
top10 = en_posts[:10]
jsonld_posts = json.dumps([{
    "@type": "BlogPosting",
    "headline": p['title'],
    "url": f"https://teslablog.eu{p['url']}",
    "datePublished": p['date']
} for p in top10[:5]], indent=6)

post_items_html = '\n'.join(render_post_item(p) for p in top10)

home_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TeslaBlog.eu — Tesla News &amp; Guides for Europe</title>
  <meta name="description" content="Independent Tesla blog for European drivers. Software updates, buying guides, Grok AI coverage, and practical tips from a Tesla owner in Europe.">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://teslablog.eu/">
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
  <meta property="og:image" content="https://teslablog.eu/assets/teslablog-og-default.jpg">
  <meta property="og:site_name" content="TeslaBlog.eu">
  <meta property="og:locale" content="en_US">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="TeslaBlog.eu — Tesla News &amp; Guides for Europe">
  <meta name="twitter:description" content="Independent Tesla blog for European drivers. Software updates, buying guides, and practical tips.">
  <meta name="twitter:image" content="https://teslablog.eu/assets/teslablog-og-default.jpg">
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

{NAV_HEADER_HOME}

<div class="site-intro">
  <h1>Tesla News &amp; Guides for Europe</h1>
  <p class="lead">An independent blog by a Tesla owner in Europe. Practical coverage of software updates, buying guides, and EV news.</p>
</div>

<div class="article-list-home">
  <p class="list-section-label">Latest</p>

{post_items_html}

</div>

{FOOTER_CTA}

{FOOTER}

</body>
</html>'''

(SITE_ROOT / 'index.html').write_text(home_html, encoding='utf-8')
print("✓ index.html written")

# ── Build blog/index.html ───────────────────────────────────────────────────
en_cards_html = '\n'.join(render_blog_card(p) for p in en_posts)
lang_cards_html = '\n'.join(render_lang_card(p) for p in lang_posts)

blog_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Blog — Tesla News &amp; Guides for Europe | TeslaBlog.eu</title>
  <meta name="description" content="All articles from TeslaBlog.eu — independent Tesla blog for European drivers. Software updates, buying guides, Grok AI, and EV news.">
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
  <link rel="canonical" href="https://teslablog.eu/blog/">
  <link rel="alternate" hreflang="en" href="https://teslablog.eu/blog/">
  <link rel="alternate" hreflang="x-default" href="https://teslablog.eu/">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://teslablog.eu/blog/">
  <meta property="og:title" content="Blog — Tesla News &amp; Guides for Europe | TeslaBlog.eu">
  <meta property="og:description" content="Independent Tesla blog for European drivers. Software updates, buying guides, and EV news.">
  <meta property="og:site_name" content="TeslaBlog.eu">
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

{NAV_HEADER_BLOG}

<nav class="breadcrumb" aria-label="Breadcrumb">
  <a href="/">Home</a>
  <span class="sep">›</span>
  <span>Blog</span>
</nav>

<main>

  <div class="page-header">
    <span class="label">All Articles</span>
    <h1>Tesla Blog Europe</h1>
    <p class="lead">Independent coverage of Tesla software, news, and buying guides for European drivers.</p>
  </div>

  <div class="layout-cols">
    <div class="main-col">
      <p class="list-heading">Latest Articles</p>
      <div class="article-list">

{en_cards_html}

      </div>

      <p class="list-heading" style="margin-top:2.5rem;">Articles in Other Languages</p>
      <div class="article-list">

{lang_cards_html}

      </div>
    </div>

    {SIDEBAR}
  </div>

</main>

{FOOTER_CTA}

{FOOTER}

{COPY_SCRIPT}
</body>
</html>'''

(BLOG_DIR / 'index.html').write_text(blog_html, encoding='utf-8')
print(f"✓ blog/index.html written ({len(en_posts)} EN posts, {len(lang_posts)} other language posts)")
