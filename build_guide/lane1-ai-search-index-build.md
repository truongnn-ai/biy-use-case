# Lane 1 build — the `vendor-profiles-index` Azure AI Search index

How to stand up the internal search index from nothing: resources, blob export,
index, skillset, indexer, verification. Implements §4 of
`docs/superpowers/specs/2026-07-27-vendorconnect-ai-data-model.md`.

This guide ends where `lane1-canvas-to-ai-search.md` begins. That one assumes a
populated index and wires it to Power Automate and the canvas app. Finish this
one first — its §1 `curl` is the same `curl` that opens the other guide.

```
Dataverse                 Blob Storage              Azure AI Search
─────────                 ────────────              ───────────────
vca_vendor         ──▶    vendor-docs/       ──▶    [data source]
 + certification          <guid>.json                    ↓
 + engagement             (one per vendor)          [skillset]
                                                    AzureOpenAIEmbedding
       §4.2 export contract                              ↓  ──▶ AOAI deployment
                                                    [indexer]
                                                    parsingMode: json
                                                    key mapping: id → id
                                                    output: embedding → vendorVector
                                                         ↓
                                                    [index]
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

| Need | Notes |
|---|---|
| Azure AI Search service, **Basic** tier | Free tier caps you at 3 indexes / 3 indexers, 50 MB, and short indexer runtimes. Semantic ranker itself is *not* the reason — see the note below |
| Storage account + a container, e.g. `vendor-docs` | StorageV2, LRS, public access disabled |
| Azure OpenAI / Foundry resource with a **custom subdomain** | `https://<name>.openai.azure.com`. The skill rejects a generic endpoint |
| A `text-embedding-3-large` deployment | Deployment *name* and *model* both matter — §8 |
| **Admin** key or `Search Service Contributor` | Creating indexes/indexers needs admin. The query key from the other guide is read-only and will 403 here |
| `curl` and `jq` | Every step below is a REST call. The portal can do most of it, but not reproducibly |

> **Correction to `lane1-canvas-to-ai-search.md` §0.** That table says semantic
> ranker is unavailable on Free. It is now available on *all* pricing tiers under
> the default **free billing plan** (a monthly request allowance; requests fail
> with a billing error once it is spent). The **standard** plan requires Basic or
> above. You do not need to enable anything to use the semantic ranker in this
> prototype. Basic is still the right tier, for the index/indexer quota reasons
> above.

### 0.1 Environment

```bash
export SEARCH_SVC="<search-service-name>"
export ADMIN_KEY="<admin-api-key>"
export API="2024-07-01"
export SEARCH="https://${SEARCH_SVC}.search.windows.net"

export AOAI_URI="https://<aoai-resource>.openai.azure.com"
export EMBED_DEPLOYMENT="text-embedding-3-large"

export STORAGE_CONN="DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"
export CONTAINER="vendor-docs"
```

**On `API=2024-07-01`:** it is still a supported stable version and it is the
oldest one where `vectorQueries[].kind: "text"` exists. `2026-04-01` is the
current latest and every payload in this guide is valid on it unchanged. Pin one
version across the index, the skillset, the indexer and the query — mixing them
is a category of bug nobody enjoys.

### 0.2 Grant the search service access to the embedding model

**Do this before anything else.** Both the skill and the vectorizer authenticate
as the search service's managed identity when you omit `apiKey`, and a missing
role assignment surfaces as a 403 *inside indexer execution*, which is a much
worse place to discover it.

```bash
# 1. Turn on the search service's system-assigned identity
az search service update \
  --name "$SEARCH_SVC" --resource-group "<rg>" --identity-type SystemAssigned

PRINCIPAL=$(az search service show \
  --name "$SEARCH_SVC" --resource-group "<rg>" \
  --query identity.principalId -o tsv)

# 2. Give it the embedding model
az role assignment create \
  --assignee-object-id "$PRINCIPAL" --assignee-principal-type ServicePrincipal \
  --role "Cognitive Services OpenAI User" \
  --scope "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<aoai-resource>"
```

Role assignments take a minute or two to propagate. If step 6 fails with 403 on
the first try, wait and re-run before changing anything.

The alternative is an `apiKey` property on both the skill and the vectorizer.
It works, it is one less moving part on day 1, and it puts a live key in two
index definitions that anyone with read access can `GET`. If you take that road,
take it knowingly and rotate afterwards.

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

Twenty files is not a burden when a script writes them.

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

```bash
az storage container create --name "$CONTAINER" --connection-string "$STORAGE_CONN"

az storage blob upload-batch \
  --destination "$CONTAINER" \
  --source ./export \
  --pattern "*.json" \
  --overwrite \
  --connection-string "$STORAGE_CONN"

az storage blob list --container-name "$CONTAINER" \
  --connection-string "$STORAGE_CONN" --query "length(@)"
```

That count is the number the indexer should report in §6. Write it down.

---

## 2. Create the index

The full definition is in data model §4. Save it to `index.json`, substituting
`resourceUri`, then:

```bash
curl -s -X PUT "${SEARCH}/indexes/vendor-profiles-index?api-version=${API}" \
  -H "Content-Type: application/json" -H "api-key: ${ADMIN_KEY}" \
  -d @index.json | jq '{name, fieldCount: (.fields|length)}'
```

Expect `201` and 14 fields.

### 2.1 The three settings you cannot change later

Index attributes split into "flexible" and "rebuild required". Get these wrong
and the fix is `DELETE` the index and start over — cheap now with 20 documents,
annoying at 5 p.m. on day 2.

| Setting | Field | Why it is here |
|---|---|---|
| `"normalizer": "lowercase"` | `websiteDomain` | `$filter` on a string is exact and case-sensitive. `websiteDomain eq 'acmetech.com'` will not match a stored `ACMETech.com`. This field is the cross-validation match key, so that miss is a demo failure (verification 6), not a cosmetic one. Normalizers are assignable **only at field creation** |
| `"dimensions": 3072` | `vendorVector` | Must equal the skill's `dimensions` and the deployment's model output |
| `searchable` / `filterable` / `facetable` / `sortable` | everywhere | Fixed at creation for all four |

`retrievable` is the useful exception — it *can* be changed on an existing index,
which is what makes the vector inspection in §6 possible.

### 2.2 Why every attribute is spelled out

The REST API defaults `Edm.String` to searchable **and** filterable **and**
facetable **and** sortable. Omitting an attribute is not declining it. Left at
defaults, `vendorText` — the concatenated blob of everything — would be
retrievable by `select=*`, facetable (a facet list of 20 unique paragraphs),
sortable, and filterable, which imposes a hard 32 KB cap on the field.

Vector fields are the opposite: via REST they default to `retrievable: false`,
and only the portal wizard flips them true. The explicit `false` in the
definition documents the intent rather than relying on that asymmetry.

---

## 3. Create the data source

```bash
curl -s -X PUT "${SEARCH}/datasources/vendor-blob-datasource?api-version=${API}" \
  -H "Content-Type: application/json" -H "api-key: ${ADMIN_KEY}" \
  -d "{
    \"name\": \"vendor-blob-datasource\",
    \"type\": \"azureblob\",
    \"credentials\": { \"connectionString\": \"${STORAGE_CONN}\" },
    \"container\": { \"name\": \"${CONTAINER}\" }
  }" | jq '.name'
```

No `dataDeletionDetectionPolicy`. That is a decision, not an omission — see §7.

---

## 4. Create the skillset

This is the piece data model §4 named but did not specify. It is what actually
populates `vendorVector`; without it every document indexes with a null vector,
hybrid search silently degrades to keyword-only, and verification 3 fails.

```bash
curl -s -X PUT "${SEARCH}/skillsets/vendor-embedding-skillset?api-version=${API}" \
  -H "Content-Type: application/json" -H "api-key: ${ADMIN_KEY}" \
  -d "{
    \"name\": \"vendor-embedding-skillset\",
    \"description\": \"Embeds vendorText for the vendor-profiles-index\",
    \"skills\": [
      {
        \"@odata.type\": \"#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill\",
        \"name\": \"embed-vendor-text\",
        \"context\": \"/document\",
        \"resourceUri\": \"${AOAI_URI}\",
        \"deploymentId\": \"${EMBED_DEPLOYMENT}\",
        \"modelName\": \"text-embedding-3-large\",
        \"dimensions\": 3072,
        \"inputs\": [ { \"name\": \"text\", \"source\": \"/document/vendorText\" } ],
        \"outputs\": [ { \"name\": \"embedding\", \"targetName\": \"vendorTextVector\" } ]
      }
    ]
  }" | jq '.name'
```

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

---

## 5. Create the indexer

Where the three pieces meet, and where the two mappings that matter live.

```bash
curl -s -X PUT "${SEARCH}/indexers/vendor-profiles-indexer?api-version=${API}" \
  -H "Content-Type: application/json" -H "api-key: ${ADMIN_KEY}" \
  -d '{
    "name": "vendor-profiles-indexer",
    "dataSourceName": "vendor-blob-datasource",
    "skillsetName": "vendor-embedding-skillset",
    "targetIndexName": "vendor-profiles-index",
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
  }' | jq '.name'
```

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

### 5.2 `outputFieldMappings` — note the `/*`

The skill's output is an array, and it lives in the enrichment tree, not in the
source document. Getting it into the index needs an *output* field mapping —
`fieldMappings` cannot see it.

`sourceFieldName` is `/document/vendorTextVector`, matching the `targetName` you
gave the skill output in §4. Microsoft's own sample writes
`/document/embedding/*` for a skill that omits `targetName` (in which case the
node takes the output's name, `embedding`). Either form works; the `/*` suffix
is the array-flattening notation and is harmless here. What is not harmless is
mismatching this path against the skillset's `targetName` — like a bad
`fieldMappings` source, a path that resolves to nothing is skipped **without an
error**, and you get 20 documents with null vectors.

### 5.3 `maxFailedItems: 0`

Default is 0 already; state it anyway. At 20 documents you want the run to stop
and shout on the first bad one, not quietly index 19 and let you find out during
rehearsal that one vendor is unsearchable.

---

## 6. Run and verify

```bash
curl -s -X POST "${SEARCH}/indexers/vendor-profiles-indexer/run?api-version=${API}" \
  -H "api-key: ${ADMIN_KEY}" -H "Content-Length: 0"

# 20-40s later
curl -s "${SEARCH}/indexers/vendor-profiles-indexer/status?api-version=${API}" \
  -H "api-key: ${ADMIN_KEY}" \
  | jq '.lastResult | {status, itemsProcessed, itemsFailed, errors, warnings}'
```

Work down this list. Each step isolates one failure mode, and each one has been
someone's afternoon.

**1 — Documents landed.**

```bash
curl -s "${SEARCH}/indexes/vendor-profiles-index/docs/\$count?api-version=${API}" \
  -H "api-key: ${ADMIN_KEY}"
```

Must equal the blob count from §1.3. Fewer means `itemsFailed`; more means you
indexed a leftover container.

**2 — The key is the GUID.** The §5.1 check, and the cheapest one to run:

```bash
curl -s "${SEARCH}/indexes/vendor-profiles-index/docs?api-version=${API}&search=*&\$top=1&\$select=id,vendorName" \
  -H "api-key: ${ADMIN_KEY}" | jq '.value[0]'
```

A GUID is correct. A base64 string means `fieldMappings` is missing — fix the
indexer, then `POST /reset` before re-running, or unchanged blobs are skipped.

**3 — Vectors are populated.** `vendorVector` is `retrievable: false`, so
temporarily flip it (allowed without a rebuild), look, and flip it back:

```bash
# GET the index, set vendorVector.retrievable = true, PUT it back
curl -s "${SEARCH}/indexes/vendor-profiles-index?api-version=${API}" \
  -H "api-key: ${ADMIN_KEY}" \
  | jq '(.fields[] | select(.name=="vendorVector") | .retrievable) = true' > idx-tmp.json

curl -s -X PUT "${SEARCH}/indexes/vendor-profiles-index?api-version=${API}" \
  -H "Content-Type: application/json" -H "api-key: ${ADMIN_KEY}" -d @idx-tmp.json > /dev/null

curl -s "${SEARCH}/indexes/vendor-profiles-index/docs?api-version=${API}&search=*&\$top=1&\$select=vendorVector" \
  -H "api-key: ${ADMIN_KEY}" | jq '.value[0].vendorVector | length'
```

Expect `3072`. `null` means the skill or the output field mapping is wrong. Then
set `retrievable` back to `false` and PUT again — do not leave it open, or one
`select=*` from a debugging session returns 20 × 3 072 floats through Power
Automate.

**4 — The vectorizer works** (query-time embedding, no vector supplied):

```bash
curl -s -X POST "${SEARCH}/indexes/vendor-profiles-index/docs/search?api-version=${API}" \
  -H "Content-Type: application/json" -H "api-key: ${ADMIN_KEY}" \
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
  -H "Content-Type: application/json" -H "api-key: ${ADMIN_KEY}" \
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

**6 — Semantic reranking actually reorders.** Run step 5 again with `queryType`
and `vectorQueries` removed. If the ordering is identical, the semantic config
is not being applied and you have plain BM25 dressed up.

**7 — The cross-validation key survives casing.** With the second Acme row
seeded (data model verification 6):

```bash
curl -s -X POST "${SEARCH}/indexes/vendor-profiles-index/docs/search?api-version=${API}" \
  -H "Content-Type: application/json" -H "api-key: ${ADMIN_KEY}" \
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
timestamps, so re-uploading a changed vendor and re-running picks it up.
**Deletion detection does not.** No policy is configured, so deleting a blob
leaves its document in the index permanently.

That is the right call here. Native blob soft delete would need soft delete
enabled on the storage account, blob versioning off, and — the awkward part —
the policy in place **from the very first indexer run**. Adding it later does
not retroactively clean up; the docs are explicit that you have to build a new
index. Setting all that up for a 20-document prototype buys nothing.

So there are exactly two refresh procedures. Pick deliberately.

**Vendor added or edited** — re-export, re-upload, re-run:

```bash
az storage blob upload-batch --destination "$CONTAINER" --source ./export \
  --pattern "*.json" --overwrite --connection-string "$STORAGE_CONN"

curl -s -X POST "${SEARCH}/indexers/vendor-profiles-indexer/run?api-version=${API}" \
  -H "api-key: ${ADMIN_KEY}" -H "Content-Length: 0"
```

**Vendor deleted, or the schema changed** — full rebuild, about 90 seconds:

```bash
curl -s -X DELETE "${SEARCH}/indexes/vendor-profiles-index?api-version=${API}" -H "api-key: ${ADMIN_KEY}"
curl -s -X PUT    "${SEARCH}/indexes/vendor-profiles-index?api-version=${API}" \
     -H "Content-Type: application/json" -H "api-key: ${ADMIN_KEY}" -d @index.json
curl -s -X POST   "${SEARCH}/indexers/vendor-profiles-indexer/reset?api-version=${API}" \
     -H "api-key: ${ADMIN_KEY}" -H "Content-Length: 0"
curl -s -X POST   "${SEARCH}/indexers/vendor-profiles-indexer/run?api-version=${API}" \
     -H "api-key: ${ADMIN_KEY}" -H "Content-Length: 0"
```

`reset` is the step people skip. Without it the indexer remembers which blobs it
has already seen and skips them all, and you get an empty index and a successful
run — the most confusing possible combination.

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
| Documents index, `id` is a base64 string | `fieldMappings` omitted. §5.1. Fix, `reset`, re-run |
| `vendorVector` null on every document | `outputFieldMappings` path does not match the skillset's `targetName`. Resolves to nothing, skipped without error. §5.2 |
| Indexer 403 / "access denied" on the skill | Managed identity missing `Cognitive Services OpenAI User`, or the role assignment has not propagated yet. §0.2 |
| `The field 'vendorVector' has dimensions 3072, model produced 1536` | Deployment is `text-embedding-3-small`. Fix the deployment, or drop the index and recreate it at 1536 in *three* places: index field, skill, and nothing else — the vectorizer follows the model |
| Query returns nonsense but no error | Skill and vectorizer point at **different models**. Both must be `text-embedding-3-large`. Nothing validates this; the vectors are simply in different spaces |
| `vectorizer not found` / unknown field | Index created without the `vectorizers` block, or the profile's `vectorizer` name does not match a name in that array |
| `Text is larger than 8,000 tokens` | A `vendorText` that grew past the skill limit. Trim engagement summaries in the exporter, or add a Text Split skill and accept the one-to-many rework |
| Warning "Text is empty", document indexes with no vector | Vendor with a blank Overview and no children. Reject it in the exporter |
| One facet value containing the whole list | Semicolon strings from the CSVs went in where JSON arrays were expected. §1.2 rule 4 |
| Filter on `websiteDomain` misses an obvious match | Scheme or `www.` not stripped at export. The normalizer handles casing only. §6 step 7 |
| Empty result cards in the app, populated externally | `vendorSummary` missing from the export or from `select` |
| Indexer succeeds, index is empty | Re-ran without `reset` after a rebuild. §7 |
| 403 creating the index | Using the query key. Index and indexer operations need the admin key. §0 |

---

## 9. Teardown

```bash
for r in indexers/vendor-profiles-indexer skillsets/vendor-embedding-skillset \
         datasources/vendor-blob-datasource indexes/vendor-profiles-index; do
  curl -s -X DELETE "${SEARCH}/${r}?api-version=${API}" -H "api-key: ${ADMIN_KEY}"
done
```

Delete in that order — an index with a live indexer pointed at it will refuse.
