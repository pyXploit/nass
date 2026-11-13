"""Build ``src/nass/data/nouns.jsonl.gz`` from the Wiktextract Arabic extract.

The upstream file is ~868 MB of JSONL, one line per English-Wiktionary entry.
We keep only the plural and dual cells of the declension tables for nouns,
adjectives and proper names, and drop everything else.

Usage::

    curl -s https://kaikki.org/dictionary/Arabic/kaikki.org-dictionary-Arabic.jsonl \\
        | python tools/build_data.py --input -

    python tools/build_data.py --input /path/to/kaikki.org-dictionary-Arabic.jsonl

Source: https://kaikki.org/dictionary/Arabic/ (Wiktextract, from English Wiktionary).
The extracted data is CC BY-SA 3.0; see ``src/nass/data/LICENSE``.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, TextIO

OUT = Path(__file__).resolve().parent.parent / "src" / "nass" / "data" / "nouns.jsonl.gz"

KEEP_POS = ("noun", "adj", "name")
DIACRITICS = frozenset(
    [chr(c) for c in range(0x064B, 0x0653)] + ["\u0670", "\u0640", "\u0653", "\u0654", "\u0655"]
)
DEMOTE = frozenset({"obsolete", "rare", "archaic", "dialectal"})


def bare(text: str) -> str:
    """Strip Arabic diacritics and tatweel."""
    return "".join(ch for ch in text if ch not in DIACRITICS)


def pick(forms: list[dict[str, Any]], kind: str) -> list[dict[str, str]]:
    """Return the citation forms (indefinite, nominative) of ``kind``."""
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for form in forms:
        tags = set(form.get("tags") or ())
        if kind not in tags:
            continue
        if tags & {"definite", "construct"} or "nominative" not in tags:
            continue
        text = form.get("form")
        if not text or text in seen:
            continue
        seen.add(text)
        kind_tag = "broken" if "broken-form" in tags else "sound" if "sound-form" in tags else ""
        out.append({"f": text, "t": kind_tag})
    return out


def gloss_of(senses: list[dict[str, Any]]) -> str:
    """First gloss that is not a form-of or a demoted sense."""
    for sense in senses:
        tags = set(sense.get("tags") or ())
        if tags & {"form-of", "obsolete", "rare", "archaic"}:
            continue
        glosses = sense.get("glosses") or ()
        if glosses:
            return str(glosses[0])[:70]
    return ""


def is_form_of(senses: list[dict[str, Any]]) -> bool:
    """True when every sense is an inflected form rather than a lemma."""
    return bool(senses) and all("form-of" in (s.get("tags") or ()) for s in senses)


def collect(stream: TextIO) -> tuple[list[dict[str, Any]], Counter[str]]:
    stats: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    for line in stream:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            stats["bad_json"] += 1
            continue
        stats["entries"] += 1
        if entry.get("pos") not in KEEP_POS:
            continue
        forms = entry.get("forms") or []
        plurals = pick(forms, "plural")
        duals = pick(forms, "dual")
        if not plurals and not duals:
            continue
        stats["candidates"] += 1
        senses = entry.get("senses") or []
        if is_form_of(senses):
            stats["dropped_form_of"] += 1
            continue
        tags: set[str] = set()
        for sense in senses:
            tags |= set(sense.get("tags") or ())
        rows.append(
            {
                "w": entry["word"],
                "pos": entry["pos"],
                "n": len(senses),
                "d": 1 if tags & DEMOTE else 0,
                "pl": plurals,
                "du": duals,
                "g": gloss_of(senses),
            }
        )
    return rows, stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSONL path, or - for stdin")
    args = parser.parse_args()

    if args.input == "-":
        rows, stats = collect(sys.stdin)
    else:
        with open(args.input, encoding="utf-8") as handle:
            rows, stats = collect(handle)

    rows.sort(key=lambda r: (bare(r["w"]), -r["n"], r["d"]))

    payload = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(OUT, "wb", compresslevel=9, mtime=0) as handle:
        handle.write(payload)

    lemmas = {bare(r["w"]) for r in rows}
    print(f"entries read      {stats['entries']:>8,}")
    print(f"candidates        {stats['candidates']:>8,}")
    print(f"dropped form-of   {stats['dropped_form_of']:>8,}")
    print(f"rows kept         {len(rows):>8,}")
    print(f"unique lemmas     {len(lemmas):>8,}")
    print(f"with plural       {sum(1 for r in rows if r['pl']):>8,}")
    print(f"with dual         {sum(1 for r in rows if r['du']):>8,}")
    print(f"raw               {len(payload) / 1024:>8,.0f} KB")
    print(f"gzipped           {OUT.stat().st_size / 1024:>8,.0f} KB")
    print(f"sha256            {hashlib.sha256(OUT.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
