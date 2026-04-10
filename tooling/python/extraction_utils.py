#!/usr/bin/env python3
"""Shared utilities for Stage 05 extraction scripts."""

from __future__ import annotations

import re
from pathlib import Path


def load_field_names_from_dict(data_dict_path: Path) -> list[str]:
    """Extract field names from data dictionary markdown.

    Looks for backtick-quoted identifiers matching Python naming conventions.
    Returns unique field names in document order.
    """
    text = data_dict_path.read_text(encoding="utf-8")
    fields = re.findall(r"`([a-z_][a-z0-9_]*)`", text)
    seen: set[str] = set()
    unique: list[str] = []
    for f in fields:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique


def load_critical_fields(data_dict_path: Path) -> list[str]:
    """Extract critical field names from 'Critical Fields' section.

    Parses the numbered list under '### Critical Fields (Must Not Be Missing)'.
    """
    text = data_dict_path.read_text(encoding="utf-8")
    match = re.search(
        r"###\s+Critical Fields.*?\n(.*?)(?=\n###|\n##|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return []
    section = match.group(1)
    return re.findall(r"\d+\.\s+(\w+)", section)
