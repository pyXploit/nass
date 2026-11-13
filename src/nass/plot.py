"""Compatibility shim for matplotlib versions that cannot shape Arabic.

matplotlib 3.11 added HarfBuzz-based complex text layout, so Arabic renders
correctly out of the box. Older versions draw one glyph per code point and
never reorder, which turns Arabic into disconnected shapes in the wrong order.

:func:`enable` checks which one you have. On 3.11 and later it does nothing and
returns ``False`` — patching there would shape the text twice and break it. On
older versions it patches the text layer and returns ``True``.

matplotlib is not a dependency of ``nass``. Importing this module is free;
calling :func:`enable` is what needs it installed.
"""

from __future__ import annotations

import re
from typing import Any

from nass.shape import display

__all__ = ["enable", "disable", "shapes_natively"]

# Presentation forms only appear in text that has already been shaped.
_ALREADY_SHAPED = re.compile(r"[\uFB50-\uFDFF\uFE70-\uFEFF]")

# HarfBuzz text layout landed in matplotlib 3.11.
_NATIVE_SHAPING = (3, 11)

_state: dict[str, Any] = {"patched": False, "original": None}


def _version() -> tuple[int, int]:
    import matplotlib

    match = re.match(r"(\d+)\.(\d+)", matplotlib.__version__)
    if not match:
        return (0, 0)
    return (int(match.group(1)), int(match.group(2)))


def shapes_natively() -> bool:
    """True when the installed matplotlib already shapes Arabic itself.

    >>> import nass
    >>> nass.plot.shapes_natively()   # doctest: +SKIP
    True
    """
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        return False
    return _version() >= _NATIVE_SHAPING


def _process(value: Any) -> Any:
    if not isinstance(value, str) or not value:
        return value
    if _ALREADY_SHAPED.search(value):
        return value
    return display(value)


def enable(*, font: str | None = None) -> bool:
    """Patch matplotlib so Arabic renders correctly, if it needs patching.

    Returns ``True`` when the patch was applied, ``False`` when the installed
    matplotlib already handles Arabic and nothing was changed.

    *font* sets ``font.family`` — useful when the default font has no Arabic
    glyphs. DejaVu Sans, matplotlib's default, does.

    >>> import nass
    >>> nass.plot.enable()          # doctest: +SKIP
    False
    """
    try:
        from matplotlib.text import Text
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise ImportError(
            "nass.plot needs matplotlib: pip install matplotlib"
        ) from exc

    if font is not None:
        import matplotlib

        matplotlib.rcParams["font.family"] = font

    if shapes_natively():
        return False

    if _state["patched"]:
        return True

    original = Text.set_text
    _state["original"] = original

    def set_text(self: Any, s: Any, *args: Any, **kwargs: Any) -> Any:
        return original(self, _process(s), *args, **kwargs)

    setattr(Text, "set_text", set_text)  # noqa: B010 - mypy rejects direct assignment
    _state["patched"] = True
    return True


def disable() -> None:
    """Undo :func:`enable`. Safe to call when it was never enabled."""
    if not _state["patched"]:
        return
    from matplotlib.text import Text

    setattr(Text, "set_text", _state["original"])  # noqa: B010
    _state["patched"] = False
