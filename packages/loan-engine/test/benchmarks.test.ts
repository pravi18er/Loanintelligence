/** Bundled MCLR reference (B-07). The same cases are asserted in the Python reference. */
import { describe, expect, it } from "vitest";
import { mclrOn, repoRateOn } from "../src/index.ts";

describe("MCLR reference (B-07)", () => {
  it("returns the revision in force on the date, as published", () => {
    expect(mclrOn("sbi", "one_year", "2022-06-15")?.value).toBe("7.40");
    expect(mclrOn("sbi", "one_year", "2022-06-14")?.value).toBe("7.20");
    expect(mclrOn("bank_of_baroda", "one_year", "2019-12-12")?.value).toBe("8.25");
    expect(mclrOn("bank_of_baroda", "six_month", "2026-11-22")?.value).toBe("8.50");
  });

  it("is labelled Illustrative from public benchmark rates, with its source", () => {
    const f = mclrOn("sbi", "one_year", "2024-01-01");
    expect(f?.label).toEqual({ kind: "illustrative", source: "public-benchmark" });
    expect(f?.explanation).toContain("sbi.bank.in");
    expect(f?.assumptions[0]).toContain("not your loan's rate");
  });

  it("says when the date is after the latest bundled revision", () => {
    expect(mclrOn("sbi", "one_year", "2026-10-15")?.assumptions).toHaveLength(1);
    expect(mclrOn("sbi", "one_year", "2026-11-22")?.assumptions).toHaveLength(2);
  });

  it("returns null outside the history or for a tenor the bank did not publish", () => {
    expect(mclrOn("sbi", "one_year", "2016-03-31")).toBeNull();
    expect(mclrOn("bank_of_baroda", "five_year", "2020-01-01")).toBeNull();
    expect(mclrOn("bank_of_baroda", "five_year", "2017-06-01")?.value).toBe("8.65");
  });
});

describe("MCLR reference wording", () => {
  it("names the bank, tenor and effective date in plain English", () => {
    expect(mclrOn("bank_of_baroda", "one_year", "2020-01-20")?.explanation).toMatch(
      /^Bank of Baroda's 1-year MCLR effective 12 Jan 2020, as published at https:\/\/bankofbaroda\.bank\.in\//,
    );
  });
});

describe("RBI repo rate (B-03)", () => {
  it("returns the rate in force from its announcement date", () => {
    expect(repoRateOn("2019-10-01")?.value).toBe("5.40");
    expect(repoRateOn("2019-10-04")?.value).toBe("5.15");
    expect(repoRateOn("2022-05-03")?.value).toBe("4.00");
    expect(repoRateOn("2026-11-22")?.value).toBe("5.50");
    expect(repoRateOn("2019-08-06")).toBeNull();
  });

  it("is labelled Illustrative and cites the RBI release", () => {
    const f = repoRateOn("2023-03-01");
    expect(f?.label).toEqual({ kind: "illustrative", source: "public-benchmark" });
    expect(f?.explanation).toContain("prid=55177");
  });
});
