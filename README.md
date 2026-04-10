# CP Material Effect

This repository stores simulation inputs and extracted reference materials for
CP-UWB material-effect analysis.

## Contents

- `simulation_inputs/csv`
  - Core CSV datasets for `M1`, `M2`, and `M3`
- `simulation_inputs/raw_zips`
  - Original zip archives provided for the study
- `simulation_inputs/unzipped`
  - Unpacked reference files, figures, and the current gamma extraction script

## Current Scope

- Reflection-case datasets (`*_R_5000.csv`)
- Transmission-case datasets (`*_T_5000.csv`)
- Off-boresight free-space reference (`m3_off-boresigjt.csv`)
- Existing analysis script:
  - `simulation_inputs/unzipped/files_1/gamma_extraction_v2.py`

## Notes

- `theta_r` in the CSV files is treated as the wall-normal incidence angle
  `theta_i`.
- Current extraction work focuses on the reflection path and M1/M2/M3
  calibration.
