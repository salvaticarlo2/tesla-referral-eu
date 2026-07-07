#!/usr/bin/env python3
"""Generate /feed.xml from blog posts and news items."""
import json
import os
import re
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

# Script lives at <repo>/tools/news-pipeline/; data sits alongside it.
REPO_DIR = str(Path(__file__).resolve().parents[2])
SITE_URL = 'https://teslablog.eu'
FEED_TITLE = 'TeslaBlog.eu — Tesla News & Updates'
FEED_DESC = 'Latest Tesla news, deals, and updates across Europe and beyond.'
NEWS_DATA = str(Path(__file__).resolve().parent / 'data' / 'news.json')


def extract_blog_posts():
    """Extract metadata from blog/*/index.html via JSON-LD."""
    posts = []
    blog_dir = os.path.join(REPO_DIR, 'blog')
    for slug in sorted(os.listdir(blog_dir)):
        index = os.path.join(blog_dir, slug, 'index.html')
        if not os.path.isfile(index):
            continue
        with open(index, 'r', encoding='utf-8') as f:
            html = f.read()
        m = re.search(
            r'<script\s+type="application/ld\+json">\s*(\{[^<]*"@type"\s*:\s*"Article"[^<]*\})\s*</script>',
            html, re.DOTALL
        )
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


def load_news_items():
    """Load news items from news.json if it exists."""
    if not os.path.isfile(NEWS_DATA):
        return []
    with open(NEWS_DATA, 'r', encoding='utf-8') as f:
        items = json.load(f)
    return [{
        'title': it['title'],
        'link': f'{SITE_URL}/news/{it["slug"]}/',
        'description': it.get('summary', ''),
        'pubDate': it.get('timestamp', ''),
        'guid': f'{SITE_URL}/news/{it["slug"]}/',
    } for it in items]


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
    for it in items[:50]:
        item = SubElement(channel, 'item')
        SubElement(item, 'title').text = it['title']
        SubElement(item, 'link').text = it['link']
        SubElement(item, 'description').text = it['description']
        SubElement(item, 'guid', isPermaLink='true').text = it['guid']
        if it.get('pubDate'):
            try:
                dt = datetime.fromisoformat(it['pubDate'].replace('Z', '+00:00'))
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
    news = load_news_items()
    all_items = posts + news
    xml = build_rss(all_items)
    out = os.path.join(REPO_DIR, 'feed.xml')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(xml)
    print(f'Generated feed.xml ({len(all_items)} items)')


if __name__ == '__main__':
    main()
