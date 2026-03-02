#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DOMAIN="https://teslablog.eu"
TODAY_UTC="$(date -u +%F)"
SITEMAP_FILE="sitemap.xml"
SITEMAP_ALT_FILE="sitemap-v2.xml"
SITEMAP_MIN_FILE="sitemap-min.xml"
TMP_FILE="$(mktemp)"
TMP_MIN_FILE="$(mktemp)"

cleanup() {
  rm -f "$TMP_FILE" "$TMP_MIN_FILE"
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
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
XML

emit_url "/" "$(lastmod_for "index.html")" "weekly" "1.0"
emit_url "/blog/" "$(lastmod_for "blog/index.html")" "weekly" "0.9"
emit_url "/referral/" "$(lastmod_for "referral/index.html")" "monthly" "0.9"

for lang in de fr nl no it; do
  page_path="${lang}/index.html"
  if [ -f "$page_path" ]; then
    emit_url "/${lang}/" "$(lastmod_for "$page_path")" "monthly" "0.7"
  fi
done

while IFS= read -r slug; do
  page_path="blog/${slug}/index.html"
  [ -f "$page_path" ] || continue
  emit_url "/blog/${slug}/" "$(lastmod_for "$page_path")" "monthly" "0.8"
done < <(find blog -mindepth 1 -maxdepth 1 -type d -printf "%f\n" | sort)

echo "</urlset>" >> "$TMP_FILE"

awk '
BEGIN {
  print "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
  print "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"
}
/<url>/ { in_url=1; loc=""; lastmod="" }
in_url && /<loc>/ { loc=$0 }
in_url && /<lastmod>/ { lastmod=$0 }
/<\/url>/ {
  if (in_url && loc != "") {
    print "  <url>"
    print loc
    if (lastmod != "") print lastmod
    print "  </url>"
  }
  in_url=0
}
END {
  print "</urlset>"
}
' "$TMP_FILE" > "$TMP_MIN_FILE"

if command -v xmllint >/dev/null 2>&1; then
  xmllint --noout "$TMP_FILE"
  xmllint --noout "$TMP_MIN_FILE"
fi

mv "$TMP_FILE" "$SITEMAP_FILE"
cp "$SITEMAP_FILE" "$SITEMAP_ALT_FILE"
mv "$TMP_MIN_FILE" "$SITEMAP_MIN_FILE"
chmod 644 "$SITEMAP_FILE" "$SITEMAP_ALT_FILE" "$SITEMAP_MIN_FILE"

url_count="$(grep -c "<loc>" "$SITEMAP_FILE")"
echo "Generated ${SITEMAP_FILE}, ${SITEMAP_ALT_FILE}, and ${SITEMAP_MIN_FILE} with ${url_count} URLs"
