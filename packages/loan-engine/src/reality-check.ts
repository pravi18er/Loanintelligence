import { amortise } from "./amortise.ts";
import { compareDates, isValidIsoDate, type IsoDate } from "./dates.ts";
import { calculatedKind, type Figure, type FigureKind } from "./labels.ts";
import { type Paise, sumPaise } from "./money.ts";
import type { LoanInput, Schedule } from "./types.ts";
import { InvalidLoanInputError, validateLoan, type Issue } from "./validation.ts";

/** Whether the customer has told us every rate change since the loan started. */
export type RateHistoryKnown = "yes" | "no" | "not_sure";

export interface RealityCheckInput {
  loan: LoanInput;
  /** The date "today" means for this report. An input, so results are repeatable. */
  asOf: IsoDate;
  /**
   * "yes": the rate never changed, or every change is entered.
   * "no" / "not_sure": past rate changes may be missing, so figures that
   * depend on them are Estimated. (A-05 benchmark estimates arrive with B-07.)
   */
  rateHistoryKnown: RateHistoryKnown;
  /** EMIs paid so far, if the customer knows it. Otherwise counted from the dates. */
  emisPaid?: number;
}

export interface RealityCheck {
  schedule: Schedule;
  emisPaid: Figure<number>;
  totalPaidSoFar: Figure<Paise>;
  principalRepaidSoFar: Figure<Paise>;
  interestPaidSoFar: Figure<Paise>;
  currentOutstanding: Figure<Paise>;
  futureInterest: Figure<Paise>;
  remainingEmis: Figure<number>;
  estimatedClosureDate: Figure<IsoDate | null>;
  /** Input checks (errors stop the calculation; checks are shown alongside results). */
  issues: Issue[];
}

const COMMON_ASSUMPTIONS = [
  "Interest is charged monthly on the reducing balance: balance × annual rate ÷ 12.",
  "Each EMI is assumed paid in full on its due date.",
  "Amounts are calculated to the paisa and shown to the nearest rupee.",
  "This is a model of your loan, not your bank's own calculation. Your bank's figures may differ.",
];

function countDue(schedule: Schedule, asOf: IsoDate): number {
  return schedule.rows.filter((r) => compareDates(r.dueDate, asOf) <= 0).length;
}

/**
 * The Release 1.0 Loan Reality Check (FR-02, FR-03): what has been paid,
 * what is owed, and what lies ahead, each with a label and explanation.
 */
export function realityCheck(input: RealityCheckInput): RealityCheck {
  const issues = validateLoan(input.loan);
  if (!isValidIsoDate(input.asOf)) {
    issues.push({
      code: "as_of_invalid",
      severity: "error",
      field: "asOf",
      message: "The report date is not a valid date.",
    });
  }
  if (input.emisPaid !== undefined && (!Number.isInteger(input.emisPaid) || input.emisPaid < 0)) {
    issues.push({
      code: "emis_paid_invalid",
      severity: "error",
      field: "emisPaid",
      message: "EMIs paid must be a whole number, 0 or more.",
    });
  }
  const errors = issues.filter((i) => i.severity === "error");
  if (errors.length > 0) throw new InvalidLoanInputError(errors);

  const schedule = amortise(input.loan);
  const rows = schedule.rows;
  const bank = input.loan.bankOutstanding;

  // EMIs paid: the customer's own count, else counted from the dates.
  const counted = countDue(schedule, input.asOf);
  const paidCount = Math.min(input.emisPaid ?? counted, rows.length);
  if (input.emisPaid !== undefined && input.emisPaid !== counted) {
    issues.push({
      code: "emis_paid_differs_from_dates",
      severity: "check",
      field: "emisPaid",
      message: `You entered ${input.emisPaid} EMIs paid; from your dates we count ${counted}. We've used your number.`,
    });
  }
  const emisPaid: Figure<number> = {
    value: paidCount,
    label:
      input.emisPaid === undefined
        ? { kind: "estimated", source: "calculated" }
        : { kind: "actual", source: "customer-provided" },
    explanation:
      input.emisPaid === undefined
        ? "Counted from your first EMI date up to the report date."
        : "The number of EMIs you told us you have paid.",
    assumptions: input.emisPaid === undefined ? ["Every EMI was paid on its due date."] : [],
  };

  // Past figures depend on the rate history and on the paid count.
  const historyKind: FigureKind = input.rateHistoryKnown === "yes" ? "modelled" : "estimated";
  const pastKind = calculatedKind(historyKind, emisPaid.label.kind);
  const historyAssumptions =
    input.rateHistoryKnown === "yes"
      ? []
      : [
          "Some past rate changes may be missing, so the rate you entered is assumed to have continued until the next change you gave us.",
        ];
  const past = rows.slice(0, paidCount);
  const pastFigure = (value: Paise, explanation: string): Figure<Paise> => ({
    value,
    label: { kind: pastKind, source: "calculated" },
    explanation,
    assumptions: [...COMMON_ASSUMPTIONS, ...historyAssumptions],
  });
  const totalPaidSoFar = pastFigure(
    sumPaise(past.map((r) => r.payment)),
    "All the EMIs paid so far, added up.",
  );
  const principalRepaidSoFar = pastFigure(
    sumPaise(past.map((r) => r.principal)),
    "The part of your EMIs that reduced the loan itself.",
  );
  const interestPaidSoFar = pastFigure(
    sumPaise(past.map((r) => r.interest)),
    "The part of your EMIs that went to interest. Early in a loan most of each EMI is interest, because interest is charged on a large balance.",
  );

  // Today's outstanding (A-06): the bank's dated figure when no EMI has fallen due since it;
  // otherwise modelled forward from it, or from the start of the loan.
  const applied = schedule.bankDifference;
  const bankUsed =
    bank !== undefined && applied !== null && compareDates(bank.asAt, input.asOf) <= 0;
  const bankIsLatest = bankUsed && paidCount < applied.appliesFromPeriod;
  const modelledOutstanding = past.at(-1)?.closing ?? input.loan.principal;
  let currentOutstanding: Figure<Paise>;
  if (bankIsLatest) {
    currentOutstanding = {
      value: bank.amount,
      label: { kind: "actual", source: bank.source },
      explanation: `The outstanding balance${bank.document ? ` from your ${bank.document}` : ""}, dated ${bank.asAt}.`,
      assumptions: [],
    };
  } else if (bankUsed) {
    currentOutstanding = {
      value: modelledOutstanding,
      label: {
        kind: calculatedKind("actual", historyKind, emisPaid.label.kind),
        source: "calculated",
      },
      explanation: `Worked forward from the outstanding balance you gave us, dated ${bank.asAt}, by the EMIs due since then.`,
      assumptions: [...COMMON_ASSUMPTIONS, ...historyAssumptions],
    };
  } else {
    currentOutstanding = pastFigure(
      modelledOutstanding,
      "What you still owe on the loan itself, after the principal repaid so far.",
    );
  }

  // The future starts from today's outstanding at the current rate.
  const futureKind = calculatedKind(currentOutstanding.label.kind, historyKind);
  const future = rows.slice(paidCount);
  const futureAssumptions = [
    ...COMMON_ASSUMPTIONS,
    "Your current rate is assumed to stay the same for the rest of the loan.",
  ];
  const futureInterest: Figure<Paise> = {
    value: sumPaise(future.map((r) => r.interest)),
    label: { kind: futureKind, source: "calculated" },
    explanation:
      "The interest still to come if your rate and EMI stay as they are. This is a projection, separate from interest already paid.",
    assumptions: futureAssumptions,
  };
  const remainingEmis: Figure<number> = {
    value: schedule.closed ? future.length : 0,
    label: { kind: futureKind, source: "calculated" },
    explanation: schedule.closed
      ? "EMIs still to pay before the loan closes."
      : "Your loan does not close at the current EMI and rate. See the warnings.",
    assumptions: futureAssumptions,
  };
  const estimatedClosureDate: Figure<IsoDate | null> = {
    value: schedule.closed ? (rows.at(-1)?.dueDate ?? null) : null,
    label: { kind: futureKind, source: "calculated" },
    explanation: "The due date of your last EMI if your rate and EMI stay as they are.",
    assumptions: futureAssumptions,
  };

  return {
    schedule,
    emisPaid,
    totalPaidSoFar,
    principalRepaidSoFar,
    interestPaidSoFar,
    currentOutstanding,
    futureInterest,
    remainingEmis,
    estimatedClosureDate,
    issues,
  };
}
