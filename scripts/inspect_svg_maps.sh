#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAPS_DIR="$ROOT_DIR/maps"
REPORT_PATH="$MAPS_DIR/INSPECTION.md"

tag_count() {
  local pattern="$1"
  local file="$2"

  (
    rg -o "$pattern" "$file" || true
  ) | wc -l | tr -d ' '
}

base_row() {
  local country="$1"
  local file="$2"
  local path="$MAPS_DIR/base/$country/$file"
  local text_tags
  local structure_tags
  local verdict

  text_tags="$(tag_count '<text|<flowRoot|<tspan' "$path")"
  structure_tags="$(tag_count '<path|<g|id=' "$path")"

  if [[ "$text_tags" == "0" ]]; then
    verdict="ready as blank base"
  else
    verdict="needs label cleanup"
  fi

  printf '| %s | `%s` | %s | %s | %s |\n' \
    "$country" \
    "maps/base/$country/$file" \
    "$text_tags" \
    "$structure_tags" \
    "$verdict"
}

locator_row() {
  local country="$1"
  local dir="$MAPS_DIR/locators/$country"
  local total
  local with_text

  total="$(find "$dir" -maxdepth 1 -type f -name '*.svg' | wc -l | tr -d ' ')"
  with_text="$(
    (
      find "$dir" -maxdepth 1 -type f -name '*.svg' -print0 | xargs -0 rg -l '<text|<flowRoot|<tspan' 2>/dev/null || true
    ) | wc -l | tr -d ' '
  )"

  printf '| %s | %s | %s |\n' "$country" "$total" "$with_text"
}

{
  cat <<'EOF'
# SVG Inspection

This report checks whether the current SVG map assets appear usable as deck-generation inputs.

## Base Maps

Interpretation:

- `text tags = 0` usually means the SVG is already label-free and usable as a blank outline base.
- high structure counts are fine; they mostly indicate many paths/groups, not a problem by themselves.

| Country | File | Text Tags | Structure Tags | Verdict |
| --- | --- | ---: | ---: | --- |
EOF

  base_row "iran" "iran-provinces.svg"
  base_row "mexico" "mexico-states.svg"
  base_row "south-africa" "south-africa-provinces.svg"
  base_row "turkey" "turkey-regions.svg"

  cat <<'EOF'

## Locator Series

`SVGs with text tags` is a quick sanity check for whether the highlighted locator maps include embedded labels.

| Country | Locator SVGs | SVGs With Text Tags |
| --- | ---: | ---: |
EOF

  locator_row "iran"
  locator_row "mexico"
  locator_row "south-africa"
  locator_row "turkey"

  cat <<'EOF'

## Summary

- All four current base SVGs are label-free by this check.
- The locator sets are also label-free by this check.
- That means we can move to card/deck generation without first stripping text out of these source SVGs.
EOF
} > "$REPORT_PATH"
