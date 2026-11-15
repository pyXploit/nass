# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 332 lemmas that were previously invisible to the lexicon, because their only
  Wiktionary plural row carried no case tag. `pick` now falls back to untagged
  rows when an entry has no tagged nominative form at all, still refusing
  anything definite, construct, accusative or genitive, any construct phrase,
  and anything carrying the definite article. The fallback never runs for an
  entry that already has a tagged form, so every lemma that was already in the
  lexicon keeps exactly the plural it had
- Lemmas whose only plural row was a bare `-` or a Latin transliteration are
  kept as known words with no plural, instead of being dropped

### Fixed
- Latin transliteration rows (`hawwāʔūna`, `ḡarafātun`) were being stored as if
  they were Arabic plural forms
- Judeo-Arabic entries written in Hebrew script were entering an Arabic lexicon
- A plural identical to its own singular is no longer returned: Wiktionary
  lists lexicalised plurals (`آثار`, `علوم`) as nouns in their own right, so
  `plural("آثار")` returned `آثار`. It now returns `None` while `known` stays
  `True`, matching how collectives like `موز` already behaved

### Planned
- More month-name sets for `speak`
- A tool for filling gaps in the plural lexicon

## [0.4.0] - 2026-11-13

### Added
- `plural`, `plurals`, `dual`, `duals` — sourced from a lexicon built out of
  English Wiktionary (9,223 lemmas, 10,860 entries). Nothing is generated: a
  word that is not in the lexicon returns `None` instead of a guess
- `glosses` — short English glosses, so homographs can be told apart
- `known` — whether a word has a lexicon entry
- `vocalized=True` on every inflection function, returning the diacritized form
- Lookup strips the definite article, so `plural("الكتاب")` works; a short
  blocklist keeps lexicalised words like `الأولى` and `اللهم` from being
  mistaken for article + stem
- `tools/gaps.py` ranks the lemmas that have no plural by how often they are used
- `tools/make_entry_data.py` and `tools/merge_overrides.py` back a small
  authoring page for filling those gaps by hand

### Notes
- The lexicon is CC BY-SA 3.0 and ships as a separate data file; the code
  remains MIT. Rebuild it with `tools/build_data.py`

## [0.3.0] - 2026-11-13

### Fixed
- `count(2, noun, dual=...)` returns the dual on its own — كتابان, not ٢ كتابان
- `speak` forms the dual for "2 + noun" instead of writing اثنان before it

### Added
- `speak` — numbers, times, dates and percentages rewritten as spoken Arabic,
  with Levantine and Egyptian month names
- `plot.enable()` — patches matplotlib versions before 3.11, and deliberately
  does nothing on 3.11+, which shapes Arabic itself via HarfBuzz

## [0.2.0] - 2026-11-13

### Added
- `shape` — presentation forms chosen from each letter's joining context,
  with lam-alef ligatures and diacritic-safe joins
- `display` — shaping plus bidi reordering for renderers that do neither
- `wrap` — line breaking with a pluggable measurer, keeping Arabic
  punctuation attached to the word it follows

## [0.1.0] - 2026-11-13

### Added
- `normalize`, `remove_diacritics`, `is_arabic`, `collapse_whitespace`
- `words`, `count`, `ordinal`, `plural_category`
- `to_arabic_digits`, `to_western_digits`
