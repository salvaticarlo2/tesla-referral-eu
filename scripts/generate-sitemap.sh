#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DOMAIN="https://teslablog.eu"
TODAY_UTC="$(date -u +%F)"
TMP_FILE="$(mktemp)"

cleanup() { rm -f "$TMP_FILE"; }
trap cleanup EXIT

lastmod_for() {
  local path="$1"
  local lastmod
  if lastmod="$(git log -1 --date=format:%Y-%m-%d --format=%ad -- "$path" 2>/dev/null)" && [ -n "$lastmod" ]; then
    printf "%s" "$lastmod"
  else
    printf "%s" "$TODAY_UTC"
  fi
}

emit_url() {
  local loc="$1"
  local lastmod="$2"
  cat >> "$TMP_FILE" <<XML
  <url>
    <loc>${DOMAIN}${loc}</loc>
    <lastmod>${lastmod}</lastmod>
  </url>
XML
}

# Header
cat > "$TMP_FILE" <<XML
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
XML

# Core pages
emit_url "/" "$(lastmod_for "index.html")"
emit_url "/blog/" "$(lastmod_for "blog/index.html")"
emit_url "/privacy/" "$(lastmod_for "privacy/index.html")"
emit_url "/referral/" "$(lastmod_for "referral/index.html")"

# Language pages
for lang in de es fr it nl no; do
  page_path="${lang}/index.html"
  if [ -f "$page_path" ]; then
    emit_url "/${lang}/" "$(lastmod_for "$page_path")"
  fi
done

# Blog posts
while IFS= read -r slug; do
  page_path="blog/${slug}/index.html"
  [ -f "$page_path" ] || continue
  emit_url "/blog/${slug}/" "$(lastmod_for "$page_path")"
done < <(find blog -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort)

# News items
if [ -d "news" ]; then
  while IFS= read -r slug; do
    page_path="news/${slug}/index.html"
    [ -f "$page_path" ] || continue
    emit_url "/news/${slug}/" "$(lastmod_for "$page_path")"
  done < <(find news -mindepth 1 -maxdepth 1 -type d -not -name "page" -exec basename {} \; | sort)

  # News index and pagination
  emit_url "/news/" "$(lastmod_for "news/index.html")"
  if [ -d "news/page" ]; then
    for page_dir in news/page/*/; do
      page_num="$(basename "$page_dir")"
      [ -f "${page_dir}index.html" ] || continue
      emit_url "/news/page/${page_num}/" "$(lastmod_for "${page_dir}index.html")"
    done
  fi
fi

echo "</urlset>" >> "$TMP_FILE"

# Validate if xmllint available
if command -v xmllint >/dev/null 2>&1; then
  xmllint --noout "$TMP_FILE"
fi

# Deploy: one canonical sitemap.xml, keep sitemap-min.xml as copy for backward compat
cp "$TMP_FILE" sitemap.xml
cp "$TMP_FILE" sitemap-min.xml
chmod 644 sitemap.xml sitemap-min.xml

# Clean up legacy files
rm -f sitemap-v2.xml sitemap_index.xml

url_count="$(grep -c "<loc>" sitemap.xml)"
echo "Generated sitemap.xml (${url_count} URLs)"
