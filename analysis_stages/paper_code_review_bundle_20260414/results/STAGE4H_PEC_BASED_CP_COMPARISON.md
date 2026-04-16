# Stage 4h - PEC-Based CP Correction Comparison

Execution date: `2026-04-14`

## Purpose

Test the proposed PEC-based reflective leakage subtraction against the locked `ideal`, `LP-derived`, and `CP raw` curves.

## Tested PEC Corrections

- simple PEC approximation:
  - `Gamma_C_new = Gamma_C_raw - Gamma_C_raw_PEC * Gamma_d`
- ratio PEC correction:
  - `lambda_PEC = Gamma_C_raw_PEC / Gamma_d_PEC`
  - `Gamma_C_new = Gamma_C_raw - lambda_PEC * Gamma_d`

The ratio form is the measurement-consistent version when `Gamma_d_PEC` is not exactly unity.

## Main Result

- `ideal < cp_pec_simple` rows: `12 / 23`
- `ideal < cp_pec_ratio` rows: `12 / 23`

This means both PEC-based CP corrections overshoot the material-limited ideal reference in most same-angle rows, so they cannot be used as a safe upper-bound-consistent headline correction.

## Mean Gain By Material

### concrete

- ideal mean: `16.07 dB`
- CP raw mean: `8.49 dB`
- LP-derived mean: `15.77 dB`
- CP PEC simple mean: `17.33 dB`
- CP PEC ratio mean: `17.82 dB`
- `ideal < cp_pec_simple` rows: `8`
- `ideal < cp_pec_ratio` rows: `7`

### glass

- ideal mean: `16.23 dB`
- CP raw mean: `9.53 dB`
- LP-derived mean: `16.18 dB`
- CP PEC simple mean: `12.96 dB`
- CP PEC ratio mean: `13.29 dB`
- `ideal < cp_pec_simple` rows: `2`
- `ideal < cp_pec_ratio` rows: `3`

### wood

- ideal mean: `14.01 dB`
- CP raw mean: `8.01 dB`
- LP-derived mean: `15.16 dB`
- CP PEC simple mean: `11.52 dB`
- CP PEC ratio mean: `11.63 dB`
- `ideal < cp_pec_simple` rows: `2`
- `ideal < cp_pec_ratio` rows: `2`

## Interpretation

- The proposed PEC subtraction removes too much of the CP residual branch.
- Relative to `CP raw`, it raises the apparent CP suppression by about `8-10 dB`, but it overshoots even beyond `ideal` in most rows.
- `LP-derived` remains the only practical estimate that stays physically close to `ideal` without the same widespread oversubtraction.

## Outputs

- full table: `D:\OneDrive - postech.ac.kr\명선\2026\3.9 CP odd-bounce\4.CP_material_effect\analysis_stages\paper_code_review_bundle_20260414\results\pec_based_cp_comparison_full.csv`
- summary: `D:\OneDrive - postech.ac.kr\명선\2026\3.9 CP odd-bounce\4.CP_material_effect\analysis_stages\paper_code_review_bundle_20260414\results\pec_based_cp_comparison_summary.csv`
- long curve CSV: `D:\OneDrive - postech.ac.kr\명선\2026\3.9 CP odd-bounce\4.CP_material_effect\analysis_stages\paper_code_review_bundle_20260414\results\pec_based_cp_comparison_long.csv`