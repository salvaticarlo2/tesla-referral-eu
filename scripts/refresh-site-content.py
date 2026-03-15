#!/usr/bin/env python3

from __future__ import annotations

import re
from pathlib import Path

from site_content import (
    build_date,
    days_remain_sentence,
    human_date,
    iso_date,
    offer_inline,
    offer_label,
    only_days_left,
    referral_days_left,
    referral_deadline_sentence,
    repo_root,
    urgency_sentence,
)


ROOT = repo_root()
TODAY = build_date()
TODAY_HUMAN = human_date(TODAY)
TODAY_ISO = iso_date(TODAY)
DAYS_LEFT = referral_days_left(TODAY)


def replace_required(text: str, pattern: str, replacement, path: Path) -> str:
    updated, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    if count == 0:
        raise RuntimeError(f"Pattern not found in {path}: {pattern}")
    return updated


def update_date_modified(text: str, path: Path) -> str:
    return replace_required(
        text,
        r'("dateModified"\s*:\s*")[0-9]{4}-[0-9]{2}-[0-9]{2}(")',
        lambda match: f"{match.group(1)}{TODAY_ISO}{match.group(2)}",
        path,
    )


def write_if_changed(path_str: str, updater) -> None:
    path = ROOT / path_str
    original = path.read_text()
    updated = updater(original, path)
    if updated != original:
        path.write_text(updated)


def refresh_march_deals(text: str, path: Path) -> str:
    text = replace_required(
        text,
        r"<strong>⏰ [^<]+</strong>",
        f"<strong>⏰ {offer_label(DAYS_LEFT)}:</strong>",
        path,
    )
    text = update_date_modified(text, path)
    text = replace_required(
        text,
        r"(Published March 4, 2026 · Updated )[A-Za-z]+ \d{1,2}, \d{4}",
        lambda match: f"{match.group(1)}{TODAY_HUMAN}",
        path,
    )
    return text


def refresh_uk_trade_in(text: str, path: Path) -> str:
    text = replace_required(
        text,
        r"Only \d+ days left",
        only_days_left(DAYS_LEFT),
        path,
    )
    text = replace_required(
        text,
        r"Only \d+ days remain\.",
        days_remain_sentence(DAYS_LEFT),
        path,
    )
    text = replace_required(
        text,
        r"With only \d+ days remaining, acting quickly is essential to secure the deal\.",
        urgency_sentence(DAYS_LEFT),
        path,
    )
    text = update_date_modified(text, path)
    return text


def refresh_navigate_on_autosteer(text: str, path: Path) -> str:
    text = replace_required(
        text,
        r"Referral deadline — [^<]+:",
        f"Referral deadline — {offer_inline(DAYS_LEFT)}:",
        path,
    )
    text = update_date_modified(text, path)
    text = replace_required(
        text,
        r"(<span>By Carlo</span> · <span>)[A-Za-z]+ \d{1,2}, \d{4}(</span> · <span>7 min read</span>)",
        lambda match: f"{match.group(1)}{TODAY_HUMAN}{match.group(2)}",
        path,
    )
    return text


def refresh_referral_program_update(text: str, path: Path) -> str:
    text = replace_required(
        text,
        r"That's \d+ days from [A-Za-z]+ \d{1,2}, \d{4}\.",
        referral_deadline_sentence(TODAY),
        path,
    )
    text = replace_required(
        text,
        r"As of [A-Za-z]+ \d{1,2}, \d{4},",
        f"As of {TODAY_HUMAN},",
        path,
    )
    text = update_date_modified(text, path)
    text = replace_required(
        text,
        r'(<time datetime=")[0-9-]+(">)[A-Za-z]+ \d{1,2}, \d{4}(</time>)',
        lambda match: f'{match.group(1)}{TODAY_ISO}{match.group(2)}{TODAY_HUMAN}{match.group(3)}',
        path,
    )
    return text


def main() -> None:
    write_if_changed("blog/tesla-march-2026-deals/index.html", refresh_march_deals)
    write_if_changed("blog/tesla-uk-trade-in-bonus-march-2026/index.html", refresh_uk_trade_in)
    write_if_changed(
        "blog/tesla-navigate-on-autosteer-europe-2026/index.html",
        refresh_navigate_on_autosteer,
    )
    write_if_changed(
        "blog/tesla-referral-program-march-2026-update/index.html",
        refresh_referral_program_update,
    )


if __name__ == "__main__":
    main()
