"""MCLR reference cases; the same values are asserted in the engine's benchmarks.test.ts."""

from __future__ import annotations

import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from benchmarks import mclr_on, repo_rate_on  # noqa: E402


class MclrReference(unittest.TestCase):
    def test_revision_in_force(self):
        self.assertEqual(mclr_on("sbi", "one_year", dt.date(2022, 6, 15)), "7.40")
        self.assertEqual(mclr_on("sbi", "one_year", dt.date(2022, 6, 14)), "7.20")
        self.assertEqual(mclr_on("bank_of_baroda", "one_year", dt.date(2019, 12, 12)), "8.25")
        self.assertEqual(mclr_on("bank_of_baroda", "six_month", dt.date(2026, 11, 22)), "8.50")

    def test_outside_history_or_unpublished_tenor(self):
        self.assertIsNone(mclr_on("sbi", "one_year", dt.date(2016, 3, 31)))
        self.assertIsNone(mclr_on("bank_of_baroda", "five_year", dt.date(2020, 1, 1)))
        self.assertEqual(mclr_on("bank_of_baroda", "five_year", dt.date(2017, 6, 1)), "8.65")


class RepoRate(unittest.TestCase):
    def test_rate_in_force(self):
        self.assertEqual(repo_rate_on(dt.date(2019, 10, 1)), "5.40")
        self.assertEqual(repo_rate_on(dt.date(2019, 10, 4)), "5.15")
        self.assertEqual(repo_rate_on(dt.date(2022, 5, 3)), "4.00")
        self.assertEqual(repo_rate_on(dt.date(2026, 11, 22)), "5.50")
        self.assertIsNone(repo_rate_on(dt.date(2019, 8, 6)))


if __name__ == "__main__":
    unittest.main()
