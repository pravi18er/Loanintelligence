import { describe, expect, it } from "vitest";
import { APPROVED_RULES, ENGINE_VERSION } from "../src/index.ts";
import { loadScenarios } from "./scenarios.ts";

const scenarios = loadScenarios();

describe("engine package", () => {
  it("exposes a version and the approved rule list", () => {
    expect(ENGINE_VERSION).toMatch(/^\d+\.\d+\.\d+$/);
    expect(APPROVED_RULES).toHaveLength(8);
  });
});

describe("golden scenarios load and are internally consistent", () => {
  it("has scenarios to test against", () => {
    expect(scenarios.length).toBeGreaterThanOrEqual(12);
  });

  describe.each(scenarios.map((s) => [s.id, s] as const))("%s", (_id, s) => {
    const rows = s.expected.schedule;

    it("uses whole paise for every amount (A-02 as amended by B-06)", () => {
      for (const r of rows) {
        for (const v of [
          r.opening_paise,
          r.interest_paise,
          r.payment_paise,
          r.principal_paise,
          r.closing_paise,
        ]) {
          expect(Number.isSafeInteger(v)).toBe(true);
        }
      }
    });

    it("reconciles every row: interest + principal = payment, opening - principal = closing", () => {
      for (const r of rows) {
        expect(r.interest_paise + r.principal_paise).toBe(r.payment_paise);
        expect(r.opening_paise - r.principal_paise).toBe(r.closing_paise);
      }
    });

    it("carries each closing balance into the next opening balance (except a dated bank figure)", () => {
      rows.slice(1).forEach((cur, i) => {
        const prev = rows[i];
        if (!cur.flags.includes("bank_outstanding_applied")) {
          expect(cur.opening_paise).toBe(prev?.closing_paise);
        }
      });
    });

    it("never shows a negative balance and closes at exactly zero when it closes", () => {
      for (const r of rows) expect(r.closing_paise).toBeGreaterThanOrEqual(0);
      if (s.expected.closed) expect(rows.at(-1)?.closing_paise).toBe(0);
    });

    it("totals equal the sum of the rows", () => {
      expect(rows.reduce((a, r) => a + r.interest_paise, 0)).toBe(s.expected.total_interest_paise);
      expect(rows.reduce((a, r) => a + r.payment_paise, 0)).toBe(s.expected.total_paid_paise);
      expect(rows).toHaveLength(s.expected.months);
    });

    it("flags every month where the EMI does not cover interest (S-05)", () => {
      const flagged = rows.some((r) => r.flags.includes("emi_does_not_cover_interest"));
      expect(s.expected.warnings.includes("emi_does_not_cover_interest")).toBe(flagged);
    });
  });
});
