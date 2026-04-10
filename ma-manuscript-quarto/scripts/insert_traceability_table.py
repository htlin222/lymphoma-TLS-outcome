#!/usr/bin/env python3
"""Insert a traceability table into 02_methods.qmd."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


START = "<!-- TRACEABILITY_TABLE_START -->"
END = "<!-- TRACEABILITY_TABLE_END -->"
NARR_START = "<!-- TRACEABILITY_NARRATIVE_START -->"
NARR_END = "<!-- TRACEABILITY_NARRATIVE_END -->"


def read_kv(path: Path, key: str) -> Optional[int]:
    if not path.exists():
        return None
    pattern = re.compile(rf"^{re.escape(key)}\s*:\s*(\d+)")
    for line in path.read_text().splitlines():
        match = pattern.match(line.strip())
        if match:
            return int(match.group(1))
    return None


def read_db_total(path: Path) -> Optional[int]:
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if (row.get("database") or "").strip().lower() == "total":
                try:
                    return int(row.get("retrieved", "0"))
                except ValueError:
                    return None
    return None


def count_decisions(path: Path, column: str) -> Dict[str, int]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or column not in reader.fieldnames:
            return {}
        counts: Dict[str, int] = {}
        for row in reader:
            decision = (row.get(column) or "").strip().lower()
            if not decision:
                continue
            counts[decision] = counts.get(decision, 0) + 1
        return counts


def count_fulltext(path: Path) -> Optional[int]:
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "file_path" not in reader.fieldnames:
            return None
        count = 0
        for row in reader:
            if (row.get("file_path") or "").strip():
                count += 1
        return count


def build_table(root: Path, round_name: str, decisions_column: str) -> tuple[str, List[tuple]]:
    protocol_dir = root / "01_protocol"
    search_dir = root / "02_search" / round_name
    screening_dir = root / "03_screening" / round_name

    db_total = read_db_total(search_dir / "db_counts.csv")
    dedupe = read_kv(search_dir / "dedupe.log", "deduped_records")
    decisions = count_decisions(screening_dir / "decisions.csv", decisions_column)
    screened_total = sum(decisions.values()) if decisions else None
    included = decisions.get("include") if decisions else None
    fulltext = count_fulltext(root / "04_fulltext" / "manifest.csv")

    def fmt(value: Optional[int]) -> str:
        return str(value) if value is not None else "NA"

    rows = [
        ("Protocol", "PICO defined", "yes" if (protocol_dir / "pico.yaml").exists() else "no", "01_protocol/pico.yaml"),
        ("Protocol", "Eligibility criteria", "yes" if (protocol_dir / "eligibility.md").exists() else "no", "01_protocol/eligibility.md"),
        ("Search", "Records identified", fmt(db_total), f"02_search/{round_name}/db_counts.csv"),
        ("Search", "Records after deduplication", fmt(dedupe), f"02_search/{round_name}/dedupe.log"),
        ("Screening", "Records screened", fmt(screened_total), f"03_screening/{round_name}/decisions.csv"),
        ("Screening", "Records included", fmt(included), f"03_screening/{round_name}/decisions.csv"),
        ("Inclusion", "Reports assessed (full text)", fmt(fulltext), "04_fulltext/manifest.csv"),
        ("Inclusion", "Studies included", fmt(included), f"03_screening/{round_name}/decisions.csv"),
    ]

    lines = [
        "### Traceability Table",
        "",
        "| Stage | Artifact | Count/Status | Source |",
        "| --- | --- | --- | --- |",
    ]
    for stage, artifact, count, source in rows:
        lines.append(f"| {stage} | {artifact} | {count} | `{source}` |")
    return "\n".join(lines), rows


def build_methods_paragraph(rows: List[tuple]) -> str:
    parts = []
    for stage, artifact, count, _ in rows:
        if stage == "Search" and artifact == "Records identified":
            if count != "NA":
                parts.append(f"We identified {count} records across all databases.")
        if stage == "Search" and artifact == "Records after deduplication":
            if count != "NA":
                parts.append(f"After deduplication, {count} records remained for screening.")
        if stage == "Screening" and artifact == "Records screened":
            if count != "NA":
                parts.append(f"We screened {count} records at title/abstract level.")
        if stage == "Screening" and artifact == "Records included":
            if count != "NA":
                parts.append(f"{count} records met inclusion criteria after screening.")
        if stage == "Inclusion" and artifact == "Reports assessed (full text)":
            if count != "NA":
                parts.append(f"{count} full-text reports were assessed for eligibility.")
        if stage == "Inclusion" and artifact == "Studies included":
            if count != "NA":
                parts.append(f"We included {count} studies in the final synthesis.")
    if not parts:
        return "Traceability counts were summarized in Table X."
    return " ".join(parts)


def insert_narrative(text: str, narrative: str, insert_before: str) -> str:
    if NARR_START in text and NARR_END in text:
        prefix = text.split(NARR_START)[0]
        suffix = text.split(NARR_END)[1]
        return prefix + NARR_START + "\n" + narrative + "\n" + NARR_END + suffix
    if insert_before in text:
        parts = text.split(insert_before)
        head = parts[0]
        tail = insert_before.join(parts[1:])
        block = NARR_START + "\n" + narrative + "\n" + NARR_END + "\n\n"
        return head + block + insert_before + tail
    return text + "\n" + NARR_START + "\n" + narrative + "\n" + NARR_END + "\n"


def insert_block(methods_text: str, block: str, narrative: str) -> str:
    if START in methods_text and END in methods_text:
        updated = insert_narrative(methods_text, narrative, START)
        prefix = updated.split(START)[0]
        suffix = updated.split(END)[1]
        return prefix + START + "\n" + block + "\n" + END + suffix

    marker = "## Study Selection"
    if marker in methods_text:
        parts = methods_text.split(marker)
        head = parts[0] + marker
        tail = marker.join(parts[1:])
        updated = head + "\n\n" + START + "\n" + block + "\n" + END + "\n" + tail
        if narrative:
            updated = insert_narrative(updated, narrative, START)
        return updated

    return methods_text.rstrip() + "\n\n" + START + "\n" + block + "\n" + END + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Insert traceability table into Methods.")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--round", default="round-01", help="Search/screening round")
    parser.add_argument("--methods", default="07_manuscript/02_methods.qmd", help="Methods file")
    parser.add_argument("--decisions-column", default="final_decision", help="Decision column")
    parser.add_argument("--out-table", default="07_manuscript/traceability_table.md", help="Table output")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    block, rows = build_table(root, args.round, args.decisions_column)
    narrative = build_methods_paragraph(rows)

    out_table = root / args.out_table
    out_table.parent.mkdir(parents=True, exist_ok=True)
    out_table.write_text(block + "\n")

    methods_path = root / args.methods
    if not methods_path.exists():
        raise SystemExit(f"Missing methods file: {methods_path}")
    updated = insert_block(methods_path.read_text(), block, narrative)
    methods_path.write_text(updated + "\n")


if __name__ == "__main__":
    main()
