#!/usr/bin/env python3
"""Check that numeric claims in Results appear in tables."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?%?\b")


def extract_numbers(text: str) -> set[str]:
    return set(NUMBER_RE.findall(text))


def main() -> None:
    parser = argparse.ArgumentParser(description="Check results claims against tables.")
    parser.add_argument("--results", required=True, help="Results file path")
    parser.add_argument("--tables-dir", required=True, help="Tables directory")
    parser.add_argument("--out", required=True, help="Output report path")
    args = parser.parse_args()

    results_path = Path(args.results)
    tables_dir = Path(args.tables_dir)

    if not results_path.exists():
        raise SystemExit(f"Missing results file: {results_path}")
    if not tables_dir.exists():
        raise SystemExit(f"Missing tables directory: {tables_dir}")

    results_numbers = extract_numbers(results_path.read_text())

    table_numbers: set[str] = set()
    for path in tables_dir.glob("*.*"):
        if path.is_file():
            table_numbers |= extract_numbers(path.read_text())

    missing = sorted(results_numbers - table_numbers)

    lines = [
        "# Claim-to-Table Check",
        "",
        f"Results numeric tokens: {len(results_numbers)}",
        f"Table numeric tokens: {len(table_numbers)}",
        "",
        "## Numbers in Results Not Found in Tables",
    ]

    if missing:
        for item in missing:
            lines.append(f"- {item}")
    else:
        lines.append("- None")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n")

    if missing:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
