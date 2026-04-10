#!/usr/bin/env python3
"""Validate pipeline and render Quarto manuscript."""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
from pathlib import Path


def validate_result_claims(root: Path) -> None:
    claims_path = root / "07_manuscript" / "result_claims.csv"
    if not claims_path.exists():
        raise SystemExit(f"Missing result claims table: {claims_path}")

    with claims_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [{k: (v or "").strip() for k, v in row.items()} for row in reader]

    if not rows:
        raise SystemExit("result_claims.csv has no rows.")

    missing_refs = []
    missing_files = []
    missing_effect_fields = []
    missing_citations = []
    for idx, row in enumerate(rows, start=1):
        fig = row.get("figure_ref", "")
        tbl = row.get("table_ref", "")
        if not fig and not tbl:
            missing_refs.append(f"row {idx} ({row.get('claim_id', '')})")
            continue

        effect = row.get("effect_estimate", "")
        ci = row.get("ci", "")
        p_value = row.get("p_value", "")
        if not effect or not ci or not p_value:
            missing_effect_fields.append(f"row {idx} ({row.get('claim_id', '')})")
        citation_keys = row.get("citation_keys", "")
        if not citation_keys.strip():
            missing_citations.append(f"row {idx} ({row.get('claim_id', '')})")

        for ref in [fig, tbl]:
            if not ref:
                continue
            ref_path = Path(ref)
            if not ref_path.is_absolute():
                ref_path = (root / "07_manuscript" / ref_path).resolve()
            if not ref_path.exists():
                missing_files.append(f"{row.get('claim_id', '')}: {ref}")

    if missing_refs:
        raise SystemExit(
            "Result claims missing figure/table refs: " + ", ".join(missing_refs)
        )
    if missing_files:
        raise SystemExit(
            "Result claims reference missing files: " + ", ".join(missing_files)
        )
    if missing_effect_fields:
        raise SystemExit(
            "Result claims missing effect/CI/p-value: " + ", ".join(missing_effect_fields)
        )
    if missing_citations:
        raise SystemExit(
            "Result claims missing citation_keys: " + ", ".join(missing_citations)
        )


def validate_results_in_manuscript(root: Path) -> None:
    claims_path = root / "07_manuscript" / "result_claims.csv"
    results_path = root / "07_manuscript" / "03_results.qmd"
    if not claims_path.exists() or not results_path.exists():
        return

    with claims_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        claims = [{k: (v or "").strip() for k, v in row.items()} for row in reader]

    results_text = results_path.read_text()
    missing_claims = []
    for row in claims:
        claim_id = row.get("claim_id", "")
        if not claim_id:
            continue
        if claim_id not in results_text:
            missing_claims.append(claim_id)

    if missing_claims:
        raise SystemExit(
            "Results missing claim IDs: " + ", ".join(sorted(missing_claims))
        )

    missing_refs = []
    for row in claims:
        ref = row.get("figure_ref", "") or row.get("table_ref", "")
        if ref and ref not in results_text:
            missing_refs.append(ref)
    if missing_refs:
        raise SystemExit(
            "Results missing figure/table references: " + ", ".join(sorted(set(missing_refs)))
        )

    paragraphs_path = root / "07_manuscript" / "result_paragraphs.qmd"
    if paragraphs_path.exists():
        qmd_text = paragraphs_path.read_text()
        missing_qmd_ids = []
        for row in claims:
            claim_id = row.get("claim_id", "")
            if claim_id and claim_id not in qmd_text:
                missing_qmd_ids.append(claim_id)
        if missing_qmd_ids:
            raise SystemExit(
                "Result paragraphs missing claim IDs: " + ", ".join(sorted(missing_qmd_ids))
            )
        min_words = int(os.getenv("RESULTS_MIN_WORDS", "25"))
        sections = {}
        current = None
        buffer = []
        for line in qmd_text.splitlines():
            if line.startswith("## "):
                if current:
                    sections[current] = "\n".join(buffer)
                current = line.replace("## ", "").strip()
                buffer = []
            else:
                buffer.append(line)
        if current:
            sections[current] = "\n".join(buffer)

        def word_count(text: str) -> int:
            return len(re.findall(r"[A-Za-z0-9]+", text))

        short_claims = []
        for row in claims:
            claim_id = row.get("claim_id", "")
            if not claim_id:
                continue
            text = sections.get(claim_id, "")
            if word_count(text) < min_words:
                short_claims.append(f"{claim_id} ({word_count(text)} words)")
        if short_claims:
            raise SystemExit(
                f"Result paragraphs below {min_words} words: " + ", ".join(short_claims)
            )

    # Enforce citations appear in Results and references.bib
    bib_path = root / "07_manuscript" / "references.bib"
    bib_keys = set()
    if bib_path.exists():
        for line in bib_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("@") and "{" in line:
                key = line.split("{", 1)[1].split(",", 1)[0].strip()
                if key:
                    bib_keys.add(key)

    missing_citations_in_results = []
    missing_citations_in_bib = []
    for row in claims:
        raw = row.get("citation_keys", "")
        for key in [k.strip().lstrip("@") for k in raw.split(",") if k.strip()]:
            if f"@{key}" not in results_text:
                missing_citations_in_results.append(f"{row.get('claim_id','')}: @{key}")
            if bib_keys and key not in bib_keys:
                missing_citations_in_bib.append(f"{row.get('claim_id','')}: @{key}")
    if missing_citations_in_results:
        raise SystemExit(
            "Results missing citations: " + ", ".join(sorted(set(missing_citations_in_results)))
        )
    if missing_citations_in_bib:
        raise SystemExit(
            "Citations missing in references.bib: " + ", ".join(sorted(set(missing_citations_in_bib)))
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and render manuscript.")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--index", default="07_manuscript/index.qmd", help="Quarto index file")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    repo_root = Path(__file__).resolve().parents[2]

    sys.path.append(str(repo_root / "ma-end-to-end" / "scripts"))
    import validate_pipeline  # type: ignore

    ok, issues = validate_pipeline.validate(root)
    if not ok:
        print("Checklist validation failed. Fix before rendering:")
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(2)

    validate_result_claims(root)
    validate_results_in_manuscript(root)

    index_path = root / args.index
    if not index_path.exists():
        raise SystemExit(f"Missing index file: {index_path}")

    result = subprocess.run(["quarto", "render", str(index_path)], check=False)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
