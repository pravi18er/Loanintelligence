# Product Requirements Document (PRD)
## Loan Intelligence Platform — Home Loan Intelligence

**Document version:** 0.2  
**Status:** Initial product definition, updated 22 Nov 2026 with product-owner approved Release 1.0 decisions  
**Product owner:** Founder / Client  
**Product management:** ChatGPT  
**Initial market:** India  
**Initial platform:** Website, with Google Sheets / Excel as a supported alternative (updated in v0.2)  
**Business model:** Freemium

---

## 1. Executive Summary

The Loan Intelligence Platform is a consumer-focused financial education and loan decision-support product designed to help Indian retail borrowers understand, evaluate and manage their loans.

The first product module will focus on home loans.

The product addresses a common problem: borrowers know their EMI amount but often do not understand how much of their repayment goes towards principal versus interest, why their outstanding balance remains high, or how much additional interest they may pay over the remaining loan tenure.

The platform will translate complex loan calculations into simple explanations, financial breakdowns, interactive dashboards and scenario simulations.

The product will not discourage borrowing or prescribe financial decisions. Its purpose is to provide transparency and enable informed choices.

## 2. Product Vision

Help every Indian borrower understand their loan and make informed financial decisions with confidence.

**Product philosophy:** Financial awareness, not financial fear.

## 3. Problem Statement

Indian retail borrowers frequently face an information and understanding gap when managing their loans.

They may receive repayment schedules and loan statements from banks, but these documents often present information in formats that are difficult for ordinary customers to interpret.

Key problems include:

1. Borrowers do not understand the principal and interest components of their EMIs.
2. They are surprised by how little principal has been repaid despite years of EMI payments.
3. They do not understand why their outstanding loan remains high.
4. They lack visibility into their projected future interest payments.
5. They cannot easily simulate multiple interest-rate changes across their loan tenure.
6. They lack a simple way to compare their bank's actual repayment information with modelled calculations.
7. They find it difficult to evaluate prepayments, top-up loans, balance transfers and early closure.

## 4. Product Goals

### Primary goal

Enable borrowers to make informed financial decisions by understanding their complete loan position.

### Supporting goals

- Explain historical loan repayment.
- Show current outstanding principal.
- Project future interest and repayment obligations.
- Explain how changing interest rates affect loan outcomes.
- Enable repayment and borrowing scenario comparisons.
- Identify discrepancies between modelled and bank-reported information.
- Make complex financial information accessible through simple explanations and visualisations.

### Non-goals

The initial product will not:

- Discourage customers from taking loans.
- Automatically recommend prepayment.
- Guarantee interest savings.
- Act as a lender or loan provider.
- Provide legal advice.
- Provide regulated financial or investment advice.
- Initiate loan transfers or negotiate with banks.
- Replace official lender statements or foreclosure quotations.

## 5. Target Audience

### Primary persona: Existing Home Loan Borrower

An Indian retail borrower who:

- Has an active home loan.
- Has been paying EMIs for some time.
- Knows the EMI but may not understand the principal-interest allocation.
- Wants to understand the remaining financial commitment.
- Wants to explore available repayment options.
- May not have detailed historical interest-rate information readily available.

### Secondary personas

**Prospective borrower:** Someone evaluating a home loan before borrowing.

**Decision-stage borrower:** Someone considering prepayment, balance transfer, top-up borrowing or early closure.

## 6. Product Scope

### 6.1 Initial Module — Home Loan Intelligence

The first module will support:

- New home loans.
- Existing home loans.
- Fixed and floating interest-rate scenarios.
- Standard monthly amortising repayment structures.
- Historical repayment analysis.
- Future repayment projections.

### 6.2 Future Modules

| Module | Priority |
|---|---|
| Personal Loan Intelligence | Future release |
| Vehicle Loan Intelligence | Future release |
| Gold Loan Intelligence | Future release |
| Credit Card Intelligence | Separate product track |

The platform should be designed with reusable components so future loan modules do not require rebuilding the entire system.

Credit cards will require a separate calculation and customer experience because revolving credit differs from standard amortising loans.

## 7. Customer Journey

### Stage 1 — Discovery and onboarding

Customer enters the platform and selects Home Loan Intelligence.

Customer provides basic loan information, including:

- Loan amount.
- Loan commencement date.
- Original tenure.
- Current EMI.
- Current interest rate.
- Current outstanding principal, if available.
- Number of EMIs paid or remaining tenure.
- Lender information.

### Stage 2 — Quick Loan Check

The system generates an initial Loan Reality Report using available information.

Results must clearly indicate whether figures are actual, modelled or estimated.

### Stage 3 — Detailed Loan Analysis

Customer may optionally upload or enter bank repayment schedule information.

The product analyses:

- Actual principal repayments.
- Actual interest payments.
- Historical interest-rate changes.
- Payment dates.
- Outstanding balance.
- Differences between bank records and modelled calculations.

### Stage 4 — Decision Support

Customer explores scenarios involving:

- Additional prepayments.
- Interest-rate changes.
- EMI adjustments.
- Tenure changes.
- Top-up loans.
- Balance transfers.
- Early loan closure.

### Stage 5 — Customer Assistance

Customers may contact the platform through email for clarification.

Initial balance-transfer process assistance may be offered for a nominal fee, subject to applicable regulatory requirements and clearly defined service boundaries.

## 8. Functional Requirements

### FR-01: Loan Profile Management

The system shall allow customers to enter and maintain their home-loan details.

The system shall distinguish between new borrowers and existing borrowers.

Existing borrowers must be able to use their current outstanding principal, EMI and remaining tenure rather than incorrectly treating the loan as a new loan.

### FR-02: Loan Reality Check Dashboard

The system shall calculate and display:

1. Total EMI paid.
2. Principal repaid.
3. Interest paid.
4. Current outstanding principal.
5. Estimated loan closure date.

The dashboard shall display:

- Principal versus interest breakdown.
- Repayment progress.
- Outstanding balance progression.
- Historical repayment summary.
- Future repayment projection.

### FR-03: Future Interest Intelligence

The system shall estimate the total interest payable over the remaining loan tenure.

It shall explain:

- Why interest was collected in earlier repayment periods.
- Why the interest component may have been high initially.
- Why outstanding principal remains significant.
- How the principal-interest allocation changes over time.
- How interest-rate and repayment changes influence future interest.

The product shall distinguish projected interest from interest already paid.

### FR-04: Dynamic Interest Rate Simulator

The system shall support multiple interest rates across the loan tenure.

Customers shall be able to define:

- Interest rate.
- Effective date or instalment.
- Rate increase.
- Rate reduction.
- Repayment adjustment behaviour.

The system shall support:

1. EMI remains constant and tenure changes.
2. Tenure remains constant and EMI changes.
3. Custom lender repayment behaviour.

The simulator shall show the impact on:

- EMI.
- Outstanding principal.
- Total interest.
- Loan closure date.

Historical rates and future hypothetical assumptions must be separately identified.

### FR-05: Historical Interest-Rate Reconstruction

The system shall allow customers to provide historical interest rates.

Where customers do not know historical rates, the future product should support research using publicly available lender and benchmark information.

The product shall distinguish:

- Customer-provided actual rates.
- Bank-documented rates.
- Publicly sourced reference rates.
- Illustrative assumptions.

Publicly available rates must never be presented as confirmed individual customer rates.

For the initial Google Sheets MVP, manual rate entry and illustrative assumptions will be prioritised.

*v0.2 update:* For Release 1.0, where actual historical rates are unavailable, publicly available historical benchmark information is used to give illustrative estimates, never represented as the customer's actual rate (decision A-05). The estimate uses the loan's own benchmark (repo rate, MCLR or Base Rate) plus an estimated spread; repo linkage is never assumed when the benchmark is unknown, and where no reliable benchmark exists the last known rate is carried forward and labelled Estimated (decision B-03).

### FR-06: Actual Bank Schedule Analysis

The system shall support entry or import of a bank repayment schedule.

It should analyse:

- Opening principal.
- Interest charged.
- Principal repaid.
- EMI paid.
- Additional prepayments.
- Closing principal.
- Historical interest rates.

The system should compare actual bank information against modelled calculations.

### FR-07: Bank Reconciliation

Where the bank-reported balance differs from the modelled balance, the system shall:

1. Display both values.
2. Calculate the difference.
3. Investigate possible causes.
4. Compare the available evidence.
5. Explain confirmed and probable reasons.
6. Identify unresolved discrepancies.

Possible causes include:

- Different historical interest rates.
- Payment-date differences.
- Missed or delayed EMIs.
- Additional payments.
- Fees and adjustments.
- Differences in calculation conventions.

The system shall not automatically modify modelled figures to match bank figures.

### FR-08: Prepayment Simulator

The system shall support:

- One-time prepayments.
- Monthly additional payments.
- Annual prepayments.
- Multiple irregular prepayments.

It shall compare:

- Reduce EMI.
- Reduce tenure.

The system shall display potential interest savings and estimated time savings.

Lender-specific recast rules and assumptions must be disclosed.

### FR-09: Preclosure Shock Test

The customer shall be able to select an intended loan closure date.

The system shall estimate:

- Outstanding principal.
- Accrued interest, where applicable.
- Applicable foreclosure charges entered by the customer.
- Other closure fees.
- Overdue amounts.
- Estimated closure amount.

The report must clarify that this is an estimate and not an official lender foreclosure quotation.

It must avoid double-counting EMIs, payments or accrued interest.

### FR-10: Top-up Loan Simulator

The system shall allow customers to evaluate additional borrowing against an existing home loan.

It shall show:

- Current outstanding principal.
- Additional loan amount.
- Combined borrowing.
- Revised EMI or tenure.
- Additional interest payable.
- Revised estimated closure date.

### FR-11: Balance Transfer Calculator

The system shall allow customers to compare an existing home loan against a proposed new lender offer.

Inputs shall include:

- Current outstanding principal.
- Current interest rate.
- Current EMI.
- Remaining tenure.
- Proposed new interest rate.
- Proposed EMI or tenure.
- Processing fees.
- Foreclosure and transfer-related costs.

Outputs shall include:

- Revised repayment schedule.
- Potential interest savings.
- Total transfer costs.
- Break-even point.
- Financial comparison.

The product shall explain the financial implications without automatically selecting a lender.

### FR-12: Interest Rate Comparison

The system shall allow comparison of multiple interest-rate scenarios.

It shall display:

- EMI differences.
- Total interest differences.
- Repayment tenure differences.
- Potential savings.

### FR-13: Customer Education

The system shall explain financial concepts using:

- Plain-English explanations.
- Tables.
- Interactive dashboards.
- Visual comparisons.
- Detailed calculation breakdowns.

Every important figure should have an accessible explanation of its origin, assumptions and data quality.

### FR-14: Validation and Error Handling

The system shall validate:

- Loan amount.
- Interest rate.
- Loan tenure.
- EMI.
- Outstanding principal.
- Payment dates.
- Prepayment amounts.
- Fee values.
- Loan closure conditions.

It shall identify invalid inputs, negative amortisation and inconsistencies.

### FR-15: Customer Support

The system shall provide an email-based clarification channel.

Optional paid initial process assistance may be introduced with clearly documented boundaries.

Professional referrals are reserved for future releases.

## 9. Non-Functional Requirements

### Accuracy

- Use validated financial calculation methods.
- Prevent negative outstanding balances.
- Handle zero-interest edge cases.
- Avoid double-counting payments and interest.
- Test multiple interest-rate scenarios.
- Reconcile modelled results against independently verified examples.

### Transparency

- Identify actual, estimated and illustrative values.
- Disclose calculation assumptions.
- Identify missing information.
- Show calculation details when requested.

### Usability

- Use simple English.
- Avoid unnecessary financial jargon.
- Provide intuitive visualisations.
- Minimise customer input requirements.
- Make reports understandable to non-financial users.

### Privacy and Security

- Protect customer loan information.
- Minimise personal data collection.
- Avoid exposing financial information.
- Establish appropriate document handling, retention and deletion policies before launch.

### Extensibility

- Support future loan modules.
- Separate reusable calculation components from loan-specific rules.
- Allow additional reporting and simulation capabilities.

## 10. Freemium Business Model

### Free Tier

Proposed capabilities:

- Loan profile.
- EMI breakdown.
- Principal and interest analysis.
- Outstanding principal.
- Repayment progress.
- Basic repayment schedule.
- Basic Loan Reality Report.

### Premium Tier

Proposed capabilities:

- Dynamic interest-rate simulation.
- Advanced prepayment analysis.
- Preclosure Shock Test.
- Balance transfer comparison.
- Top-up loan analysis.
- Historical reconstruction.
- Detailed downloadable reports.
- Multiple scenario comparisons.

Exact pricing, usage limits and payment model remain to be validated.

## 11. MVP Scope and Prioritisation

### Must Have — Initial MVP

- Loan profile.
- Existing borrower onboarding.
- EMI and amortisation engine.
- Loan Reality Check dashboard.
- Past repayment breakdown.
- Future interest projection.
- Simple-language explanations.
- Basic interest-rate change support.
- Input validation.
- Assumptions and disclosures.

### Should Have — Early Enhancement

- Historical interest-rate reconstruction.
- Actual bank repayment schedule input.
- Bank reconciliation.
- Prepayment simulator.
- Preclosure Shock Test.
- Top-up loan simulator.

### Could Have — Later Enhancement

- Advanced balance-transfer comparison.
- Automated bank schedule import.
- Historical lender rate research.
- Advanced downloadable reports.
- Customer support workflow enhancements.

### Future Platform Expansion

- Personal loans.
- Vehicle loans.
- Gold loans.
- Credit-card intelligence as a separate product track.

## 12. Success Metrics

### Customer acquisition

- Number of new customers.
- Number of completed loan profiles.
- Onboarding completion rate.

### Customer engagement

- Percentage of users generating a Loan Reality Report.
- Percentage exploring detailed repayment information.
- Percentage using scenario simulators.

### Customer value

- Report usefulness feedback.
- Customer understanding and confidence improvement.
- Percentage of users who recommend the product.
- Customer support satisfaction.

### Business performance

- Free-to-paid conversion rate.
- Revenue per paying customer.
- Customer acquisition cost.
- Refund and cancellation rate.

Targets will be defined after initial customer testing.

## 13. Key Risks and Dependencies

| Risk | Mitigation |
|---|---|
| Incomplete customer data | Transparent estimates and data-quality indicators |
| Incorrect historical rate assumptions | Source identification and explicit disclosures |
| Calculation errors | Independent testing and reconciliation |
| Complex customer experience | Progressive disclosure and plain language |
| Regulatory exposure | Compliance review and clear service boundaries |
| Customer data privacy | Data minimisation and secure handling |
| Overly ambitious MVP | Strict feature prioritisation |

## 14. Initial Technology Direction

*v0.2 update (22 Nov 2026), approved by the product owner:* **Website-first with spreadsheet support.** The website is the primary customer-facing product. Excel / Google Sheets remains a usable customer-facing alternative and, once the v2 workbook is built to the approved rules and validated, the calculation reference for validating the website. Both follow the same approved calculation rules; conflicting calculation logic is not allowed. Release 1.0 is anonymous, calculates in the browser, stores no customer loan information by default, is English only, and supports standard fully disbursed monthly home loans. See ARCHITECTURE.md and PRODUCT_DECISIONS.md.

*Original v0.1 text:* The initial MVP will use Google Sheets.

Proposed workbook architecture:

1. Welcome & Instructions
2. Loan Profile
3. Loan Reality Check
4. Repayment Engine
5. Actual Bank Schedule
6. Preclosure Shock Test
7. Prepayment Simulator
8. Interest Rate Comparison
9. Balance Transfer
10. Validation & Assumptions
11. Dynamic Interest Rate Simulator

The calculation engine and underlying data structure should be designed for future reuse beyond home loans.

## 15. Open Product Decisions

The following require further definition:

1. Exact customer input fields and onboarding flow.
2. Supported interest calculation conventions.
3. Historical rate data sources and research methodology.
4. Bank schedule upload format and supported file types.
5. Treatment of EMI changes and interest-rate resets.
6. Exact free versus premium feature boundaries.
7. Pricing and monetisation.
8. Privacy, security and regulatory review.
9. Initial customer testing and acceptance criteria.

*v0.2 update:* Item 2 is resolved by approved rules A-01 to A-08, and item 5 by A-03 and A-04 (PRODUCT_DECISIONS.md section 3). Item 8 is partly addressed by the Release 1.0 constraints (no data stored by default); a formal privacy and regulatory review remains open. The remaining items are tracked in PRODUCT_DECISIONS.md section 8.

## 15A. Approved Release 1.0 Calculation Rules (v0.2)

| ID | Area | Approved decision |
|---|---|---|
| A-01 | Interest calculation | Monthly reducing-balance interest: opening principal × annual interest rate / 1200. |
| A-02 | Rounding | Amended 22 Nov 2026: round every monetary amount (EMI, monthly interest, principal, balance) to the paisa. Round customer-facing displayed amounts to the nearest rupee. (Originally: retain full precision internally.) |
| A-03 | Interest-rate changes | Apply the revised rate from the first full monthly calculation period beginning on or after its effective date. No mid-month pro-rata calculation in Release 1.0. |
| A-04 | EMI and tenure adjustment | Keep EMI and extend tenure (default), keep tenure and recalculate EMI, or enter the bank-revised EMI. |
| A-05 | Unknown historical rates | Publicly available historical benchmark information gives illustrative estimates when actual rates are unavailable. Never represented as the customer's actual rate. |
| A-06 | Bank-provided figures | Valid, dated bank-reported figures are the starting point for future projections. Differences from modelled figures are preserved and displayed. Never silently force reconciliation. |
| A-07 | Final EMI | The final EMI is the exact remaining amount due, including applicable interest. No arbitrary 1% threshold or unnecessary extra EMI. |
| A-08 | Partial disbursements | Only fully disbursed monthly home loans. Partial disbursements and pre-EMI are excluded. |

Implementation safeguards S-01 to S-07 are recorded in PRODUCT_DECISIONS.md section 4.

## 16. Product Release Strategy

**Release 1.0 — Home Loan Reality Check**

Deliver a usable product that explains past repayment, current outstanding principal and projected future interest.

**Release 1.1 — Loan Decision Intelligence**

Introduce dynamic interest-rate scenarios, prepayment and top-up analysis.

**Release 1.2 — Actual Loan Intelligence**

Introduce bank schedule analysis, historical reconstruction and reconciliation.

**Release 1.3 — Advanced Loan Decisions**

Introduce balance-transfer comparison, advanced closure analysis and detailed reports.

**Future — Multi-loan Platform**

Expand to personal, vehicle and gold loans. Develop credit-card intelligence separately.

---

**Product success definition**

A customer should be able to enter their loan information, understand where their money has gone, understand what they still owe, see how much interest they may pay in the future, and explore their choices without feeling pressured into any particular financial decision.
