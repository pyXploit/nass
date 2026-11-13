"""Line breaking for Arabic text.

Wrapping Arabic by character count produces broken words and a ragged edge,
because glyph widths vary far more than in Latin text. Pass a real measurer —
``font.getlength`` from PIL, or your renderer's own — and this breaks at word
boundaries that respect Arabic punctuation.
"""

from __future__ import annotations

from collections.abc import Callable

__all__ = ["wrap"]

Measure = Callable[[str], float]

# Punctuation that must never begin a line.
_NO_BREAK_BEFORE = frozenset("،؛؟!.,:;)]}»”’")
# Characters that must never end a line.
_NO_BREAK_AFTER = frozenset("([{«“‘")


def _merge(words: list[str]) -> list[str]:
    """Glue punctuation to the word it belongs to before wrapping."""
    merged: list[str] = []
    for word in words:
        if merged and (word[0] in _NO_BREAK_BEFORE or merged[-1][-1] in _NO_BREAK_AFTER):
            merged[-1] = f"{merged[-1]} {word}"
        else:
            merged.append(word)
    return merged


def wrap(
    text: str,
    width: float,
    *,
    measure: Measure = len,
    break_long_words: bool = False,
) -> list[str]:
    """Break *text* into lines no wider than *width*.

    *measure* maps a string to its rendered width. It defaults to ``len``, which
    is only right for monospaced output — pass a real measurer for layout.

    Words are never split unless *break_long_words* is true, and Arabic
    punctuation is kept with the word it follows.

    >>> wrap("مرحبا بالعالم", 12)
    ['مرحبا', 'بالعالم']
    >>> wrap("مرحبا بالعالم", 12, measure=lambda s: len(s) * 2)
    ['مرحبا', 'بالعالم']
    """
    if width <= 0:
        raise ValueError("width must be positive")

    words = _merge(text.split())
    if not words:
        return []

    lines: list[str] = []
    current = ""

    for word in words:
        candidate = f"{current} {word}" if current else word
        if measure(candidate) <= width:
            current = candidate
            continue

        if current:
            lines.append(current)
            current = ""

        if measure(word) <= width or not break_long_words:
            current = word
            continue

        chunk = ""
        for ch in word:
            if measure(chunk + ch) <= width:
                chunk += ch
            else:
                if chunk:
                    lines.append(chunk)
                chunk = ch
        current = chunk

    if current:
        lines.append(current)
    return lines
