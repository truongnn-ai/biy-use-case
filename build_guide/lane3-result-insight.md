# Lane 3 (partial) build — per-result AI insight text

The first Lane 3 completion to get built: for each vendor row a search lane
already returned, a short (1–2 sentence) piece of AI-generated text
comparing that vendor to the query the user actually typed, plus one
overall summary describing how well the result set as a whole answers the
query. This is the "reasons" half of F3 ("Ranked results with match % and
reasons",
prototype-scope spec §4) — the "match %" half (a numeric score) is **not**
built here; it stays deferred, same as F7 (duplicate adjudication), F10
(recommendation) and F24 (AI Insights), the other three features tagged
Lane 3 in the scope spec's work split (§7).

Same "one-shot completion" idiom as Lane 0 (`lane0-intent-extraction.md`) —
one Azure OpenAI chat completion, no tools, no conversation state — just
later in the pipeline: this reads Lane 1's *output* rather than feeding
Lane 1's *input*. It reuses Lane 0's Azure OpenAI environment variables
outright; there is nothing new to provision.

This guide assumes `lane0-intent-extraction.md` and
`lane1-canvas-to-ai-search.md` are both built and wired — specifically that
`varExtractedCriteria` is already being set in that flow's §2.5 and, per the
small fix this guide requires there, is now also returned to the canvas app
and captured as `varExtractedCriteria` in Power Fx (§3.2 of that guide).

---

## 0. Prerequisites


| Need                                                                          | Why                                                                               | Gotcha                                                                                                                                                                                                                                                                                              |
| ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Lane 0 + Lane 1 built and wired, including the `extractedCriteria` output fix | Lane 3 scores against Lane 0's criteria list, forwarded through Lane 1's response | If `lane1-canvas-to-ai-search.md` §2.9/§3.2 haven't been updated to return and capture `extractedCriteria`, `varExtractedCriteria` won't exist in the app yet — see that guide's changelog note                                                                                                     |
| The same 3 Azure OpenAI environment variables Lane 0 uses                     | `vca_AOAIEndpoint`, `vca_AOAIChatDeployment`, `vca_AOAIKey`                       | No new provisioning — same resource, same deployment. If Lane 0 works, this works                                                                                                                                                                                                                   |
| `api-version=2024-10-21` or later                                             | Structured outputs (`response_format: json_schema`)                               | Same pin as Lane 0; older versions silently ignore `response_format` or error                                                                                                                                                                                                                       |
| Nothing from Lane 2                                                           | Lane 2 (external/Bing discovery) is not built yet                                 | This guide is written and tested against **internal results only** (Lane 1's output). It's designed to be source-agnostic (§1) so wiring the symmetrical call for `colExternal` later, once Lane 2 exists, needs no changes to the flow or prompt — only a second `.Run()` call from the canvas app |


---

## 1. Why one batched call, source-agnostic

**One call for the whole result list, not one call per vendor.** Same
rejection Lane 0 already gives for splitting one prompt into two
(`lane0-intent-extraction.md` §1): doing 10 sequential completions instead
of 1 adds 10× the round-trip latency for no accuracy gain, since every
vendor is judged against the same query and criteria. A single batched call
also keeps this comfortably inside Power Automate's 120-second synchronous
limit (`lane1-canvas-to-ai-search.md` §2.10), where Lane 3 is one more
flow call stacked on top of whatever lanes 1/2 already cost.

**Matched by `id`, not by position or lane.** The flow doesn't care whether
the rows it's given came from `colInternal`, `colExternal`, or a mix of
both — it takes an array of vendor objects, each with an `id`, and returns
one insight per `id`. This is what lets the same flow be called twice from
the canvas app (once after Lane 1's results land, again after Lane 2's do,
once that lane exists) instead of needing a server-side merge step that
doesn't exist today — Lane 1 and Lane 2 are two independently-timed flow
calls from the canvas app (the F6 staggered-fill pattern,
`lane1-canvas-to-ai-search.md` §3.4), not one flow that returns a combined
set.

**No numeric score in this pass.** `vca_searchresult.Match Score` stays
unpopulated. Adding a score later (the other half of F3) is a schema
addition to §2.2 below, not a redesign — deliberately left out now to keep
this guide's scope to exactly what was asked: insight text.

---

## 2. The structured-output call

### 2.1 System prompt

```text
You are a search-result annotator for VendorConnect AI's vendor search. You
do not search anything yourself — you read the user's original query, a list
of requirements already extracted from it, and a set of vendor profiles a
search has already returned, and you produce two things: one short insight
per vendor giving the specific reason it matches the query, and one overall
summary of the result set as a whole that also names the best-matching
vendor and why.

You will receive:
- query: the user's original free-text search
- criteria: a list of specific requirements already extracted from the query
  (may be empty — a general query has no explicit requirements)
- vendors: a list of vendor objects, each with an id, a vendorName, and the
  fields below

PART A — PER-VENDOR INSIGHTS. For each vendor, write ONE insight:

1. LENGTH AND TONE. One to two sentences, plain prose, no more than about 40
   words. No preamble ("Based on the search results...", "This vendor..."),
   no restating the query back, no bullet points. Write it the way you'd
   describe the fit to a colleague who already knows what they searched for.

2. REASON FOR MATCH. State the specific reason this vendor matches the
   query or the extracted criteria (a capability, certification,
   industry/domain, or location it actually has), and name anything
   relevant the profile does NOT show or leaves unconfirmed. A vendor with a
   strong but partial match should say so plainly rather than reading as
   either uniformly positive or uniformly negative — the reason is the
   point of the insight, not an afterthought.

3. GROUNDING. Only use facts present in the vendor object you were given
   (industry, businessDomains, capabilities, certifications, country,
   headcount, hasActiveContract, vendorSummary). Never invent a capability,
   certification, or location the vendor object doesn't state.

4. CERTIFICATION MATCHING. Certification strings are not normalized (e.g.
   "ISO27001" vs "ISO 27001" vs "ISO/IEC 27001:2022" may all appear). Treat
   these as the same certification when the query or criteria name one —
   loose-match, don't require exact string equality.

5. COVERAGE. Produce exactly one insight per vendor object you were given, in
   the same order, each tagged with that vendor's id and its vendorName
   copied back exactly as given — do not paraphrase or alter the name. Do
   not skip any vendor and do not add vendors that weren't given to you.

PART B — OVERALL SUMMARY. Separately from the per-vendor insights, write ONE
generalSummary describing the result set as a whole against the query: one
to two sentences, same plain-prose rules as PART A. Say whether the set as a
whole is a strong match, a partial/mixed match, or thin coverage for what was
asked — do not just restate that "N vendors were found." Within the same
generalSummary, also name whichever vendor is the best match among the ones
given and state a short reason why (the specific capability, certification,
industry/domain, or location that puts it ahead of the others). Weigh
explicit criteria matches over general fit when judging "best." If nothing
clearly stands out (e.g. a general query with no criteria, or every vendor
is an equally thin match), still name the strongest available vendor and
say plainly that the match is thin, rather than omitting a best match
altogether. This is a single string, not one per vendor, and not a separate
field from the rest of the summary — the best-match callout belongs in the
same generalSummary text, not bolted on as an unrelated fact.

Output strictly the JSON schema provided. Do not add commentary.
```

### 2.2 `response_format` schema

```json
{
  "type": "json_schema",
  "json_schema": {
    "name": "vendor_result_insights",
    "strict": true,
    "schema": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "generalSummary": { "type": "string" },
        "insights": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "id": { "type": "string" },
              "vendorName": { "type": "string" },
              "insight": { "type": "string" }
            },
            "required": ["id", "vendorName", "insight"]
          }
        }
      },
      "required": ["generalSummary", "insights"]
    }
  }
}
```

`vendorName` is echoed back rather than looked up separately — it's what
makes a `Test → Manually` run or a raw `curl` response (§5) human-readable
without cross-referencing GUIDs, and gives the canvas app a second,
belt-and-suspenders field to display or sanity-check against, even though
the actual row merge in §4.1 still keys on `id`. `generalSummary` sits
alongside `insights` at the top level — one string for the whole result
set, not one per vendor.

Same two caveats Lane 0's §2.2 already documents for Azure OpenAI's
strict-mode structured outputs, both apply here too: **no `maxLength` /
sentence-count enforcement in the schema** — the ~40-word, 1–2 sentence
ceiling in §2.1 is a prompt instruction, not a validated constraint, so §5's
verification checks it by hand. And the schema cannot force "exactly one
insight per input vendor, same order, with vendorName copied back
unchanged" either — that's also enforced by §2.1 point 5 alone, checked in
§5.

`temperature: 0`, `max_tokens: 1200` — sized for roughly 10 vendors at
~40 words each (well under the 800 tokens Lane 0 needs for a much larger,
more structured output); raise it if `top` in Lane 1 is ever raised above
10.

---

## 3. The flow — `VCA Lane3 Result Insight`

### 3.1 Trigger — Power Apps (V2)


| Input      | Type | Notes                                                                                                                                     |
| ---------- | ---- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `query`    | Text | The same raw query text passed to Lane 1                                                                                                  |
| `criteria` | Text | JSON string — `varExtractedCriteria` forwarded unchanged from Lane 1's response                                                           |
| `results`  | Text | JSON string — an array of vendor objects, each with `id` plus whatever fields §2.1 needs (see §4.1 for exactly what the canvas app sends) |


### 3.2 HTTP action — the completion call


| Field   | Value                                                                                                                                                                                                                                                                                                                          |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Method  | `POST`                                                                                                                                                                                                                                                                                                                         |
| URI     | `@{parameters('vca_AOAIEndpoint (vca_AOAIEndpoint)')}/openai/deployments/@{parameters('vca_AOAIChatDeployment (vca_AOAIChatDeployment)')}/chat/completions?api-version=2024-10-21`                                                                                                                                             |
| Headers | `Content-Type: application/json` `api-key: @{parameters('vca_AOAIKey (vca_AOAIKey)')}`                                                                                                                                                                                                                                         |
| Body    | `{ "messages": [{ "role": "system", "content": "<§2.1 system prompt>" }, { "role": "user", "content": "@{string(createObject('query', triggerBody()?['text'], 'criteria', triggerBody()?['text_1'], 'vendors', triggerBody()?['text_2']))}" }], "response_format": <§2.2 json_schema>, "temperature": 0, "max_tokens": 1200 }` |


Identical URI/header/env-var pattern to Lane 0's §2.3 — same resource, same
deployment, same reason to pin `api-version=2024-10-21`+. Set **Settings →
Secure Inputs: On**.

The user-message body bundles `query`, `criteria` and `results` into one
JSON object so the model sees them as clearly labeled, related inputs
rather than one flat blob of text — build it with `createObject(...)`
rather than string-concatenating, so `criteria`/`results` (already JSON
strings from the canvas app) nest correctly instead of getting double-
escaped.

### 3.3 Parse JSON — two levels

Same two-level unwrap as Lane 0's §2.4 (`choices[0].message.content` is
itself a JSON string):

1. `Parse_Lane3_Response` — the outer envelope, same shape as Lane 0's
  `Parse_Lane0_Response`.
2. `Parse_Lane3_Content` — a second Parse JSON over
  `first(body('Parse_Lane3_Response')?['choices'])?['message']?['content']`,
   using the `vendor_result_insights` schema from §2.2.

### 3.4 Select — reshape

A **Select** over `body('Parse_Lane3_Content')?['insights']`:


| Key          | Value                                 |
| ------------ | ------------------------------------- |
| `id`         | `item()?['id']`                       |
| `vendorName` | `coalesce(item()?['vendorName'], '')` |
| `insight`    | `coalesce(item()?['insight'], '')`    |


### 3.5 Respond to a PowerApp or flow


| Output           | Type | Value                                                             |
| ---------------- | ---- | ----------------------------------------------------------------- |
| `insights`       | Text | `@{string(body('Select'))}`                                       |
| `generalSummary` | Text | `@{coalesce(body('Parse_Lane3_Content')?['generalSummary'], '')}` |


`generalSummary` is read straight off `Parse_Lane3_Content` — it's a single
top-level string, not part of the array the Select reshapes. Same "cannot
return a table, return a JSON string" constraint as Lane 1's §2.9 applies to
`insights` — parse it in the app the same way; `generalSummary` is already
a plain string and needs no `ParseJSON` on the app side.

### 3.6 Failure handling

Add a parallel branch on the HTTP action, *Configure run after → has
failed / timed out*, leading to its own Respond returning `insights = "[]"`. Same pattern as `lane1-canvas-to-ai-search.md` §2.11: a bad
completion here should leave result cards showing no insight text, not an
error banner mid-demo, and it must not block the gallery that already
rendered from Lane 1.

---

## 4. Canvas wiring

### 4.1 Call it right after `colInternal` populates

Appended to the end of `btnSearch.OnSelect`, after the
`Set(varExtractedCriteria, ...)` line added to
`lane1-canvas-to-ai-search.md` §3.2:

```powerappsfx
Set(varLane3Internal,
    'VCA Lane3 Result Insight'.Run(
        txtQuery.Text,
        JSON(varExtractedCriteria),
        JSON(
            ForAll(colInternal, {
                id:              id,
                vendorName:      vendorName,
                vendorSummary:   vendorSummary,
                industry:        industry,
                businessDomains: businessDomains,
                capabilities:    capabilities,
                certifications:  certifications,
                country:         country,
                headcount:       headcount,
                hasActiveContract: hasActiveContract,
                resultSource:    resultSource
            })
        )
    )
);

ForAll(
    Table(ParseJSON(varLane3Internal.insights)) As row,
    UpdateIf(colInternal, id = Text(row.Value.id), { insight: Text(row.Value.insight) })
);

UpdateContext({
    locLane3Status: "Insights ready",
    locGeneralSummary: varLane3Internal.generalSummary
});
```

`**UpdateIf`, not a second `ClearCollect`.** The gallery already rendered
`colInternal` from Lane 1 (§3.2 of `lane1-canvas-to-ai-search.md`) — a
`ClearCollect` here would wipe and re-render every row the instant the
insight call returns, producing a visible flash instead of the field
quietly filling in per row. This is the same staggered-fill intent as F6,
one level lower — the gallery paints first, insight text is a second,
non-blocking pass over rows already on screen.

Add an `insight: Text` column to `colInternal`'s shape (defaulted to `""`
when the row is first created in Lane 1's `ClearCollect`, per
`lane1-canvas-to-ai-search.md` §3.2) so the gallery template has a
consistent field to bind to before Lane 3 returns. `row.Value.vendorName`
is available on each returned row too, but is not used in the `UpdateIf`
match — `id` remains the merge key; `vendorName` is only there for
readability if you inspect `varLane3Internal.insights` directly (e.g. in
the debugger or a temporary label) while wiring this up.

### 4.2 Gallery binding

Bind the card's secondary text to `ThisItem.insight`, and hide/collapse
that control when it's empty (`Visible: !IsBlank(ThisItem.insight)`) so a
still-pending or failed insight call doesn't leave a visibly empty line
on the card.

Bind a label above the gallery (e.g. `lblGeneralSummary.Text`) to
`locGeneralSummary`, with `Visible: !IsBlank(locGeneralSummary)` — this is
the one-line overall read on the result set as a whole, shown once above
all the per-card insights rather than repeated on every card.

### 4.3 Status line

Add `locLane3Status` alongside the existing `locLane1Status` /
`locLane2Status` pair (F6, `lane1-canvas-to-ai-search.md` §3.4) — e.g.
`"Generating match insights…"` while `varLane3Internal` is in flight,
`"Insights ready"` once it resolves. This is purely cosmetic (there's no
timer/stagger trick needed here the way F6's cross-lane one is) but keeps
the same "every async step has a visible status" convention.

### 4.4 Not built yet: the external-results call

Once Lane 2 exists and `colExternal` is populated, the same pattern
applies unchanged: call `'VCA Lane3 Result Insight'.Run(...)` again,
passing `JSON(colExternal)` instead of `JSON(colInternal)`, and
`UpdateIf(colExternal, ...)` instead. Nothing about the flow or prompt
needs to change — `resultSource` is already a field on both, and the
completion doesn't treat internal/external any differently. This is
future work, not part of this build.

---

## 5. Verification

### 5.1 Sample request body

Logical shape of the HTTP action's body from §3.2, filled in with the 3
vendors from the pasted example response (`value[]`, in the same order AI
Search returned them) and the query that produced them. `criteria` is shown
as Lane 0 would plausibly extract it for this query — pull the real value
from a live run of `lane0-intent-extraction.md` once that's wired, rather
than assuming this exact array.

```json
{
  "messages": [
    {
      "role": "system",
      "content": "<§2.1 system prompt, verbatim>"
    },
    {
      "role": "user",
      "content": "{\"query\":\"I need vendor work in Energy & Utilities domain\",\"criteria\":[\"Energy & Utilities domain experience\"],\"vendors\":[{\"id\":\"dcceb378-ee0e-43d9-ab8d-19bafed0d69e\",\"vendorName\":\"Bayanihan BPO\",\"vendorSummary\":\"Large outsourcing provider handling claims processing and back-office operations, increasingly automation-led.\",\"industry\":\"Business Process Outsourcing\",\"businessDomains\":[\"Energy & Utilities\",\"Public Sector\"],\"capabilities\":[\"Cloud Migration\",\"Cybersecurity Operations\",\"Managed Services\"],\"certifications\":[\"PCI DSS Level 1 Service Provider\",\"ISO 9001:2015\",\"HIPAA Compliance Attestation\",\"ISO/IEC 27001:2022\"],\"country\":\"Philippines\",\"headcount\":3400,\"hasActiveContract\":true,\"resultSource\":\"Internal\"},{\"id\":\"ccf4d9c6-30c1-4958-828a-5c1e9e23df79\",\"vendorName\":\"Maple Ridge Systems\",\"vendorSummary\":\"Public-sector ERP and finance transformation specialist with a bilingual service desk.\",\"industry\":\"Professional Services\",\"businessDomains\":[\"Manufacturing\",\"Energy & Utilities\"],\"capabilities\":[\"ERP Implementation\",\"Integration & APIs\",\"Change Management\"],\"certifications\":[\"ISO/IEC 20000-1:2018\",\"SOC 2 Type II\",\"ISO/IEC 27001:2022\"],\"country\":\"Canada\",\"headcount\":950,\"hasActiveContract\":true,\"resultSource\":\"Internal\"},{\"id\":\"ff685395-2b15-4523-a791-fb3d8eb5bd82\",\"vendorName\":\"Kaizen Digital KK\",\"vendorSummary\":\"Tokyo-based digital engineering house known for continuous-improvement delivery methods and factory floor automation.\",\"industry\":\"Information Technology\",\"businessDomains\":[\"Energy & Utilities\",\"Transport & Logistics\"],\"capabilities\":[\"Data Engineering\",\"Business Intelligence\",\"Machine Learning\"],\"certifications\":[\"ISTQB Partner Programme - Gold\",\"ISO 9001:2015\",\"ISO/IEC 27001:2022\"],\"country\":\"Japan\",\"headcount\":505,\"hasActiveContract\":false,\"resultSource\":\"Internal\"}]}"
    }
  ],
  "response_format": "<§2.2 json_schema, verbatim>",
  "temperature": 0,
  "max_tokens": 1200
}
```

The `user` message's `content` is itself a JSON string (matching §3.2's
`createObject(...)` construction, which produces exactly this shape) —
don't hand-nest `query`/`criteria`/`vendors` as a raw object one level up,
Azure OpenAI's chat completions API only accepts `content` as a string.

To actually run this rather than just read it, build it with `jq` so the
multi-line system prompt and schema don't need manual escaping:

```bash
AOAI_ENDPOINT="https://<foundry-or-aoai-resource>.openai.azure.com"
AOAI_DEPLOYMENT="<chat-deployment-name>"
AOAI_KEY="<key>"

# Paste the §2.1 system prompt as-is into this file.
cat > /tmp/lane3-system-prompt.txt <<'EOF'
You are a search-result annotator for VendorConnect AI's vendor search. ...
EOF

# Paste the §2.2 json_schema object as-is into this file.
cat > /tmp/lane3-response-format.json <<'EOF'
{ "type": "json_schema", "json_schema": { "...": "..." } }
EOF

cat > /tmp/lane3-vendors.json <<'EOF'
[
  { "id": "dcceb378-ee0e-43d9-ab8d-19bafed0d69e", "vendorName": "Bayanihan BPO", "vendorSummary": "Large outsourcing provider handling claims processing and back-office operations, increasingly automation-led.", "industry": "Business Process Outsourcing", "businessDomains": ["Energy & Utilities", "Public Sector"], "capabilities": ["Cloud Migration", "Cybersecurity Operations", "Managed Services"], "certifications": ["PCI DSS Level 1 Service Provider", "ISO 9001:2015", "HIPAA Compliance Attestation", "ISO/IEC 27001:2022"], "country": "Philippines", "headcount": 3400, "hasActiveContract": true, "resultSource": "Internal" },
  { "id": "ccf4d9c6-30c1-4958-828a-5c1e9e23df79", "vendorName": "Maple Ridge Systems", "vendorSummary": "Public-sector ERP and finance transformation specialist with a bilingual service desk.", "industry": "Professional Services", "businessDomains": ["Manufacturing", "Energy & Utilities"], "capabilities": ["ERP Implementation", "Integration & APIs", "Change Management"], "certifications": ["ISO/IEC 20000-1:2018", "SOC 2 Type II", "ISO/IEC 27001:2022"], "country": "Canada", "headcount": 950, "hasActiveContract": true, "resultSource": "Internal" },
  { "id": "ff685395-2b15-4523-a791-fb3d8eb5bd82", "vendorName": "Kaizen Digital KK", "vendorSummary": "Tokyo-based digital engineering house known for continuous-improvement delivery methods and factory floor automation.", "industry": "Information Technology", "businessDomains": ["Energy & Utilities", "Transport & Logistics"], "capabilities": ["Data Engineering", "Business Intelligence", "Machine Learning"], "certifications": ["ISTQB Partner Programme - Gold", "ISO 9001:2015", "ISO/IEC 27001:2022"], "country": "Japan", "headcount": 505, "hasActiveContract": false, "resultSource": "Internal" }
]
EOF

jq -n \
  --rawfile system /tmp/lane3-system-prompt.txt \
  --argjson response_format "$(cat /tmp/lane3-response-format.json)" \
  --arg query "I need vendor work in Energy & Utilities domain" \
  --argjson criteria '["Energy & Utilities domain experience"]' \
  --argjson vendors "$(cat /tmp/lane3-vendors.json)" \
  '{
    messages: [
      { role: "system", content: $system },
      { role: "user", content: ({query: $query, criteria: $criteria, vendors: $vendors} | tostring) }
    ],
    response_format: $response_format,
    temperature: 0,
    max_tokens: 1200
  }' > /tmp/lane3-request-body.json

curl -s -X POST \
  "${AOAI_ENDPOINT}/openai/deployments/${AOAI_DEPLOYMENT}/chat/completions?api-version=2024-10-21" \
  -H "Content-Type: application/json" \
  -H "api-key: ${AOAI_KEY}" \
  -d @/tmp/lane3-request-body.json \
  | jq -r '.choices[0].message.content | fromjson'
```

The final `jq -r '.choices[0].message.content | fromjson'` unwraps the same
two levels §3.3's `Parse_Lane3_Response` / `Parse_Lane3_Content` unwrap in
the flow, printing the `{generalSummary, insights}` object directly instead
of a JSON-string-inside-a-string.

### 5.2 Checklist

1. Run the §5.1 request (or the equivalent for whatever result set is on
   hand). Confirm `insights` comes back with exactly 3 entries, same `id`s
   and `vendorName`s (copied back unchanged, not paraphrased), same order
   as given — and confirm `generalSummary` is present as a single
   non-empty string, not an array or an object.
2. Confirm each insight states a specific reason the vendor matches the
   query (e.g. "matches the Energy & Utilities domain and ISO 27001
   certification requirement") rather than a generic restatement of
   `vendorSummary`, and that `generalSummary` both characterizes the set as
   a whole (strong / partial / thin match) and names one vendor by name as
   the best match, with a short reason — not just a result count.
3. Pick a vendor whose profile does **not** show a specific
   certification/capability the query implies, and confirm its insight
   says so plainly rather than glossing over the gap.
4. Confirm insights stay within roughly 1–2 sentences / 40 words — flag and
  re-tune §2.1 if the model starts padding with preamble
   ("Based on the vendor's profile...").
5. Flow **Test → Manually** with real Lane 1 output as input; confirm the
  HTTP action returns 200, both Parse JSON steps populate, and `insights`
   in the flow's output is a well-formed JSON array string.
6. In the app: confirm the gallery renders internal results first (Lane 1),
  then insight text visibly fills in per card shortly after — not a full
   re-render flash, and not blocking the initial paint.
7. Confirm insight text merges into the **correct** row — deliberately
  check a card whose `id` has an unusual value (e.g. a GUID with no
   dashes stripped) still matches correctly in the `UpdateIf`.
8. Kill it deliberately: point the HTTP URI at a non-existent deployment.
  Confirm cards still render with no insight text and no error banner,
   and `locLane3Status` doesn't get stuck on "Generating…" forever (add a
   timeout/fallback status if it does).

---

## 6. Failure modes


| Symptom                                                                                                | Cause                                                                                                                                                                                                                                                                                           |
| ------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Flow errors on the HTTP action, or the Parse JSON right after it                                       | `response_format: json_schema` unsupported — wrong chat deployment (`gpt-35-turbo`) or `api-version` older than `2024-10-21`. Same failure mode as Lane 0                                                                                                                                       |
| `insights` has fewer or more entries than `vendors` had                                                | §2.1 point 5's "exactly one per vendor" instruction isn't being followed — the schema can't enforce array length here (§2.2). Add a worked example to §2.1, same fix Lane 0's failure-modes table recommends for its own `minItems` gap                                                         |
| A returned `vendorName` doesn't match the input vendor's name (paraphrased, truncated, or reworded)    | §2.1 point 5 says "copied back exactly as given" but the model rewrote it anyway — reinforce with a worked example; this doesn't break the `id`-based merge in §4.1, but signals the model isn't grounding tightly and is worth treating as an early warning for point 3 (GROUNDING) issues too |
| `generalSummary` is missing, empty, or reads as an array/object instead of a string                    | The model didn't follow PART B, or `Parse_Lane3_Content` failed to extract it — check the raw completion body before assuming a flow bug; the `coalesce(...)` in §3.5 only guards against a null/missing key, not a wrong type                                                                  |
| `generalSummary` just restates the result count ("Found 3 vendors matching your query")                | §2.1's PART B instruction to avoid this wasn't followed — add a worked example showing a strong-match vs. thin-coverage `generalSummary` side by side                                                                                                                                           |
| `generalSummary` never names a best-match vendor, or names one without a reason                        | §2.1 PART B's best-match instruction wasn't followed strongly enough — reinforce with a worked example showing the callout inline (e.g. "...; Maple Ridge Systems is the strongest fit here given its Energy & Utilities domain experience and ISO/IEC 27001 certification.")                  |
| No card ever gets insight text, but the flow returns 200                                               | An `id` mismatch between what was sent to Lane 3 and what `UpdateIf` matches on in §4.1 — check for a type mismatch (`Text(row.Value.id)` vs. an untyped comparison)                                                                                                                            |
| Insights are generic ("This vendor may be a good fit") regardless of vendor                            | §2.1's grounding instruction (point 3) isn't being followed strongly enough — add a worked contrastive example (one strong match, one partial match) to the prompt                                                                                                                              |
| Insights read as uniformly positive even for weak matches                                              | Same as above — reinforce point 2's "name what's absent or unconfirmed" instruction with an example that explicitly calls out a gap                                                                                                                                                             |
| Insights ignore `criteria` entirely, only reference `query` text                                       | The `criteria` array wasn't reaching the model — check `varExtractedCriteria` is actually non-empty going in (confirm the `lane1-canvas-to-ai-search.md` §2.9/§3.2 fix was applied) before assuming a prompt problem                                                                            |
| Gallery flashes/re-renders instead of insight text quietly appearing                                   | `ClearCollect` was used instead of `UpdateIf` in §4.1 — check the canvas Power Fx matches §4.1 exactly                                                                                                                                                                                          |
| Certification-based insight misses an obvious match ("ISO27001" query vs "ISO/IEC 27001:2022" profile) | Expected occasionally — there's no controlled vocabulary to normalize against (same note as Lane 0's own failure-modes table). §2.1 point 4 asks the model to loose-match; if it's still missing obvious cases, add a worked example                                                            |
| Total round-trip creeping up                                                                           | Lane 3 is one more synchronous flow call on top of Lane 1 (and eventually Lane 2) — keep `max_tokens` at 1200 unless `top` is raised well above 10, and keep `temperature: 0`                                                                                                                   |


