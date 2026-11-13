"""Generate the data file for the plural entry page.

Two lists come out of this:

``gaps``    lexicon lemmas with no plural recorded, most frequent first
``verify``  the most frequent entries that do have a plural, so the data
            itself can be spot-checked

Usage::

    python tools/make_entry_data.py --freq ar_50k.txt \\
        --out /home/ubuntu/portfolio/nass-review/plurals/data.js
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


def load_rows() -> list[dict[str, Any]]:
    raw = gzip.decompress(DATA.read_bytes()).decode("utf-8")
    return [json.loads(line) for line in raw.splitlines() if line]


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
    parser.add_argument("--freq", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--verify", type=int, default=400, help="how many entries to spot-check")
    args = parser.parse_args()

    rows = load_rows()
    ranks = load_freq(Path(args.freq))

    by_lemma: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_lemma.setdefault(bare(row["w"]), []).append(row)

    gaps = []
    verify = []
    for lemma, group in by_lemma.items():
        rank = ranks.get(lemma)
        if rank is None:
            continue
        has_plural = any(row["pl"] for row in group)
        gloss = next((row["g"] for row in group if row["g"]), "")
        if has_plural:
            verify.append(
                {
                    "w": lemma,
                    "rank": rank,
                    "g": gloss,
                    "pl": [bare(f["f"]) for row in group for f in row["pl"]],
                    "du": [bare(f["f"]) for row in group for f in row["du"]],
                }
            )
        else:
            gaps.append({"w": lemma, "rank": rank, "g": gloss})

    gaps.sort(key=lambda r: r["rank"])
    verify.sort(key=lambda r: r["rank"])
    verify = verify[: args.verify]

    payload = {"gaps": gaps, "verify": verify}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "window.NASS_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(f"gaps   {len(gaps):>5}")
    print(f"verify {len(verify):>5}")
    print(f"written {out} ({out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
