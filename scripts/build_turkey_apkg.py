#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import re
import struct
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

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
BLANK_MAP_FILENAME = "turkey-regions-blank.png"
SVG_NS = "http://www.w3.org/2000/svg"
XML_NS = "http://www.w3.org/XML/1998/namespace"
BLANK_FILL_RGB = (239, 230, 200)
BLANK_STROKE_RGB = (132, 100, 59)
BLANK_BACKGROUND_RGB = (255, 253, 248)
REGION_MASK_COLORS = {
    "aegean-region": (220, 231, 243),
    "black-sea-region": (223, 231, 214),
    "central-anatolia-region": (241, 225, 196),
    "eastern-anatolia-region": (217, 214, 239),
    "marmara-region": (207, 223, 240),
    "mediterranean-region": (234, 216, 198),
    "southeastern-anatolia-region": (228, 209, 201),
}

ET.register_namespace("", SVG_NS)

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


def sanitize_svg_text(text: str) -> str:
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
    return text


def sanitize_svg(svg_path: Path, output_path: Path) -> None:
    text = sanitize_svg_text(svg_path.read_text(encoding="utf-8"))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def build_region_mask_svg(rows: list[dict[str, str]], output_path: Path) -> None:
    sample_svg = sanitize_svg_text((REPO_ROOT / rows[0]["locator_svg_path"]).read_text(encoding="utf-8"))
    sample_root = ET.fromstring(sample_svg)
    blank_root = ET.Element(
        f"{{{SVG_NS}}}svg",
        {
            "version": "1.1",
            "viewBox": sample_root.attrib.get("viewBox", "0 0 1579.453 677.313"),
            "width": sample_root.attrib.get("width", "1579.453px"),
            "height": sample_root.attrib.get("height", "677.313px"),
            f"{{{XML_NS}}}space": "preserve",
        },
    )
    ET.SubElement(
        blank_root,
        f"{{{SVG_NS}}}rect",
        {"x": "0", "y": "0", "width": "1579.453", "height": "677.313", "fill": "#fffdf8"},
    )
    all_group = ET.SubElement(blank_root, f"{{{SVG_NS}}}g", {"id": "TurkeyRegions"})
    for row in rows:
        locator_svg = sanitize_svg_text((REPO_ROOT / row["locator_svg_path"]).read_text(encoding="utf-8"))
        locator_root = ET.fromstring(locator_svg)
        provinces = locator_root.find(f".//{{{SVG_NS}}}g[@id='Provinces']")
        if provinces is None:
            raise RuntimeError(f"Could not find Provinces group in {row['locator_svg_path']}")
        group = ET.SubElement(all_group, f"{{{SVG_NS}}}g", {"id": row["subdivision_slug"].replace("-", "_")})
        color = REGION_MASK_COLORS[row["subdivision_slug"]]
        fill_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        for path in provinces.findall(f"{{{SVG_NS}}}path"):
            if path.attrib.get("fill", "").lower() == "#c12838":
                ET.SubElement(group, f"{{{SVG_NS}}}path", {"d": path.attrib["d"], "fill": fill_hex})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(blank_root).write(output_path, encoding="utf-8", xml_declaration=True)


def render_svg_to_bmp(svg_path: Path, bmp_path: Path) -> None:
    subprocess.run(
        [
            "/opt/homebrew/bin/rsvg-convert",
            "-w",
            "1200",
            "-h",
            "520",
            str(svg_path),
            "-o",
            str(bmp_path.with_suffix(".png")),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    subprocess.run(
        ["sips", "-s", "format", "bmp", str(bmp_path.with_suffix(".png")), "--out", str(bmp_path)],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def read_bmp(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    data = path.read_bytes()
    if data[:2] != b"BM":
        raise RuntimeError(f"Unsupported BMP header in {path}")

    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    width = struct.unpack_from("<i", data, 18)[0]
    height = struct.unpack_from("<i", data, 22)[0]
    planes = struct.unpack_from("<H", data, 26)[0]
    bits_per_pixel = struct.unpack_from("<H", data, 28)[0]
    compression = struct.unpack_from("<I", data, 30)[0]
    if planes != 1 or bits_per_pixel != 24 or compression != 0:
        raise RuntimeError(f"Unsupported BMP format in {path}")

    row_size = ((bits_per_pixel * width + 31) // 32) * 4
    absolute_height = abs(height)
    top_down = height < 0
    pixels: list[tuple[int, int, int]] = []
    for y in range(absolute_height):
        row_index = y if top_down else (absolute_height - 1 - y)
        row_start = pixel_offset + row_index * row_size
        for x in range(width):
            blue, green, red = data[row_start + x * 3 : row_start + x * 3 + 3]
            pixels.append((red, green, blue))
    return width, absolute_height, pixels


def write_bmp(path: Path, width: int, height: int, pixels: list[tuple[int, int, int]]) -> None:
    row_size = ((24 * width + 31) // 32) * 4
    image_size = row_size * height
    pixel_offset = 14 + 40
    file_size = pixel_offset + image_size

    header = bytearray()
    header += b"BM"
    header += struct.pack("<I", file_size)
    header += b"\x00\x00\x00\x00"
    header += struct.pack("<I", pixel_offset)
    header += struct.pack("<I", 40)
    header += struct.pack("<i", width)
    header += struct.pack("<i", height)
    header += struct.pack("<H", 1)
    header += struct.pack("<H", 24)
    header += struct.pack("<I", 0)
    header += struct.pack("<I", image_size)
    header += struct.pack("<I", 2835)
    header += struct.pack("<I", 2835)
    header += struct.pack("<I", 0)
    header += struct.pack("<I", 0)

    body = bytearray()
    padding = b"\x00" * (row_size - width * 3)
    for y in range(height - 1, -1, -1):
        row = pixels[y * width : (y + 1) * width]
        for red, green, blue in row:
            body += bytes((blue, green, red))
        body += padding

    path.write_bytes(bytes(header) + bytes(body))


def closest_region_label(pixel: tuple[int, int, int]) -> str:
    all_colors = [("bg", BLANK_BACKGROUND_RGB), *REGION_MASK_COLORS.items()]
    best_label = "bg"
    best_distance = float("inf")
    for label, color in all_colors:
        distance = sum((pixel[channel] - color[channel]) ** 2 for channel in range(3))
        if distance < best_distance:
            best_label = label
            best_distance = distance
    return best_label


def postprocess_region_mask(mask_bmp_path: Path, output_bmp_path: Path) -> None:
    width, height, pixels = read_bmp(mask_bmp_path)
    labels = [closest_region_label(pixel) for pixel in pixels]

    def index(x: int, y: int) -> int:
        return y * width + x

    boundary = [False] * (width * height)
    for y in range(height):
        for x in range(width):
            current_index = index(x, y)
            current_label = labels[current_index]
            if current_label == "bg":
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx = x + dx
                ny = y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if labels[index(nx, ny)] != current_label:
                        boundary[current_index] = True
                        break

    expanded_boundary = boundary[:]
    for y in range(height):
        for x in range(width):
            if not boundary[index(x, y)]:
                continue
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx = x + dx
                    ny = y + dy
                    if 0 <= nx < width and 0 <= ny < height and labels[index(nx, ny)] != "bg":
                        expanded_boundary[index(nx, ny)] = True

    output_pixels: list[tuple[int, int, int]] = []
    for pixel_index, label in enumerate(labels):
        if label == "bg":
            output_pixels.append(BLANK_BACKGROUND_RGB)
        elif expanded_boundary[pixel_index]:
            output_pixels.append(BLANK_STROKE_RGB)
        else:
            output_pixels.append(BLANK_FILL_RGB)
    write_bmp(output_bmp_path, width, height, output_pixels)


def convert_bmp_to_png(bmp_path: Path, png_path: Path) -> None:
    subprocess.run(
        ["sips", "-s", "format", "png", str(bmp_path), "--out", str(png_path)],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def build_blank_map(rows: list[dict[str, str]], output_path: Path) -> None:
    mask_svg_path = output_path.with_name("turkey-regions-mask.svg")
    mask_bmp_path = output_path.with_name("turkey-regions-mask.bmp")
    mask_png_path = output_path.with_name("turkey-regions-mask.png")
    blank_bmp_path = output_path.with_name("turkey-regions-blank.bmp")

    build_region_mask_svg(rows, mask_svg_path)
    render_svg_to_bmp(mask_svg_path, mask_bmp_path)
    postprocess_region_mask(mask_bmp_path, blank_bmp_path)
    convert_bmp_to_png(blank_bmp_path, output_path)

    for temporary_path in (mask_svg_path, mask_bmp_path, mask_png_path, blank_bmp_path):
        if temporary_path.exists():
            temporary_path.unlink()


def prepare_media(rows: list[dict[str, str]]) -> list[str]:
    GENERATED_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    for existing in GENERATED_MEDIA_DIR.iterdir():
        if existing.is_file():
            existing.unlink()

    prepared: dict[str, str] = {}
    for row in rows:
        source_path = REPO_ROOT / row["locator_svg_path"]
        output_path = GENERATED_MEDIA_DIR / source_path.name
        if source_path.suffix.lower() == ".svg":
            sanitize_svg(source_path, output_path)
        else:
            output_path.write_bytes(source_path.read_bytes())
        prepared[output_path.name] = str(output_path)

    blank_output_path = GENERATED_MEDIA_DIR / BLANK_MAP_FILENAME
    build_blank_map(rows, blank_output_path)
    prepared[blank_output_path.name] = str(blank_output_path)

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
        map_html(BLANK_MAP_FILENAME, "Blank map of Turkey's geographical regions", "base"),
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
