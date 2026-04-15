# Stage 4. Suppression Gain Dual Metric

## Current Role

- This file is now the historical Stage 4a small-branch audit trail.
- It should not be used as the manuscript headline source.

## Current Status

- latest preserved small-branch rerun:
  - `analysis_stages/paper_code_review_bundle_20260414/code/stage4_dual_sharedcommon_check_20260415/suppression_gain_dual.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/code/stage4_dual_sharedcommon_check_20260415/suppression_gain_dual_full.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/code/stage4_dual_sharedcommon_check_20260415/suppression_gain_table1.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/code/stage4_dual_sharedcommon_check_20260415/fig4_headline_suppression_dual.png`

## What This Stage Still Means

- It records what happens if the headline metric is built from the numerically
  smaller CP branch at each row.
- On the ideal side, that smaller branch is `Gamma_same` (paper `Gamma_X`).
- On the patch side, this audit still picks `gamma_hat_rr_leakage_corrected_cp`.

So this stage remains useful as a diagnostic trail for:

- low-angle inflation behavior
- eff-centric branch behavior
- historical branch-mismatch reasoning

It is not the final paper-safe suppression metric.

## Current Historical Summary

- main-claim rows: `29`
- concrete:
  - peak `G_supp_ideal`: `31.43 dB @ 10 deg`
  - peak `G_supp_patch_small`: `24.60 dB @ 35 deg`
- glass:
  - peak `G_supp_ideal`: `33.50 dB @ 10 deg`
  - peak `G_supp_patch_small`: `13.95 dB @ 25 deg`
- wood:
  - peak `G_supp_ideal`: `24.98 dB @ 10 deg`
  - peak `G_supp_patch_small`: `19.66 dB @ 35 deg`

These are retained only as a diagnostic history because the ideal-side low-angle
peak and the patch-side eff branch are both no longer used for the manuscript
headline.

## Successor Stages

- oblique alias-lock comparison:
  - `paper_final_analysis_sequence/04b_stage4b_convention_locked_oblique.md`
- authoritative paper-safe reporting:
  - `paper_final_analysis_sequence/04c_stage4f_raw_primary_dual_reporting.md`
