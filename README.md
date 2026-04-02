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
