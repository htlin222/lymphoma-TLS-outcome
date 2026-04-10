#!/usr/bin/env python3
"""Build a study characteristics table from extraction.csv."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


START = "<!-- STUDY_CHARACTERISTICS_START -->"
END = "<!-- STUDY_CHARACTERISTICS_END -->"


def read_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing extraction CSV: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [{k: (v or "").strip() for k, v in row.items()} for row in reader]


def insert_block(text: str, block: str, marker: str) -> str:
    if START in text and END in text:
        prefix = text.split(START)[0]
        suffix = text.split(END)[1]
        return prefix + START + "\n" + block + "\n" + END + suffix
    if marker in text:
        parts = text.split(marker)
        head = parts[0] + marker
        tail = marker.join(parts[1:])
        return head + "\n\n" + START + "\n" + block + "\n" + END + "\n" + tail
    return text.rstrip() + "\n\n" + START + "\n" + block + "\n" + END + "\n"


def build_table(rows: List[Dict[str, str]]) -> Tuple[List[str], List[Dict[str, str]]]:
    by_study: Dict[str, Dict[str, object]] = {}

    for row in rows:
        study_id = row.get("study_id", "")
        if not study_id:
            continue
        entry = by_study.setdefault(
            study_id,
            {
                "study_id": study_id,
                "record_id": "",
                "year": "",
                "design": "",
                "country": "",
                "outcomes": set(),
                "outcome_types": set(),
                "timepoints": set(),
                "arms": {},
            },
        )
        record_id = row.get("record_id", "")
        if record_id and not entry["record_id"]:
            entry["record_id"] = record_id
        for key in ("year", "design", "country"):
            if key in row and row.get(key) and not entry[key]:
                entry[key] = row.get(key)
        outcome = row.get("outcome_name", "") or row.get("outcome", "")
        if outcome:
            entry["outcomes"].add(outcome)
        outcome_type = row.get("outcome_type", "")
        if outcome_type:
            entry["outcome_types"].add(outcome_type)
        timepoint = row.get("timepoint", "")
        if timepoint:
            entry["timepoints"].add(timepoint)

        arm = row.get("arm_label", "")
        n_val = row.get("n", "")
        if arm:
            try:
                n_num = int(float(n_val)) if n_val else None
            except ValueError:
                n_num = None
            arms = entry["arms"]
            if arm not in arms or (n_num is not None and (arms[arm] or 0) < n_num):
                arms[arm] = n_num

    out_rows = []
    for study_id, entry in by_study.items():
        arms = entry["arms"]
        total_n = sum(v for v in arms.values() if isinstance(v, int))
        out_rows.append(
            {
                "study_id": study_id,
                "record_id": entry["record_id"],
                "year": entry["year"],
                "design": entry["design"],
                "country": entry["country"],
                "n_arms": str(len(arms)) if arms else "",
                "total_n": str(total_n) if total_n else "",
                "outcomes": "; ".join(sorted(entry["outcomes"])),
                "outcome_types": "; ".join(sorted(entry["outcome_types"])),
                "timepoints": "; ".join(sorted(entry["timepoints"])),
            }
        )

    headers = [
        "study_id",
        "record_id",
        "year",
        "design",
        "country",
        "n_arms",
        "total_n",
        "outcomes",
        "outcome_types",
        "timepoints",
    ]
    return headers, out_rows


def build_markdown(headers: List[str], rows: List[Dict[str, str]]) -> str:
    lines = [
        "### Study Characteristics",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row.get(h, "") for h in headers) + " |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build study characteristics table.")
    parser.add_argument("--extraction", default="05_extraction/extraction.csv", help="Extraction CSV")
    parser.add_argument("--out-csv", default="07_manuscript/study_characteristics.csv", help="Output CSV")
    parser.add_argument("--out-md", default="07_manuscript/study_characteristics.md", help="Output Markdown")
    parser.add_argument("--results", default="07_manuscript/03_results.qmd", help="Results QMD to insert")
    args = parser.parse_args()

    extraction_path = Path(args.extraction)
    rows = read_rows(extraction_path)
    headers, out_rows = build_table(rows)

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(out_rows)

    markdown = build_markdown(headers, out_rows)
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(markdown + "\n")

    results_path = Path(args.results)
    if results_path.exists():
        updated = insert_block(results_path.read_text(), markdown, "## Study Characteristics")
        results_path.write_text(updated + "\n")


if __name__ == "__main__":
    main()
