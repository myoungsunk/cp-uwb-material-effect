# actual_new_runs_20260412

This raw-data folder stores the flat HFSS exports copied from:

- `D:/codex/ansys_automation/downloads/CP_global_test_copy_new_runs_20260412_161830/cp_global_test_copy_new_runs_exports`

Dataset scope:

- cases:
  - `PEC`
  - `baseline`
- polarization:
  - `TE`
  - `TM`
- angles:
  - `70 deg`
  - `75 deg`
  - `80 deg`
  - `85 deg`
- observation distance:
  - `kobs = 0.5, 1, 2`

Important:

- filenames encode:
  - field type (`total` / `scattered`)
  - rect (`z_m` / `z_p`)
  - `theta`
  - `kobs`
- this folder is intended to be consumed via:
  - `code/generate_hfss_flat_manifest.py`
