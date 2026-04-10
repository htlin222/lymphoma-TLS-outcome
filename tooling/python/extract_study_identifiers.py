#!/usr/bin/env python3
"""Extract study identifiers from screening CSV for web-based extraction."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

MANIFEST_FIELDS = ["record_id", "title", "authors", "year", "doi", "pmid"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Filter screening CSV and write web extraction manifest"
    )
    parser.add_argument("--in-csv", required=True, help="Input screening decisions CSV")
    parser.add_argument("--filter-column", required=True, help="Column to filter on")
    parser.add_argument(
        "--filter-value", required=True, help="Value to keep (case-insensitive)"
    )
    parser.add_argument("--out-csv", required=True, help="Output manifest CSV")
    args = parser.parse_args()

    in_path = Path(args.in_csv)
    out_path = Path(args.out_csv)

    if not in_path.exists():
        raise SystemExit(f"Input CSV not found: {in_path}")

    filter_val = args.filter_value.strip().lower()
    rows: list[dict[str, str]] = []

    with in_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if args.filter_column not in (reader.fieldnames or []):
            raise SystemExit(
                f"Column '{args.filter_column}' not found. "
                f"Available: {reader.fieldnames}"
            )
        for row in reader:
            if (row.get(args.filter_column) or "").strip().lower() == filter_val:
                rows.append(
                    {field: (row.get(field) or "").strip() for field in MANIFEST_FIELDS}
                )

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Extracted {len(rows)} records where {args.filter_column}={args.filter_value}"
    )
    print(f"Output: {out_path}")


if __name__ == "__main__":
    main()
