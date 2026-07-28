# Sample data — VendorConnect AI prototype

Dummy data for the demo, matching the schema in
`docs/superpowers/specs/2026-07-27-vendorconnect-ai-data-model.md` §3.
Headers are the Dataverse **display names** from the spec, so they map 1:1 in the
import wizard. All data is fictional.

## Load order

Lookups are expressed as **display-name text**, not GUIDs, so parents must exist
first:

1. `vca_vendor.csv` (20 rows)
2. `vca_project.csv` (4 rows)
3. `vca_certification.csv` (61 rows) — `Vendor` → Vendor Name
4. `vca_engagement.csv` (32 rows) — `Vendor` → Vendor Name
5. `vca_vendorcontact.csv` (41 rows) — `Vendor` → Vendor Name
6. `vca_lifecycletask.csv` (39 rows) — `Vendor` → Vendor Name
7. `vca_shortlistitem.csv` (10 rows) — `Vendor` → Vendor Name, `Project` → Project Name

`vca_searchlog` / `vca_searchresult` are not seeded — they are written live by
the search flow.

## Conventions

- Dates: `YYYY-MM-DD`. Date-and-time: ISO 8601 UTC (`2026-07-16T08:50:00Z`).
- Empty cell = null. Blank `End Date` on an engagement means ongoing; blank
  `Project` on a shortlist item means unassigned.
- "BrandName" is retained as the client placeholder, per the spec.
- Reference "today" for the dataset is **2026-07-27**.

## Caveat — the Certification `Document` column

`Document` is a Dataverse **File** column; file content cannot be loaded from
CSV. The values are intended filenames only. Either drop the column at import
and attach a couple of placeholder PDFs by hand for the demo, or leave every
Certification's file empty and rely on the name in the row.

## What the data is shaped to demonstrate

| Beat | How the data supports it |
|---|---|
| Certification expiry | 3 expired certs (Meridian ISO 9001, Lionheart Cyber Essentials Plus, Bayanihan PCI DSS) and 1 expiring in 4 days (Bayanihan HIPAA, 2026-07-31) |
| Past Experience tab (both halves) | 19 BrandName engagements plus 13 rows with `Is Case Study = Yes`; 8 ongoing (blank End Date) |
| Contacts tab | Every vendor has 1–3 contacts; pronouns are free text and include `they/them` |
| Onboarding dashboard | 3 sets × 7 tasks — Hanseatic (3 of 7 complete), Hangang AI (1 of 7, plus one `N/A`), Silverline Cyber (7 of 7) |
| Offboarding dashboard | 2 sets × 9 tasks — Vertex Fintech (5 of 9 complete), Pacific Rim (1 of 9, plus one `N/A`) |
| Audit trail | Every `Complete` task carries a `Completed On`; no non-complete task does. Two tasks completed *after* their due date, so overdue rendering has something to show |
| Shortlist grouping (spec §3.9.2, verification 11) | 3 items under Document Digitisation Programme, 2 under Cloud Migration Phase 2, 2 under Cybersecurity Operations Uplift, 1 under the Closed project, 2 unassigned |
| Project Status variety | Active ×2, Draft ×1, Closed ×1 |
| Duplicate guard (verification 12) | No (Vendor, Project) pair repeats, so the guard starts from a clean state |

Focal Role values are limited to the spec's choice set (VM / Vendor / Contract
Owner / Risk Team / MyAccess / Finance / CSPC Buyer / User); Status to
Not Started / In Progress / Complete / N/A.

## Known gap, not fixed here

Verification 6 in the data-model spec expects two deliberate near-duplicate
vendors ("Acme Technologies Pte Ltd" / "ACME Tech" sharing one website domain) to
exercise the cross-validation match key. `vca_vendor.csv` contains only
`Acme Technologies`, so that check has no data behind it yet — a second vendor
row is still needed.
