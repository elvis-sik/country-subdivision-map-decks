# country-subdivision-map-decks

Deck-building workspace for first-level country subdivision geography decks.

Current active countries:

- Mexico
- South Africa
- Turkey
- Iran

## Data

Canonical subdivision seed CSVs live in `data/subdivisions/`.

The main fetch script is:

- `scripts/fetch_subdivision_data.py`

## First deck build

South Africa is the first end-to-end deck target.

Build setup:

```sh
uv sync --extra deck
```

Build the South Africa package:

```sh
.venv/bin/python scripts/build_south_africa_apkg.py
```

Output:

- `out/south-africa-provinces.apkg`

## Lessons

Project notes from the South Africa pass live in:

- `LESSONS.md`

## Next deck build

Mexico is the next full deck target.

Build the Mexico package:

```sh
.venv/bin/python scripts/build_mexico_apkg.py
```

Output:

- `out/mexico-federative-entities.apkg`

Turkey now also has a country-specific builder because its seven geographical regions do not have official capitals.

Build the Turkey package:

```sh
.venv/bin/python scripts/build_turkey_apkg.py
```

Output:

- `out/turkey-regions.apkg`
