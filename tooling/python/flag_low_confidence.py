#!/usr/bin/env python3
"""Flag low-confidence extraction fields for manual review."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Flag extraction fields below confidence threshold"
    )
    parser.add_argument(
        "--extraction", required=True, help="Extraction CSV with confidence columns"
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.7,
        help="Threshold below which to flag (default: 0.7)",
    )
    parser.add_argument("--out-md", required=True, help="Output markdown checklist")
    args = parser.parse_args()

    csv_path = Path(args.extraction)
    out_path = Path(args.out_md)

    if not csv_path.exists():
        raise SystemExit(f"Extraction CSV not found: {csv_path}")

    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        headers = list(reader.fieldnames or [])
        rows = list(reader)

    # Find confidence columns
    conf_cols = [h for h in headers if h.endswith("_confidence")]
    if not conf_cols:
        raise SystemExit("No *_confidence columns found — wrong input file?")

    # Scan for low-confidence fields
    flags: list[dict[str, str]] = []
    for row in rows:
        study_id = row.get("study_id", row.get("record_id", "unknown"))
        for conf_col in conf_cols:
            try:
                score = float(row.get(conf_col, "0"))
            except ValueError:
                score = 0.0
            if score < args.confidence_threshold:
                field = conf_col.removesuffix("_confidence")
                current_val = row.get(field, "")
                flags.append(
                    {
                        "study": study_id,
                        "field": field,
                        "confidence": f"{score:.2f}",
                        "current_value": current_val[:50] if current_val else "(empty)",
                    }
                )

    # Write markdown checklist
    lines = [
        "# Fields Needing Manual Verification",
        "",
        f"**Threshold**: {args.confidence_threshold}",
        f"**Studies**: {len(rows)}",
        f"**Fields flagged**: {len(flags)}",
        "",
    ]

    if not flags:
        lines.append("All fields meet the confidence threshold.")
    else:
        # Group by study
        by_study: dict[str, list[dict[str, str]]] = {}
        for f in flags:
            by_study.setdefault(f["study"], []).append(f)

        for study, items in by_study.items():
            lines.append(f"## {study}")
            lines.append("")
            for item in items:
                lines.append(
                    f"- [ ] **{item['field']}** "
                    f"(confidence: {item['confidence']}, "
                    f"current: {item['current_value']})"
                )
            lines.append("")

    lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Flagged {len(flags)} fields below {args.confidence_threshold} threshold")
    print(f"  Across {len(rows)} studies")
    print(f"  Output: {out_path}")


if __name__ == "__main__":
    main()
