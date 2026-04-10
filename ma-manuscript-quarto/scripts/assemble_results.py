#!/usr/bin/env python3
"""Assemble 03_results.qmd from result_paragraphs.qmd."""

from __future__ import annotations

import argparse
from pathlib import Path


START = "<!-- RESULT_PARAGRAPHS_START -->"
END = "<!-- RESULT_PARAGRAPHS_END -->"
SUMMARY_START = "<!-- RESULT_SUMMARY_TABLE_START -->"
SUMMARY_END = "<!-- RESULT_SUMMARY_TABLE_END -->"


def insert_block(results_text: str, block: str, start: str, end: str, marker: str) -> str:
    if start in results_text and end in results_text:
        prefix = results_text.split(start)[0]
        suffix = results_text.split(end)[1]
        return prefix + start + "\n" + block + "\n" + end + suffix

    if marker in results_text:
        parts = results_text.split(marker)
        head = parts[0] + marker
        tail = marker.join(parts[1:])
        return head + "\n\n" + start + "\n" + block + "\n" + end + "\n" + tail

    return results_text.rstrip() + "\n\n" + start + "\n" + block + "\n" + end + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble Results section.")
    parser.add_argument("--results", default="07_manuscript/03_results.qmd", help="Results QMD path")
    parser.add_argument("--paragraphs", default="07_manuscript/result_paragraphs.qmd", help="Paragraphs QMD path")
    parser.add_argument("--summary-table", default="07_manuscript/result_summary_table.md", help="Summary table path")
    args = parser.parse_args()

    results_path = Path(args.results)
    paragraphs_path = Path(args.paragraphs)
    if not results_path.exists():
        raise SystemExit(f"Missing results file: {results_path}")
    if not paragraphs_path.exists():
        raise SystemExit(f"Missing paragraphs file: {paragraphs_path}")

    block = paragraphs_path.read_text().strip()
    updated = insert_block(results_path.read_text(), block, START, END, "## Quantitative Synthesis")

    summary_path = Path(args.summary_table)
    if summary_path.exists():
        summary_block = summary_path.read_text().strip()
        updated = insert_block(updated, summary_block, SUMMARY_START, SUMMARY_END, "## Quantitative Synthesis")
    results_path.write_text(updated + "\n")


if __name__ == "__main__":
    main()
