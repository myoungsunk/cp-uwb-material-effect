# CP Branch Mapping Resolution Note

## Purpose

- Record the current Stage 2 vs Stage 3 branch-mapping mismatch.
- Define the safest interpretation rule for the current paper lock.
- Freeze the follow-up actions needed to restore ideal-style `X/C` naming.

## Status Update

The mismatch is now numerically locked enough for paper use through the
LP-anchor path, without changing the original patch script in place.

Completed follow-up actions:

- LP-anchor branch lock:
  - `analysis_stages/lp_anchor_branch_lock_20260414`
- aliased patch CP export:
  - `analysis_stages/lp_anchor_branch_lock_20260414/results/patch_cp_extracted_with_lp_anchor_alias.csv`
- Stage 4b convention-locked rerun:
  - `analysis_stages/stage4b_convention_locked_20260414`

Main-range LP-anchor verdict:

- ideal small branch = `Gamma_X`: `29 / 29`
- LP small branch = `gamma_x_from_lp`: `29 / 29`
- patch small branch = `gamma_hat_c_cp_eff`: `29 / 29`
- LP aligned vote: `29 / 29`
- patch swapped vote: `29 / 29`

So the current working mismatch is no longer just a suspicion. It is locked as
an aliasing issue in the Stage 3 patch export layer:

- residual patch branch alias:
  - `cp_residual_branch = gamma_hat_c_cp_eff`
- dominant patch branch alias:
  - `cp_dominant_branch = gamma_hat_x_cp_sys`

## Problem Statement

Stage 2 and Stage 3 both use the names `Gamma_X` and `Gamma_C`, but the
numerical branch ordering is not aligned.

- Stage 2 ideal CP transform is defined directly from linear truth:
  - `Gamma_X = (R_TE + R_TM) / 2`
  - `Gamma_C = (R_TE - R_TM) / 2`
- Stage 3 patch CP extraction uses different channel-level estimators:
  - `Gamma_X` from `LR/RL` reciprocity geometric mean
  - `Gamma_C_raw` from `RR`
  - `Gamma_C_corr = Gamma_C_raw - eps_eff * Gamma_X`

With the current locked data, the smaller ideal branch is `Gamma_X`, but the
smaller patch branch is `Gamma_C_corr`.

That means the current patch `X/C` labels should not be assumed to match the
ideal `X/C` labels one-to-one.

## Code Anchors

- Stage 2 ideal definition:
  - `analysis_stages/ideal_te_tm_scattered_stage/code/cp_transform.py`
- Stage 3 patch definition:
  - `analysis_stages/stage3_patch_paper_final_20260414/cp/code/gamma_extraction_v2.py`

## Evidence

Representative magnitudes at `6.5 GHz`:

| material | theta | ideal `Gamma_X` | ideal `Gamma_C` | patch `gamma_hat_x` | patch `gamma_hat_c_eff` | LP `gamma_x_from_lp` | LP `gamma_c_from_lp` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| concrete | `10 deg` | `0.0049` | `0.3677` | `0.4450` | `0.1808` | `0.0874` | `0.4865` |
| concrete | `30 deg` | `0.0367` | `0.3964` | `0.4288` | `0.0440` | `0.0551` | `0.4513` |
| concrete | `40 deg` | `0.0890` | `0.3882` | `0.4196` | `0.0334` | `0.0690` | `0.4308` |
| glass | `10 deg` | `0.0050` | `0.3378` | `0.4906` | `0.2003` | `0.0969` | `0.5368` |
| glass | `30 deg` | `0.0384` | `0.5388` | `0.5006` | `0.0588` | `0.0660` | `0.5296` |
| glass | `40 deg` | `0.0903` | `0.5617` | `0.5237` | `0.0348` | `0.0757` | `0.5405` |
| wood | `10 deg` | `0.0053` | `0.1091` | `0.1563` | `0.0621` | `0.0296` | `0.1705` |
| wood | `30 deg` | `0.0354` | `0.1912` | `0.2066` | `0.0149` | `0.0305` | `0.2140` |
| wood | `40 deg` | `0.0911` | `0.2174` | `0.2314` | `0.0428` | `0.0790` | `0.2274` |

## Interpretation

The current data support the following reading:

1. The ideal smaller branch is `Gamma_X`, not `Gamma_C`.
2. The LP-direct reconstruction tracks the ideal convention well:
   - `gamma_x_from_lp` tracks ideal `Gamma_X`
   - `gamma_c_from_lp` tracks ideal `Gamma_C`
3. The patch CP script behaves oppositely in naming:
   - `gamma_hat_c_cp_eff` tracks the ideal small branch
   - `gamma_hat_x_cp_sys` tracks the ideal large branch

So the most likely conclusion is:

- the current Stage 3 patch script's `X/C` labels are swapped relative to the
  ideal convention
- or the script is using a different handedness/co-cross convention that was
  never explicitly locked against a direct CP excitation

## Why Stage 4 Used The Small-Branch Rule

Because the branch naming is not yet locked, Stage 4 used the safest
branch-agnostic rule:

- `suppressed residual = smaller CP branch`

This is why Stage 4 computes the headline suppression using:

- ideal side: smaller of `Gamma_X`, `Gamma_C`
- patch side: smaller of `gamma_hat_x_cp_sys`, `gamma_hat_c_cp_eff`

In the current locked data, that becomes:

- ideal residual branch = `Gamma_X`
- patch residual branch = `gamma_hat_c_cp_eff`

## Resolution Path

### 1. Direct CP One-Point Sanity Run

Use one explicit HFSS direct-CP excitation point to lock handedness and branch
sign convention.

Recommended setup:

- frequency: `6.5 GHz`
- material: `concrete`
- angle: `30 deg`
- same geometry and observation setup as the locked ideal stage

Check:

- direct reflected CP co/cross components
- basis-transform prediction from Stage 2 linear truth
- handedness sign
- phase of the two circular branches

Acceptance rule:

- the direct CP run must identify which circular branch is the suppressed
  residual at the chosen point
- that identification must match one and only one of the Stage 3 patch export
  branches

Prepared isolated workspace:

- `analysis_stages/direct_cp_one_point_sanity_20260414/`
- fixed run spec:
  - `analysis_stages/direct_cp_one_point_sanity_20260414/config/RUN_SPEC.md`
- comparison script:
  - `analysis_stages/direct_cp_one_point_sanity_20260414/code/compare_direct_cp_one_point.py`
- direct export template:
  - `analysis_stages/direct_cp_one_point_sanity_20260414/data/direct_cp_measurement_template.csv`

### 2. Patch Script Re-Naming

Do not rename the legacy original patch-stage script in place first.

Instead:

1. keep the current legacy field names for backward traceability
2. add explicit alias columns in the isolated export layer
3. only after the direct CP sanity check passes, freeze the ideal-style names

If the current evidence is confirmed, the alias mapping should become:

- current `gamma_hat_c_cp_eff` -> ideal-style residual CP branch
- current `gamma_hat_x_cp_sys` -> ideal-style dominant CP branch

For paper safety, the preferred intermediate names are:

- `cp_branch_small_mag`
- `cp_branch_large_mag`

This avoids overclaiming before the direct CP sanity lock is complete.

### 3. LP-Direct Anchor

Use LP-direct results as the convention bridge because LP is already tied to
the local linear basis.

Procedure:

1. compute
   - `gamma_x_from_lp = (R_hat_zz_sys + R_hat_yy_sys)/2`
   - `gamma_c_from_lp = (R_hat_zz_sys - R_hat_yy_sys)/2`
2. compare those against:
   - ideal `Gamma_X`, `Gamma_C`
   - patch `gamma_hat_x_cp_sys`, `gamma_hat_c_cp_eff`
3. use the closer correspondence as the branch lock across the angle range

Current evidence already points to:

- `gamma_x_from_lp` <-> ideal `Gamma_X`
- `gamma_c_from_lp` <-> ideal `Gamma_C`
- patch `gamma_hat_c_cp_eff` <-> ideal `Gamma_X`
- patch `gamma_hat_x_cp_sys` <-> ideal `Gamma_C`

## Recommended Execution Order

1. Keep Stage 4 as-is for now, but cite this note.
2. Run the direct CP one-point sanity check.
3. Freeze the branch mapping using LP-direct plus the direct CP check.
4. Add alias columns to the isolated Stage 3 export.
5. Regenerate Stage 4 with convention-fixed branch names.

## Paper-Safe Wording Until The Lock Is Closed

- Use `smaller CP branch` and `larger CP branch` in internal notes.
- Avoid claiming that Stage 3 `Gamma_X` and ideal Stage 2 `Gamma_X` are already
  the same physical branch by notation alone.
- Keep `ground truth` reserved for the ideal linear/CP transform only.
