import DecimalJs from "decimal.js";

/**
 * The engine's own Decimal: 50 significant digits, half-up rounding.
 * Half-up matches the spreadsheet ROUND function for the positive amounts
 * the engine rounds (A-02 as amended by B-06).
 */
export const Decimal = DecimalJs.clone({ precision: 50, rounding: DecimalJs.ROUND_HALF_UP });
export type Decimal = InstanceType<typeof Decimal>;
