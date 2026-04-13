# Ideal TE/TM Scattered Stage

This stage is the ideal plane-wave / material-stage pipeline for HFSS wide-grid
exports.

## Current Summary

- `actual_center5x5_20260411` manifest is retired and deleted.
- Active manifests are now grouped under:
  - `config/current_manifests`
- The earlier transmission-side validation from the old `z_p` export is retired
  as a wrong-coordinate case.
- The corrected export set is now locked under:
  - `csv/raw/a12_corr`
- Active corrected outputs:
  - `config/current_manifests/manifest_a12_corr.csv`
  - `results/a12_corr_full/truth_table_linear.csv`
  - `results/a12_corr_full/qc_report.csv`
- Current manifest reruns are archived under:
  - `results/current_manifest_runs`
- Corrected baseline QC is clean:
  - `baseline_residual_over_incident ~= 8.3e-6 ~ 1.22e-4`
- Therefore the corrected `z_p` coordinates fixed the baseline-side geometry
  error.
- However, high-angle TE PEC transmission is still not closed:
  - `theta=80 deg, kobs=2`: `|T_TE| ~= 1.691`
  - `theta=85 deg, kobs=2`: `|T_TE| ~= 1.324`
- TM PEC behavior improves substantially with `kobs = 1, 2`, so the remaining
  blocker is now TE-dominant, not a generic transmission-plane failure.
- This dataset family must be grouped by `run_label`. Different files can share
  the same `(case, pol, rect, theta, kobs)` while differing in
  `w_plane / l_plane`, so grouping without `run_label` is invalid.
- Additional TE PEC `80/85 deg` existing-report re-extracts are archived under:
  - `csv/raw/te_pec_existing_reports_80_85_20260412`
- Combined TE report-lock bundle is archived under:
  - `csv/raw/te_lock_0413`
- Current interpretation of those added TE PEC re-extracts:
  - the old exact duplicate-block symptom is gone inside the new
    `Near_E_Table_1/2` high-angle blocks
  - `Near_E_Table_3` and `Near_E_Table_3_1` are only dedicated subset exports
    for `kobs=2, w_plane=500 mm`
  - they do **not** directly replace the active merged TE PEC scattered CSV
  - their dominant `Ey` component is much closer only after a global sign flip
    against the active merged dataset, so they remain debug-only until the
    report definition is locked
- New TE baseline existing-report comparator is now included in that bundle:
  - `Near_E_Table_3 = z_m`, `Near_E_Table_3_1 = z_p`
  - both are `scattered`
  - correct-surface comparison against the active merged baseline is relatively
    close without a strong sign-flip preference
  - therefore the current sign/report-definition ambiguity remains isolated to
    the PEC re-extract path, not to the whole TE export chain
- Copied project geometry / report audit is now archived under:
  - `results/project_copy_20260412_geometry_audit.md`
- Current audit lock from that copied AEDT:
  - the relevant ideal-stage designs do **not** use a global `z_p` plane
  - they use `z_smaller_0 -> RelativeCS1` and `z_larger_0 -> RelativeCS2`
  - only the composite `BOTH` design still has `z_larger_0 -> Global`
  - therefore the current geometry suspicion shifts from saved project setup to
    export-path / report-definition mismatch

It is intentionally separated from:

- `patch_cp_stage_system`
- `patch_lp_stage_system`
- `ideal_te_tm_stage`

The primary output is the linear-basis truth table:

- `R_TE(f, theta_i)`
- `T_TE(f, theta_i)`
- `R_TM(f, theta_i)`
- `T_TM(f, theta_i)`

## Interpretation Lock

This stage now supports mixed export modes per file through the manifest.

Each manifest row can declare:

- `field_type = scattered`
- `field_type = total`

The reconstruction rules are:

1. Reflection plane (`z_m` / `refl_rect`)
   - scattered export: `E_refl = E_scat`
   - total export: `E_refl = E_total - E_inc`
2. Transmission plane (`z_p` / `trans_rect`)
   - scattered export: `E_trans,total = E_inc + E_scat`
   - total export: `E_trans,total = E_total`
3. Baseline QC
   - scattered export: `||E_scat|| / ||E_inc||`
   - total export: `||E_total - E_inc|| / ||E_inc||`

Confirmed datasets in this stage:

- `actual_new_runs_20260412`
- `a12_corr`
- `te_pec_existing_reports_80_85_20260412` (debug-only comparator)

Active manifest folder:

- `config/current_manifests`
- lock:
  - `manifest_actual_new_runs_20260412.csv` is now treated as `scattered`
    throughout, even though some TE PEC filenames still contain `__total__`
  - rerunning after this manifest correction did not change the extracted
    coefficients, so the remaining discrepancy is not explained by the manifest
    tag alone
  - high-angle `TE PEC` rows are removed from the active manifests and from the
    current rerun outputs:
    - `case=pec`, `pol=TE`, `theta_deg >= 80`

## Active Corrected Dataset (`a12_corr`)

The current corrected rerun uses the export set copied from:

- `D:/codex/ansys_automation/downloads/cp_global_test_copy_all_available_exports`

Local stage paths:

- raw:
  - `csv/raw/a12_corr`
- manifest:
  - `config/current_manifests/manifest_a12_corr.csv`
- results:
  - `results/a12_corr_full`

## Additional TE PEC 80/85 Existing-Report Comparator

This debug-only dataset is a copied archive of the added TE PEC `80/85 deg`
existing-report exports:

- raw:
  - `csv/raw/te_pec_existing_reports_80_85_20260412`
- comparison code:
  - `code/compare_extra_te_pec_existing_reports.py`
- comparison outputs:
  - `results/te_pec_existing_reports_80_85_20260412/SUMMARY.md`
  - `results/te_pec_existing_reports_80_85_20260412/comparison_summary.json`

Current lock:

- no exact duplicate block pairs remain inside the new `Near_E_Table_1/2`
  high-angle blocks
- `Near_E_Table_3` is numerically identical to the `theta=80/85, kobs=2,
  w_plane=500 mm` subset of `Near_E_Table_1`
- `Near_E_Table_3_1` is numerically identical to the corresponding subset of
  `Near_E_Table_2`
- relative to the active merged TE PEC scattered CSV, the new re-extracts are
  closer after a global sign flip on the dominant `Ey` component
- therefore these files are currently a report-definition / sign-debug dataset,
  not a new truth source

## TE Report-Lock Bundle (`te_lock_0413`)

This bundle keeps the TE PEC and TE baseline high-angle existing-report exports
in one place:

- raw:
  - `csv/raw/te_lock_0413`
- comparison code:
  - `code/compare_te_report_lock_0413.py`
- comparison outputs:
  - `results/te_lock_0413/SUMMARY.md`
  - `results/te_lock_0413/comparison_summary.json`
- sanity-check outputs:
  - `results/te_lock_0413/SANITY_CHECK.md`
  - `results/te_lock_0413/sanity_check.json`

Current lock:

- `Near_E_Table_3 = z_m`
- `Near_E_Table_3_1 = z_p`
- both are `scattered`
- PEC:
  - duplicate-block symptom is removed in the new re-extracts
  - sign/report-definition ambiguity is still open
- baseline:
  - correct-surface comparison against the active merged baseline is relatively
    close
  - direct and sign-flipped comparisons are nearly identical
  - this points to a PEC-specific debug issue rather than a blanket TE export
    sign problem
- sanity-check verdict:
  - baseline path: pass
  - PEC duplicate symptom removed: pass
  - PEC sign/report-definition shift still present: pass
  - promotion of the new PEC re-extracts into the active truth source: fail
- coefficient-sensitivity lock:
  - for the current **TE PEC** path, reinterpreting `z_p` as a local CS rotated
    by `180 deg` about global `y` does **not** change the extracted TE `R/T`
  - therefore the current old/new TE discrepancy is not explained by a simple
    local/global basis reinterpretation on `z_p`
  - the dominant coefficient-level mismatch remains on the transmission side

Important implementation lock:

- these runs must stay separated by `run_label`
- this is required because the corrected dataset contains multiple runs with
  identical `(case, pol, rect, theta_deg, observation_distance_lambda_scale)`
  but different `w_plane / l_plane`
- if `run_label` is dropped, distinct runs are merged and the truth table is
  corrupted

## PEC Interpretation

For the current rerun setup, PEC is not an infinite-plane reference.

Current geometry facts:

- PEC/material plate size: `500 mm`
- baseline marker: `1 mm`
- observation distance sweep:
  - `kobs = 0.5, 1, 2`
  - `z_obs = kobs * lambda(6.5 GHz)`
- transmission near-rectangle width / length: `20 mm`

Current interpretation lock:

- baseline residual near zero means the field reconstruction path is correct
- larger `kobs` helps TM significantly
- larger `kobs` does not resolve the high-angle TE PEC transmission residual by
  itself
- the corrected `z_p` coordinate set confirms the above

## Structure

- `code`
  - `build_truth_table.py`
  - `compare_extra_te_pec_existing_reports.py`
  - `generate_hfss_wide_manifest.py`
  - `generate_hfss_flat_manifest.py`
  - `io_adapter.py`
  - `geometry.py`
  - `incident_field.py`
  - `projection.py`
  - `estimator.py`
  - `qc.py`
  - `cp_transform.py`
- `config`
  - `geometry.yaml`
  - `manifest*.csv`
- `csv`
  - `raw`
  - `normalized`
- `results`
  - `truth_table_linear.csv`
  - `truth_table_cp.csv` (optional)
  - `qc_report.csv`
  - `debug_maps`

## Core Difference From `ideal_te_tm_stage`

`ideal_te_tm_stage` assumes a total-field-oriented path.

This stage is for HFSS scattered exports and mixed-field reruns, so the
reflection/transmission reconstruction is manifest-driven per file.

That difference is critical. If scattered exports are interpreted as total
fields, PEC reflection and transmission are both misread.

## Local TE/TM Definition

This stage keeps the ideal-stage local projector:

- `e_TE = normalize(n x k_i)`
- `e_TM,q = e_TE x k_q`

For the current geometry:

- slab plane: `z = 0`
- surface normal: `n = (0, 0, 1)`
- incident direction: `k_i = (sin(theta_i), 0, cos(theta_i))`

This gives:

- `e_TE = (0, 1, 0)`
- `e_TM,i = (cos(theta_i), 0, -sin(theta_i))`
- `e_TM,r = (-cos(theta_i), 0, -sin(theta_i))`

So:

- `NearEY` is the direct TE candidate
- TM must be reconstructed from `NearEX` and `NearEZ`

## Run

Wide 5x5 export:

```powershell
python .\analysis_stages\ideal_te_tm_scattered_stage\code\generate_hfss_wide_manifest.py --input-root .\analysis_stages\ideal_te_tm_scattered_stage\csv\raw\actual_center5x5_20260411
python .\analysis_stages\ideal_te_tm_scattered_stage\code\build_truth_table.py --manifest .\analysis_stages\ideal_te_tm_scattered_stage\config\manifest_actual_center5x5.csv --normalized-output .\analysis_stages\ideal_te_tm_scattered_stage\csv\normalized\actual_center5x5_20260411_normalized_measurements.csv --output-dir .\analysis_stages\ideal_te_tm_scattered_stage\results\actual_center5x5_20260411_full --with-cp-transform
```

Flat mixed-field rerun:

```powershell
python .\analysis_stages\ideal_te_tm_scattered_stage\code\generate_hfss_flat_manifest.py --input-dir .\analysis_stages\ideal_te_tm_scattered_stage\csv\raw\actual_new_runs_20260412 --output .\analysis_stages\ideal_te_tm_scattered_stage\config\manifest_actual_new_runs_20260412.csv
python .\analysis_stages\ideal_te_tm_scattered_stage\code\build_truth_table.py --manifest .\analysis_stages\ideal_te_tm_scattered_stage\config\manifest_actual_new_runs_20260412.csv --normalized-output .\analysis_stages\ideal_te_tm_scattered_stage\csv\normalized\actual_new_runs_20260412_normalized_measurements.csv --output-dir .\analysis_stages\ideal_te_tm_scattered_stage\results\actual_new_runs_20260412_full
```

Corrected `z_p` rerun:

```powershell
python .\analysis_stages\ideal_te_tm_scattered_stage\code\generate_hfss_wide_manifest.py --input-root .\analysis_stages\ideal_te_tm_scattered_stage\csv\raw\a12_corr --output .\analysis_stages\ideal_te_tm_scattered_stage\config\manifest_a12_corr.csv
python .\analysis_stages\ideal_te_tm_scattered_stage\code\build_truth_table.py --manifest .\analysis_stages\ideal_te_tm_scattered_stage\config\manifest_a12_corr.csv --normalized-output .\analysis_stages\ideal_te_tm_scattered_stage\csv\normalized\a12_corr_normalized.csv --output-dir .\analysis_stages\ideal_te_tm_scattered_stage\results\a12_corr_full
```

TE PEC 80/85 existing-report comparison:

```powershell
python .\analysis_stages\ideal_te_tm_scattered_stage\code\compare_extra_te_pec_existing_reports.py
```
