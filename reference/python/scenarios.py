"""Golden scenarios for the approved Release 1.0 rules.

Run `python3 -I reference/python/scenarios.py` from the repository root to
regenerate reference/scenarios/*.json. CI regenerates them and fails if the
committed files differ, so the fixtures can never drift from this reference.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from loan_reference import (  # noqa: E402
    BANK_EMI,
    KEEP_EMI,
    KEEP_TENURE,
    BankOutstanding,
    LoanInput,
    RateChange,
    amortise,
    result_to_dict,
)

OUT_DIR = Path(__file__).resolve().parents[1] / "scenarios"
FIXTURE_VERSION = 1


def lakh(x: float | int) -> int:
    """Rupees in lakh to paise."""
    return int(D(str(x)) * 100000 * 100)


SCENARIOS: list[tuple[str, str, list[str], LoanInput]] = [
    (
        "G-01",
        "New loan, fixed rate, 20 years (Rs 50 lakh at 8.5%)",
        ["A-01", "A-02", "A-07", "A-08"],
        LoanInput(lakh(50), D("8.5"), 240, dt.date(2020, 4, 5)),
    ),
    (
        "G-02",
        "Zero interest (Rs 12 lakh, 12 months)",
        ["A-01", "A-02"],
        LoanInput(lakh(12), D("0"), 12, dt.date(2024, 1, 10)),
    ),
    (
        "G-03a",
        "Very short loan: 1 month",
        ["A-01", "A-07"],
        LoanInput(lakh(1), D("10"), 1, dt.date(2024, 1, 15)),
    ),
    (
        "G-03b",
        "Short loan: 12 months",
        ["A-01", "A-02", "A-07"],
        LoanInput(lakh(5), D("9"), 12, dt.date(2024, 1, 15)),
    ),
    (
        "G-04",
        "Maximum tenure and large amount (Rs 20 crore, 480 months)",
        ["A-01", "A-02", "A-07"],
        LoanInput(lakh(2000), D("9"), 480, dt.date(2025, 2, 1)),
    ),
    (
        "G-06",
        "Several rate changes, mixed keep-EMI and keep-tenure (v1 sample loan)",
        ["A-03", "A-04", "A-07"],
        LoanInput(
            lakh(50),
            D("8"),
            240,
            dt.date(2020, 4, 5),
            rate_changes=(
                RateChange(dt.date(2020, 6, 1), D("7.2"), KEEP_EMI),
                RateChange(dt.date(2022, 6, 1), D("7.9"), KEEP_EMI),
                RateChange(dt.date(2022, 11, 1), D("8.6"), KEEP_EMI),
                RateChange(dt.date(2023, 3, 1), D("9.15"), KEEP_TENURE),
                RateChange(dt.date(2025, 4, 1), D("8.9"), KEEP_EMI),
                RateChange(dt.date(2025, 7, 1), D("8.4"), KEEP_EMI),
            ),
        ),
    ),
    (
        "G-07",
        "Rate rise with EMI kept so the EMI no longer covers interest (must be flagged)",
        ["A-04", "S-05"],
        LoanInput(
            lakh(50),
            D("7"),
            240,
            dt.date(2020, 4, 5),
            rate_changes=(RateChange(dt.date(2021, 1, 1), D("14"), KEEP_EMI),),
        ),
    ),
    (
        "G-08",
        "Dated bank outstanding that differs from the model",
        ["A-06", "S-03", "S-04"],
        LoanInput(
            lakh(50),
            D("8.5"),
            240,
            dt.date(2020, 4, 5),
            bank_outstanding=BankOutstanding(
                dt.date(2023, 3, 31), lakh(45), "annual statement"
            ),
        ),
    ),
    (
        "G-09",
        "Bank-revised EMI after a rate change",
        ["A-04"],
        LoanInput(
            lakh(30),
            D("9"),
            240,
            dt.date(2021, 7, 10),
            rate_changes=(
                RateChange(dt.date(2022, 6, 1), D("9.5"), BANK_EMI, 2800000),
            ),
        ),
    ),
    (
        "G-10",
        "Rate changes on, after and before a period start (EMIs on the 5th)",
        ["A-03"],
        LoanInput(
            lakh(40),
            D("8"),
            240,
            dt.date(2021, 1, 5),
            rate_changes=(
                RateChange(dt.date(2021, 6, 5), D("8.25"), KEEP_EMI),
                RateChange(dt.date(2022, 6, 6), D("8.5"), KEEP_EMI),
                RateChange(dt.date(2023, 6, 1), D("8.75"), KEEP_EMI),
            ),
        ),
    ),
    (
        "G-11",
        "Bank-rounded EMI (Rs 43,391): remainder absorbed into the 240th EMI",
        ["A-04", "A-07"],
        LoanInput(
            lakh(50), D("8.5"), 240, dt.date(2020, 4, 5), starting_emi_paise=4339100
        ),
    ),
    (
        "G-12b",
        "Two rate changes inside one period with different choices: only the later applies",
        ["A-03", "A-04"],
        LoanInput(
            lakh(40),
            D("8.5"),
            180,
            dt.date(2021, 3, 5),
            rate_changes=(
                RateChange(dt.date(2022, 6, 10), D("9"), KEEP_TENURE),
                RateChange(dt.date(2022, 6, 25), D("9.4"), KEEP_EMI),
                RateChange(dt.date(2023, 9, 1), D("9.1"), KEEP_TENURE),
            ),
        ),
    ),
    (
        "G-13",
        "EMI due on the 31st (last day of shorter months)",
        ["B-05", "A-08"],
        LoanInput(lakh(25), D("8.75"), 120, dt.date(2021, 1, 31)),
    ),
]


def input_to_dict(loan: LoanInput) -> dict:
    return {
        "principal_paise": loan.principal_paise,
        "annual_rate": str(loan.annual_rate),
        "tenure_months": loan.tenure_months,
        "first_emi_date": loan.first_emi_date.isoformat(),
        "starting_emi_paise": loan.starting_emi_paise,
        "rate_changes": [
            {
                "effective": c.effective.isoformat(),
                "annual_rate": str(c.annual_rate),
                "mode": c.mode,
                "bank_emi_paise": c.bank_emi_paise,
            }
            for c in loan.rate_changes
        ],
        "bank_outstanding": None
        if loan.bank_outstanding is None
        else {
            "as_at": loan.bank_outstanding.as_at.isoformat(),
            "outstanding_paise": loan.bank_outstanding.outstanding_paise,
            "source": loan.bank_outstanding.source,
        },
    }


def build() -> dict[str, str]:
    files = {}
    for sid, title, rules, loan in SCENARIOS:
        doc = {
            "fixture_version": FIXTURE_VERSION,
            "id": sid,
            "title": title,
            "rules": rules,
            "input": input_to_dict(loan),
            "expected": result_to_dict(amortise(loan)),
        }
        files[f"{sid}.json"] = json.dumps(doc, indent=1) + "\n"
    return files


def main() -> int:
    check = "--check" in sys.argv
    files = build()
    stale = []
    for name, text in files.items():
        path = OUT_DIR / name
        if check:
            if not path.exists() or path.read_text() != text:
                stale.append(name)
        else:
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    if check:
        extra = sorted(p.name for p in OUT_DIR.glob("*.json") if p.name not in files)
        if stale or extra:
            print("Scenario files out of date:", ", ".join(stale + extra))
            print("Run: python3 -I reference/python/scenarios.py")
            return 1
        print(f"{len(files)} scenario files match the reference.")
    else:
        print(f"Wrote {len(files)} scenario files to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
