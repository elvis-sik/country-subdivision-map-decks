# Maps

This directory stores SVG source assets for the countries we decided to build decks for ourselves.

## Countries

- Mexico
- South Africa
- Turkey
- Iran

## Structure

- `base/<country>/`
  - country-level SVGs with internal subdivision borders
- `locators/<country>/`
  - one highlighted locator SVG per target subdivision when Wikimedia Commons already has a usable series
- `manifest.tsv`
  - normalized local filenames plus source titles and display labels
- `INSPECTION.md`
  - quick validation report on whether the current SVGs are label-free

## Naming

Local SVG filenames are normalized to lowercase hyphenated slugs so downstream deck-generation scripts do not need to deal with spaces, parentheses, or source-specific naming quirks.

## Source Strategy

We are sourcing from Wikimedia Commons so we have:

- stable source pages
- direct SVG downloads
- permissive licenses that allow remixing with attribution/share-alike

## Current Source Files

### Mexico

- base: `File:Mexico States blank map.svg`
- locator category: `Category:SVG locator maps of states in Mexico (location map scheme)`
- note: category includes extra zoom variants, so the fetch script filters those out and keeps the 32 current federative entities

### South Africa

- base: `File:SA provinces.svg`
- locator category: `Category:SVG locator maps of provinces in South Africa (river location map scheme)`
- note: this gives us a clean 9-file province set

### Turkey

- base: `File:Turkey-regions.svg`
- locator category: `Category:SVG locator maps of regions of Turkey (location map scheme)`
- note: this is an exact 7-file match for the target scope

### Iran

- base: `File:Iran provinces.svg`
- locator category: `Category:SVG locator maps of provinces in Iran (location map scheme)`
- note: the locator category contains duplicate/alternate series, so the fetch script keeps the clean one-file-per-province `... in Iran.svg` series and filters out extras

## Re-fetch

Run:

```bash
./scripts/fetch_commons_maps.sh
```

## Current Result

Fetched into the repo:

- Mexico: 1 base SVG + 32 locator SVGs
- South Africa: 1 base SVG + 9 locator SVGs
- Turkey: 1 base SVG + 7 locator SVGs
- Iran: 1 base SVG + 31 locator SVGs

All of those files now use normalized local names.

## Current Validation

See [INSPECTION.md](./INSPECTION.md).

Current result:

- all 4 base SVGs appear label-free
- all 79 locator SVGs appear label-free

## Next Step

Use `manifest.tsv` and the normalized SVG filenames to generate the actual deck inputs.
