#!/usr/bin/env python3
"""Lint and format QMD/MD files for Quarto manuscript best practices."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Lint rule definitions
# ---------------------------------------------------------------------------

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"
SEVERITY_STYLE = "style"

RULES = {
    "L001": ("Cross-ref label uses underscores instead of hyphens", SEVERITY_ERROR),
    "L002": ("Cross-ref label has uppercase characters", SEVERITY_ERROR),
    "L003": ("Figure without #fig- label", SEVERITY_WARNING),
    "L004": ("Table caption without #tbl- label", SEVERITY_WARNING),
    "L005": (
        "Citation uses footnote superscript numbers instead of [@key]",
        SEVERITY_WARNING,
    ),
    "L006": ("\\newpage instead of {{< pagebreak >}}", SEVERITY_WARNING),
    "L007": ("Bare URL not wrapped in <url> or markdown link", SEVERITY_WARNING),
    "L008": ("Trailing whitespace", SEVERITY_STYLE),
    "L009": ("No blank line before heading", SEVERITY_STYLE),
    "L010": ("Inconsistent heading hierarchy (skipped level)", SEVERITY_WARNING),
    "L011": ("Missing YAML frontmatter in .qmd file", SEVERITY_ERROR),
    "L012": ("Bibliography file referenced but not found", SEVERITY_ERROR),
    "L013": ("Include file referenced but not found", SEVERITY_ERROR),
    "L014": ("Figure file referenced but not found", SEVERITY_WARNING),
    "L015": ("Double blank lines", SEVERITY_STYLE),
}

# Fixable rules
FIXABLE = {"L006", "L008", "L009", "L015"}

# Regex patterns
RE_CROSSREF_LABEL = re.compile(r"\{#(fig-|tbl-|sec-|eq-|lst-|thm-|lem-|def-)([^}]+)\}")
RE_FIGURE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
RE_TABLE_CAPTION = re.compile(r"^:\s+(.+?)(?:\s+\{[^}]*\})?\s*$")
RE_TABLE_LABEL = re.compile(r"\{[^}]*#tbl-[^}]*\}")
RE_FOOTNOTE_SUPERSCRIPT = re.compile(r"[\u00b9\u00b2\u00b3\u2074-\u2079\u2070\u2071]+")
RE_NEWPAGE = re.compile(r"\\newpage\b")
RE_BARE_URL = re.compile(r"(?<![(<\[\"'])(?:https?://[^\s)>\]\"']+)(?![)>\]\"'])")
RE_HEADING = re.compile(r"^(#{1,6})\s")
RE_YAML_FENCE = re.compile(r"^---\s*$")
RE_INCLUDE = re.compile(r"\{\{<\s*include\s+(\S+)\s*>\}\}")
RE_BIB_KEY = re.compile(r"^bibliography:\s*(.+)$", re.MULTILINE)


# ---------------------------------------------------------------------------
# Diagnostic type
# ---------------------------------------------------------------------------


class Diagnostic:
    __slots__ = ("rule", "line", "col", "message", "severity")

    def __init__(self, rule: str, line: int, message: str, severity: str, col: int = 0):
        self.rule = rule
        self.line = line
        self.col = col
        self.message = message
        self.severity = severity

    def __repr__(self) -> str:
        return f"L{self.line}:{self.col} [{self.rule}] {self.message}"


# ---------------------------------------------------------------------------
# Lint checks
# ---------------------------------------------------------------------------


def lint_file(path: Path) -> list[Diagnostic]:
    """Run all lint checks on a single file."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    diagnostics: list[Diagnostic] = []

    is_qmd = path.suffix == ".qmd"
    base_dir = path.parent

    # Track state
    in_yaml = False
    yaml_started = False
    yaml_ended = False
    yaml_content = ""
    prev_heading_level = 0
    in_code_block = False

    for i, line in enumerate(lines):
        lineno = i + 1

        # Track fenced code blocks
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Track YAML frontmatter
        if i == 0 and RE_YAML_FENCE.match(line):
            in_yaml = True
            yaml_started = True
            continue
        if in_yaml:
            if RE_YAML_FENCE.match(line):
                in_yaml = False
                yaml_ended = True
            else:
                yaml_content += line + "\n"
            continue

        # L001: Cross-ref labels with underscores
        for m in RE_CROSSREF_LABEL.finditer(line):
            label_body = m.group(2)
            if "_" in label_body:
                diagnostics.append(
                    Diagnostic(
                        "L001",
                        lineno,
                        f"Label '#{m.group(1)}{label_body}' uses underscores; use hyphens",
                        SEVERITY_ERROR,
                        m.start(),
                    )
                )

        # L002: Cross-ref labels with uppercase
        for m in RE_CROSSREF_LABEL.finditer(line):
            label_body = m.group(2)
            if label_body != label_body.lower():
                diagnostics.append(
                    Diagnostic(
                        "L002",
                        lineno,
                        f"Label '#{m.group(1)}{label_body}' has uppercase; use lowercase only",
                        SEVERITY_ERROR,
                        m.start(),
                    )
                )

        # L003: Figure without #fig- label
        for m in RE_FIGURE.finditer(line):
            rest = line[m.end() :]
            if not re.match(r"\s*\{[^}]*#fig-", rest):
                diagnostics.append(
                    Diagnostic(
                        "L003",
                        lineno,
                        f"Figure '{m.group(2)}' missing {{#fig-label}}",
                        SEVERITY_WARNING,
                        m.start(),
                    )
                )

        # L004: Table caption without #tbl- label
        if RE_TABLE_CAPTION.match(line) and not RE_TABLE_LABEL.search(line):
            # Only flag lines that look like standalone table captions
            # (start with ": " and previous lines had table content)
            if i > 0 and ("|" in lines[i - 1] or "+" in lines[i - 1]):
                diagnostics.append(
                    Diagnostic(
                        "L004",
                        lineno,
                        "Table caption missing {#tbl-label}",
                        SEVERITY_WARNING,
                    )
                )

        # L005: Footnote superscript numbers
        for m in RE_FOOTNOTE_SUPERSCRIPT.finditer(line):
            diagnostics.append(
                Diagnostic(
                    "L005",
                    lineno,
                    f"Superscript number '{m.group()}' -- use [@citation-key] instead",
                    SEVERITY_WARNING,
                    m.start(),
                )
            )

        # L006: \newpage
        for m in RE_NEWPAGE.finditer(line):
            diagnostics.append(
                Diagnostic(
                    "L006",
                    lineno,
                    "Use {{< pagebreak >}} instead of \\newpage",
                    SEVERITY_WARNING,
                    m.start(),
                )
            )

        # L007: Bare URL
        for m in RE_BARE_URL.finditer(line):
            url = m.group()
            # Skip URLs inside include shortcodes and YAML
            if "{{<" in line or line.strip().startswith("#"):
                continue
            diagnostics.append(
                Diagnostic(
                    "L007",
                    lineno,
                    f"Bare URL: wrap in <{url}> or [text]({url})",
                    SEVERITY_WARNING,
                    m.start(),
                )
            )

        # L008: Trailing whitespace
        if line != line.rstrip():
            diagnostics.append(
                Diagnostic(
                    "L008",
                    lineno,
                    "Trailing whitespace",
                    SEVERITY_STYLE,
                    len(line.rstrip()),
                )
            )

        # L009: No blank line before heading
        heading_match = RE_HEADING.match(line)
        if heading_match and i > 0 and lines[i - 1].strip() != "":
            # Allow headings at line 1 or after YAML fence
            if not (i > 0 and RE_YAML_FENCE.match(lines[i - 1])):
                diagnostics.append(
                    Diagnostic(
                        "L009",
                        lineno,
                        "Add a blank line before heading",
                        SEVERITY_STYLE,
                    )
                )

        # L010: Skipped heading level
        if heading_match:
            level = len(heading_match.group(1))
            if prev_heading_level > 0 and level > prev_heading_level + 1:
                diagnostics.append(
                    Diagnostic(
                        "L010",
                        lineno,
                        f"Heading jumps from h{prev_heading_level} to h{level}",
                        SEVERITY_WARNING,
                    )
                )
            prev_heading_level = level

        # L013: Include file not found
        for m in RE_INCLUDE.finditer(line):
            inc_path = base_dir / m.group(1)
            if not inc_path.exists():
                diagnostics.append(
                    Diagnostic(
                        "L013",
                        lineno,
                        f"Include file not found: {m.group(1)}",
                        SEVERITY_ERROR,
                        m.start(),
                    )
                )

        # L014: Figure file not found
        for m in RE_FIGURE.finditer(line):
            fig_path = base_dir / m.group(2)
            if not fig_path.exists() and not m.group(2).startswith("http"):
                diagnostics.append(
                    Diagnostic(
                        "L014",
                        lineno,
                        f"Figure file not found: {m.group(2)}",
                        SEVERITY_WARNING,
                        m.start(),
                    )
                )

        # L015: Double blank lines
        if i > 0 and line.strip() == "" and lines[i - 1].strip() == "":
            # Only flag the second blank line
            if i > 1 and lines[i - 2].strip() != "":
                pass  # First double is OK to flag once
            diagnostics.append(
                Diagnostic(
                    "L015",
                    lineno,
                    "Consecutive blank lines; collapse to single",
                    SEVERITY_STYLE,
                )
            )

    # L011: Missing YAML frontmatter in .qmd
    # Skip section include files (00_abstract.qmd, 01_introduction.qmd, etc.)
    is_section_include = re.match(r"^\d{2}_", path.name)
    if is_qmd and not yaml_started and not is_section_include:
        diagnostics.append(
            Diagnostic(
                "L011",
                1,
                "QMD file missing YAML frontmatter (---)",
                SEVERITY_ERROR,
            )
        )

    # L012: Bibliography file not found
    if yaml_content:
        bib_match = RE_BIB_KEY.search(yaml_content)
        if bib_match:
            bib_val = bib_match.group(1).strip().strip('"').strip("'")
            bib_path = base_dir / bib_val
            if not bib_path.exists():
                diagnostics.append(
                    Diagnostic(
                        "L012",
                        1,
                        f"Bibliography file not found: {bib_val}",
                        SEVERITY_ERROR,
                    )
                )

    return diagnostics


# ---------------------------------------------------------------------------
# Auto-fix
# ---------------------------------------------------------------------------


def fix_file(path: Path) -> tuple[int, str]:
    """Apply auto-fixes and return (fix_count, fixed_text)."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    fixed_lines: list[str] = []
    fixes = 0
    in_code_block = False
    in_yaml = False
    yaml_started = False

    for i, line in enumerate(lines):
        # Track fenced code blocks
        if line.startswith("```"):
            in_code_block = not in_code_block
            fixed_lines.append(line)
            continue
        if in_code_block:
            fixed_lines.append(line)
            continue

        # Track YAML frontmatter
        if i == 0 and RE_YAML_FENCE.match(line):
            in_yaml = True
            yaml_started = True
            fixed_lines.append(line)
            continue
        if in_yaml:
            if RE_YAML_FENCE.match(line):
                in_yaml = False
            fixed_lines.append(line)
            continue

        original = line

        # L006: \newpage -> {{< pagebreak >}}
        if RE_NEWPAGE.search(line):
            line = RE_NEWPAGE.sub("{{< pagebreak >}}", line)

        # L008: Trailing whitespace
        line = line.rstrip()

        # L009: No blank line before heading
        if RE_HEADING.match(line) and fixed_lines and fixed_lines[-1].strip() != "":
            fixed_lines.append("")
            fixes += 1

        # L015: Double blank lines
        if line.strip() == "" and fixed_lines and fixed_lines[-1].strip() == "":
            if original != line:
                fixes += 1
            continue

        if original != line:
            fixes += 1

        fixed_lines.append(line)

    return fixes, "\n".join(fixed_lines)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def format_report(results: dict[Path, list[Diagnostic]]) -> str:
    """Generate a markdown lint report."""
    lines = ["# QMD Lint Report", ""]

    total_errors = 0
    total_warnings = 0
    total_style = 0

    for path, diags in sorted(results.items()):
        if not diags:
            continue
        lines.append(f"## `{path}`")
        lines.append("")
        lines.append("| Line | Rule | Severity | Message |")
        lines.append("|-----:|------|----------|---------|")
        for d in sorted(diags, key=lambda x: x.line):
            fix_hint = " (fixable)" if d.rule in FIXABLE else ""
            lines.append(
                f"| {d.line} | {d.rule} | {d.severity}{fix_hint} | {d.message} |"
            )
            if d.severity == SEVERITY_ERROR:
                total_errors += 1
            elif d.severity == SEVERITY_WARNING:
                total_warnings += 1
            else:
                total_style += 1
        lines.append("")

    # Summary
    total = total_errors + total_warnings + total_style
    lines.insert(
        2,
        f"**{total} issues**: {total_errors} errors, {total_warnings} warnings, {total_style} style",
    )
    lines.insert(3, "")

    if total == 0:
        lines.insert(2, "All files clean.")
        lines.insert(3, "")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lint and format QMD/MD manuscript files",
    )
    parser.add_argument(
        "--dir",
        required=True,
        help="Directory containing .qmd/.md files to lint",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        default=False,
        help="Auto-fix fixable issues (L006, L008, L009, L015)",
    )
    parser.add_argument(
        "--out-md",
        help="Write markdown report to this path",
    )
    args = parser.parse_args()

    target = Path(args.dir)
    if not target.is_dir():
        raise SystemExit(f"Not a directory: {target}")

    files = sorted(
        p
        for p in target.rglob("*")
        if p.suffix in (".qmd", ".md") and not p.name.startswith("_")
    )

    if not files:
        raise SystemExit(f"No .qmd/.md files found in {target}")

    results: dict[Path, list[Diagnostic]] = {}
    total_fixes = 0

    for path in files:
        diags = lint_file(path)
        results[path] = diags

        if args.fix:
            fix_count, fixed_text = fix_file(path)
            if fix_count > 0:
                path.write_text(fixed_text, encoding="utf-8")
                total_fixes += fix_count
                print(f"  Fixed {fix_count} issues in {path}")
                # Re-lint after fixing
                results[path] = lint_file(path)

    report = format_report(results)

    if args.out_md:
        out_path = Path(args.out_md)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Report written to {out_path}")

    # Print summary
    has_errors = False
    has_warnings = False
    for diags in results.values():
        for d in diags:
            if d.severity == SEVERITY_ERROR:
                has_errors = True
            elif d.severity == SEVERITY_WARNING:
                has_warnings = True

    total_issues = sum(len(d) for d in results.values())
    print(f"Scanned {len(files)} files, found {total_issues} issues")
    if total_fixes:
        print(f"Auto-fixed {total_fixes} issues")

    if has_errors:
        sys.exit(2)
    elif has_warnings:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
