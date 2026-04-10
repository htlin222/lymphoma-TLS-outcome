#!/usr/bin/env python3
"""Validate extraction CSV for data quality issues."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def _is_missing(value: str) -> bool:
    """Check if a value is effectively missing."""
    return value.strip().upper() in ("", "NR", "NA", "N/A", "MISSING")


def _try_float(value: str) -> float | None:
    """Attempt to parse a numeric value, returning None on failure."""
    v = value.strip()
    if _is_missing(v):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _find_column(headers: list[str], target: str) -> str | None:
    """Case-insensitive column lookup."""
    target_lower = target.lower()
    for h in headers:
        if h.lower() == target_lower:
            return h
    return None


def validate(
    rows: list[dict[str, str]], headers: list[str], critical_fields: list[str]
) -> list[str]:
    """Run all validation checks. Returns list of issue strings."""
    issues: list[str] = []

    # --- 1. Missing study_id ---
    for i, row in enumerate(rows, 1):
        sid_col = _find_column(headers, "study_id")
        if sid_col and _is_missing(row.get(sid_col, "")):
            issues.append(f"Row {i}: missing study_id")

    # --- 2. Duplicate study_id ---
    sid_col = _find_column(headers, "study_id")
    if sid_col:
        seen: dict[str, int] = {}
        for i, row in enumerate(rows, 1):
            val = row.get(sid_col, "").strip()
            if val and not _is_missing(val):
                if val in seen:
                    issues.append(
                        f"Row {i}: duplicate study_id '{val}' (first at row {seen[val]})"
                    )
                else:
                    seen[val] = i

    # --- 3. Missing critical fields ---
    for field in critical_fields:
        col = _find_column(headers, field)
        if not col:
            continue  # field not in CSV — skip silently
        for i, row in enumerate(rows, 1):
            if _is_missing(row.get(col, "")):
                sid = _get_study_label(row, headers, i)
                issues.append(f"{sid}: missing critical field '{field}'")

    # --- 4. CI lower > upper ---
    ci_patterns = re.compile(r"(.+?)_95ci_lower$", re.IGNORECASE)
    for h in headers:
        m = ci_patterns.match(h)
        if not m:
            continue
        prefix = m.group(1)
        upper_col = _find_column(headers, f"{prefix}_95ci_upper")
        if not upper_col:
            continue
        for i, row in enumerate(rows, 1):
            lo = _try_float(row.get(h, ""))
            hi = _try_float(row.get(upper_col, ""))
            if lo is not None and hi is not None and lo > hi:
                sid = _get_study_label(row, headers, i)
                issues.append(f"{sid}: CI lower ({lo}) > upper ({hi}) for '{prefix}'")

    # --- 5. Percentages out of 0-100 ---
    pct_cols = [h for h in headers if h.lower().endswith(("_percent", "_pct"))]
    for col in pct_cols:
        for i, row in enumerate(rows, 1):
            val = _try_float(row.get(col, ""))
            if val is not None and (val < 0 or val > 100):
                sid = _get_study_label(row, headers, i)
                issues.append(f"{sid}: '{col}' = {val} outside 0-100 range")

    # --- 6. Sample size mismatch (n_total vs n_intervention + n_control) ---
    total_col = _find_column(headers, "n_randomized_total")
    int_col = _find_column(headers, "n_intervention")
    ctrl_col = _find_column(headers, "n_control")
    if total_col and int_col and ctrl_col:
        for i, row in enumerate(rows, 1):
            n_total = _try_float(row.get(total_col, ""))
            n_int = _try_float(row.get(int_col, ""))
            n_ctrl = _try_float(row.get(ctrl_col, ""))
            if n_total is not None and n_int is not None and n_ctrl is not None:
                expected = n_int + n_ctrl
                if expected > 0 and abs(n_total - expected) / expected > 0.05:
                    sid = _get_study_label(row, headers, i)
                    issues.append(
                        f"{sid}: n_randomized_total ({int(n_total)}) != "
                        f"n_intervention ({int(n_int)}) + n_control ({int(n_ctrl)}) "
                        f"(>5% difference)"
                    )

    return issues


def _get_study_label(row: dict[str, str], headers: list[str], row_num: int) -> str:
    """Return a human-readable label for a row."""
    sid_col = _find_column(headers, "study_id")
    if sid_col:
        val = row.get(sid_col, "").strip()
        if val and not _is_missing(val):
            return val
    return f"Row {row_num}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate extraction CSV")
    parser.add_argument("--csv", required=True, help="Extraction CSV to validate")
    parser.add_argument(
        "--data-dict", default=None, help="Data dictionary for critical fields"
    )
    parser.add_argument(
        "--out-md", required=True, help="Output validation report (markdown)"
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    out_path = Path(args.out_md)

    if not csv_path.exists():
        raise SystemExit(f"Extraction CSV not found: {csv_path}")

    # Load critical fields
    critical: list[str] = []
    if args.data_dict:
        dd_path = Path(args.data_dict)
        if dd_path.exists():
            from extraction_utils import load_critical_fields

            critical = load_critical_fields(dd_path)
    if not critical:
        # Fallback: minimal set that every extraction should have
        critical = ["study_id"]

    # Read CSV
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        headers = list(reader.fieldnames or [])
        rows = list(reader)

    if not rows:
        raise SystemExit(f"Extraction CSV is empty: {csv_path}")

    issues = validate(rows, headers, critical)

    # Build report
    lines = [
        "# Extraction Validation Report",
        "",
        f"**File**: {csv_path}",
        f"**Studies**: {len(rows)}",
        f"**Fields**: {len(headers)}",
        f"**Critical fields checked**: {len(critical)}",
        "",
    ]

    if issues:
        lines.append(f"## Issues Found ({len(issues)})")
        lines.append("")
        for issue in issues:
            lines.append(f"- {issue}")
    else:
        lines.append("## No Issues Found")
        lines.append("")
        lines.append("All validation checks passed.")

    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Validated {len(rows)} studies, {len(headers)} fields")
    if issues:
        print(f"Found {len(issues)} issue(s) — see {out_path}")
        raise SystemExit(2)
    else:
        print("All checks passed")


if __name__ == "__main__":
    main()
