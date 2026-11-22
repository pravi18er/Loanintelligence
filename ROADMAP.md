# Roadmap — Loan Intelligence Platform

**Status:** Updated 22 November 2026 for the product owner's approved Release 1.0 baseline (PRODUCT_DECISIONS.md). Stack approved (B-01). Phase plan **approved** 22 Nov 2026. Phase 0 in progress.
**Principle:** Financial accuracy and customer trust before visual features. Each phase ends with a release gate; the next phase does not start until the gate passes.

Release names follow PRD §16. Phases are the engineering steps that deliver them. Decision IDs (A-, B-, D-, F-, L-, R-, S-) refer to PRODUCT_DECISIONS.md.

---

## Phase 0 — Foundations

Goal: a safe place to build, with the accuracy benchmark in place before any feature.

- Commit the documentation to the repository.
- B-01 to B-06 decided on 22 Nov 2026. `main` branch created from the documentation commit.
- Repository skeleton (`apps/web`, `packages/loan-engine`, `reference/`, `spreadsheet/`), TypeScript, lint, formatting.
- Continuous integration on every pull request.
- Independent Python reference implementing A-01 to A-08, and the first golden scenarios (TEST_STRATEGY.md section 2).

**Gate:** CI green. (B-07 and B-08 must be decided before the Phase 1 gate.)

## Phase 1 — Calculation engine and spreadsheet v2 (no website yet)

Goal: one set of approved rules, implemented twice, proven identical.

- Engine: decimal.js with every amount rounded to the paisa (A-02 as amended), monthly interest (A-01), rate changes by period (A-03), three EMI/tenure options (A-04), dated and sourced bank figures as projection starting points with differences kept (A-06), exact final EMI (A-07), fully disbursed loans only (A-08).
- Two-part labels on every figure (S-01) and validation, including EMI not covering interest (S-05).
- Bundled, versioned public benchmark table: repo rate, MCLR and Base Rate by loan type, plus estimated spread (A-05, B-03); carry-forward labelled Estimated where no reliable benchmark; lender coverage per B-07.
- **Spreadsheet v2** (built; matches all golden scenarios), generated from a script in the repository, implementing the same rules and using the same benchmark table (D-04, S-06). The v1 workbook is not an approved reference; v2 becomes the reference only after it is validated.
- Plain-English explanation text returned with results.

**Gate:** B-07 decided; every golden scenario agrees on every displayed rupee across engine, spreadsheet v2 and Python reference; property tests pass; product owner reviews explanation text.

## Phase 2 — Release 1.0 "Home Loan Reality Check" website

Goal: a customer can understand where their money went, what they still owe, and future interest.

Scope fixed by R-01 to R-06: anonymous, in-browser, nothing stored, English only, fully disbursed monthly home loans.

- Guided onboarding (new vs existing borrower); bank figures entered with date and source.
- Reality Check: total EMI paid, principal repaid, interest paid, outstanding, estimated closure date (FR-02).
- Future interest projection and explanations (FR-03).
- Basic interest-rate change history with the three A-04 options (PRD Must Have).
- Bank vs modelled difference shown, never adjusted (A-06).
- Charts, "How was this calculated?" panels, assumptions page, disclaimers.
- Mobile-first layout; accessibility target per L-05.

**Gate:** end-to-end tests pass, including a check that no loan data leaves the browser; launch items L-01 to L-06 decided; 10+ real borrowers (with consent) compare results with their bank statements and differences are explained; usability test with 5 non-financial users; product-owner sign-off.

## Phase 3 — Release 1.1 "Loan Decision Intelligence"

- Dynamic interest-rate simulator and scenario comparison (FR-04, FR-12).
- Prepayment simulator: one-time, monthly, annual, irregular; reduce EMI vs reduce tenure (FR-08).
- Top-up loan simulator (FR-10).
- Freemium boundary, pricing and payments (pending F-01).
- Spreadsheet updated in step for any calculation it supports (D-04).

**Gate:** golden scenarios extended to prepayments and top-ups across all implementations; F-01 decided.

## Phase 4 — Release 1.2 "Actual Loan Intelligence"

- Bank schedule entry and import (formats pending F-03) (FR-06).
- Reconciliation: show both, compute difference, test candidate causes, label confirmed / probable / unresolved (FR-07).
- Lender-specific historical rate reconstruction with source labels (FR-05).
- Daily or pro-rata interest, if approved (F-04).

**Gate:** reconciliation tested against real anonymised schedules from at least 3 lenders; no uploaded documents stored by default.

## Phase 5 — Release 1.3 "Advanced Loan Decisions"

- Balance transfer calculator with break-even (FR-11).
- Preclosure Shock Test (FR-09).
- Detailed downloadable reports.
- Customer support workflow (FR-15).

**Gate:** legal review of any paid assistance (F-05); report disclaimers reviewed.

## Future — Multi-loan platform

- Personal, vehicle and gold loan modules reusing the engine's generic core.
- Credit-card intelligence as a separate product track (R-06).

## Not scheduled (needs a product-owner decision first)

- Accounts and saved loans, and the database and authentication they would need (F-02). Previously proposed as Phase 3; removed because Release 1.0 is anonymous with nothing stored by default, and Supabase, PostgreSQL and authentication are deferred (B-01). No infrastructure is built ahead of need.
- Partial disbursements and pre-EMI (A-08).
- Languages other than English (R-04).

---

## Changes from the first draft of this roadmap

| Change | Reason |
|---|---|
| Spreadsheet v2 added to Phase 1 | D-04, S-06: both interfaces follow the same rules; v1 differs on five rules. |
| Public benchmark table moved into Phase 1 (was Release 1.2 research) | A-05 |
| "Accounts and saved loans" phase removed from the committed plan | R-01 to R-03, B-01 |
| Phases renumbered (Releases 1.1 to 1.3 are now Phases 3 to 5) | Follows from the above |
| Release order still follows PRD §16 where §11 differs | Pending F-06 |
