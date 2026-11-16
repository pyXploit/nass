"""nass — Arabic text, handled correctly, everywhere Python touches it.

Every function takes Arabic text and returns Arabic text. No objects, no
configuration, no surprises.
"""

from __future__ import annotations

import importlib
from typing import Any

from nass.inflect import dual, duals, glosses, known, plural, plurals
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
from nass.speak import speak
from nass.wrap import wrap

__version__ = "0.4.1"

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
    # inflect
    "plural",
    "plurals",
    "dual",
    "duals",
    "glosses",
    "known",
    # shape
    "shape",
    "display",
    # wrap
    "wrap",
    # speak
    "speak",
    # plot (lazy: importing it must not require matplotlib)
    "plot",
]


def __getattr__(name: str) -> Any:
    if name == "plot":
        return importlib.import_module("nass.plot")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
