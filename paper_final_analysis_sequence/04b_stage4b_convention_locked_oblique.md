# Stage 4b. Convention-Locked Oblique Suppression

## Current Status

- Latest Stage 4b shared-common rerun:
  - `analysis_stages/paper_code_review_bundle_20260414/code/stage4b_convention_locked_20260414/results_sharedcommon_check_20260415/suppression_gain_stage4b.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/code/stage4b_convention_locked_20260414/results_sharedcommon_check_20260415/suppression_gain_stage4b_full.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/code/stage4b_convention_locked_20260414/results_sharedcommon_check_20260415/suppression_gain_stage4b_table1.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/code/stage4b_convention_locked_20260414/results_sharedcommon_check_20260415/fig4b_headline_suppression_locked.png`

## Current Role

- Stage 4b is an oblique-only alias-lock comparison layer.
- It is no longer the manuscript headline source.
- The paper-safe headline reporting moved to Stage 4c raw-primary reporting.

## Main Lock

- ideal residual branch:
  - `Gamma_same` (paper `Gamma_X`)
- patch residual branch:
  - `cp_residual_branch_name`
- patch alias source:
  - `gamma_hat_rr_raw_cp`
- branch lock source:
  - `analysis_stages/lp_anchor_branch_lock_20260414/results_sharedcommon_check_20260415/patch_cp_extracted_with_lp_anchor_alias.csv`
- headline lower bound:
  - `20 deg`

## Row Counts

- full audit rows: `39`
- main-claim rows: `23`

## Material Summary

- concrete:
  - reporting range: `20 to 55 deg`
  - peak `G_supp_ideal`: `22.89 dB @ 20 deg`
  - peak `G_supp_patch_alias`: `10.76 dB @ 20 deg`
  - peak `Delta_G_alias`: `13.22 dB @ 30 deg`
  - worst LP leakage on main rows: `-19.93 dB`
- glass:
  - reporting range: `20 to 60 deg`
  - peak `G_supp_ideal`: `23.45 dB @ 30 deg`
  - peak `G_supp_patch_alias`: `11.23 dB @ 20 deg`
  - peak `Delta_G_alias`: `13.78 dB @ 30 deg`
  - worst LP leakage on main rows: `-18.45 dB`
- wood:
  - reporting range: `20 to 45 deg`
  - peak `G_supp_ideal`: `18.90 dB @ 20 deg`
  - peak `G_supp_patch_alias`: `9.04 dB @ 20 deg`
  - peak `Delta_G_alias`: `9.86 dB @ 20 deg`
  - worst LP leakage on main rows: `-27.75 dB`

## Important Caution

- Stage 4b is still an audit-layer figure.
- It uses the raw-primary alias, but it is not the final Table I / headline
  reporting layer.
- Same-angle manuscript-safe ordering and range-mean reporting are handled in
  Stage 4c.

## Audit Trail

- historical small-branch audit:
  - `paper_final_analysis_sequence/04_stage4_suppression_gain_dual_metric.md`
- authoritative raw-primary reporting:
  - `paper_final_analysis_sequence/04c_stage4f_raw_primary_dual_reporting.md`
