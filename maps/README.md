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

## Next Step

After the assets are fetched, normalize file naming and inspect whether any source SVGs need cleanup before deck generation.
