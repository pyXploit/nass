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
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, TextIO

OUT = Path(__file__).resolve().parent.parent / "src" / "nass" / "data" / "nouns.jsonl.gz"
EXTRA_OUT = OUT.parent / "arramooz.jsonl.gz"

KEEP_POS = ("noun", "adj", "name")
DIACRITICS = frozenset(
    [chr(c) for c in range(0x064B, 0x0653)] + ["\u0670", "\u0640", "\u0653", "\u0654", "\u0655"]
)
DEMOTE = frozenset({"obsolete", "rare", "archaic", "dialectal"})


def bare(text: str) -> str:
    """Strip Arabic diacritics and tatweel."""
    return "".join(ch for ch in text if ch not in DIACRITICS)


def _dedupe(forms: list[dict[str, str]]) -> list[dict[str, str]]:
    """One entry per bare spelling, keeping the diacritized variant."""
    out: list[dict[str, str]] = []
    index: dict[str, int] = {}
    for form in forms:
        key = bare(form["f"])
        if key in index:
            if len(form["f"]) > len(out[index[key]]["f"]):
                out[index[key]]["f"] = form["f"]
            continue
        index[key] = len(out)
        out.append(form)
    return out


def pick(forms: list[dict[str, Any]], kind: str) -> list[dict[str, str]]:
    """Return the citation forms (indefinite, nominative) of ``kind``.

    The strict pass keeps only forms tagged nominative and not definite or
    construct. When an entry has no such form at all, a second pass accepts
    untagged rows: Wiktionary frequently leaves the case off a plural row, and
    dropping those loses the only attested plural the entry has. The fallback
    still refuses anything marked definite, construct, accusative or genitive,
    anything containing a space (a construct phrase), and anything carrying the
    definite article.

    The fallback never runs for an entry that already has a tagged form, so a
    lemma that was already in the lexicon keeps exactly the plural it had.
    """
    strict: list[dict[str, str]] = []
    loose: list[dict[str, str]] = []
    for form in forms:
        tags = set(form.get("tags") or ())
        if kind not in tags:
            continue
        if tags & {"definite", "construct"}:
            continue
        text = form.get("form")
        if not text or not ARABIC.search(text):
            continue
        kind_tag = "broken" if "broken-form" in tags else "sound" if "sound-form" in tags else ""
        entry = {"f": text, "t": kind_tag}
        if "nominative" in tags:
            strict.append(entry)
        elif (
            not tags & {"accusative", "genitive"}
            and " " not in text
            and not text.startswith("\u0627\u0644")
        ):
            loose.append(entry)
    return strict if strict else _dedupe(loose)


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


ARABIC = re.compile(r"[\u0600-\u06ff]")


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
        word = entry.get("word") or ""
        # Judeo-Arabic spellings are written in Hebrew script; they are not
        # Arabic lemmas and must not enter an Arabic lexicon.
        if not ARABIC.search(word):
            stats["dropped_non_arabic_script"] += 1
            continue
        forms = entry.get("forms") or []
        raw_plurals = pick(forms, "plural")
        raw_duals = pick(forms, "dual")
        if (
            not raw_plurals
            and not raw_duals
            # Keep the lemma when the entry does carry a plural or dual row that
            # the filters rejected (a bare "-", a Latin transliteration, a
            # definite form): the word is still known, it just has no usable
            # form to return.
            and not any({"plural", "dual"} & set(f.get("tags") or ()) for f in forms)
        ):
            continue
        # A plural identical to its own singular is not a plural: Wiktionary
        # lists lexicalised plurals (آثار, علوم) as nouns in their own right.
        # The lemma is kept, with the circular form removed.
        bare_word = bare(word)
        plurals = [f for f in raw_plurals if bare(f["f"]) != bare_word]
        duals = [f for f in raw_duals if bare(f["f"]) != bare_word]
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
                "w": word,
                "pos": entry["pos"],
                "n": len(senses),
                "d": 1 if tags & DEMOTE else 0,
                "pl": plurals,
                "du": duals,
                "g": gloss_of(senses),
            }
        )
    return rows, stats


def merge_extra(
    rows: list[dict[str, Any]], path: Path, decided: set[str]
) -> tuple[list[dict[str, Any]], int, int]:
    """Select the rows a second source may contribute, lemma by lemma.

    The second source is only trusted where the first one is silent:

    * a lemma the curated layer already decided is left alone;
    * a lemma that is itself a plural of another word is skipped, because the
      second source sometimes lists a plural as if it were a singular;
    * a lemma that already has a plural keeps it, so two senses of one spelling
      are never mixed;
    * a lemma with no plural at all gets the second source's forms.

    The selected rows are written to their own file rather than merged into the
    first source's: the two carry different licences and must stay separate.
    """
    if not path.exists():
        return [], 0, 0
    extra = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    primary: dict[str, dict[str, Any]] = {}
    for row in rows:
        primary.setdefault(bare(row["w"]), row)
    known_plurals = {bare(form["f"]) for row in rows for form in row["pl"]}
    kept: list[dict[str, Any]] = []
    skipped = 0
    for row in extra:
        key = bare(row["w"])
        if key in decided or key in known_plurals:
            skipped += 1
            continue
        target = primary.get(key)
        if target is not None and target["pl"]:
            skipped += 1
            continue
        kept.append(row)
    return kept, len(kept), skipped


def apply_overrides(rows: list[dict[str, Any]], path: Path) -> int:
    """Apply hand-entered rows, replacing only the primary row of a lemma.

    Homograph rows are kept: confirming the plural of كتاب must not delete the
    second entry, which carries a different plural.
    """
    if not path.exists():
        return 0
    overrides = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not overrides:
        return 0
    primary: dict[str, int] = {}
    for position, row in enumerate(rows):
        primary.setdefault(bare(row["w"]), position)
    for override in overrides:
        position = primary.get(bare(override["w"]))
        if position is None:
            primary[bare(override["w"])] = len(rows)
            rows.append(override)
        else:
            merged = dict(rows[position])
            merged.update(override)
            merged["g"] = override.get("g") or rows[position].get("g", "")
            merged["n"] = max(int(override.get("n") or 1), int(rows[position].get("n") or 1))
            rows[position] = merged
    return len(overrides)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSONL path, or - for stdin")
    parser.add_argument(
        "--overrides",
        default=str(OUT.parent / "overrides.jsonl"),
        help="hand-entered rows that win over the extracted ones",
    )
    parser.add_argument(
        "--extra",
        default="",
        help="a second source of rows, merged lemma by lemma",
    )
    args = parser.parse_args()

    if args.input == "-":
        rows, stats = collect(sys.stdin)
    elif args.input.endswith(".zst"):
        with subprocess.Popen(
            ["zstd", "-dc", args.input], stdout=subprocess.PIPE, text=True, encoding="utf-8"
        ) as handle:
            assert handle.stdout is not None
            rows, stats = collect(handle.stdout)
    else:
        with open(args.input, encoding="utf-8") as handle:
            rows, stats = collect(handle)

    rows.sort(key=lambda r: (bare(r["w"]), -r["n"], r["d"]))
    # The curated layer goes on first, so a second source can still add a form
    # to a lemma that was marked "no plural": an attestation beats a judgement.
    applied = apply_overrides(rows, Path(args.overrides))
    extra_rows = extra_skipped = 0
    if args.extra:
        decided = {bare(row["w"]) for row in rows if row.get("none") or row["pl"]}
        kept, extra_rows, extra_skipped = merge_extra(rows, Path(args.extra), decided)
        payload = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept).encode()
        with gzip.GzipFile(EXTRA_OUT, "wb", compresslevel=9, mtime=0) as handle:
            handle.write(payload)
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
    print(f"overrides applied {applied:>8,}")
    print(f"extra lemmas      {extra_rows:>8,}")
    print(f"extra skipped     {extra_skipped:>8,}")
    print(f"unique lemmas     {len(lemmas):>8,}")
    print(f"with plural       {sum(1 for r in rows if r['pl']):>8,}")
    print(f"with dual         {sum(1 for r in rows if r['du']):>8,}")
    print(f"raw               {len(payload) / 1024:>8,.0f} KB")
    print(f"gzipped           {OUT.stat().st_size / 1024:>8,.0f} KB")
    print(f"sha256            {hashlib.sha256(OUT.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
