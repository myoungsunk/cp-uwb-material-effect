# Stage 3a. LP Anchor Branch Lock

## Current Status

- Stage 3a was executed in the isolated workspace:
  - `analysis_stages/lp_anchor_branch_lock_20260414`
- Outputs now exist:
  - `analysis_stages/lp_anchor_branch_lock_20260414/results/lp_anchor_branch_lock_full.csv`
  - `analysis_stages/lp_anchor_branch_lock_20260414/results/lp_anchor_branch_lock_main.csv`
  - `analysis_stages/lp_anchor_branch_lock_20260414/results/lp_anchor_branch_lock_summary.csv`
  - `analysis_stages/lp_anchor_branch_lock_20260414/results/patch_cp_extracted_with_lp_anchor_alias.csv`
  - `analysis_stages/lp_anchor_branch_lock_20260414/results/LP_ANCHOR_BRANCH_LOCK_SUMMARY.md`

## Purpose

- Lock the CP residual/dominant branch mapping without touching the original
  patch CP extraction script.
- Use the LP-derived bridge as the lowest-cost convention anchor before any
  direct-CP one-point rerun.

## Inputs

- Stage 2 ideal CP truth table
- Stage 3 patch CP export
- Stage 3 LP patch export

## Execution

1. Join ideal CP, patch CP, and LP-derived rows on common material and
   `theta_deg`.
2. Restrict the branch-lock audit to the current main-claim rows only.
3. Verify three conditions row-by-row:
   - ideal small branch is `Gamma_X`
   - LP small branch is `gamma_x_from_lp`
   - patch small branch is `gamma_hat_c_cp_eff`
4. Compare aligned versus swapped magnitude errors:
   - LP path against ideal
   - patch CP path against ideal
5. Export patch CP alias columns without modifying the original Stage 3 files.

## Pass Conditions

- Main rows audited: `29`
- Ideal small branch = `Gamma_X`: `29 / 29`
- LP small branch = `gamma_x_from_lp`: `29 / 29`
- Patch small branch = `gamma_hat_c_cp_eff`: `29 / 29`
- LP aligned vote: `29 / 29`
- Patch swapped vote: `29 / 29`

## Locked Decision

- patch residual alias:
  - `cp_residual_branch = gamma_hat_c_cp_eff`
- patch dominant alias:
  - `cp_dominant_branch = gamma_hat_x_cp_sys`

## Error Comparison

- LP aligned mean abs error: `0.071598`
- LP swapped mean abs error: `0.579540`
- Patch aligned mean abs error: `0.573917`
- Patch swapped mean abs error: `0.106229`

This makes the LP-aligned / patch-swapped interpretation numerically decisive.

## Next Stage Link

- Stage 4b uses the aliased patch CP export from this stage.
