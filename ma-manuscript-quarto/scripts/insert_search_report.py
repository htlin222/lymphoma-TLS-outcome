#!/usr/bin/env python3
"""Insert the search report into the Methods section."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

START = "<!-- SEARCH_REPORT_START -->"
END = "<!-- SEARCH_REPORT_END -->"


def load_report(report_path: Path) -> str:
    if not report_path.exists():
        raise SystemExit(f"Missing search report: {report_path}")
    lines = report_path.read_text().splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        if lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).strip()


def load_audit(audit_path: Path) -> str:
    if not audit_path.exists():
        raise SystemExit(f"Missing search audit: {audit_path}")
    data = json.loads(audit_path.read_text())
    databases = data.get("databases", [])
    lines = ["### Search Audit Hashes", ""]
    if not databases:
        lines.append("(missing)")
        return "\n".join(lines).strip()
    for entry in databases:
        db = entry.get("database", "unknown")
        qh = entry.get("query_hash", "")
        lines.append(f"- {db}: `{qh}`")
    return "\n".join(lines).strip()


def build_block(report_text: str, audit_text: str) -> str:
    return "\n".join(
        [
            START,
            "### Search Report",
            report_text,
            "",
            audit_text,
            END,
        ]
    )


def insert_block(methods_text: str, block: str) -> str:
    if START in methods_text and END in methods_text:
        prefix = methods_text.split(START)[0]
        suffix = methods_text.split(END)[1]
        return prefix + block + suffix

    marker = "## Information Sources and Search Strategy"
    if marker in methods_text:
        parts = methods_text.split(marker)
        head = parts[0] + marker
        tail = marker.join(parts[1:])
        return head + "\n\n" + block + "\n" + tail

    return methods_text.rstrip() + "\n\n" + marker + "\n\n" + block + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Insert search report into Methods.")
    parser.add_argument("--methods", default="07_manuscript/02_methods.qmd", help="Methods file")
    parser.add_argument("--report", default="02_search/round-01/search_report.md", help="Search report")
    parser.add_argument("--audit", default="02_search/round-01/search_audit.json", help="Search audit JSON")
    args = parser.parse_args()

    methods_path = Path(args.methods)
    report_text = load_report(Path(args.report))
    audit_text = load_audit(Path(args.audit))

    if not methods_path.exists():
        raise SystemExit(f"Missing methods file: {methods_path}")

    updated = insert_block(methods_path.read_text(), build_block(report_text, audit_text))
    methods_path.write_text(updated + "\n")


if __name__ == "__main__":
    main()
