#!/usr/bin/env python3
"""Generate SHA256 checksums for figures and tables."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_files(root: Path, subdir: str) -> list[Path]:
    base = root / subdir
    if not base.exists():
        return []
    return [p for p in base.glob("*.*") if p.is_file()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Hash figures and tables.")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--out", default="09_qa/artifact_hashes.json", help="Output JSON path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    figures = collect_files(root, "06_analysis/figures")
    tables = collect_files(root, "06_analysis/tables")

    data = {
        "figures": {str(p): sha256(p) for p in figures},
        "tables": {str(p): sha256(p) for p in tables},
    }

    out_path = root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
