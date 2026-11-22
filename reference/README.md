# Calculation reference

This folder holds the accuracy benchmark that every implementation of the approved calculation rules must match (PRODUCT_DECISIONS.md, sections 3 and 4; TEST_STRATEGY.md).

| Path | What it is |
|---|---|
| `python/loan_reference.py` | An independent, deliberately simple implementation of the approved Release 1.0 rules, using only the Python standard library. Not shipped to customers. |
| `python/test_loan_reference.py` | Rule tests for A-01 to A-08 and the safeguards. |
| `python/scenarios.py` | Defines the golden scenarios and writes `scenarios/*.json`. |
| `scenarios/*.json` | Golden scenarios: inputs and the expected month-by-month schedule in whole paise. |

## Rules

- The TypeScript engine (Phase 1) and spreadsheet v2 must reproduce every scenario exactly, to the paisa.
- CI regenerates the scenarios and fails if the committed files differ, so they can't drift from the reference.
- Spreadsheet v1 is **not** an approved reference.
- Not covered yet: A-05 benchmark-based illustrative rates (needs B-07), and G-05, G-12 and G-14 (as-of dates and benchmark scenarios, added in Phase 1).

## Commands

```bash
pnpm reference:test     # rule tests
pnpm reference:check    # scenarios match the reference
python3 -I reference/python/scenarios.py   # regenerate after an approved rule change
```
