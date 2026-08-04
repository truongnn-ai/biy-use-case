# Lane 1 wiring — Canvas → Power Automate → Azure AI Search

How the internal search lane is physically connected. Implements F1 (internal
half), F6 (per-lane status) and the query shape in
`docs/superpowers/specs/2026-07-27-vendorconnect-ai-data-model.md` §4.3.
`§2.3–2.5` below also wire in **Lane 0** (intent & criteria extraction, row
10c) — see `lane0-intent-extraction.md` for that step's prompt, schema and
rationale; this doc only covers where it sits in the flow. There is no
input-validation branch: every query is searched, by decision (see that
guide's §1).

Build this lane **first** — per scope spec §7, it is the path that must work
regardless of Bing provisioning or venue network.

```
Canvas app                Power Automate                        Azure
──────────                ──────────────                        ─────
btnSearch.OnSelect        [Power Apps (V2)] trigger
  └ 'VCA Lane1'.Run(q) ─▶   query : Text
                            ↓
                          [HTTP] POST  ──────────────────────▶  Azure OpenAI
                            ↓                                    chat completions
                          [Parse JSON] x2  ◀────────────────────  (Lane 0)
                            ↓
                          [Set variables: varExtractedCriteria,
                           varPrimaryIntent — no branch, always continues]
                            ↓
                          [HTTP] POST  ──────────────▶  AI Search
                            ↓                            /docs/search
                          [Parse JSON]  ◀──────────────  {"value":[…]}
                            ↓
                          [Select] → reshape
                            ↓
                          [Respond to a PowerApp or flow]
  ParseJSON(result) ◀──────  results : Text  (JSON string)
```

Four hops now, not three. Verify each in order — do not wire the canvas app
until step 1 returns rows from a terminal.

---

## 0. Prerequisites and the licensing fact to check today

| Need | Why | Gotcha |
|---|---|---|
| **HTTP action** in Power Automate | Calls the AI Search REST endpoint | **Premium connector.** Every demo user needs a Power Apps Premium (or per-app) licence. Check this on day 1 — it is a procurement problem, not a code problem. |
| AI Search **Basic** tier or above | Index, indexer and storage quotas — *not* semantic ranker | Semantic ranker now runs on **all** tiers under the default free billing plan (monthly allowance; a prototype will not exceed it). The paid *standard* plan is what needs Basic+. Free tier's real limits are 3 indexes / 3 indexers, 50 MB and capped indexer runtimes |
| A **query key**, not the admin key | The flow only reads | Portal → your search service → *Settings → Keys → Manage query keys* |
| Index `vendor-profiles-index` populated | — | Blob indexer with integrated vectorization. Build it with `lane1-ai-search-index-build.md`; schema in data-model spec §4 |

> **Alternative worth knowing:** a canvas app can call a **custom connector**
> directly, with no Power Automate in between. We are not doing that, because
> the bridge flow also merges lane 2 and shapes the response — neither of
> which a raw connector does. (Writing `vca_searchlog` / `vca_searchresult` was
> the third reason, but persisting search history is deferred for now — see
> §2.5; results go straight to the canvas app and nothing is saved yet.)
> But if you ever want a pure read with no side effects, that is the cheaper
> path.

---

## 1. Prove the index answers before touching Power Platform

Run this from a terminal. If it returns nothing, everything downstream is a
waste of time.

```bash
SEARCH_SVC="<your-service-name>"
QUERY_KEY="<query-key>"

curl -s -X POST \
  "https://${SEARCH_SVC}.search.windows.net/indexes/vendor-profiles-index/docs/search?api-version=2024-07-01" \
  -H "Content-Type: application/json" \
  -H "api-key: ${QUERY_KEY}" \
  -d '{
    "search": "document digitisation vendor with government experience",
    "queryType": "semantic",
    "semanticConfiguration": "vendor-semantic-config",
    "vectorQueries": [
      { "kind": "text", "text": "document digitisation vendor with government experience",
        "fields": "vendorVector", "k": 10 }
    ],
    "select": "id,vendorName,vendorSummary,industry,country,websiteDomain,vendorStatus,hasActiveContract,capabilities,certifications",
    "top": 10
  }' | jq '.value[] | {vendorName, "@search.score", "@search.rerankerScore"}'
```

Notes that matter:

- **`api-version=2024-07-01`** — the GA version where `vectorQueries[].kind: "text"`
  (integrated vectorization at query time) is supported. Older versions silently
  reject it; preview versions exist but pin to GA for a demo.
- **`kind: "text"` is what makes this work without an embedding call.** AI Search
  embeds the query server-side using the vectorizer declared on the index. Power
  Automate sends plain text. If you get an error about the vectorizer, the index
  was created without the `vectorizers` block in §4 of the data-model spec.
- **`vendorText` and `vendorVector` are not selectable.** Both are
  `retrievable: false` in the schema, precisely so nobody can pull the embedded
  blob or 3 072 floats per hit through this flow. Ask for them and you get an
  error rather than a bloated payload.
- **`vendorSummary` is the result card's description.** It is the only prose
  the internal lane returns. Drop it from `select` and internal cards render
  blank next to external ones. (It would also populate
  `vca_searchresult.Summary Snapshot` once search-history persistence is
  built — deferred for now, see §2.5.)

### Scores — read this before building the UI

| Field | Range | Meaning |
|---|---|---|
| `@search.score` | ~0.01–0.05 in hybrid | RRF fusion rank, **not** a relevance percentage |
| `@search.rerankerScore` | 0–4 | Semantic reranker confidence |

Neither is a match %. Do not multiply `@search.score` by 100 — you will render
"3% match" next to your best result. F3's match % comes from lane 3 (a model
completion), per scope spec §4. Sort on `@search.rerankerScore` descending.

---

## 2. The flow — `VCA Lane1 Internal Search`

Create in the same solution as the Dataverse tables so it moves environments
cleanly.

### 2.1 Trigger — Power Apps (V2)

Use **Power Apps (V2)**, not the older "Power Apps" trigger. V2 gives you named,
typed inputs instead of positional `Ask in PowerApps` tokens, which is the
difference between a readable flow and a guessing game on day 3.

| Input | Type | Notes |
|---|---|---|
| `query` | Text | Required. The raw user text |
| `top` | Number | Optional, default 10 |

### 2.2 Store the endpoint and key as environment variables

Solution → *New → More → Environment variable*.

| Name | Type | Value |
|---|---|---|
| `vca_SearchEndpoint` | Text | `https://<svc>.search.windows.net` |
| `vca_SearchQueryKey` | Secret (Azure Key Vault) | Key Vault reference |
| `vca_AOAIEndpoint` | Text | `https://<foundry-or-aoai-resource>.openai.azure.com` |
| `vca_AOAIChatDeployment` | Text | Deployment name of a structured-outputs-capable chat model (`gpt-4o` / `gpt-4o-mini` — see §2.3) |
| `vca_AOAIKey` | Secret (Azure Key Vault) | Key Vault reference |

The Key Vault route is the correct one and costs about 20 minutes (vault +
secret + grant the Power Platform service principal `get` on secrets). If that
is blocked on day 1, the pragmatic fallback is a **Text** environment variable
holding the query key, with **Settings → Secure Inputs** turned **on** for the
HTTP action so the key does not appear in run history. Say out loud that this is
a prototype shortcut; do not let it survive into anything real. The same
fallback applies to `vca_AOAIKey`.

Reference in the flow with `@parameters('vca_SearchEndpoint (vca_SearchEndpoint)')`.

### 2.3 HTTP action — Lane 0 intent & criteria extraction

Runs before Lane 1's own HTTP action (§2.6). Full prompt, schema and
rationale are in `lane0-intent-extraction.md` — this section only covers how
it wires into *this* flow. There is no validation/rejection logic here — this
call only classifies, it never blocks a query from being searched.

| Field | Value |
|---|---|
| Method | `POST` |
| URI | `@{parameters('vca_AOAIEndpoint (vca_AOAIEndpoint)')}/openai/deployments/@{parameters('vca_AOAIChatDeployment (vca_AOAIChatDeployment)')}/chat/completions?api-version=2024-10-21` |
| Headers | `Content-Type: application/json`<br>`api-key: @{parameters('vca_AOAIKey (vca_AOAIKey)')}` |
| Body | `{ "messages": [{ "role": "system", "content": "<lane0-intent-extraction.md system prompt>" }, { "role": "user", "content": "@{triggerBody()?['text']}" }], "response_format": <lane0-intent-extraction.md json_schema>, "temperature": 0, "max_tokens": 800 }` |

Pin `api-version=2024-10-21` or later — this is the GA version where
`response_format: json_schema` (structured outputs) is supported; older
versions either reject it or silently fall back to unconstrained JSON mode.
The deployment behind `vca_AOAIChatDeployment` must support structured
outputs (`gpt-4o` / `gpt-4o-mini`) — `gpt-35-turbo` does not.

Set **Settings → Secure Inputs: On** on this action too, same reason as §2.6.

### 2.4 Parse JSON — two levels

Chat completions nests the structured payload as a **string** inside
`choices[0].message.content` — the same "can't return a table, return a JSON
string and re-parse it" constraint §2.9 already applies to the Respond
action, just one hop earlier.

1. `Parse_Lane0_Response` — schema over the outer envelope:
   `{ "type": "object", "properties": { "choices": { "type": "array", "items": { "type": "object", "properties": { "message": { "type": "object", "properties": { "content": { "type": "string" } } } } } } } }`.
2. `Parse_Lane0_Content` — a second Parse JSON over
   `first(body('Parse_Lane0_Response')?['choices'])?['message']?['content']`,
   using the `vendor_search_intent` schema from `lane0-intent-extraction.md`.

### 2.5 Set flow variables — no validation branch

Lane 0 always runs, and Lane 1 always fires next — there is no accept/reject
Condition. Set three flow variables directly from `Parse_Lane0_Content`, each
with a fallback so a missing or empty field never breaks the flow:

- `varExtractedCriteria` (string) = `string(coalesce(body('Parse_Lane0_Content')?['extractedCriteria'], createArray()))`
- `varPrimaryIntent` (string) = `coalesce(body('Parse_Lane0_Content')?['primaryIntent'], 'General')`
- `varDisplayFields` (string) = `string(coalesce(body('Parse_Lane0_Content')?['displayFields'], createArray('vendorName', 'vendorSummary', 'industry', 'capabilities', 'country')))`

The `coalesce` fallback to `'General'` is what makes this safe even when Lane
0 detects nothing distinctive in the query — `General` is a genuine no-op
scoring profile (data-model spec §4), not a special case the flow has to
branch around. `varDisplayFields`'s fallback is a fixed 5-field default,
picked to be broadly useful (identity, description, sector, capability,
location) if Lane 0's own array ever comes back short or empty — see
`lane0-intent-extraction.md` §2.2 for why the schema's `minItems: 5` can't be
fully trusted on its own.

`varExtractedCriteria` should also be forwarded as an input to Lane 3's
completion prompt (F3/F7, not yet built) so Lane 3 scores the merged results
against this same criteria list rather than re-deriving one, and included
directly in the flow's response so the canvas app can render it (e.g. as
chips above the results). `varDisplayFields` is returned as-is — it tells the
canvas app which of the fields already in `colInternal` (§3.2) to actually
render on each result card, given the query's intent. **No Dataverse write
happens here** — search history persistence (`vca_searchlog` /
`vca_searchresult`) is deferred for now; results go straight back to the
canvas app. If/when persistence gets built, this is the seam where a
`vca_searchlog` write would be added — after lanes 1+2 return, since
`Internal Result Count` / `External Result Count` / `Duration Ms` aren't
known before then.

Then fall straight through into Lane 1's HTTP action (§2.6).

### 2.6 HTTP action — Lane 1 internal search

| Field | Value |
|---|---|
| Method | `POST` |
| URI | `@{parameters('vca_SearchEndpoint (vca_SearchEndpoint)')}/indexes/vendor-profiles-index/docs/search?api-version=2024-07-01` |
| Headers | `Content-Type: application/json`<br>`api-key: @{parameters('vca_SearchQueryKey (vca_SearchQueryKey)')}` |

Body — note the query text is injected in **two** places, `search` and
`vectorQueries[0].text`, and `scoringProfile` is injected from Lane 0's
classification (§2.5):

```json
{
  "search": "@{triggerBody()?['text']}",
  "scoringProfile": "@{variables('varPrimaryIntent')}",
  "queryType": "semantic",
  "semanticConfiguration": "vendor-semantic-config",
  "vectorQueries": [
    {
      "kind": "text",
      "text": "@{triggerBody()?['text']}",
      "fields": "vendorVector",
      "k": 10
    }
  ],
  "select": "id,vendorName,vendorSummary,industry,businessDomains,country,websiteDomain,vendorStatus,hasActiveContract,capabilities,certifications,headcount",
  "top": 10
}
```

> `triggerBody()?['text']` is what the V2 trigger names a Text input called
> `query`. Use the dynamic-content picker rather than typing it — V2 input tokens
> are `text`, `text_1`, `number` etc. by position, and hand-typing them is the
> single most common way this flow silently searches for an empty string.

`scoringProfile` is substituted **unconditionally**, including on `General` —
that only works because `General` is defined as a genuine no-op profile in
the data-model spec's §4 index JSON, not because the key is skipped for it.

`businessDomains` and `headcount` are new here — added specifically so
`varDisplayFields` (§2.5) always has something real to point at. Both are
already fields on the index (data-model spec §4); they just weren't
previously selected because nothing consumed them.

Then **Settings → Secure Inputs: On** on this action.

### 2.7 Parse JSON

Run the flow once, copy the real HTTP body, and use *Generate from sample*. The
schema you want is roughly:

```json
{
  "type": "object",
  "properties": {
    "value": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "@search.score":         { "type": "number" },
          "@search.rerankerScore": { "type": "number" },
          "id":                    { "type": "string" },
          "vendorName":            { "type": "string" },
          "vendorSummary":         { "type": ["string", "null"] },
          "industry":              { "type": "string" },
          "country":               { "type": "string" },
          "websiteDomain":         { "type": "string" },
          "vendorStatus":          { "type": "string" },
          "hasActiveContract":     { "type": "boolean" },
          "capabilities":          { "type": "array", "items": { "type": "string" } },
          "certifications":        { "type": "array", "items": { "type": "string" } },
          "businessDomains":       { "type": "array", "items": { "type": "string" } },
          "headcount":             { "type": ["integer", "null"] }
        }
      }
    }
  }
}
```

**Make every non-key property nullable** — change `"type": "string"` to
`"type": ["string", "null"]` for anything a vendor row might legitimately be
missing. Parse JSON hard-fails the whole flow on a null it was told to expect as
a string, and it will do this to you on the one vendor with no website domain.

### 2.8 Select — reshape to the canvas contract

A **Select** action over `body('Parse_JSON')?['value']`, mapping to flat fields.
Flatten the arrays here rather than in Power Fx; string handling in the flow is
much less painful than untyped-array handling in the app.

| Key | Value |
|---|---|
| `id` | `item()?['id']` |
| `vendorName` | `item()?['vendorName']` |
| `vendorSummary` | `coalesce(item()?['vendorSummary'], '')` |
| `industry` | `item()?['industry']` |
| `country` | `item()?['country']` |
| `websiteDomain` | `item()?['websiteDomain']` |
| `vendorStatus` | `item()?['vendorStatus']` |
| `hasActiveContract` | `item()?['hasActiveContract']` |
| `capabilities` | `join(coalesce(item()?['capabilities'], createArray()), ', ')` |
| `certifications` | `join(coalesce(item()?['certifications'], createArray()), ', ')` |
| `businessDomains` | `join(coalesce(item()?['businessDomains'], createArray()), ', ')` |
| `headcount` | `coalesce(item()?['headcount'], 0)` |
| `rerankerScore` | `coalesce(item()?['@search.rerankerScore'], 0)` |
| `resultSource` | `Internal` |

`resultSource` is a literal — it is what drives the source badge in F1/F3 once
lane 2's results are merged alongside. `businessDomains` and `headcount` are
new — they exist so the canvas app has a real value to render whenever
`varDisplayFields` (§2.5) names one of them for a given query; a query that
never triggers `boost-industry-domain` still gets these two columns in
`colInternal`, just not necessarily surfaced on the card.

### 2.9 Respond to a PowerApp or flow

**The constraint that shapes everything above:** this action can only return
Text, Number, Boolean, Date, Email or Yes/No. **It cannot return a table.** So
return the result set as a JSON *string* and parse it in the app.

| Output | Type | Value |
|---|---|---|
| `results` | Text | `@{string(body('Select'))}` |
| `resultCount` | Number | `@{length(body('Select'))}` |
| `durationMs` | Number | `@{div(sub(ticks(utcNow()), variables('startTicks')), 10000)}` |
| `displayFields` | Text | `@{variables('varDisplayFields')}` |
| `extractedCriteria` | Text | `@{variables('varExtractedCriteria')}` |

`durationMs` is display-only for now (a status-line/debug value in the canvas
app) rather than feeding a `vca_searchlog` write — search history persistence
is deferred, see §2.5. Set `startTicks` with an *Initialize variable* right
after the trigger. `displayFields` and `extractedCriteria` are both JSON
strings (already stringified in §2.5) — `ParseJSON` them in the app the same
way `results` is parsed. `extractedCriteria` was set as a flow variable back
in §2.5 but never actually left the flow until now — it needs to reach the
canvas app so it can be forwarded again, unchanged, as Lane 3's criteria
input (`lane3-result-insight.md`), rather than Lane 3 re-deriving its own
list. There is only one Respond action in this flow now — no validation
branch means no second, rejected-path Respond to keep in sync with it.

### 2.10 Two limits to design around

- **120 seconds.** A flow called synchronously from Power Apps must respond
  within about two minutes or the call fails. Lane 0 (the intent/criteria
  completion, §2.3) typically adds 1–3s ahead of Lane 1's own 2–4s; lane 2 at
  5–15s is still the dominant cost. Just do not put both lanes in one
  sequential flow and add retries.
- **Response payload size.** Keep `top` at 10 and keep `vendorText` out of the
  `select`. Large strings returned this way get truncated in ways that look like
  a parsing bug in the app.

### 2.11 Failure handling

Add a parallel branch on the HTTP action, *Configure run after → has failed /
timed out*, leading to its own **Respond to a PowerApp or flow** returning
`results = "[]"` and an `errorMessage` output. Without this, a 503 from AI Search
throws an unhandled error in the canvas app mid-demo. With it, the internal
column shows an empty state and lane 2 carries the moment. Apply the same
*Configure run after* pattern to Lane 0's HTTP action (§2.3) — a content-filter
block or a malformed completion should fall back to `varPrimaryIntent =
"General"` and `varExtractedCriteria = "[]"` rather than failing the whole flow
(this is the same fallback §2.5's `coalesce` already provides for a
well-formed-but-empty response; this branch covers the HTTP call failing
outright).

---

## 3. The canvas side

### 3.1 Add the flow

Select `btnSearch` → *Power Automate* pane in the left rail → *Add flow* → pick
`VCA Lane1 Internal Search`. Power Apps generates the reference; with spaces in
the name it is quoted: `'VCA Lane1 Internal Search'.Run(...)`.

Re-add the flow after any change to its **inputs or outputs**. The app caches the
signature, and a stale one produces the maddening symptom where the flow run
history shows correct data but the app receives nothing.

### 3.2 Call it and parse the response

```powerappsfx
// btnSearch.OnSelect
UpdateContext({ locLane1Status: "Searching internal catalogue…", locLane1Done: false });

Set(varLane1,
    'VCA Lane1 Internal Search'.Run(txtQuery.Text, 10)
);

ClearCollect(colInternal,
    ForAll(
        Table(ParseJSON(varLane1.results)) As row,
        {
            id:                Text(row.Value.id),
            vendorName:        Text(row.Value.vendorName),
            vendorSummary:     Text(row.Value.vendorSummary),
            industry:          Text(row.Value.industry),
            country:           Text(row.Value.country),
            websiteDomain:     Text(row.Value.websiteDomain),
            vendorStatus:      Text(row.Value.vendorStatus),
            hasActiveContract: Boolean(row.Value.hasActiveContract),
            capabilities:      Text(row.Value.capabilities),
            certifications:    Text(row.Value.certifications),
            businessDomains:   Text(row.Value.businessDomains),
            headcount:         Value(row.Value.headcount),
            rerankerScore:     Value(row.Value.rerankerScore),
            resultSource:      "Internal"
        }
    )
);

Set(varDisplayFields, ParseJSON(varLane1.displayFields));
Set(varExtractedCriteria, ParseJSON(varLane1.extractedCriteria));

UpdateContext({
    locLane1Status: $"Internal catalogue — {CountRows(colInternal)} results",
    locLane1Done: true
});
```

Three Power Fx facts doing the work here:

1. **`Table(ParseJSON(...))`** turns an untyped JSON array into a single-column
   table whose column is named `Value`. Hence `row.Value.vendorName`.
2. **The `As row` alias is not optional in practice.** Without it, nested
   `Value` references collide and you get a compile error that reads as though
   the field does not exist.
3. **Every field needs an explicit cast** — `Text()`, `Value()`, `Boolean()`.
   Untyped objects do not coerce implicitly, and the error message points at the
   collection rather than the field.

If you kept `capabilities` as a JSON array instead of joining it in the flow, the
Power Fx is:

```powerappsfx
capabilities: Concat(Table(row.Value.capabilities) As cap, Text(cap.Value), ", ")
```

Which is exactly why §2.8 joins it in the flow instead.

`varDisplayFields` is a table of field-name strings (e.g.
`["vendorSummary","industry","capabilities","certifications","country"]`) —
`ParseJSON` alone is enough here since it's a flat array of strings, not
nested objects. Test whether a given field should render on a card with
`CountRows(Filter(Table(varDisplayFields), Value = "headcount")) > 0` (or the
`in` operator, depending on app version). `varExtractedCriteria` is the same
shape (a flat array of requirement strings, e.g. `["Government experience",
"ISO 27001"]`) — kept as-is in scope for now, to be passed unchanged into
Lane 3's `.Run()` call (`lane3-result-insight.md`) as its `criteria` input.

### 3.3 Gallery binding

`galInternalResults.Items`:

```powerappsfx
SortByColumns(colInternal, "rerankerScore", SortOrder.Descending)
```

Do **not** put a match % on these cards from `rerankerScore`. Leave the score
field off the internal-only view; the % appears after lane 3 scores the merged
set (F3).

### 3.4 F6 — making the staggered fill actually stagger

The demo beat in scope spec §9 step 2 is internal results landing at ~2–4s while
lane 2 is still running. Power Fx runs a behaviour formula to completion, and the
screen does not reliably repaint mid-chain — so calling both flows in one
`OnSelect` gives you one repaint at the end, and no visible stagger at all.

`Concurrent()` does not solve this either: it starts both in parallel but is a
barrier, returning only when both finish.

The reliable pattern is a zero-duration timer to force a render cycle between the
lanes:

| Control | Property | Value |
|---|---|---|
| `tmrLane2` | `Start` | `locLane1Done` |
| | `Duration` | `0` |
| | `AutoStart` | `false` |
| | `Visible` | `false` |
| | `OnTimerEnd` | the lane 2 `.Run()` call and its `ClearCollect` |

`btnSearch.OnSelect` sets `locLane1Done: true` as its last statement (as above),
the app repaints with lane 1's results, the timer fires, lane 2 starts. The
status line binds to `locLane1Status` / `locLane2Status`, one row per lane.

This is the whole of F6. It is about ten minutes of work and it converts lane 2's
5–15 second wait from dead air into visible progress.

---

## 4. Verification

Work down this list; each step isolates one hop.

1. `curl` from §1 returns ≥1 row with a non-zero `@search.rerankerScore`.
2. Flow **Test → Manually** with a typed query — Lane 0's HTTP action (§2.3)
   shows 200, both Parse JSON steps (§2.4) populate, and §2.5 sets
   `varExtractedCriteria` / `varPrimaryIntent` with no branch to take.
3. Lane 1's HTTP action (§2.6) shows 200, its own Parse JSON (§2.7) shows a
   populated `value` array.
4. Flow output `results` is a JSON string starting `[{"id":`, and `resultCount`
   matches the row count.
5. In the app, `varLane1.results` is a non-empty string (check it in a temporary
   label bound to `varLane1.results`, not in the debugger).
6. `colInternal` has rows — *View → Collections*.
7. Gallery renders, sorted with the best semantic match first.
8. Kill it deliberately: point the HTTP URI at a non-existent index. The app
   should show an empty state, not an error banner.
9. Retest with a deliberately vague/generic query (e.g. "vendors") — there is
   no rejection branch, so Lane 1 and 2 still fire and the app still gets a
   normal result set; confirm `varPrimaryIntent` came back `General` and
   Lane 1's request body shows `"scoringProfile": "General"`.
10. Inspect Lane 1's HTTP request body in run history for a specific query and
    confirm `scoringProfile` is present and matches the query's expected intent
    (e.g. a capability-led query shows `"scoringProfile": "boost-capability"`).
11. Confirm `varLane1.displayFields` is a non-empty JSON array string with at
    least 5 entries, and that `colInternal` actually has a populated (non-blank)
    column for every field name it lists — including `businessDomains` and
    `headcount`, the two fields added to `select` (§2.6) specifically for this.

## 5. Common failures and what they actually mean

| Symptom | Cause |
|---|---|
| Flow succeeds, zero results, no error | Query text never reached the body — `triggerBody()?['text']` bound to the wrong V2 input token (§2.6) |
| `Unknown field 'vendorVector'` | Index built without the `vectorizers` block, or `api-version` older than `2024-07-01` |
| Parse JSON fails on one specific query | A null in a field declared non-nullable — apply the nullable fix in §2.7 |
| App gets nothing, flow history looks perfect | Stale flow signature in the app. Remove and re-add the flow |
| `Invalid argument type` on `ClearCollect` | Missing `Text()` / `Value()` cast on an untyped field |
| Everything shows "3% match" | Someone rendered `@search.score` as a percentage. See §1 |
| HTTP action unavailable / licence prompt | Premium connector. See §0 |
| Flow errors before Lane 1 even runs | Lane 0's `response_format: json_schema` rejected — wrong chat deployment (`gpt-35-turbo`) or `api-version` older than `2024-10-21`. See `lane0-intent-extraction.md` |
| `"Unknown scoring profile"` from AI Search | `varPrimaryIntent` doesn't match one of the five names in the index's `scoringProfiles` array exactly (case-sensitive) |
| Results identical regardless of query intent | `scoringProfile` isn't reaching Lane 1's body — inspect the raw request in run history; usually `varPrimaryIntent` was set after §2.6 already read it, or Lane 0's HTTP call failed silently and §2.11's fallback didn't fire |
| A field named in `displayFields` renders blank on the card | That field isn't in Lane 1's `select` (§2.6) or wasn't mapped in the Select reshape (§2.8) — check `businessDomains` and `headcount` specifically, they're the two most recently added |
| `ParseJSON(varLane1.displayFields)` errors in the app | `displayFields` wasn't stringified before the Respond action — confirm §2.5 wraps it with `string(...)` the same way `varExtractedCriteria` is |
