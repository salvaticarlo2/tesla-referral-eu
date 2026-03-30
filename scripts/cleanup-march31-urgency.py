#!/usr/bin/env python3
"""
cleanup-march31-urgency.py
Strips March 31 countdown/urgency language from all teslablog.eu pages.
Keeps referral links and codes intact.

Usage:
  python3 scripts/cleanup-march31-urgency.py --dry-run   # Preview changes
  python3 scripts/cleanup-march31-urgency.py --apply      # Apply changes
  python3 scripts/cleanup-march31-urgency.py --apply --commit  # Apply + git commit + push
"""

import os
import re
import sys
import glob
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MODE = sys.argv[1] if len(sys.argv) > 1 else "--dry-run"
COMMIT = "--commit" in sys.argv

os.chdir(REPO)

changes = []

def log(phase, filepath, detail=""):
    changes.append((phase, filepath, detail))
    print(f"  [{phase}] {filepath}" + (f" — {detail}" if detail else ""))


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def find_html():
    return sorted(glob.glob("**/*.html", recursive=True))


# =========================================================================
# PHASE 1 — Remove urgency banner blocks
# Pattern: <!-- URGENCY BANNER: March 31 deadline ... --> <div ...>...</div>
# =========================================================================
def phase1_remove_banners(html_files):
    print("\n--- Phase 1: Removing urgency banner blocks ---")
    # Pattern A: banner inside a <section> wrapper (referral/index.html)
    section_banner_re = re.compile(
        r'\s*<!-- URGENCY BANNER: March 31 deadline[^>]*-->\s*'
        r'<section[^>]*>.*?</section>\s*',
        re.DOTALL
    )
    # Pattern B: banner as a direct <div> (country pages)
    div_banner_re = re.compile(
        r'\s*<!-- URGENCY BANNER: March 31 deadline[^>]*-->\s*'
        r'<div[^>]*>.*?</div>\s*',
        re.DOTALL
    )
    for f in html_files:
        content = read(f)
        if "URGENCY BANNER: March 31 deadline" not in content:
            continue
        log("banner", f)
        if MODE == "--apply":
            if section_banner_re.search(content):
                content = section_banner_re.sub('\n', content)
            else:
                content = div_banner_re.sub('\n', content)
            write(f, content)


# =========================================================================
# PHASE 2 — Clean <title> tags
# =========================================================================
def phase2_clean_titles(html_files):
    print("\n--- Phase 2: Cleaning <title> tags ---")
    title_re = re.compile(r'<title>(.*?)</title>')

    patterns = [
        (r'\s*—\s*Buy Before March 31', ''),
        (r'\s*—\s*Only \d+ Days? Left', ''),
        (r'\s*\[Expires? Mar(?:ch)? 31\]', ''),
        (r'\s*\[March 31\]', ''),
        (r':\s*Save .{1,20}Before March 31\s*—', ':'),
        (r'\s*—\s*\d+ Days? Left', ''),
        (r'Only \d+ Days? Left\s*', ''),
        (r'\s*Before March 31\b', ''),
    ]

    for f in html_files:
        content = read(f)
        m = title_re.search(content)
        if not m:
            continue
        title = m.group(1)
        if not re.search(r'March 31|Mar 31|Days? Left', title, re.IGNORECASE):
            continue

        new_title = title
        for pat, repl in patterns:
            new_title = re.sub(pat, repl, new_title)
        new_title = re.sub(r'\s+', ' ', new_title).strip()

        if new_title != title:
            log("title", f, f'"{title}" -> "{new_title}"')
            if MODE == "--apply":
                content = content.replace(f'<title>{title}</title>',
                                          f'<title>{new_title}</title>')
                write(f, content)


# =========================================================================
# PHASE 3 — Clean meta descriptions and OG/Twitter tags
# =========================================================================
def phase3_clean_meta(html_files):
    print("\n--- Phase 3: Cleaning meta descriptions ---")
    meta_re = re.compile(
        r'<meta\s+(name|property)="(description|og:description|og:title|'
        r'twitter:description|twitter:title)"\s+content="([^"]*)"',
        re.IGNORECASE
    )

    desc_patterns = [
        (r'Offer expires March 31, 2026\.?\s*', ''),
        (r'Expires March 31, 2026\.?\s*', ''),
        (r'Valid until March 31, 2026\.?\s*', ''),
        (r'Referral program expires March 31, 2026\.?\s*', ''),
        (r'\s*—\s*expires March 31\.?', '.'),
        (r'\s*expires March 31\.?', '.'),
        (r'\s*—\s*\d+ days? left\.?', '.'),
        (r'\s*\d+ days? left\.?', ''),
        (r'Only \d+ Days? Left\s*', ''),
        (r'\[March 31\]', ''),
        (r'\[Expires? Mar(?:ch)? 31\]', ''),
        (r'Buy Before March 31\.?\s*', ''),
        (r'before March 31\.?', '.'),
        (r'Act before the deadline\.?\s*', ''),
        (r'—\s*Buy Before March 31', ''),
        (r'until March 31, 2026', ''),
        (r'through March 31, 2026', ''),
        (r'before March 31', ''),
    ]

    for f in html_files:
        content = read(f)
        if not re.search(r'March 31|Mar 31|days? left', content, re.IGNORECASE):
            continue

        changed = False
        def replace_meta(m):
            nonlocal changed
            attr, name, val = m.group(1), m.group(2), m.group(3)
            new_val = val
            for pat, repl in desc_patterns:
                new_val = re.sub(pat, repl, new_val, flags=re.IGNORECASE)
            # Also clean title patterns for og:title and twitter:title
            if 'title' in name.lower():
                new_val = re.sub(r'\s*—\s*Buy Before March 31', '', new_val)
                new_val = re.sub(r'\s*\[Expires? Mar(?:ch)? 31\]', '', new_val)
                new_val = re.sub(r'\s*\[March 31\]', '', new_val)
                new_val = re.sub(r':\s*Save .{1,20}Before March 31\s*—', ':', new_val)
                new_val = re.sub(r'\s*Before March 31\b', '', new_val)
            # Clean double periods, trailing spaces
            new_val = re.sub(r'\.\.+', '.', new_val)
            new_val = re.sub(r'\s+', ' ', new_val).strip()
            new_val = new_val.rstrip('.')
            if new_val != val.rstrip('.'):
                changed = True
            return f'<meta {attr}="{name}" content="{new_val}"'

        new_content = meta_re.sub(replace_meta, content)
        if changed:
            log("meta", f)
            if MODE == "--apply":
                write(f, new_content)


# =========================================================================
# PHASE 4 — Clean JSON-LD structured data
# =========================================================================
def phase4_clean_jsonld(html_files):
    print("\n--- Phase 4: Cleaning JSON-LD structured data ---")
    for f in html_files:
        content = read(f)
        if "application/ld+json" not in content:
            continue
        if not re.search(r'March 31|Mar 31|days? left|days? remain', content, re.IGNORECASE):
            continue

        original = content
        # Clean headline fields
        content = re.sub(
            r'("headline":\s*")([^"]*)(March 31|Mar 31)([^"]*")',
            lambda m: m.group(0)
                .replace(" — Buy Before March 31", "")
                .replace(" [Expires Mar 31]", "")
                .replace(" [March 31]", "")
                .replace(": Save £3,750 Before March 31 —", ":"),
            content
        )
        # Clean countdown text in answers
        content = re.sub(
            r'With only \d+ days? remaining, acting quickly is essential to secure the deal\.',
            'Check Tesla\'s website for current availability.',
            content
        )
        content = re.sub(r'Only \d+ days? remain\.', '', content)
        content = re.sub(r' \d+ days? left\.', '.', content)
        content = re.sub(r'— \d+ days? left', '', content)

        if content != original:
            log("jsonld", f)
            if MODE == "--apply":
                write(f, content)


# =========================================================================
# PHASE 5 — Clean body text urgency phrases
# =========================================================================
def phase5_clean_body(html_files):
    print("\n--- Phase 5: Cleaning body text urgency phrases ---")
    for f in html_files:
        if "research/" in f:
            continue
        content = read(f)
        if not re.search(
            r'days?\s+left|act now|last chance|don.t miss|before the deadline|'
            r'hurry|ending soon|running out|Only \d+ day',
            content, re.IGNORECASE
        ):
            continue

        original = content

        # Remove standalone countdown markers
        content = re.sub(r'<strong>Only \d+ days? left</strong>', '', content)
        content = re.sub(r' · <strong>Only \d+ days? left</strong>', '', content)
        content = re.sub(r'· <strong>Only \d+ days? left</strong>', '', content)

        # Clean countdown phrases in running text
        content = re.sub(r'\s*—\s*\d+ days? left', '', content)
        content = re.sub(r'\.\s*Only \d+ days? remain\.', '.', content)
        content = re.sub(
            r'With only \d+ days? remaining, acting quickly is essential to secure the deal\.',
            'Check Tesla\'s website for current availability.',
            content
        )

        # Clean urgency CTAs
        content = re.sub(r"Don't wait — order before the deadline\.", '', content)
        content = re.sub(r"Don't miss the window\.", '', content)
        content = re.sub(r'Act before the deadline\.?\s*', '', content)

        # Clean countdown-specific banners with emoji
        content = re.sub(
            r'<strong>\u23f0 \d+ Days? Left:</strong>\s*',
            '<strong>Note:</strong> ',
            content
        )
        content = re.sub(
            r'<strong>\u23f0 2 Days Left:</strong>\s*',
            '<strong>Note:</strong> ',
            content
        )

        if content != original:
            log("body", f)
            if MODE == "--apply":
                write(f, content)


# =========================================================================
# PHASE 6 — Remove research snippet file
# =========================================================================
def phase6_cleanup_research():
    print("\n--- Phase 6: Cleanup research snippets ---")
    target = "research/march-31-urgency-snippets.html"
    if os.path.exists(target):
        log("research", target, "will be removed")
        if MODE == "--apply":
            os.remove(target)


# =========================================================================
# PHASE 7 — Summary & optional commit
# =========================================================================
def phase7_summary():
    print("\n=== Summary ===")
    print(f"Total changes prepared: {len(changes)}")

    # Count remaining March 31 references
    remaining = 0
    for f in find_html():
        content = read(f)
        if re.search(r'March 31|Mar 31', content, re.IGNORECASE):
            remaining += 1
    print(f"Files still referencing March 31 after cleanup: {remaining}")
    print("(Some factual March 31 references in article body text are expected)")

    if MODE == "--dry-run":
        print("\nDRY RUN COMPLETE. Run with --apply to make changes.")

    if MODE == "--apply" and COMMIT:
        print("\n--- Committing and pushing ---")
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run([
            "git", "commit", "-m",
            "SEO: remove expired referral deadline urgency\n\n"
            "Strip March 31 countdown language (urgency banners, countdown titles,\n"
            "deadline meta descriptions, body text urgency phrases) from all pages.\n"
            "Referral links and codes preserved — only deadline framing removed.\n\n"
            "Co-Authored-By: Paperclip <noreply@paperclip.ing>"
        ], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("Pushed to main. Netlify will auto-deploy.")


# =========================================================================
# Main
# =========================================================================
if __name__ == "__main__":
    if MODE not in ("--dry-run", "--apply"):
        print("Usage: python3 scripts/cleanup-march31-urgency.py [--dry-run|--apply] [--commit]")
        sys.exit(1)

    print(f"=== Tesla March 31 Urgency Cleanup ===")
    print(f"Mode: {MODE}")
    print(f"Commit: {COMMIT}")
    print(f"Repo: {REPO}")

    html_files = find_html()
    print(f"HTML files found: {len(html_files)}")

    phase1_remove_banners(html_files)
    phase2_clean_titles(html_files)
    phase3_clean_meta(html_files)
    phase4_clean_jsonld(html_files)
    phase5_clean_body(html_files)
    phase6_cleanup_research()
    phase7_summary()

    print("\nDone.")
