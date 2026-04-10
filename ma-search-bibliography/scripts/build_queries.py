#!/usr/bin/env python3
"""Build database-specific queries from pico.yaml."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Iterable, List

import yaml


def split_terms(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        terms = []
        for item in value:
            terms.extend(split_terms(item))
        return terms
    if isinstance(value, str):
        raw = value.replace("|", ";")
        parts = [p.strip() for p in re.split(r";|,", raw) if p.strip()]
        return parts
    return []


def quote(term: str) -> str:
    term = term.strip()
    if " " in term and not term.startswith("\""):
        return f'"{term}"'
    return term


def group_terms(terms: List[str], fmt) -> str:
    if not terms:
        return ""
    formatted = [fmt(quote(t)) for t in terms]
    if len(formatted) == 1:
        return formatted[0]
    return "(" + " OR ".join(formatted) + ")"


def build_pubmed_group(terms: List[str]) -> str:
    def fmt(term: str) -> str:
        return term if "[" in term else f"{term}[tiab]"
    return group_terms(terms, fmt)


def build_scopus_group(terms: List[str]) -> str:
    return group_terms(terms, lambda term: f"TITLE-ABS-KEY({term})")


def build_embase_group(terms: List[str]) -> str:
    return group_terms(terms, lambda term: f"{term}:ti,ab,kw")


def build_cochrane_group(terms: List[str]) -> str:
    return group_terms(terms, lambda term: term)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build database queries from pico.yaml")
    parser.add_argument("--pico", default="01_protocol/pico.yaml", help="Path to pico.yaml")
    parser.add_argument("--expanded", default=None, help="Expanded terms YAML")
    parser.add_argument("--out", default="02_search/round-01/queries.txt", help="Output file")
    args = parser.parse_args()

    if args.expanded:
        expanded_path = Path(args.expanded)
        if not expanded_path.exists():
            raise SystemExit(f"Missing expanded terms file: {expanded_path}")
        pico = yaml.safe_load(expanded_path.read_text()) or {}
        population = split_terms(pico.get("population"))
        intervention = split_terms(pico.get("intervention"))
        comparison = split_terms(pico.get("comparison"))
        outcomes = split_terms(pico.get("outcomes"))
    else:
        pico_path = Path(args.pico)
        if not pico_path.exists():
            raise SystemExit(f"Missing PICO file: {pico_path}")
        pico = yaml.safe_load(pico_path.read_text()) or {}
        population = split_terms(pico.get("population", {}).get("description"))
        intervention = split_terms(pico.get("intervention", {}).get("description"))
        comparison = split_terms(pico.get("comparison", {}).get("description"))

        outcomes = []
        outcomes_block = pico.get("outcomes", {})
        for outcome in outcomes_block.get("primary", []) or []:
            outcomes.extend(split_terms(outcome.get("name")))
        for outcome in outcomes_block.get("secondary", []) or []:
            outcomes.extend(split_terms(outcome.get("name")))

    # population, intervention, comparison, outcomes populated above

    def join_parts(parts: List[str]) -> str:
        parts = [p for p in parts if p]
        return " AND ".join(parts) if parts else ""

    pubmed = join_parts(
        [
            build_pubmed_group(population),
            build_pubmed_group(intervention),
            build_pubmed_group(comparison),
            build_pubmed_group(outcomes),
        ]
    )

    scopus = join_parts(
        [
            build_scopus_group(population),
            build_scopus_group(intervention),
            build_scopus_group(comparison),
            build_scopus_group(outcomes),
        ]
    )

    embase = join_parts(
        [
            build_embase_group(population),
            build_embase_group(intervention),
            build_embase_group(comparison),
            build_embase_group(outcomes),
        ]
    )

    cochrane = join_parts(
        [
            build_cochrane_group(population),
            build_cochrane_group(intervention),
            build_cochrane_group(comparison),
            build_cochrane_group(outcomes),
        ]
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Generated from 01_protocol/pico.yaml",
        "",
        "[pubmed]",
        pubmed or "",
        "",
        "[scopus]",
        scopus or "",
        "",
        "[embase]",
        embase or "",
        "",
        "[cochrane]",
        cochrane or "",
        "",
        "# Review and refine queries per database syntax before running searches.",
    ]
    out_path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
