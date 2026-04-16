#!/usr/bin/env bash
#
# deploy-blog.sh — convert a markdown draft to HTML, wire it into teslablog.eu,
# commit, push, and ping IndexNow.
#
# Lives on the VPS at: /root/tesla-referral-eu/scripts/deploy-blog.sh
#
# Usage:
#   bash scripts/deploy-blog.sh /path/to/draft.md
#   bash scripts/deploy-blog.sh /path/to/draft.md --dry-run
#
# Frontmatter required (YAML between ---):
#   title:          string
#   slug:           kebab-case, no spaces  (becomes /blog/<slug>/)
#   target_keyword: string (for SEO tracking; not rendered)
#   description:    meta description, <160 chars
#   language:       en | de | fr | nl | no | it
#   date:           YYYY-MM-DD
#   category:       free text for the category-tag pill
#   og_image:       (optional) absolute URL; defaults to site OG default
#
# Body: everything after the closing ---
# MUST contain the string "referral/carlo719460" at least once (referral CTA rule).
#
# Exits non-zero on any failure.

set -euo pipefail

# ---------- args ----------
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <draft.md> [--dry-run]" >&2
  exit 64
fi

DRAFT="$1"
DRY_RUN=0
if [ "${2:-}" = "--dry-run" ]; then
  DRY_RUN=1
fi

if [ ! -f "$DRAFT" ]; then
  echo "ERROR: draft not found: $DRAFT" >&2
  exit 66
fi

# ---------- paths ----------
REPO="/root/tesla-referral-eu"
TEMPLATE="$REPO/scripts/templates/blog-template.html"
INSERT_PY="$REPO/scripts/insert-blog-card.py"
LOG="/root/.openclaw/workspace-tesla/indexing_log.txt"

if [ ! -f "$TEMPLATE" ]; then
  echo "ERROR: template not found: $TEMPLATE — run setup-deploy-blog.sh first." >&2
  exit 72
fi
if [ ! -f "$INSERT_PY" ]; then
  echo "ERROR: insert helper not found: $INSERT_PY — run setup-deploy-blog.sh first." >&2
  exit 72
fi

cd "$REPO"

# ---------- 1-3. Parse frontmatter, run pandoc, render template (one pass) ----------
# We do all three steps in a single Python invocation — avoids shell-quoting
# nightmares with HTML bodies and keeps error messages coherent.
#
# Inputs:  DRAFT (arg), TEMPLATE (arg)
# Output on stdout: the rendered HTML.
# Other outputs:    TITLE / SLUG / DATE / CATEGORY / LANGUAGE to a side file
#                   (so the shell can pick them up without re-parsing).

META_FILE=$(mktemp)
RENDERED_FILE=$(mktemp)
trap 'rm -f "$META_FILE" "$RENDERED_FILE"' EXIT

python3 - "$DRAFT" "$TEMPLATE" "$META_FILE" "$RENDERED_FILE" <<'PY'
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

draft_path, template_path, meta_out, rendered_out = sys.argv[1:5]

src = Path(draft_path).read_text(encoding="utf-8")
m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", src, re.DOTALL)
if not m:
    sys.stderr.write("ERROR: no frontmatter block (expected '---' … '---' at top of draft)\n")
    sys.exit(65)

fm = yaml.safe_load(m.group(1)) or {}
body_md = m.group(2)

required = ["title", "slug", "target_keyword", "description", "language", "date", "category"]
missing = [k for k in required if not fm.get(k)]
if missing:
    sys.stderr.write(f"ERROR: missing frontmatter keys: {', '.join(missing)}\n")
    sys.exit(65)

slug = str(fm["slug"])
if not re.match(r"^[a-z0-9][a-z0-9-]*$", slug):
    sys.stderr.write(f"ERROR: slug '{slug}' must be kebab-case (a-z, 0-9, hyphens)\n")
    sys.exit(65)

lang = str(fm["language"])
if lang not in {"en", "de", "fr", "nl", "no", "it"}:
    sys.stderr.write(f"ERROR: language '{lang}' must be one of en|de|fr|nl|no|it\n")
    sys.exit(65)

date = str(fm["date"])
if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
    sys.stderr.write(f"ERROR: date '{date}' must be YYYY-MM-DD\n")
    sys.exit(65)

if "referral/carlo719460" not in body_md:
    sys.stderr.write(
        "ERROR: body must contain 'referral/carlo719460' — every post needs the referral CTA.\n"
        "See SOUL.md Referral Placement Rules.\n"
    )
    sys.exit(65)

og_image = fm.get("og_image") or "https://teslablog.eu/assets/teslablog-og-default.jpg"
locale_map = {"en": "en_US", "de": "de_DE", "fr": "fr_FR",
              "nl": "nl_NL", "no": "nb_NO", "it": "it_IT"}
og_locale = locale_map[lang]

# Pandoc: markdown → HTML5 fragment
proc = subprocess.run(
    ["pandoc", "--from", "markdown", "--to", "html5", "--no-highlight"],
    input=body_md, text=True, capture_output=True, check=False,
)
if proc.returncode != 0:
    sys.stderr.write(f"ERROR: pandoc failed:\n{proc.stderr}\n")
    sys.exit(70)
body_html = proc.stdout

tpl = Path(template_path).read_text(encoding="utf-8")

def jescape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')

repl = {
    "{{TITLE}}":            fm["title"],
    "{{TITLE_JSON}}":       jescape(fm["title"]),
    "{{SLUG}}":             slug,
    "{{DESCRIPTION}}":      fm["description"],
    "{{DESCRIPTION_JSON}}": jescape(fm["description"]),
    "{{LANGUAGE}}":         lang,
    "{{OG_LOCALE}}":        og_locale,
    "{{DATE}}":             date,
    "{{CATEGORY}}":         str(fm["category"]),
    "{{OG_IMAGE}}":         og_image,
    "{{BODY_HTML}}":        body_html,
}

rendered = tpl
for k, v in repl.items():
    rendered = rendered.replace(k, v)

Path(rendered_out).write_text(rendered, encoding="utf-8")

meta = {
    "title": fm["title"], "slug": slug, "date": date,
    "category": str(fm["category"]), "language": lang,
}
Path(meta_out).write_text(json.dumps(meta), encoding="utf-8")
PY

# Read metadata back into shell vars for the downstream steps
TITLE=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["title"])' "$META_FILE")
SLUG=$(python3 -c  'import json,sys; print(json.load(open(sys.argv[1]))["slug"])'  "$META_FILE")
DATE=$(python3 -c  'import json,sys; print(json.load(open(sys.argv[1]))["date"])'  "$META_FILE")
CATEGORY=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["category"])' "$META_FILE")
LANGUAGE=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["language"])' "$META_FILE")

echo "Parsed frontmatter:"
echo "  title:    $TITLE"
echo "  slug:     $SLUG"
echo "  language: $LANGUAGE"
echo "  date:     $DATE"
echo "  category: $CATEGORY"

POST_DIR="$REPO/blog/$SLUG"
POST_FILE="$POST_DIR/index.html"

# ---------- Dry-run stops here ----------
if [ "$DRY_RUN" = "1" ]; then
  echo ""
  echo "--- DRY RUN ---"
  echo "Would write: $POST_FILE ($(wc -c < "$RENDERED_FILE") bytes)"
  echo "First 30 lines of rendered output:"
  head -30 "$RENDERED_FILE"
  echo "..."
  echo "Would update: $REPO/blog/index.html (insert card for $SLUG)"
  echo "Would update: $REPO/index.html (prepend JSON-LD + Latest Articles entry)"
  echo "Would run:    bash scripts/build-site.sh"
  echo "Would commit: 'Add blog post: $TITLE'"
  echo "Would push:   git push origin main"
  echo "Would ping:   IndexNow for https://teslablog.eu/blog/$SLUG/"
  echo "Dry run complete. No files written, no git activity."
  exit 0
fi

# ---------- 4. write the post ----------
mkdir -p "$POST_DIR"
cp "$RENDERED_FILE" "$POST_FILE"
echo "Wrote $POST_FILE ($(wc -c < "$POST_FILE") bytes)"

# ---------- 5. update blog/index.html ----------
python3 "$INSERT_PY" \
  --mode blog-index \
  --file "$REPO/blog/index.html" \
  --slug "$SLUG" \
  --title "$TITLE" \
  --date "$DATE" \
  --language "$LANGUAGE" \
  --category "$CATEGORY"

# ---------- 6. update homepage index.html ----------
python3 "$INSERT_PY" \
  --mode homepage \
  --file "$REPO/index.html" \
  --slug "$SLUG" \
  --title "$TITLE" \
  --date "$DATE" \
  --language "$LANGUAGE" \
  --category "$CATEGORY"

# ---------- 7. regenerate sitemap ----------
bash "$REPO/scripts/build-site.sh"

# ---------- 8. commit + push ----------
git -C "$REPO" add -A
if git -C "$REPO" diff --cached --quiet; then
  echo "No changes to commit (post may already exist)."
else
  git -C "$REPO" commit -m "Add blog post: $TITLE"
  git -C "$REPO" push origin main
  echo "Pushed. Netlify will deploy in ~1 minute."
fi

# ---------- 9. IndexNow ----------
URL="https://teslablog.eu/blog/$SLUG/"
# IndexNow key file: a file at site root named <hex-key>.txt whose contents are the key.
KEY_FILE=""
for candidate in "$REPO"/*.txt; do
  [ -f "$candidate" ] || continue
  base=$(basename "$candidate" .txt)
  if printf '%s' "$base" | grep -qE '^[a-f0-9]{16,}$'; then
    KEY_FILE="$candidate"
    break
  fi
done
if [ -n "$KEY_FILE" ]; then
  KEY=$(basename "$KEY_FILE" .txt)
  HTTP=$(curl -sS -o /dev/null -w "%{http_code}" -X POST "https://api.indexnow.org/IndexNow" \
    -H "Content-Type: application/json" \
    -d "{\"host\":\"teslablog.eu\",\"key\":\"$KEY\",\"urlList\":[\"$URL\"]}" || echo "000")
  echo "IndexNow: HTTP $HTTP for $URL"
else
  echo "WARN: no IndexNow key file found in $REPO (expected <hex>.txt). Skipping ping." >&2
fi

# ---------- 10. log ----------
mkdir -p "$(dirname "$LOG")"
printf '%s\tdeploy\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$SLUG" "$URL" >> "$LOG"

# ---------- 11. notify Carlo ----------
# Uses ntfy.sh (free push notifications). Carlo subscribes at:
#   https://ntfy.sh/teslablogeu-deploys (browser, phone app, or email)
curl -sS -o /dev/null \
  -H "Title: New post live on TeslaBlog" \
  -H "Tags: rocket" \
  -H "Click: $URL" \
  -d "Deployed: $TITLE — $URL" \
  "https://ntfy.sh/teslablogeu-deploys" 2>/dev/null || true

echo ""
echo "Done: $URL"
