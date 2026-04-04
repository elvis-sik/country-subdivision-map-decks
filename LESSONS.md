# Lessons Learned

## Anki Packaging

- Put full `<img ...>` HTML into note fields for map media, not just bare filenames.
- Reference those HTML fields directly from templates, like `{{Card_LocatorMap_HTML}}`.
- Include the corresponding media files in `genanki.Package.media_files`.
- When a note type's field schema changes, bump both the model ID and the note type name version.
- Keep `SubdivisionName` as field 0 and as the sort field.

## SVG Media

- Reuse SVG media for locator maps and blank maps when Anki renders them correctly.
- Sanitize older Illustrator-style SVGs before packaging them.
- Strip `DOCTYPE`, `metadata`, `foreignObject`, `switch`, and similar export baggage.
- Keep the sanitized copies as generated build artifacts rather than editing source maps in place.
- When a base SVG is labeled or otherwise unusable, derive the blank map from the clean locator SVG layers instead of forcing the bad source file.
- For layered locator maps, inspect the actual group hierarchy first; the best blank-map source may be a dedicated locator/contour group rather than the obvious top-level country group.

## Card Ergonomics

- Fronts should stay compact and ask only one thing.
- Backs should avoid repeating prompt maps when that forces scrolling.
- `Blank -> Locator` works better when the back shows only the locator answer.
- `Province/State -> Capital` works better when the front shows only the subdivision name.
- `Connections` answers are easier to read as labeled blocks than as one long sentence.
- Countries with different fact structures should get different note types instead of carrying dead or empty cards.

## Workflow

- When something looks wrong in Anki, inspect the built `.apkg` directly instead of guessing.
- Verify the package's `collection.anki2` model fields, templates, and stored note values.
- Compare against a known-good deck in the workspace when behavior is surprising.
- Rebuild and re-check after each template change; stale assumptions waste time fast.
