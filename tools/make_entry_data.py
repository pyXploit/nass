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
import subprocess
from contextlib import ExitStack
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
    rows: list[dict[str, Any]] = []
    for name in ("nouns.jsonl.gz", "arramooz.jsonl.gz"):
        raw = gzip.decompress((DATA.parent / name).read_bytes()).decode("utf-8")
        rows.extend(json.loads(line) for line in raw.splitlines() if line)
    return rows


def load_freq(path: Path) -> dict[str, int]:
    ranks: dict[str, int] = {}
    with open(path, encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            word = line.split()[0] if line.strip() else ""
            if word and word not in ranks:
                ranks[word] = index + 1
    return ranks


def clean_form(text: str) -> bool:
    """A form worth suggesting: Arabic script, one word, no article."""
    if not text or text.startswith("ال"):
        return False
    return all("\u0600" <= ch <= "\u06FF" for ch in text)


def loose_plurals(path: Path, wanted: set[str]) -> dict[str, list[str]]:
    """Plural forms Wiktionary records outside the indefinite-nominative cell.

    These are not good enough to ship unconfirmed, but they are a real source
    and make a far better prefill than an empty box.
    """
    found: dict[str, list[str]] = {}
    with ExitStack() as stack:
        if str(path).endswith(".zst"):
            proc = stack.enter_context(
                subprocess.Popen(
                    ["zstd", "-dc", str(path)],
                    stdout=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                )
            )
            handle = proc.stdout
        else:
            handle = stack.enter_context(open(path, encoding="utf-8"))
        assert handle is not None
        for line in handle:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("pos") not in ("noun", "adj", "name"):
                continue
            word = bare(entry.get("word") or "")
            if word not in wanted:
                continue
            forms = []
            for form in entry.get("forms") or []:
                tags = set(form.get("tags") or ())
                if "plural" not in tags or tags & {"definite", "construct"}:
                    continue
                text = bare(form.get("form") or "")
                if clean_form(text) and text not in forms:
                    forms.append(text)
            if forms:
                found.setdefault(word, []).extend(f for f in forms if f not in found.get(word, []))
    return found


def rule_suggestion(word: str) -> str:
    """A sound feminine plural, offered only where the shape makes it likely."""
    if word.endswith("ة") and len(word) > 3:
        return word[:-1] + "ات"
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freq", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--verify", type=int, default=400, help="how many entries to spot-check")
    parser.add_argument("--raw", help="the upstream JSONL, used to prefill suggestions")
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
        # A row flagged ``none`` was checked against the dictionaries and has no
        # plural of its own, so it is not a gap any more.
        checked_none = any(row.get("none") for row in group)
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
        elif not checked_none:
            gaps.append({"w": lemma, "rank": rank, "g": gloss})

    gaps.sort(key=lambda r: r["rank"])
    verify.sort(key=lambda r: r["rank"])
    verify = verify[: args.verify]

    if args.raw:
        sourced = loose_plurals(Path(args.raw), {gap["w"] for gap in gaps})
        for gap in gaps:
            # A form identical to the lemma means the entry is itself a plural
            # (روس, يهود, ألمان); suggesting it back would be circular.
            forms = [f for f in sourced.get(gap["w"], []) if f != gap["w"]]
            if forms:
                gap["s"] = "، ".join(forms[:3])
                gap["st"] = "source"
            else:
                guess = rule_suggestion(gap["w"])
                if guess:
                    gap["s"] = guess
                    gap["st"] = "rule"

    payload = {"gaps": gaps, "verify": verify}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "window.NASS_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(f"gaps   {len(gaps):>5}  ({sum(1 for g in gaps if g.get('s'))} prefilled)")
    print(f"verify {len(verify):>5}")
    print(f"written {out} ({out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
