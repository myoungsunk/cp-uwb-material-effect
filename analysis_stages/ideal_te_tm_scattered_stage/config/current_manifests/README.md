# Current Manifests

This folder keeps the active scattered-stage manifests that are still valid for
execution.

Current files:

- `manifest_a12_corr.csv`
- `manifest_actual_new_runs_20260412.csv`

Retired and deleted:

- `manifest_actual_center5x5.csv`

Rule:

- do not reintroduce `actual_center5x5` into active runs
- use explicit `--manifest` paths pointing into this folder
- `manifest_actual_new_runs_20260412.csv` is now locked to `field_type=scattered`
  for every row
- its TE PEC filenames may still contain `__total__`, but that is treated as a
  filename/report-label issue, not as the active interpretation
- high-angle `TE PEC` rows are removed from the active manifests:
  - filter: `case=pec`, `pol=TE`, `theta_deg >= 80`
