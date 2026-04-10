#!/usr/bin/env python3
"""Render PDF pages to PNG previews for visual QA."""

from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


def read_manifest(path: Path) -> List[dict]:
    if not path.exists():
        raise SystemExit(f"Missing manifest: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append({k: (v or "").strip() for k, v in row.items()})
        for row in rows:
            row["_manifest_dir"] = str(path.parent)
        return rows


def parse_pages(value: str) -> List[Tuple[int, int]]:
    if not value:
        return []
    parts = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            start_s, end_s = token.split("-", 1)
            start = int(start_s)
            end = int(end_s)
        else:
            start = int(token)
            end = int(token)
        if start <= 0 or end <= 0 or end < start:
            raise SystemExit(f"Invalid page range: {token}")
        parts.append((start, end))
    return parts


def find_engine(preferred: Optional[str]) -> str:
    if preferred and preferred != "auto":
        return preferred
    if shutil.which("pdftoppm"):
        return "pdftoppm"
    if shutil.which("mutool"):
        return "mutool"
    raise SystemExit("Missing renderer: install pdftoppm or mutool.")


def render_with_pdftoppm(
    pdf_path: Path, out_prefix: Path, dpi: int, pages: List[Tuple[int, int]]
) -> None:
    for start, end in pages:
        cmd = [
            "pdftoppm",
            "-png",
            "-r",
            str(dpi),
            "-f",
            str(start),
            "-l",
            str(end),
            str(pdf_path),
            str(out_prefix),
        ]
        subprocess.run(cmd, check=True)


def render_with_mutool(
    pdf_path: Path, out_prefix: Path, dpi: int, pages: List[Tuple[int, int]]
) -> None:
    for start, end in pages:
        for page in range(start, end + 1):
            output = f"{out_prefix}-{page:03d}.png"
            cmd = [
                "mutool",
                "draw",
                "-r",
                str(dpi),
                "-o",
                output,
                str(pdf_path),
                str(page),
            ]
            subprocess.run(cmd, check=True)


def render_pdf(
    pdf_path: Path,
    out_dir: Path,
    base_name: str,
    dpi: int,
    pages: List[Tuple[int, int]],
    engine: str,
) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_prefix = out_dir / base_name
    if not pages:
        pages = [(1, 2)]
    if engine == "pdftoppm":
        render_with_pdftoppm(pdf_path, out_prefix, dpi, pages)
    elif engine == "mutool":
        render_with_mutool(pdf_path, out_prefix, dpi, pages)
    else:
        raise SystemExit(f"Unsupported engine: {engine}")
    return 0


def safe_basename(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", value)
    return cleaned.strip("_") or "pdf"


def resolve_pdf(path_str: str, base_dir: Path) -> Optional[Path]:
    if not path_str:
        return None
    path = Path(path_str)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render PDF pages to PNG previews.")
    parser.add_argument("--manifest", default="04_fulltext/manifest.csv", help="Manifest CSV")
    parser.add_argument("--out-dir", default="04_fulltext/previews", help="Output directory")
    parser.add_argument("--pages", default="1-2", help="Page ranges (e.g., 1-2,5)")
    parser.add_argument("--dpi", type=int, default=150, help="Output DPI")
    parser.add_argument("--engine", default="auto", help="Renderer: auto, pdftoppm, mutool")
    parser.add_argument("--limit", type=int, default=None, help="Max PDFs to render")
    parser.add_argument("--file-path", action="append", default=[], help="Specific PDF path(s)")
    args = parser.parse_args()

    engine = find_engine(args.engine)
    out_dir = Path(args.out_dir)
    pages = parse_pages(args.pages)

    pdf_paths: List[Tuple[str, Path]] = []
    if args.file_path:
        for value in args.file_path:
            pdf = Path(value)
            if not pdf.exists():
                raise SystemExit(f"Missing PDF: {pdf}")
            pdf_paths.append((safe_basename(pdf.stem), pdf.resolve()))
    else:
        manifest = read_manifest(Path(args.manifest))
        for row in manifest:
            base_dir = Path(row.get("_manifest_dir", "."))
            pdf_path = resolve_pdf(row.get("file_path", ""), base_dir)
            if not pdf_path or not pdf_path.exists():
                continue
            record_id = row.get("record_id") or row.get("pmid") or row.get("doi") or pdf_path.stem
            pdf_paths.append((safe_basename(record_id), pdf_path))

    if args.limit is not None:
        pdf_paths = pdf_paths[: args.limit]

    if not pdf_paths:
        raise SystemExit("No PDFs found to render.")

    for base_name, pdf_path in pdf_paths:
        render_pdf(
            pdf_path=pdf_path,
            out_dir=out_dir,
            base_name=base_name,
            dpi=args.dpi,
            pages=pages,
            engine=engine,
        )


if __name__ == "__main__":
    main()
