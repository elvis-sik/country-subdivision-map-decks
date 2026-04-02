# Country Subdivision Map Decks

## Goal

Find existing Anki decks for first-level country subdivisions where the study flow is as close as possible to:

- blank map -> subdivision name
- subdivision name -> locator map

If we cannot find a good deck for a country, we should mark it as a likely build-ourselves candidate later.

## Workflow

1. Search AnkiWeb first.
2. Use Anki deck mirrors/indexes when AnkiWeb search is too noisy or JS-only.
3. Save only plausible candidates here with short notes.
4. User checks the links.
5. After review, mark each country as:
   - `usable`
   - `maybe usable`
   - `not found`
   - `build later`

## Active Scope

We are building these ourselves now.

### Keep

- Mexico: 32 federative entities
- South Africa: 9 provinces
- Turkey: 7 geographical regions
- Iran: 31 provinces

### Dropped

- Ukraine
- Poland
- Philippines
- Vietnam
- Egypt
- Kazakhstan
- Indonesia

## Initial Findings

### Mexico

Status: `build ourselves`

- [Mexican States](https://ankiweb.net/shared/info/79444390)
  - mirror: [anki-decks.com detail page](https://anki-decks.com/anki-decks/geography/mexican-states/)
  - notes: 32 cards, rating 9
- [Estados y capitales de Mexico](https://ankiweb.net/shared/info/2024767940)
  - mirror: [anki-decks.com detail page](https://anki-decks.com/anki-decks/geography/estados-y-capitales-de-mexico/)
  - notes: 32 cards, rating 1

### Indonesia

Status: `dropped`

- No solid subdivision-map deck found in the first pass through AnkiWeb mirrors and web search.

### South Africa

Status: `build ourselves`

- No solid province-map deck found in the first pass through AnkiWeb mirrors and web search.

### Poland

Status: `dropped`

- [Wojewodztwa Polskie](https://ankiweb.net/shared/info/902241656)
  - mirror: [anki-decks.com detail page](https://anki-decks.com/anki-decks/geography/wojewodztwa-polskie/)
  - notes: 16 cards, rating 4
- [Polskie Wojewodztwa](https://ankiweb.net/shared/info/2674520820)
  - mirror: [anki-decks.com detail page](https://anki-decks.com/anki-decks/geography/polskie-wojewodztwa/)
  - notes: 16 cards, rating 3
- [Regions of European Countries (with maps and capitals)](https://ankiweb.net/shared/info/592931210)
  - mirror: [anki-decks.com detail page](https://anki-decks.com/anki-decks/geography/regions-of-european-countries-with-/)
  - notes: 92 cards, rating 5; broader Europe deck, so this is only a bonus candidate

### Turkey

Status: `build ourselves`

- We only care about the 7 geographical regions now, not the 81 provinces.

### Vietnam

Status: `dropped`

- [Provinces of Vietnam](https://ankiweb.net/shared/info/663361801)
  - mirror: [anki-decks.com detail page](https://anki-decks.com/anki-decks/geography/provinces-of-vietnam/)
  - notes: 61 cards, rating 4

### Philippines

Status: `dropped`

- No solid region/province map deck found in the first pass through AnkiWeb mirrors and web search.

### Ukraine

Status: `dropped`

- [Ukrainian Oblasts (Geography)](https://ankiweb.net/shared/info/1511688484)
  - mirror: [anki-decks.com detail page](https://anki-decks.com/anki-decks/geography/ukrainian-oblasts-geography/)
  - notes: 27 cards, rating 1
- [Geography of Ukraine](https://ankiweb.net/shared/info/533004510)
  - mirror: [anki-decks.com detail page](https://anki-decks.com/anki-decks/geography/geography-of-ukraine/)
  - notes: 25 cards, rating 0
- [Regions of European Countries (with maps and capitals)](https://ankiweb.net/shared/info/592931210)
  - mirror: [anki-decks.com detail page](https://anki-decks.com/anki-decks/geography/regions-of-european-countries-with-/)
  - notes: 92 cards, rating 5; broader Europe deck, so this is only a bonus candidate

## Notes

- AnkiWeb's current shared-deck search is heavily JavaScript-driven, so the most reliable first-pass results came from Anki deck mirror/index pages that expose direct AnkiWeb IDs.
- The `not found` entries above mean "not found in the initial pass," not "definitely unavailable anywhere."

## Map Sourcing

Current goal: get SVG source maps into the repo for the four active countries.

Status: `done`

Desired assets per country:

- one base country map with first-level borders
- locator SVGs for each target subdivision where available

Expected target counts:

- Mexico: 1 base + 32 locators
- South Africa: 1 base + 9 locators
- Turkey: 1 base + 7 locators
- Iran: 1 base + 31 locators

Fetched counts:

- Mexico: 1 base + 32 locators
- South Africa: 1 base + 9 locators
- Turkey: 1 base + 7 locators
- Iran: 1 base + 31 locators

## Normalization And Inspection

Status: `done`

- filenames normalized to stable lowercase hyphen slugs
- machine-readable map manifest written to `maps/manifest.tsv`
- SVG inspection report written to `maps/INSPECTION.md`
- all 4 base SVGs and all 79 locator SVGs appear label-free by automated tag inspection

## Data Model

Status: `in progress`

Current canonical CSV fields include:

- subdivision name
- capital
- subdivision Wikipedia URL
- capital Wikipedia URL
- neighboring subdivisions
- neighboring countries
- bordering waters
- combined connections summary
- locator SVG path
- base SVG path

Country-specific enrichment now included:

- Iran: `native_name` in Persian and `aliases` for English transliteration variants
- Turkey: `native_name` in Turkish

Notes:

- water-border fields are manually curated where Wikidata was incomplete or noisy
- Turkey's seven geographical regions intentionally leave capital fields blank

## Card Model

Status: `chosen`

The working card set for country subdivision decks is:

1. locator map -> subdivision
2. subdivision -> locator map
3. subdivision -> capital
4. capital -> subdivision
5. subdivision -> connections

Modeling choice:

- use country-specific note types when helpful, so each deck can have its own styling and card ergonomics

## First Deck Pass

Status: `in progress`

South Africa is the first full deck scaffold.

Current implementation:

- reproducible APKG builder at `scripts/build_south_africa_apkg.py`
- deck package output at `out/south-africa-provinces.apkg`
- dedicated deck styling at `templates/south_africa.css`
- card backs include a small Wikipedia iframe plus a direct article link fallback

## Lessons Learned

Status: `documented`

Written to:

- `LESSONS.md`

Key points captured there:

- use HTML map fields, not bare media filenames, for Anki image references
- version note types whenever field schema changes
- sanitize packaged SVGs before including them in the deck
- keep `SubdivisionName` as the first and sort field
- optimize card backs to avoid unnecessary scrolling
- present connections as structured blocks, not long prose

## Next Deck Pass

Status: `in progress`

Mexico is the next full scaffold after South Africa.

Current implementation:

- reproducible APKG builder at `scripts/build_mexico_apkg.py`
- deck package output at `out/mexico-federative-entities.apkg`
- dedicated deck styling at `templates/mexico.css`
