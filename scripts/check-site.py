#!/usr/bin/env python3

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from site_content import (
    build_date,
    human_date,
    offer_inline,
    offer_label,
    only_days_left,
    referral_days_left,
    repo_root,
)


ROOT = repo_root()
TODAY = build_date()
TODAY_HUMAN = human_date(TODAY)
DAYS_LEFT = referral_days_left(TODAY)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_map = dict(attrs)
        value = attrs_map.get("href")
        if value:
            self.links.append(value)


def iter_html_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("index.html")
        if ".git" not in path.parts and ".claude" not in path.parts
    )


def resolve_internal_target(url: str) -> Path | None:
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc not in {"teslablog.eu", "www.teslablog.eu"}:
        return None

    if parsed.scheme in {"mailto", "tel", "javascript"}:
        return None

    path = parsed.path
    if not path or path == "/":
        return ROOT / "index.html"
    if not path.startswith("/"):
        return None

    relative = path.lstrip("/")
    target = ROOT / relative
    if path.endswith("/"):
        return target / "index.html"
    if target.suffix:
        return target
    if target.is_file():
        return target
    return target / "index.html"


def extract_date_pairs(text: str) -> list[tuple[str, str]]:
    published = re.findall(r'"datePublished"\s*:\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})', text)
    modified = re.findall(r'"dateModified"\s*:\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})', text)
    return list(zip(published, modified))


def main() -> int:
    errors: list[str] = []

    required_files = [
        ROOT / "favicon.svg",
        ROOT / "privacy/index.html",
        ROOT / "assets/teslablog-og-default.jpg",
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"Missing required file: {path.relative_to(ROOT)}")

    for path in iter_html_files():
        if '/news/' in str(path):
            continue  # News pages are auto-generated and don't follow blog validation rules
        text = path.read_text()
        rel = path.relative_to(ROOT)

        if "&amp;amp;" in text:
            errors.append(f"Double-escaped HTML entity in {rel}")

        for published, modified in extract_date_pairs(text):
            if published > TODAY.isoformat():
                errors.append(f"Future datePublished in {rel}: {published}")
            if modified > TODAY.isoformat():
                errors.append(f"Future dateModified in {rel}: {modified}")
            if modified < published:
                errors.append(f"dateModified earlier than datePublished in {rel}: {modified} < {published}")

        parser = LinkParser()
        parser.feed(text)
        for href in parser.links:
            target = resolve_internal_target(href)
            if target is None:
                continue
            if not target.exists():
                errors.append(f"Broken internal link in {rel}: {href}")

    deals_text = (ROOT / "blog/tesla-march-2026-deals/index.html").read_text()
    if offer_label(DAYS_LEFT) not in deals_text:
        errors.append("March deals countdown is out of sync")

    uk_text = (ROOT / "blog/tesla-uk-trade-in-bonus-march-2026/index.html").read_text()
    if only_days_left(DAYS_LEFT) not in uk_text:
        errors.append("UK trade-in countdown is out of sync")

    navigate_text = (ROOT / "blog/tesla-navigate-on-autosteer-europe-2026/index.html").read_text()
    expected_navigate = f"Referral deadline — {offer_inline(DAYS_LEFT)}:"
    if expected_navigate not in navigate_text:
        errors.append("Navigate on Autosteer referral countdown is out of sync")

    referral_update_text = (ROOT / "blog/tesla-referral-program-march-2026-update/index.html").read_text()
    if TODAY_HUMAN not in referral_update_text:
        errors.append("Referral program update date stamp is out of sync")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Site checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
