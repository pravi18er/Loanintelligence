import { describe, expect, it } from "vitest";
import { amortise, paise, type LoanInput } from "../src/index.ts";
import { loadScenarios, type Scenario } from "./scenarios.ts";

function toEngineInput(s: Scenario): LoanInput {
  const i = s.input;
  return {
    principal: paise(i.principal_paise),
    annualRatePercent: i.annual_rate,
    tenureMonths: i.tenure_months,
    firstEmiDate: i.first_emi_date,
    ...(i.starting_emi_paise === null ? {} : { startingEmi: paise(i.starting_emi_paise) }),
    rateChanges: i.rate_changes.map((c) => ({
      effectiveDate: c.effective,
      annualRatePercent: c.annual_rate,
      adjustment: c.mode,
      ...(c.bank_emi_paise === null ? {} : { bankEmi: paise(c.bank_emi_paise) }),
    })),
    ...(i.bank_outstanding === null
      ? {}
      : {
          bankOutstanding: {
            asAt: i.bank_outstanding.as_at,
            amount: paise(i.bank_outstanding.outstanding_paise),
            source: "bank-confirmed" as const,
            document: i.bank_outstanding.source,
          },
        }),
  };
}

describe.each(loadScenarios().map((s) => [s.id, s] as const))(
  "golden scenario %s matches the Python reference to the paisa",
  (_id, s) => {
    const result = amortise(toEngineInput(s));
    const e = s.expected;

    it("summary", () => {
      expect(result.startingEmi).toBe(e.starting_emi_paise);
      expect(result.closed).toBe(e.closed);
      expect(result.rows).toHaveLength(e.months);
      expect(result.totalInterest).toBe(e.total_interest_paise);
      expect(result.totalPaid).toBe(e.total_paid_paise);
      expect(result.warnings).toEqual(e.warnings);
    });

    it("bank difference", () => {
      const d = e.bank_difference;
      expect(
        result.bankDifference && {
          as_at: result.bankDifference.asAt,
          source: result.bankDifference.document,
          bank_paise: result.bankDifference.bank,
          modelled_paise: result.bankDifference.modelled,
          difference_paise: result.bankDifference.difference,
          applies_from_period: result.bankDifference.appliesFromPeriod,
        },
      ).toEqual(d);
    });

    it("every row", () => {
      const got = result.rows.map((r) => ({
        n: r.n,
        period_start: r.periodStart,
        due_date: r.dueDate,
        annual_rate: Number(r.annualRatePercent),
        opening_paise: r.opening,
        interest_paise: r.interest,
        payment_paise: r.payment,
        principal_paise: r.principal,
        closing_paise: r.closing,
        flags: r.flags,
      }));
      const want = e.schedule.map((r) => ({ ...r, annual_rate: Number(r.annual_rate) }));
      expect(got).toEqual(want);
    });
  },
);
