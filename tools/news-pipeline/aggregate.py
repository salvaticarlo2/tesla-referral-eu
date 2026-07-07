#!/usr/bin/env python3
"""Fetch Tesla RSS feeds, deduplicate, categorize, store in news.json."""
import json
import os
import re
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path

import feedparser
from bs4 import BeautifulSoup

# Data lives next to this script (tools/news-pipeline/data/); no /root deps.
DATA_DIR = str(Path(__file__).resolve().parent / 'data')
NEWS_FILE = os.path.join(DATA_DIR, 'news.json')
SOURCES_FILE = os.path.join(DATA_DIR, 'sources.json')
LOG_FILE = os.path.join(DATA_DIR, 'pipeline.log')

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s [aggregate] %(levelname)s %(message)s',
)
log = logging.getLogger(__name__)

# Items must match at least one keyword to be included
TESLA_KEYWORDS = [
    'tesla', 'elon musk', 'musk', 'cybertruck', 'model y', 'model 3',
    'model s', 'model x', 'supercharger', 'megacharger', 'autopilot',
    'fsd', 'full self-driving', 'self-driving', 'optimus', 'megapack',
    'powerwall', 'cybercab', 'robotaxi', 'robo-taxi', 'tsla',
    'gigafactory', 'giga berlin', 'giga texas', 'giga shanghai',
    'fremont', 'tesla semi', 'dojo', 'starlink', 'spacex',
    'terafab', 'roadster',
]


def is_tesla_relevant(title, summary):
    """Check if content is about Tesla or closely related topics."""
    text = (title + ' ' + summary).lower()
    return any(kw in text for kw in TESLA_KEYWORDS)


def load_sources():
    with open(SOURCES_FILE, 'r') as f:
        return json.load(f)


def load_existing():
    if os.path.isfile(NEWS_FILE):
        with open(NEWS_FILE, 'r') as f:
            return json.load(f)
    return []


def save_news(items):
    with open(NEWS_FILE, 'w') as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:80].rstrip('-')


def extract_summary(entry):
    """Extract 2-3 sentence summary from RSS entry."""
    content = ''
    if hasattr(entry, 'content') and entry.content:
        content = entry.content[0].get('value', '')
    elif hasattr(entry, 'summary'):
        content = entry.summary or ''
    elif hasattr(entry, 'description'):
        content = entry.description or ''

    soup = BeautifulSoup(content, 'lxml')
    text = soup.get_text(separator=' ', strip=True)
    text = unescape(text)

    sentences = re.split(r'(?<=[.!?])\s+', text)
    summary = ' '.join(sentences[:3])
    if len(summary) > 300:
        summary = summary[:297] + '...'
    return summary


def categorize(title, summary, keywords_map, default_cat):
    """Assign category based on keyword matching."""
    text = (title + ' ' + summary).lower()
    best_cat = default_cat
    best_score = 0
    for cat, keywords in keywords_map.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_cat = cat
    return best_cat


def normalize_title(title):
    return re.sub(r'[^\w\s]', '', title.lower()).strip()


def is_duplicate(new_title, new_url, existing):
    norm_new = normalize_title(new_title)
    for item in existing:
        if item['source_url'] == new_url:
            return True
        norm_existing = normalize_title(item['title'])
        words_new = set(norm_new.split())
        words_existing = set(norm_existing.split())
        if not words_new or not words_existing:
            continue
        overlap = len(words_new & words_existing)
        ratio = overlap / max(len(words_new), len(words_existing))
        if ratio > 0.85:
            return True
    return False


def parse_date(entry):
    for attr in ('published_parsed', 'updated_parsed'):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                dt = datetime(*parsed[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except (ValueError, TypeError):
                pass
    return datetime.now(timezone.utc).isoformat()


def main():
    config = load_sources()
    existing = load_existing()
    keywords_map = config.get('category_keywords', {})
    new_count = 0
    skipped_irrelevant = 0

    for source in config['feeds']:
        if not source.get('enabled', True):
            continue
        name = source['name']
        url = source['url']
        log.info(f'Fetching {name}: {url}')

        try:
            feed = feedparser.parse(url)
        except Exception as e:
            log.error(f'Failed to fetch {name}: {e}')
            continue

        if feed.bozo and not feed.entries:
            log.warning(f'Feed error for {name}: {feed.bozo_exception}')
            continue

        for entry in feed.entries[:20]:
            title = getattr(entry, 'title', '').strip()
            link = getattr(entry, 'link', '').strip()
            if not title or not link:
                continue

            if is_duplicate(title, link, existing):
                continue

            summary = extract_summary(entry)

            # Tesla relevance filter — skip non-Tesla content
            if not is_tesla_relevant(title, summary):
                skipped_irrelevant += 1
                continue

            category = categorize(
                title, summary,
                keywords_map, source.get('category_default', 'Vehicles')
            )
            slug = slugify(title)
            existing_slugs = {it['slug'] for it in existing}
            if slug in existing_slugs:
                slug = slug + '-' + hashlib.md5(link.encode()).hexdigest()[:6]

            item = {
                'title': title,
                'slug': slug,
                'summary': summary,
                'source_url': link,
                'source_name': name,
                'category': category,
                'timestamp': parse_date(entry),
                'created_at': datetime.now(timezone.utc).isoformat(),
            }
            existing.append(item)
            new_count += 1
            log.info(f'  + {title[:60]}')

    existing.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    # Retain only last 90 days
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    existing = [it for it in existing if it.get('timestamp', '') >= cutoff]
    save_news(existing)
    log.info(f'Aggregation complete: {new_count} new, {skipped_irrelevant} skipped (not Tesla), {len(existing)} total')
    print(f'{new_count} new items, {skipped_irrelevant} skipped (not Tesla), {len(existing)} total')


if __name__ == '__main__':
    main()
