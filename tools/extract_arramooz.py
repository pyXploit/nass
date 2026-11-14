"""Extract singular → plural pairs from the arramooz morphological dictionary.

arramooz (https://github.com/linuxscout/arramooz, GPL) is a hand-built Arabic
morphological dictionary. Its noun tables carry a ``الجمع`` column: for a
singular row it holds the plural, for a plural row the ``مفرده`` column holds
the singular. Both directions are read here.

Only what the tables state is kept. A cell like ``+ات`` is the dictionary
saying "the plural is formed with ات", so it is expanded mechanically; cells
that mix several notations (``+ون+ات``, ``+اتأحْنَافٌ``) are dropped rather
than guessed at.

Usage::

    git clone --depth 1 https://github.com/linuxscout/arramooz.git
    python tools/extract_arramooz.py --root arramooz --out arramooz.jsonl
"""

from __future__ import annotations

import argparse
import glob
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

DIACRITICS = frozenset(
    [chr(c) for c in range(0x064B, 0x0653)] + ["\u0670", "\u0640", "\u0653", "\u0654", "\u0655"]
)
TANWIN = "\u064B\u064C\u064D"
#: Short vowels and sukun, stripped from a stem before a suffix is appended.
SHORT = "\u064E\u064F\u0650\u0652"
#: Two case endings in a row is a sign of a broken cell, not a word.
DOUBLE_MARK = re.compile("[\u064B-\u0650]{2}")
#: A lemma that ends in one of these takes the suffix by simple concatenation.
SUFFIXABLE = frozenset(TANWIN + "\u0629")  # tanwin and ta marbuta
#: Only the sound feminine plural is expanded. The masculine one is not:
#: arramooz applies ``+ون`` to elatives and other shapes that never take it
#: (أشبه → أشبهون), and leaving it out costs only 181 lemmas.
SUFFIX = {"+ات": "\u064E\u0627\u062A\u064C"}
SPLIT = re.compile(r"[;؛]")


def bare(text: str) -> str:
    return "".join(ch for ch in text if ch not in DIACRITICS)


def arabic_word(text: str) -> bool:
    """One Arabic word, no spaces, no punctuation, no Latin."""
    if not text or " " in text or "\u200f" in text:
        return False
    return all("\u0600" <= ch <= "\u06FF" or ch in DIACRITICS for ch in text)


def expand(lemma: str, token: str) -> str | None:
    """Apply the ``+ات`` suffix, or return None when it is not safe.

    The suffix is only appended to a stem that ends in a consonant: a word
    ending in a long vowel or a hamza takes a different plural.
    """
    suffix = SUFFIX.get(token)
    if suffix is None:
        return None
    stem = lemma.rstrip(TANWIN).rstrip(SHORT)
    if stem.endswith("\u0629"):
        stem = stem[:-1].rstrip(SHORT)
    if not stem or stem[-1] in "\u0627\u0649\u0648\u064A\u0621":
        return None
    return stem + suffix

def read_table(path: Path) -> list[dict[str, str]]:
    raw = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not raw:
        return []
    header = [h.strip().lstrip("#").strip() for h in raw[0].split("\t")]
    index = {name: position for position, name in enumerate(header)}
    word_col = index.get("مشكول") or index.get("الكلمة")
    number_col = index.get("عدد")
    plural_col = index.get("الجمع")
    if word_col is None or number_col is None or plural_col is None:
        return []
    singular_col = index.get("مفرده") or index.get("مفرد") or index.get("مفرده المحسوب")
    out: list[dict[str, str]] = []
    for line in raw[1:]:
        cells = line.split("\t")
        if len(cells) <= max(word_col, number_col, plural_col):
            continue
        singular = ""
        if singular_col is not None and len(cells) > singular_col:
            singular = cells[singular_col].strip()
        out.append(
            {
                "word": cells[word_col].strip(),
                "number": cells[number_col].strip(),
                "plural": cells[plural_col].strip(),
                "singular": singular,
            }
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="the arramooz checkout")
    parser.add_argument("--out", required=True, help="where to write the pairs")
    args = parser.parse_args()

    stats: Counter[str] = Counter()
    pairs: dict[str, dict[str, Any]] = {}

    def add(lemma: str, plural: str, kind: str) -> None:
        if not arabic_word(lemma) or not arabic_word(plural):
            stats["rejected_shape"] += 1
            return
        if bare(plural) in {"ون", "ات", "ين"} or DOUBLE_MARK.search(plural):
            stats["rejected_shape"] += 1
            return
        if not (set(bare(lemma)) & set(bare(plural))):
            # A plural that shares no letter with its lemma is a broken cell.
            stats["rejected_shape"] += 1
            return
        if bare(lemma) == bare(plural):
            stats["rejected_same"] += 1
            return
        row = pairs.setdefault(bare(lemma), {"w": lemma, "pl": [], "seen": set()})
        if bare(plural) in row["seen"]:
            return
        row["seen"].add(bare(plural))
        row["pl"].append({"f": plural, "t": kind, "s": "arramooz"})
        stats["pairs"] += 1

    for path in sorted(glob.glob(str(Path(args.root) / "data" / "nouns" / "*.csv"))):
        for row in read_table(Path(path)):
            number, word, cell = row["number"], row["word"], row["plural"]
            if number == "مفرد" and cell:
                for token in SPLIT.split(cell):
                    token = token.strip()
                    if not token:
                        continue
                    if token.startswith("+"):
                        form = expand(word, token)
                        if form is None:
                            stats["skipped_suffix"] += 1
                            continue
                        add(word, form, "sound")
                    else:
                        add(word, token, "broken")
            elif number == "جمع":
                # The singular lives in its own column; the plural column is
                # empty on these rows and sometimes holds the singular instead,
                # so it is never used as a fallback.
                lemma = row["singular"]
                if lemma:
                    add(lemma, word, "broken")
                else:
                    stats["skipped_no_singular"] += 1

    rows = []
    for key in sorted(pairs):
        row = pairs[key]
        rows.append(
            {"w": row["w"], "pos": "noun", "n": 1, "d": 0, "pl": row["pl"], "du": [], "g": ""}
        )

    out = Path(args.out)
    payload = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    out.write_text(payload, encoding="utf-8")
    print(f"lemmas with a plural {len(rows):>7,}")
    print(f"plural forms         {stats['pairs']:>7,}")
    for key in ("skipped_suffix", "skipped_no_singular", "rejected_shape", "rejected_same"):
        print(f"  {key:<20} {stats[key]:>7,}")
    print(f"-> {out} ({out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
