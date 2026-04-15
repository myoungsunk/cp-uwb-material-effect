# Stage 4b. Convention-Locked Oblique Suppression

## Current Status

- Stage 4b was executed in the isolated workspace:
  - `analysis_stages/stage4b_convention_locked_20260414`
- Outputs now exist:
  - `analysis_stages/stage4b_convention_locked_20260414/results/suppression_gain_stage4b.csv`
  - `analysis_stages/stage4b_convention_locked_20260414/results/suppression_gain_stage4b_full.csv`
  - `analysis_stages/stage4b_convention_locked_20260414/results/suppression_gain_stage4b_table1.csv`
  - `analysis_stages/stage4b_convention_locked_20260414/results/fig4b_headline_suppression_locked.png`
  - `analysis_stages/stage4b_convention_locked_20260414/results/STAGE4B_SUMMARY.md`

## Current Role

- Stage 4b remains the branch-locked oblique comparison layer.
- The current paper-safe headline reporting moved to:
  - `paper_final_analysis_sequence/04c_stage4f_raw_primary_dual_reporting.md`

## Important Caution

Stage 4b fixed the branch mapping and the low-angle reporting artifact, but it
did not fully close the same-angle upper-bound question.

The follow-up same-angle audit in:

- `analysis_stages/stage4c_same_angle_gap_audit_20260414`

showed that the corrected patch residual branch can become smaller than the
ideal residual branch at many matched-angle rows. So Stage 4b should currently
be used as an oblique comparison figure, not yet as a strict
`ideal >= patch` upper-bound proof.

## Purpose

- Recompute the headline suppression metric after the CP residual branch is
  explicitly locked by Stage 3a.
- Remove the small-angle inflation from the headline claim by restricting the
  reporting range to oblique incidence only.

## Main Lock

- ideal residual branch: `Gamma_X`
- patch residual branch: `cp_residual_branch`
- patch alias source: `gamma_hat_c_cp_eff`
- branch lock source: `lp_anchor_branch_lock_20260414`
- headline lower bound: `20 deg`

## Pass Conditions

- Main-claim rows = `23`: pass
- Patch peak remains in the expected `25 deg to 40 deg` window: pass
  - concrete: `24.60 dB @ 35 deg`
  - glass: `25.45 dB @ 40 deg`
  - wood: `23.64 dB @ 30 deg`
- Ideal headline peak no longer collapses to the low-angle artifact zone: pass
  - concrete: `22.92 dB @ 20 deg`
  - glass: `23.55 dB @ 30 deg`
  - wood: `18.90 dB @ 20 deg`
- `Delta_G` stays moderate in the oblique range and no longer spikes
  artificially at `10 deg`: pass

## New Audit Caveat

The Stage 4b rerun succeeded as a branch-locked oblique comparison, but the
later Stage 4c same-angle audit found:

- corrected residual negative-gap rows:
  - `16 / 23`
- raw residual negative-gap rows:
  - `0 / 23`

So the `Delta_G` band in Stage 4b is not yet paper-safe as a universal
antenna-limited loss metric.

## Material Summary

- concrete:
  - reporting range: `20 to 55 deg`
  - peak `G_supp_ideal`: `22.92 dB @ 20 deg`
  - peak `G_supp_patch`: `24.60 dB @ 35 deg`
  - peak `Delta_G`: `8.42 dB @ 20 deg`
  - worst LP leakage on main rows: `-19.93 dB`
- glass:
  - reporting range: `20 to 60 deg`
  - peak `G_supp_ideal`: `23.55 dB @ 30 deg`
  - peak `G_supp_patch`: `25.45 dB @ 40 deg`
  - peak `Delta_G`: `8.09 dB @ 20 deg`
  - worst LP leakage on main rows: `-18.45 dB`
- wood:
  - reporting range: `20 to 45 deg`
  - peak `G_supp_ideal`: `18.90 dB @ 20 deg`
  - peak `G_supp_patch`: `23.64 dB @ 30 deg`
  - peak `Delta_G`: `4.35 dB @ 20 deg`
  - worst LP leakage on main rows: `-27.75 dB`

## Audit Trail

- Stage 4a remains preserved in:
  - `analysis_stages/stage4_suppression_dual_20260414`
- Stage 4a should be cited only as the small-branch audit trail.
- Stage 4b should currently be treated as an oblique comparison result, with
  Stage 4f raw-primary reporting used for the paper headline.
