#!/usr/bin/env python3
"""Compute dual-review agreement and Cohen's kappa from screening decisions."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


def read_column(path: Path, column: str) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if column not in reader.fieldnames:
            raise ValueError(f"Missing column '{column}' in {path}")
        values = [row.get(column, "").strip() for row in reader]
    return values


def compute_agreement(a_vals: list[str], b_vals: list[str]) -> tuple[float, float, dict[str, dict[str, int]], list[str], int]:
    if len(a_vals) != len(b_vals):
        raise ValueError("Reviewer columns have different lengths")

    labels = sorted({v for v in a_vals + b_vals if v})
    if not labels:
        raise ValueError("No labels found in reviewer columns")

    matrix = defaultdict(lambda: defaultdict(int))
    count_a = Counter()
    count_b = Counter()

    for a, b in zip(a_vals, b_vals):
        if not a or not b:
            continue
        matrix[a][b] += 1
        count_a[a] += 1
        count_b[b] += 1

    n = sum(count_a.values())
    if n == 0:
        raise ValueError("No paired decisions to evaluate")

    agree = sum(matrix[label][label] for label in labels)
    po = agree / n

    pe = 0.0
    for label in labels:
        pe += (count_a[label] / n) * (count_b[label] / n)

    kappa = (po - pe) / (1 - pe) if pe < 1 else 0.0
    return po, kappa, matrix, labels, n


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute screening agreement stats.")
    parser.add_argument("--file", required=True, help="CSV file with two reviewer columns")
    parser.add_argument("--col-a", required=True, help="Column name for reviewer A decisions")
    parser.add_argument("--col-b", required=True, help="Column name for reviewer B decisions")
    parser.add_argument("--out", required=True, help="Output markdown file")
    args = parser.parse_args()

    path = Path(args.file)
    a_vals = read_column(path, args.col_a)
    b_vals = read_column(path, args.col_b)

    po, kappa, matrix, labels, n = compute_agreement(a_vals, b_vals)

    out = Path(args.out)
    lines = [
        "# Dual-Review Agreement",
        "",
        f"Records analyzed: {n}",
        f"Percent agreement: {po:.3f}",
        f"Cohen's kappa: {kappa:.3f}",
        "",
        "## Confusion Matrix",
        "",
    ]

    header = "| Reviewer A \\ Reviewer B | " + " | ".join(labels) + " |"
    sep = "| --- | " + " | ".join(["---"] * len(labels)) + " |"
    lines.append(header)
    lines.append(sep)

    for label_a in labels:
        row = [str(matrix[label_a][label_b]) for label_b in labels]
        lines.append(f"| {label_a} | " + " | ".join(row) + " |")

    out.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
