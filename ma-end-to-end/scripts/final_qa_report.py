#!/usr/bin/env python3
"""Generate a final QA report and fail if critical items are missing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import datetime as dt
import json


def status_line(ok: bool, label: str) -> str:
    return f"- {'PASS' if ok else 'FAIL'}: {label}"


def load_checklist_lines(path: Path) -> Tuple[List[str], List[str]]:
    checked: List[str] = []
    unchecked: List[str] = []
    if not path.exists():
        return checked, unchecked
    for line in path.read_text().splitlines():
        if line.strip().startswith("- [x]") or line.strip().startswith("- [X]"):
            checked.append(line.strip())
        elif line.strip().startswith("- [ ]"):
            unchecked.append(line.strip())
    return checked, unchecked


def file_timestamp(path: Path) -> str:
    if not path.exists():
        return "missing"
    ts = dt.datetime.utcfromtimestamp(path.stat().st_mtime)
    return ts.isoformat() + "Z"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate final QA report.")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--round", default="round-01", help="Search round")
    parser.add_argument("--out", default="09_qa/final_qa_report.md", help="Output report path")
    parser.add_argument("--out-json", default=None, help="Optional JSON report path")
    parser.add_argument("--hashes", default="09_qa/artifact_hashes.json", help="Artifact hashes JSON")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    repo_root = Path(__file__).resolve().parents[2]

    sys.path.append(str(repo_root / "ma-end-to-end" / "scripts"))
    sys.path.append(str(repo_root / "ma-manuscript-quarto" / "scripts"))

    import validate_pipeline  # type: ignore
    import prisma_flow  # type: ignore

    issues: List[str] = []
    checks: List[str] = []

    ok_checklists, checklist_issues = validate_pipeline.validate(root)
    checks.append(status_line(ok_checklists, "All checklists completed"))
    if not ok_checklists:
        issues.extend(checklist_issues)

    search_audit = root / "02_search" / args.round / "search_audit.json"
    ok_audit = search_audit.exists()
    checks.append(status_line(ok_audit, "Search audit present"))
    if not ok_audit:
        issues.append(f"Missing search audit: {search_audit}")

    claim_audit = root / "09_qa" / "claim_audit.md"
    crossref_report = root / "09_qa" / "crossref_report.md"
    reporting_audit = root / "09_qa" / "reporting_checklist_audit.md"
    claim_table = root / "09_qa" / "claim_table_check.md"
    stage_transition = root / "09_qa" / "stage_transition_report.md"
    checkpoint_log = root / "09_qa" / "checkpoint.log"
    checkpoints_dir = root / "09_qa" / "checkpoints"
    evidence_map = root / "07_manuscript" / "evidence_map.md"
    result_claims = root / "07_manuscript" / "result_claims.csv"
    result_paragraphs = root / "07_manuscript" / "result_paragraphs.md"
    result_paragraphs_qmd = root / "07_manuscript" / "result_paragraphs.qmd"
    result_summary_table = root / "07_manuscript" / "result_summary_table.md"
    study_characteristics_md = root / "07_manuscript" / "study_characteristics.md"
    study_characteristics_csv = root / "07_manuscript" / "study_characteristics.csv"
    traceability_table = root / "07_manuscript" / "traceability_table.md"
    methods_qmd = root / "07_manuscript" / "02_methods.qmd"
    results_qmd = root / "07_manuscript" / "03_results.qmd"
    results_consistency = root / "09_qa" / "results_consistency_report.md"
    submission_checklist = root / "07_manuscript" / "submission_checklist.md"
    ok_claim = claim_audit.exists()
    ok_crossref = crossref_report.exists()
    ok_reporting = reporting_audit.exists()
    ok_claim_table = claim_table.exists()
    ok_stage_transition = stage_transition.exists()
    ok_checkpoint = checkpoint_log.exists() or (checkpoints_dir.exists() and any(checkpoints_dir.glob("*.tar.gz")))
    ok_evidence_map = evidence_map.exists()
    ok_result_claims = result_claims.exists()
    ok_result_paragraphs = result_paragraphs.exists()
    ok_result_paragraphs_qmd = result_paragraphs_qmd.exists()
    ok_result_summary_table = result_summary_table.exists()
    ok_study_characteristics_md = study_characteristics_md.exists()
    ok_study_characteristics_csv = study_characteristics_csv.exists()
    ok_traceability = traceability_table.exists()
    ok_traceability_inserted = False
    if methods_qmd.exists():
        text = methods_qmd.read_text()
        ok_traceability_inserted = "<!-- TRACEABILITY_TABLE_START -->" in text and "<!-- TRACEABILITY_TABLE_END -->" in text
    ok_results_inserted = False
    if results_qmd.exists():
        text = results_qmd.read_text()
        ok_results_inserted = "<!-- RESULT_PARAGRAPHS_START -->" in text and "<!-- RESULT_PARAGRAPHS_END -->" in text
    ok_summary_inserted = False
    if results_qmd.exists():
        text = results_qmd.read_text()
        ok_summary_inserted = "<!-- RESULT_SUMMARY_TABLE_START -->" in text and "<!-- RESULT_SUMMARY_TABLE_END -->" in text
    ok_study_characteristics_inserted = False
    if results_qmd.exists():
        text = results_qmd.read_text()
        ok_study_characteristics_inserted = "<!-- STUDY_CHARACTERISTICS_START -->" in text and "<!-- STUDY_CHARACTERISTICS_END -->" in text
    hash_json = root / args.hashes
    checks.append(status_line(ok_claim, "Claim audit present"))
    checks.append(status_line(ok_crossref, "Cross-reference report present"))
    checks.append(status_line(ok_reporting, "Reporting checklist audit present"))
    checks.append(status_line(ok_claim_table, "Claim-to-table report present"))
    checks.append(status_line(ok_stage_transition, "Stage transition report present"))
    checks.append(status_line(ok_checkpoint, "Checkpoint log or archive present"))
    checks.append(status_line(ok_evidence_map, "Manuscript evidence map present"))
    checks.append(status_line(ok_result_claims, "Result claims table present"))
    checks.append(status_line(ok_result_paragraphs, "Result paragraph stubs present"))
    checks.append(status_line(ok_result_paragraphs_qmd, "Result paragraph QMD present"))
    checks.append(status_line(ok_result_summary_table, "Result summary table present"))
    checks.append(status_line(ok_study_characteristics_md, "Study characteristics table (md) present"))
    checks.append(status_line(ok_study_characteristics_csv, "Study characteristics table (csv) present"))
    checks.append(status_line(ok_traceability, "Traceability table present"))
    checks.append(status_line(ok_traceability_inserted, "Traceability table inserted into Methods"))
    checks.append(status_line(ok_results_inserted, "Result paragraphs inserted into Results"))
    checks.append(status_line(ok_summary_inserted, "Result summary table inserted into Results"))
    checks.append(status_line(ok_study_characteristics_inserted, "Study characteristics inserted into Results"))
    checks.append(status_line(submission_checklist.exists(), "Submission checklist present"))
    checks.append(status_line(results_consistency.exists(), "Results consistency report present"))
    checks.append(status_line(hash_json.exists(), "Artifact hashes present"))
    if not ok_claim:
        issues.append(f"Missing claim audit: {claim_audit}")
    if not ok_crossref:
        issues.append(f"Missing crossref report: {crossref_report}")
    if not ok_reporting:
        issues.append(f"Missing reporting checklist audit: {reporting_audit}")
    if not ok_claim_table:
        issues.append(f"Missing claim-to-table report: {claim_table}")
    if not ok_stage_transition:
        issues.append(f"Missing stage transition report: {stage_transition}")
    if not ok_checkpoint:
        issues.append("Missing checkpoint log or archive in 09_qa/checkpoints")
    if not ok_evidence_map:
        issues.append(f"Missing manuscript evidence map: {evidence_map}")
    if not ok_result_claims:
        issues.append(f"Missing result claims table: {result_claims}")
    if not ok_result_paragraphs:
        issues.append(f"Missing result paragraph stubs: {result_paragraphs}")
    if not ok_result_paragraphs_qmd:
        issues.append(f"Missing result paragraph QMD: {result_paragraphs_qmd}")
    if not ok_result_summary_table:
        issues.append(f"Missing result summary table: {result_summary_table}")
    if not ok_study_characteristics_md:
        issues.append(f"Missing study characteristics table: {study_characteristics_md}")
    if not ok_study_characteristics_csv:
        issues.append(f"Missing study characteristics CSV: {study_characteristics_csv}")
    if not ok_traceability:
        issues.append(f"Missing traceability table: {traceability_table}")
    if not ok_traceability_inserted:
        issues.append(f"Traceability table not inserted into Methods: {methods_qmd}")
    if not ok_results_inserted:
        issues.append(f"Result paragraphs not inserted into Results: {results_qmd}")
    if not ok_summary_inserted:
        issues.append(f"Result summary table not inserted into Results: {results_qmd}")
    if not ok_study_characteristics_inserted:
        issues.append(f"Study characteristics not inserted into Results: {results_qmd}")
    if not submission_checklist.exists():
        issues.append(f"Missing submission checklist: {submission_checklist}")
    if not results_consistency.exists():
        issues.append(f"Missing results consistency report: {results_consistency}")
    if not hash_json.exists():
        issues.append(f"Missing artifact hashes: {hash_json}")

    prisma_ok = True
    prisma_error = ""
    try:
        prisma_flow.build_prisma_summary(
            root=root,
            round_name=args.round,
            decisions_column="final_decision",
            out_md=root / "07_manuscript" / "prisma_flow.md",
            strict=True,
        )
    except SystemExit as exc:
        prisma_ok = False
        prisma_error = str(exc)
        issues.append(f"PRISMA strict check failed: {prisma_error}")

    checks.append(status_line(prisma_ok, "PRISMA counts complete (strict)"))

    manuscript_pdf = root / "07_manuscript" / "manuscript.pdf"
    manuscript_html = root / "07_manuscript" / "manuscript.html"
    ok_render = manuscript_pdf.exists() and manuscript_html.exists()
    checks.append(status_line(ok_render, "Rendered manuscript outputs present"))
    if not ok_render:
        issues.append("Missing manuscript.pdf or manuscript.html")

    report_path = root / args.out
    report_path.parent.mkdir(parents=True, exist_ok=True)

    checklist_details: Dict[str, Dict[str, List[str]]] = {}
    for rel in validate_pipeline.CHECKLISTS:
        path = root / rel
        checked, unchecked = load_checklist_lines(path)
        checklist_details[rel] = {"checked": checked, "unchecked": unchecked}

    timestamps = {
        "dedupe_bib": file_timestamp(root / "02_search" / args.round / "dedupe.bib"),
        "db_counts_csv": file_timestamp(root / "02_search" / args.round / "db_counts.csv"),
        "search_audit": file_timestamp(root / "02_search" / args.round / "search_audit.json"),
        "prisma_flow_svg": file_timestamp(root / "07_manuscript" / "prisma_flow.svg"),
        "manuscript_pdf": file_timestamp(root / "07_manuscript" / "manuscript.pdf"),
        "manuscript_html": file_timestamp(root / "07_manuscript" / "manuscript.html"),
        "grade_summary_csv": file_timestamp(root / "08_reviews" / "grade_summary.csv"),
        "agreement_md": file_timestamp(root / "03_screening" / args.round / "agreement.md"),
        "claim_audit": file_timestamp(claim_audit),
        "crossref_report": file_timestamp(crossref_report),
        "reporting_checklist_audit": file_timestamp(reporting_audit),
        "claim_table_check": file_timestamp(claim_table),
        "stage_transition_report": file_timestamp(stage_transition),
        "checkpoint_log": file_timestamp(checkpoint_log),
        "evidence_map": file_timestamp(evidence_map),
        "result_claims": file_timestamp(result_claims),
        "result_paragraphs": file_timestamp(result_paragraphs),
        "result_paragraphs_qmd": file_timestamp(result_paragraphs_qmd),
        "result_summary_table": file_timestamp(result_summary_table),
        "study_characteristics_md": file_timestamp(study_characteristics_md),
        "study_characteristics_csv": file_timestamp(study_characteristics_csv),
        "traceability_table": file_timestamp(traceability_table),
        "results_qmd": file_timestamp(results_qmd),
        "results_consistency_report": file_timestamp(results_consistency),
        "submission_checklist": file_timestamp(submission_checklist),
        "artifact_hashes": file_timestamp(hash_json),
    }

    hashes_path = root / args.hashes
    hashes = {}
    if hashes_path.exists():
        try:
            hashes = json.loads(hashes_path.read_text())
        except Exception:
            hashes = {}

    lines = [
        "# Final QA Report",
        "",
        "## Summary",
        *checks,
        "",
        "## Issues",
    ]

    if issues:
        for issue in issues:
            lines.append(f"- {issue}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Checklist Details",
        ]
    )
    for rel, detail in checklist_details.items():
        lines.append("")
        lines.append(f"### {rel}")
        if detail["unchecked"]:
            lines.append("Unchecked items:")
            for item in detail["unchecked"]:
                lines.append(f"- {item}")
        else:
            lines.append("Unchecked items: none")

    lines.extend(
        [
            "",
            "## Key File Timestamps (UTC)",
            "",
            "| Artifact | Timestamp |",
            "| --- | --- |",
        ]
    )
    for key, value in timestamps.items():
        lines.append(f"| {key} | {value} |")

    lines.extend(
        [
            "",
            "## Artifact Hashes",
        ]
    )
    if hashes:
        lines.append("See JSON output for full hashes.")
    else:
        lines.append("- Missing or unreadable artifact hashes JSON.")

    report_path.write_text("\n".join(lines) + "\n")

    if args.out_json:
        json_path = root / args.out_json
        json_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "summary": checks,
            "issues": issues,
            "checklists": checklist_details,
            "timestamps": timestamps,
            "artifact_hashes": hashes,
        }
        json_path.write_text(json.dumps(payload, indent=2) + "\n")

    if issues:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
