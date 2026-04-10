#!/usr/bin/env python3
"""Check that figures and tables are referenced in manuscript files."""

from __future__ import annotations

import argparse
from pathlib import Path


def collect_text(manuscript_dir: Path) -> str:
    parts = []
    for path in manuscript_dir.glob("*.qmd"):
        parts.append(path.read_text())
    return "\n".join(parts).lower()


def find_unreferenced(files: list[Path], manuscript_text: str) -> list[str]:
    missing = []
    for path in files:
        name = path.name.lower()
        stem = path.stem.lower()
        if name not in manuscript_text and stem not in manuscript_text:
            missing.append(path.name)
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(description="Check figure/table references in manuscript.")
    parser.add_argument("--manuscript-dir", default="07_manuscript", help="Manuscript directory")
    parser.add_argument("--figures-dir", default="06_analysis/figures", help="Figures directory")
    parser.add_argument("--tables-dir", default="06_analysis/tables", help="Tables directory")
    parser.add_argument("--out", default="09_qa/crossref_report.md", help="Output report")
    args = parser.parse_args()

    manuscript_dir = Path(args.manuscript_dir)
    figures_dir = Path(args.figures_dir)
    tables_dir = Path(args.tables_dir)

    manuscript_text = collect_text(manuscript_dir) if manuscript_dir.exists() else ""

    figure_files = [p for p in figures_dir.glob("*.*") if p.is_file()] if figures_dir.exists() else []
    table_files = [p for p in tables_dir.glob("*.*") if p.is_file()] if tables_dir.exists() else []

    missing_figures = find_unreferenced(figure_files, manuscript_text)
    missing_tables = find_unreferenced(table_files, manuscript_text)

    lines = [
        "# Cross-Reference Report",
        "",
        "## Unreferenced Figures",
    ]
    if missing_figures:
        for item in missing_figures:
            lines.append(f"- {item}")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Unreferenced Tables")
    if missing_tables:
        for item in missing_tables:
            lines.append(f"- {item}")
    else:
        lines.append("- None")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
