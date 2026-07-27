# Data Model — VendorConnect AI Prototype (Minimal)

Dataverse tables and the derived Azure AI Search index for the 3-day Vendor
Summit prototype.

**This is a deliberately minimal model: 8 tables.** Every table and column below
is justified by a specific row in the team's planned-feature list (§1) or by the
client's all-four-stages rule. Anything the concept deck shows but the feature
list does not ask for is in the deferred appendix (§7), not here.

**Companion document:** `2026-07-27-vendorconnect-ai-prototype-scope.md` (scope,
completeness tiers, three-lane AI architecture).

**Solution:** "VendorConnect AI" · **Publisher prefix:** `vca_`

Conventions follow the Empower@BrandName Builders data model
(`docs/superpowers/plans/2026-07-22-empower-brandname-builders-plan.md`, Task 1).

---

## 1. Feature list this model serves

Transcribed from the team's Miro board. This is the authoritative feature list.

| # | Task Name | Initiative | Description |
|---|---|---|---|
| 1 | General Layout | — | Left side menu: Vendor · Discover · Onboarding · Offboarding · Shortlist |
| 2 | Vendor List | Vendor Management | List registered & existing vendors. Each item shows Name, Country/Region, Industry, Domain, Tag (Active Contract, Registered) |
| 3 | View Vendor Detail | Vendor Management | Header: Name, Industry, Domain. Tabs: Overview, Certifications, Past Experience (Case Studies, Engagement with BrandName), Contacts. Buttons: Add to shortlist, Start Onboarding/Offboarding, Compare |
| 4 | Create new vendor | Vendor Management | Multi-step form |
| 5 | Edit – Update Vendor info | Vendor Management | Core company metadata: Name, Industry (dropdown, single), Domain (multiple choice). Legal status: TBD. HQ location. Regional operating capacity, headcount |
| 6 | Edit – Upload certification | Vendor Management | Add new document. Storage: resolved in §2 |
| 7 | Edit – Past Experience | Vendor Management | Add new experience with BrandName: start date, end date, project, headcount |
| 8 | Edit – Contacts | Vendor Management | Name, Pronoun, Email, Phone number, Title |
| 9 | Discover page UI | AI-assisted Vendor Discovery | Placeholder text, "Search with AI" button, enabled only when text present |
| 10 | Search with AI | AI-assisted Vendor Discovery | (a) Validate input suitability; alert user to improve it if not. (b) Search internal (VMO engine, SIM) + external. (c) Determine core requirements sought. (d) Show criteria as true/false in results & compute match score. (e) Merge internal + external; tag "Existing Vendor" or "New Vendor" |
| 11 | Comparison | Comparison | Compare vendors against a list of static criteria (TBD) |

Priority, Assignee, Estimated Effort and Notes are unpopulated on the source board.

### 1.1 Table justification

| Table | Justified by |
|---|---|
| `vca_vendor` | Rows 2, 3, 4, 5 |
| `vca_certification` | Row 6 — "add new document" means real child rows, not display-only text |
| `vca_engagement` | Row 7 |
| `vca_vendorcontact` | Row 8 |
| `vca_lifecycletask` | The all-four-stages rule (Onboard, Offboard) |
| `vca_shortlistitem` | Row 3's "Add to shortlist" button + the nav entry |
| `vca_searchlog` | Search history page — one row per past AI search |
| `vca_searchresult` | Search history page — the result set of each past search |

Rows 1, 9 and 11 need no tables of their own — layout and the Discover page hold
no data, and Comparison reads fields that already exist.

The last two are not on the Miro board; they are required by the added
**search-history page** (list all past AI search results). Without them a search
is transient and there is nothing to list.

### 1.2 Stage coverage

| Stage | Backed by |
|---|---|
| Source Vendors | Azure AI Search index (§4) over `vca_vendor` for retrieval; `vca_searchlog` + `vca_searchresult` for the persisted outcome |
| Cross-Validate | Computed inline during row 10(e); the verdict is stored as the Vendor Tag on `vca_searchresult`. No dedicated table. |
| Onboard | `vca_lifecycletask` filtered on Stage = Onboarding |
| Offboard | `vca_lifecycletask` filtered on Stage = Offboarding |
| *(Shortlist)* | `vca_shortlistitem` |

Onboarding, Offboarding and Shortlist appear in the navigation and as buttons on
row 3, but have no feature rows on the board. `vca_lifecycletask` and
`vca_shortlistitem` are hand-seeded so those screens read real data whether or
not the instantiation flows get built.

### 1.3 Source-list notes

- **"Active Contact"** on row 2 is read as **Active Contract** — it sits beside "Registered" as a status tag.
- **ADB** appears on rows 3 and 7 where committed docs use the placeholder **BrandName**. Placeholder retained here.
- Source typos: "certificiation", "Enagement", "inclcude".

---

## 2. Resolved design decisions

| Question | Decision |
|---|---|
| Onboarding / offboarding depth | **Tables + seed data now; instantiation flows are day-3 stretch.** |
| Onboarding vs offboarding tables | **One `vca_lifecycletask` table with a Stage choice**, not two. |
| "Domain" ambiguity | **Two distinct fields.** `Website Domain` (text) is the cross-validation match key. `Business Domains` (multi-select choice) is the sector shown in the vendor list. |
| Certification document storage (row 6 TBD) | **Dataverse File column** on Certification. No SharePoint dependency inside 3 days. |
| Capabilities | **Multi-select choice on Vendor**, not a separate table with an N:N relationship. The feature list never mentions capabilities; N:N is also the fiddliest relationship to build on day 1. |
| Search results | **Persisted** as `vca_searchlog` + `vca_searchresult`, required by the search-history page. |
| Search criteria matrix (row 10 c/d) | **Persisted as JSON text**, not as tables. `Extracted Criteria` on the log, `Criteria Results` on each result row. Enough to replay a past search exactly; not queryable, which the history page never needs. |
| Cross-validation result | **Stored as the Vendor Tag** on `vca_searchresult`, not in a dedicated audit table. |
| Externally-discovered vendors | **Snapshot in `vca_searchresult`; promoted to a `vca_vendor` row only when someone acts on them** (shortlist or start onboarding). See §3.8.1. |

### 2.1 Still open, non-blocking

Neither changes the schema — the columns exist and need only their option sets filled in.

- **Legal status values** (row 5). `Legal Name` is text for now. If it turns out to mean entity type (Pte Ltd / GmbH / LLC) it becomes a choice; a text column absorbs either outcome.
- **Comparison criteria** (row 11). The comparison screen reads existing fields, so no new table is needed. Agreeing the criteria is a column selection, not a schema change.

---

## 3. Dataverse tables

### 3.1 `vca_vendor`

One row per vendor. 16 columns.

| Column | Type | Notes |
|---|---|---|
| Vendor Name | Single line of text (required) | Primary name column |
| Legal Name | Single line of text | "Legal status" — values still TBD |
| Website Domain | Single line of text | **Cross-validation match key** (§1.2) |
| Business Domains | Choice (multi-select) | Sector; also a vendor-list column |
| Capabilities | Choice (multi-select) | Search quality + comparison; folded in from the deferred Capability table |
| Industry | Choice (single) | Single choice, not multi |
| Country / Region | Choice | Vendor-list column |
| HQ Location | Single line of text | |
| Regional Operating Capacity | Multiple lines of text | |
| Headcount | Whole number | |
| Vendor Status | Choice: Potential / Registered / Existing | Drives the "Registered" tag |
| Has Active Contract | Yes/No | Drives the "Active Contract" tag |
| Source | Choice: Internal Catalogue / External Discovery / Manual Registration | Drives Existing/New Vendor tagging |
| Overview | Multiple lines of text | Profile Overview tab; feeds the search embedding |
| AI Extracted | Yes/No | Set on promotion from an external find. Drives the "unverified — model-extracted" badge on Vendor Detail |
| Source Citations | Multiple lines of text | JSON array of citation URLs, copied from the search result on promotion |

### 3.2 `vca_certification`

Row 6. 7 columns.

| Column | Type | Notes |
|---|---|---|
| Certification Name | Single line of text (required) | e.g. "ISO 27001" |
| Issuer | Single line of text | |
| Date Earned | Date only | |
| Expiry Date | Date only | |
| Reference Number | Single line of text | |
| Document | File | Stored in Dataverse, not SharePoint |
| Vendor | Lookup → Vendor (required) | Parent |

### 3.3 `vca_engagement`

Row 7 and the Past Experience tab. 8 columns.

| Column | Type | Notes |
|---|---|---|
| Project Name | Single line of text (required) | |
| Business Unit | Single line of text | |
| Outcome Summary | Multiple lines of text | 1–2 sentences |
| Start Date | Date only | |
| End Date | Date only | Blank = ongoing |
| Headcount | Whole number | |
| Is Case Study | Yes/No | "Case Studies" and "Engagement with BrandName" share one tab; a flag covers both without a second table |
| Vendor | Lookup → Vendor (required) | Parent |

### 3.4 `vca_vendorcontact`

Row 8, exactly its five fields. 6 columns.

| Column | Type | Notes |
|---|---|---|
| Contact Name | Single line of text (required) | |
| Pronoun | Single line of text | **Free text, not a choice set** — do not constrain to a picklist |
| Email | Single line of text | |
| Phone Number | Single line of text | |
| Title | Single line of text | |
| Vendor | Lookup → Vendor (required) | Parent |

### 3.5 `vca_lifecycletask`

Both checklists in one table. 10 columns.

| Column | Type | Notes |
|---|---|---|
| Task Title | Single line of text (required) | |
| Stage | Choice: Onboarding / Offboarding (required) | The two dashboards are one view filtered on this |
| Description | Multiple lines of text | Verbatim from the brief's checklists |
| Vendor | Lookup → Vendor (required) | |
| Status | Choice: Not Started / In Progress / Complete / N/A | |
| Focal Role | Choice: VM / Vendor / Contract Owner / Risk Team / MyAccess / Finance / CSPC Buyer / User | Replaces a Team Member lookup |
| Due Date | Date only | |
| Completed On | Date and Time | Audit trail |
| Sequence | Whole number | Display order |
| Notes | Multiple lines of text | |

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

Row 3's button. One implicit shortlist per user — no parent table. 4 columns.

| Column | Type | Notes |
|---|---|---|
| Vendor | Lookup → Vendor (required) | |
| Added On | Date and Time | |
| Added By | Single line of text | Demo persona name |
| Note | Multiple lines of text | |

### 3.7 `vca_searchlog`

One row per AI search. This is what the search-history page lists. 9 columns.

| Column | Type | Notes |
|---|---|---|
| Query Text | Multiple lines of text (required) | Verbatim user input — the history list's primary display |
| Submitted On | Date and Time (required) | Sort key for the history page |
| Submitted By | Single line of text | Demo persona name |
| Sources Used | Single line of text | e.g. "Internal, External" |
| Internal Result Count | Whole number | |
| External Result Count | Whole number | |
| Duration Ms | Whole number | |
| Input Validation Outcome | Choice: Accepted / Rejected – too vague | A rejected search is still logged — that history is useful, and it demonstrates the guardrail |
| Extracted Criteria | Multiple lines of text | JSON array of the requirements the model derived, e.g. `["Government experience", "ISO 27001"]`. Enables exact replay |

### 3.8 `vca_searchresult`

One row per vendor per search — the result set that makes a past search
re-openable. 11 columns.

| Column | Type | Notes |
|---|---|---|
| Search Log | Lookup → Search Log (required) | Parent |
| Vendor | Lookup → Vendor (**optional**) | Populated for internal hits, and for external hits after promotion. Null for un-promoted external finds |
| Vendor Name Snapshot | Single line of text (required) | What was found *then* — history stays truthful even if the vendor record later changes |
| Website Domain Snapshot | Single line of text | |
| Summary Snapshot | Multiple lines of text | Short description shown in the result card |
| Result Source | Choice: Internal / External | Which lane returned it |
| Vendor Tag | Choice: Existing Vendor / New Vendor | The cross-validation verdict |
| Match Score | Decimal (0–1) | Denormalised so the history page needs no recomputation |
| Rank | Whole number | Position in the merged result set |
| Criteria Results | Multiple lines of text | JSON, e.g. `[{"criterion":"ISO 27001","met":true,"evidence":"…"}]`. Renders the true/false matrix on replay |
| Source Citations | Multiple lines of text | JSON array of citation URLs, for external hits |

The snapshot columns are deliberate. A historical result should show what was
found at the time, not the current state of a record that may since have been
edited — and it lets external finds live in history without forcing a
`vca_vendor` row into existence.

#### 3.8.1 Promote-on-action

An externally-discovered vendor becomes a real `vca_vendor` row **only when
someone acts on it** — "Add to shortlist" or "Start Onboarding". Both of those
tables take a required Vendor lookup, so the row must exist by then; nothing
before that point needs it.

On promotion: create the Vendor with `Source = External Discovery`,
`Vendor Status = Potential`, `AI Extracted = Yes`, citations copied across, then
write the new GUID back to `vca_searchresult.Vendor`.

Two reasons this beats writing every external hit immediately. Search results
stay clean — ten Bing hits per query would otherwise flood the vendor list and
the search index within a few rehearsals. And row 2 specifies "registered &
existing vendor", so un-promoted finds do not belong in that list anyway.

---

## 4. Azure AI Search index

Index name `vendor-profiles-index`. One document per vendor. 13 fields.

**Key departure from the Empower@BrandName Builders pattern:** that project
hand-built embeddings in a nightly Power Automate loop. This prototype uses
**integrated vectorization** — a Blob data source, a skillset with the
`AzureOpenAIEmbedding` skill, and an `azureOpenAI` **vectorizer declared on the
index**. The vectorizer is the important part: Power Automate sends plain query
text and AI Search embeds it server-side, so the internal search lane needs no
embedding call of its own. No chunking skill — vendor documents are short enough
to embed whole.

```json
{
  "name": "vendor-profiles-index",
  "fields": [
    { "name": "id", "type": "Edm.String", "key": true, "filterable": true },
    { "name": "vendorName", "type": "Edm.String", "searchable": true, "filterable": true, "sortable": true },
    { "name": "websiteDomain", "type": "Edm.String", "searchable": true, "filterable": true },
    { "name": "vendorText", "type": "Edm.String", "searchable": true },
    { "name": "vendorVector", "type": "Collection(Edm.Single)", "searchable": true,
      "dimensions": 3072, "vectorSearchProfile": "vendor-vector-profile" },
    { "name": "vendorStatus", "type": "Edm.String", "filterable": true, "facetable": true },
    { "name": "industry", "type": "Edm.String", "filterable": true, "facetable": true },
    { "name": "businessDomains", "type": "Collection(Edm.String)", "filterable": true, "facetable": true },
    { "name": "capabilities", "type": "Collection(Edm.String)", "searchable": true, "filterable": true, "facetable": true },
    { "name": "certifications", "type": "Collection(Edm.String)", "searchable": true, "filterable": true, "facetable": true },
    { "name": "countryRegion", "type": "Edm.String", "filterable": true, "facetable": true },
    { "name": "headcount", "type": "Edm.Int32", "filterable": true, "sortable": true },
    { "name": "hasActiveContract", "type": "Edm.Boolean", "filterable": true, "facetable": true }
  ],
  "vectorSearch": {
    "algorithms": [{ "name": "hnsw-default", "kind": "hnsw" }],
    "profiles": [{
      "name": "vendor-vector-profile",
      "algorithm": "hnsw-default",
      "vectorizer": "vendor-openai-vectorizer"
    }],
    "vectorizers": [{
      "name": "vendor-openai-vectorizer",
      "kind": "azureOpenAI",
      "azureOpenAIParameters": {
        "resourceUri": "<foundry-openai-endpoint>",
        "deploymentId": "text-embedding-3-large",
        "modelName": "text-embedding-3-large"
      }
    }]
  },
  "semantic": {
    "configurations": [{
      "name": "vendor-semantic-config",
      "prioritizedFields": {
        "titleField": { "fieldName": "vendorName" },
        "prioritizedContentFields": [{ "fieldName": "vendorText" }],
        "prioritizedKeywordsFields": [
          { "fieldName": "capabilities" },
          { "fieldName": "certifications" }
        ]
      }
    }]
  }
}
```

`certifications` is derived from the child `vca_certification` rows at export
time. There is no `lastIndexedOn` — the dataset is small enough to rebuild the
index in full, so no change-watermark is needed.

### 4.1 `vendorText` composition

The single string that gets embedded. Concatenate in this order:

```
{Vendor Name} ({Legal Name})
Industry: {Industry} | Domains: {Business Domains}
HQ: {HQ Location}, {Country/Region} | Headcount: {Headcount}
Overview: {Overview}
Capabilities: {Capabilities}
Certifications: {Certification Name (Issuer), ...}
Past experience: {Project Name — Outcome Summary; ...}
Regional capacity: {Regional Operating Capacity}
```

Note that `legalName`, `hqLocation` and `regionalOperatingCapacity` are *not*
index fields — they contribute to `vendorText` (and so to semantic matching) but
nothing filters or displays on them, so they need no field of their own.

### 4.2 Blob document contract

One JSON object per vendor in the indexed container. Field names must match the
index exactly (camelCase), which is why they differ from Dataverse display names.

```json
{
  "id": "8f3c1e2a-...",
  "vendorName": "Acme Technologies",
  "websiteDomain": "acmetech.com",
  "vendorText": "Acme Technologies (Acme Technologies Pte Ltd)\nIndustry: ...",
  "vendorStatus": "Registered",
  "industry": "Information Technology",
  "businessDomains": ["Financial Services", "Public Sector"],
  "capabilities": ["Document Intelligence", "RPA"],
  "certifications": ["ISO 27001", "SOC 2 Type II"],
  "countryRegion": "Singapore",
  "headcount": 240,
  "hasActiveContract": true
}
```

**This export file is the interface between the data developer and the AI
developer — agree it before either starts.** A camelCase mismatch produces empty
search results with no error.

### 4.3 Internal search query shape

Hybrid + semantic, sent from Power Automate. `vectorQueries.kind: "text"` is what
activates the index vectorizer:

```json
{
  "search": "<user query>",
  "queryType": "semantic",
  "semanticConfiguration": "vendor-semantic-config",
  "vectorQueries": [{
    "kind": "text", "text": "<user query>",
    "fields": "vendorVector", "k": 10
  }],
  "select": "id,vendorName,industry,countryRegion,websiteDomain,vendorStatus,hasActiveContract,capabilities,certifications",
  "top": 10
}
```

---

## 5. Build order (data developer, day 1)

| # | Work | Est. |
|---|---|---|
| 1 | Solution + publisher prefix `vca_`, choice sets (Industry, Country/Region, Business Domains, Capabilities) | 45 min |
| 2 | `vca_vendor` | 1 h |
| 3 | `vca_certification` (File column), `vca_engagement`, `vca_vendorcontact` | 1 h |
| 4 | Sample vendor load — 25–30 fictional records, including two deliberate near-duplicates | 1.5 h |
| 5 | **Blob JSON export → hand to AI developer** (§4.2) | 1 h |
| 6 | `vca_searchlog` + `vca_searchresult` | 45 min |
| 7 | `vca_lifecycletask` + hand-seeded demo checklists (7 onboarding, 9 offboarding) | 1 h |
| 8 | `vca_shortlistitem` | 15 min |

Roughly 7.25 hours — one day, with modest slack for the choice-set churn that
always happens once real sample data arrives.

Step 6 must be agreed with the AI developer, not just built: the search flow
writes both tables, so the JSON shapes for `Extracted Criteria` and
`Criteria Results` are a shared contract in the same way the Blob export is.

**Step 5 is the critical path.** The index is blocked until the export shape
exists, so prioritise it over steps 6 and 7.

---

## 6. Verification

The model is correct when all of the following pass.

1. **Dataverse CRUD** — create a vendor via the row 4 multi-step form with a certification (including a real file upload to the File column), a past engagement and a contact; confirm all three children resolve on the row 3 detail tabs.
2. **Export contract** — run the JSON export and validate every camelCase key against the index field list. Check this *before* indexing; a mismatch fails silently.
3. **Indexer** — run once; confirm document count equals the Dataverse vendor count and `vendorVector` is non-null on every document.
4. **Vectorizer** — POST the §4.3 query with `vectorQueries.kind: "text"` and no pre-computed embedding. Ranked results back means integrated vectorization works and the internal lane needs no embedding call.
5. **Semantic ranker** — compare a conceptual query ("document processing for government") against keyword-only search. Results should rank differently; identical ordering means the config is not applied.
6. **Cross-validation key** — confirm the two seeded near-duplicates ("Acme Technologies Pte Ltd" / "ACME Tech", same website domain) resolve to the Existing Vendor tag on row 10(e).
7. **Lifecycle without flows** — with only hand-seeded rows and no instantiation flow, confirm both dashboards render a part-complete progress bar from `vca_lifecycletask` filtered on Stage, and that a status change persists with a timestamp. This is the check that the all-four-stages rule is met by data rather than by static screens.
8. **Search history replay** — run three searches (one deliberately too vague, so it logs as Rejected). Confirm the history page lists all three newest-first, and that re-opening one renders the original result set with match scores, Existing/New tags and the criteria matrix — read from `vca_searchresult`, with no second call to AI Search or Bing.
9. **Snapshot integrity** — after replaying a past search, edit that vendor's name in Dataverse and reopen the same history entry. It must still show the *old* name from `Vendor Name Snapshot`. If it shows the new one, the page is reading through the lookup instead of the snapshot.
10. **Promote-on-action** — shortlist an un-promoted external result. Confirm a `vca_vendor` row is created with `Source = External Discovery`, `AI Extracted = Yes` and citations copied, and that `vca_searchresult.Vendor` is back-filled with the new GUID.

---

## 7. Deferred — add only if time permits

Everything cut from the earlier draft, with what each costs to restore. Ordered
by value, not by size.

| Deferred | What it buys | Cost | Why it was cut |
|---|---|---|---|
| `vca_searchcriteria` + `vca_criteriaresult` | Promotes the criteria matrix from JSON text into queryable rows — needed only to *aggregate* across searches ("which criteria do we ask for most?") | ~1 h | The JSON columns on `vca_searchlog` / `vca_searchresult` already replay any single search exactly, which is all the history page does |
| `vca_contract` + `vca_contractdeliverylog` | Auto-created Contract Delivery Log — **explicitly named in the client brief** as an onboarding automation | ~1 h + flow | `Has Active Contract` already drives row 2's tag; CDL auto-create was stretch work anyway |
| `vca_checklisttemplate` (16 rows) | Template-driven instantiation instead of hand-seeding | ~45 min | With flows deferred and checklists hand-seeded, it is indirection with no consumer. Add it the moment the flow gets built. |
| `vca_crossvalidation` | Dedicated audit trail + a real "duplicate vendors prevented" count | ~45 min | The verdict is already stored as `vca_searchresult.Vendor Tag`; a separate table only adds aggregation the executive dashboard would need, and that is not a feature-list item |
| AI insight cache columns on Vendor (Summary, Strengths, Weaknesses, Risks, Recommendation, Citation Count, Generated On) | The AI Insights screen | ~30 min | AI Insights appears in the concept deck but in no feature-list row |
| `vca_capability` table + N:N | Category facets and a governed capability taxonomy | ~1 h | Multi-select choice covers the prototype; N:N is the fiddliest day-1 relationship |
| `vca_teammember` | Lookup integrity on assignees and contract owners | ~30 min | One demo persona; Focal Role choice covers it |
| `vca_shortlist` parent | Multiple named shortlists | ~20 min | One implicit shortlist per user is enough |
| Vendor `Rating`, `Last Indexed On` | Ratings display, incremental indexing | minutes each | Not in row 2's list columns; full index rebuilds are cheap at this size |

### 7.1 The two worth reconsidering

**Minimal and best-demo diverge in exactly two places**, both about an hour:

- **The Contract Delivery Log** is named in the client brief as a specific onboarding automation. Cutting it is defensible on time, but it should be a stated decision to the client rather than a silent omission.
- **The criteria matrix tables** make the match score explainable under questioning. The score still works without them — but "how was 94% calculated?" is answered from transient JSON rather than data you can point at.
