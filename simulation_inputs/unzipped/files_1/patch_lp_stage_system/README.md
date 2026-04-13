# Patch LP Stage System

This folder contains the LP-side analysis pipeline kept separate from the
existing CP patch-stage code.

## Current Scope

- Generate TE/TM Fresnel theory curves.
- Reuse current CP patch-stage CSVs to compute `R_TE` / `R_TM` patch proxies.
- Optionally process future LP patch-stage `M1` / `M2` / `M3` CSVs when they
  are added to `simulation_inputs/csv`.

## Main Script

- `gamma_extraction_lp.py`
  - Default: theory + CP-derived LP proxies
  - Optional LP-direct mode: `python gamma_extraction_lp.py --with-lp`

## Expected LP CSV Names

- `m1_lp_los_5000.csv`
- `m3_lp_off-boresight.csv`
- `m2_lp_metal_R_5000.csv`
- `m2_lp_concrete_R_5000.csv`
- `m2_lp_glass_R_5000.csv`
- `m2_lp_wood_R_5000.csv`

## Output

- Figures are written to `patch_lp_stage_system/outputs`
- Current CP-derived `R_TE` / `R_TM` are patch-stage proxies, not ideal
  plane-wave material-only coefficients
