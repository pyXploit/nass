"""Arabic plurals and duals, looked up from a sourced lexicon.

Nothing here is generated. Every form comes from the Wiktextract extract of
English Wiktionary (CC BY-SA 3.0, see ``nass/data/LICENSE``). A word that is
not in the lexicon returns ``None`` rather than a guess.

>>> plural("كتاب")
'كتب'
>>> plural("كتاب", vocalized=True)
'كُتُب'
>>> plurals("مدرسة")
['مدرسات', 'مدارس']
>>> dual("سيارة")
'سيارتان'
>>> plural("زززز") is None
True
"""

from __future__ import annotations

import gzip
import json
from functools import lru_cache
from importlib import resources
from typing import Any

__all__ = ["plural", "plurals", "dual", "duals", "glosses", "known"]

#: Harakat, tanwin, shadda, sukun, superscript alef, tatweel and the hamza marks.
_DIACRITICS = frozenset(
    [chr(code) for code in range(0x064B, 0x0653)]
    + ["\u0670", "\u0640", "\u0653", "\u0654", "\u0655"]
)

#: Case endings that are dropped from a citation form: tanwin and the short vowels.
_CASE = frozenset(chr(code) for code in range(0x064B, 0x0651))

#: (plural forms, dual forms, gloss) for one lexical entry.
_Row = tuple[tuple[str, ...], tuple[str, ...], str]


def _bare(text: str) -> str:
    """Strip every diacritic and tatweel."""
    return "".join(ch for ch in text if ch not in _DIACRITICS)


def _vocalized(text: str) -> str:
    """Keep the vowels, drop the trailing case ending."""
    return text.rstrip("".join(_CASE))


@lru_cache(maxsize=1)
def _table() -> dict[str, list[_Row]]:
    """Load the lexicon once, keyed by the undiacritized lemma."""
    raw = resources.files("nass").joinpath("data/nouns.jsonl.gz").read_bytes()
    table: dict[str, list[_Row]] = {}
    for line in gzip.decompress(raw).decode("utf-8").splitlines():
        if not line:
            continue
        entry: dict[str, Any] = json.loads(line)
        row: _Row = (
            tuple(form["f"] for form in entry["pl"]),
            tuple(form["f"] for form in entry["du"]),
            str(entry.get("g") or ""),
        )
        table.setdefault(_bare(entry["w"]), []).append(row)
    return table


def _forms(word: str, slot: int, vocalized: bool) -> list[str]:
    """Collect one slot across every homograph row, ranked, without duplicates."""
    rows = _table().get(_bare(word))
    if not rows:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for form in row[slot]:
            text = _vocalized(form) if vocalized else _bare(form)
            if text and text not in seen:
                seen.add(text)
                out.append(text)
    return out


def plural(word: str, *, vocalized: bool = False) -> str | None:
    """The most common plural of ``word``, or ``None`` if it is not in the lexicon.

    >>> plural("بيت")
    'بيوت'
    >>> plural("بنك")
    'بنوك'
    """
    forms = _forms(word, 0, vocalized)
    return forms[0] if forms else None


def plurals(word: str, *, vocalized: bool = False) -> list[str]:
    """Every attested plural of ``word``, most common first.

    >>> plurals("شهر")
    ['أشهر', 'شهور']
    >>> plurals("زززز")
    []
    """
    return _forms(word, 0, vocalized)


def dual(word: str, *, vocalized: bool = False) -> str | None:
    """The dual of ``word``, or ``None`` if it is not in the lexicon.

    >>> dual("كتاب")
    'كتابان'
    """
    forms = _forms(word, 1, vocalized)
    return forms[0] if forms else None


def duals(word: str, *, vocalized: bool = False) -> list[str]:
    """Every attested dual of ``word``.

    >>> duals("ماء")
    ['ماءان', 'ماوان', 'مايان']
    """
    return _forms(word, 1, vocalized)


def glosses(word: str) -> list[str]:
    """Short English glosses for ``word``, one per lexical entry.

    Useful for telling homographs apart: ``كتاب`` is both "book" and
    "Qur'an school", and the two have different plurals.

    >>> glosses("كتاب")
    ['book', "a traditional school for teaching Qur'an"]
    """
    rows = _table().get(_bare(word)) or []
    return [row[2] for row in rows if row[2]]


def known(word: str) -> bool:
    """Whether ``word`` has an entry in the lexicon.

    >>> known("كتاب")
    True
    >>> known("زززز")
    False
    """
    return _bare(word) in _table()
