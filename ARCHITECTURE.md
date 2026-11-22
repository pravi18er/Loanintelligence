# Architecture — Loan Intelligence Platform (Web)

**Status:** Updated 22 November 2026 for the product owner's approved Release 1.0 baseline (PRODUCT_DECISIONS.md). Core technology stack **approved** (B-01) with Supabase, PostgreSQL, authentication and database infrastructure **deferred**. Nothing is built yet.
**Date:** 22 November 2026
**Scope:** Home Loan Intelligence web application, designed so later loan modules (personal, vehicle, gold) reuse the same core.

How to read this document:

- **[Approved]** is a product-owner decision (IDs D-, R-, A-, S- in PRODUCT_DECISIONS.md).
- **[Confirmed]** comes directly from the PRD.
- **[Recommendation]** is the architect's proposal, pending approval.

---

## 1. Starting point

| Item | State on 22 Nov 2026 |
|---|---|
| GitHub repository `pravi18er/loanintelligence` | Empty. No commits, no branches other than the working branch. |
| PRD v0.1 | Complete for scope and features. Technology direction names **Google Sheets** as the MVP platform. |
| Release 1.0 spreadsheet (`Home_Loan_Reality_Check_v1.xlsx`) | Built and verified against known EMIs and an independent Python amortisation. Five tabs: Welcome, Loan Profile, Loan Reality Check, Repayment Engine (600 months), Validation & Assumptions. Predates the approved rules; differs on A-02, A-03, A-05, A-06, A-07. To be replaced by a v2 workbook. |

**[Approved, D-01 to D-04]** Website-first with spreadsheet support. The website is the primary product; the spreadsheet remains a customer-facing alternative and the calculation reference. Both follow the same approved rules (A-01 to A-08), with no conflicting logic.

**Consequence:** the v1 workbook predates the approved rules and differs on A-02, A-03, A-05, A-06 and A-07 (PRODUCT_DECISIONS.md section 5). v1 is **not** the approved calculation reference. A spreadsheet v2, built to the approved rules, becomes the reference only once it is validated against the Python reference and the golden scenarios.

---

## 2. Requirements that shape the architecture

### 2.1 Functional drivers [Confirmed, PRD §8]

| Driver | Source | Architectural consequence |
|---|---|---|
| Existing borrowers must start from *today's* balance, not be treated as a new loan | FR-01 | Engine needs an "anchor" concept: a known balance/rate/EMI at a date, from which projection restarts. |
| Every figure distinguishes actual, bank-confirmed, customer-provided, modelled, estimated, illustrative | §7 Stage 2, FR-05, S-01 | A two-part label (kind + source) must be part of the **data type** of every number, not a UI afterthought. |
| Multiple rate changes, with keep-EMI / keep-tenure / custom lender behaviour | FR-04 | Engine is event-driven: a timeline of rate changes, EMI changes and prepayments applied month by month. |
| Bank schedule entry/import and reconciliation, never auto-adjusting the model | FR-06, FR-07 | Two independent ledgers (bank vs modelled) compared side by side; a reconciliation module that explains differences. |
| Prepayment, preclosure, top-up, balance transfer, rate comparison | FR-08 to FR-12 | All are "scenarios": a base loan plus a list of events. One engine, many scenario builders. |
| Explain every important figure | FR-13 | Engine returns explanations/assumptions alongside numbers. |
| Validation of inputs, negative amortisation, inconsistencies | FR-14 | Shared validation schema used by both browser and server. |
| Future loan modules reuse components | §6.2, NFR Extensibility | Generic amortisation core + loan-specific rule packs. |

### 2.2 Non-functional drivers [Confirmed, PRD §9]

1. **Accuracy first.** Validated methods, no negative balances, zero-interest handling, no double counting, independent reconciliation.
2. **Transparency.** Assumptions and data quality visible.
3. **Privacy.** Minimise data collection; retention and deletion policies before launch.
4. **Simplicity.** Plain English, non-financial users, minimal inputs.
5. **Extensibility.** Calculation components separated from loan-specific rules.

### 2.3 Approved Release 1.0 constraints [Approved, R-01 to R-06]

Anonymous use; calculations in the browser; no loan data stored by default; English only; fully disbursed monthly home loans only; credit cards a separate track. These remove any need for a database, login or server-side storage in Release 1.0.

### 2.4 Team constraint [Recommendation]

The builder is a beginner-to-intermediate developer working with an AI partner. The stack should therefore favour: one language end to end, managed services over self-run servers, generous free tiers, large community and documentation, and few moving parts.

---

## 3. Technology stack [Approved, B-01, except where marked]

| Layer | Recommendation | Why | Main alternative considered |
|---|---|---|---|
| Language | **TypeScript** everywhere | One language for engine, UI and server; the type system catches unit and provenance mistakes early. | Python (excellent for finance maths, but a second language for the UI, and the engine could not run in the browser). |
| Calculation engine | **Standalone TypeScript package** (`packages/loan-engine`), zero framework dependencies, **`decimal.js`** for calculation, every amount rounded to the paisa and held as integer paise (A-02 as amended by B-06); rupee rounding for display | Runs identically in browser and server; can be tested in isolation; reusable by future modules and even by a future API or mobile app. | Calculations inside UI components (fast to start, very hard to test and trust). |
| Web framework | **Next.js** (React, App Router) | Most documented React framework; handles pages, server functions and APIs in one project; first-class hosting on Vercel. | Vite + React SPA with separate API (simpler mental model, but two deployables). |
| UI | **Tailwind CSS** + **shadcn/ui** components, **Recharts** for charts | Accessible defaults, copy-in components (no lock-in), simple charting. | MUI (heavier, more opinionated). |
| Input validation | **Zod** schemas shared by engine, forms and server | One definition of "valid loan input" everywhere. | Hand-written checks (drift between client and server). |
| Database, authentication (Supabase, PostgreSQL) | **Deferred** (B-01). Not part of Release 1.0 and not built ahead of need. | Release 1.0 is anonymous and stores nothing (R-01 to R-03). | Revisit only if accounts are approved (F-02). |
| Payments (pending F-01, not approved) | **Razorpay** proposed for Release 1.1 | Standard Indian gateway; UPI, cards, subscriptions. | Cashfree, Stripe India. |
| Monitoring (pending L-07, not approved) | **Sentry** (errors) with loan-data scrubbing | Catch production errors without seeing customer figures. | Vercel logs only. |
| Product analytics (pending L-07, not approved) | Privacy-friendly page analytics (e.g. Plausible), **no loan figures ever sent** | PRD success metrics need funnel data. | None at first. |
| Testing | **Vitest**, **fast-check** (property tests), **Playwright** (end to end) | See TEST_STRATEGY.md. | Jest. |
| Repository layout | **pnpm workspaces monorepo**: `apps/web`, `packages/loan-engine`, `reference/` (golden scenarios, Python reference, benchmark table), `spreadsheet/` (v2 workbook and its generator) | Makes the engine boundary physical, not just a convention. | Single app with an `engine/` folder (simpler, but boundary easily eroded). |

### 3.1 Role of the spreadsheet [Approved, D-02 to D-04]

The spreadsheet is kept as a customer-facing alternative and as the calculation reference. To keep one set of rules across both:

- The approved rules live in one place: PRODUCT_DECISIONS.md section 3.
- The v2 workbook is generated from a script kept in the repository, so its formulas are versioned and reviewable like code.
- The same golden scenarios (TEST_STRATEGY.md) run against the TypeScript engine, the v2 workbook (recalculated headlessly) and an independent Python reference. All three must agree on every displayed rupee before a release.
- The public benchmark table (A-05) is one data file used by both the website and the spreadsheet.
- Any rule change is made to both implementations in the same change, or not at all.

---

## 4. High-level architecture

### 4.0 Release 1.0 [Approved]

```
  Customer's browser (anonymous, nothing stored)
  ┌──────────────────────────────────────────────────────────┐
  │ Next.js website (static pages)                           │
  │  ┌──────────────────┐    ┌───────────────────────────┐   │
  │  │ Onboarding,      │───▶│ loan-engine (in browser)  │   │
  │  │ Reality Check,   │◀───│ + bundled benchmark table │   │
  │  │ explanations     │    └───────────────────────────┘   │
  │  └──────────────────┘                                    │
  └──────────────────────────────────────────────────────────┘
        ▲ page files only (no loan data sent)
  Vercel (static hosting)

  Repository: same rules, same golden scenarios
  loan-engine (TypeScript) ◀──▶ spreadsheet v2 ◀──▶ Python reference
```

There is no backend, database or login in Release 1.0. The server only delivers the website's files.

### 4.1 Frontend [Recommendation]

- Guided, progressive onboarding (PRD §7): new vs existing borrower first, then only the fields that matter.
- Bank-reported figures are entered with their "as at" date and source (A-06, S-04).
- Every displayed figure goes through one component (`<Figure>`) that shows its two-part label (S-01), rounds to the nearest rupee for display (A-02), and opens "How was this calculated?".
- Mobile-first responsive layout, English only (R-04).
- Accessibility target pending (L-05); WCAG 2.1 AA recommended.

### 4.2 Later releases (not Release 1.0)

- **Server functions** only when a feature genuinely needs them (for example payment webhooks in 1.1, pending F-01).
- **Accounts, storage, database and authentication** are deferred (B-01) and unscheduled. They are designed only if the product owner approves accounts (F-02); no infrastructure is built in anticipation.

### 4.3 Financial calculation engine [Approved, B-01 and A-01 to A-08]

The heart of the product. Design principles:

1. **Pure functions.** Input → output, no network, no clock (the "as of" date is an input), no randomness. Same input always gives the same result.
2. **Decimal maths, integer paise [Approved, B-01, B-06; A-02 amended].** Calculation uses `decimal.js`; the EMI and each month's interest are rounded half-up to the paisa, and all amounts are held as integer paise. Rounding to the nearest rupee happens only in the display layer. No JavaScript floating-point arithmetic on money.
3. **Approved rules, versioned [Approved, A-01 to A-08].** Interest = opening balance × rate / 1200; rate changes from the first full period starting on or after the effective date; three EMI/tenure options per change; final EMI = exact remaining due. These are fixed for Release 1.0, not customer settings. Every result records the rules version and the benchmark-table version used.
4. **Event timeline.** A loan is: initial terms + an ordered list of events (rate change, EMI change, dated and sourced bank figure; later releases add prepayment and top-up). The engine applies events month by month. Every simulator is just a different set of events.
5. **Two-part label on every value [Approved, S-01].** Each figure carries `{ value, kind: actual | modelled | estimated | illustrative, source: bank-confirmed | customer-provided | public-benchmark | calculated, asAt?, sourceDocument?, assumptions[] }`. Labels propagate: anything calculated from an Illustrative input is Illustrative; from an Estimated input, at best Estimated. A modelled figure can never be labelled as a bank figure (S-02).
6. **Bank figures kept apart [Approved, A-06, S-03, S-04].** A dated, sourced bank figure becomes the starting point for the projection from that date. The modelled history is not changed; the difference between bank and model is returned as its own output.
7. **Bundled benchmark table [Approved, A-05 and B-03].** A versioned, dated data file of public benchmark rates ships with the website and the spreadsheet. Repo-linked loans are estimated from the RBI repo rate plus the loan's spread at each reset date, with the reset frequency asked of the customer (quarterly if unsure) (B-03, B-09); repo linkage is never assumed when the benchmark is unknown, and BPLR loans need their own contractual reference. MCLR loans are not estimated: the customer enters each past rate, and the official SBI and Bank of Baroda MCLR histories are shown beside the loan as a reference (B-07). Benchmark-derived figures are Illustrative. Where no rate is known, the last known rate is carried forward and labelled Estimated.
8. **Layering for extensibility:**
   - `core/` generic amortisation, rounding, date schedule, provenance (reusable by any amortising loan).
   - `home-loan/` home-loan rules: floating-rate reset behaviour, existing-borrower starting point; later preclosure, top-up, balance transfer.
   - Later `personal-loan/`, `vehicle-loan/`, `gold-loan/` (gold loans often bullet repayment; will need a non-EMI schedule type). Credit cards stay a separate engine, as the PRD states.
9. **Engine versioning.** The engine has its own version, so any result can be reproduced or explained after the engine changes.
10. **Validation included [Approved, S-05].** The engine returns structured errors and warnings (EMI not covering interest, loan not closing, undated bank figures, partial-disbursement loans outside scope) with plain-English messages, matching the spreadsheet's Validation tab.

### 4.4 Hosting and environments [Approved: Vercel, B-01]

- Environments: local, preview (automatic per pull request), production.
- Secrets only in platform environment variables, never in the repository.
- Continuous integration (GitHub Actions): type check, lint, engine tests, golden-scenario comparison against the Python reference and spreadsheet v2 on every pull request; production deploys only from `main`.

---

## 5. Key technical risks and mitigations

### 5.1 Financial calculation accuracy (highest risk)

| Risk | Mitigation |
|---|---|
| Floating-point drift (e.g. 0.1 + 0.2) accumulating over 240+ months | `decimal.js` and integer paise; lint rule against float helpers on money. Spreadsheet v2 rounds at the same points, so both agree to the paisa. |
| Banks may round EMIs and interest differently from our paisa rule; the model will differ slightly | Expected and labelled: modelled figures say they may differ from the bank (S-02); customers can enter the bank's EMI (A-04). |
| Edge cases: zero interest, last EMI residual, loan closing early after prepayment, negative amortisation | Dedicated unit tests and property tests (balance never negative; principal + interest = EMI; total principal = loan). |
| Divergence between website and spreadsheet (S-06) | Shared golden scenarios run against the engine, spreadsheet v2 and an independent Python reference in CI; all displayed rupees must agree. |
| Silent behaviour change after code edits | Engine versioning, golden tests, and changelog entries for any change in output. |

### 5.2 Historical interest-rate handling

| Risk | Mitigation |
|---|---|
| Customers do not know past rates | Illustrative rates from the public benchmark table (A-05), clearly labelled; prompt for bank letters/annual statements to replace them. |
| Public benchmark rates (repo rate, EBLR/RLLR, MCLR) mistaken for the customer's actual rate | Source type in the label; benchmark-derived figures always Illustrative; never shown as the customer's rate (A-05). |
| Benchmark method misrepresents a customer's loan (for example MCLR loans, different spreads, reset dates) | Benchmark matched to the loan's own system (B-03); method stated on screen; carry forward the last known rate (Estimated) where no reliable benchmark; MCLR resets are not modelled; customers enter past MCLR rates, with official SBI and Bank of Baroda history shown as a reference (B-07). |
| Benchmark table goes stale | Versioned and dated table; maintenance owner pending (L-01). |
| Lenders reset rates on their own schedules and may apply mid-month, pro-rata interest | Release 1.0 applies changes from the first full period starting on or after the effective date (A-03), and says so; pro-rata handling is deferred (F-04). |
| Rate rise with EMI held causes negative amortisation | Engine flags it (already in spreadsheet) and explains that lenders normally extend tenure or raise EMI. |

### 5.3 Customer data privacy

| Risk | Mitigation |
|---|---|
| Loan data is sensitive personal financial data; India's **Digital Personal Data Protection Act 2023** and its 2025 Rules apply (obligations phasing in; confirm with counsel) | Release 1.0: anonymous, in-browser, nothing stored (R-01 to R-03), so no customer loan data reaches our servers. If storage is ever approved (F-02): consent, India-region hosting, deletion on request. |
| Bank statements (1.2) contain account numbers, names, addresses | Prefer manual/CSV entry; parse uploads in the browser where possible; do not keep original files by default; if stored, encrypt, auto-delete after a short retention period. |
| Leakage through analytics or error reports | Any analytics or error monitoring (pending approval) must never receive loan figures; automated test checks outgoing requests. |
| One customer seeing another's data | Not possible in Release 1.0 (nothing stored). If accounts are approved: Row Level Security and cross-account tests. |

### 5.4 Bank schedule reconciliation

| Risk | Mitigation |
|---|---|
| Banks use daily interest (actual/365), actual payment dates, pre-EMI interest, fees and bundled insurance; the model will differ | Show both values and the difference, never auto-adjust (PRD FR-07); a reconciliation module tests candidate explanations (daily vs monthly interest, a missing rate change, a payment date shift, an unrecorded prepayment) and reports confirmed, probable and unresolved causes. |
| Varied, inconsistent bank schedule formats | 1.2 starts with manual entry and a standard CSV/Excel template; automated import of specific bank formats later (PRD "Could Have"). |
| Over-confident explanations harming trust | Confidence levels on every explanation; "unresolved" is an acceptable, displayed outcome. |

### 5.5 Other risks

- **Regulatory exposure:** balance-transfer "process assistance" for a fee (PRD §7 Stage 5) may resemble a loan intermediary or DSA activity under RBI rules. Needs legal review before it is built. The product must also stay clearly educational, not advisory.
- **Scope creep:** strict release gates (see ROADMAP.md).
- **Beginner maintainability:** small number of tools, strong types, tests as documentation, AI-assisted reviews.

---

## 6. Decisions and how reversible they are

| Decision | Reversibility | Notes |
|---|---|---|
| Engine as separate, pure TypeScript package with decimal maths | **Hard to reverse later** | Approved (B-01). |
| Integer paise + two-part labels | **Hard to reverse later** | Approved by B-06 and S-01; every module depends on them. |
| TypeScript end to end | Hard | Approved (B-01). |
| Next.js / Vercel | Moderate to easy | Approved (B-01). Engine is framework-independent. |
| Anonymous in-browser mode for 1.0 | Approved (R-01 to R-03) | Accounts could be added later only with approval. |
| Analytics / monitoring vendors | Easy | Pending (L-07). |

---

## 7. What this architecture deliberately does not do yet

- No microservices, queues or separate backend service.
- No native mobile apps (responsive web first).
- No automated bank statement PDF parsing (1.2+, and only after privacy design).
- No lender-specific historical rate research (PRD "Could Have"); only the bundled public benchmark table (A-05).
- No database, login or stored customer data in Release 1.0.
- No multi-loan modules until home loan Release 1.3 is stable.

---

## 8. Changes made after the product owner's approval (22 Nov 2026)

| Area | Before | After | Reason |
|---|---|---|---|
| Number precision | Integer paise, interest rounded to the paisa | Briefly full precision (original A-02), then back to paisa rounding when A-02 was amended | A-02, B-06 |
| Figure labels | Four kinds | Kind + source (six categories) | S-01 |
| Rate changes | From the EMI due on/after the effective date | From the first full period starting on/after the effective date | A-03 |
| Unknown past rates | Held at the starting rate, labelled Estimated | Benchmark by loan type + spread, labelled Illustrative; carry-forward labelled Estimated | A-05, B-03 |
| Bank figures | Single "as of" date | Each figure dated and sourced; difference kept and shown | A-06, S-03, S-04 |
| Final EMI | 1% threshold | Exact remaining amount due, absorbed into the final EMI | A-07, B-04 |
| Database and login | Proposed for Phase 3 | Deferred; not in Release 1.0 or the committed roadmap; no infrastructure built ahead of need | R-01 to R-03, B-01 |
| Spreadsheet | v1 as validation oracle | v1 not an approved reference; v2 built to approved rules, generated from the repository, and validated before it becomes the reference | D-02 to D-04, S-06 |
| Rate-change period, dates | — | EMI date to EMI date; disbursement one month before EMI 1; month-end EMI dates | B-02, B-05 |

The full list, with each conflict and required change, is in PRODUCT_DECISIONS.md section 10.
