"""Arabic numbers: digits, words, ordinals, and counted nouns."""

from __future__ import annotations

__all__ = [
    "to_arabic_digits",
    "to_western_digits",
    "words",
    "count",
    "ordinal",
    "plural_category",
]

_ARABIC_INDIC = "٠١٢٣٤٥٦٧٨٩"
_EXTENDED_ARABIC_INDIC = "۰۱۲۳۴۵۶۷۸۹"
_WESTERN = "0123456789"

_TO_ARABIC = str.maketrans(_WESTERN, _ARABIC_INDIC)
_TO_WESTERN = str.maketrans(_ARABIC_INDIC + _EXTENDED_ARABIC_INDIC, _WESTERN * 2)

_ONES = ("", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة")

# Index 0 is ten, index 1 is eleven, and so on.
_TEENS = (
    "عشرة",
    "أحد عشر",
    "اثنا عشر",
    "ثلاثة عشر",
    "أربعة عشر",
    "خمسة عشر",
    "ستة عشر",
    "سبعة عشر",
    "ثمانية عشر",
    "تسعة عشر",
)

_TENS = ("", "", "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون")

_HUNDREDS = (
    "",
    "مئة",
    "مئتان",
    "ثلاثمئة",
    "أربعمئة",
    "خمسمئة",
    "ستمئة",
    "سبعمئة",
    "ثمانمئة",
    "تسعمئة",
)

_ORDINALS = (
    "",
    "الأول",
    "الثاني",
    "الثالث",
    "الرابع",
    "الخامس",
    "السادس",
    "السابع",
    "الثامن",
    "التاسع",
    "العاشر",
)

_ORDINAL_TEENS = (
    "",
    "الحادي عشر",
    "الثاني عشر",
    "الثالث عشر",
    "الرابع عشر",
    "الخامس عشر",
    "السادس عشر",
    "السابع عشر",
    "الثامن عشر",
    "التاسع عشر",
)

_ORDINAL_TENS = (
    "",
    "",
    "العشرون",
    "الثلاثون",
    "الأربعون",
    "الخمسون",
    "الستون",
    "السبعون",
    "الثمانون",
    "التسعون",
)

# The unit half of a compound ordinal: 21 is الحادي والعشرون, not الأول والعشرون.
_ORDINAL_UNITS = (
    "",
    "الحادي",
    "الثاني",
    "الثالث",
    "الرابع",
    "الخامس",
    "السادس",
    "السابع",
    "الثامن",
    "التاسع",
)

# (value, singular, dual, plural, accusative) from largest to smallest.
_SCALES = (
    (1_000_000_000, "مليار", "ملياران", "مليارات", "مليار"),
    (1_000_000, "مليون", "مليونان", "ملايين", "مليون"),
    (1_000, "ألف", "ألفان", "آلاف", "ألفاً"),
)

_MAX = 999_999_999_999


def to_arabic_digits(text: str) -> str:
    """Replace Western digits with Arabic-Indic ones.

    >>> to_arabic_digits("2026")
    '٢٠٢٦'
    """
    return text.translate(_TO_ARABIC)


def to_western_digits(text: str) -> str:
    """Replace Arabic-Indic and Extended Arabic-Indic digits with Western ones.

    >>> to_western_digits("٢٠٢٦")
    '2026'
    """
    return text.translate(_TO_WESTERN)


def _below_thousand(n: int, *, construct: bool = False) -> str:
    """Render 1..999. *construct* switches 200 to its construct form, مئتا."""
    parts: list[str] = []
    hundreds, rest = divmod(n, 100)
    if hundreds:
        parts.append("مئتا" if construct and hundreds == 2 else _HUNDREDS[hundreds])
    if rest:
        if rest < 10:
            parts.append(_ONES[rest])
        elif rest < 20:
            parts.append(_TEENS[rest - 10])
        else:
            tens, units = divmod(rest, 10)
            if units:
                parts.append(f"{_ONES[units]} و{_TENS[tens]}")
            else:
                parts.append(_TENS[tens])
    return " و".join(parts)


def _scale_words(
    k: int,
    singular: str,
    dual: str,
    plural: str,
    accusative: str,
    *,
    has_remainder: bool,
) -> str:
    """Render the multiplier of a scale word, e.g. 3 in 3000."""
    if k == 1:
        return singular
    if k == 2:
        return dual if not has_remainder else singular
    if 3 <= k <= 10:
        unit = _ONES[k] if k < 10 else _TEENS[0]
        return f"{unit} {plural}"
    if 11 <= k <= 99:
        return f"{_below_thousand(k)} {accusative}"
    return f"{_below_thousand(k, construct=True)} {singular}"


def words(n: int) -> str:
    """Spell an integer in Arabic words.

    Supports 0 to 999,999,999,999. Negative numbers are prefixed with سالب.

    >>> words(1234)
    'ألف ومئتان وأربعة وثلاثون'
    """
    if n < 0:
        return f"سالب {words(-n)}"
    if n == 0:
        return "صفر"
    if n > _MAX:
        raise ValueError(f"words() supports up to {_MAX:,}")

    groups: list[str] = []
    remainder = n
    for value, singular, dual, plural, accusative in _SCALES:
        k, remainder = divmod(remainder, value)
        if k:
            groups.append(
                _scale_words(
                    k, singular, dual, plural, accusative, has_remainder=bool(remainder)
                )
            )
    if remainder:
        groups.append(_below_thousand(remainder))
    return " و".join(groups)


def count(
    n: int,
    singular: str,
    *,
    dual: str | None = None,
    plural: str | None = None,
    accusative: str | None = None,
    arabic_digits: bool = True,
) -> str:
    """Attach the correctly inflected noun to a number.

    Arabic changes the noun's shape with the number: singular after 1, dual
    after 2, plural after 3-10, accusative singular after 11-99, and singular
    again from 100 up. Supply the forms you have; anything missing falls back
    to *singular*.

    >>> count(3, "كتاب", plural="كتب")
    '٣ كتب'
    """
    if n < 0:
        raise ValueError("count() expects a non-negative number")

    rest = n % 100
    if n == 1:
        form = singular
    elif n == 2:
        form = dual or singular
    elif 3 <= rest <= 10:
        form = plural or singular
    elif 11 <= rest <= 99:
        form = accusative or singular
    else:
        form = singular

    number = to_arabic_digits(str(n)) if arabic_digits else str(n)
    return f"{number} {form}"


def ordinal(n: int) -> str:
    """The ordinal word for 1..99.

    >>> ordinal(21)
    'الحادي والعشرون'
    """
    if not 1 <= n <= 99:
        raise ValueError("ordinal() supports 1..99")
    if n <= 10:
        return _ORDINALS[n]
    if n < 20:
        return _ORDINAL_TEENS[n - 10]
    tens, units = divmod(n, 10)
    if units:
        return f"{_ORDINAL_UNITS[units]} و{_ORDINAL_TENS[tens]}"
    return _ORDINAL_TENS[tens]


def plural_category(n: int) -> str:
    """The CLDR plural category for *n* in Arabic.

    One of zero, one, two, few, many, other.

    >>> plural_category(11)
    'many'
    """
    n = abs(n)
    if n == 0:
        return "zero"
    if n == 1:
        return "one"
    if n == 2:
        return "two"
    rest = n % 100
    if 3 <= rest <= 10:
        return "few"
    if 11 <= rest <= 99:
        return "many"
    return "other"
