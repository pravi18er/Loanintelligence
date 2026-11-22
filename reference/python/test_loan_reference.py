"""Rule tests for the Python reference (TEST_STRATEGY.md section 2).

Run from the repository root: python3 -I -m unittest discover -s reference/python
"""

from __future__ import annotations

import datetime as dt
import sys
import unittest
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
    add_months,
    amortise,
    emi_paise,
    monthly_interest_paise,
    to_paise,
)

L50 = 500_000_000  # Rs 50 lakh in paise
EMI_DAY_5 = dt.date(2020, 4, 5)


def base(**kw) -> LoanInput:
    args = dict(
        principal_paise=L50,
        annual_rate=D("8.5"),
        tenure_months=240,
        first_emi_date=EMI_DAY_5,
    )
    args.update(kw)
    return LoanInput(**args)


class A01Interest(unittest.TestCase):
    def test_month_one_interest(self):
        # 50,00,000 x 8.5 / 1200 = 35,416.666... -> 35,416.67
        self.assertEqual(monthly_interest_paise(L50, D("8.5")), 3_541_667)

    def test_interest_uses_opening_balance_each_month(self):
        for row in amortise(base()).rows:
            self.assertEqual(row.interest_paise, monthly_interest_paise(row.opening_paise, D("8.5")))

    def test_zero_interest(self):
        r = amortise(LoanInput(1_200_000_00, D("0"), 12, dt.date(2024, 1, 10)))
        self.assertTrue(all(x.interest_paise == 0 for x in r.rows))
        self.assertEqual(r.starting_emi_paise, 100_000_00)

    def test_known_emis(self):
        self.assertEqual(emi_paise(L50, D("8.5"), 240), 4_339_116)  # Rs 43,391.16
        self.assertEqual(emi_paise(300_000_000, D("9"), 240), 2_699_178)  # Rs 26,991.78


class A02PaisaRounding(unittest.TestCase):
    def test_half_up(self):
        self.assertEqual(to_paise(D("1.005")), 101)
        self.assertEqual(to_paise(D("1.0049")), 100)

    def test_every_amount_is_whole_paise_and_rows_reconcile(self):
        for row in amortise(base()).rows:
            self.assertEqual(row.interest_paise + row.principal_paise, row.payment_paise)
            self.assertEqual(row.opening_paise - row.principal_paise, row.closing_paise)

    def test_closes_exactly(self):
        r = amortise(base())
        self.assertTrue(r.closed)
        self.assertEqual(len(r.rows), 240)
        self.assertEqual(r.rows[-1].closing_paise, 0)


class A03RateChangePeriod(unittest.TestCase):
    def rate_by_due(self, effective: dt.date) -> dict:
        r = amortise(base(rate_changes=(RateChange(effective, D("9"), KEEP_EMI),)))
        return {row.due_date: row.annual_rate for row in r.rows}

    def test_effective_1_june_first_affects_5_july_emi(self):
        rates = self.rate_by_due(dt.date(2022, 6, 1))
        self.assertEqual(rates[dt.date(2022, 6, 5)], D("8.5"))
        self.assertEqual(rates[dt.date(2022, 7, 5)], D("9"))

    def test_effective_on_period_start(self):
        rates = self.rate_by_due(dt.date(2022, 6, 5))
        self.assertEqual(rates[dt.date(2022, 6, 5)], D("8.5"))
        self.assertEqual(rates[dt.date(2022, 7, 5)], D("9"))

    def test_effective_day_after_period_start(self):
        rates = self.rate_by_due(dt.date(2022, 6, 6))
        self.assertEqual(rates[dt.date(2022, 7, 5)], D("8.5"))
        self.assertEqual(rates[dt.date(2022, 8, 5)], D("9"))

    def test_two_changes_in_one_period_no_blend(self):
        r = amortise(base(rate_changes=(
            RateChange(dt.date(2022, 6, 10), D("9"), KEEP_EMI),
            RateChange(dt.date(2022, 6, 20), D("9.5"), KEEP_EMI),
        )))
        rates = {row.due_date: row.annual_rate for row in r.rows}
        self.assertEqual(rates[dt.date(2022, 8, 5)], D("9.5"))


class A04EmiOrTenure(unittest.TestCase):
    rise = dt.date(2022, 6, 1)

    def test_keep_emi_extends_tenure(self):
        r = amortise(base(rate_changes=(RateChange(self.rise, D("9.5"), KEEP_EMI),)))
        regular = {row.payment_paise for row in r.rows[:-1]}
        self.assertEqual(regular, {4_339_116})
        self.assertGreater(len(r.rows), 240)

    def test_keep_tenure_recalculates_emi(self):
        r = amortise(base(rate_changes=(RateChange(self.rise, D("9.5"), KEEP_TENURE),)))
        self.assertEqual(len(r.rows), 240)
        self.assertGreater(r.rows[30].payment_paise, 4_339_116)

    def test_bank_emi_used_exactly(self):
        r = amortise(base(rate_changes=(RateChange(self.rise, D("9.5"), BANK_EMI, 4_600_000),)))
        self.assertEqual(r.rows[30].payment_paise, 4_600_000)

    def test_rate_cut_keep_emi_shortens(self):
        r = amortise(base(rate_changes=(RateChange(self.rise, D("7.5"), KEEP_EMI),)))
        self.assertLess(len(r.rows), 240)

    def test_default_mode_is_keep_emi(self):
        self.assertEqual(RateChange(self.rise, D("9")).mode, KEEP_EMI)


class A06BankFigures(unittest.TestCase):
    def setUp(self):
        self.model = amortise(base())
        self.withbank = amortise(base(bank_outstanding=BankOutstanding(
            dt.date(2023, 3, 31), 450_000_000, "annual statement")))

    def test_history_unchanged_before_bank_date(self):
        d = self.withbank.bank_difference
        n = d["applies_from_period"]
        for a, b in zip(self.model.rows[: n - 1], self.withbank.rows[: n - 1]):
            self.assertEqual(a, b)

    def test_projection_restarts_from_bank_figure(self):
        d = self.withbank.bank_difference
        row = self.withbank.rows[d["applies_from_period"] - 1]
        # The balance dated 31 Mar 2023 is the opening of the period it falls in
        # (5 Mar to 5 Apr), so the first EMI due after the date uses it.
        self.assertLessEqual(row.period_start, dt.date(2023, 3, 31))
        self.assertGreater(row.due_date, dt.date(2023, 3, 31))
        self.assertEqual(row.opening_paise, 450_000_000)

    def test_compared_with_model_on_the_same_date(self):
        d = self.withbank.bank_difference
        last_due_before = self.model.rows[d["applies_from_period"] - 2]
        self.assertLessEqual(last_due_before.due_date, dt.date(2023, 3, 31))
        self.assertEqual(d["modelled_paise"], last_due_before.closing_paise)

    def test_difference_preserved(self):
        d = self.withbank.bank_difference
        self.assertEqual(d["difference_paise"], d["bank_paise"] - d["modelled_paise"])
        self.assertEqual(d["source"], "annual statement")


class A07FinalEmi(unittest.TestCase):
    def test_bank_rounded_emi_absorbed_no_extra_instalment(self):
        r = amortise(base(starting_emi_paise=4_339_100))
        self.assertEqual(len(r.rows), 240)
        self.assertEqual(r.rows[-1].payment_paise, 4_349_255)  # Rs 43,492.55
        self.assertEqual(r.rows[-1].closing_paise, 0)

    def test_final_payment_is_balance_plus_interest(self):
        last = amortise(base()).rows[-1]
        self.assertEqual(last.payment_paise, last.opening_paise + last.interest_paise)

    def test_moving_tenure_final_payment_may_be_smaller(self):
        r = amortise(base(rate_changes=(RateChange(dt.date(2022, 6, 1), D("7.5"), KEEP_EMI),)))
        last = r.rows[-1]
        self.assertLess(last.payment_paise, 4_339_116)
        self.assertEqual(last.payment_paise, last.opening_paise + last.interest_paise)


class A08AndDates(unittest.TestCase):
    def test_first_period_starts_one_month_before_emi_1(self):
        self.assertEqual(amortise(base()).rows[0].period_start, dt.date(2020, 3, 5))

    def test_month_end_dates(self):
        got = [add_months(dt.date(2021, 1, 31), i) for i in range(5)]
        self.assertEqual(got, [dt.date(2021, 1, 31), dt.date(2021, 2, 28), dt.date(2021, 3, 31),
                               dt.date(2021, 4, 30), dt.date(2021, 5, 31)])

    def test_leap_year(self):
        self.assertEqual(add_months(dt.date(2024, 1, 30), 1), dt.date(2024, 2, 29))


class Safeguards(unittest.TestCase):
    def test_emi_not_covering_interest_is_flagged(self):
        r = amortise(base(annual_rate=D("7"), rate_changes=(
            RateChange(dt.date(2021, 1, 1), D("14"), KEEP_EMI),)))
        self.assertIn("emi_does_not_cover_interest", r.warnings)
        self.assertFalse(r.closed)

    def test_invalid_inputs_rejected(self):
        with self.assertRaises(ValueError):
            amortise(base(principal_paise=0))
        with self.assertRaises(ValueError):
            amortise(base(tenure_months=481))
        with self.assertRaises(ValueError):
            amortise(base(annual_rate=D("-1")))


if __name__ == "__main__":
    unittest.main()
