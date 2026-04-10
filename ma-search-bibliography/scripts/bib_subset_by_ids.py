#!/usr/bin/env python3
"""Extract BibTeX subset by matching record IDs from CSV.

This script reads a CSV file containing record IDs and extracts matching
entries from a BibTeX file. Useful for creating subsets after screening
or for preparing full-text retrieval lists.

Usage:
    uv run bib_subset_by_ids.py \\
      --in-csv decisions.csv \\
      --in-bib dedupe.bib \\
      --out-bib included.bib \\
      --id-column record_id
"""

import argparse
import csv
import sys
from pathlib import Path

import bibtexparser


def extract_record_ids(
    csv_path, id_column="record_id", filter_column=None, filter_value=None
):
    """Extract record IDs from CSV file.

    Args:
        csv_path: Path to CSV file
        id_column: Column name containing record IDs
        filter_column: Optional column to filter by
        filter_value: Optional value to filter for

    Returns:
        set: Set of record IDs
    """
    record_ids = set()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate columns exist
        if not reader.fieldnames:
            raise ValueError(f"CSV file {csv_path} is empty or has no header")

        if id_column not in reader.fieldnames:
            raise ValueError(
                f"Column '{id_column}' not found in CSV. "
                f"Available columns: {', '.join(reader.fieldnames)}"
            )

        if filter_column and filter_column not in reader.fieldnames:
            raise ValueError(
                f"Filter column '{filter_column}' not found in CSV. "
                f"Available columns: {', '.join(reader.fieldnames)}"
            )

        # Extract IDs
        for row in reader:
            record_id = row.get(id_column, "").strip()
            if not record_id:
                continue

            # Apply filter if specified
            if filter_column:
                if row.get(filter_column, "").strip() == filter_value:
                    record_ids.add(record_id)
            else:
                record_ids.add(record_id)

    return record_ids


def extract_bib_entries(bib_path, record_ids):
    """Extract BibTeX entries matching record IDs.

    Args:
        bib_path: Path to BibTeX file
        record_ids: Set of record IDs to extract

    Returns:
        bibtexparser.bibdatabase.BibDatabase: Filtered BibTeX database
    """
    # Load full BibTeX file
    with open(bib_path, "r", encoding="utf-8") as f:
        bib_database = bibtexparser.load(f)

    # Filter entries
    matched_entries = []
    for entry in bib_database.entries:
        if entry.get("ID") in record_ids:
            matched_entries.append(entry)

    # Create filtered database
    output_db = bibtexparser.bibdatabase.BibDatabase()
    output_db.entries = matched_entries

    return output_db, len(matched_entries)


def main():
    parser = argparse.ArgumentParser(
        description="Extract BibTeX subset by record IDs from CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--in-csv",
        required=True,
        type=Path,
        help="Input CSV file containing record IDs",
    )
    parser.add_argument(
        "--in-bib", required=True, type=Path, help="Input BibTeX file (full set)"
    )
    parser.add_argument(
        "--out-bib", required=True, type=Path, help="Output BibTeX file (subset)"
    )
    parser.add_argument(
        "--id-column",
        default="record_id",
        help="CSV column containing record IDs (default: record_id)",
    )
    parser.add_argument(
        "--filter-column",
        help="Optional: CSV column to filter by (e.g., 'final_decision')",
    )
    parser.add_argument(
        "--filter-value",
        help="Optional: Value to filter for (e.g., 'Include')",
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.in_csv.exists():
        print(f"❌ Error: Input CSV not found: {args.in_csv}", file=sys.stderr)
        sys.exit(1)

    if not args.in_bib.exists():
        print(f"❌ Error: Input BibTeX not found: {args.in_bib}", file=sys.stderr)
        sys.exit(1)

    if args.filter_column and not args.filter_value:
        print(
            "❌ Error: --filter-value required when --filter-column is specified",
            file=sys.stderr,
        )
        sys.exit(1)

    # Extract record IDs from CSV
    try:
        record_ids = extract_record_ids(
            args.in_csv,
            id_column=args.id_column,
            filter_column=args.filter_column,
            filter_value=args.filter_value,
        )
        print(f"✅ Found {len(record_ids)} record IDs in CSV")
        if args.filter_column:
            print(f"   (filtered by {args.filter_column} = '{args.filter_value}')")
    except ValueError as e:
        print(f"❌ Error reading CSV: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract BibTeX entries
    try:
        output_db, matched_count = extract_bib_entries(args.in_bib, record_ids)
        print(
            f"✅ Loaded {len(bibtexparser.load(open(args.in_bib, 'r')))} entries from BibTeX"
        )
        print(f"✅ Matched {matched_count} entries")
    except Exception as e:
        print(f"❌ Error reading BibTeX: {e}", file=sys.stderr)
        sys.exit(1)

    # Write output
    try:
        args.out_bib.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out_bib, "w", encoding="utf-8") as f:
            bibtexparser.dump(output_db, f)
        print(f"✅ Wrote {matched_count} entries to {args.out_bib}")
    except Exception as e:
        print(f"❌ Error writing output: {e}", file=sys.stderr)
        sys.exit(1)

    # Summary
    if matched_count < len(record_ids):
        missing = len(record_ids) - matched_count
        print(f"\n⚠️  Warning: {missing} record IDs from CSV not found in BibTeX")
        print(
            "   This is normal if records were manually added or came from other sources"
        )


if __name__ == "__main__":
    main()
