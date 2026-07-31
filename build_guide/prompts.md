# Copilot Prompts — VendorConnect AI Dataverse Tables

Copy-paste prompts for building the 9 Dataverse tables in
`docs/superpowers/specs/2026-07-27-vendorconnect-ai-data-model.md` using **Copilot
in Power Apps** (maker portal → *Tables* → *Describe the new table*).

**Run them in order.** Tables 2–9 all point at Vendor (or at Search Log / Project),
so the parent must exist before Copilot can wire up the lookup.

**Before you start**

1. Open [https://make.powerapps.com](https://make.powerapps.com), pick the target Dev environment.
2. Work with the `new_` **publisher prefix** — the default publisher's prefix, so
  the Default solution and a solution using that publisher both produce `new_`
   names. Just confirm the prefix reads `new` before you create the first table;
   Copilot takes it from whichever solution you are in.
3. Read §0 below and create the four shared global choices first.

> **Prefix note.** The data-model spec writes every name with a `vca_` prefix
> (solution "VendorConnect AI", publisher prefix `vca_`). This document uses
> `new_` instead, per the prefix in use. The mapping is 1:1 —
> `vca_vendor` in the spec is `new_vendor` here, and so on for all 9 tables.
> Nothing else changes: display names ("Vendor Name", "Match Score") and the
> camelCase Blob export field names in spec §4.2 carry no prefix, so the export
> contract and the Azure AI Search index are unaffected. The CSV *filenames* in
> `sample_data/` keep their `vca_` names — they are files on disk, not Dataverse
> objects, and their column headers are display names that map straight in.

**What Copilot reliably gets right:** table name, primary name column, single line
of text, multiple lines of text, whole number, decimal, date only, date and time,
yes/no, and single-select choices with inline options.

**What it usually gets wrong or skips** — each table's *Fix up manually* block
lists the specifics:

- **Lookups** — it often invents a text column instead of a relationship, or
builds the relationship but not the delete behaviour.
- **Multi-select choices** — normally created as single-select. Switch the
behaviour on the column afterwards.
- **File columns** — not supported by the Copilot table builder at all.
- **Global choices** — Copilot creates *local* (table-scoped) choices. Any choice
reused across tables must be created globally first (§0) and then re-pointed.

Copilot also likes to add sample rows and columns you did not ask for. Delete the
extras before moving to the next table; a stray `new_notes` column costs nothing
but a stray *column with the same meaning as a real one* will confuse the JSON
export in §4.2 of the spec.

---



## 0. Global choices (do this first, not via Copilot)

Copilot cannot create environment-level global choices. Build these by hand in
*Solution → New → More → Choice*, then reference them by name in the prompts
below.

**These option lists are the exact distinct values used by** `sample_data/` — every
one is populated, and nothing in the CSVs falls outside them. Add options if you
want, but do not remove any: the Dataverse import wizard fails the whole row on an
unmatched choice value, and a silently-dropped multi-select value produces empty
Azure AI Search facets with no error.


| Choice name          | Behaviour                                                          | Options (count)                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| -------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `new_industry`       | Single                                                             | Business Process Outsourcing · Consulting · Cybersecurity · Engineering Services · Financial Technology · Information Technology · Professional Services · Software Publishing · Telecommunications **(9)**                                                                                                                                                                                                                                         |
| `new_country`        | **Single on Country, Multi-select on Regional Operating Capacity** | Australia · Belgium · Canada · China · France · Germany · Hong Kong SAR · India · Indonesia · Ireland · Japan · Malaysia · Myanmar · Netherlands · New Zealand · Philippines · Poland · Qatar · Saudi Arabia · Singapore · South Korea · Spain · Thailand · United Arab Emirates · United Kingdom · United States · Vietnam **(27)**                                                                                                                |
| `new_businessdomain` | **Multi-select**                                                   | Aviation · Education · Energy & Utilities · Financial Services · Healthcare · Manufacturing · Public Sector · Retail & Consumer · Telecommunications · Transport & Logistics **(10)**                                                                                                                                                                                                                                                               |
| `new_capability`     | **Multi-select**                                                   | Application Development · Business Intelligence · Change Management · Cloud Migration · Conversational AI · Cybersecurity Operations · Data Engineering · Data Governance · DevOps Automation · Document Intelligence · ERP Implementation · Identity & Access Management · Integration & APIs · Machine Learning · Managed Services · Network Infrastructure · Penetration Testing · RPA · Site Reliability Engineering · Test Automation **(20)** |


`new_country` **backs two columns on Vendor, deliberately.** Country
(single-select) and Regional Operating Capacity (multi-select) both point at
the same global choice — a global choice's option list is shared, but each
column independently decides single- vs multi-select. This keeps the two
country vocabularies from drifting apart (e.g. "USA" on one column and "United
States" on the other). The list is 27, not the 19 that Country alone would
need, because Regional Operating Capacity's sample data uses 8 countries no
vendor is headquartered in (New Zealand, Poland, Saudi Arabia, Qatar, Belgium,
China, Myanmar, Spain).

Watch the exact labels — the near-misses are what break an import. `Retail & Consumer` (not "Retail & E-commerce"), `Engineering Services` (not "Engineering &
Construction"), `Machine Learning` (not "AI & Machine Learning"), `Managed Services` (not "Managed IT Services"), `Integration & APIs` (not "Systems
Integration"), `Cybersecurity Operations` as a capability but plain
`Cybersecurity` as an industry.

Multi-select values in the CSVs are **semicolon-delimited** (`Financial Services;Public Sector`), which is what the import wizard expects — no
transformation needed.

The remaining choices in the spec are each used by exactly one table, so local
choices created inline by Copilot are fine. All of the single-table option sets in
the prompts below already match `sample_data/` exactly — verified against the
CSVs:


| Choice                                                | Values in sample data                                                                 | Matches spec |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------ |
| Vendor Status                                         | Potential (6) · Registered (8) · Existing (6)                                         | ✅            |
| Source                                                | Internal Catalogue (9) · External Discovery (6) · Manual Registration (5)             | ✅            |
| Project Status                                        | Active (2) · Draft (1) · Closed (1)                                                   | ✅            |
| Lifecycle Stage                                       | Onboarding (21) · Offboarding (18)                                                    | ✅            |
| Task Status                                           | Not Started (16) · In Progress (4) · Complete (17) · N/A (2)                          | ✅            |
| Focal Role                                            | all 8 values used                                                                     | ✅            |
| Input Validation Outcome · Result Source · Vendor Tag | not seeded — `new_searchlog` / `new_searchresult` are written live by the search flow | n/a          |


`Pronoun` in `vca_vendorcontact.csv` holds `she/her` (22), `he/him` (16) and
`they/them` (3). It stays **free text** — see table 4.

---



## 1. `new_vendor`

The parent of almost everything. Build it first.

```text
Create a Dataverse table called Vendor. It stores one row per supplier company
that BrandName either already works with or is evaluating.

Use "Vendor Name" as the primary name column.

Columns:
- Vendor Name — single line of text, required. The company's trading name.
- Legal Name — single line of text. The registered legal entity name.
- Website Domain — single line of text. The company's web domain, for example
  acmetech.com. Used to detect duplicate vendors.
- HQ Location — single line of text. City or address of the head office.
- Headcount — whole number. Total employees.
- Vendor Status — choice, single selection, with the options: Potential,
  Registered, Existing.
- Has Active Contract — yes/no. Whether the vendor currently holds a live
  contract with BrandName.
- Source — choice, single selection, with the options: Internal Catalogue,
  External Discovery, Manual Registration.
- Overview — multiple lines of text. A profile summary of the company.
- AI Extracted — yes/no. True when the row was created from an AI web search
  result rather than entered by a person.
- Source Citations — multiple lines of text. A JSON array of citation URLs.

Do not add any other columns. Do not create sample data.

---
- Business Domains — choice, allow multiple selections. The industry sectors the
  vendor serves.
- Capabilities — choice, allow multiple selections. The services the vendor can
  deliver.
- Industry — choice, single selection only. The vendor's own industry.
- Country — choice, single selection. The country the vendor is headquartered in.
- Regional Operating Capacity — choice, allow multiple selections. Which
  countries the vendor can deliver in.
```

**Fix up manually**

- Set **Business Domains** and **Capabilities** to the global choices
`new_businessdomain` / `new_capability` and confirm both are **multi-select**
(*Choices*, not *Choice*). Copilot almost always makes them single.
- Set **Industry** → `new_industry`, **Country** → `new_country` (single-select).
- Set **Regional Operating Capacity** → `new_country` as well, but as
**multi-select** (*Choices*). Same global choice as Country, different
selection behaviour — Copilot will not create this column as a choice at all
(it reads "Regional Operating Capacity" as free text), so add it by hand:
new column → *Choice* → sync with global choice `new_country` → allow
multiple selections.
- Confirm **Industry** is single-select. The spec calls this out explicitly.
- Set `Overview` and `Source Citations` max length to 2000+ — Copilot defaults
multiline text to 2000, which is fine for Overview but tight for a citation
array; bump Source Citations to 4000.

**Verify:** 16 columns beyond the system ones, and the table's logical name is
`new_vendor`.

---



## 2. `new_certification`

```text
Create a Dataverse table called Certification. Each row is one certification or
accreditation held by a vendor, such as ISO 27001.

Use "Certification Name" as the primary name column.

Columns:
- Certification Name — single line of text, required. For example "ISO 27001".
- Issuer — single line of text. The body that issued the certification.
- Date Earned — date only.
- Expiry Date — date only.
- Reference Number — single line of text. The certificate or registration number.
- Vendor — a required lookup to the existing Vendor table. Each certification
  belongs to exactly one vendor, and a vendor can have many certifications.

Do not create sample data.
```

**Fix up manually**

- **Add the** `Document` **column by hand** — type **File**. Copilot's table builder
has no File type, so this one is always manual. New column → *File* → max size
32768 KB is plenty for a PDF certificate.
- Confirm **Vendor** is a real *Lookup* column with a 1:N relationship from
Vendor, is **Business required**, and that Copilot did not create a text column
named "Vendor" instead. If it did: delete it and add the lookup manually.

**Verify:** 7 columns including Document and the Vendor lookup. Upload a real PDF
to Document on one test row — this is verification step 1 in the spec.

`sample_data/vca_certification.csv` (61 rows) carries `Document` as an intended
**filename only** — CSV cannot load file content. Drop that column at import and
attach two placeholder PDFs by hand for the demo.

---



## 3. `new_engagement`

```text
Create a Dataverse table called Engagement. Each row is one past or current piece
of delivery work a vendor has done for BrandName. It backs the "Past Experience"
tab on the vendor detail screen.

Use "Delivery Project Name" as the primary name column.

Columns:
- Delivery Project Name — single line of text, required. The name of the project
  the vendor delivered.
- Business Unit — single line of text. The BrandName business unit that engaged
  them.
- Outcome Summary — multiple lines of text. One or two sentences on what was
  delivered.
- Start Date — date only.
- End Date — date only. Left blank when the engagement is still ongoing.
- Headcount — whole number. People the vendor placed on the engagement.
- Is Case Study — yes/no. True when this engagement should be shown as a
  published case study.
- Vendor — a required lookup to the existing Vendor table. One vendor has many
  engagements.

Do not create sample data.
```

**Fix up manually**

- Keep the primary column labelled exactly **Delivery Project Name**. Do not let
it become "Project Name" — the spec's verification step 15 checks that no screen
shows two fields both labelled "Project Name" (Project has its own).
- Confirm the Vendor lookup as in table 2.

**Verify:** 8 columns.

---



## 4. `new_vendorcontact`

```text
Create a Dataverse table called Vendor Contact. Each row is one person at a
vendor company who BrandName deals with.

Use "Contact Name" as the primary name column.

Columns:
- Contact Name — single line of text, required.
- Pronoun — single line of text. Free text, entered by the user.
- Email — single line of text, formatted as email.
- Phone Number — single line of text, formatted as phone.
- Title — single line of text. Their job title.
- Vendor — a required lookup to the existing Vendor table. One vendor has many
  contacts.

Do not create sample data.
```

**Fix up manually**

- `Pronoun` **must stay free text.** If Copilot turns it into a choice with
she/her, he/him, they/them options, delete the column and re-add it as single
line of text. The spec is explicit that this is not constrained to a picklist.
- Confirm the Vendor lookup.

**Verify:** 6 columns, and the table's logical name is `new_vendorcontact` (Power
Apps will strip the space in "Vendor Contact" — check it did not produce
`new_vendor_contact`).

---



## 5. `new_searchlog`

Build this before Search Result — Search Result looks up to it.

```text
Create a Dataverse table called Search Log. Each row records one AI-assisted
vendor search that a user ran. It is what the search history page lists.

Use "Query Text" as the primary name column.

Columns:
- Query Text — multiple lines of text, required. The user's search wording,
  stored verbatim.
- Submitted On — date and time, required. When the search ran.
- Submitted By — single line of text. The name of the user who ran it.
- Sources Used — single line of text. For example "Internal, External".
- Internal Result Count — whole number.
- External Result Count — whole number.
- Duration Ms — whole number. How long the search took in milliseconds.
- Input Validation Outcome — choice, single selection, with the options:
  Accepted, Rejected - too vague.
- Extracted Criteria — multiple lines of text. A JSON array of the requirements
  the AI derived from the query.

Do not create sample data.
```

**Fix up manually**

- Dataverse **cannot use a multiline text column as the primary name column**.
Copilot will either silently make `Query Text` single-line or create a separate
primary column. Resolution: let the primary name column be a single line of
text named **Query Text** (255 chars) and *additionally* create
**Query Text Full** as multiple lines of text if you expect queries over 255
characters. For a 3-day prototype, the single-line primary column alone is
usually enough — decide now and tell the AI developer, since the search flow
writes this column.
- Rename the `Rejected - too vague` option label to `Rejected – too vague`
(en dash) if you want it to match the spec's wording exactly; the value matters,
the dash does not.
- Set `Extracted Criteria` max length to 4000.

**Verify:** 9 columns.

---



## 6. `new_searchresult`

```text
Create a Dataverse table called Search Result. Each row is one vendor that came
back from one AI search. It stores a snapshot of what was found at the time, so
that reopening a past search shows the original results.

Use "Vendor Name Snapshot" as the primary name column.

Columns:
- Vendor Name Snapshot — single line of text, required. The vendor name as it was
  found at search time.
- Website Domain Snapshot — single line of text.
- Summary Snapshot — multiple lines of text. The short description shown on the
  result card.
- Result Source — choice, single selection, with the options: Internal, External.
- Vendor Tag — choice, single selection, with the options: Existing Vendor, New
  Vendor.
- Match Score — decimal number between 0 and 1, with 2 decimal places.
- Rank — whole number. Position in the merged result list.
- Criteria Results — multiple lines of text. JSON describing which criteria this
  vendor met and the supporting evidence.
- Source Citations — multiple lines of text. A JSON array of citation URLs.
- Search Log — a required lookup to the existing Search Log table. One search log
  has many search results.
- Vendor — an optional lookup to the existing Vendor table. It is left empty for
  externally discovered vendors that have not yet been promoted to a vendor
  record.

Do not create sample data.
```

**Fix up manually**

- `Vendor` **must be optional** (Business required = *Optional*). Copilot tends
to mark every lookup required. If it is required, un-promoted external finds
cannot be logged at all and verification step 8 fails.
- `Search Log` **must be required.**
- Confirm `Match Score` is **Decimal** with precision 2 and min 0 / max 1.
- Set `Criteria Results` and `Source Citations` max length to 4000+ — the criteria
matrix JSON carries evidence strings and outgrows 2000 quickly.

**Verify:** 11 columns, one required lookup and one optional lookup.

---



## 7. `new_lifecycletask`

```text
Create a Dataverse table called Lifecycle Task. Each row is one checklist item in
either the vendor onboarding or the vendor offboarding process. Both checklists
live in this one table and are told apart by the Stage column.

Use "Task Title" as the primary name column.

Columns:
- Task Title — single line of text, required.
- Stage — choice, single selection, required, with the options: Onboarding,
  Offboarding.
- Description — multiple lines of text. What the task involves.
- Status — choice, single selection, with the options: Not Started, In Progress,
  Complete, N/A.
- Focal Role — choice, single selection, with the options: VM, Vendor, Contract
  Owner, Risk Team, MyAccess, Finance, CSPC Buyer, User.
- Due Date — date only.
- Completed On — date and time. Set when the task is marked complete.
- Sequence — whole number. The display order of the task within its checklist.
- Notes — multiple lines of text.
- Vendor — a required lookup to the existing Vendor table. One vendor has many
  lifecycle tasks.

Do not create sample data.
```

**Fix up manually**

- Confirm **Stage** is required — the two dashboards are one view filtered on it,
so a null Stage row appears on neither.
- Default `Status` to **Not Started**.
- Do **not** add a Project lookup. It is listed as deferred in the spec §7.

**Verify:** 10 columns. Then load `sample_data/vca_lifecycletask.csv` — 39 rows:
3 onboarding sets of 7 (Hanseatic 3/7 complete, Hangang AI 1/7, Silverline Cyber
7/7) and 2 offboarding sets of 9 (Vertex Fintech 5/9, Pacific Rim 1/9). Mixed
statuses are deliberate, so the progress bars read part-complete.

---



## 8. `new_project`

Seed-data only — no screens create or edit projects this phase.

```text
Create a Dataverse table called Project. Each row is a sourcing project that
vendors get shortlisted for. Rows are entered by an administrator, not through
the app.

Use "Project Name" as the primary name column.

Columns:
- Project Name — single line of text, required. What the shortlist picker
  displays.
- Project Code — single line of text. For example "SRC-2026-014".
- Business Unit — single line of text. The unit requesting the sourcing work.
- Description — multiple lines of text. The sourcing need in plain language.
- Status — choice, single selection, with the options: Draft, Active, Closed.
- Start Date — date only.
- Target Date — date only.

Do not add an owner or assignee column. Do not create sample data.
```

**Fix up manually**

- Nothing structural. Do not add an Owner column — ownership is deliberately not
modelled (spec §3.9).

**Verify:** 7 columns. Then load `sample_data/vca_project.csv` — 4 rows, Active ×2,
Draft ×1, Closed ×1 (the spec asks for 2; the sample data goes further and covers
Closed as well).

---



## 9. `new_shortlistitem`

Last, because it needs both Vendor and Project.

```text
Create a Dataverse table called Shortlist Item. Each row records that one vendor
has been shortlisted, optionally for a specific sourcing project. There is no
separate shortlist header table — items are grouped by their project.

Columns:
- Vendor — a required lookup to the existing Vendor table.
- Project — an optional lookup to the existing Project table. Left empty when the
  vendor is shortlisted but not yet assigned to a project.
- Added On — date and time. When the vendor was shortlisted.
- Added By — single line of text. Who shortlisted it, for audit only.
- Note — multiple lines of text. Why this vendor was shortlisted.

Do not create sample data.
```

**Fix up manually — this table has the most Copilot cannot do**

1. **Primary name column.** The spec lists no name column, but Dataverse forces
  one. Let Copilot create the default `Name` and leave it unused, or set it with
   a formula/flow to `Vendor name — Project name` so the row is readable in the
   maker portal. Either is fine; do not add it to any screen.
2. `Project` **must be optional.** Null is the "unassigned" bucket and the spec's
  verification steps 11–13 all depend on it.
3. **Set the Project → Shortlist Item relationship delete behaviour to
  `Remove Link`, not `Cascade`.** Copilot will not do this. Go to
   *Project → Relationships → the Shortlist Item 1:N relationship → Advanced
   options → Delete: Remove Link*. Deleting a project must return its items to
   the unassigned bucket, not destroy them.
4. **Do not create an alternate key on (Project, Vendor).** Dataverse alternate
  keys reject nullable columns and Project is nullable. Duplicate prevention is
   app-side: before insert, look for a row with the same Vendor *and* the same
   Project, treating null-Project as its own bucket rather than as a wildcard.

**Verify:** 5 business columns plus the unused primary name column. Then load
`sample_data/vca_shortlistitem.csv` — 10 rows: 3 under Document Digitisation
Programme, 2 under Cloud Migration Phase 2, 2 under Cybersecurity Operations
Uplift, 1 under the Closed project, 2 unassigned. No (Vendor, Project) pair
repeats, so the duplicate guard starts clean.

---



## After all 9 tables

1. **Publish all customizations** in the solution.
2. Walk spec §6 verification steps 1 and 15 — they are the two that catch schema
  mistakes rather than app mistakes.
3. Load `sample_data/` in the README's stated order (vendor → project →
  certification → engagement → contact → lifecycle task → shortlist item);
   lookups are display-name text, so parents must land first. **The sample data
   has 20 vendors, not the spec's 25–30, and does not yet contain the deliberate
   near-duplicate pair** ("Acme Technologies Pte Ltd" / "ACME Tech" sharing one
   website domain) — verification step 6 has no data behind it until a second Acme
   row is added. This gap is already recorded in `sample_data/README.md`.
4. Produce the Blob JSON export (spec §4.2) and hand it to the AI developer
  **before** anyone builds the index. Field names are camelCase and must match
   the index exactly; a mismatch returns empty results with no error.



### Things Copilot will never do — a single checklist


| Item                                            | Table                     | Why it matters                                        |
| ----------------------------------------------- | ------------------------- | ----------------------------------------------------- |
| `Document` File column                          | Certification             | Copilot has no File type                              |
| Multi-select on Business Domains / Capabilities | Vendor                    | Search facets and comparison read them as sets        |
| Global choices instead of local                 | Vendor (5 columns)        | Sample data and index values must agree across tables |
| `Vendor` lookup optional                        | Search Result             | Un-promoted external finds have no vendor row yet     |
| `Project` lookup optional                       | Shortlist Item            | Null is the unassigned bucket                         |
| `Remove Link` on delete                         | Project → Shortlist Item  | Cascade silently destroys shortlist work              |
| Decimal 0–1, precision 2                        | Search Result Match Score | Match score is a fraction, not a whole number         |


