#!/usr/bin/env python3
"""Initialize a SQLite schema for meta-analysis extraction."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize extraction database schema.")
    parser.add_argument("--db", required=True, help="Output SQLite database path")
    args = parser.parse_args()

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS study (
            study_id TEXT PRIMARY KEY,
            record_id TEXT,
            title TEXT,
            year INTEGER,
            doi TEXT,
            pmid TEXT,
            design TEXT,
            country TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS outcome (
            outcome_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            unit TEXT,
            outcome_type TEXT
        );

        CREATE TABLE IF NOT EXISTS arm (
            arm_id TEXT PRIMARY KEY,
            study_id TEXT NOT NULL,
            arm_label TEXT,
            n INTEGER,
            FOREIGN KEY (study_id) REFERENCES study(study_id)
        );

        CREATE TABLE IF NOT EXISTS measurement (
            measurement_id TEXT PRIMARY KEY,
            study_id TEXT NOT NULL,
            outcome_id TEXT NOT NULL,
            arm_id TEXT,
            timepoint TEXT,
            mean REAL,
            sd REAL,
            events INTEGER,
            total INTEGER,
            effect REAL,
            se REAL,
            ci_low REAL,
            ci_high REAL,
            notes TEXT,
            FOREIGN KEY (study_id) REFERENCES study(study_id),
            FOREIGN KEY (outcome_id) REFERENCES outcome(outcome_id),
            FOREIGN KEY (arm_id) REFERENCES arm(arm_id)
        );

        CREATE TABLE IF NOT EXISTS source (
            source_id TEXT PRIMARY KEY,
            study_id TEXT NOT NULL,
            record_id TEXT,
            file_path TEXT,
            page_reference TEXT,
            notes TEXT,
            FOREIGN KEY (study_id) REFERENCES study(study_id)
        );
        """
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
