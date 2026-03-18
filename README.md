# Reionization-Era Quasars

A catalogue of spectroscopically confirmed quasars at redshifts $z \geq 5.3$.

Compiled for the 54th Saas-Fee Advanced Course book chapter:

> **Observations of Early Black Holes Before and After JWST**
> Eduardo Bañados (Max Planck Institute for Astronomy, Heidelberg)
> In: *Galaxies and Black Holes in the First Billion Years as seen by the JWST*
> Saas-Fee Advanced Course 54, Springer (in press)

This database builds on the compilation presented in [Fan, Bañados & Simcoe (2023, ARA&A, 61, 373)](https://ui.adsabs.harvard.edu/abs/2023ARA%26A..61..373F/abstract) and is updated as new discoveries are published.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19094457.svg)](https://doi.org/10.5281/zenodo.19094457)

## The catalogue

The main data file is `quasar_census_saasfee_YYYYMMDD.csv`, where the date stamp indicates when the catalogue was last updated.  The most recent version is:

**`quasar_census_saasfee_20260318.csv`** — 736 quasars, $z = 5.30 - 7.64$

### Columns

| Column | Description |
|--------|-------------|
| `name` | IAU-style quasar name (JHHMMSS.ss±DDMMSS.ss) |
| `ra_deg` | Right ascension (J2000, degrees) |
| `dec_deg` | Declination (J2000, degrees) |
| `redshift` | Spectroscopic redshift |
| `m1450` | Apparent magnitude at rest-frame 1450 Å |
| `M1450` | Absolute magnitude at rest-frame 1450 Å |
| `disc_ref` | Discovery reference key(s); semicolon-separated if multiple |
| `disc_bibcode` | ADS bibcode(s) for discovery reference(s) |
| `redshift_ref` | Redshift reference key |
| `redshift_bibcode` | ADS bibcode for redshift reference |

### References

The file `references.csv` contains the full bibliographic information for all references cited in the catalogue, including ADS bibcodes and URLs.

## How to cite

If you use this catalogue, please cite the Saas-Fee book chapter and this repository:

```
Bañados, E. (2026). "Observations of Early Black Holes Before and After JWST",
    in Galaxies and Black Holes in the First Billion Years as seen by the JWST,
    Saas-Fee Advanced Course 54, Springer.
```

Please also cite the original discovery and redshift papers for individual quasars — the `disc_bibcode` and `redshift_bibcode` columns provide the relevant ADS bibcodes.

## Maintainer notes

The catalogue is maintained by [Eduardo Bañados](https://banados.www3.mpia.de/) (MPIA Heidelberg).  Corrections and suggestions are welcome — please open an issue or submit a pull request.

The `maintainer/` folder contains the source files and scripts used to build and validate the catalogue.  When updating:

1. Edit the source files in `maintainer/`: `quasar_census_saasfee.csv` (the full list with reference keys) and `references_master.csv` (the complete reference list, which may include entries beyond this catalogue).
2. Run `python maintainer/validate_catalogue.py` to check for unresolved references, duplicates, and data issues.
3. Run `python maintainer/build_quasar_database.py` to produce the merged, date-stamped catalogue and the filtered `references.csv` in the repo root.
4. Commit, push, and create a new GitHub release.  Zenodo mints a DOI automatically.

Requirements: Python 3.7+ (standard library only).

## License

This work is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
