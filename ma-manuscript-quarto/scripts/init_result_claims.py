#!/usr/bin/env python3
"""Initialize a result-to-evidence claims table for manuscript writing."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import List


def list_files(path: Path, patterns: List[str]) -> List[Path]:
    files: List[Path] = []
    if not path.exists():
        return files
    for pattern in patterns:
        files.extend(path.glob(pattern))
    return sorted([f for f in files if f.is_file()])


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize result claims table.")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--out", default="07_manuscript/result_claims.csv", help="Output CSV path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    figures = list_files(root / "06_analysis" / "figures", ["*.png", "*.svg"])
    tables = list_files(root / "06_analysis" / "tables", ["*.html", "*.csv", "*.txt"])

    rows = []
    counter = 1
    for fig in figures:
        rows.append(
            {
                "claim_id": f"C{counter:02d}",
                "result_summary": "",
                "outcome": "",
                "effect_measure": "",
                "model": "",
                "effect_estimate": "",
                "ci": "",
                "p_value": "",
                "heterogeneity_i2": "",
                "direction": "",
                "figure_ref": f"../06_analysis/figures/{fig.name}",
                "table_ref": "",
                "data_source": "figure",
                "citation_keys": "",
                "notes": "",
            }
        )
        counter += 1

    for tbl in tables:
        rows.append(
            {
                "claim_id": f"C{counter:02d}",
                "result_summary": "",
                "outcome": "",
                "effect_measure": "",
                "model": "",
                "effect_estimate": "",
                "ci": "",
                "p_value": "",
                "heterogeneity_i2": "",
                "direction": "",
                "figure_ref": "",
                "table_ref": f"../06_analysis/tables/{tbl.name}",
                "data_source": "table",
                "citation_keys": "",
                "notes": "",
            }
        )
        counter += 1

    headers = [
        "claim_id",
        "result_summary",
        "outcome",
        "effect_measure",
        "model",
        "effect_estimate",
        "ci",
        "p_value",
        "heterogeneity_i2",
        "direction",
        "figure_ref",
        "table_ref",
        "data_source",
        "citation_keys",
        "notes",
    ]

    out_path = root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
