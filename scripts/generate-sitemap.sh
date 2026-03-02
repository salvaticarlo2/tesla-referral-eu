#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DOMAIN="https://teslablog.eu"
TODAY_UTC="$(date -u +%F)"
SITEMAP_FILE="sitemap.xml"
TMP_FILE="$(mktemp)"

cleanup() {
  rm -f "$TMP_FILE"
}
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
  local changefreq="$3"
  local priority="$4"

  cat >> "$TMP_FILE" <<XML
  <url>
    <loc>${DOMAIN}${loc}</loc>
    <lastmod>${lastmod}</lastmod>
    <changefreq>${changefreq}</changefreq>
    <priority>${priority}</priority>
  </url>
XML
}

cat > "$TMP_FILE" <<XML
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
XML

cat >> "$TMP_FILE" <<XML
  <url>
    <loc>${DOMAIN}/</loc>
    <lastmod>$(lastmod_for "index.html")</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
    <xhtml:link rel="alternate" hreflang="en" href="${DOMAIN}/"/>
    <xhtml:link rel="alternate" hreflang="de" href="${DOMAIN}/de/"/>
    <xhtml:link rel="alternate" hreflang="fr" href="${DOMAIN}/fr/"/>
    <xhtml:link rel="alternate" hreflang="nl" href="${DOMAIN}/nl/"/>
    <xhtml:link rel="alternate" hreflang="no" href="${DOMAIN}/no/"/>
    <xhtml:link rel="alternate" hreflang="it" href="${DOMAIN}/it/"/>
  </url>
XML

emit_url "/blog/" "$(lastmod_for "blog/index.html")" "weekly" "0.9"
emit_url "/referral/" "$(lastmod_for "referral/index.html")" "monthly" "0.9"

for lang in de fr nl no it; do
  page_path="${lang}/index.html"
  if [ -f "$page_path" ]; then
    cat >> "$TMP_FILE" <<XML
  <url>
    <loc>${DOMAIN}/${lang}/</loc>
    <lastmod>$(lastmod_for "$page_path")</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
    <xhtml:link rel="alternate" hreflang="en" href="${DOMAIN}/"/>
    <xhtml:link rel="alternate" hreflang="de" href="${DOMAIN}/de/"/>
    <xhtml:link rel="alternate" hreflang="fr" href="${DOMAIN}/fr/"/>
    <xhtml:link rel="alternate" hreflang="nl" href="${DOMAIN}/nl/"/>
    <xhtml:link rel="alternate" hreflang="no" href="${DOMAIN}/no/"/>
    <xhtml:link rel="alternate" hreflang="it" href="${DOMAIN}/it/"/>
  </url>
XML
  fi
done

while IFS= read -r slug; do
  page_path="blog/${slug}/index.html"
  [ -f "$page_path" ] || continue
  emit_url "/blog/${slug}/" "$(lastmod_for "$page_path")" "monthly" "0.8"
done < <(find blog -mindepth 1 -maxdepth 1 -type d -printf "%f\n" | sort)

echo "</urlset>" >> "$TMP_FILE"

if command -v xmllint >/dev/null 2>&1; then
  xmllint --noout "$TMP_FILE"
fi

mv "$TMP_FILE" "$SITEMAP_FILE"
chmod 644 "$SITEMAP_FILE"

url_count="$(grep -c "<loc>" "$SITEMAP_FILE")"
echo "Generated ${SITEMAP_FILE} with ${url_count} URLs"
