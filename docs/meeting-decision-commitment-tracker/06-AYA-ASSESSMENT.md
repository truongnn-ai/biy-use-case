# AYA Assessment — Meeting Decision & Commitment Tracker

Filled-in "Assess Your App" scorecard for the **demo scope** (two apps — model-driven +
canvas — over one Dataverse). All dimensions avoid the out-of-scope (⚠️) values, so the
solution qualifies as **Team / Single department** — in-scope. Having two apps does not
change any score: same data, same users, same classification.

| # | Dimension | Selected score | Justification |
|---|-----------|:---:|---------------|
| 1 | Users | **3 — Internal: Team / Single department** | Used by one team/department; internal only, not internet-facing. |
| 2 | Data Confidentiality & Classification | **2 — Internal** | Meeting notes, decisions, commitments. The **Team Member** table holds **fictional** people (name + role only — no email/ID/PII) and is **not** linked to real M365 users; attendees are free-text. All sample data is made up. No PII, financial, or confidential data. |
| 3 | Integration | **1 — No integration with Client systems** | Dataverse only. The optional Outlook reminder uses Office 365 sources, which the matrix still classes under score 1. No Client systems. |
| 4 | Business Criticality | **2 — Useful but workaround exists** | Improves follow-through; teams can still fall back to notes/email. Not critical to operations. |
| 5 | Complexity & Scale | **1 — Simple, under 2000 records** | 3 tables, straightforward logic; demo < 200 records. |
| 6 | Expected Growth | **1 — Static, no growth planned** (demo) | Demo is static. *Departmental growth (score 3) is still in-scope* if the client later adopts it within one department. |
| 7 | Regulatory & Compliance Exposure | **1 — General data protection only** | No regulated data or reporting. |
| 8 | Service Availability | **1 — Insignificant** | Non-critical; any downtime keeps business-as-usual. |
| 9 | AI and Automation Use | **1 — No AI used** | Demo phase uses no AI. (A Microsoft-provided note-summarizer would be score 2 and is deferred to a later phase — see 03-BUILD-GUIDE §Deferred.) |

## Result

- **No ⚠️ out-of-scope dimensions selected.**
- **Category: Team / Single department** — appropriate for the demo.
- Highest scores are Users (3) and Data (2); everything else is 1–2.

## Guardrails to stay in-scope during build

- **Do not** link the Team Member table to real Microsoft 365 users or add email/ID/HR fields — that pushes Data to PII (score 5, out of scope). Keep Team Member records **fictional** (name + role) for the demo (see PRD OQ-1).
- **Do not** connect to Client systems or external SQL (would raise Integration).
- **Do not** market it as enterprise-wide or multi-department in the demo (would raise Users to ⚠️4 and Growth to ⚠️5).
- Keep the optional AI strictly **Microsoft-provided, productivity-only, human-confirmed** (score 2 max).

## Re-assess before Phase 2+

The roadmap items (Outlook/Teams sync, role-based multi-department views, approvals,
analytics) would likely raise **Users, Integration, and Growth**. Re-run the AYA form
before building any of them — several could move the app to Enterprise (out-of-scope).
