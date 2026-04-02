# SVG Inspection

This report checks whether the current SVG map assets appear usable as deck-generation inputs.

## Base Maps

Interpretation:

- `text tags = 0` usually means the SVG is already label-free and usable as a blank outline base.
- high structure counts are fine; they mostly indicate many paths/groups, not a problem by themselves.

| Country | File | Text Tags | Structure Tags | Verdict |
| --- | --- | ---: | ---: | --- |
| iran | `maps/base/iran/iran-provinces.svg` | 0 | 391 | ready as blank base |
| mexico | `maps/base/mexico/mexico-states.svg` | 0 | 432 | ready as blank base |
| south-africa | `maps/base/south-africa/south-africa-provinces.svg` | 0 | 24 | ready as blank base |
| turkey | `maps/base/turkey/turkey-regions.svg` | 0 | 5198 | ready as blank base |

## Locator Series

`SVGs with text tags` is a quick sanity check for whether the highlighted locator maps include embedded labels.

| Country | Locator SVGs | SVGs With Text Tags |
| --- | ---: | ---: |
| iran | 31 | 0 |
| mexico | 32 | 0 |
| south-africa | 9 | 0 |
| turkey | 7 | 0 |

## Summary

- All four current base SVGs are label-free by this check.
- The locator sets are also label-free by this check.
- That means we can move to card/deck generation without first stripping text out of these source SVGs.
