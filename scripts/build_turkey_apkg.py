#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import re
from pathlib import Path

try:
    import genanki
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit(
        "genanki is required to build the deck. Install it with `uv sync --extra deck` "
        "or otherwise make `genanki` available in this environment."
    ) from exc


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_CSV = REPO_ROOT / "data" / "subdivisions" / "turkey.csv"
CSS_PATH = REPO_ROOT / "templates" / "turkey.css"
OUTPUT_APKG = REPO_ROOT / "out" / "turkey-regions.apkg"
GENERATED_MEDIA_DIR = REPO_ROOT / "out" / "generated-media" / "turkey"

MODEL_ID = 1_893_420_701
DECK_ID = 1_893_420_702

FIELD_NAMES = [
    "SubdivisionName",
    "SubdivisionSlug",
    "SubdivisionType",
    "NativeName",
    "SubdivisionWikipediaUrl",
    "BordersSubdivisions",
    "BordersCountries",
    "BordersWaters",
    "Connections",
    "Notes",
    "Card_LocatorMap_HTML",
    "Card_BlankMap_HTML",
]


def read_rows() -> list[dict[str, str]]:
    with SOURCE_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def basename(path_value: str) -> str:
    return Path(path_value).name


def sanitize_svg(svg_path: Path, output_path: Path) -> None:
    text = svg_path.read_text(encoding="utf-8")
    entity_map = {
        "&ns_extend;": "http://ns.adobe.com/Extensibility/1.0/",
        "&ns_ai;": "http://ns.adobe.com/AdobeIllustrator/10.0/",
        "&ns_graphs;": "http://ns.adobe.com/Graphs/1.0/",
        "&ns_vars;": "http://ns.adobe.com/Variables/1.0/",
        "&ns_imrep;": "http://ns.adobe.com/ImageReplacement/1.0/",
        "&ns_sfw;": "http://ns.adobe.com/SaveForWeb/1.0/",
        "&ns_custom;": "http://ns.adobe.com/GenericCustomNamespace/1.0/",
        "&ns_adobe_xpath;": "http://ns.adobe.com/XPath/1.0/",
    }
    for entity, value in entity_map.items():
        text = text.replace(entity, value)

    text = re.sub(r'<!DOCTYPE[\s\S]*?\]\s*>', "", text, count=1, flags=re.IGNORECASE)
    text = re.sub(r'<!DOCTYPE[^>]*>', "", text, count=1, flags=re.IGNORECASE)
    text = re.sub(r"<metadata\b[\s\S]*?</metadata>", "", text, flags=re.IGNORECASE)
    text = re.sub(
        r"<switch>\s*<foreignObject\b[\s\S]*?</foreignObject>\s*(<g\b[\s\S]*?</g>)\s*</switch>",
        r"\1",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\s+i:extraneous=\"[^\"]*\"", "", text)
    text = re.sub(r"\s+enable-background=\"[^\"]*\"", "", text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def prepare_media(rows: list[dict[str, str]]) -> list[str]:
    GENERATED_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    for existing in GENERATED_MEDIA_DIR.iterdir():
        if existing.is_file():
            existing.unlink()

    prepared: dict[str, str] = {}
    for row in rows:
        for path_key in ("locator_svg_path", "base_svg_path"):
            source_path = REPO_ROOT / row[path_key]
            output_path = GENERATED_MEDIA_DIR / source_path.name
            if source_path.suffix.lower() == ".svg":
                sanitize_svg(source_path, output_path)
            else:
                output_path.write_bytes(source_path.read_bytes())
            prepared[output_path.name] = str(output_path)

    return [prepared[name] for name in sorted(prepared)]


def split_pipe(value: str) -> list[str]:
    return [part.strip() for part in value.split("|") if part.strip()]


def join_chips(items: list[str]) -> str:
    if not items:
        return ""
    return "".join(f'<span class="chip">{html.escape(item)}</span>' for item in items)


def map_html(filename: str, alt_text: str, extra_class: str = "") -> str:
    class_suffix = f" {extra_class}" if extra_class else ""
    return (
        f'<div class="map-frame{class_suffix}">'
        f'<img class="map-image" src="{html.escape(filename)}" alt="{html.escape(alt_text)}">'
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
      <div class="deck-label">Turkey Regions</div>
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
      <div class="deck-label">Turkey Regions</div>
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


def region_answer() -> str:
    return """
<div class="answer">
  <div class="section-label">Geographical Region</div>
  <div class="answer-main">{{SubdivisionName}}</div>
  {{#NativeName}}
  <div class="answer-sub">{{NativeName}}</div>
  {{/NativeName}}
</div>
"""


def region_meta() -> str:
    return """
<div class="meta-grid">
  <div class="panel">
    <div class="panel-title">Type</div>
    <div class="panel-value">{{SubdivisionType}}</div>
  </div>
  {{#NativeName}}
  <div class="panel">
    <div class="panel-title">Turkish Name</div>
    <div class="panel-value">{{NativeName}}</div>
  </div>
  {{/NativeName}}
</div>
{{#Notes}}
<div class="panel notes-panel">
  <div class="panel-title">Notes</div>
  <div class="panel-value">{{Notes}}</div>
</div>
{{/Notes}}
"""


def connections_answer() -> str:
    return """
<div class="answer answer-connections">
  <div class="section-label">Connections</div>
  <div class="answer-main">{{SubdivisionName}}</div>
  <div class="connection-grid">
    {{#BordersSubdivisions}}
    <div class="connection-block">
      <div class="connection-label">Neighboring Regions</div>
      <div class="chip-row">{{BordersSubdivisions}}</div>
    </div>
    {{/BordersSubdivisions}}
    {{#BordersCountries}}
    <div class="connection-block">
      <div class="connection-label">Countries</div>
      <div class="chip-row">{{BordersCountries}}</div>
    </div>
    {{/BordersCountries}}
    {{#BordersWaters}}
    <div class="connection-block">
      <div class="connection-label">Waters</div>
      <div class="chip-row">{{BordersWaters}}</div>
    </div>
    {{/BordersWaters}}
  </div>
</div>
"""


def turkey_model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        "Country Subdivisions - Turkey Regions v1",
        fields=[{"name": name} for name in FIELD_NAMES],
        css=CSS_PATH.read_text(encoding="utf-8"),
        sort_field_index=0,
        templates=[
            {
                "name": "Locator Map -> Region",
                "qfmt": front_shell(
                    "Locator to Region",
                    "{{Card_LocatorMap_HTML}}",
                ),
                "afmt": back_shell(
                    "Locator to Region",
                    "{{Card_LocatorMap_HTML}}",
                    region_answer(),
                    region_meta() + wiki_box("SubdivisionWikipediaUrl", "Region article"),
                ),
            },
            {
                "name": "Region -> Locator Map",
                "qfmt": front_shell(
                    "Region to Locator",
                    """
<div class="question">{{SubdivisionName}}</div>
"""
                    + "{{Card_BlankMap_HTML}}",
                ),
                "afmt": back_shell(
                    "Region to Locator",
                    """
<div class="question">{{SubdivisionName}}</div>
""",
                    "{{Card_LocatorMap_HTML}}",
                    region_meta() + wiki_box("SubdivisionWikipediaUrl", "Region article"),
                ),
            },
            {
                "name": "Region -> Connections",
                "qfmt": front_shell(
                    "Region to Connections",
                    """
<div class="question">{{SubdivisionName}}</div>
"""
                    + "{{Card_LocatorMap_HTML}}",
                ),
                "afmt": back_shell(
                    "Region to Connections",
                    """
<div class="question">{{SubdivisionName}}</div>
"""
                    + "{{Card_LocatorMap_HTML}}",
                    connections_answer(),
                    wiki_box("SubdivisionWikipediaUrl", "Region article"),
                ),
            },
        ],
    )


def csv_row_to_note_fields(row: dict[str, str]) -> list[str]:
    return [
        row["subdivision_name"],
        row["subdivision_slug"],
        row["subdivision_type"],
        row["native_name"],
        row["subdivision_wikipedia_url"],
        join_chips(split_pipe(row["borders_subdivisions"])),
        join_chips(split_pipe(row["borders_countries"])),
        join_chips(split_pipe(row["borders_waters"])),
        row["connections"],
        row["notes"],
        map_html(basename(row["locator_svg_path"]), f"Locator map of {row['subdivision_name']}"),
        map_html(basename(row["base_svg_path"]), "Blank map of Turkey's geographical regions", "base"),
    ]


def build_deck() -> None:
    rows = read_rows()
    model = turkey_model()
    deck = genanki.Deck(DECK_ID, "Geography::Turkey Regions")
    media_files = prepare_media(rows)

    for row in rows:
        note = genanki.Note(
            model=model,
            fields=csv_row_to_note_fields(row),
            guid=genanki.guid_for("turkey-regions", row["subdivision_slug"]),
        )
        deck.add_note(note)

    OUTPUT_APKG.parent.mkdir(parents=True, exist_ok=True)
    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(str(OUTPUT_APKG))


def main() -> int:
    build_deck()
    print(f"Wrote {OUTPUT_APKG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
