# Product Decisions Log

**Purpose:** Record every product and technical decision, who made it, and why, so the calculation logic and scope stay explainable over time.

**Status key:**

- **Approved** — decided by the product owner. Agreed baseline.
- **Confirmed** — stated in the PRD.
- **Proposed** — recommended by the architect (status shown as Pending until approved).
- **Pending** — a detail or decision not yet approved. Written down so it can be approved or corrected; not treated as decided.

Last updated: 22 November 2026 (consolidated approval for Release 1.0, then decisions on B-01 to B-05 and documentation commit).

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
| A-02 | Rounding | Retain full precision internally. Round customer-facing displayed amounts to the nearest rupee. |
| A-03 | Interest-rate changes | Apply the revised rate from the first full monthly calculation period beginning on or after its effective date. No mid-month pro-rata calculation in Release 1.0. |
| A-04 | EMI and tenure adjustment | Three options: keep EMI and extend tenure (default), keep tenure and recalculate EMI, or enter the bank-revised EMI. |
| A-05 | Unknown historical rates | Use publicly available historical benchmark information to provide illustrative estimates when actual historical rates are unavailable. Never represent benchmark rates as the customer's actual rate. |
| A-06 | Bank-provided figures | Use valid, dated bank-reported figures as the starting point for future projections. Preserve and display differences from modelled figures. Never silently force reconciliation. |
| A-07 | Final EMI | Adjust the final EMI to the exact remaining amount due, including applicable interest. No arbitrary 1% threshold or unnecessary extra EMI. |
| A-08 | Partial disbursements | Only fully disbursed monthly home loans. Partial disbursements and pre-EMI are excluded. |

### 3.1 Implementation details of each rule

The approved rules above are final. The details below explain how each rule is applied; they were approved on 22 Nov 2026 as B-02 to B-05 unless marked **(Pending)**. Nothing here reopens an approved rule.

**A-01.** Interest for a period = opening balance × annual rate ÷ 1200, at full precision. Example: ₹50,00,000 at 8.5% gives ₹35,416.6667 interest in month 1 (displayed ₹35,417).

**A-02.**
- Full precision means decimal arithmetic with at least 28 significant digits on the website. Google Sheets/Excel use about 15 significant digits, which is far finer than a paisa over 480 months, so both implementations agree on every displayed rupee.
- The **calculated EMI is kept at full precision** in the schedule. Example: ₹50L, 8.5%, 240 months gives an EMI of ₹43,391.1617, displayed as ₹43,391.
- When the customer enters their bank's EMI (which banks round, usually to the rupee), that exact amount is used.
- Display rounding is round-half-up to the nearest rupee. Totals are rounded from their full-precision value, not added up from rounded rows, so a column of rounded rows can differ from its displayed total by a rupee or two. The screen will say so where it matters.

**A-03.**
- **(Approved, B-02)** A monthly calculation period runs from one EMI due date to the next EMI due date. No mid-period splitting in Release 1.0. Interest for that period is charged with the EMI at its end.
- A new rate applies from the first period whose **start** date is on or after the effective date.
- Example: EMIs on the 5th; a rate change effective 1 June applies to the period 5 June to 5 July, so first to the EMI due 5 July. An effective date of exactly 5 June also starts with that period. An effective date of 6 June starts with the period 5 July to 5 August.
- **This differs from the v1 spreadsheet**, which applied a change to the EMI due on or after the effective date (in the example, the EMI due 5 June). See section 5.

**A-04.** No change from the v1 spreadsheet. Each rate change carries its own choice. A bank-revised EMI overrides the other two options for that change.

**A-05.**
- Release 1.0 ships a dated, versioned table of public benchmark rates bundled with the website and the spreadsheet (so no customer data is sent anywhere to look it up).
- **(Approved with qualification, B-03)** Estimated loan rate = historical benchmark rate + estimated spread, using the loan's **own** benchmark system:

  | Loan's benchmark | Illustrative estimate |
  |---|---|
  | Repo-linked (external benchmark) | Historical RBI repo rate + applicable spread |
  | MCLR-linked | Historical MCLR + applicable spread |
  | Base Rate-linked | Historical Base Rate + applicable spread |
  | BPLR-linked (older loans) | Needs its own contractual reference; no public estimate is assumed |
  | Not known | Repo linkage is **not** assumed |

- The estimated spread is the customer's known rate on a known date minus the benchmark on that date (as proposed and approved); a spread the customer enters from their sanction letter takes priority.
- Where no reliable benchmark information is available (benchmark unknown, BPLR without a reference, or no data for that lender and period), the **last known rate is carried forward** and the result is labelled **Estimated**, with the assumption stated.
- Every figure that depends on a benchmark-derived rate is labelled **Illustrative**, with the benchmark, source and date shown.
- **(Pending, B-07)** MCLR and Base Rate are set by each lender, so the table needs lender-specific histories, and these loans change rate only on their reset dates. Which lenders are covered in Release 1.0, and how reset dates are captured, is pending.
- Customer-entered or bank-documented rates always replace benchmark estimates for the periods they cover.
- **This differs from the v1 spreadsheet**, which held the starting rate constant and labelled figures Estimated.

**A-06.**
- Each bank-reported figure (outstanding principal, current rate, current EMI, remaining EMIs) must have an "as at" date and a source (for example "annual statement", "rate-change letter", "bank app"). A figure without a date is not used as a projection starting point; it is shown as a comparison only.
- The projection restarts from the first period starting on or after that date, using the bank's figure.
- The modelled history up to that date is kept unchanged, and the difference (bank minus modelled) is displayed with its direction and size.
- **This differs from the v1 spreadsheet**, which had one general "as of" date and no source field. See section 5.

**A-07.**
- **(Approved, B-04)** The regular EMI stays the same and any remaining amount due is absorbed into the final EMI, which equals the actual outstanding plus applicable interest; no unnecessary extra instalment is created. If the loan has a scheduled maturity (the original tenure, a keep-tenure recalculation, or a bank-stated remaining tenure), the EMI in the last scheduled month equals exactly the balance plus that month's interest. A small leftover caused by a rounded bank EMI is absorbed into that final EMI. Example: ₹50L, 8.5%, 240 months with a bank EMI of ₹43,391 has a final (240th) EMI of ₹43,492, not a 241st EMI of ₹102.
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

## 5. Where the v1 spreadsheet now differs from the approved rules

The v1 workbook (`home-loan-reality-check/Home_Loan_Reality_Check_v1.xlsx`) was built before this approval. **v1 is not the approved calculation reference.** Under D-04 it must be updated to v2 so both interfaces agree; v2 becomes the approved reference only after it is built and validated against the Python reference and the golden scenarios.

| Rule | v1 spreadsheet | Approved | Change needed |
|---|---|---|---|
| A-01 | Rate / 12 on reducing balance | Same | None |
| A-02 | EMI rounded to the rupee; interest rounded to the paisa each month | Full precision; round only for display | Remove internal ROUNDs; use number formats for display |
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
| P-03a | How "integer paise" (approved in B-01) fits with full internal precision (A-02). | **Pending** (B-06) | Hard (decide now) |
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
| B-04 | Final EMI | Approved: ₹50L, 8.5%, 240 months with a ₹43,391 bank EMI has a 240th EMI of ₹43,492; no extra instalment. |
| B-05 | Disbursement and EMI dates | Approved: full disbursement one calendar month before EMI 1; 29th–31st fall on the last day of shorter months, then return to the scheduled day. |

### 8.2 Still blocking (needed during Phase 1)

| # | Decision needed | Blocks | Architect's suggestion (not decided) |
|---|---|---|---|
| B-06 | "Integer paise" (B-01) and "retain full precision internally" (A-02) can conflict. If every monthly amount is stored as whole paise, interest is rounded to the paisa each month, which A-02 rules out. | Engine number types | Calculate everything in full-precision decimal.js. Use integer paise only for amounts that are naturally whole paise: customer-entered and bank-reported money, and test fixtures. This keeps A-02 unchanged. |
| B-07 | Benchmark coverage for Release 1.0: which lenders' MCLR and Base Rate histories are included, the source of each, and how reset dates (for example annual MCLR resets) are captured. | Benchmark table; Phase 1 gate | Start with the RBI repo rate plus MCLR/Base Rate histories of a short list of large lenders; ask the customer for the reset frequency, and carry forward (Estimated) where unknown. |

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
| Engine stores money as integer paise, rounding interest to the paisa | A-02 requires full internal precision; B-01 approved "decimal.js + integer paise" | Full-precision decimal.js for calculation; role of integer paise pending B-06. |
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
