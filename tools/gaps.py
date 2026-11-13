"""Rank the lexicon's gaps by how often the word is actually used.

The lexicon covers 9,223 lemmas, but not every one of them has a plural
recorded. This script joins the lexicon against a frequency list so the
missing entries can be filled in the order that matters.

Usage::

    curl -sL https://raw.githubusercontent.com/hermitdave/FrequencyWords/\\
master/content/2018/ar/ar_50k.txt -o ar_50k.txt
    python tools/gaps.py --freq ar_50k.txt --out gaps.json

The frequency list is not committed: it is a separate work with its own
licence, and the script only needs it at build time.
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "src" / "nass" / "data" / "nouns.jsonl.gz"

DIACRITICS = frozenset(
    [chr(code) for code in range(0x064B, 0x0653)]
    + ["\u0670", "\u0640", "\u0653", "\u0654", "\u0655"]
)


def bare(text: str) -> str:
    return "".join(ch for ch in text if ch not in DIACRITICS)


def load_lexicon() -> dict[str, dict[str, Any]]:
    """Collapse the rows to one record per lemma."""
    raw = gzip.decompress(DATA.read_bytes()).decode("utf-8")
    out: dict[str, dict[str, Any]] = {}
    for line in raw.splitlines():
        if not line:
            continue
        row = json.loads(line)
        key = bare(row["w"])
        record = out.setdefault(key, {"w": key, "pl": False, "du": False, "g": ""})
        record["pl"] = record["pl"] or bool(row["pl"])
        record["du"] = record["du"] or bool(row["du"])
        if not record["g"] and row.get("g"):
            record["g"] = row["g"]
    return out


def load_freq(path: Path) -> dict[str, int]:
    ranks: dict[str, int] = {}
    with open(path, encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            word = line.split()[0] if line.strip() else ""
            if word and word not in ranks:
                ranks[word] = index + 1
    return ranks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freq", required=True, help="frequency list, one word per line")
    parser.add_argument("--out", default="gaps.json", help="where to write the gap list")
    parser.add_argument("--limit", type=int, default=0, help="keep only the top N gaps")
    args = parser.parse_args()

    lexicon = load_lexicon()
    ranks = load_freq(Path(args.freq))

    missing = [r for r in lexicon.values() if not r["pl"]]
    ranked = sorted(missing, key=lambda r: ranks.get(r["w"], 10**9))
    in_freq = [r for r in ranked if r["w"] in ranks]
    unknown = [w for w in ranks if w not in lexicon]

    gaps = [
        {"w": r["w"], "rank": ranks[r["w"]], "g": r["g"], "du": r["du"]}
        for r in in_freq
    ]
    if args.limit:
        gaps = gaps[: args.limit]

    Path(args.out).write_text(json.dumps(gaps, ensure_ascii=False, indent=0), encoding="utf-8")

    print(f"lexicon lemmas        {len(lexicon):>7,}")
    print(f"  with a plural       {sum(1 for r in lexicon.values() if r['pl']):>7,}")
    print(f"  without a plural    {len(missing):>7,}")
    print(f"  ...of those, in the frequency list {len(in_freq):>7,}")
    print(f"frequency words not in the lexicon   {len(unknown):>7,}")
    print(f"written               {len(gaps):>7,} -> {args.out}")
    print()
    print("top 25 gaps:")
    for gap in gaps[:25]:
        print(f"  {gap['rank']:>5}  {gap['w']:<12} {gap['g'][:52]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
