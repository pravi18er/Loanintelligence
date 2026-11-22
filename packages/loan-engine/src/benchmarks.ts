/**
 * Bundled public benchmark rates (A-05, B-03, B-07).
 *
 * The data comes from data/benchmarks/benchmarks.json, which is built from the
 * RBI's and each bank's own published figures. The RBI repo rate is the
 * benchmark for repo-linked loans (B-03). MCLR history is a reference shown beside an
 * MCLR-linked loan; it never sets the loan's rate, because MCLR resets are not
 * modelled in Release 1.0 (B-07): the customer enters each past rate.
 */
import data from "../../../data/benchmarks/benchmarks.json" with { type: "json" };
import { compareDates, isValidIsoDate, type IsoDate } from "./dates.ts";
import type { Figure } from "./labels.ts";

export type MclrLender = "sbi" | "bank_of_baroda";
export type MclrTenor =
  | "overnight"
  | "one_month"
  | "three_month"
  | "six_month"
  | "one_year"
  | "two_year"
  | "three_year"
  | "five_year";

export const MCLR_TABLE_VERSION: string = data.mclr.table_version;

interface Series {
  id: string;
  name: string;
  source_url: string;
  retrieved: string;
  covers: string[];
  rows: { effective: string; rates: Partial<Record<string, string>> }[];
}

const SERIES = data.mclr.series as Series[];
const REPO = data.repo.series[0] as Series & { row_sources: Record<string, string> };

export const REPO_TABLE_VERSION: string = data.repo.table_version;

export const MCLR_LENDERS: readonly { id: MclrLender; name: string }[] = SERIES.map((s) => ({
  id: s.id as MclrLender,
  name: s.name,
}));

const TENOR_TEXT: Record<MclrTenor, string> = {
  overnight: "overnight",
  one_month: "1-month",
  three_month: "3-month",
  six_month: "6-month",
  one_year: "1-year",
  two_year: "2-year",
  three_year: "3-year",
  five_year: "5-year",
};

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2026-10-15" -> "15 Oct 2026", with no dependence on the runtime's locale data. */
function longDate(iso: IsoDate): string {
  const [y, m, d] = iso.split("-");
  return `${Number(d)} ${MONTHS[Number(m) - 1] ?? ""} ${y ?? ""}`;
}

/**
 * The lender's published MCLR for a tenor in force on a date, as a labelled
 * reference figure (Illustrative, from public benchmark rates), or null when
 * the bundled history does not cover that date or tenor. The value is the rate
 * as published, in percent per annum, as a string so no precision is lost.
 */
export function mclrOn(lender: MclrLender, tenor: MclrTenor, date: IsoDate): Figure<string> | null {
  if (!isValidIsoDate(date)) throw new RangeError(`Not a valid date: ${date}`);
  const series = SERIES.find((s) => s.id === lender);
  if (!series) throw new RangeError(`No bundled MCLR history for lender: ${lender}`);
  const last = series.rows[series.rows.length - 1];
  if (!last || compareDates(date, series.rows[0]?.effective ?? date) < 0) return null;
  const row = series.rows.filter((r) => compareDates(r.effective, date) <= 0).at(-1);
  const value = row?.rates[tenor];
  if (!row || value === undefined) return null;
  const assumptions = [
    "This is the bank's published benchmark, not your loan's rate: your rate is the benchmark plus your spread, and it changes only on your loan's reset dates.",
  ];
  if (compareDates(date, last.effective) > 0) {
    assumptions.push(
      `The bundled history ends with the revision effective ${longDate(last.effective)}; a later revision may exist.`,
    );
  }
  return {
    value,
    label: { kind: "illustrative", source: "public-benchmark" },
    explanation: `${series.name}'s ${TENOR_TEXT[tenor]} MCLR effective ${longDate(row.effective)}, as published at ${series.source_url} (retrieved ${longDate(series.retrieved)}).`,
    assumptions,
  };
}

/**
 * The RBI policy repo rate in force on a date (announcement date, with
 * immediate effect), as a labelled figure (Illustrative, from public benchmark
 * rates), or null before the bundled history begins (7 Aug 2019).
 */
export function repoRateOn(date: IsoDate): Figure<string> | null {
  if (!isValidIsoDate(date)) throw new RangeError(`Not a valid date: ${date}`);
  const row = REPO.rows.filter((r) => compareDates(r.effective, date) <= 0).at(-1);
  const value = row?.rates["repo_rate"];
  if (!row || value === undefined) return null;
  const last = REPO.rows.at(-1);
  const assumptions = [
    "This is the RBI repo rate, not your loan's rate: a repo-linked loan's rate is the repo rate plus your spread, applied from your bank's reset date.",
  ];
  if (last && compareDates(date, last.effective) > 0) {
    assumptions.push(
      `The bundled history ends with the change announced ${longDate(last.effective)} (retrieved ${longDate(REPO.retrieved)}); a later change may exist.`,
    );
  }
  return {
    value,
    label: { kind: "illustrative", source: "public-benchmark" },
    explanation: `RBI policy repo rate announced ${longDate(row.effective)}, with immediate effect (${REPO.row_sources[row.effective] ?? REPO.source_url}).`,
    assumptions,
  };
}
