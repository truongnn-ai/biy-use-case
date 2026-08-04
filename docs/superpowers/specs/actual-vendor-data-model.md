# Data Model — VendorConnect AI Prototype (Minimal)

## 3. Dataverse tables

### 3.1 `vca_vendor`

One row per vendor. 16 columns.


| Column                      | Type                                      | Notes                                                                                                    |
| --------------------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Vendor Name                 | Single line of text (required)            | Primary name column                                                                                      |
| Legal Name                  | Single line of text                       | "Legal status" — values still TBD                                                                        |
| Website Domain              | Single line of text                       | **Cross-validation match key** (§1.2)                                                                    |
| Business Domains            | Choice (local choice, single-select)      | Sector; also a vendor-list column                                                                        |
| Capabilities                | Choice (local choice, single-select)      | Search quality + comparison; folded in from the deferred Capability table                                |
| Industry                    | Single line of text                       | Single line of text                                                                                      |
| Country                     | Single line of text                       | Single line of text                                                                                      |
| HQ Location                 | Single line of text                       |                                                                                                          |
| Regional Operating Capacity | Choice (local choice, single-select)      |                                                                                                          |
| Headcount                   | Whole number                              |                                                                                                          |
| Vendor Status               | Choice: Potential / Registered / Existing | Drives the "Registered" tag                                                                              |
| Has Active Contract         | Yes/No                                    | Drives the "Active Contract" tag                                                                         |
| Source                      | Single line of text                       | Drives Existing/New Vendor tagging                                                                       |
| Overview                    | Single line of text (Rick text)           | Profile Overview tab; feeds the search embedding                                                         |
| AI Extracted                | Yes/No                                    | Set on promotion from an external find. Drives the "unverified — model-extracted" badge on Vendor Detail |
| Source Citations            | Single line of text                       | JSON array of citation URLs, copied from the search result on promotion                                  |




### 3.2 `vca_certification`

Row 6. 7 columns.


| Column             | Type                           | Notes                               |
| ------------------ | ------------------------------ | ----------------------------------- |
| Certification Name | Single line of text (required) | e.g. "ISO 27001"                    |
| Issuer             | Single line of text            |                                     |
| Date Earned        | Date only                      |                                     |
| Expiry Date        | Date only                      |                                     |
| Reference Number   | Single line of text            |                                     |
| Document           | File                           | Stored in Dataverse, not SharePoint |
| Vendor             | Lookup → Vendor (required)     | Parent                              |




### 3.3 `vca_engagement`

Row 7 and the Past Experience tab. 8 columns.


| Column                | Type                           | Notes                                                                                                                           |
| --------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| Delivery Project Name | Single line of text (required) | Named "Delivery" to distinguish it from `vca_project` (a *sourcing* project). This is the vendor's past delivery with BrandName |
| Business Unit         | Single line of text            |                                                                                                                                 |
| Outcome Summary       | Multiple lines of text         | 1–2 sentences                                                                                                                   |
| Start Date            | Date only                      |                                                                                                                                 |
| End Date              | Date only                      | Blank = ongoing                                                                                                                 |
| Headcount             | Whole number                   |                                                                                                                                 |
| Is Case Study         | Yes/No                         | "Case Studies" and "Engagement with BrandName" share one tab; a flag covers both without a second table                         |
| Vendor                | Lookup → Vendor (required)     | Parent                                                                                                                          |




### 3.4 `vca_vendorcontact`

Row 8, exactly its five fields. 6 columns.


| Column       | Type                           | Notes                                                            |
| ------------ | ------------------------------ | ---------------------------------------------------------------- |
| Contact Name | Single line of text (required) |                                                                  |
| Pronoun      | Single line of text            | **Free text, not a choice set** — do not constrain to a picklist |
| Email        | Single line of text            |                                                                  |
| Phone Number | Single line of text            |                                                                  |
| Title        | Single line of text            |                                                                  |
| Vendor       | Lookup → Vendor (required)     | Parent                                                           |




### 3.5 `vca_lifecycletask`

Both checklists in one table. 10 columns.


| Column       | Type                                                                                      | Notes                                            |
| ------------ | ----------------------------------------------------------------------------------------- | ------------------------------------------------ |
| Task Title   | Single line of text (required)                                                            |                                                  |
| Stage        | Choice: Onboarding / Offboarding (required)                                               | The two dashboards are one view filtered on this |
| Description  | Multiple lines of text                                                                    | Verbatim from the brief's checklists             |
| Vendor       | Lookup → Vendor (required)                                                                |                                                  |
| Status       | Choice: Not Started / In Progress / Complete / N/A                                        |                                                  |
| Focal Role   | Choice: VM / Vendor / Contract Owner / Risk Team / MyAccess / Finance / CSPC Buyer / User | Replaces a Team Member lookup                    |
| Due Date     | Date only                                                                                 |                                                  |
| Completed On | Date and Time                                                                             | Audit trail                                      |
| Sequence     | Whole number                                                                              | Display order                                    |
| Notes        | Multiple lines of text                                                                    |                                                  |


One table rather than two, deliberately: the two dashboards are the same view
filtered on Stage, so a single instantiation flow serves both. That matters
precisely *because* the flows are stretch work — if only one flow gets built, it
covers both stages.

**Seed by hand.** Since the instantiation flows may not get built, pre-create the
demo vendors' rows: one onboarding set (7 tasks from the brief, mixed statuses so
the progress bar reads part-complete) and one offboarding set (9 tasks). The
screens then read real Dataverse data and the audit-trail claim holds regardless.
If the flows land on day 3 they simply replace hand-seeding for new vendors.

### 3.6 `vca_shortlistitem`

Row 3's button. Grouped by project — no named-shortlist parent table. 5 columns.


| Column   | Type                            | Notes                                                      |
| -------- | ------------------------------- | ---------------------------------------------------------- |
| Vendor   | Lookup → Vendor (required)      |                                                            |
| Project  | Lookup → Project (**optional**) | Null = unassigned. The grouping key for the shortlist page |
| Added On | Date and Time                   |                                                            |
| Added By | Single line of text             | Audit only — no longer the grouping key                    |
| Note     | Multiple lines of text          |                                                            |


**Set the Project → Shortlist Item relationship to** `Remove Link` **on delete, not**
`Cascade`**.** Deleting a project should return its items to the unassigned bucket,
not silently destroy shortlist work. This is only safe *because* the lookup is
optional — anyone tightening it to required must revisit the cascade behaviour at
the same time.

**Duplicate prevention is app-side.** An alternate key on (Project, Vendor) will
not work, because Dataverse alternate keys do not tolerate a nullable column and
Project is nullable. Before insert, check for an existing row with the same
Vendor *and* the same Project, treating null-Project as its own bucket rather
than as a wildcard — the same vendor legitimately appears in two different
projects.