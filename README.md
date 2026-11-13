# nass · نص

**Arabic text, handled correctly, everywhere Python touches it.**

[![CI](https://github.com/pyXploit/nass/actions/workflows/ci.yml/badge.svg)](https://github.com/pyXploit/nass/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://pypi.org/project/nass/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[العربية](README.ar.md)

Python's standard library treats Arabic as a sequence of code points. That is
correct and almost never what you want: the same word has several spellings,
numbers have six plural categories, and a renderer that does not shape letters
turns your text into disconnected shapes in the wrong order.

`nass` is the layer between those two facts. Every function takes Arabic text
and returns Arabic text — no objects, no configuration, no surprises.

```bash
pip install nass
```

## What it does

```python
import nass

nass.normalize("أَحْمَد")      # 'احمد'          search and comparison
nass.words(1234)              # 'ألف ومئتان وأربعة وثلاثون'
nass.count(3, "كتاب", plural="كتب")   # '٣ كتب'
nass.ordinal(21)              # 'الحادي والعشرون'
nass.plural_category(11)      # 'many'
nass.to_arabic_digits("2026") # '٢٠٢٦'
```

## Why the plural categories matter

Arabic does not have singular and plural. It has six categories, and the noun
changes shape for each one:

| n | Category | Form |
|---|---|---|
| 0 | `zero` | صفر كتاب |
| 1 | `one` | كتاب |
| 2 | `two` | كتابان |
| 3–10 | `few` | ٣ كتب |
| 11–99 | `many` | ١١ كتابًا |
| 100+ | `other` | ١٠٠ كتاب |

`nass.count()` applies those rules for you. Supply the forms you have;
anything you leave out falls back to the singular.

## Normalisation

Arabic search fails because one word has many spellings. `normalize()` folds
them together:

| Input | Output | Rule |
|---|---|---|
| `أحمد` | `احمد` | alef variants |
| `مدرسة` | `مدرسه` | teh marbuta |
| `مصطفى` | `مصطفي` | alef maqsura |
| `كـتـاب` | `كتاب` | tatweel |
| `مُحَمَّد` | `محمد` | diacritics |
| `١٢٣` | `123` | Arabic-Indic digits |

Every rule can be switched off when the original orthography has to survive:

```python
nass.normalize("مُحَمَّد", strip_diacritics=False)  # 'مُحَمَّد'
```

## API

| Function | Purpose |
|---|---|
| `normalize(text, **rules)` | Fold to a canonical form for comparison |
| `remove_diacritics(text)` | Drop every combining mark |
| `is_arabic(text, threshold=0.5)` | Is this mostly Arabic? |
| `collapse_whitespace(text)` | One space, trimmed |
| `words(n)` | Spell an integer in Arabic |
| `count(n, noun, **forms)` | Number plus correctly inflected noun |
| `ordinal(n)` | 1–99 as an ordinal word |
| `plural_category(n)` | CLDR category: zero, one, two, few, many, other |
| `to_arabic_digits(text)` | `2026` → `٢٠٢٦` |
| `to_western_digits(text)` | `٢٠٢٦` → `2026` |

## Status

`0.1.0` ships normalisation and numbers. Planned, in order:

- `shape` — presentation forms and bidi reordering, for renderers that do not shape
- `wrap` — line breaking with real font metrics
- `speak` — normalisation for speech synthesis
- `plot` — one-line matplotlib integration

## Development

```bash
pip install -e ".[dev]"
ruff check .
mypy
pytest
```

Tests are table-driven: the rules are the test data, so a wrong rule fails
loudly instead of quietly.

## License

MIT
