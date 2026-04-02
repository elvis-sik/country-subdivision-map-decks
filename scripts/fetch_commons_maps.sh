#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAPS_DIR="$ROOT_DIR/maps"
BASE_DIR="$MAPS_DIR/base"
LOCATORS_DIR="$MAPS_DIR/locators"
USER_AGENT="country-subdivision-map-decks/1.0 (personal study project)"

urlencode() {
  jq -rn --arg value "$1" '$value | @uri'
}

download_commons_file() {
  local title="$1"
  local dest_dir="$2"
  local filename="${title#File:}"
  local encoded_filename

  mkdir -p "$dest_dir"
  encoded_filename="$(urlencode "$filename")"

  curl -fsSL \
    --retry 8 \
    --retry-delay 2 \
    --retry-all-errors \
    -A "$USER_AGENT" \
    -o "$dest_dir/$filename" \
    "https://commons.wikimedia.org/wiki/Special:Redirect/file/$encoded_filename"

  sleep 1
}

fetch_category_titles() {
  local category_title="$1"
  local encoded_category

  encoded_category="$(urlencode "$category_title")"

  curl -fsSL \
    --retry 5 \
    --retry-delay 2 \
    --retry-all-errors \
    -A "$USER_AGENT" \
    "https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtitle=$encoded_category&cmlimit=200&format=json" \
    | jq -r '.query.categorymembers[] | select(.ns == 6) | .title'
}

echo "Fetching base SVGs..."
download_commons_file "File:Mexico States blank map.svg" "$BASE_DIR/mexico"
download_commons_file "File:SA provinces.svg" "$BASE_DIR/south-africa"
download_commons_file "File:Turkey-regions.svg" "$BASE_DIR/turkey"
download_commons_file "File:Iran provinces.svg" "$BASE_DIR/iran"

echo "Fetching Turkey locator SVGs..."
fetch_category_titles "Category:SVG locator maps of regions of Turkey (location map scheme)" \
  | while IFS= read -r title; do
      download_commons_file "$title" "$LOCATORS_DIR/turkey"
    done

echo "Fetching South Africa locator SVGs..."
fetch_category_titles "Category:SVG locator maps of provinces in South Africa (river location map scheme)" \
  | while IFS= read -r title; do
      download_commons_file "$title" "$LOCATORS_DIR/south-africa"
    done

echo "Fetching Mexico locator SVGs..."
fetch_category_titles "Category:SVG locator maps of states in Mexico (location map scheme)" \
  | rg -v '\(zoom\)|special marker|^File:Mexico map\.svg$' \
  | while IFS= read -r title; do
      download_commons_file "$title" "$LOCATORS_DIR/mexico"
    done

echo "Fetching Iran locator SVGs..."
fetch_category_titles "Category:SVG locator maps of provinces in Iran (location map scheme)" \
  | rg ' in Iran\.svg$' \
  | rg -v '^File:(Central iran|East of Iran|North of Iran|South of Iran|West of iran)\.svg$| provinces in Iran\.svg$|^File:Kerman province and Sistan and Baluchestan province in Iran\.svg$' \
  | while IFS= read -r title; do
      download_commons_file "$title" "$LOCATORS_DIR/iran"
    done

echo
echo "Fetch complete."
echo "Base counts:"
find "$BASE_DIR" -type f -name '*.svg' | sed "s#^$ROOT_DIR/##" | sort
echo
echo "Locator counts:"
for country in iran mexico south-africa turkey; do
  count="$(find "$LOCATORS_DIR/$country" -type f -name '*.svg' | wc -l | tr -d ' ')"
  echo "  $country: $count"
done
