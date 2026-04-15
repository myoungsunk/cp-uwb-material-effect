# Stage 4 Summary

Execution date: `2026-04-14`

This stage was executed in the isolated workspace:

- `analysis_stages/stage4_suppression_dual_20260414`

## Outputs

- Full audit table: `analysis_stages\paper_code_review_bundle_20260414\code\stage4_dual_sharedcommon_check_20260415\suppression_gain_dual_full.csv`
- Main claim table: `analysis_stages\paper_code_review_bundle_20260414\code\stage4_dual_sharedcommon_check_20260415\suppression_gain_dual.csv`
- Table I summary: `analysis_stages\paper_code_review_bundle_20260414\code\stage4_dual_sharedcommon_check_20260415\suppression_gain_table1.csv`
- Headline figure: `analysis_stages\paper_code_review_bundle_20260414\code\stage4_dual_sharedcommon_check_20260415\fig4_headline_suppression_dual.png`

## Row Counts

- Full audit rows: `39`
- Main-claim rows: `29`

## Branch Mapping Used For Final Gain

The headline suppression gain is computed from the smaller CP branch at each row.
This is an inference from the locked data because the symbol naming in the ideal and
patch stages is not numerically aligned.

- concrete: ideal small=ideal_same_mag, patch small=gamma_hat_c_cp_eff_mag, rows=10
- glass: ideal small=ideal_same_mag, patch small=gamma_hat_c_cp_eff_mag, rows=11
- wood: ideal small=ideal_same_mag, patch small=gamma_hat_c_cp_eff_mag, rows=8

## Material Summary

- concrete: range=10-55 deg, n=10, peak G_ideal=31.43 dB @ 10 deg, peak G_patch=24.60 dB @ 35 deg, peak Delta_G=25.21 dB @ 10 deg, worst LP leakage=-17.28 dB, ideal small=ideal_same_mag, patch small=gamma_hat_c_cp_eff_mag
- glass: range=10-60 deg, n=11, peak G_ideal=33.50 dB @ 10 deg, peak G_patch=13.95 dB @ 25 deg, peak Delta_G=28.83 dB @ 10 deg, worst LP leakage=-16.41 dB, ideal small=ideal_same_mag, patch small=gamma_hat_c_cp_eff_mag
- wood: range=10-45 deg, n=8, peak G_ideal=24.98 dB @ 10 deg, peak G_patch=19.66 dB @ 35 deg, peak Delta_G=19.75 dB @ 10 deg, worst LP leakage=-26.48 dB, ideal small=ideal_same_mag, patch small=gamma_hat_c_cp_eff_mag

## Notes

- Audit columns using the raw label-based branches are also included in the CSV.
- `G_supp_ideal_db` and `G_supp_patch_db` are the small-branch residual metrics used for the headline figure.
- LP leakage diagnostics are attached row-wise for methods/supporting checks.