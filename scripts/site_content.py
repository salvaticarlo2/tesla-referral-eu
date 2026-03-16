#!/usr/bin/env python3

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo


REFERRAL_DEADLINE = date(2026, 3, 31)
SITE_TZ = ZoneInfo("Europe/Zurich")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def build_date() -> date:
    override = os.environ.get("BUILD_DATE")
    if override:
        return date.fromisoformat(override)
    return datetime.now(SITE_TZ).date()


def human_date(value: date) -> str:
    return f"{value.strftime('%B')} {value.day}, {value.year}"


def iso_date(value: date) -> str:
    return value.isoformat()


def referral_days_left(value: date) -> int:
    return (REFERRAL_DEADLINE - value).days


def offer_label(days_left: int) -> str:
    if days_left > 1:
        return f"{days_left} Days Left"
    if days_left == 1:
        return "1 Day Left"
    if days_left == 0:
        return "Offer Ends Today"
    return "Offer Ended"


def offer_inline(days_left: int) -> str:
    if days_left > 1:
        return f"{days_left} days left"
    if days_left == 1:
        return "1 day left"
    if days_left == 0:
        return "ends today"
    return "offer ended"


def only_days_left(days_left: int) -> str:
    if days_left > 1:
        return f"Only {days_left} days left"
    if days_left == 1:
        return "Only 1 day left"
    if days_left == 0:
        return "Offer ends today"
    return "Offer ended March 31"


def days_remain_sentence(days_left: int) -> str:
    if days_left > 1:
        return f"Only {days_left} days remain."
    if days_left == 1:
        return "Only 1 day remains."
    if days_left == 0:
        return "The offer ends today."
    return "The offer ended on March 31, 2026."


def urgency_sentence(days_left: int) -> str:
    if days_left > 1:
        return (
            f"With only {days_left} days remaining, acting quickly is essential "
            "to secure the deal."
        )
    if days_left == 1:
        return "With only 1 day remaining, acting quickly is essential to secure the deal."
    if days_left == 0:
        return "The deadline is today, so acting quickly is essential to secure the deal."
    return "The offer ended on March 31, 2026."


def referral_deadline_sentence(value: date) -> str:
    days_left = referral_days_left(value)
    if days_left > 1:
        return f"That's {days_left} days from {human_date(value)}."
    if days_left == 1:
        return f"That's 1 day from {human_date(value)}."
    if days_left == 0:
        return f"That deadline is today, {human_date(value)}."
    return "That deadline has now passed."

