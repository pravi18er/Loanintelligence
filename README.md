# Loan Intelligence Platform

Helping every Indian borrower understand their loan and make informed financial decisions with confidence.

**Financial awareness, not financial fear.** The platform explains loans; it does not tell anyone what to do.

The first module is **Home Loan Intelligence**: where your EMIs have gone, what you still owe, how much interest may lie ahead, and how rate changes, prepayments, top-ups or a balance transfer would change that.

> **Status (22 November 2026):** Planning. The product owner has approved the Release 1.0 baseline: website-first with spreadsheet support, eight calculation rules, Release 1.0 constraints and implementation safeguards (see [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md)). The core technology stack and phase plan are approved, with database and login infrastructure deferred. Phase 0 (foundations) is under way: repository skeleton, CI and the Python calculation reference with golden scenarios. No customer-facing code yet.

## Documents

| Document | What it covers |
|---|---|
| [PRD.md](PRD.md) | Product requirements (v0.2): scope, features, releases, approved Release 1.0 calculation rules. |
| [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) | Decision register: approved decisions, pending decisions, deferred features, and changes caused by the approval. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Recommended stack and architecture, risks and trade-offs. |
| [ROADMAP.md](ROADMAP.md) | Phased plan from foundations to Release 1.3, with release gates. |
| [TEST_STRATEGY.md](TEST_STRATEGY.md) | How financial accuracy, transparency and privacy are tested. |

## Current assets

- **Release 1.0 Google Sheets workbook v1** (`Home_Loan_Reality_Check_v1.xlsx`, kept in the project files): a working Home Loan Reality Check, verified against known EMIs. It predates the approved rules and differs on five of them (A-02, A-03, A-05, A-06, A-07), so it is **not** the approved calculation reference. A v2 workbook built to the approved rules will replace it as the customer spreadsheet, and becomes the calculation reference once validated.

## Release 1.0 at a glance (approved)

- Website is the main product; the spreadsheet remains an alternative and must follow the same rules.
- Anonymous, calculations in the browser, no loan data stored by default, English only.
- Standard, fully disbursed monthly home loans.
- Every figure says what it is (actual, modelled, estimated, illustrative) and where it came from (bank, customer, public benchmark, calculated).

## Technology stack (approved)

TypeScript · standalone calculation engine using decimal.js · Next.js · Tailwind CSS + shadcn/ui · Recharts · Zod · Vitest, fast-check, Playwright · pnpm workspaces monorepo · Vercel.

Deferred: Supabase, PostgreSQL, authentication and any database infrastructure. Release 1.0 needs none of them. Every amount is rounded to the paisa and held as integer paise (B-06). Pending: payments, monitoring and analytics.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the reasoning and alternatives.

## Planned repository layout

```
apps/web/               Next.js website (added in Phase 2)
packages/loan-engine/   Pure TypeScript calculation engine (skeleton now; rules in Phase 1)
reference/              Golden test scenarios, Python reference, public benchmark table
spreadsheet/            Generator for the v2 customer workbook
```

## Development

Requires Node 22+, pnpm 10 and Python 3.10+.

```bash
pnpm install
pnpm check     # formatting, lint, type check, engine tests, Python reference tests, scenario check
```

## Important

This product is educational. It is not financial, legal or investment advice, not a lender, and not a substitute for official lender statements or foreclosure quotations.
