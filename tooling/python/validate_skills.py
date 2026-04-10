#!/usr/bin/env python3
"""Validate skill file structure for all ma-*/SKILL.md files.

Checks:
  1. YAML frontmatter — required fields: name, description, stage, depends_on, next
  2. Required sections — Overview, Pipeline Context, Inputs, Outputs, Workflow,
     Resources, Notes, Common Issues, Validation
  3. Section order — must follow the canonical order above
  4. Frontmatter consistency — stage matches Pipeline Context, depends_on/next valid

Usage:
  uv run tooling/python/validate_skills.py                   # --check (default)
  uv run tooling/python/validate_skills.py --check           # report only
  uv run tooling/python/validate_skills.py --out-md report.md  # write markdown report

Exit codes:
  0 = all checks pass
  1 = errors found
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# --- Constants ---

REQUIRED_FRONTMATTER = ["name", "description", "stage", "depends_on", "next"]

REQUIRED_SECTIONS = [
    "Overview",
    "Pipeline Context",
    "Inputs",
    "Outputs",
    "Workflow",
    "Resources",
    "Notes",
    "Common Issues",
    "Validation",
]

# All known ma-* module names (for cross-reference validation)
KNOWN_MODULES = {
    "ma-topic-intake",
    "ma-search-bibliography",
    "ma-screening-quality",
    "ma-fulltext-management",
    "ma-data-extraction",
    "ma-meta-analysis",
    "ma-manuscript-quarto",
    "ma-peer-review",
    "ma-publication-quality",
    "ma-end-to-end",
}

# --- Parsing ---


def parse_frontmatter(text: str) -> tuple[dict[str, str], int]:
    """Extract YAML frontmatter from markdown text.

    Returns (fields_dict, end_line_index).
    Simple parser — no PyYAML dependency.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, 0

    fields: dict[str, str] = {}
    end_idx = 0
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break
        match = re.match(r"^(\w[\w_]*)\s*:\s*(.*)$", line)
        if match:
            fields[match.group(1)] = match.group(2).strip()

    return fields, end_idx


def extract_sections(text: str) -> list[str]:
    """Extract ## section headings in order."""
    return re.findall(r"^## (.+)$", text, re.MULTILINE)


# --- Validators ---


def validate_frontmatter(fields: dict[str, str], module: str) -> list[str]:
    """Validate frontmatter fields."""
    errors: list[str] = []

    for key in REQUIRED_FRONTMATTER:
        if key not in fields:
            errors.append(f"[{module}] missing frontmatter field: {key}")

    # name should match module name
    if "name" in fields and fields["name"].strip("\"'") != module:
        errors.append(
            f"[{module}] frontmatter 'name' is '{fields['name']}', expected '{module}'"
        )

    # stage should be a two-digit string or a known role (e.g. "orchestrator")
    VALID_STAGE_ROLES = {"orchestrator"}
    if "stage" in fields:
        stage = fields["stage"].strip("\"'")
        if not re.match(r"^\d{2}$", stage) and stage not in VALID_STAGE_ROLES:
            errors.append(
                f"[{module}] frontmatter 'stage' is '{stage}', expected two-digit string (e.g. '01') or {VALID_STAGE_ROLES}"
            )

    # depends_on and next should reference known modules
    for ref_field in ("depends_on", "next"):
        if ref_field in fields:
            raw = fields[ref_field].strip("[]")
            if raw:
                refs = [r.strip().strip("\"'") for r in raw.split(",")]
                for ref in refs:
                    if ref and ref not in KNOWN_MODULES:
                        errors.append(
                            f"[{module}] frontmatter '{ref_field}' references unknown module: {ref}"
                        )

    return errors


def validate_sections(sections: list[str], module: str) -> list[str]:
    """Validate required sections and their order."""
    errors: list[str] = []

    # Check required sections exist
    section_set = set(sections)
    for req in REQUIRED_SECTIONS:
        if req not in section_set:
            errors.append(f"[{module}] missing section: ## {req}")

    # Check order (only among sections that exist and are required)
    present_required = [s for s in sections if s in REQUIRED_SECTIONS]
    canonical_order = [s for s in REQUIRED_SECTIONS if s in section_set]

    if present_required != canonical_order:
        errors.append(
            f"[{module}] section order mismatch: "
            f"got {present_required}, expected {canonical_order}"
        )

    return errors


def validate_pipeline_context(
    text: str, fields: dict[str, str], module: str
) -> list[str]:
    """Cross-check Pipeline Context section against frontmatter."""
    errors: list[str] = []

    # Extract stage from Pipeline Context
    stage_match = re.search(r"\*\*Stage\*\*:\s*(\d+)", text)
    if stage_match and "stage" in fields:
        ctx_stage = stage_match.group(1).zfill(2)
        fm_stage = fields["stage"].strip("\"'")
        if ctx_stage != fm_stage:
            errors.append(
                f"[{module}] Pipeline Context stage ({ctx_stage}) != "
                f"frontmatter stage ({fm_stage})"
            )

    return errors


# --- Main ---


def validate_skill_file(path: Path) -> list[str]:
    """Run all validations on a single SKILL.md file."""
    module = path.parent.name
    text = path.read_text()

    fields, _ = parse_frontmatter(text)
    sections = extract_sections(text)

    errors: list[str] = []
    errors.extend(validate_frontmatter(fields, module))
    errors.extend(validate_sections(sections, module))
    errors.extend(validate_pipeline_context(text, fields, module))

    return errors


def build_report(results: dict[str, list[str]], total_modules: int) -> str:
    """Build a markdown validation report."""
    passed = sum(1 for errs in results.values() if not errs)
    failed = total_modules - passed
    total_errors = sum(len(errs) for errs in results.values())

    lines = [
        "# Skill Validation Report",
        "",
        "## Summary",
        "",
        f"- **Modules**: {total_modules}",
        f"- **Passed**: {passed}",
        f"- **Failed**: {failed}",
        f"- **Total errors**: {total_errors}",
        f"- **Status**: {'PASS' if total_errors == 0 else 'FAIL'}",
        "",
        "## Details",
        "",
        "| Module | Status | Errors |",
        "| --- | --- | --- |",
    ]

    for module in sorted(results):
        errs = results[module]
        status = "PASS" if not errs else "FAIL"
        lines.append(f"| `{module}` | {status} | {len(errs)} |")

    lines.append("")

    # Error details
    if total_errors > 0:
        lines.append("## Errors")
        lines.append("")
        for module in sorted(results):
            errs = results[module]
            if errs:
                lines.append(f"### {module}")
                lines.append("")
                for e in errs:
                    lines.append(f"- {e}")
                lines.append("")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate skill file structure for all ma-*/SKILL.md files."
    )
    parser.add_argument("--root", default=".", help="Project root directory")
    parser.add_argument(
        "--check", action="store_true", default=True, help="Check mode (default)"
    )
    parser.add_argument("--out-md", help="Output markdown report")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    skills_dir = root / ".claude" / "skills"

    results: dict[str, list[str]] = {}
    total = 0

    for skill_dir in sorted(skills_dir.glob("ma-*")):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            results[skill_dir.name] = [f"[{skill_dir.name}] SKILL.md not found"]
            total += 1
            continue

        total += 1
        results[skill_dir.name] = validate_skill_file(skill_file)

    # Print summary
    total_errors = sum(len(errs) for errs in results.values())
    passed = sum(1 for errs in results.values() if not errs)

    for module in sorted(results):
        errs = results[module]
        status = "PASS" if not errs else "FAIL"
        print(f"  {status}  {module}" + (f"  ({len(errs)} errors)" if errs else ""))
        for e in errs:
            print(f"        - {e}")

    print(f"\nSkill Validation: {passed}/{total} passed, {total_errors} errors")

    # Write report
    if args.out_md:
        out = Path(args.out_md)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_report(results, total))
        print(f"Report: {out}")

    if total_errors > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
