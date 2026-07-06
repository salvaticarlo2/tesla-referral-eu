#!/usr/bin/env python3
"""
generate-og-images.py — renders a Cold Minimal share card (1200x630 PNG)
for every blog post and core page, and points that page's og:image /
twitter:image metas at it. Idempotent: skips pages whose card exists and
whose metas already point at the right URL. Safe to run every pipeline
cycle; requires Pillow (guarded by the caller).
"""
import re
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OG_DIR = ROOT / 'assets' / 'og'
FONTS = Path(__file__).resolve().parent / 'ogfonts'
SITE = 'https://teslablog.eu'

INK = (17, 19, 24)
SEC = (105, 112, 128)
TER = (139, 145, 158)
HAIR = (231, 230, 225)
ORANGE = (235, 80, 23)
WHITE = (255, 255, 255)

W, H = 1200, 630
PAD = 72
QUIET = '--quiet' in sys.argv


def load(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render(title, kicker, footer_label, out_path):
    img = Image.new('RGB', (W, H), WHITE)
    d = ImageDraw.Draw(img)

    mono_sm = load('GeistMono-500.ttf', 30)
    # Masthead
    x = PAD
    d.text((x, PAD), 'TESLABLOG', font=mono_sm, fill=INK)
    x2 = x + d.textlength('TESLABLOG', font=mono_sm)
    d.text((x2, PAD), '.EU', font=mono_sm, fill=ORANGE)
    d.line([(PAD, PAD + 56), (W - PAD, PAD + 56)], fill=INK, width=3)

    # Kicker
    if kicker:
        d.text((PAD, PAD + 84), kicker.upper(), font=load('GeistMono-500.ttf', 26), fill=ORANGE)

    # Title, auto-sized
    max_w = W - 2 * PAD
    for size in (76, 66, 58, 50):
        f = load('Geist-700.ttf', size)
        lines = wrap(d, title, f, max_w)
        if len(lines) <= 4:
            break
    y = PAD + 136
    for ln in lines[:4]:
        d.text((PAD, y), ln, font=f, fill=INK)
        y += int(size * 1.14)

    # Footer row
    fy = H - PAD - 34
    d.rectangle([PAD, fy + 6, PAD + 22, fy + 28], fill=ORANGE)
    d.text((PAD + 40, fy), footer_label.upper(), font=load('GeistMono-500.ttf', 26), fill=TER)
    # Hairline frame
    d.rectangle([0, 0, W - 1, H - 1], outline=HAIR, width=2)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, 'PNG', optimize=True)


def title_of(html):
    m = re.search(r'<title>([^<]+)</title>', html)
    if not m:
        return None
    t = m.group(1)
    t = re.sub(r'\s*\|\s*TeslaBlog\.eu\s*$', '', t)
    t = t.replace('&amp;', '&').replace('&#x27;', "'").replace('&quot;', '"')
    return t.strip()


def kicker_of(html):
    m = re.search(r'class="category-tag"[^>]*>([^<]+)<', html)
    return m.group(1).strip() if m else ''


def date_of(html):
    m = re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})"', html)
    return m.group(1) if m else ''


def point_metas(path, slug):
    html = path.read_text(encoding='utf-8')
    url = f'{SITE}/assets/og/{slug}.png'
    new = re.sub(r'(<meta property="og:image" content=")[^"]+(">)', rf'\g<1>{url}\g<2>', html)
    new = re.sub(r'(<meta name="twitter:image" content=")[^"]+(">)', rf'\g<1>{url}\g<2>', new)
    if new != html:
        path.write_text(new, encoding='utf-8')
        return True
    return False


def main():
    made = pointed = 0
    targets = []  # (slug, page_path, title, kicker, footer)

    for d in sorted((ROOT / 'blog').iterdir()):
        p = d / 'index.html'
        if not d.is_dir() or not p.exists():
            continue
        html = p.read_text(encoding='utf-8')
        t = title_of(html)
        if not t:
            continue
        date = date_of(html)
        targets.append((d.name, p, t, kicker_of(html), date or 'teslablog.eu'))

    CORE = [
        ('home', ROOT / 'index.html', 'Tesla news & guides for Europe.', '', 'Independent · not affiliated with Tesla'),
        ('blog', ROOT / 'blog' / 'index.html', 'Articles.', '', 'Buying guides · software · referrals'),
        ('gear', ROOT / 'gear' / 'index.html', 'Gear.', 'Owner-tested', 'Accessories I actually bought'),
        ('referral', ROOT / 'referral' / 'index.html', 'Tesla referrals in Europe: how they work.', 'Referral', 'Status & verification guide'),
        ('about', ROOT / 'about' / 'index.html', 'About this site.', '', 'One owner · honest automation'),
    ]
    for slug, p, t, k, foot in CORE:
        if p.exists():
            targets.append((slug, p, t, k, foot))

    for slug, page, title, kicker, foot in targets:
        out = OG_DIR / f'{slug}.png'
        if not out.exists():
            render(title, kicker, foot, out)
            made += 1
        if point_metas(page, slug):
            pointed += 1

    if not QUIET:
        print(f'og-images: {made} rendered, {pointed} pages re-pointed, {len(targets)} total targets')


if __name__ == '__main__':
    main()
