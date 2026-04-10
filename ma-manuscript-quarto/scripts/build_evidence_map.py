#!/usr/bin/env python3
"""Build a manuscript evidence map from pipeline artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import Iterable, List, Tuple


def file_timestamp(path: Path) -> str:
    if not path.exists():
        return "missing"
    ts = dt.datetime.utcfromtimestamp(path.stat().st_mtime)
    return ts.isoformat() + "Z"


def list_files(base: Path, patterns: Iterable[str]) -> List[Path]:
    if not base.exists():
        return []
    files: List[Path] = []
    for pattern in patterns:
        files.extend(base.glob(pattern))
    return sorted([p for p in files if p.is_file()])


def add_file(lines: List[str], label: str, path: Path) -> None:
    exists = "yes" if path.exists() else "no"
    lines.append(f"| {label} | {exists} | {file_timestamp(path)} |")


def add_dir(lines: List[str], label: str, path: Path, patterns: Iterable[str]) -> None:
    files = list_files(path, patterns)
    if not files:
        lines.append(f"| {label} | no | missing |")
        return
    for idx, file in enumerate(files, start=1):
        short_label = f"{label}/{file.name}"
        lines.append(f"| {short_label} | yes | {file_timestamp(file)} |")


def section_header(lines: List[str], title: str) -> None:
    lines.append("")
    lines.append(f"## {title}")
    lines.append("")
    lines.append("| Artifact | Exists | Timestamp (UTC) |")
    lines.append("| --- | --- | --- |")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build manuscript evidence map.")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--round", default="round-01", help="Search/screening round")
    parser.add_argument("--out", default="07_manuscript/evidence_map.md", help="Output markdown")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    round_dir = root / "02_search" / args.round
    screening_dir = root / "03_screening" / args.round

    lines: List[str] = ["# Manuscript Evidence Map", ""]

    section_header(lines, "Protocol")
    add_file(lines, "01_protocol/pico.yaml", root / "01_protocol" / "pico.yaml")
    add_file(lines, "01_protocol/eligibility.md", root / "01_protocol" / "eligibility.md")
    add_file(lines, "01_protocol/outcomes.md", root / "01_protocol" / "outcomes.md")
    add_file(lines, "01_protocol/search-plan.md", root / "01_protocol" / "search-plan.md")

    section_header(lines, "Search")
    add_file(lines, f"02_search/{args.round}/queries.txt", round_dir / "queries.txt")
    add_file(lines, f"02_search/{args.round}/search_report.md", round_dir / "search_report.md")
    add_file(lines, f"02_search/{args.round}/search_audit.json", round_dir / "search_audit.json")
    add_file(lines, f"02_search/{args.round}/db_counts.md", round_dir / "db_counts.md")
    add_file(lines, f"02_search/{args.round}/dedupe.log", round_dir / "dedupe.log")
    add_file(lines, f"02_search/{args.round}/dedupe.bib", round_dir / "dedupe.bib")

    section_header(lines, "Screening")
    add_file(lines, f"03_screening/{args.round}/decisions.csv", screening_dir / "decisions.csv")
    add_file(lines, f"03_screening/{args.round}/quality.csv", screening_dir / "quality.csv")
    add_file(lines, f"03_screening/{args.round}/agreement.md", screening_dir / "agreement.md")
    add_file(lines, f"03_screening/{args.round}/included.bib", screening_dir / "included.bib")

    section_header(lines, "Fulltext")
    add_file(lines, "04_fulltext/manifest.csv", root / "04_fulltext" / "manifest.csv")
    add_dir(lines, "04_fulltext/previews", root / "04_fulltext" / "previews", ["*.png"])

    section_header(lines, "Extraction")
    add_file(lines, "05_extraction/extraction.csv", root / "05_extraction" / "extraction.csv")
    add_file(lines, "05_extraction/extraction.sqlite", root / "05_extraction" / "extraction.sqlite")
    add_file(lines, "05_extraction/data-dictionary.md", root / "05_extraction" / "data-dictionary.md")
    add_file(lines, "05_extraction/source.csv", root / "05_extraction" / "source.csv")
    add_file(lines, "05_extraction/source_validation.md", root / "05_extraction" / "source_validation.md")

    section_header(lines, "Analysis Outputs")
    add_file(lines, "06_analysis/validation.md", root / "06_analysis" / "validation.md")
    add_file(lines, "06_analysis/renv.lock", root / "06_analysis" / "renv.lock")
    add_dir(lines, "06_analysis/figures", root / "06_analysis" / "figures", ["*.png", "*.svg"])
    add_dir(lines, "06_analysis/tables", root / "06_analysis" / "tables", ["*.html", "*.csv", "*.txt"])

    section_header(lines, "Reviews")
    add_file(lines, "08_reviews/grade_summary.csv", root / "08_reviews" / "grade_summary.csv")
    add_file(lines, "08_reviews/grade_summary.md", root / "08_reviews" / "grade_summary.md")

    section_header(lines, "Manuscript Pre-Checks")
    add_file(lines, "07_manuscript/prisma_flow.md", root / "07_manuscript" / "prisma_flow.md")
    add_file(lines, "07_manuscript/prisma_flow.svg", root / "07_manuscript" / "prisma_flow.svg")
    add_file(lines, "07_manuscript/result_claims.csv", root / "07_manuscript" / "result_claims.csv")
    add_file(lines, "07_manuscript/result_paragraphs.md", root / "07_manuscript" / "result_paragraphs.md")
    add_file(lines, "07_manuscript/result_paragraphs.qmd", root / "07_manuscript" / "result_paragraphs.qmd")
    add_file(lines, "07_manuscript/result_summary_table.md", root / "07_manuscript" / "result_summary_table.md")
    add_file(lines, "07_manuscript/study_characteristics.md", root / "07_manuscript" / "study_characteristics.md")
    add_file(lines, "07_manuscript/study_characteristics.csv", root / "07_manuscript" / "study_characteristics.csv")
    add_file(lines, "07_manuscript/submission_checklist.md", root / "07_manuscript" / "submission_checklist.md")
    add_file(lines, "07_manuscript/traceability_table.md", root / "07_manuscript" / "traceability_table.md")

    section_header(lines, "QA")
    add_file(lines, "09_qa/claim_audit.md", root / "09_qa" / "claim_audit.md")
    add_file(lines, "09_qa/reporting_checklist_audit.md", root / "09_qa" / "reporting_checklist_audit.md")
    add_file(lines, "09_qa/claim_table_check.md", root / "09_qa" / "claim_table_check.md")
    add_file(lines, "09_qa/crossref_report.md", root / "09_qa" / "crossref_report.md")
    add_file(lines, "09_qa/results_consistency_report.md", root / "09_qa" / "results_consistency_report.md")

    out_path = root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
