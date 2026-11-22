/**
 * Repo-linked estimate of unknown past rates (A-05, B-03, B-09).
 *
 * Mirrors reference/python/repo_estimate.py and the spreadsheet's repo-linked
 * estimate table. The rule:
 *
 * - Reset dates: the first reset date (default: one reset interval after
 *   disbursement, which is one month before EMI 1), then every `resetMonths`
 *   months (same day each month, month-end clamped), up to the report date.
 * - Known rates: the starting rate from disbursement, and each rate change the
 *   customer entered, from its date.
 * - At each reset date R the estimate is repo(R) + spread, where spread is the
 *   sanction-letter spread if given, else the latest known rate on or before R
 *   minus the repo rate on that rate's date.
 * - No estimate at R if the customer entered a change in [R, next reset), if a
 *   repo rate is not available for a date needed, or if the estimate is not
 *   above zero. The last known rate then carries forward (labelled Estimated).
 * - An estimate becomes a keep-EMI rate change (A-04 default) only when it
 *   differs from the rate in force just before R.
 */
import { repoRateOn } from "./benchmarks.ts";
import { addMonths, compareDates, type IsoDate } from "./dates.ts";
import { Decimal } from "./decimal.ts";
import type { LoanInput, RateChange } from "./types.ts";

export type ResetMonths = 1 | 3 | 6 | 12;
export const MAX_RESETS = 120;

export interface RepoEstimate {
  /** How often the bank resets the rate. Quarterly when the customer is unsure (B-09). */
  resetMonths: ResetMonths;
  /** The loan's first reset date, if known. */
  firstReset?: IsoDate;
  /** The spread over the repo rate from the sanction letter, in percent, e.g. "2.75". */
  spreadPercent?: string;
}

const repo = (on: IsoDate): Decimal | null => {
  const f = repoRateOn(on);
  return f === null ? null : new Decimal(f.value);
};

/** The estimated rate changes up to `asOf`, each labelled public-benchmark. */
export function estimatedRepoChanges(
  loan: LoanInput,
  est: RepoEstimate,
  asOf: IsoDate,
): RateChange[] {
  if (![1, 3, 6, 12].includes(est.resetMonths)) {
    throw new RangeError("Reset frequency must be 1, 3, 6 or 12 months.");
  }
  const disbursed = addMonths(loan.firstEmiDate, -1);
  const anchor = est.firstReset ?? addMonths(disbursed, est.resetMonths);
  if (compareDates(anchor, disbursed) <= 0) {
    throw new RangeError("The first reset date must be after the loan was disbursed.");
  }
  const entered = loan.rateChanges ?? [];
  const out: RateChange[] = [];
  let prevReset: IsoDate | null = null;
  let prevEst: Decimal | null = null;
  for (let k = 0; k < MAX_RESETS; k++) {
    const reset = addMonths(anchor, k * est.resetMonths);
    if (compareDates(reset, asOf) > 0) break;
    const next = addMonths(anchor, (k + 1) * est.resetMonths);
    const known = entered.filter((c) => compareDates(c.effectiveDate, reset) <= 0).at(-1);
    const pDate = known?.effectiveDate ?? disbursed;
    const pRate = new Decimal(known?.annualRatePercent ?? loan.annualRatePercent);
    const repoR = repo(reset);
    let spread: Decimal | null;
    if (est.spreadPercent !== undefined) {
      spread = new Decimal(est.spreadPercent);
    } else {
      const repoP = repo(pDate);
      spread = repoP === null ? null : pRate.minus(repoP);
    }
    let value = repoR === null || spread === null ? null : repoR.plus(spread);
    if (value !== null && value.lte(0)) value = null;
    const before =
      prevReset === null || compareDates(pDate, prevReset) >= 0 || prevEst === null
        ? pRate
        : prevEst;
    const dropped = entered.some(
      (c) => compareDates(c.effectiveDate, reset) >= 0 && compareDates(c.effectiveDate, next) < 0,
    );
    if (value !== null && !dropped && !value.eq(before)) {
      out.push({
        effectiveDate: reset,
        annualRatePercent: value.toString(),
        adjustment: "keep_emi",
        source: "public-benchmark",
      });
    }
    prevReset = reset;
    prevEst = value;
  }
  return out;
}

/** The loan with estimated changes merged into the entered ones, by date. */
export function withRepoEstimates(loan: LoanInput, est: RepoEstimate, asOf: IsoDate): LoanInput {
  const merged = [...(loan.rateChanges ?? []), ...estimatedRepoChanges(loan, est, asOf)];
  // A stable sort keeps the customer's order for changes on the same date.
  merged.sort((a, b) => compareDates(a.effectiveDate, b.effectiveDate));
  return { ...loan, rateChanges: merged };
}
