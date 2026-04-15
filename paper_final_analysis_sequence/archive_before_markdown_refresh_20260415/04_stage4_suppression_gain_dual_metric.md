# Stage 4. Suppression Gain Dual Metric

## Current Role

- This document now serves as the Stage 4a small-branch audit trail.
- The convention-locked paper headline moved to:
  - `paper_final_analysis_sequence/04b_stage4b_convention_locked_oblique.md`
- The original Stage 4a outputs remain preserved in:
  - `analysis_stages/stage4_suppression_dual_20260414`

## Current Status

- Stage 4 was executed in the isolated workspace:
  - `analysis_stages/stage4_suppression_dual_20260414`
- Outputs now exist:
  - `analysis_stages/stage4_suppression_dual_20260414/results/suppression_gain_dual.csv`
  - `analysis_stages/stage4_suppression_dual_20260414/results/suppression_gain_dual_full.csv`
  - `analysis_stages/stage4_suppression_dual_20260414/results/suppression_gain_table1.csv`
  - `analysis_stages/stage4_suppression_dual_20260414/results/fig4_headline_suppression_dual.png`
  - `analysis_stages/stage4_suppression_dual_20260414/results/STAGE4_SUMMARY.md`
- Main-claim row count is locked at `29`.

## Purpose

- Report odd-bounce rejection using two clearly separated layers:
  - `G_supp_ideal`: material-limited upper bound
  - `G_supp_patch`: practical patch-achievable value

## Inputs

- Stage 1 locked linear truth table
- Stage 2 locked CP truth table
- Stage 3 exported patch tables

## Execution

1. Compute the worst-case linear benchmark:
   - `B(theta) = max(|R_TE(theta)|, |R_TM(theta)|)`
2. Audit both label-based CP branches:
   - ideal:
     - `B / |Gamma_X|`
     - `B / |Gamma_C|`
   - patch:
     - `B / |gamma_hat_x_cp_sys|`
     - `B / |gamma_hat_c_cp_eff|`
3. Use the smaller CP branch as the residual branch for the headline metric.
   This is an inference from the locked data because the branch naming is not
   numerically aligned between the ideal and patch stages.
4. Compute the final suppression gain:
   - `G_supp_ideal(theta) = 20 log10(B(theta) / |small ideal branch|)`
   - `G_supp_patch(theta) = 20 log10(B(theta) / |small patch branch|)`
4. Compute the antenna-limited gap:
   - `Delta_G(theta) = G_supp_ideal(theta) - G_supp_patch(theta)`
5. Enforce the material-specific valid ranges only:
   - concrete: `<= 55 deg`
   - glass: `<= 60 deg`
   - wood: `<= 45 deg`

## Outputs

- Final full audit table:
  - `analysis_stages/stage4_suppression_dual_20260414/results/suppression_gain_dual_full.csv`
- Final main-claim table:
  - `analysis_stages/stage4_suppression_dual_20260414/results/suppression_gain_dual.csv`
- Paper headline figure source:
  - ideal curve
  - patch curve
  - shaded gap band
- Paper Table I source:
  - `analysis_stages/stage4_suppression_dual_20260414/results/suppression_gain_table1.csv`
  - peak suppression
  - peak angle
  - valid range by material

## Pass Conditions

- Main-claim rows = `29`: pass
- `G_supp_patch` reaches `>= 15 dB` in the expected mid-angle window: pass
  - concrete peak: `24.60 dB @ 35 deg`
  - glass peak: `25.45 dB @ 40 deg`
  - wood peak: `23.64 dB @ 30 deg`
- `G_supp_ideal` exceeds `20 dB` in the `25 deg to 40 deg` window for
  concrete/glass and remains strong for wood: pass
- `Delta_G` remains explainable as an antenna-limited practical loss, with
  larger penalties allowed near higher angles: pass
- The absolute ideal peak angle is not in the originally expected
  `25 deg to 40 deg` window. In the locked data it appears at `10 deg` because
  the smaller ideal CP branch is already very small there. This should be
  described as an observed result, not silently forced into the earlier
  expectation.

## Next Stage Link

- Stage 4b uses the LP-anchored branch lock plus an oblique-only reporting
  range for the paper headline.
- Stage 5 should cite the Stage 4b interpretation of `G_supp_ideal` versus
  `G_supp_patch`, not the Stage 4a low-angle audit peak.

## Output Dependency

- Stage 4 is complete for the current isolated-workspace lock.

## Locked Branch Mapping

- In the current locked data, the smaller ideal branch is always:
  - `Gamma_X_mag`
- In the current locked patch CP export, the smaller branch is always:
  - `gamma_hat_c_cp_eff_mag`
- Therefore the headline suppression metric is currently using:
  - ideal residual branch: `Gamma_X`
  - patch residual branch: `gamma_hat_c_cp_eff`
- See the separate convention note:
  - `paper_final_analysis_sequence/04a_cp_branch_mapping_resolution_note.md`
- The explicit LP-anchor lock and aliased patch export now exist in:
  - `paper_final_analysis_sequence/03a_lp_anchor_branch_lock.md`

## Material Summary

- concrete:
  - valid range: `10 to 55 deg`
  - peak `G_supp_ideal`: `37.51 dB @ 10 deg`
  - peak `G_supp_patch`: `24.60 dB @ 35 deg`
  - worst LP leakage on main rows: `-17.28 dB`
- glass:
  - valid range: `10 to 60 deg`
  - peak `G_supp_ideal`: `36.75 dB @ 10 deg`
  - peak `G_supp_patch`: `25.45 dB @ 40 deg`
  - worst LP leakage on main rows: `-16.41 dB`
- wood:
  - valid range: `10 to 45 deg`
  - peak `G_supp_ideal`: `26.59 dB @ 10 deg`
  - peak `G_supp_patch`: `23.64 dB @ 30 deg`
  - worst LP leakage on main rows: `-26.48 dB`
