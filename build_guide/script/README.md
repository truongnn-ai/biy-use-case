# Vendor export script

`export_vendors.py` builds the per-vendor JSON blobs for the
`vendor-profiles-index` Azure AI Search index, per
`build_guide/lane1-ai-search-index-build.md` §1 and
`docs/superpowers/specs/2026-07-27-vendorconnect-ai-data-model.md` §4.

## Usage

```bash
python3 export_vendors.py [--input-dir DIR] [--output-dir DIR]
```

python3 export_[vendors.py](http://vendors.py) --input-dir /Users/ethanng/Documents/ws/biy_app/build_guide/exported_sample_data --output-dir output/

Run from anywhere; both paths default to relative-to-cwd, so either `cd` into
the repo root first or pass absolute paths.

- `--input-dir` (default `build_guide/exported_sample_data`) — must contain
`new_vendors.csv`, `new_certifications.csv`, `new_engagement1s.csv`, exported
from the Dataverse `Vendor`/`Certification`/`Engagement` tables. Use Power
Query's Dataverse connector (not the plain "Export to Excel" view export),
since it resolves choice fields to text and multi-select choices to
semicolon-joined strings, and supports pulling multi-select columns at all
— the plain view export does not.
- `--output-dir` (default `build_guide/script/output`) — where the
`<vendor-guid>.json` files are written. Drag this whole folder into the
`vendor-docs` blob container (§1.3) once done.



## What it does

- Joins certifications and engagements to their vendor by the real Dataverse
GUID (`new_vendor` → `new_vendorid`), not by name.
- Normalizes `websiteDomain` (strips scheme, `www.`, path/slash, lowercases).
- Builds `vendorSummary` from the first sentence of the vendor's Overview
(truncated to ~200 chars if needed).
- Builds `vendorText` in the exact field order data-model §4.1 requires.
- Emits `businessDomains`, `capabilities`, and `certifications` as JSON
arrays, never semicolon strings.
- Skips (with a printed warning) any vendor with a blank Overview, since an
empty `vendorText` would index with a null vector and never surface in
vector search.

After running, the script prints how many documents were written and lists
any skipped vendors with the reason. Cross-check the written count against
the blob count after upload, per §1.3.