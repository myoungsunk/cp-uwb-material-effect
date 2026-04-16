# Verify Estimator Roundtrip

Execution date: `2026-04-16`

This is a synthetic algebraic bridge test using the current single-frequency ideal truth at `6.5 GHz`.
It is not a new EM replay and does not relax the current truth-frequency limitation.

## Modes

- `lp_identity`: LP extractor with diagonal ideal `R_TM / R_TE` injected into the Stage 3 LP form.
- `cp_raw_identity`: CP raw path identity test with `h_tilde_RR / h3_RR = Gamma_flip`.
- `cp_eff_minimal`: CP minimal model with `h_tilde_RR = h3_RR * Gamma_flip + h3_LR * Gamma_same` so the corrected path should recover the ideal co-term.

- `single_reference`: uses one fixed reference stack at `theta=20.0 deg` to expose reference-reuse drift.

## Angle-Resolved Identity

- cp / cp_eff_minimal / Gamma_C_eff: 13/13 pass, max complex error=2.285e-16
- cp / cp_eff_minimal / Gamma_X: 13/13 pass, max complex error=3.879e-18
- cp / cp_raw_identity / Gamma_C_raw: 13/13 pass, max complex error=2.265e-16
- cp / cp_raw_identity / Gamma_X: 13/13 pass, max complex error=3.879e-18
- lp / lp_identity / Gamma_C: 0/13 pass, max complex error=8.872e-04
- lp / lp_identity / Gamma_X: 0/13 pass, max complex error=4.199e-02
- lp / lp_identity / R_TE: 13/13 pass, max complex error=2.220e-16
- lp / lp_identity / R_TM: 13/13 pass, max complex error=2.243e-16

## Fixed-Reference Replay

- cp / cp_eff_minimal / Gamma_C_eff: max complex error=1.822e+01, mean complex error=6.816e+00
- cp / cp_eff_minimal / Gamma_X: max complex error=9.820e-01, mean complex error=2.267e-01
- cp / cp_raw_identity / Gamma_C_raw: max complex error=1.842e+01, mean complex error=6.836e+00
- cp / cp_raw_identity / Gamma_X: max complex error=9.820e-01, mean complex error=2.267e-01
- lp / lp_identity / Gamma_C: max complex error=1.786e+01, mean complex error=6.605e+00
- lp / lp_identity / Gamma_X: max complex error=5.016e+00, mean complex error=1.226e+00
- lp / lp_identity / R_TE: max complex error=1.449e+01, mean complex error=5.920e+00
- lp / lp_identity / R_TM: max complex error=2.189e+01, mean complex error=7.437e+00

## Outputs

- Full rows: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_estimator_roundtrip_full.csv`
- Summary: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_estimator_roundtrip_summary.csv`
