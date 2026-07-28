#!/usr/bin/env python3
"""
Export one JSON blob per vendor for the `vendor-profiles-index` Azure AI
Search index, per build_guide/lane1-ai-search-index-build.md §1 and
docs/superpowers/specs/2026-07-27-vendorconnect-ai-data-model.md §4.

Reads the Dataverse table export in build_guide/exported_sample_data/
(new_vendors.csv, new_certifications.csv, new_engagement1s.csv) and writes
<vendor-guid>.json files ready to upload to the `vendor-docs` blob container.
"""

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

WEBSITE_SCHEME_RE = re.compile(r"^https?://", re.IGNORECASE)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def split_semicolon(value):
    if not value:
        return []
    return [v.strip() for v in value.split(";") if v.strip()]


def parse_bool(value):
    return (value or "").strip().lower() == "true"


def normalize_website_domain(raw):
    domain = (raw or "").strip()
    domain = WEBSITE_SCHEME_RE.sub("", domain)
    domain = domain.split("/", 1)[0]
    domain = domain.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def build_vendor_summary(overview):
    overview = (overview or "").strip()
    if not overview:
        return ""
    first_sentence = SENTENCE_SPLIT_RE.split(overview, maxsplit=1)[0].strip()
    if len(first_sentence) <= 200:
        return first_sentence
    truncated = first_sentence[:200].rsplit(" ", 1)[0].rstrip(".,;: ")
    return truncated + "..."


def build_vendor_text(vendor, certs, engagements):
    business_domains = split_semicolon(vendor.get("new_businessdomains"))
    capabilities = split_semicolon(vendor.get("new_capabilities"))
    regional_capacity = split_semicolon(vendor.get("new_regionaloperatingcapacity"))

    cert_parts = []
    for cert in certs:
        name = (cert.get("new_certificationname") or "").strip()
        issuer = (cert.get("new_issuer") or "").strip()
        if not name:
            continue
        cert_parts.append(f"{name} ({issuer})" if issuer else name)

    engagement_parts = []
    for engagement in engagements:
        project = (engagement.get("new_deliveryprojectname") or "").strip()
        outcome = (engagement.get("new_outcomesummary") or "").strip()
        if not project and not outcome:
            continue
        engagement_parts.append(f"{project} — {outcome}" if outcome else project)

    lines = [
        f"{(vendor.get('new_vendorname') or '').strip()} ({(vendor.get('new_legalname') or '').strip()})",
        f"Industry: {(vendor.get('new_industry') or '').strip()} | Domains: {', '.join(business_domains)}",
        f"HQ: {(vendor.get('new_headquarterslocation') or '').strip()}, "
        f"{(vendor.get('new_country') or '').strip()} | Headcount: {(vendor.get('new_headcount') or '').strip()}",
        f"Overview: {(vendor.get('new_overview') or '').strip()}",
        f"Capabilities: {', '.join(capabilities)}",
        f"Certifications: {', '.join(cert_parts)}",
        f"Past experience: {'; '.join(engagement_parts)}",
        f"Regional capacity: {', '.join(regional_capacity)}",
    ]
    return "\n".join(lines)


def build_document(vendor, certs, engagements):
    vendor_name = (vendor.get("new_vendorname") or "").strip()
    vendor_id = (vendor.get("new_vendorid") or "").strip().lower()
    overview = (vendor.get("new_overview") or "").strip()

    if not overview:
        return None, f"{vendor_name!r} ({vendor_id}): blank Overview, would index with a null vector"

    headcount_raw = (vendor.get("new_headcount") or "").strip()
    certifications = [
        (cert.get("new_certificationname") or "").strip()
        for cert in certs
        if (cert.get("new_certificationname") or "").strip()
    ]

    document = {
        "id": vendor_id,
        "vendorName": vendor_name,
        "websiteDomain": normalize_website_domain(vendor.get("new_websitedomain")),
        "vendorSummary": build_vendor_summary(overview),
        "vendorText": build_vendor_text(vendor, certs, engagements),
        "vendorStatus": (vendor.get("new_vendorstatus") or "").strip(),
        "industry": (vendor.get("new_industry") or "").strip(),
        "businessDomains": split_semicolon(vendor.get("new_businessdomains")),
        "capabilities": split_semicolon(vendor.get("new_capabilities")),
        "certifications": certifications,
        "country": (vendor.get("new_country") or "").strip(),
        "headcount": int(headcount_raw) if headcount_raw else 0,
        "hasActiveContract": parse_bool(vendor.get("new_hasactivecontract")),
    }
    return document, None


def group_by_vendor(rows):
    grouped = defaultdict(list)
    for row in rows:
        key = (row.get("new_vendor") or "").strip().lower()
        grouped[key].append(row)
    return grouped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        default="build_guide/exported_sample_data",
        help="Directory containing new_vendors.csv, new_certifications.csv, new_engagement1s.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="build_guide/script/output",
        help="Directory to write <vendor-guid>.json files into",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    vendors = read_csv(input_dir / "new_vendors.csv")
    certifications = read_csv(input_dir / "new_certifications.csv")
    engagements = read_csv(input_dir / "new_engagement1s.csv")

    certs_by_vendor = group_by_vendor(certifications)
    engagements_by_vendor = group_by_vendor(engagements)

    written = 0
    skipped = []
    for vendor in vendors:
        vendor_id = (vendor.get("new_vendorid") or "").strip().lower()
        document, skip_reason = build_document(
            vendor,
            certs_by_vendor.get(vendor_id, []),
            engagements_by_vendor.get(vendor_id, []),
        )
        if skip_reason:
            skipped.append(skip_reason)
            continue

        out_path = output_dir / f"{document['id']}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(document, f, indent=2, ensure_ascii=False)
        written += 1

    print(f"Wrote {written} vendor document(s) to {output_dir}")
    if skipped:
        print(f"Skipped {len(skipped)} vendor(s):")
        for reason in skipped:
            print(f"  - {reason}")


if __name__ == "__main__":
    main()
