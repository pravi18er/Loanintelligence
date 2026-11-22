import type { IsoDate } from "./dates.ts";
import type { Paise } from "./money.ts";

/** What to do when the interest rate changes (A-04). */
export type RateAdjustment =
  /** Keep the EMI the same and let the tenure move. The default. */
  | "keep_emi"
  /** Keep the end date and recalculate the EMI. */
  | "keep_tenure"
  /** Use the new EMI the bank set. */
  | "bank_emi";

/** Where an input figure came from (S-01, S-04). */
export type InputSource = "bank-confirmed" | "customer-provided";

export interface RateChange {
  /** Date the new rate takes effect. It applies from the first period starting on or after it (A-03). */
  effectiveDate: IsoDate;
  /** New annual rate in percent, as a decimal string, e.g. "8.75". */
  annualRatePercent: string;
  /** Defaults to "keep_emi". */
  adjustment?: RateAdjustment;
  /** Required when adjustment is "bank_emi". */
  bankEmi?: Paise;
  source?: InputSource;
}

/** A dated outstanding balance reported by the bank (A-06, S-04). */
export interface BankOutstanding {
  asAt: IsoDate;
  amount: Paise;
  source: InputSource;
  /** For example "annual statement", "bank app". */
  document?: string;
}

export interface LoanInput {
  /** Fully disbursed loan amount (A-08). */
  principal: Paise;
  /** Starting annual rate in percent, as a decimal string, e.g. "8.5". */
  annualRatePercent: string;
  /** Original tenure in months, 1 to 480. */
  tenureMonths: number;
  /** Due date of EMI number 1. */
  firstEmiDate: IsoDate;
  /** The bank's starting EMI, if the customer entered it. Otherwise it is calculated. */
  startingEmi?: Paise;
  rateChanges?: readonly RateChange[];
  bankOutstanding?: BankOutstanding;
}

export type RowFlag =
  "rate_change" | "bank_outstanding_applied" | "final_emi_adjusted" | "emi_does_not_cover_interest";

export interface ScheduleRow {
  /** EMI number, from 1. */
  n: number;
  /** Start of the calculation period (the previous EMI date). */
  periodStart: IsoDate;
  /** EMI due date, at the end of the period. */
  dueDate: IsoDate;
  /** Annual rate in percent used for this period, as a decimal string. */
  annualRatePercent: string;
  opening: Paise;
  interest: Paise;
  payment: Paise;
  principal: Paise;
  closing: Paise;
  flags: RowFlag[];
}

export interface BankDifference {
  asAt: IsoDate;
  source: InputSource;
  document?: string;
  bank: Paise;
  modelled: Paise;
  /** Bank minus modelled. Shown to the customer, never applied back to the model (A-06, S-03). */
  difference: Paise;
  /** First EMI number whose opening balance is the bank's figure. */
  appliesFromPeriod: number;
}

export type ScheduleWarning =
  "emi_does_not_cover_interest" | "loan_does_not_close_within_600_months";

export interface Schedule {
  startingEmi: Paise;
  closed: boolean;
  rows: ScheduleRow[];
  totalInterest: Paise;
  totalPaid: Paise;
  warnings: ScheduleWarning[];
  bankDifference: BankDifference | null;
}
