#!/usr/bin/env python3
"""Minimal .env loader without external dependencies."""

from __future__ import annotations

import os
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    here = start or Path(__file__).resolve()
    for parent in [here] + list(here.parents):
        if (parent / ".env").exists():
            return parent
    return Path.cwd()


def load_dotenv(repo_root: Path | None = None) -> None:
    root = repo_root or find_repo_root()
    env_path = root / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key:
            continue
        if key not in os.environ:
            os.environ[key] = value.strip()
