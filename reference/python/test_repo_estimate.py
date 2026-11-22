"""Repo-linked estimate cases; the same values are asserted in the engine's repo-estimate.test.ts."""

from __future__ import annotations

import datetime as dt
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from loan_reference import LoanInput, RateChange  # noqa: E402
from repo_estimate import RepoEstimate, estimated_changes  # noqa: E402

LOAN = LoanInput(500_000_000, D("8.4"), 240, dt.date(2020, 1, 5))
TODAY = dt.date(2026, 11, 22)


def got(loan=LOAN, est=RepoEstimate(), as_of=TODAY):
    return [(c.effective.isoformat(), c.annual_rate) for c in estimated_changes(loan, est, as_of)]


class RepoEstimateRule(unittest.TestCase):
    def test_quarterly_resets_keep_spread(self):
        self.assertEqual(got()[:3], [("2020-06-05", D("7.25")), ("2022-06-05", D("7.65")), ("2022-09-05", D("8.65"))])

    def test_repo_announced_on_reset_date(self):
        self.assertEqual(got()[-1], ("2025-12-05", D("8.50")))

    def test_entered_change_replaces_interval_and_reanchors(self):
        loan = LoanInput(**{**LOAN.__dict__, "rate_changes": (RateChange(dt.date(2023, 6, 1), D("9.4")),)})
        g = got(loan)
        self.assertNotIn("2023-03-05", [d for d, _ in g])
        self.assertIn(("2025-03-05", D("9.15")), g)

    def test_sanction_spread_priority(self):
        self.assertEqual(got(est=RepoEstimate(3, None, D("2.5")), as_of=dt.date(2020, 3, 31)), [("2020-03-05", D("7.65"))])

    def test_no_repo_for_anchor(self):
        self.assertEqual(got(LoanInput(500_000_000, D("8.4"), 240, dt.date(2018, 1, 5))), [])

    def test_stops_at_report_date(self):
        self.assertEqual(got(as_of=dt.date(2022, 6, 4)), [("2020-06-05", D("7.25"))])

    def test_invalid(self):
        with self.assertRaises(ValueError):
            got(est=RepoEstimate(2))
        with self.assertRaises(ValueError):
            got(est=RepoEstimate(3, dt.date(2019, 12, 5)))


if __name__ == "__main__":
    unittest.main()
