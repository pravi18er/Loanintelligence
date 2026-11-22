# Test Strategy — Loan Intelligence Platform

**Status:** Updated 22 November 2026 for the product owner's approved Release 1.0 baseline (PRODUCT_DECISIONS.md). Tooling approved (B-01).
**Priority order:** (1) calculation correctness, (2) honest labelling of figures, (3) privacy, (4) usability, (5) visuals.

A wrong number shown confidently is the worst failure this product can have. Most testing effort goes into the calculation rules.

---

## 1. Test layers

| Layer | Tool (approved, B-01) | What it covers | When it runs |
|---|---|---|---|
| Rule tests | Vitest | One or more named tests per approved rule A-01 to A-08 (section 2). | Every pull request |
| Golden scenarios | Vitest + shared JSON scenarios | Full schedules compared month by month across the engine, spreadsheet v2 and the Python reference (section 3). | Every pull request |
| Property-based tests | fast-check | Invariants over thousands of random loans (section 4). | Every pull request |
| Safeguard tests | Vitest + Testing Library | Labels, discrepancy display, validation (section 5). | Every pull request |
| End-to-end | Playwright | Customer journeys on desktop and mobile; no loan data leaves the browser. | Every pull request (smoke), nightly (full) |
| Accessibility | axe in Playwright + manual | Target pending L-05. | Every pull request; manual per release |
| Acceptance | Real borrowers | Results compared with bank statements; explanations understood. | Each release gate |

## 2. Test cases for the eight approved calculation rules (S-07)

Each case runs against all three implementations: the TypeScript engine, spreadsheet v2 and the Python reference. Expected values below are in whole paise (A-02 as amended by B-06); displayed values are rounded to the nearest rupee. They are asserted in `reference/python/test_loan_reference.py`.

### A-01 Monthly reducing-balance interest

| ID | Case | Expected |
|---|---|---|
| T-A01-1 | ₹50,00,000 at 8.5%, month 1 interest | 5,000,000 × 8.5 / 1200 = ₹35,416.67 (shown ₹35,417) |
| T-A01-2 | Interest each month uses that month's opening balance | Interest(n) = Opening(n) × rate / 1200 for every n |
| T-A01-3 | 0% interest | Interest is exactly ₹0 every month; EMI = loan ÷ tenure |
| T-A01-4 | Known EMIs | ₹50L, 8.5%, 240 months: EMI ₹43,391.16 (shown ₹43,391). ₹30L, 9%, 240 months: EMI ₹26,991.78 (shown ₹26,992) |

### A-02 Paisa rounding, display rounding (amended by B-06)

| ID | Case | Expected |
|---|---|---|
| T-A02-1 | Paisa rounding inside the schedule | ₹50L at 8.5%, 240 months: every amount is whole paise; interest + principal = payment and opening − principal = closing in every row; final EMI ₹43,392.20; total interest ₹54,13,879.44 (shown ₹54,13,879) |
| T-A02-2 | Rounding direction | Half-up at the paisa (₹1.005 → ₹1.01) and at the rupee (₹x.50 up, ₹x.49 down); balances never negative |
| T-A02-3 | Totals | Displayed total = round(exact sum of paise rows), not the sum of rupee-rounded rows; note shown where they differ |
| T-A02-4 | Spreadsheet and engine agree | Every amount identical to the paisa across implementations for all golden scenarios |

### A-03 Rate change from the first full period on or after the effective date

EMIs due on the 5th of each month. A calculation period runs from one EMI date to the next (approved, B-02).

| ID | Case | Expected |
|---|---|---|
| T-A03-1 | Effective 1 June | 5 June EMI uses the previous rate; new rate first used for the period 5 June to 5 July (EMI due 5 July) |
| T-A03-2 | Effective 5 June (same day as a period start) | New rate first used for the period starting 5 June |
| T-A03-3 | Effective 6 June | New rate first used for the period starting 5 July |
| T-A03-4 | Two changes inside the same period | Only the later one applies from the next period start; no pro-rata blend |
| T-A03-5 | Effective date before the loan starts | Treated as the starting rate; validation warning |

### A-04 EMI and tenure options

| ID | Case | Expected |
|---|---|---|
| T-A04-1 | Rate rise, keep EMI (default) | EMI unchanged; tenure extends; closure date moves later |
| T-A04-2 | Rate rise, keep tenure | EMI recalculated on remaining balance and remaining months; closure date unchanged |
| T-A04-3 | Rate change with bank-revised EMI | The bank's EMI is used exactly, overriding both other options |
| T-A04-4 | Rate cut, keep EMI | Tenure shortens |
| T-A04-5 | Default when no option chosen | Keep EMI |

### A-05 Illustrative rates from public benchmarks

| ID | Case | Expected |
|---|---|---|
| T-A05-1 | Repo-linked loan, past rates unknown | Missing periods = historical repo rate + estimated spread (B-03), labelled Illustrative |
| T-A05-1b | MCLR-linked loan | No automatic estimate: entered rates are used, gaps carry forward labelled Estimated; the SBI or Bank of Baroda MCLR on a date is available as a labelled reference (B-07) |
| T-A05-1c | Base Rate-linked loan | Uses that lender's historical Base Rate + spread |
| T-A05-1d | Benchmark unknown | Repo linkage is **not** assumed; last known rate carried forward, labelled Estimated |
| T-A05-1e | BPLR-linked loan without a contractual reference | No public estimate; last known rate carried forward, labelled Estimated |
| T-A05-1f | Spread | Spread = known rate − benchmark on the same date; a spread entered from the sanction letter takes priority |
| T-A05-2 | Labelling | Every figure depending on a benchmark-derived rate is labelled Illustrative, source Public benchmark, with table version and date |
| T-A05-3 | Never shown as actual | No benchmark-derived rate or figure can carry the Actual label (type-level and unit tests) |
| T-A05-4 | Customer or bank rate available for a period | It replaces the benchmark estimate for that period |
| T-A05-5 | Same table in both interfaces | Engine and spreadsheet v2 read identical benchmark values (checksum test) |

### A-06 Dated bank figures as projection starting point

| ID | Case | Expected |
|---|---|---|
| T-A06-1 | Bank outstanding dated 31 March, differs from model | The bank figure becomes the opening balance of the period 31 March falls in (5 March to 5 April), so the EMI due 5 April uses it; compared with the model's balance after the 5 March EMI; modelled history unchanged |
| T-A06-2 | Difference preserved | Bank value, modelled value and difference (with direction) all returned and displayed |
| T-A06-3 | Bank figure without a date | Not used as a starting point; shown as comparison only, with a prompt for the date |
| T-A06-4 | Source recorded | Source document type and date carried on the figure's label |
| T-A06-5 | No silent reconciliation | Entering a bank figure never changes any modelled figure before its date |

### A-07 Final EMI equals the exact remaining amount due

Rule detail approved (B-04): regular EMI stays the same; any remaining amount due is absorbed into the final EMI.

| ID | Case | Expected |
|---|---|---|
| T-A07-1 | Calculated EMI, original tenure | Loan closes in exactly 240 months with zero balance; final EMI ₹43,392.20; no extra EMI |
| T-A07-2 | Bank-rounded EMI ₹43,391 on ₹50L, 8.5%, 240 months | Final (240th) EMI is the exact remaining due, ₹43,492.55 (shown ₹43,493); no 241st EMI of about ₹102 |
| T-A07-3 | Keep-EMI after a rate cut, tenure moving | Final payment = exact balance + that month's interest, which may be smaller than a normal EMI |
| T-A07-4 | No threshold | No code path or formula uses a percentage threshold for the final EMI (code review + test) |

### A-08 Fully disbursed monthly loans only

| ID | Case | Expected |
|---|---|---|
| T-A08-1 | Standard loan | Full amount treated as disbursed one calendar month before EMI 1 (B-05) |
| T-A08-3 | EMI day 31, 30 or 29 | Falls on the last calendar day of shorter months and returns to the scheduled day when it exists (B-05) |
| T-A08-2 | Customer indicates partial disbursement or pre-EMI | Plain-English "not supported in this version" message; no results shown |

## 3. Golden scenarios

Three independent implementations must agree to the paisa for every month: TypeScript engine, spreadsheet v2 (recalculated headlessly in CI), Python reference. The scenarios live in `reference/scenarios/` and are regenerated and checked in CI.

| # | Scenario |
|---|---|
| G-01 | New loan, fixed rate, 20 years |
| G-02 | 0% interest |
| G-03 | Very short loans (1 and 12 months) |
| G-04 | Maximum tenure (480 months), ₹20 crore |
| G-05 | Existing borrower, no rate changes |
| G-06 | Existing borrower with several rate changes, mixed A-04 options |
| G-07 | Rate rise with EMI kept that makes EMI smaller than interest (must be flagged) |
| G-08 | Dated bank outstanding that differs from the model |
| G-09 | Bank-revised EMI |
| G-10 | Rate changes on, before and after a period start (A-03 boundaries) |
| G-11 | Bank-rounded EMI final adjustment (A-07) |
| G-12 | Unknown past rates filled from the benchmark table (A-05) |
| G-12b | Two rate changes inside one period with different choices (only the later applies), then keep tenure after the tenure was moving |
| G-13 | EMI due on the 31st: 31 Jan, 28 Feb, 31 Mar, 30 Apr, 31 May (B-05) |
| G-14 | MCLR-linked loan with some past rates not entered: carry-forward, labelled Estimated (B-07) |

The v1 workbook is not an approved calculation reference. Spreadsheet v2 becomes a reference only after it passes these scenarios against the Python reference.

## 4. Invariants (property-based tests)

For any valid generated loan:

1. Outstanding balance is never negative.
2. Each month: principal part + interest part = amount paid.
3. Total principal repaid = original loan when the loan closes.
4. Opening balance of month n+1 = closing balance of month n.
5. With 0% interest, interest is exactly zero.
6. A higher rate never gives lower total interest (same A-04 option).
7. Same input, same output.
8. Labels propagate: anything depending on an Illustrative input is Illustrative; on an Estimated input, at best Estimated.
9. A month where the EMI does not cover interest is always flagged.
10. Entering a dated bank figure never changes modelled figures before its date.

## 5. Safeguard tests (S-01 to S-06)

| Safeguard | Test |
|---|---|
| S-01 Labels | Every figure on every screen has a kind and a source; a test fails if a raw number is rendered outside the `<Figure>` component. |
| S-02 Modelled ≠ bank | Modelled figures always show "Modelled" and a "may differ from your bank" note; no modelled figure can carry the Bank-confirmed source. |
| S-03 Discrepancies kept | Bank vs modelled difference is displayed and never applied back to the model. |
| S-04 Dates and sources | A bank figure without date and source cannot become a projection starting point. |
| S-05 Invalid scenarios | EMI below interest, loan not closing, invalid dates, out-of-scope loan types all produce plain-English errors. |
| S-06 Consistency | Golden scenarios run against website engine and spreadsheet v2 in CI; any difference fails the build. |

## 6. Privacy tests (R-02, R-03)

- No network request from the website contains loan figures (Playwright network inspection).
- Nothing is written to browser storage or servers beyond what the approved design allows.
- If analytics or error monitoring is approved, their payloads are checked for loan fields.

## 7. Change control

- Any change to calculation output needs: updated golden scenarios, an engine version bump, the same change in spreadsheet v2, a changelog entry, and product-owner approval.
- The eight approved rules are not changed unless a material financial correctness issue is found, and then only with product-owner approval.
- Pull requests cannot merge with failing tests; tests are never skipped or disabled to get green.

## 8. Release 1.0 acceptance

1. All automated suites green.
2. At least 10 consented real loans compared with bank statements; differences explained or recorded as unresolved (verifier pending L-02).
3. Usability test with 5 non-financial users: can they say what they've paid in interest, what they still owe, and when the loan ends?
4. Product owner reviews explanation text and disclaimers.
