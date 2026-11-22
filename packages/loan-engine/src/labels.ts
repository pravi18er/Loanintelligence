/**
 * Two-part labels carried by every figure the engine reports (S-01, S-02).
 *
 * Kind says what the figure is; source says where its inputs came from.
 * A figure is only as strong as its weakest input.
 */

export type FigureKind = "actual" | "modelled" | "estimated" | "illustrative";

export type FigureSource =
  "bank-confirmed" | "customer-provided" | "public-benchmark" | "calculated";

export interface Label {
  kind: FigureKind;
  source: FigureSource;
}

/** A value with its label and a plain-English explanation (FR-13). */
export interface Figure<T> {
  value: T;
  label: Label;
  /** How the figure was worked out, in plain English. */
  explanation: string;
  /** Assumptions that apply to this figure, in plain English. */
  assumptions: string[];
}

const STRENGTH: Record<FigureKind, number> = {
  actual: 3,
  modelled: 2,
  estimated: 1,
  illustrative: 0,
};

/**
 * The kind of a figure calculated from inputs of the given kinds: the weakest
 * one, and never "actual", because a calculation is never the bank's own figure.
 */
export function calculatedKind(...inputs: FigureKind[]): Exclude<FigureKind, "actual"> {
  const weakest = inputs.reduce<FigureKind>(
    (w, k) => (STRENGTH[k] < STRENGTH[w] ? k : w),
    "modelled",
  );
  return weakest === "actual" ? "modelled" : weakest;
}

/** Customer-facing badge text for a label, e.g. "Actual · from your bank". */
export function labelText(label: Label): string {
  const kind = {
    actual: "Actual",
    modelled: "Modelled",
    estimated: "Estimated",
    illustrative: "Illustrative",
  }[label.kind];
  const source = {
    "bank-confirmed": "from your bank",
    "customer-provided": "as you entered it",
    "public-benchmark": "from public benchmark rates",
    calculated: "calculated",
  }[label.source];
  return `${kind} · ${source}`;
}
