# Stage 4g Eff Mechanism Audit

Execution date: `2026-04-14`

This stage was executed in the isolated workspace:

- `analysis_stages/stage4g_eff_mechanism_audit_20260414`

## Core Findings

The Stage 4 `eff` failure is now separated into two mechanisms:

1. same-direction over-subtraction:
   freq points with `rho >= 1` and `|Delta_phi| <= 15 deg`: `41.5%`
   angle rows with overcorrection on at least `50%` of the band: `10/23`

2. shared-`eps_eff` model mismatch:
   same `(theta,f)` current `eps_eff` material spread mean max-pairwise diff: `0.0000`
   same `(theta,f)` back-solved `eps_obs` from LP bridge mean max-pairwise diff: `0.0339`

So the correction worsens because the subtraction term often reaches raw-residual scale with near-zero phase gap,
and the `eps` required to hit the LP-derived residual target is materially different from the single shared current `eps_eff`.

## Material Summary

- concrete: eps_eff -5.38 dB -> -9.24 dB (monotonic decrease=True), negative eff rows=5, band-majority overcorrection rows=3, mean |eps_obs_lp - eps_eff|=0.2045
- glass: eps_eff -5.38 dB -> -9.87 dB (monotonic decrease=True), negative eff rows=6, band-majority overcorrection rows=4, mean |eps_obs_lp - eps_eff|=0.2043
- wood: eps_eff -5.38 dB -> -8.14 dB (monotonic decrease=True), negative eff rows=5, band-majority overcorrection rows=3, mean |eps_obs_lp - eps_eff|=0.2301

## Interpretation

- `|eps_eff|` itself still decreases with angle; the failure is not high-angle growth of the current correction coefficient.
- The first practical proof of over-correction is the freq-resolved pattern `rho >= 1` together with `Delta_phi ~= 0 deg`.
- The second practical proof is the LP-target back-solved `eps_obs`: it varies with `(theta, f, material)` even though the current `eps_eff` is shared across materials at the same `(theta, f)`.
- Ideal-target back-solving is also exported at `6.5 GHz` only. Use it as a diagnostic fit-style reference, not as calibration.

## Ideal 6.5 GHz Diagnostic

- center-frequency `eps_obs_ideal` mean |difference vs current eps_eff|: `0.2405`

## Outputs

- Angle summary: `analysis_stages\paper_code_review_bundle_20260414\results\eff_mechanism_audit_full.csv`
- Material summary: `analysis_stages\paper_code_review_bundle_20260414\results\eff_mechanism_summary.csv`
- Freq-resolved `rho / Delta_phi / eps_obs_lp`: `analysis_stages\paper_code_review_bundle_20260414\results\eff_mechanism_audit_freq_resolved.csv`
- LP-target material spread by `(theta, f)`: `analysis_stages\paper_code_review_bundle_20260414\results\eps_obs_lp_material_spread_freq.csv`
- LP-target material spread by `theta`: `analysis_stages\paper_code_review_bundle_20260414\results\eps_obs_lp_material_spread_theta_summary.csv`
- Ideal-target center-frequency diagnostic: `analysis_stages\paper_code_review_bundle_20260414\results\eps_obs_ideal_center_6p5ghz.csv`
- Ideal-target center-frequency summary: `analysis_stages\paper_code_review_bundle_20260414\results\eps_obs_ideal_center_summary.csv`
