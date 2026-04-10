#!/usr/bin/env python3
"""Validate that all checklists are complete."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

CHECKLISTS = [
    "01_protocol/CHECKLIST.md",
    "02_search/CHECKLIST.md",
    "03_screening/CHECKLIST.md",
    "04_fulltext/CHECKLIST.md",
    "05_extraction/CHECKLIST.md",
    "06_analysis/CHECKLIST.md",
    "07_manuscript/CHECKLIST.md",
    "08_reviews/CHECKLIST.md",
    "09_qa/CHECKLIST.md",
]

UNCHECKED_RE = re.compile(r"^\s*-\s*\[\s*\]\s+", re.IGNORECASE)


def validate(root: Path) -> tuple[bool, list[str]]:
    issues: list[str] = []
    for rel in CHECKLISTS:
        path = root / rel
        if not path.exists():
            issues.append(f"Missing checklist: {rel}")
            continue
        lines = path.read_text().splitlines()
        for line in lines:
            if UNCHECKED_RE.match(line):
                issues.append(f"Unchecked: {rel} :: {line.strip()}")

    search_dir = root / "02_search"
    audit_files = list(search_dir.glob("round-*/search_audit.json")) if search_dir.exists() else []
    if not audit_files:
        issues.append("Missing search audit: 02_search/round-XX/search_audit.json")

    return (len(issues) == 0, issues)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate pipeline checklists.")
    parser.add_argument("--root", default=".", help="Project root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ok, issues = validate(root)
    if not ok:
        print("Checklist validation failed:")
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(2)
    print("All checklists completed.")


if __name__ == "__main__":
    main()
