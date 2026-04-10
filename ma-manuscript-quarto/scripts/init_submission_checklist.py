#!/usr/bin/env python3
"""Initialize a submission checklist tailored to a target journal."""

from __future__ import annotations

import argparse
from pathlib import Path


def build_checklist(journal: str) -> str:
    target = journal.strip() if journal else "UNSPECIFIED"
    lines = [
        "# Submission Checklist",
        "",
        f"- Target journal: {target}",
        "- Target article type: <fill>",
        "- Journal URL: <fill>",
        "",
        "## Manuscript Files",
        "- `07_manuscript/manuscript.pdf`",
        "- `07_manuscript/manuscript.html`",
        "- `07_manuscript/references.bib`",
        "- `07_manuscript/prisma_flow.svg`",
        "- `07_manuscript/result_summary_table.md` (if required as supplement)",
        "",
        "## Figures and Tables",
        "- Figures: 300 dpi, labeled, referenced in text",
        "- Tables: manuscript-ready and referenced in text",
        "- Verify all figure/table refs appear in Results and match `result_claims.csv`",
        "",
        "## Reporting Checklists",
        "- PRISMA 2020 checklist completed",
        "- MOOSE checklist completed if observational",
        "- GRADE summary (SoF) included if applicable",
        "",
        "## Methods and Reproducibility",
        "- Protocol and eligibility criteria consistent with methods",
        "- Search strategy documented with audit hashes",
        "- Data extraction and risk-of-bias recorded",
        "- Analysis scripts and `renv.lock` available",
        "",
        "## Declarations",
        "- Funding statement",
        "- Conflict of interest statement",
        "- Ethics/IRB statement (if applicable)",
        "- Data availability statement",
        "- Code availability statement",
        "- Author contributions (CRediT)",
        "",
        "## Journal-Specific Checks",
        "- Word count limit",
        "- Abstract structure requirements",
        "- Reference style",
        "- Figure/table limits",
        "- Supplementary material policy",
        "- Open access policy / fees",
        "",
        "## Cover Letter",
        "- Novelty and significance",
        "- Fit to journal scope",
        "- Prior submissions disclosure",
        "",
        "## Final QA",
        "- `09_qa/final_qa_report.md` PASS",
        "- `09_qa/results_consistency_report.md` PASS",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize submission checklist.")
    parser.add_argument("--journal", default="", help="Target journal name")
    parser.add_argument("--out", default="07_manuscript/submission_checklist.md", help="Output path")
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_checklist(args.journal) + "\n")


if __name__ == "__main__":
    main()
