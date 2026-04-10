#!/usr/bin/env python3
"""Run multi-DB search, merge, dedupe, and summarize counts."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from env_utils import load_dotenv


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run multi-DB search pipeline.")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--round", default="round-01", help="Round name")
    parser.add_argument("--email", required=True, help="Email for PubMed")
    parser.add_argument("--pico", default=None, help="Override PICO path")
    parser.add_argument("--expanded", default=None, help="Expanded terms YAML")
    parser.add_argument("--queries", default=None, help="Use an existing queries.txt")
    parser.add_argument("--skip-scopus", action="store_true")
    parser.add_argument("--skip-embase", action="store_true")
    parser.add_argument("--skip-cochrane", action="store_true")
    parser.add_argument("--skip-zotero", action="store_true")
    parser.add_argument("--zotero-collection-key", default=None)
    parser.add_argument("--zotero-library-type", default=None)
    parser.add_argument("--zotero-library-id", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    round_dir = root / "02_search" / args.round
    round_dir.mkdir(parents=True, exist_ok=True)

    pico_path = Path(args.pico) if args.pico else root / "01_protocol" / "pico.yaml"
    queries_path = Path(args.queries) if args.queries else round_dir / "queries.txt"

    if not queries_path.exists():
        cmd = [
            sys.executable,
            str(Path(__file__).resolve().parent / "build_queries.py"),
            "--pico",
            str(pico_path),
            "--out",
            str(queries_path),
        ]
        if args.expanded:
            cmd.extend(["--expanded", str(args.expanded)])
        run(cmd)

    pubmed_bib = round_dir / "results.bib"
    pubmed_log = round_dir / "log.md"
    run(
        [
            sys.executable,
            str(Path(__file__).resolve().parent / "pubmed_fetch.py"),
            "--query",
            read_query(queries_path, "pubmed"),
            "--email",
            args.email,
            "--out-bib",
            str(pubmed_bib),
            "--out-log",
            str(pubmed_log),
        ]
    )

    bibs = [pubmed_bib]

    if not args.skip_scopus:
        scopus_bib = round_dir / "scopus.bib"
        run(
            [
                sys.executable,
                str(Path(__file__).resolve().parent / "scopus_fetch.py"),
                "--query",
                read_query(queries_path, "scopus"),
                "--out-json",
                str(round_dir / "scopus.json"),
                "--out-bib",
                str(scopus_bib),
                "--out-log",
                str(round_dir / "scopus.log"),
            ]
        )
        bibs.append(scopus_bib)

    if not args.skip_embase:
        embase_bib = round_dir / "embase.bib"
        run(
            [
                sys.executable,
                str(Path(__file__).resolve().parent / "embase_fetch.py"),
                "--query",
                read_query(queries_path, "embase"),
                "--out-json",
                str(round_dir / "embase.json"),
                "--out-bib",
                str(embase_bib),
                "--out-log",
                str(round_dir / "embase.log"),
            ]
        )
        bibs.append(embase_bib)

    if not args.skip_cochrane:
        cochrane_bib = round_dir / "cochrane.bib"
        run(
            [
                sys.executable,
                str(Path(__file__).resolve().parent / "cochrane_fetch.py"),
                "--query",
                read_query(queries_path, "cochrane"),
                "--out-json",
                str(round_dir / "cochrane.json"),
                "--out-bib",
                str(cochrane_bib),
                "--out-log",
                str(round_dir / "cochrane.log"),
            ]
        )
        bibs.append(cochrane_bib)

    if not args.skip_zotero:
        collection_key = args.zotero_collection_key or os.getenv("ZOTERO_COLLECTION_KEY")
        library_type = args.zotero_library_type or os.getenv("ZOTERO_LIBRARY_TYPE")
        library_id = args.zotero_library_id or os.getenv("ZOTERO_LIBRARY_ID")
        if collection_key:
            if not library_type or not library_id:
                raise SystemExit("Zotero collection key provided but missing library type/id.")
            zotero_bib = round_dir / "zotero.bib"
            cmd = [
                sys.executable,
                str(Path(__file__).resolve().parent / "zotero_fetch.py"),
                "--collection-key",
                collection_key,
                "--library-type",
                library_type,
                "--library-id",
                library_id,
                "--out-bib",
                str(zotero_bib),
                "--out-log",
                str(round_dir / "zotero.log"),
            ]
            run(cmd)
            bibs.append(zotero_bib)

    dedupe_cmd = [
        sys.executable,
        str(Path(__file__).resolve().parent / "multi_db_dedupe.py"),
        "--out-merged",
        str(round_dir / "merged.bib"),
        "--out-bib",
        str(round_dir / "dedupe.bib"),
        "--out-log",
        str(round_dir / "dedupe.log"),
    ]
    for bib in bibs:
        if bib.exists():
            dedupe_cmd.extend(["--in-bib", str(bib)])
    run(dedupe_cmd)

    run(
        [
            sys.executable,
            str(Path(__file__).resolve().parent / "db_counts.py"),
            "--root",
            str(root),
            "--round",
            args.round,
        ]
    )

    run(
        [
            sys.executable,
            str(Path(__file__).resolve().parent / "search_report.py"),
            "--root",
            str(root),
            "--round",
            args.round,
        ]
    )

    run(
        [
            sys.executable,
            str(Path(__file__).resolve().parent / "search_audit.py"),
            "--root",
            str(root),
            "--round",
            args.round,
        ]
    )


def read_query(path: Path, section: str) -> str:
    content = path.read_text().splitlines()
    start = None
    for i, line in enumerate(content):
        if line.strip().lower() == f"[{section}]":
            start = i + 1
            break
    if start is None:
        raise SystemExit(f"Missing [{section}] in {path}")
    query_lines = []
    for line in content[start:]:
        if line.strip().startswith("["):
            break
        if line.strip().startswith("#"):
            continue
        if line.strip():
            query_lines.append(line.strip())
    if not query_lines:
        raise SystemExit(f"Empty query for [{section}] in {path}")
    return " ".join(query_lines)


if __name__ == "__main__":
    main()
