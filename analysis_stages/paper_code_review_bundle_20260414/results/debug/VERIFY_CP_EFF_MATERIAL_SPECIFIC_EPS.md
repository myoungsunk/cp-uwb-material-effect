# Verify CP Eff Material-Specific Eps Replay

Execution date: `2026-04-16`

## Scope

- No production Stage 4 headline value is modified.
- Inputs are the existing `verify_cp_eps_material_drift` diagnostics plus the locked `stage4f_raw_primary_full.csv` table.
- Two material-specific replay targets are evaluated:
  - `lp_target_pointwise`: use `eps_obs_lp(theta,f,material)` directly at each frequency point.
  - `ideal_center_const`: use `eps_obs_ideal(theta,6.5 GHz,material)` as an angle-specific constant across the band.
- Pass criterion from the current plan: violation count `< 5/23`.

## Main Findings

- Locked Stage 4 baseline remains `16/23` violations for CP eff.
- The refreshed freq-resolved replay of the current shared eff path gives `8/23` band violations.
- `lp_target_pointwise` does not solve CP eff: `15/23` band violations.
- `ideal_center_const` does solve most of it: `3/23` band violations and `2/23` at `6.5 GHz`.
- The `< 5/23` pass criterion is met for the ideal-target replay: `True`.

## Interpretation

- The LP-target replay is a useful negative control: by construction it reproduces the LP bridge residual and therefore inherits the LP below-ideal pattern rather than fixing CP eff.
- The ideal-target replay reduces the violation count to a small concrete-only residue in the band summary, which is strong evidence that the shared `eps_eff` model is the dominant CP eff failure mode.
- This replay does not touch CP raw, so the main open issue is specifically the correction model, not the raw CP estimator path.
- There is one bookkeeping caveat: the current refreshed CP band export no longer matches the locked `stage4f` shared-eff snapshot for glass and wood. The replay report keeps both baselines explicit instead of hiding that mismatch.

## Remaining Band Violators

- concrete 30 deg: Delta_ideal_minus_eff_ideal_center_band_db `-0.229 dB`
- concrete 40 deg: Delta_ideal_minus_eff_ideal_center_band_db `-0.158 dB`
- concrete 50 deg: Delta_ideal_minus_eff_ideal_center_band_db `-0.137 dB`

## Remaining 6.5 GHz Violators

- glass 55 deg: Delta_ideal_minus_eff_ideal_center_6p5_db `-0.015 dB`
- wood 20 deg: Delta_ideal_minus_eff_ideal_center_6p5_db `-0.003 dB`

## Stage4f Baseline Mismatch Note

- Largest difference between locked `stage4f` shared-eff magnitude and the refreshed shared-eff replay: `glass 50 deg`, band magnitude difference `0.191417`.
- Raw CP band magnitude remains aligned; the mismatch is specific to the shared-eff path in the locked snapshot.

## Outputs

- Angle summary CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_cp_eff_material_specific_eps.csv`
- Freq detail CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_cp_eff_material_specific_eps_freq.csv`
- Summary CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_cp_eff_material_specific_eps_summary.csv`
