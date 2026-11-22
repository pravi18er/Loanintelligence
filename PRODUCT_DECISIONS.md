# Product Decisions Log

**Purpose:** Record every product and technical decision, who made it, and why, so the calculation logic and scope stay explainable over time.

**Status key:**

- **Approved** — decided by the product owner. Agreed baseline.
- **Confirmed** — stated in the PRD.
- **Proposed** — recommended by the architect (status shown as Pending until approved).
- **Pending** — a detail or decision not yet approved. Written down so it can be approved or corrected; not treated as decided.

Last updated: 22 November 2026 (consolidated approval for Release 1.0; decisions B-01 to B-09; documentation commit; phase plan approved).

---

## 1. Product direction (Approved, 22 Nov 2026)

**Website-first with spreadsheet support (Option C).**

| ID | Decision |
|---|---|
| D-01 | The website is the primary customer-facing product. |
| D-02 | The Excel / Google Sheets workbook remains a usable customer-facing alternative. |
| D-03 | The spreadsheet also serves as a calculation reference for validating the website. |
| D-04 | Both interfaces follow the same approved calculation rules. Conflicting calculation logic across the two is not allowed. |

Consequence: the calculation rules in section 3 are the single source of truth. The website engine and the spreadsheet are two implementations of the same rules, checked against each other by shared test scenarios (see TEST_STRATEGY.md). Any rule change updates both, or neither.

## 2. Release 1.0 product constraints (Approved, 22 Nov 2026)

| ID | Constraint |
|---|---|
| R-01 | Anonymous customer experience (no account needed). |
| R-02 | Calculations performed locally in the customer's browser. |
| R-03 | No customer loan information stored by default. |
| R-04 | English language only. |
| R-05 | Standard, fully disbursed monthly home loans only. |
| R-06 | Credit cards remain a separate future product track. |

## 3. Approved calculation rules for Release 1.0

| ID | Area | Approved decision |
|---|---|---|
| A-01 | Interest calculation | Monthly reducing-balance interest: opening principal × annual interest rate / 1200. |
| A-02 | Rounding | **Amended 22 Nov 2026 (B-06):** round every monetary amount to the paisa (integer paise): the EMI and each month's interest, principal and balance. Round customer-facing displayed amounts to the nearest rupee. *(Originally: retain full precision internally.)* |
| A-03 | Interest-rate changes | Apply the revised rate from the first full monthly calculation period beginning on or after its effective date. No mid-month pro-rata calculation in Release 1.0. |
| A-04 | EMI and tenure adjustment | Three options: keep EMI and extend tenure (default), keep tenure and recalculate EMI, or enter the bank-revised EMI. |
| A-05 | Unknown historical rates | Use publicly available historical benchmark information to provide illustrative estimates when actual historical rates are unavailable. Never represent benchmark rates as the customer's actual rate. |
| A-06 | Bank-provided figures | Use valid, dated bank-reported figures as the starting point for future projections. Preserve and display differences from modelled figures. Never silently force reconciliation. |
| A-07 | Final EMI | Adjust the final EMI to the exact remaining amount due, including applicable interest. No arbitrary 1% threshold or unnecessary extra EMI. |
| A-08 | Partial disbursements | Only fully disbursed monthly home loans. Partial disbursements and pre-EMI are excluded. |

### 3.1 Implementation details of each rule

The approved rules above are final. The details below explain how each rule is applied; they were approved on 22 Nov 2026 as B-02 to B-06 unless marked **(Pending)**. Nothing here reopens an approved rule.

**A-01.** Interest for a period = opening balance × annual rate ÷ 1200, rounded to the paisa (A-02). Example: ₹50,00,000 at 8.5% gives ₹35,416.67 interest in month 1 (displayed ₹35,417).

**A-02 (as amended by B-06).**
- Every monetary amount is held in whole paise. Calculations use decimal.js, and each result is rounded half-up to the paisa (the same as the spreadsheet's ROUND function) at these points: the EMI when it is calculated or recalculated, and each month's interest. Principal (payment − interest) and the closing balance (opening − principal) are then exact in paise.
- Example: ₹50L, 8.5%, 240 months gives an EMI of ₹43,391.16 (displayed ₹43,391), month 1 interest of ₹35,416.67, a final 240th EMI of ₹43,392.20 and total interest of ₹54,13,879.44.
- When the customer enters their bank's EMI, that exact amount is used.
- Display rounding is half-up to the nearest rupee. Totals are the exact sum of the paise rows, then rounded for display, so a column of rounded rows can differ from its displayed total by a rupee or two. The screen will say so where it matters.
- Because the spreadsheet rounds at the same points, the website and spreadsheet agree to the paisa, not just to the rupee.

**A-03.**
- **(Approved, B-02)** A monthly calculation period runs from one EMI due date to the next EMI due date. No mid-period splitting in Release 1.0. Interest for that period is charged with the EMI at its end.
- A new rate applies from the first period whose **start** date is on or after the effective date.
- Example: EMIs on the 5th; a rate change effective 1 June applies to the period 5 June to 5 July, so first to the EMI due 5 July. An effective date of exactly 5 June also starts with that period. An effective date of 6 June starts with the period 5 July to 5 August.
- **This differs from the v1 spreadsheet**, which applied a change to the EMI due on or after the effective date (in the example, the EMI due 5 June). See section 5.

**A-04.** Each rate change carries its own choice. A bank-revised EMI overrides the other two options for that change.
- **(Implementation detail, Phase 1)** If several changes fall inside one calculation period, only the last one applies, with its own choice (consistent with A-03's "no mid-period splitting").
- **(Implementation detail, Phase 1)** "Keep tenure" after the tenure has been moving uses the month the loan would have closed at the previous rate and EMI, worked out with the standard formula n = −ln(1 − r·B/E) ÷ ln(1 + r), rounded up. The spreadsheet uses ROUNDUP(NPER(...)), which gives the same result.

**A-05.**
- Release 1.0 ships a dated, versioned table of public benchmark rates bundled with the website and the spreadsheet (so no customer data is sent anywhere to look it up).
- **(Approved with qualification, B-03)** Estimated loan rate = historical benchmark rate + estimated spread, using the loan's **own** benchmark system:

  | Loan's benchmark | Illustrative estimate |
  |---|---|
  | Repo-linked (external benchmark) | Historical RBI repo rate + applicable spread |
  | MCLR-linked | No automatic estimate (B-07): the customer enters each past rate; the bundled SBI and Bank of Baroda MCLR history is shown beside the loan as a reference only |
  | Base Rate-linked | No bundled Base Rate history in Release 1.0 (B-07); the customer enters past rates |
  | BPLR-linked (older loans) | Needs its own contractual reference; no public estimate is assumed |
  | Not known | Repo linkage is **not** assumed |

- **(Approved, B-09, 22 Nov 2026)** For a repo-linked loan the customer gives the bank's reset frequency (every 1, 3, 6 or 12 months; **every 3 months if unsure**) and, optionally, the first reset date (default: one reset interval after disbursement) and the spread from the sanction letter. At each reset date up to the report date, the estimate is the RBI repo rate in force on that date (from its announcement date) plus the spread. It becomes a keep-EMI rate change (A-04 default) only if it differs from the rate in force just before, and then applies from the first period starting on or after the reset date (A-03). There is no estimate in a reset interval where the customer entered a rate change, or where a repo rate is not available (before 7 Aug 2019); the last known rate then carries forward, labelled Estimated. Figures that use an estimated rate are labelled Illustrative, from public benchmark rates.
- The estimated spread is the customer's known rate on a known date minus the benchmark on that date (as proposed and approved); a spread the customer enters from their sanction letter takes priority.
- Where no reliable benchmark information is available (benchmark unknown, BPLR without a reference, or no data for that lender and period), the **last known rate is carried forward** and the result is labelled **Estimated**, with the assumption stated.
- Every figure that depends on a benchmark-derived rate is labelled **Illustrative**, with the benchmark, source and date shown.
- **(Approved, B-08)** After a bank-revised EMI (A-04 option 3), the loan keeps its existing scheduled maturity, so any remainder is absorbed into the final EMI (B-04).
- **(Approved, B-07, 22 Nov 2026)** Release 1.0 bundles the official MCLR histories of **SBI and Bank of Baroda** only, copied from each bank's own website (`data/benchmarks/mclr/`). HDFC Bank, ICICI Bank and Axis Bank publish no official MCLR history, so none is bundled for them. MCLR resets are **not** modelled: the customer enters each past rate of an MCLR-linked loan, and the bundled history is shown beside the loan as a reference only. Any period without an entered rate carries forward the last known rate, labelled Estimated. Base Rate histories are not bundled (the answer named MCLR only).
- Customer-entered or bank-documented rates always replace benchmark estimates for the periods they cover.
- **This differs from the v1 spreadsheet**, which held the starting rate constant and labelled figures Estimated.

**A-06.**
- Each bank-reported figure (outstanding principal, current rate, current EMI, remaining EMIs) must have an "as at" date and a source (for example "annual statement", "rate-change letter", "bank app"). A figure without a date is not used as a projection starting point; it is shown as a comparison only.
- **(Correctness fix, Phase 1)** A dated balance is the balance after every EMI due on or before its date. It becomes the opening balance of the period that date falls in, so the first EMI due after the date is calculated from it. The model's balance on the same date (after the last EMI due on or before it) is what it is compared with. An earlier draft of this note said "from the first period starting on or after that date", which would have compared the bank's balance with the model one EMI later and ignored the bank's figure for a month.
- The modelled history up to that date is kept unchanged, and the difference (bank minus modelled) is displayed with its direction and size.
- **This differs from the v1 spreadsheet**, which had one general "as of" date and no source field. See section 5.

**A-07.**
- **(Approved, B-04)** The regular EMI stays the same and any remaining amount due is absorbed into the final EMI, which equals the actual outstanding plus applicable interest; no unnecessary extra instalment is created. If the loan has a scheduled maturity (the original tenure, a keep-tenure recalculation, or a bank-stated remaining tenure), the EMI in the last scheduled month equals exactly the balance plus that month's interest. A small leftover caused by a rounded bank EMI is absorbed into that final EMI. Example: ₹50L, 8.5%, 240 months with a bank EMI of ₹43,391 has a final (240th) EMI of ₹43,492.55 (displayed ₹43,493), not a 241st EMI of about ₹102. (The example approved under B-04 showed ₹43,492 under full precision; rounding each month to the paisa under B-06 moves it by 18 paise.)
- If the tenure is moving because the EMI is being kept after a rate change, the loan closes in the first month where balance plus interest is no more than the EMI, and that final payment is exactly balance plus interest (it can be smaller than a normal EMI).
- No percentage threshold is used anywhere.
- **This differs from the v1 spreadsheet**, which used a 1%-of-EMI threshold.

**A-08 and dates.** **(Approved, B-05)** Modelling convention, not a claim about the actual bank disbursement date: full disbursement is assumed one calendar month before the first EMI. EMIs due on the 29th, 30th or 31st fall on the last calendar day of shorter months and return to the scheduled day when it exists again (31 Jan, 28 Feb, 31 Mar, 30 Apr, 31 May). Under-construction loans with tranches or pre-EMI interest are rejected with a plain-English message.

## 4. Implementation safeguards (Approved, 22 Nov 2026)

| ID | Safeguard | How it is built in |
|---|---|---|
| S-01 | Clearly distinguish actual, bank-confirmed, customer-provided, modelled, estimated and illustrative information. | Two-part label on every figure (section 4.1). |
| S-02 | Never represent a modelled calculation as an exact bank calculation. | Modelled figures always carry the "Modelled" label and a "may differ from your bank" note; bank figures are never relabelled. |
| S-03 | Preserve discrepancies between bank-reported and modelled figures. | Both values stored side by side in the result; the difference is a reported output, never applied back to the model. |
| S-04 | Capture effective dates and source information for bank-provided figures. | Date and source are required fields for any bank figure used in a projection (A-06). |
| S-05 | Flag invalid repayment scenarios, including where EMI does not cover interest. | Engine validation returns errors and warnings with plain-English text; negative amortisation is always flagged. |
| S-06 | Keep calculation logic consistent between website and spreadsheet. | Shared rules (section 3) and shared golden test scenarios run against both. |
| S-07 | Include test cases for all eight approved calculation conventions. | TEST_STRATEGY.md section 2 maps each of A-01 to A-08 to named test cases. |

### 4.1 Figure labels

Every figure carries two parts.

**What kind of figure it is:**

| Kind | Meaning |
|---|---|
| Actual | Something that really happened or is really owed, reported by the bank or the customer. |
| Modelled | Calculated from complete inputs using the approved rules. Not the bank's own calculation. |
| Estimated | Calculated, but some input is missing or assumed (for example, an EMI-paid count inferred from dates). |
| Illustrative | Depends on a public benchmark or a hypothetical assumption, not on the customer's own loan records. |

**Where the input came from:**

| Source | Meaning |
|---|---|
| Bank-confirmed | Taken from a bank document, with its date and document type. |
| Customer-provided | Entered by the customer from memory or their own records, without a bank document. |
| Public benchmark | From the bundled public benchmark table (A-05), with its source and date. |
| Calculated | Produced by the engine. |

Rules: a figure is only as strong as its weakest input. Anything calculated from an Illustrative input is Illustrative; anything calculated from an Estimated input is at best Estimated. "Actual" is only ever used with a Bank-confirmed or Customer-provided source, and the screen shows which.

## 5. Where the v1 spreadsheet differed from the approved rules (now replaced by v2)

Spreadsheet v2 (`spreadsheet/` in the repository) implements the approved rules and matches every golden scenario to the paisa, checked automatically in LibreOffice. The table below records what changed from v1.

The v1 workbook (`home-loan-reality-check/Home_Loan_Reality_Check_v1.xlsx`) was built before this approval. **v1 is not the approved calculation reference.** Under D-04 it must be updated to v2 so both interfaces agree; v2 becomes the approved reference only after it is built and validated against the Python reference and the golden scenarios.

| Rule | v1 spreadsheet | Approved | Change needed |
|---|---|---|---|
| A-01 | Rate / 12 on reducing balance | Same | None |
| A-02 | EMI rounded to the rupee; interest rounded to the paisa each month | EMI and every monthly amount rounded to the paisa (B-06) | Round the EMI to 2 decimals instead of 0 |
| A-03 | Change applies to the EMI due on or after the effective date | Change applies from the first period starting on or after the effective date | Shift the rate lookup by one period |
| A-04 | Three options per change | Same | None |
| A-05 | Unknown past rates held at starting rate, labelled Estimated | Benchmark by loan type (repo, MCLR, Base Rate) + spread, labelled Illustrative; carry-forward labelled Estimated where no reliable benchmark | Add benchmark type input, benchmark table and lookup; relabel |
| A-06 | One general "as of" date; no source field; bank figures take over at next EMI | Each bank figure dated and sourced; projection restarts from that date | Add date and source fields; restart logic |
| A-07 | Residual up to 1% of EMI folded into last EMI | Final EMI = exact remaining due; no threshold | Replace threshold logic with the maturity rule |
| A-08 | Full disbursement one month before EMI 1 | Same | None |
| Labels | Actual / Modelled / Estimated | Two-part labels, six categories (S-01) | Add source column and Illustrative |

Known EMI checks still hold at displayed level: ₹50L at 8.5% for 20 years shows ₹43,391; ₹30L at 9% for 20 years shows ₹26,992.

## 6. Architecture decisions

| ID | Decision | Status | Reversibility |
|---|---|---|---|
| P-01 | Website-first, spreadsheet kept as customer alternative and reference (v2 once validated). | **Approved** (D-01 to D-04) | Moderate |
| P-02 | TypeScript end to end. | **Approved** (B-01) | Hard |
| P-03 | Standalone, framework-free calculation engine using decimal.js. | **Approved** (B-01) | Hard |
| P-03a | Every monetary amount rounded to the paisa and held as integer paise (A-02 amended). | **Approved** (B-06) | Hard |
| P-04 | Two-part label on every figure as part of its data type (S-01). | **Approved** (S-01) | Hard |
| P-05 | Next.js, Tailwind CSS + shadcn/ui, Recharts, Zod; hosted on Vercel. | **Approved** (B-01) | Moderate |
| P-06 | Release 1.0 anonymous, in-browser, nothing stored. | **Approved** (R-01 to R-03) | Easy |
| P-07 | Engine and benchmark table versioned. | Pending (follows from S-06; low risk) | Easy now, hard to retrofit |
| P-08 | Engine must match spreadsheet v2 and an independent Python reference on shared golden scenarios before any release. | **Approved** (S-06, S-07) | — |
| P-09 | Vitest, fast-check, Playwright; pnpm workspaces monorepo. | **Approved** (B-01) | Easy |
| P-10 | Supabase, PostgreSQL, authentication and any database infrastructure. | **Deferred** (B-01): not built for Release 1.0, and not built ahead of need for later releases | — |
| P-11 | Razorpay payments; Sentry error monitoring; product analytics. | Pending (F-01, L-07) | Easy |
| P-12 | No storage of uploaded bank statements by default (Release 1.2). | Pending (consistent with R-03) | Easy |

## 7. Observations on the PRD

1. **Technology direction.** PRD §14 names Google Sheets as the MVP platform. Now resolved by D-01 to D-04.
2. **Release plan vs MoSCoW list differ.** Preclosure Shock Test and Historical Reconstruction are "Should Have" (§11) but appear in Releases 1.3 and 1.2 (§16). Balance transfer is "Could Have" but a Release 1.3 headline. ROADMAP.md follows §16.
3. **Benchmark-based rates move forward.** A-05 brings illustrative benchmark rates into Release 1.0. PRD FR-05 had said manual entry and illustrative assumptions are prioritised for the MVP, with public-rate research later. Full historical reconstruction (lender-specific research, bank-documented histories) stays in Release 1.2.
4. **Free vs premium overlap.** "Basic interest-rate change support" is MVP Must Have, while "Dynamic interest-rate simulation" is premium. Boundary pending (F-01).
5. **Accrued interest in preclosure (FR-09)** implies daily interest between EMI dates, which A-03 excludes from Release 1.0. To be decided for Release 1.3.

## 8. Pending decisions

### 8.1 Decided on 22 Nov 2026

| # | Decision | Outcome |
|---|---|---|
| B-01 | Technology stack | Approved: TypeScript, standalone engine, decimal.js + integer paise, Next.js, Tailwind + shadcn/ui, Recharts, Zod, Vitest + fast-check + Playwright, pnpm monorepo, Vercel. Supabase, PostgreSQL, authentication and database infrastructure deferred. |
| B-02 | Rate-change period | Approved: one EMI date to the next; a change effective 1 June with EMIs on the 5th first affects the 5 July EMI. |
| B-03 | Benchmark method | Approved with qualification: benchmark by loan type (section 3.1, A-05); never assume repo linkage; carry forward last known rate, labelled Estimated, where no reliable benchmark. |
| B-04 | Final EMI | Approved: ₹50L, 8.5%, 240 months with a ₹43,391 bank EMI has a 240th EMI of ₹43,492 (₹43,492.55, shown ₹43,493, after the B-06 paisa rule); no extra instalment. |
| B-05 | Disbursement and EMI dates | Approved: full disbursement one calendar month before EMI 1; 29th–31st fall on the last day of shorter months, then return to the scheduled day. |
| B-06 | Integer paise vs full precision | Approved: round every amount to the paisa ("go for round numbers"). A-02 amended accordingly. |
| B-08 | Tenure after a bank-revised EMI | Approved: keep the existing maturity; any remainder is absorbed into the final EMI. |
| B-09 | Repo reset timing | Approved: ask the reset frequency (quarterly if unsure); each repo change reaches the estimate at the loan's next reset date (section 3.1, A-05). |
| B-07 | Benchmark coverage | Approved: official MCLR histories of SBI and Bank of Baroda only (HDFC, ICICI and Axis publish none), shown as a reference; customers enter each past MCLR rate; no MCLR reset modelling; no Base Rate table. RBI repo rate history for repo-linked loans per B-03. |

### 8.2 Still blocking (needed during Phase 1)

| # | Decision needed | Blocks | Architect's suggestion (not decided) |
|---|---|---|---|
| — | None at present. | | |

### 8.3 Needed before public launch of Release 1.0 (not blocking the engine)

| # | Decision needed | Architect's suggestion (not decided) |
|---|---|---|
| L-01 | Who maintains the benchmark table, and how quickly after an RBI or lender rate change? | Within a week of each policy change; each update versioned and dated. |
| L-02 | Who independently verifies calculations (for example a chartered accountant, or real statements from volunteer borrowers)? | At least 10 real anonymised loans compared. |
| L-03 | On-screen wording for items outside 1.0 (tax benefits, PMAY subsidy, bundled insurance, joint borrowers). | A short "not included" list on the assumptions page. |
| L-04 | Product name and website domain. | — |
| L-05 | Accessibility target. | WCAG 2.1 AA. |
| L-06 | Support channel: which email address and tool? | Shared inbox; never ask for loan documents by email. |
| L-07 | Whether to use error monitoring or analytics at all, given anonymous use. | Only if no loan figures can reach them. |

### 8.4 Needed for later releases

| # | Decision needed | Needed by |
|---|---|---|
| F-01 | Free vs premium boundary and pricing; payment provider (P-09). | Release 1.1 |
| F-02 | Whether accounts and saved loans are offered at all; if so, retention and deletion policy and the database/authentication choice (deferred under B-01). | Before any storage is introduced |
| F-03 | Bank schedule input formats. | Release 1.2 |
| F-04 | Daily interest / accrued interest for preclosure and reconciliation. | Release 1.2 / 1.3 |
| F-05 | Balance-transfer process assistance for a fee (legal review). | Before Release 1.3 |
| F-06 | Release order where PRD §11 and §16 differ (Preclosure, Historical Reconstruction, Balance Transfer). ROADMAP follows §16 until you decide. | Release 1.1 planning |

Answered by the approval: product direction (D-01 to D-04), language (R-04), accounts for 1.0 (none, R-01), storage (none by default, R-03), loan types (R-05).

## 9. Deferred features (not in Release 1.0)

| Feature | PRD reference | Planned release |
|---|---|---|
| Accounts and saved loans | — | Not scheduled; pending F-02 |
| Dynamic multi-scenario rate simulator and rate comparison | FR-04 (beyond basic changes), FR-12 | 1.1 |
| Prepayment simulator | FR-08 | 1.1 |
| Top-up loan simulator | FR-10 | 1.1 |
| Premium tier and payments | §10 | 1.1 |
| Bank schedule entry/import and reconciliation | FR-06, FR-07 (beyond the single-balance comparison in 1.0) | 1.2 |
| Full historical rate reconstruction (lender-specific, bank-documented histories) | FR-05 | 1.2 |
| Daily interest, mid-month pro-rata rate changes | A-03 excludes from 1.0 | 1.2 / 1.3 |
| Preclosure Shock Test | FR-09 | 1.3 |
| Balance transfer calculator | FR-11 | 1.3 |
| Downloadable reports | §10 | 1.3 |
| Paid process assistance | §7 Stage 5, FR-15 | Pending legal review |
| Partial disbursements, pre-EMI | A-08 | Not scheduled |
| Languages other than English | R-04 | Not scheduled |
| Personal, vehicle, gold loans | §6.2 | Future |
| Credit cards | §6.2, R-06 | Separate product track |

## 10. Changes to architecture and release scope caused by the approval

| Earlier proposal | Conflict | Required change |
|---|---|---|
| Engine stores money as integer paise, rounding interest to the paisa | A-02 originally required full internal precision | Resolved by B-06: A-02 amended to paisa rounding; the original proposal stands. |
| Four labels (Actual / Modelled / Estimated / Illustrative) | S-01 lists six categories | Two-part label: kind (Actual, Modelled, Estimated, Illustrative) plus source (Bank-confirmed, Customer-provided, Public benchmark, Calculated). |
| v1 spreadsheet as the validation oracle | v1 follows old A-02, A-03, A-05, A-06, A-07 | Spreadsheet v2 must be built to the approved rules; v1 retired as a reference for those rules. |
| Historical rate research deferred to 1.2 | A-05 needs benchmark rates in 1.0 | A bundled, versioned public benchmark table moves into Release 1.0 (Phase 1). Lender-specific reconstruction stays in 1.2. |
| Phase 3 "Accounts and saved loans" as the next step after 1.0 | R-01 to R-03; B-01 defers Supabase, database and authentication | Removed from the committed roadmap; no infrastructure built ahead of need. Unscheduled, pending F-02. |
| Benchmark rule assumed repo linkage | B-03 qualification | Benchmark chosen by the loan's own system; unknown benchmark never assumed repo-linked. |
| Bank figures taken over from "next EMI" using one general date | A-06, S-04: dated, sourced figures | Each bank figure carries its own date and source; projection restarts from that date. |

## 11. Decision history

| Date | Decision | By |
|---|---|---|
| 22 Nov 2026 | PRD v0.1 adopted as reference spec. | Product owner |
| 22 Nov 2026 | Release 1.0 spreadsheet (v1) built and verified against known EMIs. | Product owner / AI partner |
| 22 Nov 2026 | Architecture P-01 to P-10 proposed. | AI architect |
| 22 Nov 2026 | Consolidated approval: website-first with spreadsheet support (D-01 to D-04), calculation rules A-01 to A-08, Release 1.0 constraints R-01 to R-06, safeguards S-01 to S-07. Supersedes the earlier assumed conventions. | Product owner (Praveen Sudhakaran) |
| 22 Nov 2026 | Decisions on B-01 to B-05 (stack with database/auth deferred; EMI-to-EMI period; benchmark by loan type; final EMI; date convention). Documentation commit approved. | Product owner (Praveen Sudhakaran) |
| 22 Nov 2026 | B-06: round every monetary amount to the paisa (A-02 amended). Phase plan approved; `main` branch created from the documentation commit; Phase 0 started. | Product owner (Praveen Sudhakaran) |
| 22 Nov 2026 | B-08: keep the existing maturity after a bank-revised EMI. B-07 partly decided: MCLR histories of SBI, HDFC Bank, ICICI Bank, Bank of Baroda and Axis Bank; Base Rate and reset capture still pending. | Product owner (Praveen Sudhakaran) |
| 22 Nov 2026 | B-09 decided: ask the reset frequency, quarterly if unsure; repo changes reach the estimate at the next reset. | Product owner (Praveen Sudhakaran) |
| 22 Nov 2026 | B-07 decided: SBI and Bank of Baroda MCLR histories only, shown as a reference; customers enter each past MCLR rate; no reset modelling. | Product owner (Praveen Sudhakaran) |
