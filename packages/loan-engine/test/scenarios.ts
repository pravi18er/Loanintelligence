import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/** Shape of a golden scenario file written by reference/python/scenarios.py. */
export interface ScenarioRow {
  n: number;
  period_start: string;
  due_date: string;
  annual_rate: string;
  opening_paise: number;
  interest_paise: number;
  payment_paise: number;
  principal_paise: number;
  closing_paise: number;
  flags: string[];
}

export interface Scenario {
  fixture_version: number;
  id: string;
  title: string;
  rules: string[];
  input: {
    principal_paise: number;
    annual_rate: string;
    tenure_months: number;
    first_emi_date: string;
    starting_emi_paise: number | null;
    rate_changes: {
      effective: string;
      annual_rate: string;
      mode: "keep_emi" | "keep_tenure" | "bank_emi";
      bank_emi_paise: number | null;
    }[];
    bank_outstanding: { as_at: string; outstanding_paise: number; source: string } | null;
    /** Repo-linked estimate settings (B-09), or null. */
    repo_estimate: {
      reset_months: 1 | 3 | 6 | 12;
      first_reset: string | null;
      spread: string | null;
      as_of: string;
    } | null;
  };
  expected: {
    starting_emi_paise: number;
    closed: boolean;
    months: number;
    total_interest_paise: number;
    total_paid_paise: number;
    warnings: string[];
    bank_difference: {
      as_at: string;
      source: string;
      bank_paise: number;
      modelled_paise: number;
      difference_paise: number;
      applies_from_period: number;
    } | null;
    schedule: ScenarioRow[];
    /** Present when repo_estimate is set: the estimated rate changes. */
    estimated_changes?: { effective: string; annual_rate: string }[];
  };
}

const here = dirname(fileURLToPath(import.meta.url));
export const SCENARIO_DIR = join(here, "..", "..", "..", "reference", "scenarios");

export function loadScenarios(): Scenario[] {
  return readdirSync(SCENARIO_DIR)
    .filter((f) => f.endsWith(".json"))
    .sort()
    .map((f) => JSON.parse(readFileSync(join(SCENARIO_DIR, f), "utf8")) as Scenario);
}
