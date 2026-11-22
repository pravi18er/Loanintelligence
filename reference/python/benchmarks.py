"""Bundled MCLR reference (B-07), mirroring packages/loan-engine/src/benchmarks.ts.

MCLR history is shown beside an MCLR-linked loan as a reference only; it never
sets the loan's rate.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

DATA = json.loads(
    (Path(__file__).resolve().parents[2] / "data" / "benchmarks" / "benchmarks.json").read_text()
)
MCLR_TABLE_VERSION = DATA["mclr"]["table_version"]


def mclr_on(lender: str, tenor: str, on: dt.date) -> str | None:
    """The lender's published MCLR for a tenor in force on a date, as published
    (percent per annum, string), or None when the history does not cover it."""
    series = next((s for s in DATA["mclr"]["series"] if s["id"] == lender), None)
    if series is None:
        raise ValueError(f"No bundled MCLR history for lender: {lender}")
    day = on.isoformat()
    rows = [r for r in series["rows"] if r["effective"] <= day]
    return rows[-1]["rates"].get(tenor) if rows else None


def repo_rate_on(on: dt.date) -> str | None:
    """The RBI policy repo rate in force on a date, or None before 7 Aug 2019."""
    day = on.isoformat()
    rows = [r for r in DATA["repo"]["series"][0]["rows"] if r["effective"] <= day]
    return rows[-1]["rates"]["repo_rate"] if rows else None
