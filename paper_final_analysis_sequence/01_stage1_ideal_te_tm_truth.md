# Stage 1. Ideal TE/TM Truth Table

## Current Status

- Active ideal/material lock already exists under:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal`
- Reproducibility rerun completed on `2026-04-14` under:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414`
- That run already contains:
  - `truth_table_linear_locked.csv`
  - `truth_table_cp.csv`
  - `qc_report.csv`
  - `sanity_check/sanity_check_fresnel_comparison.csv`
- The diagnosis note reports:
  - `qc_report.csv` fail rows = `0`
  - TE main region: `10 deg to 60 deg`
  - TM main region: `10 deg to 70 deg`
- The `2026-04-14` rerun verified:
  - QC fail rows = `0`
  - `truth_table_linear_locked.csv`: byte-identical to the locked reference
  - `sanity_check_fresnel_comparison.csv`: byte-identical to the locked reference
  - `truth_table_cp.csv`: numerically identical within floating-point roundoff
    only

## Purpose

- Freeze the material-slab linear-basis truth table against Fresnel.
- Lock the ideal reference before any CP or patch comparison.

## Inputs

- Data:
  - `analysis_stages/ideal_te_tm_scattered_stage/data/0.TE_PEC`
  - `analysis_stages/ideal_te_tm_scattered_stage/data/0.TM_PEC`
  - `analysis_stages/ideal_te_tm_scattered_stage/data/1.TE_baseline`
  - `analysis_stages/ideal_te_tm_scattered_stage/data/1.TM_baseline`
  - `analysis_stages/ideal_te_tm_scattered_stage/data/2.TE_concrete`
  - `analysis_stages/ideal_te_tm_scattered_stage/data/2.TE_glass`
  - `analysis_stages/ideal_te_tm_scattered_stage/data/2.TE_wood`
  - `analysis_stages/ideal_te_tm_scattered_stage/data/2.TM_concrete1`
  - `analysis_stages/ideal_te_tm_scattered_stage/data/2.TM_glass1`
  - `analysis_stages/ideal_te_tm_scattered_stage/data/2.TM_wood1`
- Code:
  - `analysis_stages/ideal_te_tm_scattered_stage/code/build_truth_table.py`
  - `analysis_stages/ideal_te_tm_scattered_stage/code/projection.py`
  - `analysis_stages/ideal_te_tm_scattered_stage/code/sanity_check_fresnel.py`
  - `analysis_stages/ideal_te_tm_scattered_stage/code/te_tm_extraction_ideal_plane_wave.py`
- Active manifest:
  - `analysis_stages/ideal_te_tm_scattered_stage/config/current_manifests/manifest_material_5000mm_kobs5_phase0_nominal.csv`

## Execution

1. Reproject the exported fields onto the local TE/TM basis.
2. Rebuild the locked linear truth table from the active manifest:

```powershell
python .\analysis_stages\ideal_te_tm_scattered_stage\code\build_truth_table.py `
  --manifest .\analysis_stages\ideal_te_tm_scattered_stage\config\current_manifests\manifest_material_5000mm_kobs5_phase0_nominal.csv `
  --geometry .\analysis_stages\ideal_te_tm_scattered_stage\config\geometry_material_5000mm_kobs5.yaml `
  --normalized-output .\analysis_stages\ideal_te_tm_scattered_stage\results\current_manifest_runs\material_5000mm_kobs5_phase0_nominal\normalized_measurements.csv `
  --output-dir .\analysis_stages\ideal_te_tm_scattered_stage\results\current_manifest_runs\material_5000mm_kobs5_phase0_nominal `
  --with-cp-transform
```

3. Re-run the Fresnel comparison on the locked linear table:

```powershell
python .\analysis_stages\ideal_te_tm_scattered_stage\code\sanity_check_fresnel.py `
  --input .\analysis_stages\ideal_te_tm_scattered_stage\results\current_manifest_runs\material_5000mm_kobs5_phase0_nominal\truth_table_linear_locked.csv `
  --output-dir .\analysis_stages\ideal_te_tm_scattered_stage\results\current_manifest_runs\material_5000mm_kobs5_phase0_nominal\sanity_check `
  --slab-thickness-m 0.1
```

## Outputs

- Locked linear truth table:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal/truth_table_linear_locked.csv`
- Reproducibility rerun outputs:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414/truth_table_linear_locked.csv`
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414/truth_table_cp.csv`
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414/qc_report.csv`
- Fresnel comparison:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal/sanity_check/sanity_check_fresnel_comparison.csv`
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414/sanity_check/sanity_check_fresnel_comparison.csv`
- Figure source for paper Fig. 1:
  - `|R_TE|` and `|R_TM|` versus `theta_i`, material-wise, with Fresnel overlay

## Pass Conditions

- `qc_report.csv` fail rows = `0`
- TE main region remains `10 deg to 60 deg`
- TM main region remains `10 deg to 70 deg`
- Material Fresnel sanity remains consistent with the 2026-04-13 diagnosis lock
- Wood TM limitation remains carried forward:
  - wood main-claim upper angle = `45 deg`
- Reproducibility check:
  - linear truth table reproduced exactly
  - Fresnel comparison reproduced exactly
  - CP table differences are limited to floating-point formatting noise at
    about `1e-16`

## Next Stage Link

- Stage 2 consumes the locked `truth_table_linear_locked.csv` and derives the
  CP upper bound from it.
