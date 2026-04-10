#!/usr/bin/env python3
"""Expand PICO terms using MeSH and optional Emtree synonym files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List

import yaml

from mesh_expand import expand_terms


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


def read_emtree_csv(path: Path) -> Dict[str, List[str]]:
    if not path.exists():
        return {}
    mapping: Dict[str, List[str]] = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        if "," not in line:
            continue
        preferred, synonym = line.split(",", 1)
        preferred = preferred.strip()
        synonym = synonym.strip()
        if not preferred or not synonym:
            continue
        mapping.setdefault(preferred, []).append(synonym)
    return mapping


def merge_emtree(terms: List[str], emtree_map: Dict[str, List[str]]) -> List[str]:
    expanded = set(terms)
    for term in terms:
        for synonym in emtree_map.get(term, []):
            expanded.add(synonym)
    return sorted(expanded)


def expand_block(
    block: Any,
    lookup_url: str,
    match: str,
    emtree_map: Dict[str, List[str]],
    cache_path: Path | None,
) -> List[str]:
    base_terms = split_terms(block)
    mesh_terms = expand_terms(base_terms, lookup_url, match, None, cache_path=cache_path)
    if emtree_map:
        return merge_emtree(mesh_terms, emtree_map)
    return mesh_terms


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand PICO terms with MeSH and Emtree.")
    parser.add_argument("--pico", default="01_protocol/pico.yaml", help="Path to pico.yaml")
    parser.add_argument("--lookup-url", default=None, help="MeSH lookup URL override")
    parser.add_argument("--match", default="exact", help="MeSH lookup match mode")
    parser.add_argument("--cache", default=None, help="MeSH cache file path")
    parser.add_argument("--emtree-csv", default=None, help="Optional Emtree synonyms CSV")
    parser.add_argument("--out", default="02_search/round-01/expanded_terms.yaml", help="Output YAML")
    args = parser.parse_args()

    pico_path = Path(args.pico)
    if not pico_path.exists():
        raise SystemExit(f"Missing PICO file: {pico_path}")

    pico = yaml.safe_load(pico_path.read_text()) or {}
    lookup_url = args.lookup_url or "https://id.nlm.nih.gov/mesh/lookup/descriptor"

    emtree_map = read_emtree_csv(Path(args.emtree_csv)) if args.emtree_csv else {}

    cache_path = Path(args.cache) if args.cache else None

    expanded = {
        "population": expand_block(pico.get("population", {}).get("description"), lookup_url, args.match, emtree_map, cache_path),
        "intervention": expand_block(pico.get("intervention", {}).get("description"), lookup_url, args.match, emtree_map, cache_path),
        "comparison": expand_block(pico.get("comparison", {}).get("description"), lookup_url, args.match, emtree_map, cache_path),
        "outcomes": [],
    }

    outcomes_block = pico.get("outcomes", {})
    for outcome in outcomes_block.get("primary", []) or []:
        expanded["outcomes"].extend(
            expand_block(outcome.get("name"), lookup_url, args.match, emtree_map, cache_path)
        )
    for outcome in outcomes_block.get("secondary", []) or []:
        expanded["outcomes"].extend(
            expand_block(outcome.get("name"), lookup_url, args.match, emtree_map, cache_path)
        )

    expanded["outcomes"] = sorted(set(expanded["outcomes"]))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.safe_dump(expanded, sort_keys=False))


if __name__ == "__main__":
    main()
