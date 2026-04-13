# Ideal TE/TM Stage

This stage is the material/slab-physics pipeline built around an analytic incident plane wave.

It is intentionally separate from the patch-inclusive `patch_cp_stage_system` and
`patch_lp_stage_system` pipelines. The primary output here is the linear-basis truth table:

- `R_TE(f, theta_i)`
- `T_TE(f, theta_i)`
- `R_TM(f, theta_i)`
- `T_TM(f, theta_i)`

## Structure

- `code`
  - `build_truth_table.py`: main pipeline
  - `generate_hfss_wide_manifest.py`: build a manifest from actual HFSS 5x5 wide exports
  - `io_adapter.py`: manifest/raw CSV normalization
  - `geometry.py`: direction and basis definitions
  - `incident_field.py`: analytic incident plane wave
  - `projection.py`: TE/TM scalar projection
  - `estimator.py`: matched plane-wave estimator
  - `qc.py`: baseline, PEC, fit, smoothness, passivity checks
  - `cp_transform.py`: optional linear-to-CP transform
  - `te_tm_extraction_ideal_plane_wave.py`: wrapper entrypoint
- `config`
  - `manifest.csv`: manifest template
  - `geometry.yaml`: source origin / QC config
- `csv`
  - `raw`: place PEC, baseline, and slab exports here
  - `normalized`: normalized common-schema dump
- `results`
  - `truth_table_linear.csv`
  - `truth_table_cp.csv` (optional)
  - `qc_report.csv`
  - `debug_maps`

## Core Approach

1. Normalize raw HFSS CSV exports into a common schema:
   `case, pol, rect, f_hz, theta_deg, point_id, x, y, z, Ex, Ey, Ez`
   The current adapter supports both:
   - already-normalized long CSV
   - HFSS center-grid wide CSV where `_u` is the row axis and `_v/Freq/theta/component` are encoded in the headers
2. Generate the analytic incident field from `source_origin_m`, `k_hat`, and the local TE/TM basis.
3. On the reflection plane, use `E_refl_only = E_total - E_inc`.
4. On the transmission plane, use `E_trans_only = E_total`.
5. Project vector fields into TE/TM scalar fields.
6. Estimate one complex plane-wave amplitude per rectangle using the matched-wave estimator.
7. Build `R_TE`, `T_TE`, `R_TM`, `T_TM` truth tables.
8. Use the PEC case to phase-lock the reflection convention.

## Local TE/TM Definition

This stage does not reuse the LP port projection used in the patch-stage code.

TE/TM are defined from the local plane of incidence:

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
- TM must be formed from `NearEX` and `NearEZ` through the local projector
- TM must not be read as a single global LP port axis

The PEC phase lock is configured so the default target is:

- `R_TE ~= -1`
- `R_TM ~= +1`
- `T ~= 0`

If a different sign convention is desired, change
`pec_target_reflection_te` / `pec_target_reflection_tm` in
`config/geometry.yaml`.

For the current HFSS ideal export set, the geometry config also matches the
actual setup:

- source reference point at `-100 mm` along `k_i`
- observation planes at `0.5 * lambda` along `k_r` / `k_t`
- wide-grid `_u/_v` mapped as:
  - `_u` -> local TE axis
  - `_v` -> negative local TM axis

## Run

```powershell
python .\\analysis_stages\\ideal_te_tm_stage\\code\\generate_hfss_wide_manifest.py --input-root .\\analysis_stages\\ideal_te_tm_stage\\csv\\raw\\actual_center5x5_20260411
python .\\analysis_stages\\ideal_te_tm_stage\\code\\build_truth_table.py --with-cp-transform
```

## Important Difference From Patch-Stage Code

- Patch-stage scripts operate on antenna-inclusive channel responses and use `M1/M2/M3` or metal normalization.
- This stage operates on pointwise field exports with an analytic incident plane wave.
- Baseline is used for QC, not as the main reference.
- TE/TM truth is produced first; CP quantities are optional second-stage derived outputs.
