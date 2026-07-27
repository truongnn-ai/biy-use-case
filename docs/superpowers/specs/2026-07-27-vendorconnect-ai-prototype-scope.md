# VendorConnect AI — Prototype Scope (Vendor Summit)

**Constraint:** 3 calendar days, 3 developers (~9 dev-days, realistically ~8
after provisioning and rehearsal).

**Purpose of this document:** define the narrow slice we build, and state the
*expected completeness* of every feature so nobody discovers on day 3 that two
people assumed different things about the same screen.

---

## 1. Decisions taken

| Decision | Choice |
|---|---|
| Platform | Microsoft Power Platform + Azure |
| Internal source | Client-supplied sample vendor profiles → Dataverse + Azure AI Search |
| External source | **Grounding with Bing Search** (live, no cached fallback) |
| AI architecture | **Three lanes, not one agent** — see §3. Foundry Agent Service is used *only* for external web grounding. |
| Conversational layer | **No Copilot Studio.** Canvas → Power Automate → Azure services |
| Demo robustness | Golden path scripted + free-text search genuinely works on any query |
| Provisioning | Nothing exists yet — provisioned on day 1 |

### Why Bing, not Google/LinkedIn/Gartner

The deck lists Google Search, Gartner Insights, LinkedIn Company Profiles and
industry directories. Scraping any of those is off the table in three days
(and against their terms). Grounding with Bing Search is a first-party Foundry
tool that returns live web results **with citations**, which is what the
"external source" claim actually needs. The other sources appear in the UI as
visible-but-disconnected toggles — see §4, feature F2.

### Why Foundry Agent Service at all — and only here

Microsoft **retired the Bing Search APIs on 11 August 2025** (v7 and Custom
Search, for existing customers as well as new ones). Grounding with Bing Search
inside Azure AI Agents is the designated replacement, and it is deliberately not
a drop-in: it returns *grounded answers with citations* rather than raw SERP
JSON, and it expects the Agent framework wrapped around it.

So Agent Service is a **structural requirement for exactly one capability** —
live external web discovery (F1/F2). There is no longer a REST search endpoint
to call directly from Power Automate. The secondary benefit, on that same
feature, is the managed tool loop.

Everything else in this prototype deliberately bypasses it:

- **Semantic retrieval is Azure AI Search's job**, not Agent Service's. Putting
  an agent in front of it adds a proxy and a model round trip for no capability.
- **Summaries, insights, match rationales and duplicate adjudication are
  one-shot completions** over text we already hold. No tools, no conversation
  state, no orchestration — so no agent.

Reference: [Bing Search API retirement announcement](https://learn.microsoft.com/en-us/lifecycle/announcements/bing-search-api-retirement)

---

## 2. Completeness levels

Every feature below is tagged with one of these. This is the contract.

| Tier | Name | What it means |
|---|---|---|
| **L3** | **Functional** | Real backend, real data, works on arbitrary input the audience supplies. Safe to hand the keyboard to a stranger. |
| **L2** | **Wired** | Real data and real backend, but only exercised along the prepared path / prepared records. Works if you follow the script; may show empty states off it. |
| **L1** | **UI only** | Screens and interactions are real; data is static or stubbed. No backend. This is the tier the brief assigns to anything complex or requiring deep integration. |
| **L0** | **Out of scope** | Not present in the prototype at all. Listed in §6 so the omission is deliberate, not forgotten. |

---

## 3. Architecture (as built for the prototype)

Three independent lanes behind one Power Automate bridge. Each lane uses the
cheapest Azure service that does the job, and no lane depends on another.

```
  Canvas App
  (all screens)
        │
        ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  Power Automate (bridge flows)                               │
  └───┬──────────────────┬──────────────────┬───────────────────┘
      │                  │                  │
   LANE 1             LANE 2             LANE 3
   internal           external           reasoning
   search             search             (no tools)
      │                  │                  │
      ▼                  ▼                  ▼
  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐
  │ Azure AI    │  │ Foundry      │  │ Azure OpenAI     │
  │ Search REST │  │ Agent        │  │ chat completions │
  │             │  │ (Bing        │  │                  │
  │ hybrid +    │  │  Grounding   │  │ F3 match reasons │
  │ semantic    │  │  tool ONLY)  │  │ F7 adjudication  │
  │ ranker      │  │              │  │ F10 recommend    │
  │             │  │ live web +   │  │ F24 AI Insights  │
  │ ~2–4s       │  │ citations    │  │                  │
  └─────────────┘  └──────────────┘  └──────────────────┘

  Dataverse (system of record, read/written directly by the canvas app)
  Vendor · Capability · Certification · Engagement
  Onboarding Task · Offboarding Task · Contract Delivery Log · Checklist Template
```

**Why three lanes rather than one agent with two tools.** The internal search
path is the reliable path — it keeps working if the venue network or Bing fails.
Routing it through the agent loop would have added a model round trip purely to
decide "call AI Search," pushing a 2–4s query into the agent's plausible 5–15s
envelope. Splitting the lanes also means that when something misbehaves during
rehearsal, you are debugging a REST call rather than an opaque
model-decides-which-tool loop.

**Index seeding shortcut:** the internal search index is built by an Azure AI
Search **Blob indexer with integrated vectorization** over a JSON export of the
sample vendor data — not by a hand-built embedding pipeline in Power Automate.
This is roughly a two-hour job instead of a day, and it is the single biggest
time saving in the plan. Dataverse remains the system of record for lifecycle
state (checklists, registration, CDL).

### 3.1 Constraint inherited from Bing Grounding

Grounding with Bing returns **synthesised grounded answers with citation links,
not structured search results.** We cannot pull a clean vendor list from the web
and rank it with deterministic logic of our own. This has one direct scope
consequence, carried into F23: fields on an externally-discovered vendor profile
are model-extracted with citations attached, not reliable structured data. The
profile screen should be built to show provenance rather than imply a verified
record.

---

## 4. Feature scope by stage

All four stages are represented, per the rule.

### Stage 1 — Source Vendors

| ID | Feature | Tier | Notes on what "done" means |
|---|---|---|---|
| F1 | Natural-language vendor search | **L3** | *Lanes 1 + 2, called in parallel.* Free-text query → hybrid semantic + keyword retrieval over the internal index (lane 1), alongside a live Bing-grounded external sweep (lane 2). Results merge in the bridge flow. Any query the audience types returns real ranked results. **This is the headline moment, and the only feature that needs Foundry Agent Service.** |
| F2 | Search source toggles | **L2** | Two sources are real and switchable, one per lane: internal catalogue + Bing. Oracle Supplier Master, Coupa, Gartner, LinkedIn and industry directories render as greyed toggles labelled *"not connected in prototype"* — honest, and it demonstrates the extension point. |
| F3 | Ranked results with match % and reasons | **L3** | *Lane 3.* A single completion scores and explains the merged result set, with a badge showing each vendor's source. Scores are model-generated, not a tuned algorithm — say so if asked. |
| F4 | AI-suggested filters | **L1** | Chips render and are clickable; they filter the returned set client-side only. No re-query, no learned suggestions. |
| F5 | Recent searches | **L2** | Written to and read from Dataverse per user. Cheap, and it makes the landing screen feel lived-in. |
| F6 | Progressive search status | **L2** | *"Searching internal catalogue… searching web…"* step indicator, one line per lane. **Not cosmetic** — lane 1 returns in ~2–4s but lane 2's agent round trip is plausibly 5–15s, so showing internal results the moment they land turns the external wait into visible progress rather than dead air. |

### Stage 2 — Cross-Validate

| ID | Feature | Tier | Notes on what "done" means |
|---|---|---|---|
| F7 | Duplicate / existing-vendor detection | **L3** | *Lane 3.* Deterministic fuzzy name + web-domain match against Dataverse, with a one-shot completion adjudicating near-misses ("Acme Technologies Pte Ltd" vs "ACME Tech"). No agent needed — this is single-turn classification. Works on arbitrary vendors, including ones just discovered via Bing. **Cheapest credibility win in the whole build** — half a day, fully real. |
| F8 | Multi-system validation panel | **L1** | The Found / Registered / Active Contract result rows for Oracle, Coupa and VMO Engine are rendered from the single Dataverse record, presented as if from three systems. Deep integration into those systems is explicitly out. |
| F9 | Vendor status classification | **L2** | Potential / Registered / Existing derived from real Dataverse fields on the sample records. |
| F10 | AI recommendation ("reuse existing contract") | **L2** | *Lane 3.* One-shot completion over the validation result. Real generation, prepared records. |

### Stage 3 — Onboard

| ID | Feature | Tier | Notes on what "done" means |
|---|---|---|---|
| F11 | Onboarding checklist instantiation | **L2** | "Start Onboarding" fires a flow that creates all 7 real checklist tasks from a Dataverse template, with focal and due date populated. Real writes. |
| F12 | Checklist status progression | **L2** | Tasks can be genuinely marked complete; the overall progress bar recomputes from Dataverse. |
| F13 | Contract Delivery Log auto-create | **L2** | A CDL record is auto-created and pre-populated on onboarding start, including the Schedule 10 and NDA line items. This is the specific automation the brief calls out, so it should be real. |
| F14 | Vendor classification (VCF) | **L1** | Form renders, captures a classification value. The actual VCF process is a separate governance system — UI only. |
| F15 | Vendor registration wizard | **L2 / L1 split** | Steps 1–2 (Company Info, Capabilities) write to Dataverse — **L2**. Step 3 (Documents) is an upload stub with no storage or extraction — **L1**. Step 4 (AI Validation) reuses F7 — **L3** by inheritance. |
| F16 | Access provisioning | **L1** | Checklist row and status only. No MyAccess integration, no real provisioning request. |
| F17 | Background checks / ITSCP attestation | **L1** | Checklist rows with status and focal. No document handling. |

### Stage 4 — Offboard

| ID | Feature | Tier | Notes on what "done" means |
|---|---|---|---|
| F18 | Offboarding checklist instantiation | **L2** | Same template-driven pattern as F11 over the 9 real offboarding items. Reuses F11's flow shape, so it is cheap once onboarding works. |
| F19 | Checklist status + audit trail | **L2** | Status changes persist with timestamp and actor in Dataverse — this is the "auditable" claim in the brief, and it is genuinely satisfied. |
| F20 | Access revocation notification | **L1** | Button and confirmation state. No email, no MyAccess call. |
| F21 | Data destruction certificate | **L1** | Placeholder row and a static sample document link. No generation. |
| F22 | Final billing gate | **L1** | Displays that final payment is blocked until the checklist completes. Logic is display-only, not enforced. |

### Cross-cutting

| ID | Feature | Tier | Notes on what "done" means |
|---|---|---|---|
| F23 | Vendor profile screen | **L2** | Overview and Capabilities tabs render real indexed data for internal vendors. For an externally-discovered vendor, fields are **model-extracted with citation links attached**, per the §3.1 constraint — build the screen to show provenance, not to imply a verified record. Certifications / Experience / Contacts / Documents tabs show sample data where the record has it, empty states otherwise. |
| F24 | AI Insights | **L2** | *Lane 3.* Strengths / weaknesses / risks / recommendation from a one-shot completion over the vendor's indexed text plus any Bing citations. **The source count is the real citation count from the Bing response, not a hardcoded "52 sources."** Performance and risk scores are model-estimated — label them as such. |
| F25 | AI Marketplace browse | **L2** | Gallery and category filters over real Dataverse records. Low cost because the data already exists for F1. |
| F26 | Executive dashboard | **L2 / L1 split** | Headline totals (vendors, registered, potential, active contracts) computed live from Dataverse — **L2**. Trend chart, region breakdown and risk heat map are static — **L1**. |
| F27 | Compare vendors | **L2** *(should-have)* | Side-by-side matrix from indexed structured fields plus a lane-3 recommendation. |
| F28 | Governance & performance | **L1** *(stretch)* | Fully static. We have no SLA, incident or KPI data, and ingesting it is out of scope. |
| F29 | Persistent AI Copilot panel | **L2** *(stretch)* | A canvas chat surface calling the same bridge flow as F1. Identical capability, different framing. Note that multi-turn follow-ups ("does this vendor also do cloud?") would need conversation state we are not building — treat it as single-turn. Cut first if time runs short. |

---

## 5. Screen priority and the honest UI trade

Twelve deck-quality screens with one UI developer in three days is not
achievable. Rather than degrade all twelve uniformly, we cut by priority:

**Must-have — 7 screens at full fidelity**
Landing Dashboard · AI Search Experience · Vendor Profile · Cross Validation ·
AI Insights · Onboarding Dashboard · Offboarding Dashboard

**Should-have — 3 screens, reduced fidelity acceptable**
Marketplace Browse · Registration Wizard · Executive Dashboard

**Stretch — cut without hesitation**
Compare Vendors · Governance & Performance · Persistent Copilot Panel

Half of day 1 goes to a reusable canvas theme and component set. That looks
like lost time on day 1 and repays itself across the remaining screens; without
it, screens 8 onward get visibly worse.

---

## 6. Explicitly out of scope (L0)

Named so the omissions are decisions, not oversights:

- Vendor self-service portal and vendor-side authentication (Power Pages, B2B guest access)
- Real integration with Oracle Supplier Master, Coupa, SIM or VMO Engine
- Document upload, storage, and AI extraction of certifications or contracts
- Real notifications: email, Teams, MyAccess access requests
- Approval and review workflow before a vendor profile goes live
- SLA / KPI / incident data ingestion and real performance scoring
- Certificate or report generation (data destruction, PER, exit scorecard)
- Role-based access control beyond a single demo persona
- Multi-language, accessibility audit, mobile layout

---

## 7. Work split

Split by layer, not by screen — three people editing one canvas app will
collide.

**Dev A — Data & Platform (Dataverse)**
1. Schema: Vendor, Capability, Certification, Engagement, Onboarding Task, Offboarding Task, Contract Delivery Log, Checklist Template
2. Sample data load, plus the JSON export that seeds the search index
3. Cross-validate deterministic matcher (F7)
4. Checklist instantiation flows and CDL auto-create (F11–F13, F18–F19)
5. Dashboard aggregate views (F26)

**Dev B — AI & Azure**
1. Day-1 provisioning: Foundry project + model deployment, Azure AI Search (Basic+), Bing Grounding resource
2. **Lane 1** — Blob seed → indexer with integrated vectorization → verify hybrid retrieval → expose via Power Automate HTTP action
3. **Lane 2** — Foundry agent with the Bing Grounding tool only; parse grounded answer + citations into a vendor shortlist
4. **Lane 3** — completion prompts for F3 ranking/rationale, F7 adjudication, F10 recommendation, F24 insights
5. Bridge flows and response shaping into canvas-consumable JSON

Build lanes in this order deliberately: **lane 1 first**. It is the path that
must work regardless of what happens with Bing provisioning or venue network, so
it should be finished and demoable before lane 2 starts.

**Dev C — UI (Canvas)**
1. App shell, navigation, theme and component set
2. Must-have screens in priority order
3. Wiring to Dev B's bridge flow and Dev A's tables
4. Should-have screens with whatever time remains

**Reserve the final half-day for rehearsal, not features.** Latency tuning and
demo-narrative data polish always surface things that look like bugs on stage.

---

## 8. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| **Nothing provisioned yet** | Blocks Dev B on day 1. Bing Grounding and AI Search Basic may need approval or quota. | Kick off provisioning **before any other work**, ideally today. The three-lane split contains this: lanes 1 and 3 need only AI Search + a model deployment. If Bing Grounding approval slips, lane 2 drops and the external source becomes L1 — the rest of the demo is unaffected. |
| **Bing live-only, no software fallback** | *Accepted risk, chosen deliberately.* If venue network or the API fails, the headline moment dies. | Zero-code mitigation: rehearse on the actual venue network, and keep a full screen recording of a successful run as a last resort. Adding a cached fallback later costs ~half a day if you change your mind. |
| **Client sample data not yet received** | Blocks Dev A's data load and Dev B's index. | Generate 25–30 fictional vendor profiles on day 1 against the expected shape. Swap in real data when it lands — the index rebuild is minutes, not hours. |
| **Lane 2 round-trip latency (5–15s)** | Dead air during the most important 30 seconds of the demo. | Largely mitigated by the lane split — render lane 1's internal results at ~2–4s while lane 2 is still running, so the screen is never empty. Plus F6's per-lane status indicator. Cap result size and rehearse with a stopwatch. |
| **Grounding with Bing pricing** | Not a prototype concern — volume is trivial. Becomes a real conversation at production scale, where reporting puts it 40–483% above the retired Bing API, with low-volume callers hit hardest. | Out of scope for the summit, but have the number ready if a stakeholder asks about run cost. |
| **Model-generated scores read as computed metrics** | Credibility damage if someone asks how the 94% was derived. | Label AI-estimated figures in the UI. Have a one-sentence answer ready: model-assessed from retrieved evidence, not a tuned scoring algorithm. |
| **Three devs on one canvas app** | Merge collisions, lost work. | Dev C owns the canvas app exclusively. A and B expose flows and tables, and never open the app. |

---

## 9. Demo narrative (the golden path)

One continuous story across all four stages, with a live search in the middle:

1. **Landing** — vendor manager describes a need in plain language.
2. **Source** *(live, unscripted)* — internal catalogue results land first (~2–4s), then live web results fill in beside them with source badges. Invite a query from the audience here; the staggered fill is a feature, not a stumble — narrate it.
3. **Profile → AI Insights** — open a promising external find; strengths, risks, and a recommendation generate live with real citation count.
4. **Cross-Validate** *(live, unscripted)* — the system detects this vendor is already registered under a slightly different name. This is the "weeks of duplicated effort avoided" beat.
5. **Onboard** — start onboarding on a genuinely new vendor; the 7-item checklist and the Contract Delivery Log are created automatically.
6. **Offboard** — show the auditable checklist with real status history on a vendor at end of contract.
7. **Executive dashboard** — close on duplicates prevented and time-to-shortlist.

Steps 2 and 4 are the two moments that must be genuinely live. Everything else
can follow prepared records without weakening the story.
