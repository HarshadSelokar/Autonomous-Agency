# Phase 24 — Product, Customer & Go-To-Market Operations

## Overview
Phase 24 introduces comprehensive Product Management, CRM & Sales Pipeline, Customer Success & Support, Marketing Campaign Execution, and Go-To-Market (GTM) Operations into the Autonomous AI Organization Platform.

This phase enforces governed commercial boundaries, strict customer tenant isolation, and seamless automated integration with Phase 23 Autonomous Business Operations (billing, invoicing, payments, and revenue recognition).

---

## Key Domain Boundaries & Non-Negotiable Invariants

1. **Entity Separation Principle**:
   - `LEAD != PROSPECT != CUSTOMER != CONTRACT != ORDER != PAYMENT != REVENUE`
   - A Lead entering the pipeline is not a Prospect, and an Opportunity is not guaranteed Revenue until Closed-Won and recognized by Phase 23 Business Operations.

2. **Epistemological & Security Safety**:
   - `CUSTOMER FEEDBACK != FACT AUTOMATICALLY`
   - `CUSTOMER MESSAGE != AUTHORIZED INSTRUCTION`
   - Customer feedback undergoes validation before synthesis into product requirements. Customer messages cannot issue system-level execution commands.

3. **Commercial Governance & Discount Control**:
   - `RECOMMENDATION != AUTHORIZATION != EXECUTION`
   - Any commercial proposal with a discount exceeding **15.0%** triggers an automatic `APPROVAL_REQUIRED` status and strictly requires a **Human Governance Approval ID** to send or execute.
   - Price discounts outside [0.0%, 100.0%] raise `PricingPolicyViolationError`.

4. **Multi-Tenant Customer Data Isolation**:
   - Requests cross-referencing customer data across tenant boundaries must pass `verify_customer_access(requestor_customer_id, target_customer_id)`.
   - Access attempts violating tenant isolation raise `CustomerDataIsolationError`.

---

## Architectural Components & Flow

```
                                  +-----------------------+
                                  |  Product Management   |
                                  | (Catalog, Releases,   |
                                  | Feedback, Roadmap)    |
                                  +-----------+-----------+
                                              |
                                              v
+-----------------------+         +-----------+-----------+         +-----------------------+
|  Marketing Campaigns  | ------> |      CRM & Sales      | ------> |   Human Governance    |
| (Email, Ads, Events)  |         | (Leads, Opportunities)|         | (Discount >15% Check) |
+-----------------------+         +-----------+-----------+         +-----------+-----------+
                                              |                                 |
                                              +---------------+-----------------+
                                                              |
                                                              v (Deal Closed-Won)
                                                  +-----------+-----------+
                                                  | Phase 23 Business Ops |
                                                  | Invoices, Payments,   |
                                                  | Revenue Recognition   |
                                                  +-----------+-----------+
                                                              |
                                                              v
                                                  +-----------+-----------+
                                                  |  Customer Success &   |
                                                  |  Support Ticketing    |
                                                  +-----------------------+
```

---

## Operational Loop & Workflows

### 1. Product Catalog & Versioning
- Define product offerings, pricing tiers (FREE, PRO, ENTERPRISE), base prices, and feature matrices.
- Release versioning (`ProductVersion`) tracks software milestones.

### 2. Lead Ingestion & Qualification
- Ingest leads from inbound web, events, or outbound campaigns.
- Score leads based on engagement; qualified leads advance to sales opportunities.

### 3. Sales Pipeline & Governance Proposals
- Advance opportunities through stages: `IDENTIFIED` -> `QUALIFIED` -> `DISCOVERY` -> `PROPOSAL` -> `NEGOTIATION` -> `WON`.
- Generate commercial proposals with base pricing and discount percentages.
- Automatic governance check blocks proposals with discounts >15% unless an authorized `governance_approval_id` is supplied.

### 4. Deal Closed-Won Execution
- When an Opportunity reaches `WON`, `GTMOperationsService.execute_deal_won_and_onboard()` executes:
  1. Activates Customer account and records contract ARR/ACV.
  2. Triggers Phase 23 `BusinessOperationsService` to issue an Invoice, record Payment, and recognize Revenue.
  3. Initiates an automated Customer Onboarding Plan.

### 5. Customer Success & Support Ticketing
- Tracks customer health snapshots, product usage, and NPS/CSAT scores.
- Manages support cases with priority levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- Escalates unresolved technical issues directly to Task Engine engineering tasks (`escalate_support_case_to_task`).

### 6. Marketing & ROI Analytics
- Launch email, digital, and webinar campaigns with allocated budgets.
- Track conversions, leads generated, revenue generated, and ROI percentages.

---

## API Endpoints Reference

All endpoints are registered under `/api/v1/gtm/`:

- **Products & Requirements**:
  - `POST /api/v1/gtm/products` - Create product
  - `GET /api/v1/gtm/products` - List products
  - `POST /api/v1/gtm/feedback` - Record customer feedback
  - `POST /api/v1/gtm/requirements` - Synthesize feedback to requirement

- **CRM & Sales**:
  - `POST /api/v1/gtm/leads` - Ingest sales lead
  - `POST /api/v1/gtm/opportunities` - Create sales opportunity
  - `POST /api/v1/gtm/proposals` - Create commercial proposal
  - `POST /api/v1/gtm/proposals/{proposal_id}/send` - Approve & send proposal (checks >15% discount governance)

- **Customer Success & Support**:
  - `POST /api/v1/gtm/customers` - Create customer
  - `POST /api/v1/gtm/support-cases` - Create support case
  - `POST /api/v1/gtm/support-cases/{case_id}/resolve` - Resolve support case

- **Marketing Campaigns & Analytics**:
  - `POST /api/v1/gtm/campaigns` - Create marketing campaign
  - `POST /api/v1/gtm/campaigns/{campaign_id}/launch` - Launch campaign
  - `GET /api/v1/gtm/metrics` - Fetch company executive GTM summary metrics

---

## Frontend Integration

The Pixel Office frontend includes the **GTM Operations Dashboard** (`GTMDashboard.tsx`):
- Navigation icon in the primary sidebar.
- Realtime metrics tiles: Active Products, Total Leads, Pipeline Value, Active Customers, Contract ARR, Avg CSAT, Open Tickets.
- Interactive tabbed interface:
  - **CRM Pipeline**: Visual stage-by-stage opportunity tracker.
  - **Product Catalog**: Active products, base prices, and release versions.
  - **Customer Success**: Customer health scores, onboarding progress, and support tickets.
  - **Marketing Campaigns**: Active campaigns, budget tracking, and ROI.
