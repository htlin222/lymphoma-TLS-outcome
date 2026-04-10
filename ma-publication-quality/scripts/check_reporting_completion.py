#!/usr/bin/env python3
"""Check PRISMA/MOOSE checklists for completion (no empty rows)."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_table(path: Path) -> list[list[str]]:
    lines = [line for line in path.read_text().splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        return []
    rows = []
    for line in lines[2:]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows


def find_incomplete(rows: list[list[str]], required_cols: list[int]) -> list[int]:
    missing = []
    for idx, row in enumerate(rows, start=1):
        if any(idx_col >= len(row) or not row[idx_col] for idx_col in required_cols):
            missing.append(idx)
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(description="Check reporting checklist completion.")
    parser.add_argument("--prisma", default="07_manuscript/prisma_checklist.md")
    parser.add_argument("--moose", default=None, help="Optional MOOSE checklist path")
    parser.add_argument("--out", default="09_qa/reporting_checklist_audit.md")
    args = parser.parse_args()

    issues = []

    prisma_path = Path(args.prisma)
    if prisma_path.exists():
        rows = parse_table(prisma_path)
        missing = find_incomplete(rows, [1, 2, 3])
        if missing:
            issues.append(f"PRISMA incomplete rows: {', '.join(map(str, missing))}")
    else:
        issues.append(f"Missing PRISMA checklist: {prisma_path}")

    if args.moose:
        moose_path = Path(args.moose)
        if moose_path.exists():
            rows = parse_table(moose_path)
            missing = find_incomplete(rows, [1, 2, 3])
            if missing:
                issues.append(f"MOOSE incomplete rows: {', '.join(map(str, missing))}")
        else:
            issues.append(f"Missing MOOSE checklist: {moose_path}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Reporting Checklist Audit", ""]
    if issues:
        lines.append("## Issues")
        for issue in issues:
            lines.append(f"- {issue}")
    else:
        lines.append("- All reporting checklists complete.")

    out_path.write_text("\n".join(lines) + "\n")

    if issues:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
