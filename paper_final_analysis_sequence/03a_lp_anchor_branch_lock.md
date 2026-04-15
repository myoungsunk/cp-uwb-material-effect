# Stage 3a. LP Anchor Branch Lock

## Current Status

- Latest shared-common rerun outputs:
  - `analysis_stages/lp_anchor_branch_lock_20260414/results_sharedcommon_check_20260415/lp_anchor_branch_lock_full.csv`
  - `analysis_stages/lp_anchor_branch_lock_20260414/results_sharedcommon_check_20260415/lp_anchor_branch_lock_main.csv`
  - `analysis_stages/lp_anchor_branch_lock_20260414/results_sharedcommon_check_20260415/lp_anchor_branch_lock_summary.csv`
  - `analysis_stages/lp_anchor_branch_lock_20260414/results_sharedcommon_check_20260415/patch_cp_extracted_with_lp_anchor_alias.csv`
  - `analysis_stages/lp_anchor_branch_lock_20260414/results_sharedcommon_check_20260415/LP_ANCHOR_BRANCH_LOCK_SUMMARY.md`

## Purpose

- Lock the patch CP residual/dominant mapping without modifying the legacy
  Stage 3 extractor in place.
- Use LP-direct as the convention bridge against the ideal same/flip lock.

## Main-Range Verdict

- main rows audited: `29`
- ideal small branch = `Gamma_same` (paper `Gamma_X`): `29 / 29`
- LP small branch = `gamma_x_from_lp`: `29 / 29`
- patch eff small branch = `gamma_hat_rr_leakage_corrected_cp`: `29 / 29`
- LP aligned vote: `29 / 29`
- patch eff swapped vote: `29 / 29`

## Error Comparison

- LP aligned mean abs error: `0.071366`
- LP swapped mean abs error: `0.578750`
- patch eff aligned mean abs error: `0.529120`
- patch eff swapped mean abs error: `0.109407`

This keeps the LP-aligned / patch-swapped reading numerically decisive.

## Locked Decision

- authoritative patch residual alias:
  - `cp_residual_branch = gamma_hat_rr_raw_cp`
- authoritative patch dominant alias:
  - `cp_dominant_branch = gamma_hat_cross_agm_cp`
- supplementary corrected residual alias:
  - `cp_residual_branch_supplementary = gamma_hat_rr_leakage_corrected_cp`

So `gamma_hat_rr_leakage_corrected_cp` remains useful as an audit signal, but it is no longer
the manuscript-facing residual branch.

## Next Stage Link

- Stage 4b uses this export as an alias-lock oblique audit.
- Stage 4c uses the same raw-primary alias as the paper-safe headline layer.
