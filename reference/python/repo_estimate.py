"""Repo-linked estimate of unknown past rates (A-05, B-03, B-09).

Mirrors packages/loan-engine/src/repo-estimate.ts and the Loan Profile
"repo-linked estimate" table of the spreadsheet. The rule:

- Reset dates: the first reset date (default: one reset interval after
  disbursement, which is one month before EMI 1), then every `reset_months`
  months (same day each month, month-end clamped), up to the report date.
- Known rates: the starting rate from disbursement, and each rate change the
  customer entered, from its date.
- At each reset date R the estimate is repo(R) + spread, where spread is the
  sanction-letter spread if given, else the latest known rate on or before R
  minus the repo rate on that rate's date.
- No estimate at R if the customer entered a change in [R, next reset), if a
  repo rate is not available for a date needed, or if the estimate is not
  above zero. The last known rate then carries forward (labelled Estimated).
- An estimate becomes a keep-EMI rate change (A-04 default) only when it
  differs from the rate in force just before R.
"""

from __future__ import annotations

import datetime as dt
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from benchmarks import repo_rate_on  # noqa: E402
from loan_reference import KEEP_EMI, LoanInput, RateChange, add_months  # noqa: E402

RESET_MONTHS = (1, 3, 6, 12)
MAX_RESETS = 120


@dataclass(frozen=True)
class RepoEstimate:
    reset_months: int = 3
    first_reset: dt.date | None = None
    spread: Decimal | None = None


def _repo(on: dt.date) -> Decimal | None:
    r = repo_rate_on(on)
    return None if r is None else Decimal(r)


def estimated_changes(loan: LoanInput, est: RepoEstimate, as_of: dt.date) -> tuple[RateChange, ...]:
    if est.reset_months not in RESET_MONTHS:
        raise ValueError("reset_months must be 1, 3, 6 or 12")
    disbursed = add_months(loan.first_emi_date, -1)
    anchor = est.first_reset or add_months(disbursed, est.reset_months)
    if anchor <= disbursed:
        raise ValueError("first reset date must be after disbursement")
    entered = list(loan.rate_changes)
    out: list[RateChange] = []
    prev_reset: dt.date | None = None
    prev_est: Decimal | None = None
    for k in range(MAX_RESETS):
        reset = add_months(anchor, k * est.reset_months)
        if reset > as_of:
            break
        nxt = add_months(anchor, (k + 1) * est.reset_months)
        known = [c for c in entered if c.effective <= reset]
        p_date, p_rate = (known[-1].effective, known[-1].annual_rate) if known else (disbursed, loan.annual_rate)
        repo_r = _repo(reset)
        if est.spread is not None:
            spread = est.spread
        else:
            repo_p = _repo(p_date)
            spread = None if repo_p is None else p_rate - repo_p
        value = None if repo_r is None or spread is None else repo_r + spread
        if value is not None and value <= 0:
            value = None
        if prev_reset is None or p_date >= prev_reset or prev_est is None:
            before = p_rate
        else:
            before = prev_est
        dropped = any(reset <= c.effective < nxt for c in entered)
        if value is not None and not dropped and value != before:
            out.append(RateChange(reset, value, KEEP_EMI))
        prev_reset, prev_est = reset, value
    return tuple(out)


def with_estimates(loan: LoanInput, est: RepoEstimate, as_of: dt.date) -> LoanInput:
    """The loan with estimated changes merged into the entered ones, by date."""
    merged = sorted(
        list(loan.rate_changes) + list(estimated_changes(loan, est, as_of)), key=lambda c: c.effective
    )
    return LoanInput(**{**loan.__dict__, "rate_changes": tuple(merged)})
