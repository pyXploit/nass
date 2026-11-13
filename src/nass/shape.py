"""Shaping and display reordering for renderers that do neither.

Most renderers — matplotlib, PIL, a few PDF libraries — draw one glyph per code
point, left to right. Arabic needs the opposite: letters change shape depending
on their neighbours, and the line reads right to left.

:func:`shape` picks the right presentation form for every letter.
:func:`display` also reorders the result so a left-to-right renderer draws it
correctly. Use ``display`` when the renderer does neither; use ``shape`` alone
when it already handles bidi.
"""

from __future__ import annotations

import unicodedata

__all__ = ["shape", "display"]

_LAM = "\u0644"
_ALEF_VARIANTS = frozenset("\u0622\u0623\u0625\u0627")

_FORM_NAMES = ("isolated", "final", "initial", "medial")

# base char -> {form: presentation char}
_FORMS: dict[str, dict[str, str]] = {}
# (lam, alef) -> {form: presentation char}
_LIGATURES: dict[tuple[str, str], dict[str, str]] = {}


def _build_tables() -> None:
    """Derive the presentation-form tables from Unicode's own decomposition data.

    Every Arabic presentation form decomposes to its base letter plus a tag
    naming the form, so the mapping does not have to be maintained by hand.
    """
    for cp in range(0xFB50, 0xFF00):
        ch = chr(cp)
        decomposition = unicodedata.decomposition(ch)
        if not decomposition.startswith("<"):
            continue
        tag, _, rest = decomposition.partition(" ")
        form = tag[1:-1]
        if form not in _FORM_NAMES:
            continue
        parts = rest.split()
        if len(parts) == 1:
            _FORMS.setdefault(chr(int(parts[0], 16)), {})[form] = ch
        elif len(parts) == 2:
            key = (chr(int(parts[0], 16)), chr(int(parts[1], 16)))
            _LIGATURES.setdefault(key, {})[form] = ch


_build_tables()


def _joining(ch: str) -> str | None:
    """Joining type of *ch*: D dual, R right-joining, U non-joining, None other."""
    forms = _FORMS.get(ch)
    if not forms:
        return None
    if "initial" in forms:
        return "D"
    if "final" in forms:
        return "R"
    return "U"


def _neighbor(text: str, index: int, step: int) -> str | None:
    """The nearest non-mark character from *index*, or None at the edge."""
    j = index + step
    while 0 <= j < len(text):
        if unicodedata.category(text[j]) != "Mn":
            return text[j]
        j += step
    return None


def shape(text: str) -> str:
    """Replace Arabic letters with the presentation form their context needs.

    The result stays in logical order. Diacritics are left untouched.

    >>> shape("ب") == "\\ufe8f"
    True
    >>> shape("بب") == "\\ufe91\\ufe90"
    True
    """
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]

        if ch == _LAM and i + 1 < n and text[i + 1] in _ALEF_VARIANTS:
            ligature = _LIGATURES.get((ch, text[i + 1]))
            if ligature is not None:
                prev = _neighbor(text, i, -1)
                joins_prev = prev is not None and _joining(prev) == "D"
                out.append(ligature["final"] if joins_prev else ligature["isolated"])
                i += 2
                continue

        forms = _FORMS.get(ch)
        if forms is None:
            out.append(ch)
            i += 1
            continue

        prev = _neighbor(text, i, -1)
        nxt = _neighbor(text, i, 1)
        joins_prev = prev is not None and _joining(prev) == "D"
        joins_next = nxt is not None and _joining(nxt) in ("D", "R")

        if joins_prev and joins_next:
            form = "medial"
        elif joins_prev:
            form = "final"
        elif joins_next:
            form = "initial"
        else:
            form = "isolated"

        out.append(forms.get(form) or forms.get("isolated") or ch)
        i += 1
    return "".join(out)


_RTL_RANGES = (
    (0x0600, 0x06FF),
    (0x0750, 0x077F),
    (0x08A0, 0x08FF),
    (0xFB50, 0xFDFF),
    (0xFE70, 0xFEFF),
)


def _direction(ch: str) -> str:
    if ch.isdigit():
        return "L"
    cp = ord(ch)
    if any(lo <= cp <= hi for lo, hi in _RTL_RANGES):
        return "R"
    if ch.isalnum():
        return "L"
    return "N"


def _resolve_neutrals(dirs: list[str], base: str) -> list[str]:
    out = list(dirs)
    i = 0
    n = len(out)
    while i < n:
        if out[i] != "N":
            i += 1
            continue
        j = i
        while j < n and out[j] == "N":
            j += 1
        before = out[i - 1] if i > 0 else base
        after = out[j] if j < n else base
        resolved = before if before == after else base
        for k in range(i, j):
            out[k] = resolved
        i = j
    return out


def _clusters(text: str) -> list[str]:
    """Split into base-plus-marks units so reversing cannot orphan a diacritic."""
    out: list[str] = []
    for ch in text:
        if unicodedata.category(ch) == "Mn" and out:
            out[-1] += ch
        else:
            out.append(ch)
    return out


def _reorder(text: str) -> str:
    if not text:
        return text
    dirs = [_direction(ch) for ch in text]
    base = "R" if dirs.count("R") >= dirs.count("L") else "L"
    dirs = _resolve_neutrals(dirs, base)

    runs: list[tuple[str, str]] = []
    start = 0
    for i in range(1, len(text) + 1):
        if i == len(text) or dirs[i] != dirs[start]:
            runs.append((dirs[start], text[start:i]))
            start = i

    runs.reverse()
    parts: list[str] = []
    for direction, chunk in runs:
        if direction == "R":
            parts.append("".join(reversed(_clusters(chunk))))
        else:
            parts.append(chunk)
    return "".join(parts)


def display(text: str) -> str:
    """Shape *text* and reorder it for a renderer that draws left to right.

    >>> display("بب") == "\\ufe90\\ufe91"
    True
    """
    return _reorder(shape(text))
