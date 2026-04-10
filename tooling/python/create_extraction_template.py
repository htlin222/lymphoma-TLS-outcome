#!/usr/bin/env python3
"""Create blank extraction CSV template from data dictionary and PDF JSONL."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from extraction_utils import load_field_names_from_dict


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create extraction template CSV with one row per study"
    )
    parser.add_argument(
        "--pdf-jsonl", required=True, help="PDF texts JSONL from extract_pdf_text.py"
    )
    parser.add_argument("--data-dict", required=True, help="Data dictionary markdown")
    parser.add_argument("--out-csv", required=True, help="Output template CSV")
    args = parser.parse_args()

    pdf_jsonl = Path(args.pdf_jsonl)
    dd_path = Path(args.data_dict)
    out_csv = Path(args.out_csv)

    if not pdf_jsonl.exists():
        raise SystemExit(f"PDF JSONL not found: {pdf_jsonl}")
    if not dd_path.exists():
        raise SystemExit(f"Data dictionary not found: {dd_path}")

    fields = load_field_names_from_dict(dd_path)
    if not fields:
        raise SystemExit("No fields found in data dictionary")

    # Read study IDs from JSONL
    studies: list[str] = []
    with pdf_jsonl.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rec = json.loads(line)
                if rec.get("error") is None:
                    studies.append(rec.get("record_id", ""))

    # Write blank template
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for study_id in studies:
            row = {f: "" for f in fields}
            if "study_id" in fields:
                row["study_id"] = study_id
            writer.writerow(row)

    print(f"Created template: {out_csv}")
    print(f"  {len(studies)} studies, {len(fields)} fields")


if __name__ == "__main__":
    main()
