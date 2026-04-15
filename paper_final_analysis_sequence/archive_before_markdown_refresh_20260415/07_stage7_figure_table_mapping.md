# Stage 7. Figure and Table Mapping

Execution date: `2026-04-14`

## Current Status

- executed and locked
- main-text mapping now points only to locked Stage 1 to 6 outputs
- branch naming ambiguity is closed by Stage 3a plus the direct CP one-point sanity
- `eff` and PEC-based CP corrections are explicitly excluded from headline use

## Purpose

- bind each manuscript figure and table to one locked claim, one locked source
  set, and one reporting rule

## Inputs

- Stage 1 rerun lock in
  `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414`
- Stage 3a LP-anchor branch lock in
  `analysis_stages/lp_anchor_branch_lock_20260414/results`
- Stage 4f raw-primary reporting lock in
  `analysis_stages/stage4f_raw_primary_dual_20260414/results`
- direct CP one-point sanity in
  `analysis_stages/direct_cp_one_point_sanity_20260414/results`
- rejected correction-path audits in
  `analysis_stages/stage4g_eff_mechanism_audit_20260414/results` and
  `analysis_stages/stage4h_pec_based_cp_correction_20260414/results`
- Stage 5 discussion lock in
  `analysis_stages/stage5_odd_bounce_extension_20260414/results`
- Stage 6 internal frequency-robustness sweep in
  `analysis_stages/stage6_uwb_dispersion_sensitivity_20260414/results`

## Execution

1. Freeze the manuscript to three claim layers only:
   - `ideal`: material-limited upper bound
   - `LP-derived`: practical estimate closest to the ideal branch behavior
   - `CP raw`: conservative system result including antenna leakage floor
2. Keep all manuscript-facing gain plots and tables in the validated oblique
   ranges only:
   - concrete: `20 deg to 55 deg`
   - glass: `20 deg to 60 deg`
   - wood: `20 deg to 45 deg`
3. Exclude the following from headline figures and tables:
   - `Gamma_C_eff`
   - PEC-based CP corrections
   - peak-to-peak ideal-vs-patch comparisons at mismatched angles
4. Use range means or same-angle comparisons for Table I and text claims.
5. Keep convention checks, correction-model failure analysis, and internal UWB
   robustness as supplement-only items.

## Outputs

- final paper-element map below
- stage-side execution note:
  `analysis_stages/stage7_figure_table_mapping_20260414/results/STAGE7_FIGURE_TABLE_MAPPING.md`
- machine-readable manifest:
  `analysis_stages/stage7_figure_table_mapping_20260414/results/paper_element_map_20260414.csv`

## Pass Conditions

- every main-text element traces to locked CSV or markdown outputs only
- no headline element depends on `eff` or PEC-based CP correction
- Table I no longer uses unmatched peak-to-peak comparisons

## Next Stage Link

- this is the last pipeline stage
- it now feeds manuscript assembly, figure rendering, and caption polishing

## Paper Element Map

| Paper element | Status | Locked source(s) | Claim / rule |
| --- | --- | --- | --- |
| Fig. 1 | locked | `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414/truth_table_linear_locked.csv`; `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414/sanity_check/sanity_check_fresnel_comparison.csv` | `|R_TE|` and `|R_TM|` vs angle with Fresnel overlay. This is the Stage 1 truth lock. |
| Fig. 2 | locked | `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414/truth_table_cp_recomputed_20260414.csv` | Ideal CP basis transform only. Show `Gamma_X` as the small residual branch and `Gamma_C` as the dominant branch. |
| Fig. 3 | locked | `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414/truth_table_cp_recomputed_20260414.csv`; `analysis_stages/lp_anchor_branch_lock_20260414/results/patch_cp_extracted_with_lp_anchor_alias.csv`; `analysis_stages/lp_anchor_branch_lock_20260414/results/lp_anchor_branch_lock_main.csv` | Practical branch comparison. Overlay ideal residual, LP-derived residual, and CP raw residual after the Stage 3a alias lock. Do not use `eff` as a main curve here. |
| Fig. 4 (headline) | locked | `analysis_stages/stage4f_raw_primary_dual_20260414/results/stage4f_raw_primary_full.csv`; `analysis_stages/stage4h_pec_based_cp_correction_20260414/results/pec_based_cp_comparison_long.csv` filtered to `curve in {ideal, lp, cp_raw}` | Headline suppression plot over the validated oblique range. Main message is the gap between the ideal upper bound, the LP-derived practical estimate, and the conservative CP raw result. |
| Table I | locked | `analysis_stages/stage4f_raw_primary_dual_20260414/results/table1_raw_primary_means.csv`; `analysis_stages/stage4h_pec_based_cp_correction_20260414/results/pec_based_cp_comparison_summary.csv` | Report range-wise mean suppression by material. Use `ideal`, `LP-derived`, and `CP raw`. Avoid peak-to-peak values because peak angles differ across layers. |
| Supplement A | locked | `analysis_stages/lp_anchor_branch_lock_20260414/results/LP_ANCHOR_BRANCH_LOCK_SUMMARY.md`; `analysis_stages/lp_anchor_branch_lock_20260414/results/lp_anchor_branch_lock_full.csv` | Branch mapping resolution and patch alias lock. |
| Supplement B | locked | `analysis_stages/direct_cp_one_point_sanity_20260414/results/DIRECT_CP_ONE_POINT_WITH_REFERENCES.md`; `analysis_stages/direct_cp_one_point_sanity_20260414/results/direct_cp_one_point_comparison.csv` | Direct CP one-point sanity for convention and implementation consistency. |
| Supplement C | locked | `analysis_stages/stage4g_eff_mechanism_audit_20260414/results/STAGE4G_EFF_MECHANISM_AUDIT.md`; `analysis_stages/stage4h_pec_based_cp_correction_20260414/results/STAGE4H_PEC_BASED_CP_COMPARISON.md` | Rejected correction paths. Show why `eff` and PEC-based CP subtraction are supplementary only. |
| Supplement D | executed with caveat | `analysis_stages/stage6_uwb_dispersion_sensitivity_20260414/results/STAGE6_SUMMARY.md`; `analysis_stages/stage6_uwb_dispersion_sensitivity_20260414/results/uwb_dispersion_sensitivity_summary.csv` | Internal `3-10 GHz` robustness check under the locked analytic material model. Do not describe this as externally calibrated dispersion proof. |

## Caption Guardrails

- Use `upper bound` only for the ideal layer.
- Use `practical estimate` for LP-derived curves.
- Use `conservative system result` or `antenna-leakage-inclusive result` for
  CP raw.
- Do not describe `eff` as more physical than `raw`.
- Do not present PEC-based CP correction as a manuscript-facing improvement.
