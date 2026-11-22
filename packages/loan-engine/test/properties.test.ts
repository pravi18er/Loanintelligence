/** Invariants over many generated loans (TEST_STRATEGY.md section 4). */
import fc from "fast-check";
import { describe, expect, it } from "vitest";
import { addMonths, amortise, paise, type LoanInput, type RateChange } from "../src/index.ts";

const rate = fc.integer({ min: 0, max: 1500 }).map((bp) => (bp / 100).toString());

const loan: fc.Arbitrary<LoanInput> = fc
  .record({
    principal: fc.integer({ min: 10_000_00, max: 20_00_00_000_00 }),
    rate: fc.integer({ min: 500, max: 1500 }).map((bp) => (bp / 100).toString()),
    tenure: fc.integer({ min: 1, max: 480 }),
    day: fc.integer({ min: 1, max: 31 }),
    month: fc.integer({ min: 1, max: 12 }),
    year: fc.integer({ min: 2005, max: 2025 }),
    changes: fc.array(
      fc.record({
        offset: fc.integer({ min: 1, max: 300 }),
        rate,
        adjustment: fc.constantFrom("keep_emi", "keep_tenure") as fc.Arbitrary<
          "keep_emi" | "keep_tenure"
        >,
      }),
      { maxLength: 4 },
    ),
  })
  .map(({ principal, rate: r, tenure, day, month, year, changes }) => {
    const first = `${year}-${String(month).padStart(2, "0")}-${String(Math.min(day, 28)).padStart(2, "0")}`;
    const seen = new Set<string>();
    const rateChanges: RateChange[] = [];
    for (const c of changes) {
      const effectiveDate = addMonths(first, c.offset);
      if (seen.has(effectiveDate)) continue;
      seen.add(effectiveDate);
      rateChanges.push({ effectiveDate, annualRatePercent: c.rate, adjustment: c.adjustment });
    }
    return {
      principal: paise(principal),
      annualRatePercent: r,
      tenureMonths: tenure,
      firstEmiDate: first,
      rateChanges,
    };
  });

function safeAmortise(l: LoanInput) {
  try {
    return amortise(l);
  } catch {
    return null; // e.g. keep tenure requested after a non-repaying period
  }
}

describe("schedule invariants", () => {
  it("rows reconcile, balances never go negative, totals add up, and closing loans end at zero", () => {
    fc.assert(
      fc.property(loan, (l) => {
        const s = safeAmortise(l);
        if (!s) return;
        let prevClosing: number = l.principal;
        for (const r of s.rows) {
          expect(r.interest + r.principal).toBe(r.payment);
          expect(r.opening - r.principal).toBe(r.closing);
          expect(r.opening).toBe(prevClosing);
          expect(r.closing).toBeGreaterThanOrEqual(0);
          prevClosing = r.closing;
        }
        expect(s.rows.reduce((a, r) => a + r.interest, 0)).toBe(s.totalInterest);
        if (s.closed) {
          expect(s.rows.at(-1)?.closing).toBe(0);
          expect(s.rows.reduce((a, r) => a + r.principal, 0)).toBe(l.principal);
        }
      }),
      { numRuns: 300 },
    );
  });

  it("without rate changes, the loan closes by its tenure with no extra instalment", () => {
    fc.assert(
      fc.property(loan, (l) => {
        const s = amortise({ ...l, rateChanges: [] });
        expect(s.closed).toBe(true);
        // Rounding the EMI up to the paisa repays a little faster than the exact
        // EMI. On a small loan over a long term that can add up to more than one
        // EMI, so the loan closes a month early with a smaller final EMI (A-07):
        // e.g. Rs 10,000.19 at 14.92% over 478 months closes in month 477.
        expect(s.rows.length).toBeLessThanOrEqual(l.tenureMonths);
        if (s.rows.length < l.tenureMonths) {
          expect(s.rows.at(-1)?.payment).toBeLessThan(s.rows[0]?.payment ?? 0);
        }
      }),
      { numRuns: 300 },
    );
  });

  it("a month where the EMI does not cover interest is always flagged", () => {
    fc.assert(
      fc.property(loan, (l) => {
        const s = safeAmortise(l);
        if (!s) return;
        for (const r of s.rows) {
          if (r.payment <= r.interest) expect(r.flags).toContain("emi_does_not_cover_interest");
        }
      }),
      { numRuns: 300 },
    );
  });

  it("a higher fixed rate never gives less total interest", () => {
    // Rounding the EMI to the paisa moves total interest by up to about Rs 140
    // on a small, long, high-rate loan (e.g. Rs 10,000.27 over 419 months: 14.62%
    // pays Rs 80 more interest than 14.63%, because 14.62% rounds its EMI down).
    // So the property is checked for rate rises of 0.25% or more, which always
    // outweigh that rounding.
    fc.assert(
      fc.property(loan, fc.integer({ min: 25, max: 300 }), (l, bump) => {
        const lower = amortise({ ...l, rateChanges: [] });
        const higherRate = (Number(l.annualRatePercent) * 100 + bump) / 100;
        const higher = amortise({
          ...l,
          annualRatePercent: higherRate.toString(),
          rateChanges: [],
        });
        expect(higher.totalInterest).toBeGreaterThanOrEqual(lower.totalInterest);
      }),
      { numRuns: 200 },
    );
  });

  it("is deterministic", () => {
    fc.assert(
      fc.property(loan, (l) => {
        expect(safeAmortise(l)).toEqual(safeAmortise(l));
      }),
      { numRuns: 100 },
    );
  });
});
