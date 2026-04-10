#!/usr/bin/env python3
"""Generate a PRISMA flow summary from project artifacts."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def read_kv(path: Path, key: str) -> int | None:
    if not path.exists():
        return None
    pattern = re.compile(rf"^{re.escape(key)}\s*:\s*(\d+)")
    for line in path.read_text().splitlines():
        match = pattern.match(line.strip())
        if match:
            return int(match.group(1))
    return None


def count_decisions(path: Path, column: str) -> dict[str, int]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if column not in reader.fieldnames:
            return {}
        counts: dict[str, int] = {}
        for row in reader:
            decision = row.get(column, "").strip().lower()
            if not decision:
                continue
            counts[decision] = counts.get(decision, 0) + 1
        return counts


def count_fulltext(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if "file_path" not in reader.fieldnames:
            return None
        count = 0
        for row in reader:
            if row.get("file_path", "").strip():
                count += 1
        return count


def build_prisma_summary(
    root: Path,
    round_name: str,
    decisions_column: str,
    out_md: Path,
    strict: bool = False,
) -> dict[str, str]:
    search_log = root / "02_search" / round_name / "log.md"
    dedupe_log = root / "02_search" / round_name / "dedupe.log"
    decisions_csv = root / "03_screening" / round_name / "decisions.csv"
    manifest_csv = root / "04_fulltext" / "manifest.csv"

    records_identified = read_kv(search_log, "count")
    db_counts_csv = root / "02_search" / round_name / "db_counts.csv"
    db_total = None
    if db_counts_csv.exists():
        try:
            import csv

            with db_counts_csv.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                total = 0
                for row in reader:
                    if row.get("database") == "total":
                        value = row.get("retrieved", "")
                        try:
                            total = int(value)
                        except ValueError:
                            total = None
                        break
                    value = row.get("retrieved", "")
                    if value and value != "NA":
                        total += int(value)
                db_total = total
        except Exception:
            db_total = None

    if db_total is not None:
        records_identified = db_total
    records_after_dedupe = read_kv(dedupe_log, "deduped_records")

    decisions = count_decisions(decisions_csv, decisions_column)
    included = decisions.get("include", 0)
    excluded = decisions.get("exclude", 0)
    maybe = decisions.get("maybe", 0)

    fulltext_count = count_fulltext(manifest_csv)

    def fmt(value: int | None) -> str:
        return str(value) if value is not None else "NA"

    counts = {
        "records_identified": fmt(records_identified),
        "records_after_dedupe": fmt(records_after_dedupe),
        "records_screened": fmt(records_after_dedupe),
        "records_excluded": str(excluded),
        "reports_sought": str(included + maybe),
        "reports_assessed": fmt(fulltext_count),
        "studies_included": str(included),
    }

    if strict:
        missing = [key for key, value in counts.items() if value == "NA"]
        if missing:
            raise SystemExit(f"PRISMA counts missing: {', '.join(missing)}")

    lines = [
        "# PRISMA Flow Summary",
        "",
        "## Counts",
        "",
        f"- Records identified: {counts['records_identified']}",
        f"- Records after deduplication: {counts['records_after_dedupe']}",
        f"- Records screened: {counts['records_screened']}",
        f"- Records excluded: {counts['records_excluded']}",
        f"- Reports sought for retrieval: {counts['reports_sought']}",
        f"- Reports assessed for eligibility: {counts['reports_assessed']}",
        f"- Studies included: {counts['studies_included']}",
        "",
        "## Mermaid Diagram",
        "",
        "```mermaid",
        "flowchart TD",
        f"A[Records identified (n={counts['records_identified']})] --> B[Records after deduplication (n={counts['records_after_dedupe']})]",
        f"B --> C[Records screened (n={counts['records_screened']})]",
        f"C --> D[Records excluded (n={counts['records_excluded']})]",
        f"C --> E[Reports sought for retrieval (n={counts['reports_sought']})]",
        f"E --> F[Reports assessed for eligibility (n={counts['reports_assessed']})]",
        f"F --> G[Studies included (n={counts['studies_included']})]",
        "```",
        "",
        "## Notes",
        "- If any counts show NA, populate the missing logs or override manually.",
    ]

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n")
    return counts


def render_svg(out_path: Path, counts: dict[str, str]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    width = 900
    height = 700
    box_w = 360
    box_h = 60
    x = (width - box_w) // 2
    y = 40
    y_gap = 80

    labels = [
        ("Records identified", counts.get("records_identified", "NA")),
        ("Records after deduplication", counts.get("records_after_dedupe", "NA")),
        ("Records screened", counts.get("records_screened", "NA")),
        ("Records excluded", counts.get("records_excluded", "NA")),
        ("Reports sought for retrieval", counts.get("reports_sought", "NA")),
        ("Reports assessed for eligibility", counts.get("reports_assessed", "NA")),
        ("Studies included", counts.get("studies_included", "NA")),
    ]

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<style>',
        '.box { fill: #f7f7f7; stroke: #333; stroke-width: 1; }',
        '.text { font-family: Arial, sans-serif; font-size: 14px; }',
        '.line { stroke: #333; stroke-width: 1; }',
        '</style>',
    ]

    positions = []
    for idx, (title, count) in enumerate(labels):
        box_y = y + idx * y_gap
        positions.append((x, box_y))
        svg_lines.append(f'<rect class="box" x="{x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="6" ry="6"/>')
        svg_lines.append(
            f'<text class="text" x="{x + 12}" y="{box_y + 24}">{title}</text>'
        )
        svg_lines.append(
            f'<text class="text" x="{x + 12}" y="{box_y + 44}">n={count}</text>'
        )

        if idx > 0:
            prev_x, prev_y = positions[idx - 1]
            svg_lines.append(
                f'<line class="line" x1="{prev_x + box_w/2}" y1="{prev_y + box_h}" '
                f'x2="{x + box_w/2}" y2="{box_y}" />'
            )

    svg_lines.append("</svg>")
    out_path.write_text("\n".join(svg_lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PRISMA flow markdown.")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--round", default="round-01", help="Search/screening round")
    parser.add_argument("--decisions-column", default="final_decision", help="Decision column name")
    parser.add_argument("--out", required=True, help="Output markdown file")
    parser.add_argument("--out-svg", default=None, help="Optional SVG output path")
    parser.add_argument("--strict", action="store_true", help="Fail if any counts are NA")
    args = parser.parse_args()

    root = Path(args.root)
    round_name = args.round

    counts = build_prisma_summary(
        root,
        round_name,
        args.decisions_column,
        Path(args.out),
        strict=args.strict,
    )

    if args.out_svg:
        render_svg(Path(args.out_svg), counts)


if __name__ == "__main__":
    main()
