#!/usr/bin/env python3
"""Deduplicate BibTeX records by DOI, PMID, or normalized title."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, Tuple


def norm_doi(value: str) -> str:
    if not value:
        return ""
    value = value.strip().lower()
    value = value.replace("https://doi.org/", "").replace("http://doi.org/", "")
    return value


def norm_title(value: str) -> str:
    if not value:
        return ""
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def score_entry(entry: Dict[str, str]) -> Tuple[int, int]:
    fields = [v for v in entry.values() if isinstance(v, str) and v.strip()]
    has_doi = 1 if entry.get("doi") else 0
    return (len(fields), has_doi)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deduplicate BibTeX records.")
    parser.add_argument("--in-bib", required=True, help="Input .bib file")
    parser.add_argument("--out-bib", required=True, help="Output .bib file")
    parser.add_argument("--out-log", required=True, help="Output log file")
    args = parser.parse_args()

    from bibtexparser import loads
    from bibtexparser.bwriter import BibTexWriter

    bib_text = Path(args.in_bib).read_text()
    bib_db = loads(bib_text)

    deduped: Dict[str, Dict[str, str]] = {}
    collisions = 0

    for entry in bib_db.entries:
        doi = norm_doi(entry.get("doi", ""))
        pmid = entry.get("pmid", "").strip()
        title = norm_title(entry.get("title", ""))

        key = doi or pmid or title
        if not key:
            key = entry.get("ID")

        if key in deduped:
            collisions += 1
            if score_entry(entry) > score_entry(deduped[key]):
                deduped[key] = entry
        else:
            deduped[key] = entry

    writer = BibTexWriter()
    writer.indent = "  "
    writer.order_entries_by = None

    output_db = bib_db
    output_db.entries = list(deduped.values())
    Path(args.out_bib).write_text(writer.write(output_db))

    log = [
        f"input_records: {len(bib_db.entries)}",
        f"deduped_records: {len(output_db.entries)}",
        f"collisions: {collisions}",
    ]
    Path(args.out_log).write_text("\n".join(log) + "\n")


if __name__ == "__main__":
    main()
