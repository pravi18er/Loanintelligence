/**
 * Loan Intelligence calculation engine.
 *
 * Phase 0 contains only the package boundary. The calculation rules
 * (A-01 to A-08 in PRODUCT_DECISIONS.md) are implemented in Phase 1 and must
 * match the golden scenarios in reference/scenarios/ exactly, to the paisa.
 */

/** Version of the engine. Bumped whenever any calculated output changes. */
export const ENGINE_VERSION = "0.0.0";

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
