# Lane 0 build — Intent & Criteria Extraction

The upfront step that runs before Lane 1 and Lane 2 fire. One Azure OpenAI
chat completion, no tools, no conversation state — same "one-shot completion"
idiom as Lane 3 (prototype-scope spec §3), just earlier in the pipeline.
Implements the first half of row 10(c) ("determine core requirements sought")
from `docs/superpowers/specs/2026-07-27-vendorconnect-ai-data-model.md`.
**There is no input-validation/rejection step** — every query is searched;
row 10(a) ("validate input suitability") is explicitly out of scope for now,
by decision, not oversight.

This guide assumes `lane1-ai-search-index-build.md` is done (the index exists
and answers hybrid queries) and reads alongside `lane1-canvas-to-ai-search.md`
— that doc's §2.3–2.5 are the flow steps this one supplies content for. Build
order: this can be built any time after the index exists, but it must be
wired in before Lane 1's HTTP action is demo-ready, since Lane 1 now expects
`varPrimaryIntent` to already be set (§2.6 of that guide).

---

## 0. Prerequisites

| Need | Why | Gotcha |
|---|---|---|
| A chat deployment that supports structured outputs | `response_format: json_schema` needs it | `gpt-4o` or `gpt-4o-mini`. **Not** `gpt-35-turbo` — it silently falls back to plain chat, ignoring `response_format`, and the flow's second Parse JSON then fails on whatever prose comes back |
| `api-version=2024-10-21` or later on the chat completions call | GA structured outputs | Older versions accept the request but return unconstrained JSON (or an error, depending on version) — pin this the same way `lane1-ai-search-index-build.md` pins the search API version |
| 3 environment variables | Endpoint, deployment name, key | `vca_AOAIEndpoint`, `vca_AOAIChatDeployment`, `vca_AOAIKey` — added to `lane1-canvas-to-ai-search.md` §2.2 alongside the existing Search env vars |
| `vendor-profiles-index`'s `scoringProfiles` block already added | The five profile names this step classifies into must exist on the index, or Lane 1 errors with "unknown scoring profile" | See §4 below — already added to the data-model spec |

---

## 1. Why one call, not two

The obvious decomposition is two separate prompts: one to extract criteria,
one to classify intent. Reject that — it doubles the latency added ahead of
Lane 1 (each round trip is 0.5–2s) for no accuracy gain, since both
judgements read the same input and don't depend on each other's output. One
call, one schema, same discipline the Lane 3 prompts already follow
(prototype-scope spec §3: "no tools, no orchestration").

There is also no input-validation step and no accept/reject branch. Every
query gets searched, full stop — if Lane 0 detects nothing distinctive in a
vague or generic query, `primaryIntent` simply comes back `General` (§2.2),
which is a genuine no-op scoring profile, not a rejection. This keeps the
flow to one straight line with no branch to test or demo around.

The scoring-profile mechanism is deliberately **static, not dynamic**. Azure
AI Search also supports per-query "tag" scoring functions, where the flow
passes arbitrary boost values at query time (`scoringParameters`) built from
whatever the model extracted. That would let one query boost several fields
at once (capability *and* certification *and* location) instead of picking a
single dominant one. It was considered and rejected for this build: it needs
the flow to assemble a variable-length parameter array — one join/condition
per category, several of which may be empty — which is exactly the kind of
several-fiddly-low-code-steps failure mode this repo's other build guides
keep flagging (the `fieldMappings` GUID bug, the output-mapping path
mismatch, the semicolon-vs-JSON-array export bug — all silent, all costly on
stage). A static profile is **one string substitution**, directly analogous
to how `triggerBody()?['text']` already gets substituted into the search
body. Losing multi-field boosting on compound queries is a real but bounded
cost: the profile only shifts which candidates land in the top 10 that
hybrid + semantic reranking then sorts properly, it is not the only
relevance signal, and Lane 3's F3 completion still does the real explainable
scoring afterward.

---

## 2. The structured-output call

### 2.1 System prompt

```text
You are the intake classifier for VendorConnect AI's vendor search. You do not
search anything yourself — you read one free-text vendor search query and
produce a single structured judgement about it, used before any search runs.
Every query gets searched; you never reject one, you only classify it.

Do all of the following in one pass:

1. CRITERIA EXTRACTION. Extract each distinct, standalone requirement as a
   short string a vendor profile could be scored against later (e.g.
   "Government experience", "ISO 27001", "Cloud migration experience"). Do
   not invent requirements the query does not state. Maximum 8 criteria.
   Leave empty if the query names no explicit requirement (e.g. a general
   relationship question like "vendors we've worked with").

2. PRIMARY INTENT. Decide which single requirement category the query is
   dominantly about, using this fixed priority when more than one applies:
   Capability > Certification > IndustryOrDomain > Location. If none apply,
   or the query is a general relationship/history question ("vendors we've
   worked with"), the intent is General. Use these category definitions to
   judge which one applies — do not output the matched values, only the
   final category choice below:

   - Capability — the query is about a service/technical capability, e.g.
     Application Development, Business Intelligence, Change Management,
     Cloud Migration, Conversational AI, Cybersecurity Operations, Data
     Engineering, Data Governance, DevOps Automation, Document Intelligence,
     ERP Implementation, Identity & Access Management, Integration & APIs,
     Machine Learning, Managed Services, Network Infrastructure, Penetration
     Testing, RPA, Site Reliability Engineering, Test Automation.
   - Certification — the query names a specific certification or compliance
     standard (e.g. "ISO 27001", "SOC 2", "PCI DSS"). There is no controlled
     list for this one.
   - IndustryOrDomain — the query is about the vendor's own industry (e.g.
     Business Process Outsourcing, Consulting, Cybersecurity, Engineering
     Services, Financial Technology, Information Technology, Professional
     Services, Software Publishing, Telecommunications) or the client sector
     it serves (e.g. Aviation, Education, Energy & Utilities, Financial
     Services, Healthcare, Manufacturing, Public Sector, Retail & Consumer,
     Telecommunications, Transport & Logistics).
   - Location — the query names a specific country (e.g. Australia,
     Belgium, ..., Vietnam). This only matches a vendor's headquarters
     country in the search index, not delivery/regional presence — treat
     "operates in X" and "headquartered in X" the same way here, the
     distinction is handled elsewhere.

   Output exactly one of: "boost-capability", "boost-certification",
   "boost-industry-domain", "boost-location", "General".

3. DISPLAY FIELDS. Choose which vendor fields would be most useful to show
   the user for this specific query, from this fixed list only: vendorName,
   websiteDomain, vendorSummary, vendorStatus, industry, businessDomains,
   capabilities, certifications, country, headcount, hasActiveContract.
   Include whichever field(s) most directly answer the query's intent, then
   add enough other generally-useful fields to give a fuller picture of the
   vendor — always return at least 5 fields, even for a narrow, single-topic
   query. Never list the same field name twice. Do not take the shortcut of
   returning all 11 fields; choose the ones that actually matter for this
   query.

Output strictly the JSON schema provided. Do not add commentary.
```

The category definitions above are informed by the global choices in
`build_guide/prompts.md` §0 (`new_capability`, `new_industry`,
`new_businessdomain`, `new_country`) — they help the model disambiguate
similar-sounding terms across categories (e.g. "Cybersecurity Operations" is
a capability, "Cybersecurity" is an industry). Since only the category name
is emitted now, not the matched values, a drift between this list and the
real choice sets degrades classification quality rather than causing a hard
schema failure — worth a periodic check, not a strict sync requirement.

The 11-field `displayFields` list is exactly the vendor fields available in
Lane 1's own result set — `id` is excluded (an identifier, not something a
user reads) and `vendorText` / `vendorVector` are excluded because they are
`retrievable: false` on the index and never reach the flow at all (data-model
spec §4). `headcount` and `businessDomains` are added to Lane 1's `select`
(`lane1-canvas-to-ai-search.md` §2.6) specifically so this list has something
real to point at — recommending a field the query never actually fetched
would be a silent dead end.

### 2.2 `response_format` schema

Three fields, all consumed downstream (§3). There is no per-category
detection/value breakdown in the output — the model still reasons through
the category definitions in §2.1 to pick `primaryIntent`, it just doesn't
have to emit that reasoning as structured data nobody reads.

```json
{
  "type": "json_schema",
  "json_schema": {
    "name": "vendor_search_intent",
    "strict": true,
    "schema": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "extractedCriteria": {
          "type": "array",
          "items": { "type": "string" },
          "maxItems": 8
        },
        "primaryIntent": {
          "type": "string",
          "enum": [
            "boost-capability", "boost-certification",
            "boost-industry-domain", "boost-location", "General"
          ]
        },
        "displayFields": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": [
              "vendorName", "websiteDomain", "vendorSummary", "vendorStatus",
              "industry", "businessDomains", "capabilities", "certifications",
              "country", "headcount", "hasActiveContract"
            ]
          },
          "minItems": 5,
          "maxItems": 8
        }
      },
      "required": ["extractedCriteria", "primaryIntent", "displayFields"]
    }
  }
}
```

`primaryIntent`'s five enum values are exactly the five `scoringProfiles`
names on the index (§4) — that identity is what lets the flow substitute the
value directly with no lookup/mapping step.

**`uniqueItems` is not a permitted keyword under Azure OpenAI's strict-mode
structured outputs** — including it is a hard `400 invalid_request_error`
("`uniqueItems` is not permitted") at request time, not a soft
best-effort miss, so it must be left out entirely, as above.

**`minItems`/`maxItems` are accepted by schema validation but are not
guaranteed to be behaviorally enforced** — the officially supported JSON
Schema subset for `strict: true` is narrower than full JSON Schema, and
array-length constraints are not consistently honored across API versions
even when the request itself is accepted. Treat them here as documentation of
intent, not a hard guarantee; the actual floor of 5 (and no duplicate field
names) is enforced by the prompt instruction (§2.1), and §5's verification
checks the model actually complies rather than trusting the schema alone.

---

## 3. The flow

Full wiring detail (HTTP action, two-level Parse JSON, the one-line edit to
Lane 1's body) lives in `lane1-canvas-to-ai-search.md` §2.2–2.6 — built there
rather than duplicated here, since it's inserted into that flow, not a flow
of its own. There is **no branch** — Lane 0 always runs and Lane 1 always
follows it. In short:

1. §2.3 — HTTP POST to Azure OpenAI chat completions with the §2.1/§2.2
   prompt and schema above.
2. §2.4 — two-level Parse JSON, because `choices[0].message.content` is
   itself a JSON string.
3. §2.5 — set `varExtractedCriteria`, `varPrimaryIntent` and
   `varDisplayFields` from the parsed result, each with a `coalesce`
   fallback (`"[]"` / `"General"` / a 5-field default list) if the model
   response is missing something, then fall straight through into Lane 1's
   HTTP action. No Condition, no rejection path. `varExtractedCriteria` is
   also passed as an input to Lane 3's prompt (not yet built) so it scores
   against this same list instead of re-deriving one; `varDisplayFields` is
   returned to the canvas app as-is, for it to decide which fields to render
   on each result card. Both are included directly in the flow's response.
   **No Dataverse write happens here** — search-history persistence
   (`vca_searchlog` / `vca_searchresult`)
   is deferred for now; everything goes straight back to the canvas app.
4. §2.6 (Lane 1's own HTTP action) — one line added:
   `"scoringProfile": "@{variables('varPrimaryIntent')}"`, substituted
   unconditionally.

---

## 4. The index change — `scoringProfiles`

Added to `vendor-profiles-index` in
`docs/superpowers/specs/2026-07-27-vendorconnect-ai-data-model.md` §4, as a
sibling of `vectorSearch` and `semantic`:

```json
"scoringProfiles": [
  { "name": "boost-capability", "text": { "weights": { "capabilities": 4 } } },
  { "name": "boost-certification", "text": { "weights": { "certifications": 4 } } },
  { "name": "boost-industry-domain", "text": { "weights": { "industry": 3, "businessDomains": 3 } } },
  { "name": "boost-location", "text": { "weights": { "country": 3 } } },
  { "name": "General", "text": { "weights": { "vendorText": 1, "vendorSummary": 1 } } }
]
```

This is an **in-place index update**, not a rebuild — none of
`capabilities` / `certifications` / `industry` / `businessDomains` /
`country`'s `searchable`/`filterable`/`sortable`/`facetable` attributes
change (unlike the `normalizer` and `dimensions` settings
`lane1-ai-search-index-build.md` §2.1 warns are fixed at creation). Apply via
*Indexes → vendor-profiles-index → Edit JSON*, no delete/recreate, no
indexer reset needed.

Fields omitted from a profile's `weights` default to `1`, so each boost
profile only needs to name the field(s) it's promoting relative to that
baseline. `General` is a deliberate **true no-op** — weight 1 on the two
prose fields is functionally identical to the unweighted default — which is
what licenses Lane 1's unconditional substitution (§3 step 4) instead of a
branch that omits the key.

`text.weights` only reweights the BM25/full-text leg that feeds RRF fusion
alongside the vector leg; it does not touch `vendorVector`'s own ranking,
and with `queryType: semantic` the reranker still makes the final ordering
call from `@search.rerankerScore`. The profile's job is nudging the right
candidates into the top 10 the reranker sees, not guaranteeing a top-result
swap — worth saying out loud before rehearsal so a "no visible change"
result doesn't read as a bug.

Weight values (3–4×) are a starting point, not measured — tune during
rehearsal by comparing a boosted query against the same query with
`scoringProfile` forced to `General` (verification step 6 below).

---

## 5. Verification

1. `curl` the Azure OpenAI chat completions endpoint directly with 5 sample
   queries — one per intent category plus one deliberately vague/generic one
   (e.g. "vendors") — and confirm `extractedCriteria`, `primaryIntent` and
   `displayFields` all look right, before touching Power Automate at all.
2. Confirm a certification-only query (e.g. "PCI DSS compliant vendors")
   classifies as `primaryIntent: "boost-certification"` and the certification
   itself shows up as a string in `extractedCriteria`, despite there being no
   controlled vocabulary for certifications.
3. Confirm `displayFields` on every one of the 5 sample queries has **at
   least 5 entries**, all drawn from the fixed 11-field list, with no
   repeated field name. `uniqueItems` isn't even in the schema (§2.2 —
   Azure OpenAI's strict mode rejects it outright) and `minItems` isn't
   guaranteed enforced either, so this has to be checked by hand rather than
   assumed from the schema — if any response comes back under 5 or repeats a
   field, that's a prompt-tuning problem, not a schema bug. Confirm also
   that a capability-led query's `displayFields` actually includes
   `capabilities` (the model isn't just returning a fixed unrelated set to
   satisfy the count).
4. Confirm a multi-signal query (e.g. "ISO 27001 vendor doing cloud
   migration in Singapore") follows the stated priority order — capability
   wins here, not certification or location.
5. Run the full flow on the vague/generic query end-to-end: there is no
   branch to take, so Lane 1 still fires — confirm `primaryIntent` came back
   `General`, `scoringProfile` in Lane 1's request body reads `"General"`,
   and the canvas app still receives a normal, non-empty result set.
6. Run the full flow on a capability-leaning query and inspect Lane 1's raw
   HTTP request body in run history — confirm
   `"scoringProfile": "boost-capability"` is actually present, not just
   present in Lane 0's output.
7. Re-run the same query with `scoringProfile` temporarily forced to
   `General` and confirm result ordering visibly differs from the boosted
   run — proves the profile does something. Then confirm the generic query
   from step 5 (genuinely `General`-intent) produces ordering identical to
   how Lane 1 behaved before this build — proves the no-op profile is truly
   neutral.
8. Confirm `varDisplayFields` reaches the flow's response output unchanged
   (§2.9 of `lane1-canvas-to-ai-search.md`), and that every field name in it
   corresponds to a key actually present in `colInternal` — i.e. Lane 1's
   `select` (§2.6) and Select reshape (§2.8) both include `headcount` and
   `businessDomains` now, not just the original 9 fields.
9. Once Lane 3 exists: confirm Lane 3 scores against Lane 0's
   `extractedCriteria` array verbatim (passed through as a flow variable)
   rather than re-deriving its own criteria list. Nothing is persisted to
   `vca_searchlog` / `vca_searchresult` at this stage — that write is
   deferred, not part of this verification.
10. Time-box: confirm Lane 0 + Lane 1 + Lane 2 combined stays comfortably
    under the 120-second Power Automate synchronous limit
    (`lane1-canvas-to-ai-search.md` §2.10).

---

## 6. Failure modes

| Symptom | Cause |
|---|---|
| `400 invalid_request_error`: `"'uniqueItems' is not permitted"` | `uniqueItems` was left in the `displayFields` schema — it is not a supported keyword under strict-mode structured outputs at all (not just unenforced). Remove it; §2.2's schema already omits it |
| Flow errors on Lane 0's HTTP action, or the Parse JSON right after it | `response_format: json_schema` unsupported — wrong chat deployment (`gpt-35-turbo`) or `api-version` older than `2024-10-21` |
| `extractedCriteria` always empty on obviously-specific queries | System prompt ambiguity about when to populate vs. leave empty — add a worked example to §2.1 |
| `primaryIntent` ignores the stated priority order on multi-signal queries | Priority rule not reinforced strongly enough in the prompt — add an explicit worked example, same fix as above |
| Outer Parse JSON fails | `choices[]` empty — usually a content filter block. Add a `Configure run after: has failed` branch, same pattern as `lane1-canvas-to-ai-search.md` §2.11, falling back to `varPrimaryIntent = "General"` and `varExtractedCriteria = "[]"` |
| `"Unknown scoring profile"` error from AI Search | `primaryIntent`'s value doesn't match one of the five names in the index's `scoringProfiles` array exactly (case-sensitive) — check §4 was applied to the index actually in use |
| Results identical regardless of detected intent | `scoringProfile` isn't reaching Lane 1's HTTP body — inspect the raw request in run history; usually `varPrimaryIntent` wasn't set before Lane 1's HTTP action ran (§2.5 ordering), or Lane 0's HTTP call itself failed silently |
| Every query gets classified `General`, boosting never visibly kicks in | Re-run the §5 step 1 `curl` tests directly against the chat completions endpoint on a known capability/cert/location query — if `primaryIntent` still comes back `General` there, the category definitions in §2.1 have drifted too far from `prompts.md` §0's actual vocabulary to be recognized |
| Certification strings inconsistently worded ("ISO27001" vs "ISO 27001") | Expected — there's no controlled vocabulary to normalize against. Lane 3 should loose-match, not require exact equality, when scoring against `Extracted Criteria` |
| `displayFields` comes back with fewer than 5 entries | `minItems` on the schema isn't guaranteed enforced (§2.2) — the model is skipping the "at least 5" instruction. Add a worked example to §2.1 showing a narrow query still returning 5 |
| `displayFields` comes back with all 11 fields on every query | The model is taking the "return everything" shortcut the prompt explicitly forbids — tighten §2.1's wording, or lower `maxItems` |
| `displayFields` contains a repeated field name | `uniqueItems` can't be used (see the first row above), so de-duplication is prompt-only (§2.1 already says "never list the same field name twice"). If it still recurs, reinforce with a worked example the same way other prompt-compliance issues in this table are fixed |
| A field named in `displayFields` shows up blank/missing in the canvas app | Lane 1's `select` (§2.6) or Select reshape (§2.8) doesn't actually include that field — check `headcount` and `businessDomains` were added alongside the original 9 |
| Total round-trip creeping toward the 120s limit | Lane 0 latency compounding with lanes 1+2 — keep `max_tokens` low (800 is enough for this schema) and `temperature: 0` |
