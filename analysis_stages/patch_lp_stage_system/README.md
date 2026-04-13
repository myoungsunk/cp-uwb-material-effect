# Patch LP Stage System

This folder is the active working area for the LP patch-stage pipeline.

## Structure

- `code`
  - LP patch-stage analysis code
- `csv`
  - Current CP CSV copies for proxy comparison
  - Future LP CSVs should also be added here
- `results`
  - LP theory / proxy comparison figures

## Scope

- Fresnel TE/TM theory curves
- CP-derived patch-stage `R_TE` / `R_TM` proxy comparison
- future LP-direct `zz` / `yy` simple-ratio extraction

## Method Subfolders

- `metal_plate_normalized`
  - imported from `files (4).zip`
- `m3_unfolded_comparison`
  - imported from `files (5).zip`

## Current Data Status

- LP source CSVs are stored in `csv`
- Current execution uses LP reflection-case files (`*_R_5000.csv`)
- LP transmission-case files (`*_T_5000.csv`) are stored but not yet used
