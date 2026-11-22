/**
 * Named test cases for the approved rules (TEST_STRATEGY.md section 2).
 * The same expected values are asserted in reference/python/test_loan_reference.py.
 */
import { describe, expect, it } from "vitest";
import {
  addMonths,
  amortise,
  calculateEmi,
  displayRupees,
  InvalidLoanInputError,
  monthlyInterest,
  paise,
  rupeesToPaise,
  validateLoan,
  type LoanInput,
  type RateChange,
} from "../src/index.ts";
import { Decimal } from "../src/decimal.ts";

const L50 = rupeesToPaise("5000000");
const base = (over: Partial<LoanInput> = {}): LoanInput => ({
  principal: L50,
  annualRatePercent: "8.5",
  tenureMonths: 240,
  firstEmiDate: "2020-04-05",
  ...over,
});
const change = (
  effectiveDate: string,
  rate: string,
  extra: Partial<RateChange> = {},
): RateChange => ({
  effectiveDate,
  annualRatePercent: rate,
  ...extra,
});
const rateOn = (loan: LoanInput, due: string) =>
  amortise(loan).rows.find((r) => r.dueDate === due)?.annualRatePercent;

describe("A-01 monthly reducing-balance interest", () => {
  it("T-A01-1 month 1 interest on Rs 50 lakh at 8.5% is Rs 35,416.67", () => {
    expect(monthlyInterest(L50, new Decimal("8.5"))).toBe(3_541_667);
  });
  it("T-A01-2 every month's interest uses that month's opening balance", () => {
    for (const r of amortise(base()).rows) {
      expect(r.interest).toBe(monthlyInterest(r.opening, new Decimal("8.5")));
    }
  });
  it("T-A01-3 0% interest: no interest and EMI = loan / tenure", () => {
    const s = amortise(
      base({ principal: rupeesToPaise("1200000"), annualRatePercent: "0", tenureMonths: 12 }),
    );
    expect(s.totalInterest).toBe(0);
    expect(s.startingEmi).toBe(rupeesToPaise("100000"));
  });
  it("T-A01-4 known EMIs", () => {
    expect(calculateEmi(L50, new Decimal("8.5"), 240)).toBe(4_339_116);
    expect(calculateEmi(rupeesToPaise("3000000"), new Decimal("9"), 240)).toBe(2_699_178);
    expect(displayRupees(paise(4_339_116))).toBe(43_391);
    expect(displayRupees(paise(2_699_178))).toBe(26_992);
  });
});

describe("A-02 paisa rounding (amended by B-06)", () => {
  it("T-A02-1 Rs 50 lakh at 8.5%: final EMI Rs 43,392.20, total interest Rs 54,13,879.44", () => {
    const s = amortise(base());
    expect(s.rows).toHaveLength(240);
    expect(s.rows.at(-1)?.payment).toBe(4_339_220);
    expect(s.totalInterest).toBe(541_387_944);
    expect(displayRupees(s.totalInterest)).toBe(5_413_879);
  });
  it("T-A02-2 half-up at the paisa and at the rupee", () => {
    expect(rupeesToPaise("1.005")).toBe(101);
    expect(rupeesToPaise("1.0049")).toBe(100);
    expect(displayRupees(paise(150))).toBe(2);
    expect(displayRupees(paise(149))).toBe(1);
  });
});

describe("A-03 rate change from the first period starting on or after its date (B-02)", () => {
  it("T-A03-1 effective 1 June: 5 June EMI old rate, 5 July EMI new rate", () => {
    const loan = base({ rateChanges: [change("2022-06-01", "9")] });
    expect(rateOn(loan, "2022-06-05")).toBe("8.5");
    expect(rateOn(loan, "2022-07-05")).toBe("9");
  });
  it("T-A03-2 effective on a period start (5 June) starts with that period", () => {
    const loan = base({ rateChanges: [change("2022-06-05", "9")] });
    expect(rateOn(loan, "2022-06-05")).toBe("8.5");
    expect(rateOn(loan, "2022-07-05")).toBe("9");
  });
  it("T-A03-3 effective 6 June starts with the period beginning 5 July", () => {
    const loan = base({ rateChanges: [change("2022-06-06", "9")] });
    expect(rateOn(loan, "2022-07-05")).toBe("8.5");
    expect(rateOn(loan, "2022-08-05")).toBe("9");
  });
  it("T-A03-4 two changes inside one period: the later applies, no blend", () => {
    const loan = base({ rateChanges: [change("2022-06-10", "9"), change("2022-06-20", "9.5")] });
    expect(rateOn(loan, "2022-08-05")).toBe("9.5");
  });
  it("T-A03-5 a change dated before the loan starts is flagged for checking", () => {
    const issues = validateLoan(base({ rateChanges: [change("2019-01-01", "9")] }));
    expect(issues.map((i) => i.code)).toContain("rate_change_before_loan");
  });
});

describe("A-04 EMI and tenure options", () => {
  it("T-A04-1 keep EMI on a rate rise extends the tenure", () => {
    const s = amortise(
      base({ rateChanges: [change("2022-06-01", "9.5", { adjustment: "keep_emi" })] }),
    );
    expect(new Set(s.rows.slice(0, -1).map((r) => r.payment))).toEqual(new Set([4_339_116]));
    expect(s.rows.length).toBeGreaterThan(240);
  });
  it("T-A04-2 keep tenure recalculates the EMI and keeps the end date", () => {
    const s = amortise(
      base({ rateChanges: [change("2022-06-01", "9.5", { adjustment: "keep_tenure" })] }),
    );
    expect(s.rows).toHaveLength(240);
    expect(s.rows[30]?.payment).toBeGreaterThan(4_339_116);
  });
  it("T-A04-3 a bank-revised EMI is used exactly", () => {
    const s = amortise(
      base({
        rateChanges: [
          change("2022-06-01", "9.5", { adjustment: "bank_emi", bankEmi: paise(4_600_000) }),
        ],
      }),
    );
    expect(s.rows[30]?.payment).toBe(4_600_000);
  });
  it("T-A04-4 keep EMI on a rate cut shortens the tenure", () => {
    const s = amortise(base({ rateChanges: [change("2022-06-01", "7.5")] }));
    expect(s.rows.length).toBeLessThan(240);
  });
  it("T-A04-5 the default is keep EMI", () => {
    const a = amortise(base({ rateChanges: [change("2022-06-01", "9.5")] }));
    const b = amortise(
      base({ rateChanges: [change("2022-06-01", "9.5", { adjustment: "keep_emi" })] }),
    );
    expect(a).toEqual(b);
  });
});

describe("A-06 dated bank figures", () => {
  const model = amortise(base());
  const withBank = amortise(
    base({
      bankOutstanding: {
        asAt: "2023-03-31",
        amount: rupeesToPaise("4500000"),
        source: "bank-confirmed",
        document: "annual statement",
      },
    }),
  );
  const d = withBank.bankDifference;

  it("T-A06-1 the bank balance becomes the opening of the period its date falls in", () => {
    expect(d).not.toBeNull();
    const row = withBank.rows[(d?.appliesFromPeriod ?? 0) - 1];
    expect((row?.periodStart ?? "") <= "2023-03-31").toBe(true);
    expect((row?.dueDate ?? "") > "2023-03-31").toBe(true);
    expect(row?.opening).toBe(rupeesToPaise("4500000"));
  });
  it("T-A06-1b it is compared with the model on the same date", () => {
    const lastDueBefore = model.rows[(d?.appliesFromPeriod ?? 0) - 2];
    expect((lastDueBefore?.dueDate ?? "") <= "2023-03-31").toBe(true);
    expect(d?.modelled).toBe(lastDueBefore?.closing);
  });
  it("T-A06-2 and T-A06-5 the modelled history before that date is unchanged", () => {
    const before = (d?.appliesFromPeriod ?? 1) - 1;
    expect(withBank.rows.slice(0, before)).toEqual(model.rows.slice(0, before));
  });
  it("T-A06-2 the difference is kept, with its source", () => {
    expect(d?.difference).toBe((d?.bank ?? 0) - (d?.modelled ?? 0));
    expect(d?.document).toBe("annual statement");
    expect(d?.source).toBe("bank-confirmed");
  });
  it("T-A06-3 an undated bank figure is rejected", () => {
    expect(() =>
      amortise(
        base({
          bankOutstanding: { asAt: "", amount: rupeesToPaise("4500000"), source: "bank-confirmed" },
        }),
      ),
    ).toThrow(InvalidLoanInputError);
  });
});

describe("A-07 final EMI is exactly what remains due (B-04)", () => {
  it("T-A07-1 calculated EMI: closes in exactly 240 months, no extra EMI", () => {
    const s = amortise(base());
    expect(s.rows).toHaveLength(240);
    expect(s.rows.at(-1)?.closing).toBe(0);
  });
  it("T-A07-2 bank-rounded EMI Rs 43,391: 240th EMI is Rs 43,492.55, no 241st", () => {
    const s = amortise(base({ startingEmi: rupeesToPaise("43391") }));
    expect(s.rows).toHaveLength(240);
    expect(s.rows.at(-1)?.payment).toBe(4_349_255);
    expect(displayRupees(s.rows.at(-1)?.payment ?? paise(0))).toBe(43_493);
  });
  it("T-A07-3 with tenure moving, the final payment is balance + interest and may be smaller", () => {
    const last = amortise(base({ rateChanges: [change("2022-06-01", "7.5")] })).rows.at(-1);
    expect(last?.payment).toBe((last?.opening ?? 0) + (last?.interest ?? 0));
    expect(last?.payment).toBeLessThan(4_339_116);
  });
});

describe("A-08 and dates (B-05)", () => {
  it("T-A08-1 the first period starts one calendar month before EMI 1", () => {
    expect(amortise(base()).rows[0]?.periodStart).toBe("2020-03-05");
  });
  it("T-A08-3 EMI day 31 uses the last day of shorter months, then returns", () => {
    expect([0, 1, 2, 3, 4].map((m) => addMonths("2021-01-31", m))).toEqual([
      "2021-01-31",
      "2021-02-28",
      "2021-03-31",
      "2021-04-30",
      "2021-05-31",
    ]);
    expect(addMonths("2024-01-30", 1)).toBe("2024-02-29");
  });
});

describe("S-05 invalid repayment scenarios are flagged", () => {
  it("EMI not covering interest is flagged and the loan reported as not closing", () => {
    const s = amortise(base({ annualRatePercent: "7", rateChanges: [change("2021-01-01", "14")] }));
    expect(s.warnings).toEqual([
      "emi_does_not_cover_interest",
      "loan_does_not_close_within_600_months",
    ]);
  });
  it("invalid inputs give plain-English errors", () => {
    const codes = validateLoan(
      base({ principal: paise(0), tenureMonths: 481, annualRatePercent: "-1" }),
    ).map((i) => i.code);
    expect(codes).toEqual(
      expect.arrayContaining(["principal_invalid", "tenure_invalid", "rate_out_of_range"]),
    );
    expect(() => amortise(base({ principal: paise(0) }))).toThrow(InvalidLoanInputError);
  });
  it("a likely percentage typo is a check, not an error", () => {
    expect(validateLoan(base({ annualRatePercent: "0.085" }))[0]?.severity).toBe("check");
  });
});

describe("A-07 rounding can close a small, long loan a month early", () => {
  it("Rs 10,000.19 at 14.92% over 478 months closes in month 477 with a smaller final EMI", () => {
    const s = amortise({
      principal: paise(1_000_019),
      annualRatePercent: "14.92",
      tenureMonths: 478,
      firstEmiDate: "2005-01-01",
    });
    expect(s.rows).toHaveLength(477);
    expect(s.rows[0]?.payment).toBe(12_468);
    expect(s.rows.at(-1)?.payment).toBe(10_757);
    expect(s.closed).toBe(true);
  });
});
