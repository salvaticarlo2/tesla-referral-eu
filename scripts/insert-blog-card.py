#!/usr/bin/env python3
"""
insert-blog-card.py — idempotent inserts for teslablog.eu post listings.

Uses targeted regex insertion (not full HTML parsing) so the rest of the file
is left exactly as-is. BS4's re-serialization was too aggressive: it was
lowercasing attributes, reordering them, and collapsing whitespace, producing
huge noisy diffs. Surgical insertion keeps git history clean.

Modes:

  --mode blog-index  --file /root/tesla-referral-eu/blog/index.html
    Inserts a <article class="blog-card"> as the first child of
    <div class="article-list">.

  --mode homepage    --file /root/tesla-referral-eu/index.html
    (a) Prepends an entry to the "blogPost": [...] array of the JSON-LD
        <script> whose top-level "@type" is "Blog". Caps at 10 entries.
    (b) Inserts a <article class="post-item"> immediately after
        <p class="list-section-label">Latest Articles</p>. Caps at 10.

Idempotent: if the slug's URL already appears in the file, nothing changes.

No external deps (stdlib only).
"""

import argparse
import json
import re
import sys
from pathlib import Path


# --------------------------- helpers ---------------------------

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fmt_month_year(date_iso: str) -> str:
    """'2026-04-15' -> 'Apr 2026'."""
    y, m, _d = date_iso.split("-")
    return f"{MONTHS[int(m) - 1]} {y}"


def post_url(slug: str) -> str:
    return f"https://teslablog.eu/blog/{slug}/"


def post_path(slug: str) -> str:
    return f"/blog/{slug}/"


def category_tag_value(language: str, category: str) -> str:
    """The category-tag text shown on listing cards."""
    if category:
        return category
    flag_map = {"en": "🇬🇧 English", "de": "🇩🇪 Deutsch", "fr": "🇫🇷 Français",
                "nl": "🇳🇱 Nederlands", "no": "🇳🇴 Norsk", "it": "🇮🇹 Italiano"}
    return flag_map.get(language, "Blog")


# --------------------------- blog-index mode ---------------------------

def build_blog_card(*, slug, title, date, language, category, description):
    desc_line = f"        <p>{description}</p>\n" if description else ""
    return (
        "    <article class=\"blog-card\">\n"
        "      <div class=\"blog-card-content\">\n"
        f"        <span class=\"category-tag\">{category_tag_value(language, category)}</span>\n"
        f"        <h2><a href=\"{post_path(slug)}\">{title}</a></h2>\n"
        f"{desc_line}"
        f"        <div class=\"article-meta\">{fmt_month_year(date)}</div>\n"
        "      </div>\n"
        "    </article>\n"
    )


def insert_into_blog_index(html: str, *, slug, title, date, language,
                           category, description) -> str:
    # Idempotency
    if post_path(slug) in html:
        print(f"[blog-index] slug '{slug}' already present — no change.")
        return html

    card = build_blog_card(slug=slug, title=title, date=date,
                           language=language, category=category,
                           description=description)

    # Find <div class="article-list"> ... insert card right after the opening tag
    # (and after any whitespace) so the new card is the first child.
    pattern = re.compile(r'(<div class="article-list">\s*\n)', re.IGNORECASE)
    new_html, count = pattern.subn(r"\1" + card, html, count=1)
    if count == 0:
        raise RuntimeError(
            "Could not find '<div class=\"article-list\">' in blog/index.html — "
            "structure changed? Insertion aborted."
        )
    print(f"[blog-index] inserted card for '{slug}' as first child of .article-list")
    return new_html


# --------------------------- homepage: JSON-LD ---------------------------

def update_homepage_jsonld(html: str, *, slug, title, date) -> tuple[str, bool]:
    """Prepend a new BlogPosting entry to the blogPost array inside the
    JSON-LD <script> block whose top-level @type is "Blog".

    Uses surgical text insertion (NOT full JSON parse+reserialize) so the
    rest of the JSON-LD block keeps its existing formatting. Caps at 10.

    Returns (new_html, changed).
    """
    # Idempotency: if this URL is already in the JSON-LD, skip.
    if post_url(slug) in html:
        return html, False

    # 1. Find the JSON-LD <script> block that contains '"blogPost":'
    script_pattern = re.compile(
        r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
        re.DOTALL,
    )
    match = None
    for m in script_pattern.finditer(html):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") == "Blog" \
                and isinstance(data.get("blogPost"), list):
            match = m
            break
    if match is None:
        return html, False  # No Blog JSON-LD — nothing to update.

    block = match.group(0)

    # 2. Find the '[' that opens the blogPost array. NOTE: no trailing \s*
    #    so we can detect the indentation that follows.
    open_re = re.search(r'"blogPost"\s*:\s*\[', block)
    if not open_re:
        return html, False

    # 3. Detect indentation of existing entries: look at the whitespace between
    #    `[` and the first `{`.
    after_bracket = block[open_re.end():]
    first_entry_match = re.match(r'(?P<ws>[ \t\n]*)\{', after_bracket)
    if first_entry_match and "\n" in first_entry_match.group("ws"):
        # ws looks like "\n      " — take spaces after the last newline
        ws = first_entry_match.group("ws")
        entry_indent = ws.rsplit("\n", 1)[-1]  # "      " (outer brace indent)
    else:
        # Fallback indent if array is empty or single-line
        entry_indent = "      "

    # Probe inner-key indent by inspecting the first entry's first key line
    inner_indent = entry_indent + "      "  # default
    first_key_match = re.search(
        r'\{\s*\n([ \t]+)"', block[open_re.end():],
    )
    if first_key_match:
        inner_indent = first_key_match.group(1)

    # 4. Build the new entry body (multi-line, matching existing style)
    new_entry_body = (
        "{\n"
        + inner_indent + '"@type": "BlogPosting",\n'
        + inner_indent + f'"headline": "{_jq(title)}",\n'
        + inner_indent + f'"url": "{post_url(slug)}",\n'
        + inner_indent + f'"datePublished": "{date}"\n'
        + entry_indent + "},\n"
        + entry_indent
    )

    # 5. Insert it right after the opening '[' plus a newline + entry_indent.
    #    We want the resulting text to read:
    #       "blogPost": [
    #             {      <-- new entry (entry_indent)
    #                  ...keys (inner_indent)
    #             },
    #             {      <-- original first entry (preserved as-is)
    insert_pos = match.start() + open_re.end()
    new_html = (
        html[:insert_pos]
        + "\n" + entry_indent + new_entry_body
        + html[insert_pos + len(first_entry_match.group("ws") if first_entry_match else ""):]
    )

    # 6. Cap at 10 entries. Count "@type": "BlogPosting" occurrences inside the
    #    updated block. If >10, trim the last ones off.
    # Re-find the block (it moved) and cap.
    new_match = script_pattern.search(new_html)
    if new_match:
        new_block = new_match.group(0)
        entry_count = len(re.findall(r'"@type"\s*:\s*"BlogPosting"', new_block))
        if entry_count > 10:
            # Find positions of each "{ ... }, (or "}") inside the array.
            # Simpler: find all '{' positions inside the block that start a
            # BlogPosting, truncate after the 10th closing brace before the ']'.
            # We'll just truncate from the (limit+1)-th entry's opening '{' back
            # to and including its preceding comma. For safety, do a bounded
            # textual find of the 11th entry's start.
            array_start = re.search(r'"blogPost"\s*:\s*\[', new_block).end()
            entries_text = new_block[array_start:]
            # Split by entry via top-level '{...}' boundaries is complex; we'll
            # instead find each BlogPosting block by matching '{' ... '}' pairs
            # non-greedily (good enough given entries don't nest objects).
            entry_spans = []
            depth = 0
            entry_start_local = None
            for i, ch in enumerate(entries_text):
                if ch == '{':
                    if depth == 0:
                        entry_start_local = i
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0 and entry_start_local is not None:
                        entry_spans.append((entry_start_local, i + 1))
                        entry_start_local = None
                        if len(entry_spans) >= 11:
                            break
            if len(entry_spans) > 10:
                # Cut from the 11th entry's start (including any preceding ',')
                cut_start_local = entry_spans[10][0]
                # Walk backwards to swallow a comma and trailing whitespace
                while cut_start_local > 0 and entries_text[cut_start_local - 1] in " \n\t":
                    cut_start_local -= 1
                if cut_start_local > 0 and entries_text[cut_start_local - 1] == ',':
                    cut_start_local -= 1
                new_entries_text = entries_text[:cut_start_local]
                updated_block = new_block[:array_start] + new_entries_text + new_block[array_start + len(entries_text):]
                new_html = new_html[:new_match.start()] + updated_block + new_html[new_match.end():]

    return new_html, True


def _jq(s: str) -> str:
    """JSON-string-escape a plain string (for building JSON by hand)."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


# --------------------------- homepage: post-item ---------------------------

def build_post_item(*, slug, title, date, language, category, description):
    desc_line = f"      <p>{description}</p>\n" if description else ""
    return (
        "  <article class=\"post-item\">\n"
        f"    <div class=\"post-item-date\">{fmt_month_year(date)}</div>\n"
        "    <div class=\"post-item-body\">\n"
        f"      <div class=\"post-item-tag\">{category_tag_value(language, category)}</div>\n"
        f"      <h2><a href=\"{post_path(slug)}\">{title}</a></h2>\n"
        f"{desc_line}"
        f"      <a href=\"{post_path(slug)}\" class=\"read-more\">Read article →</a>\n"
        "    </div>\n"
        "  </article>\n"
    )


def insert_post_item(html: str, *, slug, title, date, language, category,
                     description) -> tuple[str, bool]:
    # Idempotency: check if the slug already appears inside a post-item block
    # (NOT just anywhere in the file — JSON-LD also contains the URL).
    post_item_re = re.compile(
        r'<article class="post-item">.*?</article>',
        re.DOTALL,
    )
    target = post_path(slug)
    for block in post_item_re.findall(html):
        if target in block:
            return html, False

    item = build_post_item(slug=slug, title=title, date=date,
                           language=language, category=category,
                           description=description)

    # Insert immediately after <p class="list-section-label">Latest Articles</p>
    pattern = re.compile(
        r'(<p class="list-section-label">Latest Articles</p>\s*\n)',
        re.IGNORECASE,
    )
    new_html, count = pattern.subn(r"\1\n" + item, html, count=1)
    if count == 0:
        print(
            "[homepage] WARN: '<p class=\"list-section-label\">Latest Articles</p>' "
            "not found. Skipping post-item insertion (JSON-LD may still be updated).",
            file=sys.stderr,
        )
        return html, False

    # Cap post-item count at 10 (drop oldest — they appear in order, oldest last)
    new_html = _cap_post_items(new_html, limit=10)

    return new_html, True


def _cap_post_items(html: str, *, limit: int) -> str:
    """Keep at most `limit` post-item articles. Drops later ones."""
    # Match each entire <article class="post-item">...</article> block.
    article_re = re.compile(
        r'<article class="post-item">.*?</article>\s*',
        re.DOTALL,
    )
    matches = list(article_re.finditer(html))
    if len(matches) <= limit:
        return html
    # Remove from the (limit)-th onward (0-indexed), going backwards so offsets stay valid.
    to_remove = matches[limit:]
    out = html
    for m in reversed(to_remove):
        out = out[:m.start()] + out[m.end():]
    return out


def insert_into_homepage(html: str, *, slug, title, date, language, category,
                        description) -> str:
    new_html, jsonld_changed = update_homepage_jsonld(
        html, slug=slug, title=title, date=date,
    )
    if jsonld_changed:
        print(f"[homepage] prepended '{slug}' to JSON-LD blogPost array")

    new_html2, item_changed = insert_post_item(
        new_html, slug=slug, title=title, date=date, language=language,
        category=category, description=description,
    )
    if item_changed:
        print(f"[homepage] inserted post-item for '{slug}' (capped at 10)")

    if not jsonld_changed and not item_changed:
        print(f"[homepage] slug '{slug}' already present — no change.")
    return new_html2


# --------------------------- CLI ---------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["blog-index", "homepage"], required=True)
    ap.add_argument("--file", required=True, help="absolute path to HTML file")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--language", required=True)
    ap.add_argument("--category", default="")
    ap.add_argument("--description", default="",
                    help="optional meta/excerpt shown on listing cards")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        sys.exit(66)

    html = path.read_text(encoding="utf-8")

    if args.mode == "blog-index":
        new_html = insert_into_blog_index(
            html, slug=args.slug, title=args.title, date=args.date,
            language=args.language, category=args.category,
            description=args.description,
        )
    else:
        new_html = insert_into_homepage(
            html, slug=args.slug, title=args.title, date=args.date,
            language=args.language, category=args.category,
            description=args.description,
        )

    if new_html != html:
        path.write_text(new_html, encoding="utf-8")
        print(f"Wrote {path}")
    else:
        print(f"No changes written to {path}")


if __name__ == "__main__":
    main()
