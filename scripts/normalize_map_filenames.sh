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

titleize_slug() {
  printf '%s' "$1" | awk -F- '{
    for (i = 1; i <= NF; i++) {
      $i = toupper(substr($i, 1, 1)) substr($i, 2)
    }
    gsub(/-/, " ")
    print
  }'
}

canonical_label_from_slug() {
  local country="$1"
  local slug="$2"

  case "$country:$slug" in
    mexico:mexico-city) printf 'Mexico City' ;;
    mexico:state-of-mexico) printf 'State of Mexico' ;;
    south-africa:kwazulu-natal) printf 'KwaZulu-Natal' ;;
    south-africa:north-west) printf 'North West' ;;
    turkey:black-sea-region) printf 'Black Sea Region' ;;
    turkey:central-anatolia-region) printf 'Central Anatolia Region' ;;
    turkey:eastern-anatolia-region) printf 'Eastern Anatolia Region' ;;
    turkey:mediterranean-region) printf 'Mediterranean Region' ;;
    turkey:southeastern-anatolia-region) printf 'Southeastern Anatolia Region' ;;
    turkey:marmara-region) printf 'Marmara Region' ;;
    turkey:aegean-region) printf 'Aegean Region' ;;
    iran:chahar-mahaal-and-bakhtiari) printf 'Chahar Mahaal and Bakhtiari' ;;
    iran:kohgiluyeh-and-boyer-ahmad) printf 'Kohgiluyeh and Boyer-Ahmad' ;;
    iran:sistan-and-baluchistan) printf 'Sistan and Baluchistan' ;;
    iran:east-azerbaijan) printf 'East Azerbaijan' ;;
    iran:west-azerbaijan) printf 'West Azerbaijan' ;;
    iran:north-khorasan) printf 'North Khorasan' ;;
    iran:razavi-khorasan) printf 'Razavi Khorasan' ;;
    iran:south-khorasan) printf 'South Khorasan' ;;
    mexico:baja-california) printf 'Baja California' ;;
    mexico:baja-california-sur) printf 'Baja California Sur' ;;
    mexico:nuevo-leon) printf 'Nuevo Leon' ;;
    mexico:quintana-roo) printf 'Quintana Roo' ;;
    mexico:san-luis-potosi) printf 'San Luis Potosi' ;;
    *)
      titleize_slug "$slug"
      ;;
  esac
}

canonical_source_title() {
  local country="$1"
  local slug="$2"
  local label="$3"

  case "$country" in
    turkey)
      printf 'File:%s in Turkey.svg' "$label"
      ;;
    south-africa)
      printf 'File:%s in South Africa.svg' "$label"
      ;;
    iran)
      printf 'File:%s in Iran.svg' "$label"
      ;;
    mexico)
      case "$slug" in
        aguascalientes|baja-california|baja-california-sur|campeche|oaxaca)
          printf 'File:%s in Mexico.svg' "$label"
          ;;
        mexico-city)
          printf 'File:Mexico (city) in Mexico.svg'
          ;;
        state-of-mexico)
          printf 'File:Mexico (state) in Mexico.svg'
          ;;
        *)
          printf 'File:%s in Mexico (location map scheme).svg' "$label"
          ;;
      esac
      ;;
    *)
      echo "Unsupported source-title country: $country" >&2
      exit 1
      ;;
  esac
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

  if [[ -f "$source_path" && "$source_path" != "$target_path" ]]; then
    mv "$source_path" "$target_path"
  elif [[ ! -f "$target_path" ]]; then
    echo "Missing base file: $source_path or $target_path" >&2
    exit 1
  fi

  append_manifest_row "$country" "base" "$slug" "$label" "File:$source_name" "$local_path"
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
  local source_title=""

  while IFS= read -r -d '' source_path; do
    source_name="$(basename "$source_path")"
    stem="${source_name%.svg}"

    case "$country" in
      turkey)
        if [[ "$stem" == *" in Turkey" ]]; then
          label="${stem% in Turkey}"
          slug="$(slugify "$label")"
        else
          slug="$stem"
          label="$(canonical_label_from_slug "$country" "$slug")"
        fi
        ;;
      south-africa)
        if [[ "$stem" == *" in South Africa" ]]; then
          label="${stem% in South Africa}"
          slug="$(slugify "$label")"
        else
          slug="$stem"
          label="$(canonical_label_from_slug "$country" "$slug")"
        fi
        ;;
      iran)
        if [[ "$stem" == *" in Iran" ]]; then
          label="${stem% in Iran}"
          slug="$(slugify "$label")"
        else
          slug="$stem"
          label="$(canonical_label_from_slug "$country" "$slug")"
        fi
        ;;
      mexico)
        case "$stem" in
          "Mexico (city) in Mexico")
            label="Mexico City"
            slug="mexico-city"
            ;;
          "Mexico (state) in Mexico")
            label="State of Mexico"
            slug="state-of-mexico"
            ;;
          *" in Mexico"*)
            label="$(printf '%s' "$stem" | sed -E 's/ in Mexico( \(location map scheme\))?$//')"
            slug="$(slugify "$label")"
            ;;
          *)
            slug="$stem"
            label="$(canonical_label_from_slug "$country" "$slug")"
            ;;
        esac
        ;;
      *)
        echo "Unsupported locator country: $country" >&2
        exit 1
        ;;
    esac

    target_name="$slug.svg"
    target_path="$dir/$target_name"

    if [[ "$source_path" != "$target_path" ]]; then
      mv "$source_path" "$target_path"
    fi

    source_title="$(canonical_source_title "$country" "$slug" "$label")"

    append_manifest_row \
      "$country" \
      "locator" \
      "$slug" \
      "$label" \
      "$source_title" \
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
