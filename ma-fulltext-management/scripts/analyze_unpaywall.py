#!/usr/bin/env python3
"""Analyze Unpaywall API results and generate summary statistics.

This script analyzes the CSV output from unpaywall_fetch.py and generates
a summary report of Open Access coverage, types, and retrieval potential.

Usage:
    uv run analyze_unpaywall.py \\
      --in-csv unpaywall_results.csv \\
      --out-md unpaywall_summary.md
"""

import argparse
import csv
import sys
from pathlib import Path


def analyze_unpaywall_results(csv_path):
    """Analyze Unpaywall results CSV.

    Args:
        csv_path: Path to unpaywall_results.csv

    Returns:
        dict: Analysis results with counts and percentages
    """
    total = 0
    oa_count = 0
    closed_count = 0
    pdf_available = 0
    oa_types = {}
    host_types = {}
    licenses = {}

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            total += 1
            is_oa = row.get("is_oa", "").strip()
            oa_status = row.get("oa_status", "").strip()
            pdf_url = row.get("best_oa_pdf_url", "").strip()
            host_type = row.get("host_type", "").strip()
            license_type = row.get("license", "").strip()

            if is_oa == "True":
                oa_count += 1
                if pdf_url:
                    pdf_available += 1
                if oa_status:
                    oa_types[oa_status] = oa_types.get(oa_status, 0) + 1
                if host_type:
                    host_types[host_type] = host_types.get(host_type, 0) + 1
                if license_type:
                    licenses[license_type] = licenses.get(license_type, 0) + 1
            elif is_oa == "False":
                closed_count += 1

    return {
        "total": total,
        "oa_count": oa_count,
        "closed_count": closed_count,
        "pdf_available": pdf_available,
        "oa_types": oa_types,
        "host_types": host_types,
        "licenses": licenses,
    }


def print_summary(results, output_file=None):
    """Print analysis summary to console and optionally to file.

    Args:
        results: Analysis results dict
        output_file: Optional file handle for markdown output
    """
    total = results["total"]
    oa_count = results["oa_count"]
    closed_count = results["closed_count"]
    pdf_available = results["pdf_available"]
    oa_types = results["oa_types"]
    host_types = results["host_types"]
    licenses = results["licenses"]

    # Console output
    print("📊 Unpaywall Analysis Results")
    print("=" * 80)
    print(f"Total records queried: {total}")
    print(f"Open Access (OA): {oa_count} ({oa_count / total * 100:.1f}%)")
    print(f"  - With PDF URL: {pdf_available} ({pdf_available / total * 100:.1f}%)")
    print(f"Closed Access: {closed_count} ({closed_count / total * 100:.1f}%)")
    print()

    if oa_types:
        print("OA Types:")
        for oa_type, count in sorted(oa_types.items(), key=lambda x: -x[1]):
            pct = count / oa_count * 100 if oa_count > 0 else 0
            print(f"  - {oa_type:10s}: {count:3d} ({pct:5.1f}% of OA)")
        print()

    if host_types:
        print("Host Types:")
        for host_type, count in sorted(host_types.items(), key=lambda x: -x[1]):
            pct = count / oa_count * 100 if oa_count > 0 else 0
            print(f"  - {host_type:15s}: {count:3d} ({pct:5.1f}% of OA)")
        print()

    if licenses:
        print("Licenses:")
        for license_type, count in sorted(licenses.items(), key=lambda x: -x[1]):
            pct = count / oa_count * 100 if oa_count > 0 else 0
            print(f"  - {license_type:20s}: {count:3d} ({pct:5.1f}% of OA)")
        print()

    print("📋 Next Steps:")
    print(
        f"  1. PDF retrieval potential: {pdf_available}/{total} ({pdf_available / total * 100:.1f}%)"
    )
    print(f"  2. Need manual retrieval: {closed_count} closed access records")
    print(
        f"  3. Institutional access may help with {oa_count - pdf_available} OA records without PDF URLs"
    )

    # Markdown output
    if output_file:
        output_file.write("# Unpaywall Analysis Summary\n\n")
        output_file.write("## Overview\n\n")
        output_file.write(f"- **Total records**: {total}\n")
        output_file.write(
            f"- **Open Access**: {oa_count} ({oa_count / total * 100:.1f}%)\n"
        )
        output_file.write(
            f"- **With PDF URL**: {pdf_available} ({pdf_available / total * 100:.1f}%)\n"
        )
        output_file.write(
            f"- **Closed Access**: {closed_count} ({closed_count / total * 100:.1f}%)\n"
        )
        output_file.write("\n---\n\n")

        if oa_types:
            output_file.write("## Open Access Types\n\n")
            output_file.write("| OA Type | Count | Percentage |\n")
            output_file.write("|---------|------:|-----------:|\n")
            for oa_type, count in sorted(oa_types.items(), key=lambda x: -x[1]):
                pct = count / oa_count * 100 if oa_count > 0 else 0
                output_file.write(f"| {oa_type} | {count} | {pct:.1f}% |\n")
            output_file.write("\n")

        if host_types:
            output_file.write("## Host Types\n\n")
            output_file.write("| Host Type | Count | Percentage |\n")
            output_file.write("|-----------|------:|-----------:|\n")
            for host_type, count in sorted(host_types.items(), key=lambda x: -x[1]):
                pct = count / oa_count * 100 if oa_count > 0 else 0
                output_file.write(f"| {host_type} | {count} | {pct:.1f}% |\n")
            output_file.write("\n")

        if licenses:
            output_file.write("## Licenses\n\n")
            output_file.write("| License | Count | Percentage |\n")
            output_file.write("|---------|------:|-----------:|\n")
            for license_type, count in sorted(licenses.items(), key=lambda x: -x[1]):
                pct = count / oa_count * 100 if oa_count > 0 else 0
                output_file.write(f"| {license_type} | {count} | {pct:.1f}% |\n")
            output_file.write("\n")

        output_file.write("## Recommendations\n\n")
        output_file.write(
            f"1. **Automated retrieval**: {pdf_available} PDFs available for download\n"
        )
        output_file.write(
            f"2. **Manual retrieval needed**: {closed_count} closed access records\n"
        )
        output_file.write(
            f"3. **Institutional access**: May help retrieve {oa_count - pdf_available} OA records\n"
        )
        output_file.write(
            f"4. **Expected retrieval rate**: "
            f"{(pdf_available + closed_count * 0.5) / total * 100:.1f}% "
            f"(assuming 50% success via institutional access)\n"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Unpaywall results and generate summary",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--in-csv",
        required=True,
        type=Path,
        help="Input CSV from unpaywall_fetch.py",
    )
    parser.add_argument("--out-md", type=Path, help="Optional markdown output file")

    args = parser.parse_args()

    # Validate input
    if not args.in_csv.exists():
        print(f"❌ Error: Input CSV not found: {args.in_csv}", file=sys.stderr)
        sys.exit(1)

    # Analyze results
    results = analyze_unpaywall_results(args.in_csv)

    # Print to console and optionally to markdown
    if args.out_md:
        with open(args.out_md, "w", encoding="utf-8") as f:
            print_summary(results, output_file=f)
        print(f"\n✅ Markdown summary saved to: {args.out_md}")
    else:
        print_summary(results)


if __name__ == "__main__":
    main()
