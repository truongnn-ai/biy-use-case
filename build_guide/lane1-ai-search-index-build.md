# Lane 1 build — the `vendor-profiles-index` Azure AI Search index

How to stand up the internal search index from nothing: resources, blob export,
index, skillset, indexer, verification. Implements §4 of
`docs/superpowers/specs/2026-07-27-vendorconnect-ai-data-model.md`.

Built **in the Azure portal**. Every object below is created from *Search
management* in the portal blade. `curl` appears only in §6, for testing — the
same query the Power Automate flow will send, run from a terminal first so you
know the index answers before Power Platform is in the picture.

This guide ends where `lane1-canvas-to-ai-search.md` begins. That one assumes a
populated index and wires it to Power Automate and the canvas app. Finish this
one first.

```
Dataverse                 Blob Storage              Azure AI Search
─────────                 ────────────              ───────────────
vca_vendor         ──▶    vendor-docs/       ──▶    Data sources
 + certification          <guid>.json                    ↓
 + engagement             (one per vendor)          Skillsets
                                                    AzureOpenAIEmbedding
       §4.2 export contract                              ↓  ──▶ Azure OpenAI
                                                                embedding deployment
                                                    Indexers
                                                    parsingMode: json
                                                    key mapping: id → id
                                                    output: embedding → vendorVector
                                                         ↓
                                                    Indexes
                                                    14 fields + vectorizer
                                                    + semantic config
```

Two Azure OpenAI calls, at two different times, easily confused:

| | When | Configured on | Embeds |
|---|---|---|---|
| **Embedding skill** | Indexing | Skillset | `vendorText`, once per vendor |
| **Vectorizer** | Query | Index | The user's query, every search |

They must point at the **same model** or the vectors live in different spaces
and results are noise. Nothing errors when they diverge — see §8.

**Time budget: about 2 hours** if provisioning is already done, of which ~40
minutes is the export script. Build it on day 1; three other things are blocked
on it.

---

## 0. Prerequisites

Create these in the portal first. Nothing below works without all four.

| Resource | Portal path | Notes |
|---|---|---|
| Azure AI Search, **Basic** tier | *Create a resource → AI Search* | Free tier caps you at 3 objects of each type, 50 MB, and 3–10 min indexer runtimes with a skillset. Semantic ranker is *not* the reason — see below |
| Storage account + container `vendor-docs` | *Storage account → Data storage → Containers → + Container* | StorageV2 (general-purpose v2), standard performance. Anonymous access: **Private** |
| Azure OpenAI resource or Foundry project with a **custom subdomain** | *Create a resource → Azure OpenAI*, or a Foundry project | The endpoint must be a custom subdomain — `https://<name>.openai.azure.com`, `services.ai.azure.com` or `cognitiveservices.azure.com`. A generic endpoint is rejected by the skill. (The "must be created in the Azure portal, not Foundry" restriction you may read in the docs applies to the **Import data** wizard, which §0.1 tells you not to use) |
| A `text-embedding-3-large` deployment | *Foundry portal → Deployments → Deploy model* | Note the **deployment name** — it is often different from the model name and you need both |

Write down, from *Search service → Overview* and *Settings → Keys*:

- Search service URL — `https://<svc>.search.windows.net`
- A **query key** (*Manage query keys*) — read-only, all §6 tests use it
- The Azure OpenAI endpoint and the embedding deployment name

> **Leave API keys enabled.** *Search service → Settings → Keys → API access
> control* should stay on **API keys** or **Both**. The §6 tests and the Power
> Automate flow both authenticate with `api-key`; switching to RBAC-only breaks
> them.

> **Correction to `lane1-canvas-to-ai-search.md` §0.** That table used to say
> semantic ranker is unavailable on Free. It runs on *all* pricing tiers under
> the default **free billing plan** (a monthly request allowance; requests fail
> with a billing error once spent). The **standard** plan needs Basic or above.
> You do not need to enable anything to use the semantic ranker here — *Settings
> → Premium features* can stay as it is. Basic is still right, for the object
> quota and runtime reasons above.

### 0.1 Do not use the "Import data" wizard

The portal's headline button on the search service Overview page is **Import
data**, and it does look like exactly this job — blob source, integrated
vectorization, one wizard. It will build the wrong index.

The wizard chunks content (`textSplitMode: pages`, 2 000 characters, 500
overlap, **not configurable**) and generates its own schema: `chunk_id` as the
document key, plus `parent_id`, `chunk`, `title`, `text_vector`. The docs are
explicit that *you can't modify the generated fields or their attributes*. So you
get one document per chunk instead of per vendor, no `websiteDomain`, no
`vendorSummary`, no `hasActiveContract`, and a key that is not the Dataverse
GUID — which is §5.1's failure by another route.

Build the four objects individually from **Search management** instead. It is
four paste operations and it produces the schema the spec asks for.

### 0.2 Managed identity and two role assignments

**Do this before anything else.** The skill, the vectorizer and the data-source
connection all authenticate as the search service's managed identity, and a
missing role surfaces as a 403 *inside indexer execution* — a much worse place
to find it.

**Turn on the identity:**

1. *Search service → Settings → Identity*
2. **System assigned** tab → Status **On** → **Save**
3. Accept the prompt. Copy the **Object (principal) ID** that appears.

**Grant it the embedding model:**

1. Go to your **Azure OpenAI resource** → *Access control (IAM)*
2. **+ Add → Add role assignment**
3. Role: **Cognitive Services OpenAI User** → **Next**
4. Assign access to: **Managed identity** → **+ Select members**
5. Managed identity: **Search service** → pick your service → **Select**
6. **Review + assign**

**Grant it the blob container:**

1. Go to your **Storage account** → *Access control (IAM)*
2. Same flow, role: **Storage Blob Data Reader**, member: your search service

That second one is what lets the data source in §3 connect with a managed
identity instead of a connection string with an account key in it.

Role assignments take a minute or two to propagate. If §6 fails with 403 on the
first attempt, wait and re-run before changing anything.

The alternative to all of this is an `apiKey` on the skill and the vectorizer,
plus a connection string on the data source. It works, it is fewer steps on day
1, and it puts live secrets into three object definitions that anyone with read
access to the service can open. If you take that road, take it knowingly.

---

## 1. Export the vendor documents

One JSON blob per vendor, named `<vendor-guid>.json`, matching §4.2 of the data
model exactly.

### 1.1 Why one blob per vendor and not one array

The tempting shortcut is a single `vendors.json` array with the indexer set to
`parsingMode: jsonArray` — one file to re-upload instead of twenty. Don't.

With any one-to-many parsing mode (`jsonArray`, `jsonLines`, `delimitedText`)
the indexer synthesises its own `AzureSearch_DocumentKey` and base64-encodes it
into your key field. **Your `id` stops being the Dataverse GUID.** Everything
downstream that depends on that GUID breaks: promote-on-action writing back to
`vca_searchresult.Vendor` (data model §3.8.1), the vendor-detail deep link from
a result card, and the F7 dedupe against Dataverse. The docs also explicitly
discourage overriding the key in that mode, because a per-element `id` is not
guaranteed unique *across blobs* even when it is unique within one.

`parsingMode: json` — one blob, one document — has none of that, and it is the
only mode where deletion detection is even available if you later want it.

Twenty files is not a burden when a script writes them and the portal uploads
them in one drag.

### 1.2 The exporter

Owned by the data developer (build order step 5). Whatever produces it — Power
Automate, a script against the Dataverse Web API, a hand-rolled pass over the
CSVs in `build_guide/sample_data/` — it must emit this shape:

```json
{
  "id": "8f3c1e2a-4b5d-4e6f-9a01-2b3c4d5e6f70",
  "vendorName": "Acme Technologies",
  "websiteDomain": "acmetech.com",
  "vendorSummary": "Boutique document AI firm specialising in intelligent document processing for regulated industries.",
  "vendorText": "Acme Technologies (Acme Technologies Pte Ltd)\nIndustry: Information Technology | Domains: Financial Services, Public Sector\nHQ: Singapore, Singapore | Headcount: 240\nOverview: ...\nCapabilities: Document Intelligence, RPA, Machine Learning\nCertifications: ISO/IEC 27001:2022 (BSI Group), SOC 2 Type II (Schellman)\nPast experience: Invoice Intelligence Pilot — Piloted intelligent document processing over 12,000 supplier invoices...\nRegional capacity: Singapore, Malaysia, Indonesia",
  "vendorStatus": "Registered",
  "industry": "Information Technology",
  "businessDomains": ["Financial Services", "Public Sector"],
  "capabilities": ["Document Intelligence", "RPA", "Machine Learning"],
  "certifications": ["ISO/IEC 27001:2022", "SOC 2 Type II"],
  "country": "Singapore",
  "headcount": 240,
  "hasActiveContract": true
}
```

Four rules that are easy to get wrong and silent when you do:

1. **`id` is the raw Dataverse GUID** — lowercase, no braces. AI Search keys
   permit letters, digits, `-`, `_` and `=`, so a bare GUID is fine and a
   `{...}`-wrapped one is not.
2. **`websiteDomain` is normalised**: lowercase, no scheme, no leading `www.`,
   no trailing slash or path. `https://www.ACMETech.com/` → `acmetech.com`. The
   index normalizer lowercases for you but will not strip `https://`.
3. **`vendorText` follows §4.1's field order** and stays under 8 000 tokens —
   the skill's hard input limit, which errors rather than truncates. Roughly
   30 000 characters; nothing in the sample data is near it.
4. **Collections are JSON arrays, not semicolon strings.** The CSVs use
   `Financial Services;Public Sector`; the index wants
   `["Financial Services", "Public Sector"]`. This is the single most common
   export bug, and its symptom is a facet list with one enormous value in it.

An empty `vendorText` is a *warning* from the skill, not an error — the document
indexes with a null vector and then never appears in vector results. Reject
empty `vendorText` in the exporter rather than debugging it in the index.

### 1.3 Upload

1. *Storage account → Data storage → Containers → `vendor-docs`*
2. **Upload** → drag the whole export folder in, or **Browse for files** and
   multi-select all `*.json`
3. Expand **Advanced** and tick **Overwrite if files already exist** — you will
   re-upload these more than once
4. **Upload**

The blob count shown in the container is the number the indexer should report in
§6. Write it down.

---

## 2. Create the index

*Search service → Search management → Indexes → + Add index → **Add index
(JSON)***

Paste the full definition from data model §4, substituting `resourceUri` with
your Azure OpenAI endpoint. **Save**.

Expect 14 fields. If the JSON option is not offered on your portal build, use
**Edit JSON** on the index immediately after creating it — but see §2.1 first,
because most field attributes cannot be changed after creation, so the
definition has to be right the first time.

### 2.1 The three settings you cannot change later

Index attributes split into "flexible" and "rebuild required". Get these wrong
and the fix is deleting the index and starting over — cheap now with 20
documents, annoying at 5 p.m. on day 2.

| Setting | Field | Why it is here |
|---|---|---|
| `"normalizer": "lowercase"` | `websiteDomain` | `$filter` on a string is exact and case-sensitive. `websiteDomain eq 'acmetech.com'` will not match a stored `ACMETech.com`. This field is the cross-validation match key, so that miss is a demo failure (verification 6), not a cosmetic one. Normalizers are assignable **only at field creation** |
| `"dimensions": 3072` | `vendorVector` | Must equal the skill's `dimensions` and the deployment's model output |
| `searchable` / `filterable` / `facetable` / `sortable` | everywhere | Fixed at creation for all four |

`retrievable` is the useful exception — it *can* be changed on an existing index,
which is what makes the vector check in §6 possible from the portal.

The `normalizer` property is a good reason to paste JSON rather than build the
field grid by hand: the visual field editor does not reliably surface it, and a
field created without it looks identical in the grid to one created with it.

### 2.2 Why every attribute is spelled out

The REST API defaults `Edm.String` to searchable **and** filterable **and**
facetable **and** sortable. Omitting an attribute is not declining it. Left at
defaults, `vendorText` — the concatenated blob of everything — would be
retrievable by `select=*`, facetable (a facet list of 20 unique paragraphs),
sortable, and filterable, which imposes a hard 32 KB cap on the field.

Vector fields are the opposite: created through JSON they default to
`retrievable: false`, and only the wizard flips them true. The explicit `false`
in the definition documents the intent rather than relying on that asymmetry.

After saving, open the **Fields** tab and spot-check three rows: `vendorText`
retrievable unticked, `vendorVector` retrievable unticked, `websiteDomain`
filterable ticked.

---

## 3. Create the data source

*Search management → Data sources → + Add data source*

| Field | Value |
|---|---|
| Name | `vendor-blob-datasource` |
| Data source type | **Azure Blob Storage** |
| Subscription / Storage account | yours |
| Blob container | `vendor-docs` |
| Blob folder | *(leave empty)* |
| **Authenticate using managed identity** | **Ticked**, identity type **System-assigned** |
| **Track deletions** | **Unticked** |

Leaving *Track deletions* off is a decision, not an oversight — see §7. The
managed identity checkbox is what depends on the **Storage Blob Data Reader**
assignment from §0.2; without that role this saves fine and then fails at
indexing time with an authorization error.

Parsing mode is **not** on this form. It is an indexer setting — §5.

---

## 4. Create the skillset

*Search management → Skillsets → + Add skillset*

This page is a JSON editor. It is the piece data model §4 named but did not
specify, and it is what actually populates `vendorVector`; without it every
document indexes with a null vector, hybrid search silently degrades to
keyword-only, and verification 3 fails.

Replace `<your-openai-resource>` and `<embedding-deployment-name>`:

```json
{
  "name": "vendor-embedding-skillset",
  "description": "Embeds vendorText for the vendor-profiles-index",
  "skills": [
    {
      "@odata.type": "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill",
      "name": "embed-vendor-text",
      "context": "/document",
      "resourceUri": "https://<your-openai-resource>.openai.azure.com",
      "deploymentId": "<embedding-deployment-name>",
      "modelName": "text-embedding-3-large",
      "dimensions": 3072,
      "inputs": [
        { "name": "text", "source": "/document/vendorText" }
      ],
      "outputs": [
        { "name": "embedding", "targetName": "vendorTextVector" }
      ]
    }
  ]
}
```

**Save**.

Four things to get right:

- **`context: "/document"`** — one embedding per document. There is no chunking
  skill because vendor profiles are short; if you ever add `Text Split`, the
  context becomes `/document/pages/*` and the index needs a one-to-many rethink.
- **`source: "/document/vendorText"`** — with `parsingMode: json`, the JSON's
  top-level properties are promoted to `/document/<name>`. If you left parsing
  mode unset the text would be at `/document/content` instead, and this path
  would silently resolve to nothing.
- **`deploymentId` is the deployment name you typed in Foundry**; `modelName` is
  the underlying model. They are frequently different strings and both are
  required.
- **`dimensions: 3072` must equal the index field's.** Setting it on the skill
  but not the field, or vice versa, is the failure in §8.

No `apiKey` and no `authIdentity` means the system-assigned identity from §0.2.
There is no `cognitiveServices` block because the embedding skill bills through
Azure OpenAI, not through a Foundry multi-service key.

---

## 5. Create the indexer

*Search management → Indexers → + Add indexer*

Where the three pieces meet, and where the two mappings that matter live.
Neither of them is on the visual form, so use the JSON editor.

**An indexer runs immediately when it is created.** Create it with
`"disabled": true`, confirm the definition, then enable and run — otherwise it
fires with an incomplete definition, indexes 20 documents with the wrong key,
and you have to reset it before the fix takes effect.

```json
{
  "name": "vendor-profiles-indexer",
  "dataSourceName": "vendor-blob-datasource",
  "skillsetName": "vendor-embedding-skillset",
  "targetIndexName": "vendor-profiles-index",
  "disabled": true,
  "parameters": {
    "batchSize": 10,
    "maxFailedItems": 0,
    "configuration": {
      "parsingMode": "json",
      "indexedFileNameExtensions": ".json"
    }
  },
  "fieldMappings": [
    { "sourceFieldName": "id", "targetFieldName": "id" }
  ],
  "outputFieldMappings": [
    { "sourceFieldName": "/document/vendorTextVector", "targetFieldName": "vendorVector" }
  ]
}
```

Save, reopen it via **Edit JSON**, set `"disabled": false`, save again. Then §6.

Note that **this is the point where data first moves.** Everything up to here —
index, data source, skillset, indexer — has been definitions only, and the index
has held zero documents. Indexers run on creation *and on update*, so flipping
`disabled` to false is likely to start a run on its own. If §6's **Run** then
reports 0/0 documents processed against a populated index, that is why, and
nothing is wrong.

### 5.1 `fieldMappings` — the one that costs you the GUID

**This mapping is not optional, and leaving it out fails silently.**

When a blob indexer finds no explicit mapping for the key field, it defaults to
mapping `metadata_storage_path` — base64-encoded — into it. Your carefully
exported Dataverse GUID is discarded and `id` comes back as
`aHR0cHM6Ly9zdG9yYWdl...`. Nothing errors. Documents index. Search works. And
then promote-on-action cannot write `vca_searchresult.Vendor`, the result card
cannot deep-link to the vendor detail screen, and F7 cannot match against
Dataverse — three separate bugs from one omitted line, discovered separately.

Every other field maps by name automatically, because the JSON property names
were chosen to equal the index field names. This is the one exception.

### 5.2 `outputFieldMappings` — note the path

The skill's output is an array, and it lives in the enrichment tree, not in the
source document. Getting it into the index needs an *output* field mapping —
`fieldMappings` cannot see it.

`sourceFieldName` is `/document/vendorTextVector`, matching the `targetName` you
gave the skill output in §4. Microsoft's own sample writes
`/document/embedding/*` for a skill that omits `targetName` (in which case the
node takes the output's name, `embedding`). Either form works. What is not
harmless is mismatching this path against the skillset's `targetName` — like a
bad `fieldMappings` source, a path that resolves to nothing is skipped
**without an error**, and you get 20 documents with null vectors.

### 5.3 `maxFailedItems: 0`

Default is 0 already; state it anyway. At 20 documents you want the run to stop
and shout on the first bad one, not quietly index 19 and let you find out during
rehearsal that one vendor is unsearchable.

---

## 6. Run and verify

*Search management → Indexers → `vendor-profiles-indexer` → **Run***

The page shows status, docs succeeded, and a per-document error/warning list.
Wait for **Success** with `itemsFailed: 0` before going further; a red run here
is a §8 lookup, not something to work around.

Then work down this list. Steps 1–3 are portal; 4–7 are `curl`, because they are
the queries the flow will send and you want them proven outside Power Platform.

Set up for the curl steps:

```bash
export SEARCH="https://<search-service-name>.search.windows.net"
export QUERY_KEY="<query-key>"
export API="2024-07-01"
```

**On `API=2024-07-01`:** it is still a supported stable version and the oldest
one where `vectorQueries[].kind: "text"` exists. `2026-04-01` is the current
latest and every payload here is valid on it unchanged. Pin one version across
the index, the indexer and the query.

**1 — Documents landed.** *Indexes → `vendor-profiles-index`* shows the document
count. It must equal the blob count from §1.3. Fewer means `itemsFailed`; more
means you indexed a leftover container.

**2 — The key is the GUID.** The §5.1 check, and the cheapest one to run. Open
*Indexes → `vendor-profiles-index` → Search explorer*, hit **Search** with the
default `*`, and read the `id` on the first document.

A GUID is correct. A base64 string means `fieldMappings` is missing — fix it via
**Edit JSON**, then **Reset** the indexer before **Run**, or unchanged blobs are
skipped and nothing changes.

**3 — Vectors are populated.** `vendorVector` is `retrievable: false`, so it is
absent from every result. Temporarily flip it — this is the one attribute change
that does not need a rebuild:

1. *Indexes → `vendor-profiles-index` → Fields*
2. Tick **Retrievable** on `vendorVector` → **Save**
3. *Search explorer* → **Query options** → untick *Hide vector values in search
   results* → **Search**
4. Confirm a long float array on every document
5. Go back to **Fields**, untick **Retrievable**, **Save**

Missing or null means the skill or the output field mapping is wrong. Do not
leave retrievable on — one `select=*` from a later debugging session would pull
3 072 floats per hit through Power Automate.

Note that *Hide vector values in search results* is a **display** toggle in
Search explorer. It does not override `retrievable: false`; with retrievable off
there is nothing to hide either way. Both steps are needed.

**4 — The vectorizer works** — query-time embedding, no vector supplied:

```bash
curl -s -X POST "${SEARCH}/indexes/vendor-profiles-index/docs/search?api-version=${API}" \
  -H "Content-Type: application/json" -H "api-key: ${QUERY_KEY}" \
  -d '{
    "vectorQueries": [{ "kind": "text", "text": "document processing for government",
                        "fields": "vendorVector", "k": 5 }],
    "select": "vendorName,industry"
  }' | jq '.value[] | {vendorName, score: ."@search.score"}'
```

Ranked results mean integrated vectorization is live and the Power Automate lane
never needs an embedding call. A `vectorizer not found` or 403 sends you back to
§0.2 or the index's `vectorizers` block.

**5 — The full hybrid + semantic query.** This is the exact payload the flow
sends, and the opening `curl` of `lane1-canvas-to-ai-search.md` §1:

```bash
curl -s -X POST "${SEARCH}/indexes/vendor-profiles-index/docs/search?api-version=${API}" \
  -H "Content-Type: application/json" -H "api-key: ${QUERY_KEY}" \
  -d '{
    "search": "document digitisation vendor with government experience",
    "queryType": "semantic",
    "semanticConfiguration": "vendor-semantic-config",
    "vectorQueries": [{ "kind": "text", "text": "document digitisation vendor with government experience",
                        "fields": "vendorVector", "k": 10 }],
    "select": "id,vendorName,vendorSummary,industry,country,websiteDomain,vendorStatus,hasActiveContract,capabilities,certifications",
    "top": 10
  }' | jq '.value[] | {vendorName, vendorSummary, r: ."@search.rerankerScore"}'
```

Every hit needs a non-null `@search.rerankerScore` (0–4) and a non-empty
`vendorSummary`. A null reranker score means `queryType` or
`semanticConfiguration` did not take. An empty `vendorSummary` means the
exporter skipped it — and it is what the internal result card renders, so it is
visible on stage.

**6 — Semantic reranking actually reorders.** Run step 5 again with `queryType`,
`semanticConfiguration` and `vectorQueries` removed. If the ordering is
identical, the semantic config is not being applied and you have plain BM25
dressed up.

**7 — The cross-validation key survives casing.** With the second Acme row
seeded (data model verification 6):

```bash
curl -s -X POST "${SEARCH}/indexes/vendor-profiles-index/docs/search?api-version=${API}" \
  -H "Content-Type: application/json" -H "api-key: ${QUERY_KEY}" \
  -d '{ "search": "*", "filter": "websiteDomain eq '"'"'acmetech.com'"'"'",
        "select": "vendorName,websiteDomain" }' | jq '.value'
```

Two rows. One row means only one vendor is seeded, or the exporter did not
normalise `https://www.` off the messy one — the normalizer fixes casing, not
scheme or subdomain.

**8 — Do not read `@search.score` as a percentage.** Covered in the other
guide's §1 and repeated because it keeps happening: in hybrid search that value
is an RRF fusion rank, typically 0.01–0.05. Rendering it as a percentage puts
"3% match" beside your best result. Sort on `@search.rerankerScore`; the match %
comes from lane 3.

---

## 7. Refreshing the index

Change detection works automatically — the indexer compares blob `LastModified`
timestamps, so re-uploading a changed vendor and hitting **Run** picks it up.
**Deletion detection does not.** *Track deletions* is off in §3, so deleting a
blob leaves its document in the index permanently.

That is the right call here. Native blob soft delete would need soft delete
enabled on the storage account, blob versioning off, and — the awkward part —
the policy in place **from the very first indexer run**. Adding it later does not
retroactively clean up; the docs are explicit that you have to build a new
index. Setting all that up for a 20-document prototype buys nothing.

So there are exactly two refresh procedures. Pick deliberately.

**Vendor added or edited**

1. *Storage account → Containers → `vendor-docs` → Upload*, overwrite on
2. *Search management → Indexers → `vendor-profiles-indexer` → **Run***

**Vendor deleted, or the schema changed** — about 90 seconds:

1. *Indexes → `vendor-profiles-index` → **Delete***
2. *Indexes → + Add index (JSON)* → paste the definition again
3. *Indexers → `vendor-profiles-indexer` → **Reset***
4. *Indexers → `vendor-profiles-indexer` → **Run***

**Reset is the step people skip.** Without it the indexer remembers which blobs
it has already processed and skips them all, so you get an empty index and a
successful run — the most confusing possible combination. Any time you change
the indexer definition or rebuild the index, reset before running.

Keep the index JSON in the repo next to this guide. Step 2 is a paste, and
retyping a 14-field definition under time pressure is how normalizers go
missing.

### 7.1 What this means during the demo

A vendor promoted from an external find (data model §3.8.1) is written to
Dataverse but **not to the index**, so internal search will not return it until
the next export. This is expected. It is also why data model verification 3
counts *exported blobs* rather than Dataverse rows: after one promote-on-action
run, those two numbers legitimately differ.

Re-run the exporter between rehearsals, not during one.

---

## 8. Failure modes

Ordered by how long each one costs before you work out what it is.

| Symptom | Cause |
|---|---|
| Documents index, `id` is a base64 string | `fieldMappings` omitted. §5.1. Fix, **Reset**, **Run** |
| `vendorVector` null on every document | `outputFieldMappings` path does not match the skillset's `targetName`. Resolves to nothing, skipped without error. §5.2 |
| Index has one document per *chunk*, fields called `chunk_id` / `text_vector` | Built with the **Import data** wizard. §0.1. Delete and start at §2 |
| Indexer 403 / "access denied" calling the skill | Managed identity missing **Cognitive Services OpenAI User**, or the assignment has not propagated. §0.2 |
| Indexer cannot read the container | Managed identity missing **Storage Blob Data Reader**. §0.2 |
| `The field 'vendorVector' has dimensions 3072, model produced 1536` | Deployment is `text-embedding-3-small`. Fix the deployment, or delete the index and recreate it at 1536 in both the index field and the skill |
| Query returns nonsense but no error | Skill and vectorizer point at **different models**. Both must be `text-embedding-3-large`. Nothing validates this; the vectors are simply in different spaces |
| `vectorizer not found` / unknown field | Index created without the `vectorizers` block, or the profile's `vectorizer` name does not match a name in that array |
| `Text is larger than 8,000 tokens` | A `vendorText` that grew past the skill limit. Trim engagement summaries in the exporter, or add a Text Split skill and accept the one-to-many rework |
| Warning "Text is empty", document indexes with no vector | Vendor with a blank Overview and no children. Reject it in the exporter |
| One facet value containing the whole list | Semicolon strings from the CSVs went in where JSON arrays were expected. §1.2 rule 4 |
| Filter on `websiteDomain` misses an obvious match | Scheme or `www.` not stripped at export. The normalizer handles casing only. §6 step 7 |
| Empty result cards in the app, populated externally | `vendorSummary` missing from the export or from `select` |
| Indexer run succeeds, 0/0 documents processed, index **empty** | Re-ran without **Reset** after a rebuild. §7 |
| Indexer run succeeds, 0/0 documents processed, index **populated** | Nothing to do. Change detection found no new or changed blobs — it already ran when you enabled it in §5 |
| Indexer ran before you finished configuring it | Indexers run on creation. Create with `"disabled": true`. §5 |
| 403 on the §6 curl steps | *Keys → API access control* set to RBAC-only, or you used an admin key that has since been rotated. §0 |

Two portal tools worth knowing when the table does not cover it:

- **Debug Sessions** (*Search management → Debug sessions*) runs the skillset
  against a single document and shows the enrichment tree. It is the fastest way
  to see whether `/document/vendorText` and `/document/vendorTextVector` exist
  with the names you think they have.
- The **indexer execution history** on the indexer page keeps per-run warnings,
  not just errors. The "Text is empty" case only ever appears there.

---

## 9. Teardown

*Search management*, deleting in this order — an index with a live indexer
pointed at it will refuse:

1. **Indexers** → `vendor-profiles-indexer` → Delete
2. **Skillsets** → `vendor-embedding-skillset` → Delete
3. **Data sources** → `vendor-blob-datasource` → Delete
4. **Indexes** → `vendor-profiles-index` → Delete

The blob container and the role assignments can stay; they cost nothing and
rebuilding from §2 is faster with them in place.
