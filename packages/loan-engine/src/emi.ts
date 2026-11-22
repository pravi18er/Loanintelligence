import { Decimal } from "./decimal.ts";
import { type Paise, roundToPaise } from "./money.ts";

/** One month's interest: opening balance x annual rate / 1200, rounded to the paisa (A-01, A-02). */
export function monthlyInterest(openingBalance: Paise, annualRatePercent: Decimal): Paise {
  return roundToPaise(new Decimal(openingBalance).times(annualRatePercent).dividedBy(1200));
}

/**
 * Standard EMI, P x r x (1 + r)^n / ((1 + r)^n - 1), rounded to the paisa
 * (A-02 as amended by B-06). With a 0% rate the EMI is P / n.
 */
export function calculateEmi(balance: Paise, annualRatePercent: Decimal, months: number): Paise {
  if (!Number.isInteger(months) || months < 1) {
    throw new RangeError("The number of months must be a whole number of at least 1.");
  }
  const p = new Decimal(balance);
  if (annualRatePercent.isZero()) return roundToPaise(p.dividedBy(months));
  const r = annualRatePercent.dividedBy(1200);
  const f = r.plus(1).pow(months);
  return roundToPaise(p.times(r).times(f).dividedBy(f.minus(1)));
}
