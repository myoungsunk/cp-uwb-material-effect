# Stage 4c Same-Angle Gap Audit

Execution date: `2026-04-14`

This stage was executed in the isolated workspace:

- `analysis_stages/stage4c_same_angle_gap_audit_20260414`

## Core Finding

The same-angle gap stays physically consistent only for the raw patch residual branch.

- corrected residual (`gamma_hat_c_cp_eff`) negative-gap rows: `8/23`
- raw residual (`gamma_hat_c_cp_raw`) negative-gap rows: `0/23`

So the current effective correction layer breaks the intended
`ideal >= patch` same-angle interpretation over most of the oblique main range.

## Summary By Material

- concrete: n=8, eff negative=5/8, raw negative=0/8, mean Delta_eff=-2.33 dB, mean Delta_raw=7.64 dB
- glass: n=9, eff negative=1/9, raw negative=0/9, mean Delta_eff=5.40 dB, mean Delta_raw=6.78 dB
- wood: n=6, eff negative=2/6, raw negative=0/6, mean Delta_eff=2.56 dB, mean Delta_raw=6.04 dB

## Interpretation

- LP-anchor aliasing solved the branch-name mismatch.
- It did not prove that the corrected patch residual branch is a strict practical lower-bound to the ideal residual branch.
- The sign flip appears only after applying the effective correction layer.
- That makes over-correction or quantity mismatch the next active issue, not branch aliasing.

## Negative-Gap Rows

- concrete 35 deg: ideal=0.071869, raw=0.166720, eff=0.027989, Delta_raw=7.31 dB, Delta_eff=-8.19 dB
- concrete 40 deg: ideal=0.089012, raw=0.194366, eff=0.033411, Delta_raw=6.78 dB, Delta_eff=-8.51 dB
- concrete 45 deg: ideal=0.139044, raw=0.204746, eff=0.054971, Delta_raw=3.36 dB, Delta_eff=-8.06 dB
- concrete 50 deg: ideal=0.167934, raw=0.232695, eff=0.083208, Delta_raw=2.83 dB, Delta_eff=-6.10 dB
- concrete 55 deg: ideal=0.175456, raw=0.250642, eff=0.120921, Delta_raw=3.10 dB, Delta_eff=-3.23 dB
- glass 55 deg: ideal=0.217662, raw=0.257833, eff=0.166746, Delta_raw=1.47 dB, Delta_eff=-2.31 dB
- wood 35 deg: ideal=0.067121, raw=0.106783, eff=0.030234, Delta_raw=4.03 dB, Delta_eff=-6.93 dB
- wood 45 deg: ideal=0.120057, raw=0.133950, eff=0.106405, Delta_raw=0.95 dB, Delta_eff=-1.05 dB

## Outputs

- Full audit: `analysis_stages\stage4c_same_angle_gap_audit_20260414\results_aliasfree_20260415\same_angle_gap_audit_full.csv`
- Summary table: `analysis_stages\stage4c_same_angle_gap_audit_20260414\results_aliasfree_20260415\same_angle_gap_audit_summary.csv`
