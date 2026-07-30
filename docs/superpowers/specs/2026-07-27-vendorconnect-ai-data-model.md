# Data Model — VendorConnect AI Prototype (Minimal)

Dataverse tables and the derived Azure AI Search index for the 3-day Vendor
Summit prototype.

**This is a deliberately minimal model: 9 tables.** Every table and column below
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
| 2 | Vendor List | Vendor Management | List registered & existing vendors. Each item shows Name, Country, Industry, Domain, Tag (Active Contract, Registered) |
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
| `vca_project` | Project-scoped shortlisting — **dummy data only, no UI** |

Rows 1, 9 and 11 need no tables of their own — layout and the Discover page hold
no data, and Comparison reads fields that already exist.

The last three are not on the Miro board. `vca_searchlog` and `vca_searchresult`
are required by the added **search-history page** (list all past AI search
results) — without them a search is transient and there is nothing to list.
`vca_project` exists so shortlisted vendors can be assigned to a sourcing
project; it is seeded directly in Dataverse and has no screens of its own.

### 1.2 Stage coverage

| Stage | Backed by |
|---|---|
| Source Vendors | Azure AI Search index (§4) over `vca_vendor` for retrieval; `vca_searchlog` + `vca_searchresult` for the persisted outcome |
| Cross-Validate | Computed inline during row 10(e); the verdict is stored as the Vendor Tag on `vca_searchresult`. No dedicated table. |
| Onboard | `vca_lifecycletask` filtered on Stage = Onboarding |
| Offboard | `vca_lifecycletask` filtered on Stage = Offboarding |
| *(Shortlist)* | `vca_shortlistitem`, grouped by `vca_project` |

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
| Project assignment | Shortlisted vendors are assigned to a **`vca_project`** via an **optional** lookup. Null = unassigned. |
| Project UI | **None this phase.** No project list, detail or CRUD screens; rows are seeded directly in Dataverse. The only project UI is a picker on shortlist items. |
| Project scoping of search | **Search history stays global.** No Project lookup on `vca_searchlog` — searching is often exploratory before a project exists. |

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
| Country | Choice | Vendor-list column |
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
| Delivery Project Name | Single line of text (required) | Named "Delivery" to distinguish it from `vca_project` (a *sourcing* project). This is the vendor's past delivery with BrandName |
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

Row 3's button. Grouped by project — no named-shortlist parent table. 5 columns.

| Column | Type | Notes |
|---|---|---|
| Vendor | Lookup → Vendor (required) | |
| Project | Lookup → Project (**optional**) | Null = unassigned. The grouping key for the shortlist page |
| Added On | Date and Time | |
| Added By | Single line of text | Audit only — no longer the grouping key |
| Note | Multiple lines of text | |

**Set the Project → Shortlist Item relationship to `Remove Link` on delete, not
`Cascade`.** Deleting a project should return its items to the unassigned bucket,
not silently destroy shortlist work. This is only safe *because* the lookup is
optional — anyone tightening it to required must revisit the cascade behaviour at
the same time.

**Duplicate prevention is app-side.** An alternate key on (Project, Vendor) will
not work, because Dataverse alternate keys do not tolerate a nullable column and
Project is nullable. Before insert, check for an existing row with the same
Vendor *and* the same Project, treating null-Project as its own bucket rather
than as a wildcard — the same vendor legitimately appears in two different
projects.

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

### 3.9 `vca_project`

A sourcing project — the thing a shortlist is *for*. **Dummy data only this
phase:** rows are seeded directly in Dataverse (maker portal or data import), and
no screen creates, edits or opens a project. 7 columns.

| Column | Type | Notes |
|---|---|---|
| Project Name | Single line of text (required) | Primary name column; what the shortlist picker displays |
| Project Code | Single line of text | e.g. "SRC-2026-014" |
| Business Unit | Single line of text | Requesting unit |
| Description | Multiple lines of text | The sourcing need in plain language |
| Status | Choice: Draft / Active / Closed | Display only this phase — there is no project list to filter |
| Start Date | Date only | Display only this phase |
| Target Date | Date only | Display only this phase |

Ownership is not modelled — no Owner column, consistent with `vca_teammember`
being deferred.

#### 3.9.1 Why a table rather than a text column

A free-text project name per shortlist item needs no table, but typos fragment
the grouping silently — "Doc Digitisation" and "Document Digitisation" become two
projects and nobody notices. A lookup against seeded rows makes the set closed
without needing any project management UI to maintain it.

#### 3.9.2 Seed data

Two projects, deliberately different statuses:

- **"Document Digitisation Programme"** — Active, 3 shortlisted vendors
- **"Cloud Migration Phase 2"** — Draft, 2 shortlisted vendors
- Plus 2 shortlist items left unassigned, to prove the bucket renders

That is enough to show grouping works and that Status is carried, without a
project screen to display it on.

---

## 4. Azure AI Search index

Index name `vendor-profiles-index`. One document per vendor. 14 fields.

**Pin `api-version=2024-07-01` or later** for every call against this index.
`vectorQueries[].kind: "text"` (§4.3) does not exist before it. `2024-07-01` is
still a supported stable version; `2026-04-01` is the current latest and the
schema below is unchanged on it.

**Key departure from the Empower@BrandName Builders pattern:** that project
hand-built embeddings in a nightly Power Automate loop. This prototype uses
**integrated vectorization** — a Blob data source, a skillset with the
`AzureOpenAIEmbedding` skill, and an `azureOpenAI` **vectorizer declared on the
index**. The vectorizer is the important part: Power Automate sends plain query
text and AI Search embeds it server-side, so the internal search lane needs no
embedding call of its own. No chunking skill — vendor documents are short enough
to embed whole.

The index is only half of it. The data source, skillset and indexer that
*populate* `vendorVector` are specified in
`build_guide/lane1-ai-search-index-build.md`, along with the two settings that
are fixed at creation time and cannot be changed later — the `lowercase`
normalizer on `websiteDomain`, and the explicit `id` key field mapping.

```json
{
  "name": "vendor-profiles-index",
  "fields": [
    { "name": "id", "type": "Edm.String", "key": true, "searchable": false, "filterable": true, "sortable": true, "facetable": false },
    { "name": "vendorName", "type": "Edm.String", "searchable": true, "filterable": true, "sortable": true, "facetable": false },
    { "name": "websiteDomain", "type": "Edm.String", "searchable": true, "filterable": true, "sortable": true, "facetable": false, "normalizer": "lowercase" },
    { "name": "vendorText", "type": "Edm.String", "searchable": true, "retrievable": true, "filterable": false, "sortable": false, "facetable": false },
    { "name": "vendorSummary", "type": "Edm.String", "searchable": true, "retrievable": true, "filterable": false, "sortable": false, "facetable": false },
    { "name": "vendorVector", "type": "Collection(Edm.Single)", "searchable": true, "retrievable": false,
      "dimensions": 3072, "vectorSearchProfile": "vendor-vector-profile" },
    { "name": "vendorStatus", "type": "Edm.String", "searchable": true, "filterable": true, "facetable": true, "sortable": true },
    { "name": "industry", "type": "Edm.String", "searchable": true, "filterable": true, "facetable": true, "sortable": false },
    { "name": "businessDomains", "type": "Collection(Edm.String)", "searchable": true, "filterable": true, "facetable": true },
    { "name": "capabilities", "type": "Collection(Edm.String)", "searchable": true, "filterable": true, "facetable": true },
    { "name": "certifications", "type": "Collection(Edm.String)", "searchable": true, "filterable": true, "facetable": true },
    { "name": "country", "type": "Edm.String", "searchable": true, "filterable": true, "facetable": true, "sortable": true },
    { "name": "headcount", "type": "Edm.Int32", "filterable": true, "sortable": true, "facetable": false },
    { "name": "hasActiveContract", "type": "Edm.Boolean", "filterable": true, "facetable": true }
  ],
  "vectorSearch": {
    "algorithms": [{
      "name": "hnsw-default",
      "kind": "hnsw",
      "hnswParameters": { "metric": "cosine", "m": 4, "efConstruction": 400, "efSearch": 500 }
    }],
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

**Every attribute above is written out on purpose.** The REST API defaults
`Edm.String` to searchable *and* filterable *and* facetable *and* sortable, so
omitting an attribute is not the same as declining it. Two of these matter:

- **`vendorText` is `retrievable: false` and non-filterable.** It is the whole
  embedded blob. Left at defaults it is returned by `select=*`, and filterable
  `Edm.String` carries a hard 32 KB cap that a verbose vendor could one day trip
  — an indexing failure that reads like a data problem.
- **`vendorVector` is `retrievable: false`**, so no query can accidentally pull
  3 072 floats per hit back through Power Automate. `retrievable` is one of the
  few attributes that *can* be flipped later without a rebuild, which is how
  verification 3 inspects the vector. `stored` is deliberately left at its
  default `true`: setting it false saves about 250 KB at this size and would
  make that inspection impossible without a rebuild.

**`websiteDomain` carries the `lowercase` normalizer** because it is the
cross-validation match key (§1.2), and `$filter` on a string field is an exact,
case-sensitive comparison. Without it, `websiteDomain eq 'acmetech.com'` does
not match a stored `ACMETech.com`, and verification 6 fails for a reason that
looks like a matching-logic bug. Normalizers can only be set when the field is
created — adding one later requires a full index rebuild.

**`vendorSummary` exists to serve `vca_searchresult.Summary Snapshot`** (§3.8),
the short description on a result card. Without it the only prose in the index
is `vendorText`, which the internal lane must not select, so internal result
cards would render with no description while external ones — which get theirs
from the Bing grounded answer — render with. It maps from the Dataverse
`Overview` column, truncated at export. It is `searchable: false` so it does not
double-count against `vendorText` in keyword scoring.

### 4.1 `vendorText` composition

The single string that gets embedded. Concatenate in this order:

```
{Vendor Name} ({Legal Name})
Industry: {Industry} | Domains: {Business Domains}
HQ: {HQ Location}, {Country} | Headcount: {Headcount}
Overview: {Overview}
Capabilities: {Capabilities}
Certifications: {Certification Name (Issuer), ...}
Past experience: {Project Name — Outcome Summary; ...}
Regional capacity: {Regional Operating Capacity}
```

Note that `legalName`, `hqLocation` and `regionalOperatingCapacity` are *not*
index fields — they contribute to `vendorText` (and so to semantic matching) but
nothing filters or displays on them, so they need no field of their own.

Keep the whole string under 8 000 tokens. That is the hard input limit on the
`AzureOpenAIEmbedding` skill, and exceeding it is an error, not a truncation.
Nothing in the sample data comes close — a vendor with 20 engagements might.

### 4.2 Blob document contract

One JSON object per vendor, **one blob per vendor**, in the indexed container.
Field names must match the index exactly (camelCase), which is why they differ
from Dataverse display names.

```json
{
  "id": "8f3c1e2a-...",
  "vendorName": "Acme Technologies",
  "websiteDomain": "acmetech.com",
  "vendorSummary": "Boutique document AI firm specialising in intelligent document processing for regulated industries.",
  "vendorText": "Acme Technologies (Acme Technologies Pte Ltd)\nIndustry: ...",
  "vendorStatus": "Registered",
  "industry": "Information Technology",
  "businessDomains": ["Financial Services", "Public Sector"],
  "capabilities": ["Document Intelligence", "RPA"],
  "certifications": ["ISO 27001", "SOC 2 Type II"],
  "country": "Singapore",
  "headcount": 240,
  "hasActiveContract": true
}
```

**This export file is the interface between the data developer and the AI
developer — agree it before either starts.** A camelCase mismatch produces empty
search results with no error.

Three rules the exporter has to honour:

- **`id` is the Dataverse vendor GUID, lowercase, no braces.** Promote-on-action
  (§3.8.1) writes this value back to `vca_searchresult.Vendor`, so if it is
  anything else that link cannot be made. It is also why the indexer needs an
  explicit key field mapping — see the build guide.
- **`websiteDomain` is normalised at export**: lowercased, scheme stripped,
  leading `www.` stripped, no trailing slash or path. The index normalizer
  handles casing on its own, but not `https://` or `www.`.
- **`vendorSummary` is the Dataverse `Overview` text, first sentence or ~200
  characters.** It is display copy, not search copy.

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
  "select": "id,vendorName,vendorSummary,industry,country,websiteDomain,vendorStatus,hasActiveContract,capabilities,certifications",
  "top": 10
}
```

`vendorText` and `vendorVector` are absent from `select` by design *and* by
schema — both are `retrievable: false`, so the omission is enforced rather than
merely documented.

---

## 5. Build order (data developer, day 1)

| # | Work | Est. |
|---|---|---|
| 1 | Solution + publisher prefix `vca_`, choice sets (Industry, Country, Business Domains, Capabilities) | 45 min |
| 2 | `vca_vendor` | 1 h |
| 3 | `vca_certification` (File column), `vca_engagement`, `vca_vendorcontact` | 1 h |
| 4 | Sample vendor load — 25–30 fictional records, including two deliberate near-duplicates | 1.5 h |
| 5 | **Blob JSON export → hand to AI developer** (§4.2) | 1 h |
| 6 | `vca_searchlog` + `vca_searchresult` | 45 min |
| 7 | `vca_lifecycletask` + hand-seeded demo checklists (7 onboarding, 9 offboarding) | 1 h |
| 8 | `vca_project` + 2 seeded project rows | 20 min |
| 9 | `vca_shortlistitem` incl. Project lookup (Remove Link on delete) + seed assignments | 30 min |

Roughly 7.85 hours — a full day with little slack. If sample data arrives late,
steps 7–9 are the ones to push to day 2; they block no other developer.

Keeping projects UI-less is what makes this affordable — a project list and detail
screen would have cost roughly half a day of the UI developer's time for no demo
beat that shortlist grouping does not already deliver.

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
3. **Indexer** — run once; confirm the indexer reports 0 failed documents, that the index document count equals the number of exported blobs, and that `id` on a returned document is the Dataverse GUID rather than a base64 string (if it is base64, the key field mapping is missing). Then flip `vendorVector` to `retrievable: true`, confirm it is non-null and 3 072 long on every document, and flip it back — `retrievable` is changeable without a rebuild.
4. **Vectorizer** — POST the §4.3 query with `vectorQueries.kind: "text"` and no pre-computed embedding. Ranked results back means integrated vectorization works and the internal lane needs no embedding call.
5. **Semantic ranker** — compare a conceptual query ("document processing for government") against keyword-only search. Results should rank differently; identical ordering means the config is not applied.
6. **Cross-validation key** — confirm the two seeded near-duplicates ("Acme Technologies Pte Ltd" / "ACME Tech", same website domain) resolve to the Existing Vendor tag on row 10(e). Seed one of the two with a deliberately messy domain (`https://www.ACMETech.com/`) so this also exercises export-time normalisation and the `lowercase` normalizer, not just the happy path. *`vca_vendor.csv` currently holds only one Acme row — the second is still to be added.*
7. **Lifecycle without flows** — with only hand-seeded rows and no instantiation flow, confirm both dashboards render a part-complete progress bar from `vca_lifecycletask` filtered on Stage, and that a status change persists with a timestamp. This is the check that the all-four-stages rule is met by data rather than by static screens.
8. **Search history replay** — run three searches (one deliberately too vague, so it logs as Rejected). Confirm the history page lists all three newest-first, and that re-opening one renders the original result set with match scores, Existing/New tags and the criteria matrix — read from `vca_searchresult`, with no second call to AI Search or Bing.
9. **Snapshot integrity** — after replaying a past search, edit that vendor's name in Dataverse and reopen the same history entry. It must still show the *old* name from `Vendor Name Snapshot`. If it shows the new one, the page is reading through the lookup instead of the snapshot.
10. **Promote-on-action** — shortlist an un-promoted external result into a project. Confirm a `vca_vendor` row is created with `Source = External Discovery`, `AI Extracted = Yes` and citations copied, that `vca_searchresult.Vendor` is back-filled with the new GUID, and that the shortlist item carries the project.
11. **Project grouping** — shortlist three vendors to one project and two with no project. Confirm the shortlist page groups 3 under the project name and 2 under Unassigned, and that reassigning an unassigned item moves it between groups.
12. **Duplicate guard across projects** — add the same vendor twice to one project (blocked), then that same vendor to a *different* project (allowed) and to the unassigned bucket (allowed). All three must hold. This is the check that null-Project is treated as its own bucket rather than as a wildcard.
13. **Project delete behaviour** — delete a project holding 3 items. The items must survive and appear as unassigned. If they vanish, the relationship is `Cascade` instead of `Remove Link`.
14. **Comparison scoping** — select a project group and hit Compare; confirm the comparison set is that group's vendors, not the whole shortlist.
15. **Label disambiguation** — confirm the Past Experience tab reads "Delivery Project Name", and that no screen shows two fields both labelled "Project Name".
16. **Index refresh** — add a vendor in Dataverse, re-run the export and the indexer, and confirm the new vendor is findable. Then delete a vendor's blob, re-run, and confirm its document is **still in the index**: no deletion detection policy is configured, so removals need a full rebuild. Know which of the two you are doing before a rehearsal — a promoted external vendor (verification 10) is invisible to internal search until the next export, and that is expected, not a bug.

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
| `vca_shortlist` parent | Multiple named shortlists within one project | ~20 min | One implicit shortlist per project is enough |
| Project UI (list, detail, CRUD) | Creating and managing projects in-app instead of seeding them | ~half a day of UI work | No demo beat that shortlist grouping does not already deliver |
| `Project` lookup on `vca_lifecycletask` | Onboarding scoped to the project a vendor was sourced for | ~20 min | Real onboarding usually happens *for* a contract or project — the obvious next step if this model goes past the summit, but not needed for the prototype |
| Vendor `Rating`, `Last Indexed On` | Ratings display, incremental indexing | minutes each | Not in row 2's list columns; full index rebuilds are cheap at this size |

### 7.1 The two worth reconsidering

**Minimal and best-demo diverge in exactly two places**, both about an hour:

- **The Contract Delivery Log** is named in the client brief as a specific onboarding automation. Cutting it is defensible on time, but it should be a stated decision to the client rather than a silent omission.
- **The criteria matrix tables** make the match score explainable under questioning. The score still works without them — but "how was 94% calculated?" is answered from transient JSON rather than data you can point at.
