/** Repo-linked estimate (A-05, B-03, B-09). The same cases are in reference/python/test_repo_estimate.py. */
import { describe, expect, it } from "vitest";
import { estimatedRepoChanges, realityCheck, rupeesToPaise, type LoanInput } from "../src/index.ts";

const loan = (over: Partial<LoanInput> = {}): LoanInput => ({
  principal: rupeesToPaise("5000000"),
  annualRatePercent: "8.4",
  tenureMonths: 240,
  firstEmiDate: "2020-01-05",
  ...over,
});
const dates = (l: LoanInput, months: 1 | 3 | 6 | 12 = 3, asOf = "2026-11-22") =>
  estimatedRepoChanges(l, { resetMonths: months }, asOf).map((c) => [
    c.effectiveDate,
    c.annualRatePercent,
  ]);

describe("repo-linked estimate (B-09)", () => {
  it("applies each repo change at the next quarterly reset, keeping the spread", () => {
    // Disbursed 5 Dec 2019 at 8.4% when repo was 5.15%: spread 3.25%.
    expect(dates(loan()).slice(0, 3)).toEqual([
      ["2020-06-05", "7.25"], // repo 4.00% (22 May 2020)
      ["2022-06-05", "7.65"], // repo 4.40% (4 May 2022)
      ["2022-09-05", "8.65"], // repo 5.40% (5 Aug 2022)
    ]);
  });

  it("uses the repo rate announced on the reset date itself", () => {
    expect(dates(loan()).at(-1)).toEqual(["2025-12-05", "8.5"]); // repo 5.25%, 5 Dec 2025
  });

  it("an entered change replaces the estimate for its reset interval and re-anchors the spread", () => {
    const l = loan({ rateChanges: [{ effectiveDate: "2023-06-01", annualRatePercent: "9.4" }] });
    const got = dates(l);
    expect(got.map((g) => g[0])).not.toContain("2023-03-05");
    // 9.4% on 1 Jun 2023 when repo was 6.50%: spread 2.90%; repo 6.25% from 7 Feb 2025.
    expect(got).toContainEqual(["2025-03-05", "9.15"]);
  });

  it("a sanction-letter spread takes priority", () => {
    const got = estimatedRepoChanges(
      loan(),
      { resetMonths: 3, spreadPercent: "2.5" },
      "2020-03-31",
    );
    expect(got).toEqual([
      {
        effectiveDate: "2020-03-05",
        annualRatePercent: "7.65",
        adjustment: "keep_emi",
        source: "public-benchmark",
      },
    ]);
  });

  it("makes no estimate without a repo rate for the anchor date (carry forward)", () => {
    expect(dates(loan({ firstEmiDate: "2018-01-05" }))).toEqual([]);
  });

  it("stops at the report date", () => {
    expect(dates(loan(), 3, "2022-06-04")).toEqual([["2020-06-05", "7.25"]]);
  });

  it("rejects an unsupported reset frequency or a first reset before disbursement", () => {
    expect(() => estimatedRepoChanges(loan(), { resetMonths: 2 as 3 }, "2026-01-01")).toThrow();
    expect(() =>
      estimatedRepoChanges(loan(), { resetMonths: 3, firstReset: "2019-12-05" }, "2026-01-01"),
    ).toThrow();
  });

  it("labels Reality Check figures Illustrative, from public benchmark rates", () => {
    const rc = realityCheck({
      loan: loan(),
      asOf: "2025-11-22",
      rateHistoryKnown: "no",
      repoEstimate: { resetMonths: 3 },
    });
    expect(rc.interestPaidSoFar.label).toEqual({
      kind: "illustrative",
      source: "public-benchmark",
    });
    expect(rc.futureInterest.label.kind).toBe("illustrative");
    expect(rc.interestPaidSoFar.assumptions.join(" ")).toContain("RBI repo rate");
  });
});
