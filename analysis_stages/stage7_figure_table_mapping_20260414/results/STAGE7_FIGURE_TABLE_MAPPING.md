# Stage 7 Figure/Table Mapping

Execution date: `2026-04-14`

## Goal

Freeze the paper-facing mapping after the Stage 4 raw-primary lock, the Stage
3a LP-anchor branch lock, the direct CP one-point sanity, and the Stage 6
internal robustness sweep.

## Final Manuscript Layers

- `ideal`: material-limited upper bound
- `LP-derived`: practical estimate closest to ideal same-angle behavior
- `CP raw`: conservative antenna-leakage-inclusive system result

The following are excluded from headline use:

- `CP eff`
- PEC-based CP corrections
- unmatched peak-to-peak comparisons

## Valid Reporting Ranges

- concrete: `20 deg to 55 deg`
- glass: `20 deg to 60 deg`
- wood: `20 deg to 45 deg`

## Locked Element Map

| Element | Main source | Supporting source | Final use |
| --- | --- | --- | --- |
| Fig. 1 | `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414/truth_table_linear_locked.csv` | `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414/sanity_check/sanity_check_fresnel_comparison.csv` | Main text |
| Fig. 2 | `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414/truth_table_cp_recomputed_20260414.csv` | none | Main text |
| Fig. 3 | `analysis_stages/lp_anchor_branch_lock_20260414/results/patch_cp_extracted_with_lp_anchor_alias.csv` | `analysis_stages/lp_anchor_branch_lock_20260414/results/lp_anchor_branch_lock_main.csv` and Stage 2 CP truth table | Main text |
| Fig. 4 | `analysis_stages/stage4f_raw_primary_dual_20260414/results/stage4f_raw_primary_full.csv` | `analysis_stages/stage4h_pec_based_cp_correction_20260414/results/pec_based_cp_comparison_long.csv` filtered to `lp` | Main text |
| Table I | `analysis_stages/stage4f_raw_primary_dual_20260414/results/table1_raw_primary_means.csv` | `analysis_stages/stage4h_pec_based_cp_correction_20260414/results/pec_based_cp_comparison_summary.csv` | Main text |
| Supp. A | `analysis_stages/lp_anchor_branch_lock_20260414/results/LP_ANCHOR_BRANCH_LOCK_SUMMARY.md` | `lp_anchor_branch_lock_full.csv` | Supplement |
| Supp. B | `analysis_stages/direct_cp_one_point_sanity_20260414/results/DIRECT_CP_ONE_POINT_WITH_REFERENCES.md` | `direct_cp_one_point_comparison.csv` | Supplement |
| Supp. C | `analysis_stages/stage4g_eff_mechanism_audit_20260414/results/STAGE4G_EFF_MECHANISM_AUDIT.md` | `analysis_stages/stage4h_pec_based_cp_correction_20260414/results/STAGE4H_PEC_BASED_CP_COMPARISON.md` | Supplement |
| Supp. D | `analysis_stages/stage6_uwb_dispersion_sensitivity_20260414/results/STAGE6_SUMMARY.md` | `uwb_dispersion_sensitivity_summary.csv` | Supplement with caveat |

## Table I Rule

Use range-wise mean suppression, not peak-to-peak suppression. Peak angles differ
across `ideal`, `LP-derived`, and `CP raw`, so peak-only comparisons can falsely
make a practical curve look better than the ideal upper bound.

## Headline Figure Rule

Figure 4 should show only:

- `ideal`
- `LP-derived`
- `CP raw`

Do not draw `CP eff`, PEC-simple, or PEC-ratio curves in the headline plot.

## Closed Issues Relevant To Stage 7

- branch naming mismatch: closed by Stage 3a plus direct CP one-point sanity
- `eff` over-correction: retained as supplementary limitation only
- PEC-based reflective leakage correction: rejected for headline use
- Stage 6 external-dispersion proof: not claimed
