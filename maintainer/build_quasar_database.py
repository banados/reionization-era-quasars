#!/usr/bin/env python3
"""
build_quasar_database.py

Merge the quasar census with the master reference list to produce:
  1. A date-stamped, self-contained catalogue with ADS bibcodes.
  2. A filtered references.csv containing only cited references.

Usage (from the repo root):
    python maintainer/build_quasar_database.py              # today's date
    python maintainer/build_quasar_database.py 20260318     # specific date

Inputs (in maintainer/):
    quasar_census_saasfee.csv   — source quasar list (reference keys only)
    references_master.csv       — complete reference list

Outputs (in repo root):
    quasar_census_saasfee_YYYYMMDD.csv  — merged catalogue
    references.csv                      — filtered references
"""

import csv
import sys
import os
from datetime import date
from urllib.parse import unquote

# ── resolve paths relative to this script's location ──────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

QUASAR_INPUT = os.path.join(SCRIPT_DIR, "quasar_census_saasfee.csv")
REFS_INPUT = os.path.join(SCRIPT_DIR, "references_master.csv")
REFS_OUTPUT = os.path.join(REPO_ROOT, "references.csv")


def clean_bibcode(raw: str) -> str:
    """Decode URL-encoded characters (e.g. %26 -> &) in ADS bibcodes."""
    return unquote(raw).rstrip("/")


def load_references(path: str) -> dict:
    refs = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["NameYear"].strip()
            refs[key] = {
                "bibcode": clean_bibcode(row["ADS ID"].strip()),
                "ads_url": row["ADS Link"].strip(),
                "notes": row.get("Notes", "").strip(),
            }
    return refs


def resolve_refs(ref_field, ref_lookup, errors, quasar_name, field_label):
    keys = [k.strip() for k in ref_field.split(";")]
    bibcodes = []
    for k in keys:
        if k in ref_lookup:
            bibcodes.append(ref_lookup[k]["bibcode"])
        else:
            bibcodes.append("")
            errors.append(
                f"  {quasar_name}: '{k}' ({field_label}) not found in references_master.csv"
            )
    return ";".join(bibcodes)


def main():
    # ── date stamp ────────────────────────────────────────────────
    if len(sys.argv) > 1:
        datestamp = sys.argv[1]
    else:
        datestamp = date.today().strftime("%Y%m%d")

    quasar_output = os.path.join(REPO_ROOT, f"quasar_census_saasfee_{datestamp}.csv")

    # ── check inputs ──────────────────────────────────────────────
    for path in (QUASAR_INPUT, REFS_INPUT):
        if not os.path.isfile(path):
            print(f"ERROR: Input file not found: {path}")
            sys.exit(1)

    # ── load data ─────────────────────────────────────────────────
    ref_lookup = load_references(REFS_INPUT)
    print(f"Loaded {len(ref_lookup)} references from {os.path.basename(REFS_INPUT)}")

    with open(QUASAR_INPUT, newline="", encoding="utf-8") as f:
        quasars = list(csv.DictReader(f))
    print(f"Loaded {len(quasars)} quasars from {os.path.basename(QUASAR_INPUT)}")

    # ── merge ─────────────────────────────────────────────────────
    errors = []
    used_refs = set()

    output_columns = [
        "name", "ra_deg", "dec_deg", "redshift",
        "m1450", "M1450",
        "disc_ref", "disc_bibcode",
        "redshift_ref", "redshift_bibcode",
    ]

    merged_rows = []
    for q in quasars:
        disc_ref = q["disc_ref"].strip()
        z_ref = q["redshift_ref"].strip()

        disc_bib = resolve_refs(disc_ref, ref_lookup, errors, q["name"], "disc_ref")
        z_bib = resolve_refs(z_ref, ref_lookup, errors, q["name"], "redshift_ref")

        for k in disc_ref.split(";"):
            used_refs.add(k.strip())
        for k in z_ref.split(";"):
            used_refs.add(k.strip())

        merged_rows.append({
            "name": q["name"],
            "ra_deg": q["ra_deg"],
            "dec_deg": q["dec_deg"],
            "redshift": q["redshift"],
            "m1450": q["m1450"],
            "M1450": q["M1450"],
            "disc_ref": disc_ref,
            "disc_bibcode": disc_bib,
            "redshift_ref": z_ref,
            "redshift_bibcode": z_bib,
        })

    if errors:
        print(f"\nWARNING: {len(errors)} unresolved reference(s):")
        for e in errors:
            print(e)
    else:
        print("All references resolved successfully.")

    # ── write merged catalogue ────────────────────────────────────
    with open(quasar_output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_columns)
        writer.writeheader()
        writer.writerows(merged_rows)
    print(f"\nWrote {len(merged_rows)} quasars to {os.path.basename(quasar_output)}")

    # ── write filtered references ─────────────────────────────────
    ref_columns = ["NameYear", "bibcode", "ads_url", "notes"]
    used_count = 0
    with open(REFS_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ref_columns)
        writer.writeheader()
        for key in sorted(ref_lookup.keys()):
            if key in used_refs:
                writer.writerow({
                    "NameYear": key,
                    "bibcode": ref_lookup[key]["bibcode"],
                    "ads_url": ref_lookup[key]["ads_url"],
                    "notes": ref_lookup[key]["notes"],
                })
                used_count += 1

    unused_count = len(ref_lookup) - used_count
    print(f"Wrote {used_count} used references to references.csv")
    if unused_count > 0:
        unused_keys = sorted(set(ref_lookup.keys()) - used_refs)
        print(f"  ({unused_count} unused references omitted: {', '.join(unused_keys)})")

    # ── summary ───────────────────────────────────────────────────
    redshifts = [float(r["redshift"]) for r in merged_rows]
    z_min, z_max = min(redshifts), max(redshifts)

    print(f"\n{'='*50}")
    print(f"  DATABASE SUMMARY")
    print(f"{'='*50}")
    print(f"  Total quasars:  {len(merged_rows)}")
    print(f"  Redshift range: {z_min:.4f} – {z_max:.4f}")
    print(f"  z >= 7:         {sum(1 for z in redshifts if z >= 7)}")
    print(f"  6 <= z < 7:     {sum(1 for z in redshifts if 6 <= z < 7)}")
    print(f"  5 <= z < 6:     {sum(1 for z in redshifts if z < 6)}")
    print(f"  Unique refs:    {len(used_refs)}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
