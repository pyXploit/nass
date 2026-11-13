"""Normalisation for Arabic text: comparison, search, and deduplication."""

from __future__ import annotations

import re

__all__ = [
    "normalize",
    "remove_diacritics",
    "is_arabic",
    "collapse_whitespace",
]

# Arabic combining marks: harakat, tanwin, shadda, sukun, superscript alef,
# the maddah and hamza marks, and the Quranic annotation signs.
_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")

_TATWEEL = "\u0640"

_ALEF = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا"})
_TEH_MARBUTA = str.maketrans({"ة": "ه"})
_YEH = str.maketrans({"ى": "ي"})

_ARABIC_INDIC = "٠١٢٣٤٥٦٧٨٩"
_EXTENDED_ARABIC_INDIC = "۰۱۲۳۴۵۶۷۸۹"
_WESTERN = "0123456789"
_DIGITS = str.maketrans(_ARABIC_INDIC + _EXTENDED_ARABIC_INDIC, _WESTERN * 2)

_WHITESPACE = re.compile(r"\s+")

# Arabic, Arabic Supplement, Arabic Extended-A, and the presentation forms.
_ARABIC_RANGES = (
    (0x0600, 0x06FF),
    (0x0750, 0x077F),
    (0x08A0, 0x08FF),
    (0xFB50, 0xFDFF),
    (0xFE70, 0xFEFF),
)


def remove_diacritics(text: str) -> str:
    """Drop every combining mark from *text*."""
    return _DIACRITICS.sub("", text)


def collapse_whitespace(text: str) -> str:
    """Collapse runs of whitespace to one space and trim both ends."""
    return _WHITESPACE.sub(" ", text).strip()


def is_arabic(text: str, threshold: float = 0.5) -> bool:
    """True when at least *threshold* of the letters in *text* are Arabic.

    Digits, punctuation and Latin letters are ignored when counting, so a
    mostly-Arabic string with an English brand name still counts as Arabic.
    """
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return False
    arabic = sum(
        1 for ch in letters if any(lo <= ord(ch) <= hi for lo, hi in _ARABIC_RANGES)
    )
    return arabic / len(letters) >= threshold


def normalize(
    text: str,
    *,
    strip_diacritics: bool = True,
    unify_alef: bool = True,
    unify_teh_marbuta: bool = True,
    unify_yeh: bool = True,
    strip_tatweel: bool = True,
    unify_digits: bool = True,
) -> str:
    """Fold *text* into a canonical form suitable for comparison.

    The defaults are the aggressive form used for search: two spellings of the
    same word collapse to one string. Turn a rule off when the original
    orthography has to survive.

    >>> normalize("أَحْمَد")
    'احمد'
    >>> normalize("مدرسة")
    'مدرسه'
    """
    if strip_diacritics:
        text = _DIACRITICS.sub("", text)
    if strip_tatweel:
        text = text.replace(_TATWEEL, "")
    if unify_alef:
        text = text.translate(_ALEF)
    if unify_teh_marbuta:
        text = text.translate(_TEH_MARBUTA)
    if unify_yeh:
        text = text.translate(_YEH)
    if unify_digits:
        text = text.translate(_DIGITS)
    return text
