"""Independent reference implementation of the approved Release 1.0 rules.

This is NOT product code. It exists so the TypeScript engine and the
spreadsheet (v2) can be checked against a second, simple implementation of
the same rules. It uses only the Python standard library.

Approved rules implemented (see PRODUCT_DECISIONS.md):

A-01  Monthly reducing-balance interest: opening balance x annual rate / 1200.
A-02  (amended by B-06, 22 Nov 2026) Every monetary amount is rounded to the
      paisa (integer paise): the EMI, each month's interest, principal and
      balance. Customer-facing display rounds to the nearest rupee.
      Rounding is half-up, matching the spreadsheet ROUND function.
A-03  A rate change applies from the first calculation period beginning on or
      after its effective date. A period runs from one EMI due date to the next
      (B-02). No mid-period splitting.
A-04  Per change: keep EMI (default, tenure moves), keep tenure (EMI
      recalculated), or a bank-revised EMI.
A-06  A dated bank-reported outstanding is the balance after every EMI due on
      or before its date. It becomes the opening balance of the period in
      which its date falls (the first EMI due after the date). The modelled
      balance compared with it is the closing balance of the last EMI due on
      or before the date. Modelled history is unchanged and the difference is
      reported, never applied backwards.
A-07  The final EMI is the exact remaining amount due (balance + interest).
      Where a scheduled maturity exists, any remainder is absorbed into the
      EMI at maturity; no extra instalment is created (B-04).
A-08  Fully disbursed loans only: full disbursement is assumed one calendar
      month before EMI 1 (B-05).
B-05  EMI dates on the 29th-31st fall on the last day of shorter months and
      return to the scheduled day when it exists again.

Not implemented yet: A-05 benchmark-based illustrative rates (pending B-07).
"""

from __future__ import annotations

import calendar
import datetime as dt
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().prec = 50

PAISA = Decimal("0.01")
MAX_MONTHS = 600
KEEP_EMI = "keep_emi"
KEEP_TENURE = "keep_tenure"
BANK_EMI = "bank_emi"


def to_paise(amount: Decimal) -> int:
    """Round a rupee amount half-up to the paisa and return integer paise."""
    return int((amount.quantize(PAISA, rounding=ROUND_HALF_UP) * 100).to_integral_value())


def rupees(paise: int) -> Decimal:
    return Decimal(paise) / 100


def add_months(start: dt.date, months: int) -> dt.date:
    """Same day-of-month `months` later; clamp to the month's last day (B-05)."""
    total = start.year * 12 + (start.month - 1) + months
    year, month = divmod(total, 12)
    month += 1
    last = calendar.monthrange(year, month)[1]
    return dt.date(year, month, min(start.day, last))


def monthly_interest_paise(balance_paise: int, annual_rate: Decimal) -> int:
    """A-01 then A-02: balance x rate / 1200, rounded to the paisa."""
    return to_paise(rupees(balance_paise) * annual_rate / 1200)


def emi_paise(balance_paise: int, annual_rate: Decimal, months: int) -> int:
    """Standard EMI formula, rounded to the paisa (A-02 as amended)."""
    if months <= 0:
        raise ValueError("months must be positive")
    p = rupees(balance_paise)
    if annual_rate == 0:
        return to_paise(p / months)
    r = annual_rate / 1200
    f = (1 + r) ** months
    return to_paise(p * r * f / (f - 1))


@dataclass(frozen=True)
class RateChange:
    effective: dt.date
    annual_rate: Decimal
    mode: str = KEEP_EMI
    bank_emi_paise: int | None = None


@dataclass(frozen=True)
class BankOutstanding:
    as_at: dt.date
    outstanding_paise: int
    source: str


@dataclass(frozen=True)
class LoanInput:
    principal_paise: int
    annual_rate: Decimal
    tenure_months: int
    first_emi_date: dt.date
    starting_emi_paise: int | None = None  # bank's EMI, if the customer entered it
    rate_changes: tuple[RateChange, ...] = ()
    bank_outstanding: BankOutstanding | None = None


@dataclass
class Row:
    n: int
    period_start: dt.date
    due_date: dt.date
    annual_rate: Decimal
    opening_paise: int
    interest_paise: int
    payment_paise: int
    principal_paise: int
    closing_paise: int
    flags: list[str] = field(default_factory=list)


@dataclass
class Result:
    rows: list[Row]
    starting_emi_paise: int
    closed: bool
    warnings: list[str]
    bank_difference: dict | None


def months_to_clear(balance_paise: int, annual_rate: Decimal, emi: int) -> int | None:
    """Whole months to clear a balance at a fixed rate and EMI, or None if never.

    Closed form, rounded up: n = -ln(1 - r*B/E) / ln(1 + r), with r = rate/1200
    (B/E when the rate is 0). Used when the tenure must be "kept" after it has
    been moving; the spreadsheet computes the same with ROUNDUP(NPER(...)).
    """
    b = rupees(balance_paise)
    e = rupees(emi)
    if annual_rate == 0:
        return int((b / e).to_integral_value(rounding="ROUND_CEILING"))
    r = annual_rate / 1200
    if e <= r * b:
        return None
    n = -((1 - r * b / e).ln()) / (1 + r).ln()
    return int(n.to_integral_value(rounding="ROUND_CEILING"))


def amortise(loan: LoanInput) -> Result:
    if loan.principal_paise <= 0:
        raise ValueError("loan amount must be positive")
    if not 1 <= loan.tenure_months <= 480:
        raise ValueError("tenure must be between 1 and 480 months")
    if loan.annual_rate < 0:
        raise ValueError("rate cannot be negative")

    changes = sorted(loan.rate_changes, key=lambda c: c.effective)
    emi = loan.starting_emi_paise or emi_paise(
        loan.principal_paise, loan.annual_rate, loan.tenure_months
    )
    starting_emi = emi
    rate = loan.annual_rate
    maturity: int | None = loan.tenure_months  # None means tenure is moving
    balance = loan.principal_paise
    applied = 0
    anchor_done = loan.bank_outstanding is None
    rows: list[Row] = []
    warnings: list[str] = []
    bank_difference = None

    n = 0
    while balance > 0 and n < MAX_MONTHS:
        n += 1
        start = add_months(loan.first_emi_date, n - 2)
        due = add_months(loan.first_emi_date, n - 1)
        flags: list[str] = []

        # A-06: dated bank outstanding restarts the projection.
        if not anchor_done and due > loan.bank_outstanding.as_at:
            anchor_done = True
            modelled = balance
            bank = loan.bank_outstanding.outstanding_paise
            bank_difference = {
                "as_at": loan.bank_outstanding.as_at.isoformat(),
                "source": loan.bank_outstanding.source,
                "bank_paise": bank,
                "modelled_paise": modelled,
                "difference_paise": bank - modelled,
                "applies_from_period": n,
            }
            balance = bank
            flags.append("bank_outstanding_applied")
            if balance <= 0:
                n -= 1
                break

        # A-03: the latest change effective on or before this period's start.
        # Several changes inside one period: only the last applies (no blend).
        ch = None
        while applied < len(changes) and changes[applied].effective <= start:
            ch = changes[applied]
            applied += 1
        if ch is not None:
            old_rate, rate = rate, ch.annual_rate
            flags.append("rate_change")
            if ch.mode == BANK_EMI:
                if ch.bank_emi_paise is None:
                    raise ValueError("bank_emi mode needs bank_emi_paise")
                emi = ch.bank_emi_paise
            elif ch.mode == KEEP_TENURE:
                if maturity is None:
                    remaining = months_to_clear(balance, old_rate, emi)
                    if remaining is None:
                        raise ValueError("cannot keep tenure: loan was not closing")
                    maturity = n - 1 + remaining
                remaining = maturity - n + 1
                if remaining < 1:
                    raise ValueError("cannot keep tenure: no months remaining")
                emi = emi_paise(balance, rate, remaining)
            elif ch.mode == KEEP_EMI:
                maturity = None
            else:
                raise ValueError(f"unknown mode {ch.mode}")

        opening = balance
        interest = monthly_interest_paise(opening, rate)
        due_total = opening + interest

        # A-07: final EMI is the exact remaining amount due.
        if (maturity is not None and n >= maturity) or due_total <= emi:
            payment = due_total
            if n > 1 and payment != emi:
                flags.append("final_emi_adjusted")
        else:
            payment = emi
        if payment <= interest:
            flags.append("emi_does_not_cover_interest")
        principal = payment - interest
        balance = opening - principal
        rows.append(Row(n, start, due, rate, opening, interest, payment, principal, balance, flags))

    closed = balance == 0
    if any("emi_does_not_cover_interest" in r.flags for r in rows):
        warnings.append("emi_does_not_cover_interest")
    if not closed:
        warnings.append("loan_does_not_close_within_600_months")
    return Result(rows, starting_emi, closed, warnings, bank_difference)


def result_to_dict(result: Result) -> dict:
    return {
        "starting_emi_paise": result.starting_emi_paise,
        "closed": result.closed,
        "months": len(result.rows),
        "total_interest_paise": sum(r.interest_paise for r in result.rows),
        "total_paid_paise": sum(r.payment_paise for r in result.rows),
        "warnings": result.warnings,
        "bank_difference": result.bank_difference,
        "schedule": [
            {
                "n": r.n,
                "period_start": r.period_start.isoformat(),
                "due_date": r.due_date.isoformat(),
                "annual_rate": str(r.annual_rate),
                "opening_paise": r.opening_paise,
                "interest_paise": r.interest_paise,
                "payment_paise": r.payment_paise,
                "principal_paise": r.principal_paise,
                "closing_paise": r.closing_paise,
                "flags": r.flags,
            }
            for r in result.rows
        ],
    }
