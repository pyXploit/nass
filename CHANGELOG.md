# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- More month-name sets for `speak`

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
