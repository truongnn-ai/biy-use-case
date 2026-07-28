# Lane 1 wiring — Canvas → Power Automate → Azure AI Search

How the internal search lane is physically connected. Implements F1 (internal
half), F6 (per-lane status) and the query shape in
`docs/superpowers/specs/2026-07-27-vendorconnect-ai-data-model.md` §4.3.

Build this lane **first** — per scope spec §7, it is the path that must work
regardless of Bing provisioning or venue network.

```
Canvas app                Power Automate                Azure
──────────                ──────────────                ─────
btnSearch.OnSelect        [Power Apps (V2)] trigger
  └ 'VCA Lane1'.Run(q) ─▶   query : Text
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

Three hops, three places it can break. Verify each in order — do not wire the
canvas app until step 1 returns rows from a terminal.

---

## 0. Prerequisites and the licensing fact to check today

| Need | Why | Gotcha |
|---|---|---|
| **HTTP action** in Power Automate | Calls the AI Search REST endpoint | **Premium connector.** Every demo user needs a Power Apps Premium (or per-app) licence. Check this on day 1 — it is a procurement problem, not a code problem. |
| AI Search **Basic** tier or above | Semantic ranker is not available on Free | Semantic ranker has a free 1 000 query/month allowance; a prototype will not exceed it |
| A **query key**, not the admin key | The flow only reads | Portal → your search service → *Settings → Keys → Manage query keys* |
| Index `vendor-profiles-index` populated | — | Blob indexer with integrated vectorization, per data-model spec §4 |

> **Alternative worth knowing:** a canvas app can call a **custom connector**
> directly, with no Power Automate in between. We are not doing that, because
> the bridge flow also merges lane 2, writes `vca_searchlog` / `vca_searchresult`,
> and shapes the response — none of which a raw connector does. But if you ever
> want a pure read with no side effects, that is the cheaper path.

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
    "select": "id,vendorName,industry,country,websiteDomain,vendorStatus,hasActiveContract,capabilities,certifications",
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
- **Do not `select` `vendorText`.** It is the embedded blob of everything and it
  will blow up the response payload.

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

The Key Vault route is the correct one and costs about 20 minutes (vault +
secret + grant the Power Platform service principal `get` on secrets). If that
is blocked on day 1, the pragmatic fallback is a **Text** environment variable
holding the query key, with **Settings → Secure Inputs** turned **on** for the
HTTP action so the key does not appear in run history. Say out loud that this is
a prototype shortcut; do not let it survive into anything real.

Reference in the flow with `@parameters('vca_SearchEndpoint (vca_SearchEndpoint)')`.

### 2.3 HTTP action

| Field | Value |
|---|---|
| Method | `POST` |
| URI | `@{parameters('vca_SearchEndpoint (vca_SearchEndpoint)')}/indexes/vendor-profiles-index/docs/search?api-version=2024-07-01` |
| Headers | `Content-Type: application/json`<br>`api-key: @{parameters('vca_SearchQueryKey (vca_SearchQueryKey)')}` |

Body — note the query text is injected in **two** places, `search` and
`vectorQueries[0].text`:

```json
{
  "search": "@{triggerBody()?['text']}",
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
  "select": "id,vendorName,industry,country,websiteDomain,vendorStatus,hasActiveContract,capabilities,certifications",
  "top": 10
}
```

> `triggerBody()?['text']` is what the V2 trigger names a Text input called
> `query`. Use the dynamic-content picker rather than typing it — V2 input tokens
> are `text`, `text_1`, `number` etc. by position, and hand-typing them is the
> single most common way this flow silently searches for an empty string.

Then **Settings → Secure Inputs: On** on this action.

### 2.4 Parse JSON

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
          "industry":              { "type": "string" },
          "country":               { "type": "string" },
          "websiteDomain":         { "type": "string" },
          "vendorStatus":          { "type": "string" },
          "hasActiveContract":     { "type": "boolean" },
          "capabilities":          { "type": "array", "items": { "type": "string" } },
          "certifications":        { "type": "array", "items": { "type": "string" } }
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

### 2.5 Select — reshape to the canvas contract

A **Select** action over `body('Parse_JSON')?['value']`, mapping to flat fields.
Flatten the arrays here rather than in Power Fx; string handling in the flow is
much less painful than untyped-array handling in the app.

| Key | Value |
|---|---|
| `id` | `item()?['id']` |
| `vendorName` | `item()?['vendorName']` |
| `industry` | `item()?['industry']` |
| `country` | `item()?['country']` |
| `websiteDomain` | `item()?['websiteDomain']` |
| `vendorStatus` | `item()?['vendorStatus']` |
| `hasActiveContract` | `item()?['hasActiveContract']` |
| `capabilities` | `join(coalesce(item()?['capabilities'], createArray()), ', ')` |
| `certifications` | `join(coalesce(item()?['certifications'], createArray()), ', ')` |
| `rerankerScore` | `coalesce(item()?['@search.rerankerScore'], 0)` |
| `resultSource` | `Internal` |

`resultSource` is a literal — it is what drives the source badge in F1/F3 once
lane 2's results are merged alongside.

### 2.6 Respond to a PowerApp or flow

**The constraint that shapes everything above:** this action can only return
Text, Number, Boolean, Date, Email or Yes/No. **It cannot return a table.** So
return the result set as a JSON *string* and parse it in the app.

| Output | Type | Value |
|---|---|---|
| `results` | Text | `@{string(body('Select'))}` |
| `resultCount` | Number | `@{length(body('Select'))}` |
| `durationMs` | Number | `@{div(sub(ticks(utcNow()), variables('startTicks')), 10000)}` |

`durationMs` feeds `vca_searchlog.Duration Ms`. Set `startTicks` with an
*Initialize variable* right after the trigger.

### 2.7 Two limits to design around

- **120 seconds.** A flow called synchronously from Power Apps must respond
  within about two minutes or the call fails. Lane 1 at 2–4s is nowhere near it;
  lane 2 at 5–15s is fine too. Just do not put both lanes in one sequential flow
  and add retries.
- **Response payload size.** Keep `top` at 10 and keep `vendorText` out of the
  `select`. Large strings returned this way get truncated in ways that look like
  a parsing bug in the app.

### 2.8 Failure handling

Add a parallel branch on the HTTP action, *Configure run after → has failed /
timed out*, leading to its own **Respond to a PowerApp or flow** returning
`results = "[]"` and an `errorMessage` output. Without this, a 503 from AI Search
throws an unhandled error in the canvas app mid-demo. With it, the internal
column shows an empty state and lane 2 carries the moment.

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
            industry:          Text(row.Value.industry),
            country:           Text(row.Value.country),
            websiteDomain:     Text(row.Value.websiteDomain),
            vendorStatus:      Text(row.Value.vendorStatus),
            hasActiveContract: Boolean(row.Value.hasActiveContract),
            capabilities:      Text(row.Value.capabilities),
            certifications:    Text(row.Value.certifications),
            rerankerScore:     Value(row.Value.rerankerScore),
            resultSource:      "Internal"
        }
    )
);

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

Which is exactly why §2.5 joins it in the flow instead.

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
2. Flow **Test → Manually** with a typed query — HTTP action shows 200, Parse
   JSON shows a populated `value` array.
3. Flow output `results` is a JSON string starting `[{"id":`, and `resultCount`
   matches the row count.
4. In the app, `varLane1.results` is a non-empty string (check it in a temporary
   label bound to `varLane1.results`, not in the debugger).
5. `colInternal` has rows — *View → Collections*.
6. Gallery renders, sorted with the best semantic match first.
7. Kill it deliberately: point the HTTP URI at a non-existent index. The app
   should show an empty state, not an error banner.

## 5. Common failures and what they actually mean

| Symptom | Cause |
|---|---|
| Flow succeeds, zero results, no error | Query text never reached the body — `triggerBody()?['text']` bound to the wrong V2 input token (§2.3) |
| `Unknown field 'vendorVector'` | Index built without the `vectorizers` block, or `api-version` older than `2024-07-01` |
| Parse JSON fails on one specific query | A null in a field declared non-nullable — apply the nullable fix in §2.4 |
| App gets nothing, flow history looks perfect | Stale flow signature in the app. Remove and re-add the flow |
| `Invalid argument type` on `ClearCollect` | Missing `Text()` / `Value()` cast on an untyped field |
| Everything shows "3% match" | Someone rendered `@search.score` as a percentage. See §1 |
| HTTP action unavailable / licence prompt | Premium connector. See §0 |
