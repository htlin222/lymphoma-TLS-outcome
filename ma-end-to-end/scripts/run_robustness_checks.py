#!/usr/bin/env python3
"""Run robustness checks: agreement stats, PRISMA flow, and GRADE summary."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run robustness checks.")
    parser.add_argument("--root", default=None, help="Project root (default: repo root)")
    parser.add_argument("--round", default="round-01", help="Search/screening round")
    parser.add_argument("--decisions-column", default="final_decision", help="Final decision column")
    parser.add_argument("--col-a", default="decision_r1", help="Reviewer A column")
    parser.add_argument("--col-b", default="decision_r2", help="Reviewer B column")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    root = Path(args.root).resolve() if args.root else repo_root

    search_audit = root / "02_search" / args.round / "search_audit.json"
    if not search_audit.exists():
        raise SystemExit(f"Missing search audit: {search_audit}")

    # Import scripts by adding their directories to sys.path
    sys.path.append(str(repo_root / "ma-screening-quality" / "scripts"))
    sys.path.append(str(repo_root / "ma-manuscript-quarto" / "scripts"))
    sys.path.append(str(repo_root / "ma-peer-review" / "scripts"))

    import dual_review_agreement  # type: ignore
    import prisma_flow  # type: ignore
    import init_grade_summary  # type: ignore

    decisions_csv = root / "03_screening" / args.round / "decisions.csv"
    agreement_out = root / "03_screening" / args.round / "agreement.md"
    agreement_out.parent.mkdir(parents=True, exist_ok=True)

    a_vals = dual_review_agreement.read_column(decisions_csv, args.col_a)
    b_vals = dual_review_agreement.read_column(decisions_csv, args.col_b)
    po, kappa, matrix, labels, n = dual_review_agreement.compute_agreement(a_vals, b_vals)

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
    agreement_out.write_text("\n".join(lines) + "\n")

    prisma_out = root / "07_manuscript" / "prisma_flow.md"
    prisma_svg = root / "07_manuscript" / "prisma_flow.svg"
    counts = prisma_flow.build_prisma_summary(
        root=root,
        round_name=args.round,
        decisions_column=args.decisions_column,
        out_md=prisma_out,
        strict=True,
    )
    prisma_flow.render_svg(prisma_svg, counts)

    extraction_csv = root / "05_extraction" / "extraction.csv"
    grade_csv = root / "08_reviews" / "grade_summary.csv"
    grade_md = root / "08_reviews" / "grade_summary.md"
    outcomes = init_grade_summary.read_outcomes(extraction_csv)
    init_grade_summary.write_csv(grade_csv, outcomes)
    init_grade_summary.write_markdown(grade_md, outcomes)

    # Generate artifact hashes if possible
    sys.path.append(str(repo_root / "ma-end-to-end" / "scripts"))
    import hash_artifacts  # type: ignore
    hash_artifacts.main()


if __name__ == "__main__":
    main()
