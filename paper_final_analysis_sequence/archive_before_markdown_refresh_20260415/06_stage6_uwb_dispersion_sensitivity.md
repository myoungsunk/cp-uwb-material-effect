# Stage 6. UWB Dispersion Sensitivity

## Current Status

- This stage is now executed in:
  - `analysis_stages/stage6_uwb_dispersion_sensitivity_20260414`
- Important scope note:
  - no frequency-dependent material law was identified in the current
    repository code
  - so the executed result is a `3-10 GHz` frequency robustness sweep under the
    locked analytic material model, not a full externally calibrated dispersive
    characterization

## Purpose

- Show that the single-tone `6.5 GHz` claim remains representative over the
  target UWB band.

## Inputs

- Stage 1 material definitions and slab thickness lock
- Fresnel comparison logic from:
  - `analysis_stages/ideal_te_tm_scattered_stage/code/sanity_check_fresnel.py`
- Locked angles:
  - `20 deg`
  - `30 deg`
  - `45 deg`

## Execution

1. Use analytic slab reflection only; no HFSS rerun is needed.
2. Sweep frequency from `3 GHz` to `10 GHz`.
3. Recompute ideal `R_TE`, `R_TM`, and derived `Gamma_C`.
4. Recompute `G_supp_ideal(f)` at the three locked angles.
5. Compare the band-averaged value against the `6.5 GHz` single-tone result.

## Outputs

- Executed outputs:
  - `analysis_stages/stage6_uwb_dispersion_sensitivity_20260414/results/uwb_dispersion_sensitivity_full.csv`
  - `analysis_stages/stage6_uwb_dispersion_sensitivity_20260414/results/uwb_dispersion_sensitivity_summary.csv`
  - `analysis_stages/stage6_uwb_dispersion_sensitivity_20260414/results/fig_stage6_uwb_dispersion_sensitivity.png`
  - `analysis_stages/stage6_uwb_dispersion_sensitivity_20260414/results/STAGE6_SUMMARY.md`

## Pass Conditions

- External reference check:
  - band-averaged `G_supp_ideal` stays within `+/- 1 dB` of the locked HFSS
    `6.5 GHz` value
- Internal robustness check:
  - band-averaged `G_supp_ideal` stays within `+/- 1 dB` of the analytic
    `6.5 GHz` value from the same material model

## Next Stage Link

- Stage 7 uses this result only as a supplement reference, not as a main text
  figure.

## Current Interpretation Lock

- Against the locked HFSS `6.5 GHz` reference, this stage is `PARTIAL / FAIL`
  because the comparison mixes band variation with a fixed model offset at
  `6.5 GHz`.
- Against the analytic `6.5 GHz` reference from the same material model, most
  rows pass and the band variation is generally small.
- Therefore this stage should be cited only as an internal robustness check
  under the current analytic model.
