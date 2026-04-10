#!/usr/bin/env python3
"""Copy PRISMA/MOOSE checklist templates into the manuscript folder."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize reporting checklists.")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--include-moose", action="store_true", help="Include MOOSE checklist")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    skill_root = Path(__file__).resolve().parents[1]
    refs = skill_root / "references"

    prisma_src = refs / "prisma2020-checklist-template.md"
    moose_src = refs / "moose-checklist-template.md"

    prisma_dst = root / "07_manuscript" / "prisma_checklist.md"
    moose_dst = root / "07_manuscript" / "moose_checklist.md"

    prisma_dst.parent.mkdir(parents=True, exist_ok=True)

    if prisma_src.exists() and not prisma_dst.exists():
        prisma_dst.write_text(prisma_src.read_text())

    if args.include_moose and moose_src.exists() and not moose_dst.exists():
        moose_dst.write_text(moose_src.read_text())


if __name__ == "__main__":
    main()
