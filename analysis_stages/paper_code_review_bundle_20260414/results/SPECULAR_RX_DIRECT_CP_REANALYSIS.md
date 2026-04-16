# Specular RX Direct CP Reanalysis

Execution date: `2026-04-14`

## Purpose

Recompute the direct-CP `ideal / cp-raw / cp cal` comparison from the new
specular RX files.

## Calibration Paths Tested

- `cp-raw`: `Gamma_r_raw = h_tilde_RR / h3_RR`
- `cp cal (M3)`: `Gamma_r_raw - (h3_LR / h3_RR) * Gamma_d`
- `cp cal (PEC ratio)`: `Gamma_r_raw - lambda_PEC * Gamma_d`, where
  `lambda_PEC = Gamma_r_raw_PEC / Gamma_d_PEC`

Here `Gamma_d` is the dominant direct-CP branch reconstructed from the
reciprocal geometric mean of `LR` and `RL`.

## Headline Oblique Result

- oblique row count: `23`
- `Gamma_d` phase-anchor flips applied: `0 / 39`
- `Gamma_d_PEC` phase-anchor flips applied: `0 / 39`
- negative-gap rows for `cp-raw`: `3 / 23`
- negative-gap rows for `cp cal (M3)`: `18 / 23`
- negative-gap rows for `cp cal (PEC ratio)`: `20 / 23`

So the phase-anchor guard is now in place, but for this specular RX dataset it
does not change any row. The new direct specular RX data improve the raw branch
slightly, while both calibrated branches still overshoot the ideal upper bound
too often to be used as a safe headline layer.

## Mean Suppression By Material (`20 deg` to valid max)

### concrete

- ideal mean: `16.07 dB`
- CP raw mean: `10.18 dB`
- CP cal (M3) mean: `19.42 dB`
- CP cal (PEC ratio) mean: `17.71 dB`
- raw negative rows: `0`
- cal M3 negative rows: `6`
- cal PEC-ratio negative rows: `7`
- raw minus prior Stage 4f mean: `+1.69 dB`

### glass

- ideal mean: `16.23 dB`
- CP raw mean: `10.51 dB`
- CP cal (M3) mean: `19.06 dB`
- CP cal (PEC ratio) mean: `17.81 dB`
- raw negative rows: `2`
- cal M3 negative rows: `6`
- cal PEC-ratio negative rows: `8`
- raw minus prior Stage 4f mean: `+0.99 dB`

### wood

- ideal mean: `14.01 dB`
- CP raw mean: `9.07 dB`
- CP cal (M3) mean: `20.03 dB`
- CP cal (PEC ratio) mean: `15.34 dB`
- raw negative rows: `1`
- cal M3 negative rows: `6`
- cal PEC-ratio negative rows: `5`
- raw minus prior Stage 4f mean: `+1.06 dB`

## Validated Full-Range Mean (`10 deg` to valid max)

- concrete: ideal `18.65 dB`, raw `10.06 dB`, cal(M3) `17.59 dB`, cal(PEC ratio) `20.97 dB`
- glass: ideal `18.57 dB`, raw `10.36 dB`, cal(M3) `17.50 dB`, cal(PEC ratio) `20.68 dB`
- wood: ideal `16.50 dB`, raw `9.04 dB`, cal(M3) `17.67 dB`, cal(PEC ratio) `18.87 dB`

## Raw Negative-Gap Rows In The Oblique Window

- glass / 55 deg: `G_ideal=9.95 dB`, `G_cp_raw=10.09 dB`
- glass / 60 deg: `G_ideal=8.12 dB`, `G_cp_raw=8.36 dB` (valid-range edge)
- wood / 45 deg: `G_ideal=8.28 dB`, `G_cp_raw=8.41 dB` (valid-range edge)

## Interpretation

- `cp-raw` is the only branch that stays close to the ideal ordering on most
  oblique rows.
- The complex-square-root phase ambiguity is now explicitly guarded by a
  single-branch phase anchor, but no flip was actually triggered on this
  dataset. So the current calibration failure is not caused by the sqrt branch
  cut here.
- `cp cal (M3)` still shows the same over-subtraction pattern seen earlier.
- `cp cal (PEC ratio)` uses the new matched-geometry PEC reference, but it
  still overshoots the ideal upper bound on most rows.
- So these new files strengthen the direct-CP reconstruction itself, but they
  do not close the calibration-model problem.

## Outputs

- full table: `analysis_stages\paper_code_review_bundle_20260414\results\specular_rx_direct_cp_full.csv`
- oblique table: `analysis_stages\paper_code_review_bundle_20260414\results\specular_rx_direct_cp_oblique.csv`
- summary: `analysis_stages\paper_code_review_bundle_20260414\results\specular_rx_direct_cp_summary.csv`
- negative rows: `analysis_stages\paper_code_review_bundle_20260414\results\specular_rx_direct_cp_negative_rows.csv`
- suppression figure: `analysis_stages\paper_code_review_bundle_20260414\results\fig_specular_rx_suppression_comparison.png`
- residual figure: `analysis_stages\paper_code_review_bundle_20260414\results\fig_specular_rx_residual_comparison.png`
