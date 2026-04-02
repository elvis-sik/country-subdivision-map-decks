#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
from pathlib import Path

try:
    import genanki
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit(
        "genanki is required to build the deck. Install it with `uv sync --extra deck` "
        "or otherwise make `genanki` available in this environment."
    ) from exc


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_CSV = REPO_ROOT / "data" / "subdivisions" / "south-africa.csv"
CSS_PATH = REPO_ROOT / "templates" / "south_africa.css"
OUTPUT_APKG = REPO_ROOT / "out" / "south-africa-provinces.apkg"

MODEL_ID = 1_893_420_501
DECK_ID = 1_893_420_502

FIELD_NAMES = [
    "CountryName",
    "SubdivisionType",
    "SubdivisionSlug",
    "SubdivisionName",
    "NativeName",
    "Aliases",
    "CapitalName",
    "SubdivisionWikipediaUrl",
    "CapitalWikipediaUrl",
    "BordersSubdivisions",
    "BordersCountries",
    "BordersWaters",
    "Connections",
    "LocatorFilename",
    "BaseFilename",
]


def read_rows() -> list[dict[str, str]]:
    with SOURCE_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def basename(path_value: str) -> str:
    return Path(path_value).name


def split_pipe(value: str) -> list[str]:
    return [part.strip() for part in value.split("|") if part.strip()]


def join_chips(items: list[str]) -> str:
    if not items:
        return ""
    return "".join(f'<span class="chip">{html.escape(item)}</span>' for item in items)


def map_html(field_name: str, alt_text: str, extra_class: str = "") -> str:
    class_suffix = f" {extra_class}" if extra_class else ""
    return (
        f'<div class="map-frame{class_suffix}">'
        f'<img class="map-image" src="{{{{{field_name}}}}}" alt="{html.escape(alt_text)}">'
        "</div>"
    )


def wiki_box(url_field: str, title: str) -> str:
    return f"""
{{{{#{url_field}}}}}
<div class="wiki-box">
  <div class="wiki-header">
    <div class="wiki-label">{title}</div>
  </div>
  <iframe class="wiki-frame" src="{{{{{url_field}}}}}" loading="lazy" referrerpolicy="no-referrer"></iframe>
  <div class="wiki-link"><a href="{{{{{url_field}}}}}">Open article</a></div>
</div>
{{{{/{url_field}}}}}
"""


def front_shell(card_kind: str, prompt_html: str) -> str:
    return f"""
<div class="shell">
  <div class="plate">
    <div class="banner">
      <div class="deck-label">South Africa Provinces</div>
      <div class="card-kind">{card_kind}</div>
    </div>
    <div class="body">
      <div class="prompt-label">Prompt</div>
      {prompt_html}
    </div>
  </div>
</div>
"""


def back_shell(card_kind: str, prompt_html: str, answer_html: str, extra_html: str = "") -> str:
    return f"""
<div class="shell">
  <div class="plate">
    <div class="banner">
      <div class="deck-label">South Africa Provinces</div>
      <div class="card-kind">{card_kind}</div>
    </div>
    <div class="body">
      <div class="prompt-label">Prompt</div>
      {prompt_html}
      {answer_html}
      {extra_html}
    </div>
  </div>
</div>
"""


def province_answer() -> str:
    return """
<div class="answer">
  <div class="section-label">Province</div>
  <div class="answer-main">{{SubdivisionName}}</div>
  <div class="answer-sub">{{CapitalName}} is the capital.</div>
</div>
"""


def capital_answer() -> str:
    return """
<div class="answer">
  <div class="section-label">Capital</div>
  <div class="answer-main">{{CapitalName}}</div>
  <div class="answer-sub">{{SubdivisionName}}</div>
</div>
"""


def capital_to_province_answer() -> str:
    return """
<div class="answer">
  <div class="section-label">Province</div>
  <div class="answer-main">{{SubdivisionName}}</div>
</div>
"""


def province_meta() -> str:
    return """
<div class="meta-grid">
  <div class="panel">
    <div class="panel-title">Capital</div>
    <div class="panel-value">{{CapitalName}}</div>
  </div>
  <div class="panel">
    <div class="panel-title">Type</div>
    <div class="panel-value">{{SubdivisionType}}</div>
  </div>
</div>
"""


def connections_panels() -> str:
    return """
{{#BordersSubdivisions}}
<div class="panel connections">
  <div class="panel-title">Neighboring Provinces</div>
  <div class="chip-row">{{BordersSubdivisions}}</div>
</div>
{{/BordersSubdivisions}}
{{#BordersCountries}}
<div class="panel connections">
  <div class="panel-title">Countries</div>
  <div class="chip-row">{{BordersCountries}}</div>
</div>
{{/BordersCountries}}
{{#BordersWaters}}
<div class="panel connections">
  <div class="panel-title">Waters</div>
  <div class="chip-row">{{BordersWaters}}</div>
</div>
{{/BordersWaters}}
"""


def south_africa_model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        "Country Subdivisions - South Africa Provinces",
        fields=[{"name": name} for name in FIELD_NAMES],
        css=CSS_PATH.read_text(encoding="utf-8"),
        templates=[
            {
                "name": "Locator Map -> Province",
                "qfmt": front_shell(
                    "Locator to Province",
                    map_html("LocatorFilename", "Locator map of a South African province"),
                ),
                "afmt": back_shell(
                    "Locator to Province",
                    map_html("LocatorFilename", "Locator map of a South African province"),
                    province_answer(),
                    province_meta() + wiki_box("SubdivisionWikipediaUrl", "Province article"),
                ),
            },
            {
                "name": "Province -> Locator Map",
                "qfmt": front_shell(
                    "Province to Locator",
                    """
<div class="question">{{SubdivisionName}}</div>
"""
                    + map_html("BaseFilename", "Blank map of South African provinces", "base"),
                ),
                "afmt": back_shell(
                    "Province to Locator",
                    """
<div class="question">{{SubdivisionName}}</div>
"""
                    + map_html("BaseFilename", "Blank map of South African provinces", "base"),
                    map_html("LocatorFilename", "Locator map of {{SubdivisionName}}"),
                    province_meta() + wiki_box("SubdivisionWikipediaUrl", "Province article"),
                ),
            },
            {
                "name": "Province -> Capital",
                "qfmt": front_shell(
                    "Province to Capital",
                    """
<div class="question">{{SubdivisionName}}</div>
"""
                    + map_html("LocatorFilename", "Locator map of {{SubdivisionName}}"),
                ),
                "afmt": back_shell(
                    "Province to Capital",
                    """
<div class="question">{{SubdivisionName}}</div>
"""
                    + map_html("LocatorFilename", "Locator map of {{SubdivisionName}}"),
                    capital_answer(),
                    wiki_box("CapitalWikipediaUrl", "Capital article"),
                ),
            },
            {
                "name": "Capital -> Province",
                "qfmt": front_shell(
                    "Capital to Province",
                    """
<div class="question">{{CapitalName}}</div>
""",
                ),
                "afmt": back_shell(
                    "Capital to Province",
                    """
<div class="question">{{CapitalName}}</div>
""",
                    capital_to_province_answer() + map_html("LocatorFilename", "Locator map of {{SubdivisionName}}"),
                    wiki_box("CapitalWikipediaUrl", "Capital article"),
                ),
            },
            {
                "name": "Province -> Connections",
                "qfmt": front_shell(
                    "Province to Connections",
                    """
<div class="question">{{SubdivisionName}}</div>
"""
                    + map_html("LocatorFilename", "Locator map of {{SubdivisionName}}"),
                ),
                "afmt": back_shell(
                    "Province to Connections",
                    """
<div class="question">{{SubdivisionName}}</div>
"""
                    + map_html("LocatorFilename", "Locator map of {{SubdivisionName}}"),
                    """
<div class="answer">
  <div class="section-label">Connections</div>
  <div class="answer-main">{{SubdivisionName}}</div>
  <div class="answer-sub">{{Connections}}</div>
</div>
""",
                    connections_panels() + wiki_box("SubdivisionWikipediaUrl", "Province article"),
                ),
            },
        ],
    )


def csv_row_to_note_fields(row: dict[str, str]) -> list[str]:
    return [
        row["country_name"],
        row["subdivision_type"],
        row["subdivision_slug"],
        row["subdivision_name"],
        row["native_name"],
        row["aliases"],
        row["capital_name"],
        row["subdivision_wikipedia_url"],
        row["capital_wikipedia_url"],
        join_chips(split_pipe(row["borders_subdivisions"])),
        join_chips(split_pipe(row["borders_countries"])),
        join_chips(split_pipe(row["borders_waters"])),
        row["connections"],
        basename(row["locator_svg_path"]),
        basename(row["base_svg_path"]),
    ]


def media_files(rows: list[dict[str, str]]) -> list[str]:
    files = {
        str(REPO_ROOT / row["locator_svg_path"])
        for row in rows
    }
    files.update(str(REPO_ROOT / row["base_svg_path"]) for row in rows)
    return sorted(files)


def build_deck() -> None:
    rows = read_rows()
    model = south_africa_model()
    deck = genanki.Deck(DECK_ID, "Geography::South Africa Provinces")

    for row in rows:
        note = genanki.Note(
            model=model,
            fields=csv_row_to_note_fields(row),
            guid=genanki.guid_for("south-africa-provinces", row["subdivision_slug"]),
        )
        deck.add_note(note)

    OUTPUT_APKG.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(deck)
    package.media_files = media_files(rows)
    package.write_to_file(str(OUTPUT_APKG))


def main() -> int:
    build_deck()
    print(f"Wrote {OUTPUT_APKG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
