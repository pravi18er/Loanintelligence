"""Build data/benchmarks/benchmarks.json from the source CSV files.

The CSV files are the bank's or RBI's published figures copied verbatim; the
JSON file is what the engine, the Python reference and the spreadsheet read.
Run `python3 -I data/benchmarks/build.py` after editing a CSV; CI runs it with
--check and fails if the JSON is out of date or a CSV is malformed.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "benchmarks.json"


def read_series(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="") as f:
        rows = list(csv.reader(f))
    header, body = rows[0], rows[1:]
    if header[0] != "effective_date":
        raise ValueError(f"{path.name}: first column must be effective_date")
    out, previous = [], None
    for line, row in enumerate(body, start=2):
        if len(row) != len(header):
            raise ValueError(f"{path.name}:{line}: expected {len(header)} values")
        date = dt.date.fromisoformat(row[0]).isoformat()
        if previous is not None and date <= previous:
            raise ValueError(f"{path.name}:{line}: dates must increase")
        previous = date
        rates = {}
        for name, value in zip(header[1:], row[1:]):
            if value == "":
                continue
            rate = Decimal(value)
            if not Decimal("0") < rate < Decimal("20"):
                raise ValueError(f"{path.name}:{line}: implausible rate {value}")
            rates[name] = value
        out.append({"effective": date, "rates": rates})
    return header[1:], out


def build() -> str:
    doc: dict = {"generated_from": "data/benchmarks/*/sources.json and CSV files"}
    for kind in sorted(p.parent.name for p in HERE.glob("*/sources.json")):
        meta = json.loads((HERE / kind / "sources.json").read_text())
        series = []
        for s in meta["series"]:
            tenors, rows = read_series(HERE / kind / s["file"])
            if tenors != s["tenors"]:
                raise ValueError(f"{s['file']}: columns {tenors} != sources.json {s['tenors']}")
            if [rows[0]["effective"], rows[-1]["effective"]] != s["covers"]:
                raise ValueError(f"{s['file']}: covers {s['covers']} does not match the rows")
            series.append({**s, "rows": rows})
        doc[kind] = {k: v for k, v in meta.items() if k != "series"} | {"series": series}
    return json.dumps(doc, indent=1) + "\n"


def main() -> int:
    text = build()
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text() != text:
            print("data/benchmarks/benchmarks.json is out of date. Run: python3 -I data/benchmarks/build.py")
            return 1
        print("benchmarks.json matches the source files.")
        return 0
    OUT.write_text(text)
    print(f"Wrote {OUT.relative_to(HERE.parents[1])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
