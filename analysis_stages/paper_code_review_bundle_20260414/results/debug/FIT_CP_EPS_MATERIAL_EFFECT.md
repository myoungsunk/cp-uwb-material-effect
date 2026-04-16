# Fit CP Eps Material Effect

Execution date: `2026-04-16`

## Scope

- Fit simple material-effect models on top of the shared `eps_eff` CP correction.
- Fit target is the existing `eps_obs_ideal` center-frequency replay at `6.5 GHz`.
- Evaluation uses the locked Stage 4 ideal-anchor gain baseline on the current main-range `23` rows.
- The A1 ideal-center replay is included as a high-flexibility reference row, not as a low-dimensional fit.

## Model Family

- `shared_current`: no material effect, current shared model
- `material_scale_centerfit`: `eps_fit = a_m * eps_shared`
- `material_offset_centerfit`: `eps_fit = eps_shared + b_m`
- `material_affine_centerfit`: `eps_fit = a_m * eps_shared + b_m`
- `a1_ideal_center_const_reference`: per-(material, theta) ideal-center replay from A1

## Main Result

- Shared current baseline: `8/23` band violations
- Best low-dimensional material-effect fit in this sweep: `material_scale_centerfit`, `4/23` band violations
- The same scale model gives `8/23` violations at `6.5 GHz`
- Offset model: `6/23` band violations
- Affine model: `5/23` band violations
- A1 high-flexibility reference remains better: `3/23` band violations

## Interpretation

- A material effect does help. Even a single complex scale per material reduces the band violation count substantially relative to the shared baseline.
- But a material-only low-dimensional model is not enough to fully match the A1 replay quality.
- In the current data, `material_scale_centerfit` is the best simple model among the tested families.
- This suggests that the CP eff failure is not just a single shared coefficient problem; there is real material dependence, but one complex degree of freedom per material still leaves residual angle-dependent mismatch.

## Best Material-Scale Coefficients

- concrete: `a = 0.538664 + 0.236739j`, `|a| = 0.588391`, `phase = 23.73 deg`
- glass: `a = 0.541866 + 0.243021j`, `|a| = 0.593867`, `phase = 24.16 deg`
- wood: `a = 0.140153 + 0.086440j`, `|a| = 0.164666`, `phase = 31.66 deg`

## Outputs

- Angle detail CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\fit_cp_eps_material_effect_detail.csv`
- Summary CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\fit_cp_eps_material_effect_summary.csv`
- Coefficients CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\fit_cp_eps_material_effect_coefficients.csv`
