#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAPS_DIR="$ROOT_DIR/maps"
BASE_DIR="$MAPS_DIR/base"
LOCATORS_DIR="$MAPS_DIR/locators"
MANIFEST_PATH="$MAPS_DIR/manifest.tsv"

slugify() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/&/ and /g' \
    | sed -E "s/[()'.,]//g" \
    | sed -E 's/ +/-/g' \
    | sed -E 's/-+/-/g' \
    | sed -E 's/^-|-$//g'
}

write_manifest_header() {
  printf 'country\tkind\tslug\tlabel\tsource_title\tlocal_path\n' > "$MANIFEST_PATH"
}

append_manifest_row() {
  local country="$1"
  local kind="$2"
  local slug="$3"
  local label="$4"
  local source_title="$5"
  local local_path="$6"

  printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$country" "$kind" "$slug" "$label" "$source_title" "$local_path" >> "$MANIFEST_PATH"
}

rename_base_file() {
  local country="$1"
  local source_name="$2"
  local target_name="$3"
  local label="$4"
  local source_path="$BASE_DIR/$country/$source_name"
  local target_path="$BASE_DIR/$country/$target_name"
  local slug="${target_name%.svg}"
  local local_path="maps/base/$country/$target_name"
  local source_title="$source_name"

  if [[ -f "$source_path" && "$source_path" != "$target_path" ]]; then
    mv "$source_path" "$target_path"
  elif [[ -f "$target_path" ]]; then
    source_title="$target_name"
  else
    echo "Missing base file: $source_path or $target_path" >&2
    exit 1
  fi

  append_manifest_row "$country" "base" "$slug" "$label" "$source_title" "$local_path"
}

normalize_locator_dir() {
  local country="$1"
  local dir="$LOCATORS_DIR/$country"
  local source_name=""
  local stem=""
  local label=""
  local slug=""
  local target_name=""
  local target_path=""

  while IFS= read -r -d '' source_path; do
    source_name="$(basename "$source_path")"
    stem="${source_name%.svg}"

    case "$country" in
      turkey)
        label="${stem% in Turkey}"
        ;;
      south-africa)
        label="${stem% in South Africa}"
        ;;
      iran)
        label="${stem% in Iran}"
        ;;
      mexico)
        case "$stem" in
          "Mexico (city) in Mexico")
            label="Mexico City"
            ;;
          "Mexico (state) in Mexico")
            label="State of Mexico"
            ;;
          *)
            label="$(printf '%s' "$stem" | sed -E 's/ in Mexico( \(location map scheme\))?$//')"
            ;;
        esac
        ;;
      *)
        echo "Unsupported locator country: $country" >&2
        exit 1
        ;;
    esac

    slug="$(slugify "$label")"
    target_name="$slug.svg"
    target_path="$dir/$target_name"

    if [[ "$source_path" != "$target_path" ]]; then
      mv "$source_path" "$target_path"
    fi

    append_manifest_row \
      "$country" \
      "locator" \
      "$slug" \
      "$label" \
      "$source_name" \
      "maps/locators/$country/$target_name"
  done < <(find "$dir" -maxdepth 1 -type f -name '*.svg' -print0 | sort -z)
}

write_manifest_header

rename_base_file "iran" "Iran provinces.svg" "iran-provinces.svg" "Iran provinces"
rename_base_file "mexico" "Mexico States blank map.svg" "mexico-states.svg" "Mexico states"
rename_base_file "south-africa" "SA provinces.svg" "south-africa-provinces.svg" "South Africa provinces"
rename_base_file "turkey" "Turkey-regions.svg" "turkey-regions.svg" "Turkey regions"

normalize_locator_dir "iran"
normalize_locator_dir "mexico"
normalize_locator_dir "south-africa"
normalize_locator_dir "turkey"
