/**
 * Loan Intelligence calculation engine.
 *
 * Implements the approved Release 1.0 calculation rules (PRODUCT_DECISIONS.md
 * section 3). Every result must match the golden scenarios in
 * reference/scenarios/ exactly, to the paisa.
 */

/** Version of the engine. Bumped whenever any calculated output changes. */
export const ENGINE_VERSION = "0.1.0";

/** Approved calculation rules this engine is required to implement. */
export const APPROVED_RULES = [
  "A-01",
  "A-02",
  "A-03",
  "A-04",
  "A-05",
  "A-06",
  "A-07",
  "A-08",
] as const;

export type ApprovedRule = (typeof APPROVED_RULES)[number];

export { amortise, MAX_MONTHS } from "./amortise.ts";
export { addMonths, isValidIsoDate, type IsoDate } from "./dates.ts";
export { calculateEmi, monthlyInterest } from "./emi.ts";
export { displayRupees, paise, rupeesToPaise, sumPaise, type Paise } from "./money.ts";
export type * from "./types.ts";
export {
  InvalidLoanInputError,
  validateLoan,
  type Issue,
  type IssueSeverity,
} from "./validation.ts";
export {
  calculatedKind,
  labelText,
  type Figure,
  type FigureKind,
  type FigureSource,
  type Label,
} from "./labels.ts";
export {
  realityCheck,
  type RateHistoryKnown,
  type RealityCheck,
  type RealityCheckInput,
} from "./reality-check.ts";
export {
  MCLR_LENDERS,
  MCLR_TABLE_VERSION,
  mclrOn,
  REPO_TABLE_VERSION,
  repoRateOn,
  type MclrLender,
  type MclrTenor,
} from "./benchmarks.ts";
