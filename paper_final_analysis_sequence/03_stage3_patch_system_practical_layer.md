# Stage 3. Patch System Practical Layer

## Current Status

- Isolated Stage 3 numeric exports exist at:
  - `analysis_stages/stage3_patch_paper_final_20260414/cp/results/patch_cp_extracted.csv`
  - `analysis_stages/stage3_patch_paper_final_20260414/lp/results/patch_lp_extracted.csv`
- Paper-facing alias lock is added in Stage 3a:
  - `analysis_stages/lp_anchor_branch_lock_20260414/results_sharedcommon_check_20260415/patch_cp_extracted_with_lp_anchor_alias.csv`

## Purpose

- Separate practical system-stage behavior from the ideal material-only upper
  bound.
- Export patch tables on the locked paper angle/material grid.
- Keep raw and corrected CP residuals both available, but promote only the raw
  residual to the manuscript headline path.

## Locked Interpretation

- dominant patch CP branch:
  - `gamma_hat_cross_agm_cp` (legacy export: `gamma_hat_x_cp_sys`)
- primary residual patch CP branch:
  - `gamma_hat_rr_raw_cp` (legacy export: `gamma_hat_c_cp_raw`)
- supplementary corrected residual:
  - `gamma_hat_rr_leakage_corrected_cp` (legacy export: `gamma_hat_c_cp_eff`)
- Stage 3 leakage coefficient:
  - `m3_leakage_lr_over_rr` (legacy local name: `eps_eff`)
- LP bridge branches:
  - `gamma_x_from_lp`
  - `gamma_c_from_lp`

## Execution Summary

1. Stage 3 extracted CP and LP system-stage tables in an isolated workspace.
2. Non-paper lock angle `56 deg` was excluded from the paper-final join keys.
3. LP leakage monitors were kept row-wise for later audit.
4. Stage 3a then added branch-safe alias columns and later promoted the new
   canonical names while retaining legacy compatibility columns.

## Outputs

- CP table:
  - `analysis_stages/stage3_patch_paper_final_20260414/cp/results/patch_cp_extracted.csv`
- LP table:
  - `analysis_stages/stage3_patch_paper_final_20260414/lp/results/patch_lp_extracted.csv`
- branch-safe aliased CP table:
  - `analysis_stages/lp_anchor_branch_lock_20260414/results_sharedcommon_check_20260415/patch_cp_extracted_with_lp_anchor_alias.csv`

## Pass Conditions

- patch tables merge cleanly on `material, theta_deg`
- `56 deg` is excluded from paper-final comparison keys
- LP leakage monitors remain available on every main-claim row
- no manuscript headline uses `gamma_hat_rr_leakage_corrected_cp` as the primary patch
  residual

## Next Stage Link

- Stage 4b consumes the aliased CP export as an oblique branch-lock audit.
- Stage 4c consumes the same raw-primary alias for the paper-safe headline.
