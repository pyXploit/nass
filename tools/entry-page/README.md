# Plural entry page

A small authoring page for filling gaps in the plural lexicon. It is deployed
to `https://codox.dpdns.org/nass-review/plurals/`; the files here are the
source of truth.

```bash
python tools/make_entry_data.py --freq ar_50k.txt --raw kaikki-ar.jsonl \
    --out /home/ubuntu/portfolio/nass-review/plurals/data.js
```

Then open the page, work through the lists, and press **Export JSON**. Feed the
download back in:

```bash
python tools/merge_overrides.py --input nass-overrides.json
python tools/build_data.py --input kaikki-ar.jsonl
```

`data.js` is generated and is not committed.

## Prefills

Gap entries arrive with a suggestion where one exists, marked in the UI:

- `source` — a plural Wiktionary records outside the indefinite-nominative
  cell. Real data, but from a less reliable cell, so it needs confirming.
- `rule` — a sound feminine plural derived from a word ending in ة. A guess,
  and labelled as one.

Nothing enters the lexicon until it is confirmed here.
