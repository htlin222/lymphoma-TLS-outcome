#!/usr/bin/env python3
"""Map web-searched study data to extraction columns with confidence scores."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from extraction_utils import load_field_names_from_dict

# Deterministic mapping from web data keys to extraction fields.
# Format: extraction_field -> (source, key_path, confidence)
# source: "pubmed" or "ctgov"
FIELD_MAP: list[tuple[str, str, str, float]] = [
    # (extraction_field, source, key, confidence)
    ("study_id", "pubmed", "first_author", 0.6),
    ("first_author", "pubmed", "first_author", 0.95),
    ("journal", "pubmed", "journal", 0.95),
    ("publication_year", "pubmed", "publication_year", 0.95),
    ("doi", "pubmed", "doi", 0.99),
    ("pmid", "pubmed", "pmid", 0.99),
    ("nct_number", "ctgov", "nct_number", 0.99),
    ("trial_name", "ctgov", "brief_title", 0.7),
]


def _get_nested(data: dict, key: str) -> str:
    """Get a value from a dict, returning empty string if missing."""
    val = data.get(key)
    if val is None:
        return ""
    if isinstance(val, (list, dict)):
        return json.dumps(val, ensure_ascii=False)
    return str(val).strip()


def map_study(web_record: dict, all_fields: list[str]) -> dict[str, str]:
    """Map a single web record to extraction fields with confidence."""
    pubmed = web_record.get("pubmed", {})
    ctgov = web_record.get("ctgov", {})
    sources = {"pubmed": pubmed, "ctgov": ctgov}

    row: dict[str, str] = {}
    confidences: dict[str, float] = {}

    for field in all_fields:
        row[field] = ""
        confidences[field] = 0.0

    # Apply deterministic mappings
    for ext_field, source, key, conf in FIELD_MAP:
        if ext_field not in row:
            continue
        src_data = sources.get(source, {})
        val = _get_nested(src_data, key)
        if val and "error" not in src_data:
            row[ext_field] = val
            confidences[ext_field] = conf

    # Special: study_id from first_author + year
    if not row.get("study_id"):
        author = _get_nested(pubmed, "first_author").split()[0] if pubmed else ""
        year = _get_nested(pubmed, "publication_year")
        if author and year:
            row["study_id"] = f"{author}{year}"
            confidences["study_id"] = 0.6

    # CTgov enrollment -> n_randomized_total
    enrollment = ctgov.get("enrollment_count")
    if enrollment is not None and "n_randomized_total" in row:
        row["n_randomized_total"] = str(enrollment)
        confidences["n_randomized_total"] = 0.5  # enrollment != randomized

    # record_id passthrough
    if "record_id" in row:
        row["record_id"] = web_record.get("record_id", "")
        confidences["record_id"] = 1.0

    # Add confidence columns
    for field in all_fields:
        row[f"{field}_confidence"] = str(confidences.get(field, 0.0))

    return row


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Map web data to extraction columns with confidence scores"
    )
    parser.add_argument("--web-data", required=True, help="Web search JSONL")
    parser.add_argument("--data-dict", required=True, help="Data dictionary markdown")
    parser.add_argument("--out-csv", required=True, help="Output extraction CSV")
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.7,
        help="Minimum confidence to include value (default: 0.7)",
    )
    args = parser.parse_args()

    web_path = Path(args.web_data)
    dd_path = Path(args.data_dict)
    out_csv = Path(args.out_csv)

    if not web_path.exists():
        raise SystemExit(f"Web data not found: {web_path}")
    if not dd_path.exists():
        raise SystemExit(f"Data dictionary not found: {dd_path}")

    all_fields = load_field_names_from_dict(dd_path)
    if not all_fields:
        raise SystemExit("No fields found in data dictionary")

    # Read web data
    web_records: list[dict] = []
    with web_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                web_records.append(json.loads(line))

    if not web_records:
        raise SystemExit("Web data JSONL is empty")

    # Map each study
    rows: list[dict[str, str]] = []
    for rec in web_records:
        rows.append(map_study(rec, all_fields))

    # Build fieldnames: extraction fields + confidence columns
    conf_fields = [f"{f}_confidence" for f in all_fields]
    fieldnames = all_fields + conf_fields

    out_csv.parent.mkdir(parents=True, exist_ok=True)

    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    # Stats
    total_cells = len(rows) * len(all_fields)
    filled = sum(
        1
        for r in rows
        for f in all_fields
        if r.get(f, "").strip()
        and float(r.get(f"{f}_confidence", "0")) >= args.confidence_threshold
    )
    pct = (filled / total_cells * 100) if total_cells else 0

    print(f"Mapped {len(rows)} studies to {len(all_fields)} fields")
    print(
        f"  High-confidence cells (>={args.confidence_threshold}): {filled}/{total_cells} ({pct:.1f}%)"
    )
    print(f"  Output: {out_csv}")


if __name__ == "__main__":
    main()
