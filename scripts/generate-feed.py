#!/usr/bin/env python3
"""Generate /feed.xml from the real blog posts.

Replaces tools/news-pipeline/generate_feed.py, which only ran as step 4 of the
news pipeline. That pipeline was retired on 2026-07-24, which left feed.xml
frozen at its last news-era build: new blog posts never reached the feed.

This version reads blog/ only. It deliberately does not touch
tools/news-pipeline/data/news.json, which is still in the repo for rollback:
those /news/ URLs return 410 Gone and must never re-enter the feed.

Run directly, or let scripts/generate-indexes.py call it (it does, at the end).
"""
import json
import os
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

REPO_DIR = str(Path(__file__).resolve().parents[1])
SITE_URL = 'https://teslablog.eu'
FEED_TITLE = 'TeslaBlog.eu — Tesla News & Updates'
FEED_DESC = 'Latest Tesla news, deals, and updates across Europe and beyond.'
MAX_ITEMS = 50

# Posts use BlogPosting; older ones use Article, one uses NewsArticle.
LD_RE = re.compile(
    r'<script\s+type="application/ld\+json">\s*'
    r'(\{[^<]*"@type"\s*:\s*"(?:Article|BlogPosting|NewsArticle)"[^<]*\})\s*</script>',
    re.DOTALL,
)

# The channel declares <language>en</language>, and translated posts have their
# own /de/ /es/ /fr/ /it/ /nl/ trees, so keep the feed English-only.
LANG_RE = re.compile(r'<html[^>]*\blang="([a-z-]+)"', re.IGNORECASE)


def extract_blog_posts():
    """Extract post metadata from blog/*/index.html via JSON-LD."""
    posts = []
    blog_dir = os.path.join(REPO_DIR, 'blog')
    for slug in sorted(os.listdir(blog_dir)):
        index = os.path.join(blog_dir, slug, 'index.html')
        if not os.path.isfile(index):
            continue
        with open(index, 'r', encoding='utf-8') as f:
            html = f.read()
        lang = LANG_RE.search(html)
        if lang and not lang.group(1).lower().startswith('en'):
            continue
        m = LD_RE.search(html)
        if not m:
            continue
        try:
            ld = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        posts.append({
            'title': ld.get('headline', slug),
            'link': f'{SITE_URL}/blog/{slug}/',
            'description': ld.get('description', ''),
            'pubDate': ld.get('datePublished', ''),
            'guid': f'{SITE_URL}/blog/{slug}/',
        })
    return posts


def build_rss(items):
    """Build RSS 2.0 XML string."""
    rss = Element('rss', version='2.0', attrib={
        'xmlns:atom': 'http://www.w3.org/2005/Atom'
    })
    channel = SubElement(rss, 'channel')
    SubElement(channel, 'title').text = FEED_TITLE
    SubElement(channel, 'link').text = SITE_URL
    SubElement(channel, 'description').text = FEED_DESC
    SubElement(channel, 'language').text = 'en'
    atom_link = SubElement(channel, 'atom:link')
    atom_link.set('href', f'{SITE_URL}/feed.xml')
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')

    items.sort(key=lambda x: x.get('pubDate', ''), reverse=True)
    for it in items[:MAX_ITEMS]:
        item = SubElement(channel, 'item')
        SubElement(item, 'title').text = it['title']
        SubElement(item, 'link').text = it['link']
        SubElement(item, 'description').text = it['description']
        SubElement(item, 'guid', isPermaLink='true').text = it['guid']
        if it.get('pubDate'):
            try:
                dt = datetime.fromisoformat(it['pubDate'].replace('Z', '+00:00'))
                # datePublished is usually a bare date; treat it as UTC so the
                # feed emits "+0000" rather than the "-0000" (unknown zone) form.
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                SubElement(item, 'pubDate').text = format_datetime(dt)
            except (ValueError, TypeError):
                SubElement(item, 'pubDate').text = it['pubDate']

    raw = tostring(rss, encoding='unicode')
    pretty = parseString(raw).toprettyxml(indent='  ')
    lines = pretty.split('\n')
    if lines[0].startswith('<?xml'):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    return '\n'.join(lines)


def main():
    posts = extract_blog_posts()
    if not posts:
        raise SystemExit('generate-feed: no blog posts found, refusing to write an empty feed')
    xml = build_rss(posts)
    out = os.path.join(REPO_DIR, 'feed.xml')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(xml)
    print(f'✓ feed.xml written ({len(posts)} posts)')


if __name__ == '__main__':
    main()
