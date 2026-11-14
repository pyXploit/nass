"""Turn the researched gap answers into src/nass/data/overrides.jsonl.

``tools/gap_fills.json`` records what the dictionaries say about every lemma
that the Wiktionary extract left without a plural: either the plural forms, or
``none`` when the word has no plural of its own (a collective, an already-plural
form, a maṣdar, a dual, an elative or a proper name).

Usage::

    python tools/research_fills.py
    python tools/build_data.py --input kaikki-ar.jsonl

Rows already in ``overrides.jsonl`` (for example the ones exported by the entry
page) are kept; a researched answer replaces the row for the same word.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
FILLS = ROOT / "tools" / "gap_fills.json"
OUT = ROOT / "src" / "nass" / "data" / "overrides.jsonl"


def row(word: str, entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "w": word,
        "pos": "noun",
        "n": 1,
        "d": 0,
        "pl": [{"f": form["f"], "t": form.get("t", "")} for form in entry.get("pl") or []],
        "du": [{"f": form["f"], "t": form.get("t", "")} for form in entry.get("du") or []],
        "g": "",
        "none": 1 if entry.get("none") else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fills", default=str(FILLS), help="the researched answers")
    parser.add_argument("--out", default=str(OUT), help="where to write the override rows")
    args = parser.parse_args()

    fills = json.loads(Path(args.fills).read_text(encoding="utf-8"))
    fills.pop("_comment", None)

    out = Path(args.out)
    existing: dict[str, dict[str, Any]] = {}
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            if line:
                old = json.loads(line)
                existing[old["w"]] = old

    for word, entry in fills.items():
        existing[word] = row(word, entry)

    rows = [existing[word] for word in sorted(existing)]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )

    added = sum(1 for r in rows if r["pl"] or r["du"])
    print(f"overrides written {len(rows):>5}  ({added} with a form, {len(rows) - added} none)")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
