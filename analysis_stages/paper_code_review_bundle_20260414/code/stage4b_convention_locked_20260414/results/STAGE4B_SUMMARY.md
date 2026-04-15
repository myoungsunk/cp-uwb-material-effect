# Stage 4b Summary

Execution date: `2026-04-14`

This stage was executed in the isolated workspace:

- `analysis_stages/stage4b_convention_locked_20260414`

The original Stage 4a workspace is preserved as:

- `analysis_stages/stage4_suppression_dual_20260414`

## Main-Claim Lock

- ideal residual branch: `Gamma_X`
- patch residual branch: `cp_residual_branch`
- branch lock source: `lp_anchor_branch_lock_20260414`
- headline reporting lower bound: `20 deg`

## Outputs

- Full audit table: `analysis_stages\stage4b_convention_locked_20260414\results\suppression_gain_stage4b_full.csv`
- Main claim table: `analysis_stages\stage4b_convention_locked_20260414\results\suppression_gain_stage4b.csv`
- Table I summary: `analysis_stages\stage4b_convention_locked_20260414\results\suppression_gain_stage4b_table1.csv`
- Headline figure: `analysis_stages\stage4b_convention_locked_20260414\results\fig4b_headline_suppression_locked.png`

## Row Counts

- Full audit rows: `39`
- Main-claim rows: `23`

## Material Summary

- concrete: range=20-55 deg, n=8, peak G_ideal=22.92 dB @ 20 deg, peak G_patch=24.60 dB @ 35 deg, peak Delta_G=8.42 dB @ 20 deg, worst LP leakage=-19.93 dB
- glass: range=20-60 deg, n=9, peak G_ideal=23.55 dB @ 30 deg, peak G_patch=25.45 dB @ 40 deg, peak Delta_G=8.09 dB @ 20 deg, worst LP leakage=-18.45 dB
- wood: range=20-45 deg, n=6, peak G_ideal=18.90 dB @ 20 deg, peak G_patch=23.64 dB @ 30 deg, peak Delta_G=4.35 dB @ 20 deg, worst LP leakage=-27.75 dB

## Notes

- Stage 4b removes the small-angle peak inflation by restricting the headline range to oblique incidence.
- The raw label-based branches remain available in the Stage 4a audit trail.
