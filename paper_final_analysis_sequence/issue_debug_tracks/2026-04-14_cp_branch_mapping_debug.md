# CP Branch Mapping Debug Log

## Goal

Resolve the Stage 2 versus Stage 3 patch CP branch-label mismatch without
editing the legacy Stage 3 extraction script in place.

## Initial Assessment That Triggered The Debug

The trigger condition on `2026-04-14` was:

- ideal and LP-derived branches agreed
- patch CP branches appeared swapped
- Stage 4a showed ideal headline peaks at `10 deg`
- patch peaks still sat in the expected `25 deg to 40 deg` window

That combination implied two separate but linked tasks:

1. lock the branch mapping
2. remove the low-angle headline artifact

## Debug Path

1. Confirmed the Stage 2 ideal convention:
   - `Gamma_X = (R_TE + R_TM) / 2`
   - `Gamma_C = (R_TE - R_TM) / 2`
2. Rechecked the Stage 3 patch CP export:
   - smaller exported branch was `gamma_hat_c_cp_eff`
   - larger exported branch was `gamma_hat_x_cp_sys`
3. Rechecked the Stage 3 LP-derived bridge:
   - smaller derived branch was `gamma_x_from_lp`
   - larger derived branch was `gamma_c_from_lp`
4. Preserved the original Stage 4 run as the small-branch audit trail.
5. Built an isolated LP-anchor audit workspace.
6. Exported a convention-locked patch CP alias CSV.
7. Recomputed Stage 4b with:
   - explicit residual branch lock
   - oblique-only headline range

## Key Evidence

Main-range LP-anchor audit result:

- main rows audited: `29`
- ideal small = `Gamma_X`: `29 / 29`
- LP small = `gamma_x_from_lp`: `29 / 29`
- patch small = `gamma_hat_c_cp_eff`: `29 / 29`
- LP aligned vote: `29 / 29`
- patch swapped vote: `29 / 29`

Error comparison:

- LP aligned mean abs error: `0.071598`
- LP swapped mean abs error: `0.579540`
- patch aligned mean abs error: `0.573917`
- patch swapped mean abs error: `0.106229`

This makes the LP-aligned / patch-swapped interpretation decisive over the
current paper main range.

## Outputs Created

- LP-anchor workspace:
  - `analysis_stages/lp_anchor_branch_lock_20260414`
- alias export:
  - `analysis_stages/lp_anchor_branch_lock_20260414/results/patch_cp_extracted_with_lp_anchor_alias.csv`
- Stage 4a audit trail:
  - `analysis_stages/stage4_suppression_dual_20260414/results/STAGE4A_AUDIT_TRAIL.md`
- Stage 4b convention-locked rerun:
  - `analysis_stages/stage4b_convention_locked_20260414`
- Stage 4a vs Stage 4b comparison note:
  - `paper_final_analysis_sequence/issue_debug_tracks/2026-04-14_stage4a_vs_stage4b_debug.md`

## Final Lock

- `cp_residual_branch = gamma_hat_c_cp_eff`
- `cp_dominant_branch = gamma_hat_x_cp_sys`
- paper headline source:
  - Stage 4b, not Stage 4a
- headline lower bound:
  - `20 deg`

## Why The Stage 4b Choice Was Correct

Stage 4b followed the more physical of the two available fixes:

- chosen:
  - restrict the headline to the validated oblique range
- not chosen:
  - insert a denominator floor into `G_supp`

That choice preserves a clean interpretation:

- near normal incidence, the polarization basis becomes ill-conditioned
- so the paper headline should stay in the oblique operating range

This matches the actual Stage 4b outcome:

- ideal headline peaks moved out of the `10 deg` artifact edge
- patch peaks stayed unchanged in the expected mid-angle window
- `Delta_G` no longer exaggerated a low-angle antenna penalty

## Remaining Optional Check

The direct-CP one-point sanity run is still useful, but it is now a supplement
validation step rather than the critical-path blocker.
