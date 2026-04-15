# Stage 4a. CP Branch Mapping Resolution Note

## Current Closure State

The original branch-mapping mismatch is now closed enough for paper use.

What is locked:

- Stage 2 internal labels are now explicit:
  - `Gamma_same` = paper `Gamma_X`
  - `Gamma_flip` = paper `Gamma_C`
- Stage 3a LP-anchor lock is decisive on the current main range.
- The manuscript-facing patch residual alias is now `gamma_hat_rr_raw_cp`
  (legacy export: `gamma_hat_c_cp_raw`).
- The direct CP one-point sanity has been executed and closes convention /
  implementation consistency.

What remains supplementary only:

- `gamma_hat_rr_leakage_corrected_cp` (legacy export: `gamma_hat_c_cp_eff`)
- PEC-based CP subtraction

## Main-Range LP-Anchor Verdict

- ideal small branch = `Gamma_same`: `29 / 29`
- LP small branch = `gamma_x_from_lp`: `29 / 29`
- patch eff small branch = `gamma_hat_rr_leakage_corrected_cp`: `29 / 29`
- LP aligned vote: `29 / 29`
- patch eff swapped vote: `29 / 29`

## Interpretation

The evidence still says two things at once:

1. The ideal and LP-derived branches align naturally:
   - `Gamma_same` / paper `Gamma_X` is the ideal small residual branch
   - `gamma_x_from_lp` tracks that same residual behavior
2. The patch eff branch is numerically the small branch, but it is not
   manuscript-safe as the primary residual because same-angle audits show
   over-correction behavior

So the paper-safe lock is:

- authoritative patch residual alias:
  - `cp_residual_branch = gamma_hat_rr_raw_cp`
- authoritative patch dominant alias:
  - `cp_dominant_branch = gamma_hat_cross_agm_cp`
- supplementary corrected residual:
  - `cp_residual_branch_supplementary = gamma_hat_rr_leakage_corrected_cp`

## Direct CP One-Point Sanity

- executed at:
  - `concrete / 30 deg / 6.5 GHz`
- current locked output:
  - `analysis_stages/paper_code_review_bundle_20260414/code/direct_cp_one_point_sanity_20260414/results_sharedcommon_check_20260415/DIRECT_CP_ONE_POINT_WITH_REFERENCES.md`

Current interpretation:

- it validates convention and implementation consistency
- it does not promote `eff` over `raw`
- the remaining issue is correction-model validity, not handedness labeling

## Paper-Safe Wording

- use `Gamma_same / Gamma_flip` or `same-hand / flipped-hand` in internal audit
  notes
- use paper symbols `Gamma_X / Gamma_C` only with the explicit Stage 2 mapping
- use `gamma_hat_rr_raw_cp` as the primary patch residual in manuscript claims
