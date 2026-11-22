import { Decimal } from "./decimal.ts";

/**
 * An amount of money in whole paise (1 rupee = 100 paise).
 * Every monetary amount in the engine is held this way (A-02, B-06).
 */
export type Paise = number & { readonly __unit: "paise" };

/** Wrap an integer number of paise, rejecting anything that is not a safe whole number. */
export function paise(value: number): Paise {
  if (!Number.isSafeInteger(value)) {
    throw new RangeError(`Not a whole number of paise: ${value}`);
  }
  return value as Paise;
}

/** Convert an exact decimal number of paise to whole paise, rounding half-up. */
export function roundToPaise(value: Decimal): Paise {
  return paise(value.toDecimalPlaces(0, Decimal.ROUND_HALF_UP).toNumber());
}

/** Rupees (as a decimal string, e.g. "4500000" or "43391.16") to whole paise, rounding half-up. */
export function rupeesToPaise(rupees: string | number): Paise {
  return roundToPaise(new Decimal(rupees).times(100));
}

/** Whole paise to a rupee amount rounded half-up to the nearest rupee, for display (A-02). */
export function displayRupees(amount: Paise): number {
  return new Decimal(amount).dividedBy(100).toDecimalPlaces(0, Decimal.ROUND_HALF_UP).toNumber();
}

/** Add amounts of paise exactly. */
export function sumPaise(values: readonly Paise[]): Paise {
  return paise(values.reduce<number>((total, v) => total + v, 0));
}
