# Paper Final Analysis Sequence

This folder is the paper-wide execution and reporting layer for the final
CP odd-bounce material-effect analysis.

Numeric outputs stay in the existing stage workspaces under `analysis_stages/`.
This folder only locks the sequence, notation, pass conditions, and
paper-facing deliverables.

## Source of Truth

- Ideal TE/TM scattered stage:
  - `analysis_stages/ideal_te_tm_scattered_stage`
- CP patch system stage:
  - `analysis_stages/patch_cp_stage_system`
- LP patch system stage:
  - `analysis_stages/patch_lp_stage_system`
- Active range/diagnosis locks:
  - `analysis_stages/ideal_te_tm_scattered_stage/data/material_cp_valid_range_diagnosis_20260413.md`
  - `analysis_stages/ideal_te_tm_scattered_stage/data/pec_observation_setup_diagnosis_20260413.md`

## Stage Status

| Stage | File | Status | Note |
| --- | --- | --- | --- |
| 0 | `00_stage0_notation_lock.md` | drafted | Paper-wide notation lock written here. |
| 1 | `01_stage1_ideal_te_tm_truth.md` | rerun verified | `2026-04-14` rerun reproduced the locked linear truth and Fresnel sanity outputs. |
| 2 | `02_stage2_ideal_cp_upper_bound.md` | rerun verified | `2026-04-14` recomputed CP table matched the locked CP table exactly. |
| 3 | `03_stage3_patch_system_practical_layer.md` | isolated workspace executed | Stage 3 exports were generated in `analysis_stages/stage3_patch_paper_final_20260414` without touching the original stage folders. |
| 3a | `03a_lp_anchor_branch_lock.md` | isolated workspace executed | LP-derived bridge locked the patch CP residual/dominant alias in `analysis_stages/lp_anchor_branch_lock_20260414`. |
| 4 | `04_stage4_suppression_gain_dual_metric.md` | audit trail preserved | This now functions as Stage 4a small-branch audit trail in `analysis_stages/stage4_suppression_dual_20260414`. |
| 4b | `04b_stage4b_convention_locked_oblique.md` | isolated workspace executed | Convention-locked oblique headline outputs were generated in `analysis_stages/stage4b_convention_locked_20260414`. |
| 4c | `04c_stage4f_raw_primary_dual_reporting.md` | isolated workspace executed | Raw-primary dual reporting is now the paper-safe Stage 4 headline in `analysis_stages/stage4f_raw_primary_dual_20260414`. |
| 5 | `05_stage5_odd_bounce_extension.md` | executed and locked | Odd-bounce extension text is locked in `analysis_stages/stage5_odd_bounce_extension_20260414`. |
| 6 | `06_stage6_uwb_dispersion_sensitivity.md` | executed with caveat | Internal `3-10 GHz` robustness sweep is locked in `analysis_stages/stage6_uwb_dispersion_sensitivity_20260414`, but it is not an externally calibrated dispersion proof. |
| 7 | `07_stage7_figure_table_mapping.md` | executed and locked | Final paper element mapping is locked here and mirrored in `analysis_stages/stage7_figure_table_mapping_20260414`. |

## Important Lock

- The currently confirmed ideal-material lock is the refreshed
  `5000 mm / k_obs = 5` path.
- Valid range is already locked:
  - concrete: `10 deg to 55 deg`
  - glass: `10 deg to 60 deg`
  - wood: `10 deg to 45 deg`
  - shared conservative range: `10 deg to 45 deg`
- Manuscript suppression reporting is additionally restricted to the oblique
  headline ranges:
  - concrete: `20 deg to 55 deg`
  - glass: `20 deg to 60 deg`
  - wood: `20 deg to 45 deg`
- `ground truth` is reserved for Fresnel/ideal TE/TM.
- Patch quantities stay explicitly labeled as system-stage or effective bounds.

## Sequence

1. Read `00_stage0_notation_lock.md` before editing captions, legends, tables,
   or manuscript notation.
2. If a paper-facing issue needs independent tracking, open:
   - `issue_debug_tracks/`
3. Reconfirm the ideal lock from Stages 1 and 2 before touching patch-stage
   comparisons.
4. Export standardized patch CSVs in Stage 3 before locking the branch mapping
   with Stage 3a.
5. Keep Stage 4 as the small-branch audit trail, then use Stage 4b for the
   convention-locked oblique comparison layer.
6. Use Stage 4c as the current paper-safe raw-primary reporting layer.
7. Use Stage 5 for the manuscript discussion scope, Stage 6 as a
   supplement-only internal robustness check, and Stage 7 for the final paper
   element map.

## Current Gap

There is no remaining headline-blocking numeric issue in the current lock.
The remaining work is manuscript assembly, final figure rendering, and caption
polishing. Optional reviewer-defense extensions are additional direct-CP spot
checks or a frequency-dependent material model, but neither is required for the
current paper-safe claim set.

## Issue Track

- Separate problem/debug markdown management now lives in:
  - `paper_final_analysis_sequence/issue_debug_tracks`
- Closed issue:
  - CP branch mapping mismatch
- Retained supplementary limitation:
  - `eff` correction-model validity and PEC-based CP subtraction remain
    supplement-only because they can oversubtract relative to the ideal
    upper-bound reference
