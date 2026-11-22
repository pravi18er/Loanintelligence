"""Check the v2 workbook's Repayment Engine against every golden scenario.

For each file in reference/scenarios/, the scenario's inputs are written into
a fresh copy of the workbook, LibreOffice recalculates it headlessly, and every
row is compared with the expected schedule to the paisa.

Usage (from the repository root; needs openpyxl and LibreOffice `soffice`):
    python3 -I spreadsheet/verify_workbook.py
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_workbook as bw  # noqa: E402

sys.path.insert(0, str(HERE.parent / "reference" / "python"))
from benchmarks import mclr_on, repo_rate_on  # noqa: E402

# (benchmark, tenor, date) looked up on the Benchmark Rates tab and compared
# with the Python reference.
BENCH_CASES = [
    ("sbi", "one_year", "2022-06-15"),
    ("sbi", "one_year", "2022-06-14"),
    ("sbi", "six_month", "2026-11-22"),
    ("sbi", "one_year", "2016-03-31"),
    ("bank_of_baroda", "one_year", "2019-12-12"),
    ("bank_of_baroda", "five_year", "2020-01-01"),
    ("bank_of_baroda", "five_year", "2017-06-01"),
    ("rbi_repo", "repo_rate", "2019-10-01"),
    ("rbi_repo", "repo_rate", "2022-05-04"),
    ("rbi_repo", "repo_rate", "2026-11-22"),
]

SCENARIOS = HERE.parent / "reference" / "scenarios"
MODE_TEXT = {"keep_emi": bw.MODE_KEEP_EMI, "keep_tenure": bw.MODE_KEEP_TENURE, "bank_emi": bw.MODE_BANK_EMI}
FLAG_TEXT = {
    "bank_outstanding_applied": "bank balance used",
    "rate_change": "rate change",
    "final_emi_adjusted": "final EMI adjusted",
    "emi_does_not_cover_interest": "EMI does not cover interest",
}


def d(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def rupees(paise: int | None):
    return None if paise is None else float(Decimal(paise) / 100)


def fill(path: Path, scenario: dict) -> None:
    wb = bw.build()
    ws = wb["Loan Profile"]
    i = scenario["input"]
    ws["C5"] = rupees(i["principal_paise"])
    ws["C6"] = d(i["first_emi_date"])
    ws["C7"] = i["tenure_months"]
    ws["C8"] = float(i["annual_rate"])
    ws["C9"] = rupees(i["starting_emi_paise"])
    ws["C12"] = AS_OF
    b = i["bank_outstanding"]
    ws["C14"] = rupees(b["outstanding_paise"]) if b else None
    ws["C15"] = d(b["as_at"]) if b else None
    for k in range(bw.CHANGE_ROWS):
        for col in "BCDEF":
            ws[f"{col}{23 + k}"] = None
    for k, c in enumerate(i["rate_changes"]):
        row = 23 + k
        ws[f"B{row}"] = d(c["effective"])
        ws[f"C{row}"] = float(c["annual_rate"])
        ws[f"D{row}"] = MODE_TEXT[c["mode"]]
        ws[f"E{row}"] = rupees(c["bank_emi_paise"])
        ws[f"F{row}"] = bw.SOURCE_BANK
    wb.save(path)


def to_paise(v) -> int:
    return int((Decimal(str(v)) * 100).to_integral_value(rounding="ROUND_HALF_UP"))


def as_date(v) -> str:
    if isinstance(v, dt.datetime):
        v = v.date()
    return v.isoformat()


def compare(path: Path, scenario: dict) -> list[str]:
    wb = load_workbook(path, data_only=True)
    ws = wb["Repayment Engine"]
    got = []
    for r in range(bw.FIRST_ROW, bw.LAST_ROW + 1):
        if ws[f"B{r}"].value is not True:
            break
        notes = ws[f"Q{r}"].value or ""
        got.append({
            "n": int(ws[f"A{r}"].value),
            "period_start": as_date(ws[f"C{r}"].value),
            "due_date": as_date(ws[f"D{r}"].value),
            "annual_rate": Decimal(str(ws[f"H{r}"].value)),
            "opening_paise": to_paise(ws[f"J{r}"].value),
            "interest_paise": to_paise(ws[f"M{r}"].value),
            "payment_paise": to_paise(ws[f"N{r}"].value),
            "principal_paise": to_paise(ws[f"O{r}"].value),
            "closing_paise": to_paise(ws[f"P{r}"].value),
            "flags": [f for f, t in FLAG_TEXT.items() if t in notes],
        })
    expected = scenario["expected"]["schedule"]
    problems = dashboard_problems(wb, scenario)
    if len(got) != len(expected):
        problems.append(f"{len(got)} rows, expected {len(expected)}")
    for g, e in zip(got, expected):
        e = {**e, "annual_rate": Decimal(e["annual_rate"]), "flags": sorted(e["flags"])}
        g = {**g, "flags": sorted(g["flags"])}
        if g != e:
            diff = {k: (g[k], e[k]) for k in e if g.get(k) != e[k]}
            problems.append(f"row {e['n']}: {diff}")
            if len(problems) > 5:
                break
    return problems


AS_OF = dt.date(2025, 11, 22)


def dashboard_problems(wb, scenario: dict) -> list[str]:
    """The Loan Reality Check totals must equal sums over the expected schedule."""
    rows = scenario["expected"]["schedule"]
    paid = [r for r in rows if dt.date.fromisoformat(r["due_date"]) <= AS_OF]
    want = {
        "EMIs paid so far": len(paid),
        "Total EMIs paid": sum(r["payment_paise"] for r in paid),
        "Principal repaid": sum(r["principal_paise"] for r in paid),
        "Interest paid": sum(r["interest_paise"] for r in paid),
        "Interest still to pay (projection)": sum(r["interest_paise"] for r in rows[len(paid):]),
    }
    ws = wb["Loan Reality Check"]
    got = {}
    for r in range(5, 14):
        label, value = ws.cell(r, 2).value, ws.cell(r, 3).value
        if label in want:
            got[label] = int(value) if label == "EMIs paid so far" else to_paise(value)
    return [f"dashboard {k}: {got.get(k)} != {v}" for k, v in want.items() if got.get(k) != v]


def fill_bench(path: Path, case: tuple[str, str, str]) -> None:
    sid, tenor, day = case
    wb = bw.build()
    ws = wb["Benchmark Rates"]
    ws["C5"] = next(t for t, _, i in bw.benchmark_series() if i == sid)
    ws["C6"] = bw.TENOR_TEXT[tenor]
    ws["C7"] = d(day)
    wb.save(path)


def bench_problem(path: Path, case: tuple[str, str, str]) -> str | None:
    sid, tenor, day = case
    want = repo_rate_on(d(day)) if sid == "rbi_repo" else mclr_on(sid, tenor, d(day))
    got = load_workbook(path, data_only=True)["Benchmark Rates"]["C9"].value
    ok = (Decimal(str(got)) == Decimal(want)) if want is not None and isinstance(got, (int, float)) else (
        want is None and isinstance(got, str))
    return None if ok else f"{case}: workbook {got!r}, reference {want!r}"


def main() -> int:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        print("LibreOffice (soffice) is required.")
        return 2
    failures = 0
    files = sorted(SCENARIOS.glob("*.json"))
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        src_dir, out_dir = tmpdir / "in", tmpdir / "out"
        src_dir.mkdir()
        out_dir.mkdir()
        scenarios = {}
        for f in files:
            s = json.loads(f.read_text())
            scenarios[s["id"]] = s
            fill(src_dir / f"{s['id']}.xlsx", s)
        for k, case in enumerate(BENCH_CASES):
            fill_bench(src_dir / f"bench-{k:02d}.xlsx", case)
        subprocess.run(
            [soffice, "--headless", f"-env:UserInstallation=file://{tmpdir}/profile",
             "--convert-to", "xlsx", "--outdir", str(out_dir), *map(str, sorted(src_dir.glob("*.xlsx")))],
            check=True, capture_output=True, timeout=600,
        )
        for sid, s in scenarios.items():
            problems = compare(out_dir / f"{sid}.xlsx", s)
            if problems:
                failures += 1
                print(f"FAIL {sid}: " + "; ".join(problems))
            else:
                print(f"ok   {sid}: {len(s['expected']['schedule'])} rows match to the paisa")
        bench_failures = [p for k, c in enumerate(BENCH_CASES) if (p := bench_problem(out_dir / f"bench-{k:02d}.xlsx", c))]
    for p in bench_failures:
        print(f"FAIL benchmark lookup {p}")
    print(f"{len(files) - failures}/{len(files)} scenarios match.")
    print(f"{len(BENCH_CASES) - len(bench_failures)}/{len(BENCH_CASES)} benchmark lookups match the reference.")
    return 1 if failures or bench_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
