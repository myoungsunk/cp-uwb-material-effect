# Verify LP Cross-Pol Contamination

Execution date: `2026-04-16`

## Scope

- No new simulation is used.
- Source map is the existing Stage 3 LP frequency-resolved export.
- The audit reconstructs the LP internal cross-pol ratios from the exported Stage 3 ratios:
  - `|h_tilde_zy / h_tilde_zz| = |r_hat_zy_sys / r_hat_zz_sys|`
  - `|h_tilde_yz / h_tilde_yy| = |r_hat_yz_sys / r_hat_yy_sys|`
- Fresnel deviation overlap uses the existing metal-normalized replay output.
- Pass target from the review note: main-range cross-pol `<= -20 dB`.
- Legacy warning threshold: `-15 dB`.
- Elevated threshold used for discrimination: `-10 dB`.
- Large Fresnel deviation threshold: `>1.0 dB`.

## Main Findings

- `-15 dB` warning is non-discriminative in this dataset: `39/39` theta-rows exceed it.
- The stricter pass target also fails everywhere: `23/23` main-range rows exceed `-20 dB`.
- Main-range correlation between max cross-pol and metal-normalized Fresnel deviation is only moderate: Pearson `0.389`, Spearman `0.402`.
- Non-main-range correlation is strong: Pearson `0.802`, Spearman `0.806`.
- All large-deviation rows (`>1.0 dB`) are captured by the elevated `-10 dB` threshold: `2/2` in the non-main range.

## Interpretation

- Cross-pol contamination is real and becomes severe at high angle.
- However, `-15 dB` alone does not explain the current LP main-range contradiction because every theta-row already exceeds that threshold.
- The overlap with large Fresnel deviation becomes informative only once leakage rises to about `-10 dB` or worse, and that pattern is concentrated outside the current main range.
- This means cross-pol is a credible high-angle validity limiter, but not the primary cause of the main-range LP ordering failure after metal normalization.

## Worst Theta Rows

- wood 55 deg: max cross-pol `22.81 dB`, mean cross-pol `11.28 dB`, main-range=`False`, max Fresnel dev `4.475 dB`
- glass 65 deg: max cross-pol `6.57 dB`, mean cross-pol `-0.46 dB`, main-range=`False`, max Fresnel dev `0.280 dB`
- glass 70 deg: max cross-pol `6.31 dB`, mean cross-pol `4.39 dB`, main-range=`False`, max Fresnel dev `1.213 dB`
- concrete 65 deg: max cross-pol `6.24 dB`, mean cross-pol `4.94 dB`, main-range=`False`, max Fresnel dev `0.207 dB`
- wood 50 deg: max cross-pol `1.48 dB`, mean cross-pol `-2.41 dB`, main-range=`False`, max Fresnel dev `0.446 dB`
- wood 60 deg: max cross-pol `-0.14 dB`, mean cross-pol `-2.70 dB`, main-range=`False`, max Fresnel dev `0.882 dB`
- concrete 70 deg: max cross-pol `-0.73 dB`, mean cross-pol `-1.04 dB`, main-range=`False`, max Fresnel dev `0.835 dB`
- wood 45 deg: max cross-pol `-5.35 dB`, mean cross-pol `-10.44 dB`, main-range=`True`, max Fresnel dev `0.256 dB`
- concrete 60 deg: max cross-pol `-5.57 dB`, mean cross-pol `-6.63 dB`, main-range=`False`, max Fresnel dev `0.164 dB`
- wood 65 deg: max cross-pol `-6.03 dB`, mean cross-pol `-6.83 dB`, main-range=`False`, max Fresnel dev `0.148 dB`

## Large-Deviation Overlap

- glass 70 deg: max Fresnel dev `1.213 dB`, max cross-pol `6.31 dB`, `-10 dB` exceeded=`True`
- wood 55 deg: max Fresnel dev `4.475 dB`, max cross-pol `22.81 dB`, `-10 dB` exceeded=`True`

## Outputs

- Map CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_lp_crosspol_contamination_map.csv`
- Theta summary CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_lp_crosspol_contamination_theta_summary.csv`
- Overlap summary CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_lp_crosspol_contamination_overlap_summary.csv`
