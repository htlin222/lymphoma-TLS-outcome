#!/usr/bin/env python3
"""Validate that extracted studies have source references to full texts."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


def read_extraction_studies(path: Path) -> Set[str]:
    if not path.exists():
        raise SystemExit(f"Missing extraction CSV: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if "study_id" not in (reader.fieldnames or []):
            raise SystemExit("extraction.csv missing study_id column")
        return {row.get("study_id", "").strip() for row in reader if row.get("study_id", "").strip()}


def read_sources_csv(path: Path) -> Tuple[List[Dict[str, str]], Optional[str]]:
    if not path.exists():
        return [], "missing_source_csv"
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if "study_id" not in (reader.fieldnames or []):
            return [], "missing_study_id_column"
        rows = [{k: (v or "").strip() for k, v in row.items()} for row in reader]
        return rows, None


def read_sources_db(path: Path) -> Tuple[List[Dict[str, str]], Optional[str]]:
    if not path.exists():
        return [], "missing_source_db"
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("SELECT study_id, file_path, page_reference, notes FROM source")
        rows = [
            {
                "study_id": (row[0] or "").strip(),
                "file_path": (row[1] or "").strip(),
                "page_reference": (row[2] or "").strip(),
                "notes": (row[3] or "").strip(),
            }
            for row in cur.fetchall()
        ]
        conn.close()
        return rows, None
    except Exception as exc:
        return [], f"db_error: {exc.__class__.__name__}"


def summarize(
    studies: Set[str],
    sources: List[Dict[str, str]],
    min_sources: int,
    base_dir: Path,
) -> Dict[str, object]:
    counts: Dict[str, int] = {study: 0 for study in studies}
    missing_files = 0
    missing_pages = 0

    for row in sources:
        study_id = row.get("study_id", "")
        if not study_id:
            continue
        if study_id not in counts:
            counts[study_id] = 0
        counts[study_id] += 1
        file_path = row.get("file_path", "")
        if file_path:
            path_obj = Path(file_path)
            if not path_obj.is_absolute():
                path_obj = (base_dir / path_obj).resolve()
            if not path_obj.exists():
                missing_files += 1
        if not row.get("page_reference", "").strip():
            missing_pages += 1

    missing_source = [study for study, count in counts.items() if count < min_sources]
    return {
        "studies": len(studies),
        "sources_rows": len(sources),
        "studies_missing_source": missing_source,
        "missing_files": missing_files,
        "missing_page_reference": missing_pages,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate extraction source references.")
    parser.add_argument("--extraction", default="05_extraction/extraction.csv", help="Extraction CSV")
    parser.add_argument("--source-csv", default="05_extraction/source.csv", help="Source CSV")
    parser.add_argument("--source-db", default="05_extraction/extraction.sqlite", help="Source SQLite DB")
    parser.add_argument("--min-sources", type=int, default=1, help="Minimum sources per study")
    parser.add_argument("--out", default="05_extraction/source_validation.md", help="Output report")
    parser.add_argument("--out-json", default=None, help="Output JSON report")
    args = parser.parse_args()

    extraction_path = Path(args.extraction)
    studies = read_extraction_studies(extraction_path)

    source_rows, source_issue = read_sources_csv(Path(args.source_csv))
    source_origin = "source.csv"
    if source_issue:
        source_rows, source_issue = read_sources_db(Path(args.source_db))
        source_origin = "extraction.sqlite"

    if source_issue:
        raise SystemExit(f"No source records available: {source_issue}")

    if Path(args.source_csv).exists():
        base_dir = Path(args.source_csv).resolve().parent
    elif Path(args.source_db).exists():
        base_dir = Path(args.source_db).resolve().parent
    else:
        base_dir = Path.cwd()
    summary = summarize(studies, source_rows, args.min_sources, base_dir)
    missing_source = summary["studies_missing_source"]
    missing_files = summary["missing_files"]
    missing_pages = summary["missing_page_reference"]

    lines = [
        "# Source Validation Report",
        "",
        f"Extraction file: {extraction_path}",
        f"Source input: {source_origin}",
        f"Studies in extraction: {summary['studies']}",
        f"Source rows: {summary['sources_rows']}",
        f"Missing source entries: {len(missing_source)}",
        f"Missing source files: {missing_files}",
        f"Missing page references: {missing_pages}",
        "",
        "## Studies Missing Source Entries",
    ]
    if missing_source:
        for study in missing_source:
            lines.append(f"- {study}")
    else:
        lines.append("- None")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n")

    if args.out_json:
        json_path = Path(args.out_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(summary, indent=2) + "\n")

    if missing_source or missing_files:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
