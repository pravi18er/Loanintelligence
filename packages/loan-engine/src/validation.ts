import { Decimal } from "./decimal.ts";
import { compareDates, isValidIsoDate } from "./dates.ts";
import type { LoanInput } from "./types.ts";

export type IssueSeverity = "error" | "check";

export interface Issue {
  code: string;
  severity: IssueSeverity;
  /** Which input the issue is about, e.g. "principal" or "rateChanges[2].bankEmi". */
  field: string;
  /** Plain-English explanation for the customer. */
  message: string;
}

export const MAX_TENURE_MONTHS = 480;
export const MAX_RATE_PERCENT = 25;

function rateIssue(value: unknown, field: string): Issue | null {
  let rate: Decimal;
  try {
    rate = new Decimal(value as string);
  } catch {
    return {
      code: "rate_invalid",
      severity: "error",
      field,
      message: "Enter the interest rate as a percentage, for example 8.5.",
    };
  }
  if (!rate.isFinite() || rate.isNegative() || rate.greaterThan(MAX_RATE_PERCENT)) {
    return {
      code: "rate_out_of_range",
      severity: "error",
      field,
      message: `Enter the interest rate as a percentage between 0 and ${MAX_RATE_PERCENT}, for example 8.5.`,
    };
  }
  if (rate.greaterThan(0) && (rate.lessThan(5) || rate.greaterThan(15))) {
    return {
      code: "rate_unusual",
      severity: "check",
      field,
      message:
        "Rates outside 5% to 15% are unusual for Indian home loans. Did you enter 0.085 instead of 8.5?",
    };
  }
  return null;
}

function isPositiveWholePaise(v: unknown): boolean {
  return typeof v === "number" && Number.isSafeInteger(v) && v > 0;
}

/** Check a loan's inputs. Anything with severity "error" must be fixed before calculating. */
export function validateLoan(input: LoanInput): Issue[] {
  const issues: Issue[] = [];
  const add = (i: Issue | null) => {
    if (i) issues.push(i);
  };

  if (!isPositiveWholePaise(input.principal)) {
    add({
      code: "principal_invalid",
      severity: "error",
      field: "principal",
      message: "Enter your original loan amount in rupees.",
    });
  }
  add(rateIssue(input.annualRatePercent, "annualRatePercent"));
  if (
    !Number.isInteger(input.tenureMonths) ||
    input.tenureMonths < 1 ||
    input.tenureMonths > MAX_TENURE_MONTHS
  ) {
    add({
      code: "tenure_invalid",
      severity: "error",
      field: "tenureMonths",
      message: "Enter the original tenure in whole months, between 1 and 480 (40 years).",
    });
  }
  if (!isValidIsoDate(input.firstEmiDate)) {
    add({
      code: "first_emi_date_invalid",
      severity: "error",
      field: "firstEmiDate",
      message: "Enter the due date of your first EMI.",
    });
  }
  if (input.startingEmi !== undefined && !isPositiveWholePaise(input.startingEmi)) {
    add({
      code: "starting_emi_invalid",
      severity: "error",
      field: "startingEmi",
      message: "Your EMI must be an amount above zero.",
    });
  }

  const changes = input.rateChanges ?? [];
  changes.forEach((c, i) => {
    const field = `rateChanges[${i}]`;
    if (!isValidIsoDate(c.effectiveDate)) {
      add({
        code: "rate_change_date_invalid",
        severity: "error",
        field: `${field}.effectiveDate`,
        message: "Each rate change needs the date it took effect.",
      });
    } else if (
      isValidIsoDate(input.firstEmiDate) &&
      compareDates(c.effectiveDate, input.firstEmiDate) < 0
    ) {
      add({
        code: "rate_change_before_loan",
        severity: "check",
        field: `${field}.effectiveDate`,
        message:
          "This rate change is dated before your first EMI. If it was your starting rate, enter it as the starting rate instead.",
      });
    }
    add(rateIssue(c.annualRatePercent, `${field}.annualRatePercent`));
    if ((c.adjustment ?? "keep_emi") === "bank_emi" && !isPositiveWholePaise(c.bankEmi)) {
      add({
        code: "bank_emi_missing",
        severity: "error",
        field: `${field}.bankEmi`,
        message: "You chose 'the bank set a new EMI': enter that EMI.",
      });
    }
  });
  const dates = changes.map((c) => c.effectiveDate);
  if (new Set(dates).size !== dates.length) {
    add({
      code: "rate_change_duplicate",
      severity: "error",
      field: "rateChanges",
      message: "Two rate changes have the same date. Keep only the correct one.",
    });
  }

  const bank = input.bankOutstanding;
  if (bank) {
    if (!isValidIsoDate(bank.asAt)) {
      add({
        code: "bank_figure_undated",
        severity: "error",
        field: "bankOutstanding.asAt",
        message:
          "Enter the date of the statement your outstanding balance comes from. Without it we can't use the figure for your projection.",
      });
    }
    if (typeof bank.amount !== "number" || !Number.isSafeInteger(bank.amount) || bank.amount < 0) {
      add({
        code: "bank_outstanding_invalid",
        severity: "error",
        field: "bankOutstanding.amount",
        message: "The outstanding balance must be zero or more.",
      });
    } else if (isPositiveWholePaise(input.principal) && bank.amount > input.principal) {
      add({
        code: "bank_outstanding_above_loan",
        severity: "check",
        field: "bankOutstanding.amount",
        message:
          "Your outstanding balance is above your original loan amount. Please double-check it.",
      });
    }
  }
  return issues;
}

export class InvalidLoanInputError extends Error {
  readonly issues: Issue[];
  constructor(issues: Issue[]) {
    super(issues.map((i) => `${i.field}: ${i.message}`).join(" "));
    this.name = "InvalidLoanInputError";
    this.issues = issues;
  }
}
