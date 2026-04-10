#!/usr/bin/env python3
"""Initialize a GRADE summary table from extraction data."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def read_outcomes(csv_path: Path) -> list[tuple[str, str]]:
    if not csv_path.exists():
        return []

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []

        outcome_id_key = None
        for key in ("outcome_id", "outcome", "outcome_name"):
            if key in headers:
                outcome_id_key = key
                break

        name_key = None
        for key in ("outcome_name", "name", "outcome_label"):
            if key in headers:
                name_key = key
                break

        if not outcome_id_key:
            return []

        outcomes = []
        for row in reader:
            outcome_id = row.get(outcome_id_key, "").strip()
            if not outcome_id:
                continue
            outcome_name = row.get(name_key, "").strip() if name_key else ""
            outcomes.append((outcome_id, outcome_name))

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for outcome_id, outcome_name in outcomes:
        if outcome_id in seen:
            continue
        seen.add(outcome_id)
        deduped.append((outcome_id, outcome_name))
    return deduped


def write_csv(out_path: Path, rows: list[tuple[str, str]]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "outcome_id",
        "outcome_name",
        "risk_of_bias",
        "inconsistency",
        "indirectness",
        "imprecision",
        "publication_bias",
        "certainty",
        "notes",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        if rows:
            for outcome_id, outcome_name in rows:
                writer.writerow([outcome_id, outcome_name, "", "", "", "", "", "", ""])
        else:
            writer.writerow(["<outcome_id>", "<outcome_name>", "", "", "", "", "", "", ""])


def write_markdown(out_path: Path, rows: list[tuple[str, str]]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "Outcome ID",
        "Outcome Name",
        "Risk of Bias",
        "Inconsistency",
        "Indirectness",
        "Imprecision",
        "Publication Bias",
        "Certainty",
        "Notes",
    ]
    lines = ["# GRADE Summary Table", ""]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    if rows:
        for outcome_id, outcome_name in rows:
            row = [
                outcome_id,
                outcome_name,
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
            lines.append("| " + " | ".join(row) + " |")
    else:
        lines.append("| <outcome_id> | <outcome_name> |  |  |  |  |  |  |  |")

    out_path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize GRADE summary tables.")
    parser.add_argument("--extraction", required=True, help="Path to extraction CSV")
    parser.add_argument("--out-csv", required=True, help="Output CSV path")
    parser.add_argument("--out-md", required=True, help="Output markdown path")
    args = parser.parse_args()

    outcomes = read_outcomes(Path(args.extraction))
    write_csv(Path(args.out_csv), outcomes)
    write_markdown(Path(args.out_md), outcomes)


if __name__ == "__main__":
    main()
