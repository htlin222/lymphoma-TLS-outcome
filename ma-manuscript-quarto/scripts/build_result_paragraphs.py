#!/usr/bin/env python3
"""Generate Results paragraph stubs from result_claims.csv."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List


def read_claims(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Missing claims CSV: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [{k: (v or "").strip() for k, v in row.items()} for row in reader]


def parse_claim_ids(text: str) -> List[str]:
    ids = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("## "):
            ids.append(line.replace("## ", "").strip())
    return ids


def parse_citation_keys(raw: str) -> List[str]:
    if not raw:
        return []
    keys = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if token.startswith("@"):
            token = token[1:]
        keys.append(token)
    return keys


def format_citations(raw: str) -> str:
    keys = parse_citation_keys(raw)
    if not keys:
        return ""
    return "(" + "; ".join(f"@{k}" for k in keys) + ")"


def build_section(row: Dict[str, str]) -> List[str]:
    claim_id = row.get("claim_id", "")
    lines = [f"### {claim_id}", ""]
    lines.append(f"- Result summary: {row.get('result_summary', '')}")
    lines.append(f"- Outcome: {row.get('outcome', '')}")
    lines.append(f"- Effect measure: {row.get('effect_measure', '')}")
    lines.append(f"- Model: {row.get('model', '')}")
    lines.append(f"- Effect estimate: {row.get('effect_estimate', '')}")
    lines.append(f"- CI: {row.get('ci', '')}")
    lines.append(f"- p-value: {row.get('p_value', '')}")
    lines.append(f"- Heterogeneity (I2): {row.get('heterogeneity_i2', '')}")
    lines.append(f"- Direction: {row.get('direction', '')}")
    lines.append(f"- Figure ref: {row.get('figure_ref', '')}")
    lines.append(f"- Table ref: {row.get('table_ref', '')}")
    lines.append(f"- Citation keys: {row.get('citation_keys', '')}")
    lines.append("")
    lines.append("Draft paragraph:")
    lines.append(
        "Write 2-4 sentences: main effect, uncertainty, heterogeneity, and reference the figure/table."
    )
    lines.append("")
    lines.append("Auto draft paragraph:")
    summary = row.get("result_summary", "").strip()
    outcome = row.get("outcome", "").strip()
    measure = row.get("effect_measure", "").strip()
    model = row.get("model", "").strip()
    estimate = row.get("effect_estimate", "").strip()
    ci = row.get("ci", "").strip()
    p_value = row.get("p_value", "").strip()
    i2 = row.get("heterogeneity_i2", "").strip()
    direction = row.get("direction", "").strip()
    fig = row.get("figure_ref", "").strip()
    tbl = row.get("table_ref", "").strip()
    ref = fig or tbl
    parts = []
    if outcome:
        parts.append(f"For {outcome},")
    if measure and estimate:
        parts.append(f"the pooled {measure} was {estimate}")
    elif estimate:
        parts.append(f"the pooled effect was {estimate}")
    if ci:
        parts.append(f"({ci})")
    if p_value:
        parts.append(f"(p={p_value})")
    citations = format_citations(row.get("citation_keys", ""))
    if citations:
        parts.append(citations)
    if model:
        parts.append(f"using a {model} model")
    sentence = " ".join(parts).strip()
    if sentence:
        sentence = sentence.rstrip(".") + "."
    if summary:
        sentence = summary.rstrip(".") + ". " + sentence if sentence else summary.rstrip(".") + "."
    if direction:
        sentence += f" The effect favored {direction}."
    if i2:
        sentence += f" Heterogeneity was I2={i2}."
    if ref:
        sentence += f" See {ref}."
    lines.append(sentence if sentence else "Draft based on claim fields.")
    lines.append("")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Build result paragraph stubs.")
    parser.add_argument("--claims", default="07_manuscript/result_claims.csv", help="Claims CSV")
    parser.add_argument("--out", default="07_manuscript/result_paragraphs.md", help="Output markdown")
    parser.add_argument("--out-qmd", default="07_manuscript/result_paragraphs.qmd", help="Output Quarto snippet")
    parser.add_argument("--out-summary", default="07_manuscript/result_summary_table.md", help="Summary table output")
    args = parser.parse_args()

    claims = read_claims(Path(args.claims))
    if not claims:
        raise SystemExit("No rows found in result_claims.csv")

    lines = ["# Results Paragraph Stubs", ""]
    for row in claims:
        lines.extend(build_section(row))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n")

    qmd_lines = ["# Results Paragraph Drafts", ""]
    for row in claims:
        claim_id = row.get("claim_id", "")
        qmd_lines.append(f"## {claim_id}")
        summary = row.get("result_summary", "").strip()
        auto_text = ""
        outcome = row.get("outcome", "").strip()
        measure = row.get("effect_measure", "").strip()
        model = row.get("model", "").strip()
        estimate = row.get("effect_estimate", "").strip()
        ci = row.get("ci", "").strip()
        p_value = row.get("p_value", "").strip()
        i2 = row.get("heterogeneity_i2", "").strip()
        direction = row.get("direction", "").strip()
        fig = row.get("figure_ref", "").strip()
        tbl = row.get("table_ref", "").strip()
        ref = fig or tbl
        parts = []
        if outcome:
            parts.append(f"For {outcome},")
        if measure and estimate:
            parts.append(f"the pooled {measure} was {estimate}")
        elif estimate:
            parts.append(f"the pooled effect was {estimate}")
        if ci:
            parts.append(f"({ci})")
    if p_value:
        parts.append(f"(p={p_value})")
    citations = format_citations(row.get("citation_keys", ""))
    if citations:
        parts.append(citations)
    if model:
        parts.append(f"using a {model} model")
        sentence = " ".join(parts).strip()
        if sentence:
            sentence = sentence.rstrip(".") + "."
        if summary:
            sentence = summary.rstrip(".") + ". " + sentence if sentence else summary.rstrip(".") + "."
        if direction:
            sentence += f" The effect favored {direction}."
        if i2:
            sentence += f" Heterogeneity was I2={i2}."
        if ref:
            sentence += f" See {ref}."
        auto_text = sentence if sentence else "Draft based on claim fields."
        qmd_lines.append(auto_text)
        qmd_lines.append("")

    qmd_path = Path(args.out_qmd)
    qmd_path.parent.mkdir(parents=True, exist_ok=True)
    qmd_path.write_text("\n".join(qmd_lines) + "\n")

    # Sanity: ensure each claim ID appears in QMD
    qmd_ids = set(parse_claim_ids("\n".join(qmd_lines)))
    missing_ids = [row.get("claim_id", "") for row in claims if row.get("claim_id", "") not in qmd_ids]
    if missing_ids:
        raise SystemExit("Missing claim IDs in result_paragraphs.qmd: " + ", ".join(missing_ids))

    summary_lines = [
        "# Results Summary Table",
        "",
        "| Claim ID | Outcome | Effect | CI | p-value | I2 | Ref | Citations |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in claims:
        ref = row.get("figure_ref", "") or row.get("table_ref", "")
        citations = "; ".join(f"@{k}" for k in parse_citation_keys(row.get("citation_keys", "")))
        summary_lines.append(
            f"| {row.get('claim_id','')} | {row.get('outcome','')} | {row.get('effect_estimate','')} | {row.get('ci','')} | {row.get('p_value','')} | {row.get('heterogeneity_i2','')} | {ref} | {citations} |"
        )
    summary_path = Path(args.out_summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(summary_lines) + "\n")


if __name__ == "__main__":
    main()
