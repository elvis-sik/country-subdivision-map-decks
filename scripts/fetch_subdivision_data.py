#!/usr/bin/env python3

import csv
import json
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
MAP_MANIFEST_PATH = ROOT_DIR / "maps" / "manifest.tsv"
OUTPUT_DIR = ROOT_DIR / "data" / "subdivisions"

USER_AGENT = "country-subdivision-map-decks/1.0 (personal study project)"
WIKIDATA_API_ENDPOINT = "https://www.wikidata.org/w/api.php"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
ENTITY_BATCH_SIZE = 25
COUNTRY_ENTITY_QID = "Q6256"

COUNTRY_CONFIGS = {
    "iran": {
        "country_name": "Iran",
        "country_qid": "Q794",
        "subdivision_type": "province",
        "notes": "",
    },
    "mexico": {
        "country_name": "Mexico",
        "country_qid": "Q96",
        "subdivision_type": "federative entity",
        "notes": "",
    },
    "south-africa": {
        "country_name": "South Africa",
        "country_qid": "Q258",
        "subdivision_type": "province",
        "notes": "",
    },
    "turkey": {
        "country_name": "Turkey",
        "country_qid": "Q43",
        "subdivision_type": "geographical region",
        "notes": "Turkey's seven geographical regions do not have official capitals; capital fields are left blank.",
        "item_qids": [
            "Q155564",
            "Q155533",
            "Q155526",
            "Q155542",
            "Q155583",
            "Q155552",
            "Q155638",
        ],
    },
}

SUBDIVISION_SLUG_OVERRIDES = {
    ("iran", "East Azarbaijan"): "east-azerbaijan",
    ("iran", "West Azarbaijan"): "west-azerbaijan",
    ("iran", "Chaharmahal and Bakhtiari"): "chahar-mahaal-and-bakhtiari",
    ("iran", "Sistan and Baluchestan"): "sistan-and-baluchistan",
}

MANUAL_ROW_OVERRIDES = {
    "turkey": {
        "aegean-region": {
            "capital_name": "",
            "capital_wikidata_id": "",
            "capital_wikipedia_url": "",
            "borders_countries": "",
            "borders_waters": "Aegean Sea",
        },
        "black-sea-region": {
            "capital_name": "",
            "capital_wikidata_id": "",
            "capital_wikipedia_url": "",
            "borders_countries": "Georgia",
            "borders_waters": "Black Sea",
        },
        "central-anatolia-region": {
            "capital_name": "",
            "capital_wikidata_id": "",
            "capital_wikipedia_url": "",
            "borders_countries": "",
            "borders_waters": "",
        },
        "eastern-anatolia-region": {
            "capital_name": "",
            "capital_wikidata_id": "",
            "capital_wikipedia_url": "",
            "borders_countries": "Armenia | Azerbaijan | Georgia | Iran | Iraq",
            "borders_waters": "",
        },
        "marmara-region": {
            "capital_name": "",
            "capital_wikidata_id": "",
            "capital_wikipedia_url": "",
            "borders_countries": "Bulgaria | Greece",
            "borders_waters": "Aegean Sea | Black Sea | Sea of Marmara",
        },
        "mediterranean-region": {
            "capital_name": "",
            "capital_wikidata_id": "",
            "capital_wikipedia_url": "",
            "borders_countries": "Syria",
            "borders_waters": "Mediterranean Sea",
        },
        "southeastern-anatolia-region": {
            "capital_name": "",
            "capital_wikidata_id": "",
            "capital_wikipedia_url": "",
            "borders_countries": "Iraq | Syria",
            "borders_waters": "",
        },
    }
}

FIELDNAMES = [
    "country_slug",
    "country_name",
    "subdivision_type",
    "subdivision_slug",
    "subdivision_name",
    "subdivision_wikidata_id",
    "subdivision_wikipedia_url",
    "capital_name",
    "capital_wikidata_id",
    "capital_wikipedia_url",
    "borders_subdivisions",
    "borders_countries",
    "borders_waters",
    "connections",
    "locator_svg_path",
    "base_svg_path",
    "notes",
]


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def slugify(text: str) -> str:
    ascii_text = strip_accents(text)
    ascii_text = ascii_text.replace("&", " and ")
    cleaned = []
    for ch in ascii_text.lower():
        if ch.isalnum() or ch in {" ", "-"}:
            cleaned.append(ch)
        elif ch in {"'", ".", ",", "(", ")"}:
            continue
        else:
            cleaned.append(" ")
    slug = "".join(cleaned)
    slug = "-".join(part for part in slug.replace("-", " ").split())
    return slug


def normalize_subdivision_name(country_slug: str, label: str) -> str:
    normalized = label.strip()
    if country_slug == "iran" and normalized.endswith(" Province"):
        return normalized[: -len(" Province")]
    return normalized


def chunked(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def wikidata_request(params: dict) -> dict:
    encoded_params = urllib.parse.urlencode(params)
    url = f"{WIKIDATA_API_ENDPOINT}?{encoded_params}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="GET",
    )

    for attempt in range(1, 6):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code not in RETRYABLE_STATUS_CODES or attempt == 5:
                raise
        except urllib.error.URLError:
            if attempt == 5:
                raise

        time.sleep(2 * attempt)

    raise RuntimeError("Wikidata API retries exhausted")


def wbgetentities(ids: list[str]) -> dict[str, dict]:
    entities: dict[str, dict] = {}
    for batch in chunked(ids, ENTITY_BATCH_SIZE):
        response = wikidata_request(
            {
                "action": "wbgetentities",
                "format": "json",
                "ids": "|".join(batch),
                "languages": "en",
                "props": "labels|sitelinks|claims",
            }
        )
        entities.update(response["entities"])
    return entities


def load_map_manifest() -> dict:
    manifest = {"base": {}, "locators": {}}
    with MAP_MANIFEST_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            if row["kind"] == "base":
                manifest["base"][row["country"]] = row["local_path"]
            elif row["kind"] == "locator":
                manifest["locators"][(row["country"], row["slug"])] = row["local_path"]
    return manifest


def extract_label(entity: dict) -> str:
    return entity.get("labels", {}).get("en", {}).get("value", "")


def extract_enwiki_url(entity: dict) -> str:
    sitelink = entity.get("sitelinks", {}).get("enwiki")
    if not sitelink:
        return ""
    title = sitelink["title"].replace(" ", "_")
    return f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title)}"


def claim_entity_ids(entity: dict, prop: str) -> list[str]:
    ids = []
    for claim in entity.get("claims", {}).get(prop, []):
        mainsnak = claim.get("mainsnak", {})
        datavalue = mainsnak.get("datavalue", {})
        value = datavalue.get("value", {})
        if isinstance(value, dict) and value.get("id"):
            ids.append(value["id"])
    return ids


def first_claim_entity_id(entity: dict, prop: str) -> str:
    ids = claim_entity_ids(entity, prop)
    return ids[0] if ids else ""


def build_connections(row: dict) -> str:
    connection_parts = []
    subdivisions = [value for value in row["borders_subdivisions"].split(" | ") if value]
    countries = [value for value in row["borders_countries"].split(" | ") if value]
    waters = [value for value in row["borders_waters"].split(" | ") if value]

    if subdivisions:
        connection_parts.append(
            f"Borders peer subdivisions: {', '.join(subdivisions)}"
        )
    if countries:
        connection_parts.append(f"Countries: {', '.join(countries)}")
    if waters:
        connection_parts.append(f"Waters: {', '.join(waters)}")
    return "; ".join(connection_parts)


def apply_manual_row_overrides(country_slug: str, row: dict) -> None:
    overrides = MANUAL_ROW_OVERRIDES.get(country_slug, {}).get(row["subdivision_slug"], {})
    for key, value in overrides.items():
        row[key] = value


def collect_subdivision_qids(config: dict) -> list[str]:
    if "item_qids" in config:
        return list(config["item_qids"])

    country_entity = wbgetentities([config["country_qid"]])[config["country_qid"]]
    return claim_entity_ids(country_entity, "P150")


def init_row(country_slug: str, config: dict, manifest: dict, entity: dict) -> dict:
    label = normalize_subdivision_name(country_slug, extract_label(entity))
    subdivision_slug = SUBDIVISION_SLUG_OVERRIDES.get((country_slug, label), slugify(label))
    locator_path = manifest["locators"].get((country_slug, subdivision_slug))
    if not locator_path:
        raise KeyError(
            f"Missing locator SVG path for {country_slug}:{label} ({subdivision_slug})"
        )

    capital_qid = first_claim_entity_id(entity, "P36")

    return {
        "country_slug": country_slug,
        "country_name": config["country_name"],
        "subdivision_type": config["subdivision_type"],
        "subdivision_slug": subdivision_slug,
        "subdivision_name": label,
        "subdivision_wikidata_id": entity["id"],
        "subdivision_wikipedia_url": extract_enwiki_url(entity),
        "capital_name": "",
        "capital_wikidata_id": capital_qid,
        "capital_wikipedia_url": "",
        "borders_subdivisions": "",
        "borders_countries": "",
        "borders_waters": "",
        "connections": "",
        "locator_svg_path": locator_path,
        "base_svg_path": manifest["base"][country_slug],
        "notes": config["notes"],
        "_neighbor_qids": set(claim_entity_ids(entity, "P47")),
        "_water_qids": set(claim_entity_ids(entity, "P206")),
    }


def collect_country_rows(country_slug: str, config: dict, manifest: dict) -> list[dict]:
    subdivision_qids = collect_subdivision_qids(config)
    print(f"  Found {len(subdivision_qids)} subdivisions", file=sys.stderr)

    subdivision_entities = wbgetentities(subdivision_qids)
    rows = [init_row(country_slug, config, manifest, subdivision_entities[qid]) for qid in subdivision_qids]
    rows_by_qid = {row["subdivision_wikidata_id"]: row for row in rows}
    subdivision_qid_set = set(rows_by_qid.keys())

    related_qids = set()
    for row in rows:
        if row["capital_wikidata_id"]:
            related_qids.add(row["capital_wikidata_id"])
        related_qids.update(row["_neighbor_qids"])
        related_qids.update(row["_water_qids"])

    print(f"  Fetching {len(related_qids)} related entities", file=sys.stderr)
    related_entities = wbgetentities(sorted(related_qids)) if related_qids else {}

    foreign_country_qids = set()
    for row in rows:
        for neighbor_qid in row["_neighbor_qids"]:
            if neighbor_qid in subdivision_qid_set:
                continue
            neighbor_entity = related_entities.get(neighbor_qid, {})
            if COUNTRY_ENTITY_QID in claim_entity_ids(neighbor_entity, "P31"):
                continue
            foreign_country_qids.update(
                qid
                for qid in claim_entity_ids(neighbor_entity, "P17")
                if qid != config["country_qid"]
            )

    country_entities = wbgetentities(sorted(foreign_country_qids)) if foreign_country_qids else {}

    for row in rows:
        capital_qid = row["capital_wikidata_id"]
        if capital_qid:
            capital_entity = related_entities.get(capital_qid, {})
            row["capital_name"] = extract_label(capital_entity)
            row["capital_wikipedia_url"] = extract_enwiki_url(capital_entity)

        same_country_neighbors = set()
        countries = set()
        waters = set()

        for neighbor_qid in row["_neighbor_qids"]:
            if neighbor_qid in subdivision_qid_set:
                same_country_neighbors.add(rows_by_qid[neighbor_qid]["subdivision_name"])
                continue

            neighbor_entity = related_entities.get(neighbor_qid, {})
            neighbor_label = extract_label(neighbor_entity)
            neighbor_country_qids = claim_entity_ids(neighbor_entity, "P17")

            if COUNTRY_ENTITY_QID in claim_entity_ids(neighbor_entity, "P31"):
                if neighbor_label:
                    countries.add(neighbor_label)
                continue

            for neighbor_country_qid in neighbor_country_qids:
                if neighbor_country_qid != config["country_qid"]:
                    country_label = extract_label(country_entities.get(neighbor_country_qid, {}))
                    if country_label:
                        countries.add(country_label)

        for water_qid in row["_water_qids"]:
            water_label = extract_label(related_entities.get(water_qid, {}))
            if water_label:
                waters.add(water_label)

        sorted_neighbors = sorted(same_country_neighbors)
        sorted_countries = sorted(countries)
        sorted_waters = sorted(waters)

        row["borders_subdivisions"] = " | ".join(sorted_neighbors)
        row["borders_countries"] = " | ".join(sorted_countries)
        row["borders_waters"] = " | ".join(sorted_waters)
        apply_manual_row_overrides(country_slug, row)
        row["connections"] = build_connections(row)

        del row["_neighbor_qids"]
        del row["_water_qids"]

    rows.sort(key=lambda row: row["subdivision_slug"])
    return rows


def write_country_csv(country_slug: str, rows: list[dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{country_slug}.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def write_combined_csv(all_rows: list[dict]) -> None:
    output_path = OUTPUT_DIR / "all.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)


def main() -> int:
    manifest = load_map_manifest()
    all_rows = []

    for country_slug, config in COUNTRY_CONFIGS.items():
        print(f"Fetching {country_slug}...", file=sys.stderr)
        rows = collect_country_rows(country_slug, config, manifest)
        write_country_csv(country_slug, rows)
        all_rows.extend(rows)

    all_rows.sort(key=lambda row: (row["country_slug"], row["subdivision_slug"]))
    write_combined_csv(all_rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
