# Sample data — external vendor discovery batch

Dummy data representing ~100 externally-sourced vendor prospects that have
never been engaged. Mirrors the **column layout** of `../sample_data`
(display-name headers, same lookup-by-text convention) so it loads with the
same import wizard, but intentionally does **not** follow the newer data
model in `docs/superpowers/specs/2026-07-27-vendorconnect-ai-data-model.md` —
per instructions, this batch stays on the original 3-table shape used by
`../sample_data`.

Only 3 tables are seeded here (no projects, contacts, lifecycle tasks or
shortlist items — those aren't meaningful for vendors with no history):

## Load order

1. `vca_vendor.csv` (105 rows — 100 net-new external vendors + 5 dedup-demo rows, see below)
2. `vca_certification.csv` (105 rows) — `Vendor` → Vendor Name
3. `vca_engagement.csv` (**0 rows**, header only) — external vendors have no
   BrandName delivery history by definition; the table exists only so the
   import target/schema is exercised.

## Conventions

Same as `../sample_data`: dates `YYYY-MM-DD`; empty cell = null; "today" for
this dataset is **2026-07-31**.

Every vendor here has `Has Active Contract = False` and `Vendor Status` of
either `Potential` or `Registered` (never `Existing`) — external prospects by
definition have no active engagement. `Source` is limited to
`External Discovery` (paired with `AI Extracted = True` and 2 source-citation
URLs) or `Manual Registration` (paired with `AI Extracted = False`, no
citations) — `Internal Catalogue` is not used, since nothing here has been
through internal cataloguing yet.

## Dedup demo — last 5 rows of `vca_vendor.csv`

The last 5 rows are near-duplicates of the **last 5 vendors** in
`../sample_data/vca_vendor.csv` (Maple Ridge Systems, Victoria Peak Advisory,
Siam Integration, Lumiere Ingenierie, Shannon Cloud Group), re-discovered
independently through external sourcing:

| Website Domain (dedup key) | Internal record | External record (this file) |
|---|---|---|
| `mapleridgesystems.ca` | Maple Ridge Systems | Maple Ridge IT Systems |
| `vpadvisory.hk` | Victoria Peak Advisory | Victoria Peak Advisory Group |
| `siamintegration.co.th` | Siam Integration | Siam Integration Group |
| `lumiere-ing.fr` | Lumiere Ingenierie | Lumière Ingénierie |
| `shannoncloud.ie` | Shannon Cloud Group | Shannon Cloud |

Each pair shares the exact same **Website Domain** but differs in Vendor
Name, Legal Name, Headcount, capability ordering, regional coverage, and
overview wording — the shape a real external-discovery feed would produce
for a vendor the org already knows. `vca_certification.csv` carries one
matching certification for each of the 5 (dated 2026, i.e. found/renewed
after the internal record), under the *external* display name, so a
name-based join alone won't reconcile them — only the domain will.

This complements the "known gap" called out in `../sample_data/README.md`
(§ Known gap, not fixed here), which asked for a second near-duplicate vendor
row to exercise the cross-validation match key — these 5 pairs, spread
across the internal/external boundary, cover that gap.

## Suggested enhancements

- **Normalize the dedup key before matching.** Compare
  `lower(strip_protocol_and_www(Website Domain))` rather than the raw
  column — a feed will eventually send `https://www.Domain.com/` or mixed
  case, and a raw string match would miss it even though it's the same
  vendor.
- **Don't dedup on domain alone once contracts exist.** Domain match is a
  fine signal for merging *discovery* records, but once one side has
  `Has Active Contract = True` or an engagement history, matching should
  require human confirmation before merging — collapsing an active vendor
  into a freshly-discovered lookalike record could silently drop history.
- **Carry a provenance/merge-source field.** When two records merge, keep a
  pointer back to both source rows (e.g. an `AlsoKnownAs` or `MergedFrom`
  list) instead of discarding the losing record outright — useful for audit
  and for undoing a bad auto-merge.
- **Extend the dedup key set.** Domain is the primary key here, but consider
  a secondary fuzzy match on (normalized Legal Name + Country) for vendors
  that share a domain-less presence (e.g. subsidiaries that publish under a
  parent's website) or that migrate domains.
