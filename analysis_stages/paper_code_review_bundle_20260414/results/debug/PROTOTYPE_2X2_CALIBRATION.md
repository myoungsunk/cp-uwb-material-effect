# Prototype 2x2 Calibration

Execution date: `2026-04-16`

This is a single-frequency supervised prototype using existing ideal truth at `6.5 GHz`.
It estimates per-theta `J_rx` and `J_tx` with alternating least squares and evaluates `S_hat = J_rx^{-1} H J_tx^{-1}`.
This is not yet wired into the headline Stage 3/4 pipeline.

- LP frequency used: `6.500 GHz`
- CP frequency used: `6.500 GHz`

## Theta Summary

- lp theta=10.0 deg: fit_rms=3.213e-07, mean S_hat error=8.310e-03, max branch error=1.203e-02, cond(J_rx/J_tx)=1.57e+00/1.01e+00
- lp theta=15.0 deg: fit_rms=1.400e-06, mean S_hat error=1.988e-02, max branch error=3.143e-02, cond(J_rx/J_tx)=1.51e+00/1.03e+00
- lp theta=20.0 deg: fit_rms=1.815e-06, mean S_hat error=2.005e-02, max branch error=3.462e-02, cond(J_rx/J_tx)=1.50e+00/1.07e+00
- lp theta=25.0 deg: fit_rms=2.957e-06, mean S_hat error=2.011e-02, max branch error=2.717e-02, cond(J_rx/J_tx)=1.66e+00/1.36e+00
- lp theta=30.0 deg: fit_rms=3.685e-06, mean S_hat error=1.574e-02, max branch error=1.479e-02, cond(J_rx/J_tx)=1.66e+00/1.29e+00
- lp theta=35.0 deg: fit_rms=4.669e-06, mean S_hat error=1.481e-02, max branch error=1.723e-02, cond(J_rx/J_tx)=1.66e+00/1.42e+00
- lp theta=40.0 deg: fit_rms=7.373e-06, mean S_hat error=1.686e-02, max branch error=1.593e-02, cond(J_rx/J_tx)=1.55e+00/1.36e+00
- lp theta=45.0 deg: fit_rms=1.498e-05, mean S_hat error=2.651e-02, max branch error=4.545e-02, cond(J_rx/J_tx)=1.55e+00/1.37e+00
- lp theta=50.0 deg: fit_rms=1.662e-05, mean S_hat error=2.103e-02, max branch error=2.750e-02, cond(J_rx/J_tx)=1.45e+00/1.32e+00
- lp theta=55.0 deg: fit_rms=3.468e-05, mean S_hat error=3.432e-02, max branch error=4.700e-02, cond(J_rx/J_tx)=1.53e+00/1.37e+00
- lp theta=60.0 deg: fit_rms=4.450e-05, mean S_hat error=3.510e-02, max branch error=4.809e-02, cond(J_rx/J_tx)=1.38e+00/1.30e+00
- lp theta=65.0 deg: fit_rms=5.017e-05, mean S_hat error=3.851e-02, max branch error=4.980e-02, cond(J_rx/J_tx)=1.34e+00/1.29e+00
- lp theta=70.0 deg: fit_rms=1.019e-04, mean S_hat error=6.780e-02, max branch error=7.695e-02, cond(J_rx/J_tx)=1.38e+00/1.31e+00
- cp theta=10.0 deg: fit_rms=3.617e-07, mean S_hat error=9.207e-03, max branch error=5.554e-03, cond(J_rx/J_tx)=1.48e+00/1.01e+00
- cp theta=15.0 deg: fit_rms=1.885e-06, mean S_hat error=2.503e-02, max branch error=2.450e-02, cond(J_rx/J_tx)=1.55e+00/1.04e+00
- cp theta=20.0 deg: fit_rms=2.607e-06, mean S_hat error=3.030e-02, max branch error=1.898e-02, cond(J_rx/J_tx)=1.54e+00/1.12e+00
- cp theta=25.0 deg: fit_rms=5.282e-06, mean S_hat error=3.394e-02, max branch error=2.012e-02, cond(J_rx/J_tx)=1.58e+00/1.25e+00
- cp theta=30.0 deg: fit_rms=6.455e-06, mean S_hat error=2.640e-02, max branch error=1.604e-02, cond(J_rx/J_tx)=1.46e+00/1.36e+00
- cp theta=35.0 deg: fit_rms=4.933e-06, mean S_hat error=1.755e-02, max branch error=1.703e-02, cond(J_rx/J_tx)=1.51e+00/1.62e+00
- cp theta=40.0 deg: fit_rms=7.589e-06, mean S_hat error=1.613e-02, max branch error=1.344e-02, cond(J_rx/J_tx)=1.40e+00/1.57e+00
- cp theta=45.0 deg: fit_rms=1.564e-05, mean S_hat error=2.722e-02, max branch error=2.589e-02, cond(J_rx/J_tx)=1.49e+00/1.64e+00
- cp theta=50.0 deg: fit_rms=1.732e-05, mean S_hat error=2.120e-02, max branch error=2.126e-02, cond(J_rx/J_tx)=1.44e+00/1.54e+00
- cp theta=55.0 deg: fit_rms=3.593e-05, mean S_hat error=3.548e-02, max branch error=3.517e-02, cond(J_rx/J_tx)=1.39e+00/1.58e+00
- cp theta=60.0 deg: fit_rms=4.608e-05, mean S_hat error=3.419e-02, max branch error=4.286e-02, cond(J_rx/J_tx)=1.42e+00/1.49e+00
- cp theta=65.0 deg: fit_rms=5.700e-05, mean S_hat error=3.959e-02, max branch error=2.809e-02, cond(J_rx/J_tx)=1.41e+00/1.44e+00
- cp theta=70.0 deg: fit_rms=1.095e-04, mean S_hat error=6.505e-02, max branch error=5.609e-02, cond(J_rx/J_tx)=1.31e+00/1.44e+00

## Outputs

- Fitted matrices: `analysis_stages\paper_code_review_bundle_20260414\results\debug\prototype_2x2_calibration_matrices.csv`
- Sample reconstruction table: `analysis_stages\paper_code_review_bundle_20260414\results\debug\prototype_2x2_calibration_sample_reconstruction.csv`
- Theta summary: `analysis_stages\paper_code_review_bundle_20260414\results\debug\prototype_2x2_calibration_theta_summary.csv`
