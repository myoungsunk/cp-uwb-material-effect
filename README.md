# CP Material Effect

This repository stores simulation inputs, archived references, and active
analysis-stage workspaces for CP-UWB material-effect analysis.

## Contents

- `DEBUGGING_NOTE.md`
  - Persistent debugging note for this folder
  - Canonical place for assumptions, findings, procedures, and future updates
- `analysis_stages`
  - Active purpose-based workspaces
  - Each stage uses `code`, `csv`, and `results`
- `simulation_inputs/csv`
  - Shared/raw CSV pool for `M1`, `M2`, and `M3`
  - Copied into active stages as needed
- `simulation_inputs/raw_zips`
  - Original zip archives provided for the study
- `simulation_inputs/unzipped`
  - Archived unpacked references, older figures, and source drop folders

## Active Stages

- `analysis_stages/patch_cp_stage_system`
  - Current CP patch-stage pipeline
- `analysis_stages/patch_lp_stage_system`
  - LP theory/proxy stage and future LP-direct pipeline
- `analysis_stages/ideal_te_tm_stage`
  - Future ideal plane-wave material/slab stage

## Notes

- Use `DEBUGGING_NOTE.md` as the persistent debugging log and procedure note for
  this folder.
- `theta_r` in the CSV files is treated as the wall-normal incidence angle
  `theta_i`.
- Current extraction work focuses on reflection-path `M1/M2/M3` calibration.
- Patch-stage outputs should be interpreted as system-stage quantities unless
  separately validated against an ideal/material stage.
- Older unpacked folders under `simulation_inputs/unzipped/files_*` are kept as
  archive/reference sources.

## Consolidated Report

- `ACTIVE_OLD_M3_REPORT.md`
  - Current consolidated quantitative report based on the rerun active `OLD M3`
    dataset
  - Reflects the restored active reference, not the archived `NEW M3` case
- `report_data/old_m3_active`
  - Structured CSV tables used by the consolidated report
  - Includes antenna diagnostics, CP concrete summary, LP concrete summary,
    triple comparison, and suppression gain tables
