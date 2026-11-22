import { describe, expect, it } from "vitest";
import {
  calculatedKind,
  labelText,
  realityCheck,
  rupeesToPaise,
  type Figure,
  type LoanInput,
  type RealityCheck,
} from "../src/index.ts";

const loan: LoanInput = {
  principal: rupeesToPaise("5000000"),
  annualRatePercent: "8.5",
  tenureMonths: 240,
  firstEmiDate: "2020-04-05",
};

const figures = (r: RealityCheck): Figure<unknown>[] => [
  r.emisPaid,
  r.totalPaidSoFar,
  r.principalRepaidSoFar,
  r.interestPaidSoFar,
  r.currentOutstanding,
  r.futureInterest,
  r.remainingEmis,
  r.estimatedClosureDate,
];

describe("Loan Reality Check (FR-02, FR-03)", () => {
  const r = realityCheck({ loan, asOf: "2025-11-22", rateHistoryKnown: "yes" });

  it("counts EMIs due on or before the report date", () => {
    // 5 Apr 2020 to 5 Nov 2025 inclusive
    expect(r.emisPaid.value).toBe(68);
  });

  it("past and future add up exactly", () => {
    expect(r.principalRepaidSoFar.value + r.interestPaidSoFar.value).toBe(r.totalPaidSoFar.value);
    expect(loan.principal - r.principalRepaidSoFar.value).toBe(r.currentOutstanding.value);
    expect(r.interestPaidSoFar.value + r.futureInterest.value).toBe(r.schedule.totalInterest);
    expect(r.emisPaid.value + r.remainingEmis.value).toBe(240);
    expect(r.estimatedClosureDate.value).toBe("2040-03-05");
  });

  it("a new loan has paid nothing and owes the full amount", () => {
    const n = realityCheck({ loan, asOf: "2020-01-01", rateHistoryKnown: "yes" });
    expect(n.emisPaid.value).toBe(0);
    expect(n.totalPaidSoFar.value).toBe(0);
    expect(n.currentOutstanding.value).toBe(loan.principal);
    expect(n.futureInterest.value).toBe(n.schedule.totalInterest);
  });

  it("every figure has a label and a plain-English explanation (S-01, FR-13)", () => {
    for (const f of figures(r)) {
      expect(f.label.kind).toBeTruthy();
      expect(f.label.source).toBeTruthy();
      expect(f.explanation.length).toBeGreaterThan(10);
    }
  });
});

describe("labels (S-01, S-02)", () => {
  it("dates-counted EMIs are Estimated; with a full rate history the rest are Modelled at best", () => {
    const r = realityCheck({ loan, asOf: "2025-11-22", rateHistoryKnown: "yes" });
    expect(r.emisPaid.label).toEqual({ kind: "estimated", source: "calculated" });
    expect(r.interestPaidSoFar.label.kind).toBe("estimated");
  });

  it("with the customer's own EMI count and a full rate history, past figures are Modelled", () => {
    const r = realityCheck({ loan, asOf: "2025-11-22", rateHistoryKnown: "yes", emisPaid: 68 });
    expect(r.emisPaid.label).toEqual({ kind: "actual", source: "customer-provided" });
    expect(r.interestPaidSoFar.label).toEqual({ kind: "modelled", source: "calculated" });
    expect(r.futureInterest.label.kind).toBe("modelled");
  });

  it("an unknown rate history makes past and future figures Estimated", () => {
    const r = realityCheck({
      loan,
      asOf: "2025-11-22",
      rateHistoryKnown: "not_sure",
      emisPaid: 68,
    });
    expect(r.interestPaidSoFar.label.kind).toBe("estimated");
    expect(r.futureInterest.label.kind).toBe("estimated");
    expect(r.interestPaidSoFar.assumptions.join(" ")).toMatch(/rate changes may be missing/);
  });

  it("a bank balance with no EMI due since is Actual, from the bank", () => {
    const r = realityCheck({
      loan: {
        ...loan,
        bankOutstanding: {
          asAt: "2025-11-10",
          amount: rupeesToPaise("4200000"),
          source: "bank-confirmed",
          document: "bank app",
        },
      },
      asOf: "2025-11-22",
      rateHistoryKnown: "yes",
      emisPaid: 68,
    });
    expect(r.currentOutstanding.value).toBe(rupeesToPaise("4200000"));
    expect(r.currentOutstanding.label).toEqual({ kind: "actual", source: "bank-confirmed" });
    expect(labelText(r.currentOutstanding.label)).toBe("Actual · from your bank");
    expect(r.futureInterest.label.kind).toBe("modelled");
    expect(r.schedule.bankDifference?.difference).not.toBe(0);
  });

  it("an older bank balance is worked forward and is never labelled Actual (S-02)", () => {
    const r = realityCheck({
      loan: {
        ...loan,
        bankOutstanding: {
          asAt: "2024-03-31",
          amount: rupeesToPaise("4400000"),
          source: "bank-confirmed",
        },
      },
      asOf: "2025-11-22",
      rateHistoryKnown: "yes",
      emisPaid: 68,
    });
    expect(r.currentOutstanding.label.kind).toBe("modelled");
    expect(r.currentOutstanding.label.source).toBe("calculated");
  });

  it("a calculation is never Actual, whatever its inputs", () => {
    expect(calculatedKind("actual", "actual")).toBe("modelled");
    expect(calculatedKind("actual", "illustrative")).toBe("illustrative");
    expect(calculatedKind("modelled", "estimated")).toBe("estimated");
  });

  it("flags an EMI count that differs from the dates, and uses the customer's", () => {
    const r = realityCheck({ loan, asOf: "2025-11-22", rateHistoryKnown: "yes", emisPaid: 66 });
    expect(r.emisPaid.value).toBe(66);
    expect(r.issues.map((i) => i.code)).toContain("emis_paid_differs_from_dates");
  });
});
