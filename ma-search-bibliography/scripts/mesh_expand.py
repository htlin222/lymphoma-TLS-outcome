#!/usr/bin/env python3
"""Expand terms using the NLM MeSH RDF Lookup API."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Iterable, List, Set

import requests

from env_utils import load_dotenv, find_repo_root

DEFAULT_LOOKUP = "https://id.nlm.nih.gov/mesh/lookup/descriptor"


def normalize_term(term: str) -> str:
    return re.sub(r"\s+", " ", term.strip())


def fetch_lookup(label: str, lookup_url: str, match: str) -> list[dict[str, Any]]:
    params = {"label": label, "match": match}
    resp = requests.get(lookup_url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, list) else []


def extract_labels(value: Any) -> list[str]:
    labels: list[str] = []
    if isinstance(value, str):
        labels.append(value)
    elif isinstance(value, list):
        for item in value:
            labels.extend(extract_labels(item))
    elif isinstance(value, dict):
        for key in ("@value", "label", "prefLabel"):
            if key in value:
                labels.extend(extract_labels(value[key]))
    return labels


def is_term_type(type_value: Any) -> bool:
    if isinstance(type_value, str):
        return "Term" in type_value
    if isinstance(type_value, list):
        return any(is_term_type(item) for item in type_value)
    return False


def collect_terms_from_graph(graph: list[dict[str, Any]]) -> Set[str]:
    terms: Set[str] = set()
    for node in graph:
        node_type = node.get("@type") or node.get("type")
        if is_term_type(node_type) or "label" in node or "prefLabel" in node or "rdfs:label" in node:
            for key in ("label", "prefLabel", "rdfs:label"):
                if key in node:
                    for label in extract_labels(node.get(key)):
                        if label:
                            terms.add(label)
    return terms


def fetch_descriptor_terms(resource_url: str) -> Set[str]:
    url = resource_url + ".json" if not resource_url.endswith(".json") else resource_url
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    payload = resp.json()

    terms: Set[str] = set()
    if isinstance(payload, dict):
        if "@graph" in payload and isinstance(payload["@graph"], list):
            terms |= collect_terms_from_graph(payload["@graph"])
        for key in ("label", "prefLabel", "rdfs:label"):
            if key in payload:
                for label in extract_labels(payload.get(key)):
                    if label:
                        terms.add(label)
    return terms


def load_cache(cache_path: Path) -> dict:
    if not cache_path.exists():
        return {"lookup": {}, "terms": {}}
    try:
        data = json.loads(cache_path.read_text())
        if isinstance(data, dict):
            data.setdefault("lookup", {})
            data.setdefault("terms", {})
            return data
    except Exception:
        pass
    return {"lookup": {}, "terms": {}}


def save_cache(cache_path: Path, cache: dict) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2) + "\n")


def expand_terms(
    labels: Iterable[str],
    lookup_url: str,
    match: str,
    max_terms: int | None,
    cache_path: Path | None = None,
) -> list[str]:
    expanded: Set[str] = set()
    cache = load_cache(cache_path) if cache_path else {"lookup": {}, "terms": {}}
    for label in labels:
        label = normalize_term(label)
        if not label:
            continue
        expanded.add(label)
        cache_key = f"{match}::{label}"
        if cache_key in cache["lookup"]:
            resources = cache["lookup"][cache_key]
        else:
            results = fetch_lookup(label, lookup_url, match)
            resources = [item.get("resource") or item.get("uri") for item in results]
            resources = [r for r in resources if r]
            cache["lookup"][cache_key] = resources

        for resource in resources:
            if resource in cache["terms"]:
                terms = cache["terms"][resource]
            else:
                try:
                    terms = list(fetch_descriptor_terms(resource))
                except Exception:
                    continue
                cache["terms"][resource] = terms
            for term in terms:
                expanded.add(normalize_term(term))

    terms_list = sorted({t for t in expanded if t})
    if max_terms and len(terms_list) > max_terms:
        return terms_list[:max_terms]
    if cache_path:
        save_cache(cache_path, cache)
    return terms_list


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Expand terms with MeSH RDF lookup.")
    parser.add_argument("--terms", action="append", default=[], help="Term to expand (repeatable)")
    parser.add_argument("--terms-file", default=None, help="File with one term per line")
    parser.add_argument("--lookup-url", default=os.getenv("MESH_LOOKUP_URL", DEFAULT_LOOKUP))
    parser.add_argument("--match", default="exact", help="Lookup match mode (exact or contains)")
    parser.add_argument("--max-terms", type=int, default=None, help="Cap number of terms")
    parser.add_argument("--cache", default=None, help="Cache file path")
    parser.add_argument("--out", required=True, help="Output JSON file")
    args = parser.parse_args()

    labels = list(args.terms)
    if args.terms_file:
        labels.extend(Path(args.terms_file).read_text().splitlines())

    cache_path = Path(args.cache) if args.cache else find_repo_root() / "02_search" / "round-01" / "mesh_cache.json"
    terms = expand_terms(labels, args.lookup_url, args.match, args.max_terms, cache_path=cache_path)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"terms": terms}, indent=2) + "\n")


if __name__ == "__main__":
    main()
