import { Decimal } from "./decimal.ts";
import { addMonths, compareDates } from "./dates.ts";
import { calculateEmi, monthlyInterest } from "./emi.ts";
import { type Paise, paise, sumPaise } from "./money.ts";
import type {
  BankDifference,
  LoanInput,
  RateChange,
  RowFlag,
  Schedule,
  ScheduleRow,
  ScheduleWarning,
} from "./types.ts";
import { InvalidLoanInputError, validateLoan } from "./validation.ts";

/** Longest schedule the engine will produce (50 years), so a loan that never closes still ends. */
export const MAX_MONTHS = 600;

/** Months needed to clear `balance` at a fixed rate and EMI, or null if it never clears. */
function monthsToClear(balance: Paise, rate: Decimal, emi: Paise): number | null {
  let b: number = balance;
  let months = 0;
  while (b > 0) {
    months += 1;
    const interest = monthlyInterest(paise(b), rate);
    if (emi <= interest || months > MAX_MONTHS) return null;
    b = b + interest - emi;
  }
  return months;
}

/**
 * Build the month-by-month repayment schedule under the approved Release 1.0
 * rules (PRODUCT_DECISIONS.md section 3):
 *
 * - A-01 monthly reducing-balance interest, A-02/B-06 every amount in paise.
 * - A-03/B-02 a rate change applies from the first period (EMI date to EMI
 *   date) starting on or after its effective date.
 * - A-04 keep EMI (default), keep tenure, or the bank's new EMI.
 * - A-06 a dated bank outstanding restarts the projection; the modelled
 *   history is untouched and the difference is reported.
 * - A-07/B-04 the final EMI is exactly what remains due; where a scheduled
 *   maturity exists the remainder is absorbed into the EMI at maturity.
 * - A-08/B-05 full disbursement one month before EMI 1; month-end dates.
 *
 * After a bank-revised EMI the existing maturity is kept (pending B-08).
 *
 * Throws InvalidLoanInputError if validateLoan() reports any error.
 */
export function amortise(input: LoanInput): Schedule {
  const errors = validateLoan(input).filter((i) => i.severity === "error");
  if (errors.length > 0) throw new InvalidLoanInputError(errors);

  const changes: RateChange[] = [...(input.rateChanges ?? [])].sort((a, b) =>
    compareDates(a.effectiveDate, b.effectiveDate),
  );
  let rate = new Decimal(input.annualRatePercent);
  let emi: Paise = input.startingEmi ?? calculateEmi(input.principal, rate, input.tenureMonths);
  const startingEmi = emi;
  /** EMI number at which the loan is scheduled to end, or null while the tenure is moving. */
  let maturity: number | null = input.tenureMonths;
  let balance: Paise = input.principal;
  let nextChange = 0;
  const bank = input.bankOutstanding;
  let bankApplied = bank === undefined;
  let bankDifference: BankDifference | null = null;
  const rows: ScheduleRow[] = [];

  let n = 0;
  while (balance > 0 && n < MAX_MONTHS) {
    n += 1;
    const periodStart = addMonths(input.firstEmiDate, n - 2);
    const dueDate = addMonths(input.firstEmiDate, n - 1);
    const flags: RowFlag[] = [];

    // A-06: a dated bank outstanding restarts the projection.
    if (!bankApplied && bank && compareDates(periodStart, bank.asAt) >= 0) {
      bankApplied = true;
      bankDifference = {
        asAt: bank.asAt,
        source: bank.source,
        ...(bank.document === undefined ? {} : { document: bank.document }),
        bank: bank.amount,
        modelled: balance,
        difference: paise(bank.amount - balance),
        appliesFromPeriod: n,
      };
      balance = bank.amount;
      flags.push("bank_outstanding_applied");
      if (balance <= 0) break;
    }

    // A-03: apply every change effective on or before this period's start.
    let change = changes[nextChange];
    while (change && compareDates(change.effectiveDate, periodStart) <= 0) {
      nextChange += 1;
      const previousRate = rate;
      rate = new Decimal(change.annualRatePercent);
      flags.push("rate_change");
      const adjustment = change.adjustment ?? "keep_emi";
      if (adjustment === "bank_emi") {
        emi = change.bankEmi as Paise; // presence checked by validateLoan
      } else if (adjustment === "keep_tenure") {
        if (maturity === null) {
          const remaining = monthsToClear(balance, previousRate, emi);
          if (remaining === null) {
            throw new InvalidLoanInputError([
              {
                code: "keep_tenure_without_end_date",
                severity: "error",
                field: `rateChanges`,
                message:
                  "We can't keep your tenure for this rate change because, before it, the EMI was not repaying the loan. Enter the bank's new EMI instead.",
              },
            ]);
          }
          maturity = n - 1 + remaining;
        }
        emi = calculateEmi(balance, rate, maturity - n + 1);
      } else {
        maturity = null;
      }
      change = changes[nextChange];
    }

    const opening = balance;
    const interest = monthlyInterest(opening, rate);
    const dueInFull = paise(opening + interest);

    // A-07: the final EMI is exactly what remains due.
    let payment: Paise;
    if ((maturity !== null && n >= maturity) || dueInFull <= emi) {
      payment = dueInFull;
      if (n > 1 && payment !== emi) flags.push("final_emi_adjusted");
    } else {
      payment = emi;
    }
    if (payment <= interest) flags.push("emi_does_not_cover_interest");
    const principal = paise(payment - interest);
    balance = paise(opening - principal);
    rows.push({
      n,
      periodStart,
      dueDate,
      annualRatePercent: rate.toString(),
      opening,
      interest,
      payment,
      principal,
      closing: balance,
      flags,
    });
  }

  const warnings: ScheduleWarning[] = [];
  if (rows.some((r) => r.flags.includes("emi_does_not_cover_interest"))) {
    warnings.push("emi_does_not_cover_interest");
  }
  const closed = balance === 0;
  if (!closed) warnings.push("loan_does_not_close_within_600_months");

  return {
    startingEmi,
    closed,
    rows,
    totalInterest: sumPaise(rows.map((r) => r.interest)),
    totalPaid: sumPaise(rows.map((r) => r.payment)),
    warnings,
    bankDifference,
  };
}
