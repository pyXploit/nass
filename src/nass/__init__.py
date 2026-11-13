"""nass — Arabic text, handled correctly, everywhere Python touches it.

Every function takes Arabic text and returns Arabic text. No objects, no
configuration, no surprises.
"""

from __future__ import annotations

from nass.normalize import collapse_whitespace, is_arabic, normalize, remove_diacritics
from nass.numbers import (
    count,
    ordinal,
    plural_category,
    to_arabic_digits,
    to_western_digits,
    words,
)
from nass.shape import display, shape
from nass.wrap import wrap

__version__ = "0.2.0"

__all__ = [
    "__version__",
    # normalize
    "normalize",
    "remove_diacritics",
    "is_arabic",
    "collapse_whitespace",
    # numbers
    "words",
    "count",
    "ordinal",
    "plural_category",
    "to_arabic_digits",
    "to_western_digits",
    # shape
    "shape",
    "display",
    # wrap
    "wrap",
]
