# Verify Cross-Dipole CP vs Ideal TE/TM

Execution date: `2026-04-16`

## Scope

- External input is the cross-dipole CP ideal-source export with one LoS-only file plus metal/material reflection files.
- Stage 1 ideal TE/TM truth is first synthesized into CP truth using:
  - `Gamma_same = 0.5 * (R_TE + R_TM)`
  - `Gamma_flip = 0.5 * (R_TE - R_TM)`
- Because the external CP replay is built as `material / metal` channel ratios, the authoritative ideal target is also PEC-normalized:
  - `gamma_rr_ideal = Gamma_same(material) / Gamma_same(PEC)`
  - `gamma_cross_ideal = Gamma_flip(material) / Gamma_flip(PEC)`
- Measurement-side definitions:
  - `gamma_rr = h_tilde_RR(material) / h_tilde_RR(metal)`
  - `gamma_cross = 0.5 * [h_tilde_LR(material) / h_tilde_LR(metal) + h_tilde_RL(material) / h_tilde_RL(metal)]`
- Only the three available multifreq truth points are compared: `6.24`, `6.50`, `6.74 GHz`.

## Main Findings

- `gamma_cross` tracks the PEC-normalized ideal CP target reasonably well in the current main range: mean abs magnitude error `1.017 dB`, mean phase error `10.98 deg`, joint pass `20/69`.
- At the center point `6.50 GHz`, `gamma_cross` stays similar: mean abs magnitude error `1.009 dB`, mean phase error `10.19 deg`.
- `gamma_rr` does not reproduce the PEC-normalized same-hand ideal target: main-range mean abs magnitude error `25.851 dB`, mean phase error `82.55 deg`, joint pass `0/69`.
- The same-hand PEC reference is intrinsically tiny in this dataset: `|Gamma_same(PEC)|` ranges from `0.000420` to `0.055118` across the compared rows. That makes the RR normalization path ill-conditioned.
- The cross-hand average is numerically safe because `LR` and `RL` remain symmetric: max relative mismatch `1.710e-11`. Same-hand `LL/RR` is much less stable once the reference branch approaches zero: max relative mismatch `8.342e-01`.

## Interpretation

- With the current cross-dipole ideal-source replay, the cross-hand CP branch behaves like a valid proxy for the TE/TM-synthesized CP dominant branch.
- The same-hand RR branch is not a stable truth-comparable observable under the same PEC-normalized construction.
- So this dataset supports `gamma_cross` as the cleaner comparison axis, while `gamma_rr` remains dominated by the small-reference same-hand residual problem.

## Best Cross-Hand Rows

- glass 20 deg: mean cross mag error `0.122 dB`
- glass 30 deg: mean cross mag error `0.267 dB`
- concrete 20 deg: mean cross mag error `0.423 dB`
- wood 20 deg: mean cross mag error `0.531 dB`
- concrete 25 deg: mean cross mag error `0.535 dB`

## Worst RR Rows

- wood 25 deg: mean RR mag error `-39.202 dB`
- wood 35 deg: mean RR mag error `-36.807 dB`
- glass 35 deg: mean RR mag error `-33.632 dB`
- concrete 35 deg: mean RR mag error `-32.101 dB`
- concrete 50 deg: mean RR mag error `-32.084 dB`

## Outputs

- Full CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_cross_dipole_cp_vs_ideal_te_tm_full.csv`
- Summary CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_cross_dipole_cp_vs_ideal_te_tm_summary.csv`
- 6.50 GHz magnitude plot: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_cross_dipole_cp_vs_ideal_te_tm_6p5ghz_mag.png`
- 6.50 GHz phase plot: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_cross_dipole_cp_vs_ideal_te_tm_6p5ghz_phase.png`
