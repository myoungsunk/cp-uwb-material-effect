# Direct CP One-Point Sanity

## Purpose

This isolated workspace freezes the direct-CP one-point sanity procedure used
to lock handedness and co/cross convention without modifying the legacy Stage 2
or Stage 3 pipelines.

The fixed sanity point is:

- material: `concrete`
- incidence angle: `30 deg`
- frequency: `6.5 GHz`

## Inputs

- Stage 2 ideal CP truth:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414/truth_table_cp_recomputed_20260414.csv`
- Stage 2 geometry lock:
  - `analysis_stages/ideal_te_tm_scattered_stage/config/geometry_material_5000mm_kobs5.yaml`
- Stage 3 patch CP export:
  - `analysis_stages/stage3_patch_paper_final_20260414/cp/results/patch_cp_extracted.csv`
- Stage 3 LP bridge export:
  - `analysis_stages/stage3_patch_paper_final_20260414/lp/results/patch_lp_extracted.csv`
- Future direct-CP HFSS export:
  - `data/direct_cp_measurement_template.csv`

## Workflow

1. Generate the frozen reference snapshot from the already locked Stage 2/3
   outputs.
2. Run one direct-CP HFSS point at the fixed geometry.
3. Fill the measurement CSV with the two reflected CP branches.
4. Re-run the comparison script to identify which receive CP branch is the
   small residual branch.

## Commands

Generate the current reference snapshot:

```powershell
python code/compare_direct_cp_one_point.py `
  --material concrete `
  --theta-deg 30 `
  --freq-ghz 6.5 `
  --truth-csv ..\ideal_te_tm_scattered_stage\results\current_manifest_runs\material_5000mm_kobs5_phase0_nominal_rerun_20260414\truth_table_cp_recomputed_20260414.csv `
  --patch-cp-csv ..\stage3_patch_paper_final_20260414\cp\results\patch_cp_extracted.csv `
  --lp-csv ..\stage3_patch_paper_final_20260414\lp\results\patch_lp_extracted.csv `
  --output-dir results
```

Re-run after the direct-CP point is exported:

```powershell
python code/compare_direct_cp_one_point.py `
  --material concrete `
  --theta-deg 30 `
  --freq-ghz 6.5 `
  --truth-csv ..\ideal_te_tm_scattered_stage\results\current_manifest_runs\material_5000mm_kobs5_phase0_nominal_rerun_20260414\truth_table_cp_recomputed_20260414.csv `
  --patch-cp-csv ..\stage3_patch_paper_final_20260414\cp\results\patch_cp_extracted.csv `
  --lp-csv ..\stage3_patch_paper_final_20260414\lp\results\patch_lp_extracted.csv `
  --measurement-csv data\direct_cp_measurement_template.csv `
  --output-dir results
```

## Outputs

- `results/direct_cp_target_reference.csv`
- `results/direct_cp_target_reference.md`
- `results/direct_cp_comparison.csv` after measurement is available
- `results/direct_cp_comparison.md` after measurement is available
- `results/direct_cp_one_point_normalized.csv` after LOS/M3/PEC/CONCRETE references are available
- `results/DIRECT_CP_ONE_POINT_WITH_REFERENCES.md` after LOS/M3/PEC/CONCRETE references are available

## Interpretation Rule

Until the direct-CP point is available, use only:

- `small CP branch`
- `large CP branch`

Do not freeze ideal-style `X/C` naming on the Stage 3 patch export until the
direct-CP point and LP bridge both support the same mapping.
