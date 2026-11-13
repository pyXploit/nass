"""Turn an exported entry page file into src/nass/data/overrides.jsonl.

The page at /nass-review/plurals/ keeps its work in localStorage and exports a
JSON file. This script converts that file into the override rows that
``tools/build_data.py`` merges over the extracted lexicon.

Usage::

    python tools/merge_overrides.py --input nass-overrides.json
    python tools/build_data.py --input kaikki-ar.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "nass" / "data" / "overrides.jsonl"


def row(word: str, entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "w": word,
        "pos": "noun",
        "n": 1,
        "d": 0,
        "pl": [{"f": form, "t": ""} for form in entry.get("pl") or []],
        "du": [{"f": form, "t": ""} for form in entry.get("du") or []],
        "g": "",
        "none": 1 if entry.get("none") else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="the JSON exported by the page")
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for section in ("gaps", "verify"):
        for word, entry in (payload.get(section) or {}).items():
            if not entry.get("pl") and not entry.get("du") and not entry.get("none"):
                continue
            rows.append(row(word, entry))

    rows.sort(key=lambda r: r["w"])
    out = Path(args.out)
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
