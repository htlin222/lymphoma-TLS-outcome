#!/usr/bin/env python3
"""Check consistency between result claims and analysis outputs."""

from __future__ import annotations

import argparse
import csv
import os
import re
from pathlib import Path
from typing import Dict, List, Set


def read_claims(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing claims CSV: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [{k: (v or "").strip() for k, v in row.items()} for row in reader]


def list_files(path: Path, patterns: List[str]) -> List[Path]:
    files: List[Path] = []
    if not path.exists():
        return files
    for pattern in patterns:
        files.extend(path.glob(pattern))
    return sorted([p for p in files if p.is_file()])


def parse_citations(raw: str) -> List[str]:
    keys = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if token.startswith("@"):
            token = token[1:]
        keys.append(token)
    return keys


def read_bib_keys(path: Path) -> Set[str]:
    if not path.exists():
        return set()
    keys = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("@") and "{" in line:
            key = line.split("{", 1)[1].split(",", 1)[0].strip()
            if key:
                keys.add(key)
    return keys


def main() -> None:
    parser = argparse.ArgumentParser(description="Results consistency report.")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--claims", default="07_manuscript/result_claims.csv", help="Claims CSV")
    parser.add_argument("--results", default="07_manuscript/03_results.qmd", help="Results QMD")
    parser.add_argument("--figures", default="06_analysis/figures", help="Figures dir")
    parser.add_argument("--tables", default="06_analysis/tables", help="Tables dir")
    parser.add_argument("--bib", default="07_manuscript/references.bib", help="References BibTeX")
    parser.add_argument("--out", default="09_qa/results_consistency_report.md", help="Output report")
    parser.add_argument("--strict", action="store_true", help="Fail on missing items")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    claims = read_claims(root / args.claims)
    results_path = root / args.results
    results_text = results_path.read_text() if results_path.exists() else ""

    fig_files = list_files(root / args.figures, ["*.png", "*.svg"])
    tbl_files = list_files(root / args.tables, ["*.html", "*.csv", "*.txt"])
    fig_names = {f"../06_analysis/figures/{p.name}" for p in fig_files}
    tbl_names = {f"../06_analysis/tables/{p.name}" for p in tbl_files}
    all_output_refs = fig_names | tbl_names

    referenced_refs: Set[str] = set()
    missing_refs: List[str] = []
    missing_claim_ids: List[str] = []
    missing_refs_in_results: List[str] = []
    missing_citations_in_results: List[str] = []
    missing_citations_in_bib: List[str] = []
    short_claims: List[str] = []

    bib_keys = read_bib_keys(root / args.bib)

    # Optional word count check using result_paragraphs.qmd
    paragraphs_path = root / "07_manuscript" / "result_paragraphs.qmd"
    min_words = int(os.getenv("RESULTS_MIN_WORDS", "25"))
    if paragraphs_path.exists():
        text = paragraphs_path.read_text()
        sections = {}
        current = None
        buffer = []
        for line in text.splitlines():
            if line.startswith("## "):
                if current:
                    sections[current] = "\n".join(buffer)
                current = line.replace("## ", "").strip()
                buffer = []
            else:
                buffer.append(line)
        if current:
            sections[current] = "\n".join(buffer)

        def word_count(value: str) -> int:
            return len(re.findall(r"[A-Za-z0-9]+", value))

        for row in claims:
            claim_id = row.get("claim_id", "")
            if not claim_id:
                continue
            content = sections.get(claim_id, "")
            if word_count(content) < min_words:
                short_claims.append(f"{claim_id} ({word_count(content)} words)")

    for row in claims:
        claim_id = row.get("claim_id", "")
        if claim_id and claim_id not in results_text:
            missing_claim_ids.append(claim_id)

        ref = row.get("figure_ref", "") or row.get("table_ref", "")
        if ref:
            referenced_refs.add(ref)
            if ref not in all_output_refs:
                missing_refs.append(ref)
            if ref not in results_text:
                missing_refs_in_results.append(ref)

        for key in parse_citations(row.get("citation_keys", "")):
            if f"@{key}" not in results_text:
                missing_citations_in_results.append(f"{row.get('claim_id','')}: @{key}")
            if bib_keys and key not in bib_keys:
                missing_citations_in_bib.append(f"{row.get('claim_id','')}: @{key}")

    unreferenced = sorted(all_output_refs - referenced_refs)

    lines = [
        "# Results Consistency Report",
        "",
        f"Claims: {len(claims)}",
        f"Figures: {len(fig_files)}",
        f"Tables: {len(tbl_files)}",
        "",
        "## Missing Claim IDs In Results",
    ]
    if missing_claim_ids:
        lines.extend([f"- {cid}" for cid in sorted(set(missing_claim_ids))])
    else:
        lines.append("- None")

    lines.extend(["", "## Missing Figure/Table References In Results"])
    if missing_refs_in_results:
        lines.extend([f"- {ref}" for ref in sorted(set(missing_refs_in_results))])
    else:
        lines.append("- None")

    lines.extend(["", "## Missing Referenced Output Files"])
    if missing_refs:
        lines.extend([f"- {ref}" for ref in sorted(set(missing_refs))])
    else:
        lines.append("- None")

    lines.extend(["", "## Unreferenced Outputs (not in claims)"])
    if unreferenced:
        lines.extend([f"- {ref}" for ref in unreferenced])
    else:
        lines.append("- None")

    lines.extend(["", "## Missing Citations In Results"])
    if missing_citations_in_results:
        lines.extend([f"- {item}" for item in sorted(set(missing_citations_in_results))])
    else:
        lines.append("- None")

    lines.extend(["", "## Missing Citations In references.bib"])
    if missing_citations_in_bib:
        lines.extend([f"- {item}" for item in sorted(set(missing_citations_in_bib))])
    else:
        lines.append("- None")

    lines.extend(["", f"## Claim Paragraphs Below {min_words} Words"])
    if short_claims:
        lines.extend([f"- {item}" for item in sorted(set(short_claims))])
    else:
        lines.append("- None")

    out_path = root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n")

    if args.strict:
        if (
            missing_claim_ids
            or missing_refs
            or missing_refs_in_results
            or missing_citations_in_results
            or missing_citations_in_bib
            or short_claims
        ):
            raise SystemExit(2)


if __name__ == "__main__":
    main()
