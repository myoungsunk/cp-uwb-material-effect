# Stage CSV Integrated

This folder is the consolidated CSV package for the paper-facing analysis.

## Structure

- `stage_csv_manifest_20260415.csv`
  - master manifest for every copied CSV
  - includes source path, packaged path, role, and paper-use field
- `stage_0`
  - notation-only placeholder CSV
- `stage_1`
  - ideal TE/TM truth, Fresnel sanity, lock-variant A/B, and phase-lock audit
- `stage_2`
  - same/flip-safe ideal CP truth tables
- `stage_3`
  - LP-anchor branch lock and practical LP/CP patch exports
- `stage_4`
  - raw-primary headline tables plus direct-CP sanity and supplement audits
- `stage_5`
  - discussion-only placeholder CSV
- `stage_6`
  - UWB sensitivity sweep CSVs
- `stage_7`
  - manuscript figure/table export CSVs

## Reading Order

1. Start from `stage_csv_manifest_20260415.csv`.
2. Read `stage_1` and `stage_2` first for the ideal anchor.
3. Read `stage_3` for the practical patch layer and alias lock.
4. Use `stage_4/headline_raw_primary` as the current paper headline source.
5. Treat other `stage_4` subfolders as audit and supplement layers.

## Notes

- `stage_0` and `stage_5` do not generate standalone numeric outputs in the
  current workflow, so each contains a placeholder manifest CSV.
- This package is a copy layer only. Authoritative generation still lives under
  `analysis_stages/`.
