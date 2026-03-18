#!/usr/bin/env python3
"""
validate_catalogue.py

Validate the quasar census source files for internal consistency.
Run this before building a new release.

Usage (from the repo root):
    python maintainer/validate_catalogue.py

Checks performed:
  1. All reference keys in the quasar file resolve in references_master.csv
  2. No duplicate quasar entries (by name or by coordinates)
  3. Coordinate sanity (RA in [0, 360), Dec in [-90, 90])
  4. Redshift range check (z >= 5.0)
  5. Magnitude sanity (m1450 and M1450 are valid floats)
  6. Reference key format consistency (no URL encoding, no underscores)
  7. Bibcode format in references_master.csv

Exit code 0 if all checks pass, 1 if any warnings/errors found.
"""

import csv
import sys
import os
from collections import Counter
from urllib.parse import unquote

# ── resolve paths relative to this script's location ──────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

QUASAR_FILE = os.path.join(SCRIPT_DIR, "quasar_census_saasfee.csv")
REFS_FILE = os.path.join(SCRIPT_DIR, "references_master.csv")


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check_references(quasars, refs):
    ref_keys = {row["NameYear"].strip() for row in refs}
    errors = []
    used_keys = set()

    for i, q in enumerate(quasars, start=2):
        for field in ("disc_ref", "redshift_ref"):
            for key in q[field].split(";"):
                key = key.strip()
                used_keys.add(key)
                if key not in ref_keys:
                    errors.append(f"  Line {i}: {q['name']} — '{key}' ({field}) not in references_master.csv")

    unused = sorted(ref_keys - used_keys)
    return errors, unused


def check_duplicates(quasars):
    errors = []

    names = [q["name"] for q in quasars]
    dupes = [name for name, count in Counter(names).items() if count > 1]
    for d in dupes:
        errors.append(f"  Duplicate name: {d}")

    coords = []
    for q in quasars:
        try:
            coords.append((q["name"], float(q["ra_deg"]), float(q["dec_deg"])))
        except ValueError:
            pass

    threshold_deg = 2.0 / 3600.0
    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            dra = abs(coords[i][1] - coords[j][1])
            ddec = abs(coords[i][2] - coords[j][2])
            if dra < threshold_deg and ddec < threshold_deg:
                errors.append(
                    f"  Close pair ({dra*3600:.1f}\", {ddec*3600:.1f}\"): "
                    f"{coords[i][0]} and {coords[j][0]}"
                )

    return errors


def check_values(quasars):
    errors = []

    for i, q in enumerate(quasars, start=2):
        name = q["name"]

        try:
            ra = float(q["ra_deg"])
            if not (0.0 <= ra < 360.0):
                errors.append(f"  Line {i}: {name} — RA={ra} out of range [0, 360)")
        except ValueError:
            errors.append(f"  Line {i}: {name} — invalid RA: '{q['ra_deg']}'")

        try:
            dec = float(q["dec_deg"])
            if not (-90.0 <= dec <= 90.0):
                errors.append(f"  Line {i}: {name} — Dec={dec} out of range [-90, 90]")
        except ValueError:
            errors.append(f"  Line {i}: {name} — invalid Dec: '{q['dec_deg']}'")

        try:
            z = float(q["redshift"])
            if z < 5.0:
                errors.append(f"  Line {i}: {name} — z={z} below catalogue threshold (5.0)")
            if z > 15.0:
                errors.append(f"  Line {i}: {name} — z={z} suspiciously high")
        except ValueError:
            errors.append(f"  Line {i}: {name} — invalid redshift: '{q['redshift']}'")

        for mag_col in ("m1450", "M1450"):
            try:
                mag = float(q[mag_col])
                if mag_col == "M1450" and (mag > -18.0 or mag < -32.0):
                    errors.append(f"  Line {i}: {name} — {mag_col}={mag} seems unusual")
                if mag_col == "m1450" and (mag < 14.0 or mag > 30.0):
                    errors.append(f"  Line {i}: {name} — {mag_col}={mag} seems unusual")
            except ValueError:
                errors.append(f"  Line {i}: {name} — invalid {mag_col}: '{q[mag_col]}'")

    return errors


def check_ref_format(quasars):
    warnings = []

    for i, q in enumerate(quasars, start=2):
        for field in ("disc_ref", "redshift_ref"):
            for key in q[field].split(";"):
                key = key.strip()
                if "%" in key:
                    warnings.append(f"  Line {i}: {q['name']} — URL-encoded key '{key}' in {field}")
                if "_" in key:
                    warnings.append(f"  Line {i}: {q['name']} — underscore in key '{key}' ({field})")
                if "+" in key and not key.startswith("+"):
                    warnings.append(f"  Line {i}: {q['name']} — '+' in key '{key}' ({field})")
                if "InPrep" in key or "inprep" in key.lower():
                    warnings.append(f"  Line {i}: {q['name']} — placeholder ref '{key}' ({field})")

    return warnings


def check_bibcode_format(refs):
    warnings = []
    for r in refs:
        ads_id = r["ADS ID"].strip()
        name = r["NameYear"].strip()
        if "%" in ads_id:
            warnings.append(f"  {name}: ADS ID '{ads_id}' contains URL encoding")
        if ads_id.endswith("/"):
            warnings.append(f"  {name}: ADS ID '{ads_id}' has trailing slash")
    return warnings


def main():
    for path in (QUASAR_FILE, REFS_FILE):
        if not os.path.isfile(path):
            print(f"ERROR: File not found: {path}")
            sys.exit(1)

    quasars = load_csv(QUASAR_FILE)
    refs = load_csv(REFS_FILE)

    print(f"Validating {len(quasars)} quasars from {os.path.basename(QUASAR_FILE)}")
    print(f"Against {len(refs)} references from {os.path.basename(REFS_FILE)}")
    print()

    all_ok = True

    # 1. Reference resolution
    ref_errors, unused_refs = check_references(quasars, refs)
    if ref_errors:
        all_ok = False
        print(f"ERRORS — Unresolved references ({len(ref_errors)}):")
        for e in ref_errors:
            print(e)
    else:
        print("OK — All reference keys resolve.")
    if unused_refs:
        print(f"INFO — {len(unused_refs)} references in master file but not used by any quasar:")
        print(f"       {', '.join(unused_refs[:10])}{'...' if len(unused_refs) > 10 else ''}")
    print()

    # 2. Duplicates
    dup_errors = check_duplicates(quasars)
    if dup_errors:
        all_ok = False
        print(f"WARNINGS — Duplicates or close pairs ({len(dup_errors)}):")
        for e in dup_errors:
            print(e)
    else:
        print("OK — No duplicate names or close coordinate pairs.")
    print()

    # 3. Value checks
    val_errors = check_values(quasars)
    if val_errors:
        all_ok = False
        print(f"ERRORS — Value range issues ({len(val_errors)}):")
        for e in val_errors:
            print(e)
    else:
        print("OK — All coordinates, redshifts, and magnitudes in expected ranges.")
    print()

    # 4. Reference format
    fmt_warnings = check_ref_format(quasars)
    if fmt_warnings:
        print(f"WARNINGS — Reference key format ({len(fmt_warnings)}):")
        for w in fmt_warnings:
            print(w)
    else:
        print("OK — All reference keys follow standard format.")
    print()

    # 5. Bibcode format
    bib_warnings = check_bibcode_format(refs)
    if bib_warnings:
        print(f"WARNINGS — Bibcode format in references_master.csv ({len(bib_warnings)}):")
        for w in bib_warnings:
            print(w)
    else:
        print("OK — All ADS IDs in references_master.csv are clean.")
    print()

    # Summary
    z_vals = [float(q["redshift"]) for q in quasars]
    print("=" * 50)
    print(f"  SUMMARY: {len(quasars)} quasars, z = {min(z_vals):.2f} – {max(z_vals):.2f}")
    print(f"  z >= 7: {sum(1 for z in z_vals if z >= 7)}")
    print(f"  6 <= z < 7: {sum(1 for z in z_vals if 6 <= z < 7)}")
    print(f"  5 <= z < 6: {sum(1 for z in z_vals if z < 6)}")
    if all_ok:
        print("  STATUS: ALL CHECKS PASSED")
    else:
        print("  STATUS: ISSUES FOUND (see above)")
    print("=" * 50)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
