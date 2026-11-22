# Home Loan Reality Check workbook (v2)

The customer-facing Excel / Google Sheets version of the Release 1.0 Reality Check. It follows the same approved rules as the website engine (PRODUCT_DECISIONS.md, D-04 and S-06), and v1 is no longer used.

| File | Purpose |
|---|---|
| `build_workbook.py` | Generates the workbook (`spreadsheet/dist/Home_Loan_Reality_Check_v2.xlsx`). The formulas live here, so they are reviewed and versioned like code. |
| `verify_workbook.py` | Fills the workbook with every golden scenario in `reference/scenarios/`, recalculates it in LibreOffice and checks every row, and the dashboard totals, to the paisa. It also checks lookups on the Benchmark Rates tab against the Python reference. Runs in CI. |

```bash
pnpm spreadsheet:build    # needs openpyxl
pnpm spreadsheet:verify   # needs openpyxl and LibreOffice
```

Tabs: Welcome, Loan Profile (inputs), Loan Reality Check (results with labels and explanations), Repayment Engine (600 rows), Validation & Assumptions, Benchmark Rates (published SBI and Bank of Baroda MCLR and the RBI repo rate, read from `data/benchmarks/benchmarks.json`, with a lookup; a reference only, B-07).

Notes on formulas:

- Amounts are rounded with `ROUND(ROUND(x, 6), 2)`. The inner rounding removes floating-point noise, so half-paisa cases round the same way as the decimal engine.
- Uses only functions available in Excel 2010+, Google Sheets and LibreOffice (`EDATE`, `PMT`, `NPER`, `COUNTIF(S)`, `SUMIFS`, `INDEX`, `MATCH`, `CHOOSE`).
- CI checks the workbook in LibreOffice. Google Sheets is not checked automatically; before each release, open the built file in Google Sheets and compare the sample loan with the website.
