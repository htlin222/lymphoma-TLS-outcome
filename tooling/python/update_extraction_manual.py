#!/usr/bin/env python3
"""Merge LLM-extracted data with manual corrections (manual wins)."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge LLM extraction with manual corrections"
    )
    parser.add_argument("--llm-jsonl", required=True, help="LLM extracted JSONL")
    parser.add_argument("--manual-csv", required=True, help="Manual corrections CSV")
    parser.add_argument("--out-csv", required=True, help="Output merged CSV")
    args = parser.parse_args()

    llm_path = Path(args.llm_jsonl)
    manual_path = Path(args.manual_csv)
    out_path = Path(args.out_csv)

    if not llm_path.exists():
        raise SystemExit(f"LLM JSONL not found: {llm_path}")
    if not manual_path.exists():
        raise SystemExit(f"Manual CSV not found: {manual_path}")

    # Load LLM data keyed by study_id
    llm_data: dict[str, dict[str, str]] = {}
    with llm_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("status") != "success" or not rec.get("extracted_data"):
                continue
            extracted = rec["extracted_data"]
            sid = str(extracted.get("study_id", extracted.get("record_id", "")))
            row: dict[str, str] = {}
            for k, v in extracted.items():
                if v is None:
                    row[k] = ""
                elif isinstance(v, (list, dict)):
                    row[k] = json.dumps(v, ensure_ascii=False)
                elif isinstance(v, bool):
                    row[k] = "TRUE" if v else "FALSE"
                else:
                    row[k] = str(v)
            llm_data[sid] = row

    # Load manual corrections
    manual_rows: list[dict[str, str]] = []
    with manual_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        manual_fields = list(reader.fieldnames or [])
        manual_rows = list(reader)

    # Collect all field names (union)
    all_fields_set: set[str] = set()
    for row in llm_data.values():
        all_fields_set.update(row.keys())
    all_fields_set.update(manual_fields)
    # Preserve manual CSV field order, then add any extras from LLM
    all_fields = list(manual_fields)
    for f in sorted(all_fields_set - set(manual_fields)):
        all_fields.append(f)

    # Merge: manual values override LLM where non-empty
    merged: list[dict[str, str]] = []
    for manual_row in manual_rows:
        sid = manual_row.get("study_id", "").strip()
        base = dict(llm_data.get(sid, {}))
        for field in all_fields:
            manual_val = (manual_row.get(field) or "").strip()
            if manual_val:
                base[field] = manual_val
            elif field not in base:
                base[field] = ""
        merged.append(base)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=all_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(merged)

    print(f"Merged {len(merged)} studies")
    print(f"  LLM records: {len(llm_data)}")
    print(f"  Manual rows: {len(manual_rows)}")
    print(f"  Output: {out_path}")


if __name__ == "__main__":
    main()
