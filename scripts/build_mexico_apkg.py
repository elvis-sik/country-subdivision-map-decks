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
SOURCE_CSV = REPO_ROOT / "data" / "subdivisions" / "mexico.csv"
CSS_PATH = REPO_ROOT / "templates" / "mexico.css"
OUTPUT_APKG = REPO_ROOT / "out" / "mexico-federative-entities.apkg"
GENERATED_MEDIA_DIR = REPO_ROOT / "out" / "generated-media" / "mexico"

MODEL_ID = 1_893_420_601
DECK_ID = 1_893_420_602

FIELD_NAMES = [
    "SubdivisionName",
    "SubdivisionSlug",
    "SubdivisionType",
    "NativeName",
    "Aliases",
    "CapitalName",
    "SubdivisionWikipediaUrl",
    "CapitalWikipediaUrl",
    "BordersSubdivisions",
    "BordersCountries",
    "BordersWaters",
    "Connections",
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
      <div class="deck-label">Mexico Federative Entities</div>
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
      <div class="deck-label">Mexico Federative Entities</div>
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


def entity_answer() -> str:
    return """
<div class="answer">
  <div class="section-label">Federative Entity</div>
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


def capital_to_entity_answer() -> str:
    return """
<div class="answer">
  <div class="section-label">Federative Entity</div>
  <div class="answer-main">{{SubdivisionName}}</div>
</div>
"""


def entity_meta() -> str:
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


def connections_answer() -> str:
    return """
<div class="answer answer-connections">
  <div class="section-label">Connections</div>
  <div class="answer-main">{{SubdivisionName}}</div>
  <div class="connection-grid">
    {{#BordersSubdivisions}}
    <div class="connection-block">
      <div class="connection-label">Neighboring Entities</div>
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


def mexico_model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        "Country Subdivisions - Mexico Federative Entities v1",
        fields=[{"name": name} for name in FIELD_NAMES],
        css=CSS_PATH.read_text(encoding="utf-8"),
        sort_field_index=0,
        templates=[
            {
                "name": "Locator Map -> Entity",
                "qfmt": front_shell("Locator to Entity", "{{Card_LocatorMap_HTML}}"),
                "afmt": back_shell(
                    "Locator to Entity",
                    "{{Card_LocatorMap_HTML}}",
                    entity_answer(),
                    entity_meta() + wiki_box("SubdivisionWikipediaUrl", "Entity article"),
                ),
            },
            {
                "name": "Entity -> Locator Map",
                "qfmt": front_shell(
                    "Entity to Locator",
                    """
<div class="question">{{SubdivisionName}}</div>
"""
                    + "{{Card_BlankMap_HTML}}",
                ),
                "afmt": back_shell(
                    "Entity to Locator",
                    """
<div class="question">{{SubdivisionName}}</div>
""",
                    "{{Card_LocatorMap_HTML}}",
                    entity_meta() + wiki_box("SubdivisionWikipediaUrl", "Entity article"),
                ),
            },
            {
                "name": "Entity -> Capital",
                "qfmt": front_shell(
                    "Entity to Capital",
                    """
<div class="question">{{SubdivisionName}}</div>
""",
                ),
                "afmt": back_shell(
                    "Entity to Capital",
                    """
<div class="question">{{SubdivisionName}}</div>
"""
                    + "{{Card_LocatorMap_HTML}}",
                    capital_answer(),
                    wiki_box("CapitalWikipediaUrl", "Capital article"),
                ),
            },
            {
                "name": "Capital -> Entity",
                "qfmt": front_shell(
                    "Capital to Entity",
                    """
<div class="question">{{CapitalName}}</div>
""",
                ),
                "afmt": back_shell(
                    "Capital to Entity",
                    """
<div class="question">{{CapitalName}}</div>
""",
                    capital_to_entity_answer() + "{{Card_LocatorMap_HTML}}",
                    wiki_box("CapitalWikipediaUrl", "Capital article"),
                ),
            },
            {
                "name": "Entity -> Connections",
                "qfmt": front_shell(
                    "Entity to Connections",
                    """
<div class="question">{{SubdivisionName}}</div>
"""
                    + "{{Card_LocatorMap_HTML}}",
                ),
                "afmt": back_shell(
                    "Entity to Connections",
                    """
<div class="question">{{SubdivisionName}}</div>
"""
                    + "{{Card_LocatorMap_HTML}}",
                    connections_answer(),
                    wiki_box("SubdivisionWikipediaUrl", "Entity article"),
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
        row["aliases"],
        row["capital_name"],
        row["subdivision_wikipedia_url"],
        row["capital_wikipedia_url"],
        join_chips(split_pipe(row["borders_subdivisions"])),
        join_chips(split_pipe(row["borders_countries"])),
        join_chips(split_pipe(row["borders_waters"])),
        row["connections"],
        map_html(basename(row["locator_svg_path"]), f"Locator map of {row['subdivision_name']}"),
        map_html(basename(row["base_svg_path"]), "Blank map of Mexico's federative entities", "base"),
    ]


def build_deck() -> None:
    rows = read_rows()
    model = mexico_model()
    deck = genanki.Deck(DECK_ID, "Geography::Mexico Federative Entities")
    media_files = prepare_media(rows)

    for row in rows:
        note = genanki.Note(
            model=model,
            fields=csv_row_to_note_fields(row),
            guid=genanki.guid_for("mexico-federative-entities", row["subdivision_slug"]),
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
