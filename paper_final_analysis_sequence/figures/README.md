# Figures

This folder contains the current paper-facing figure PNG exports and their
paired CSV files.

## Index

- full figure list:
  - `FIGURE_LIST.md`

## Files

- `fig1_linear_truth_vs_fresnel.png`
  - Stage 1 HFSS linear truth with Fresnel overlay
- `fig2_ideal_cp_oblique.png`
  - Stage 2 ideal CP oblique-angle view
- `fig3_practical_branch_overlay.png`
  - Stage 3 practical overlay using ideal, LP-derived, and CP raw residual
- `fig4_headline_suppression.png`
  - Stage 4 raw-primary headline suppression figure
- `fig5_pec_final_setup_rt_vs_angle.png`
  - PEC final-setup R/T vs angle
- `fig6_material_final_setup_rt_vs_angle.png`
  - material final-setup R/T vs angle
- `fig7_ideal_cp_branch_separation.png`
  - ideal CP branch-separation metric vs angle
- `fig8_stage4_three_component_vs_angle.png`
  - Stage 4 raw / correction / corrected anglewise comparison
- `fig9_stage4_dominant_residual_ratio_vs_angle.png`
  - Stage 4 dominant / residual ratio comparison vs angle
- `fig10_stage4_ideal_raw_eff_residual_vs_angle.png`
  - Stage 4 ideal / raw / corrected residual comparison vs angle
- `fig11_stage4_ideal_cross_vs_angle.png`
  - Stage 4 ideal dominant vs patch cross-dominant comparison vs angle
- `fig12_stage4_ideal_lp_raw_residual_vs_angle.png`
  - Stage 4 ideal / LP / CP raw residual comparison vs angle
- `fig13_stage4_ideal_lp_dominant_vs_angle.png`
  - Stage 4 ideal vs LP dominant comparison vs angle
- `fig14_stage4_ideal_lp_dominant_residual_ratio_vs_angle.png`
  - Stage 4 ideal vs LP dominant-to-residual ratio comparison vs angle
- `fig15_stage4_ideal_lp_cp_dominant_residual_ratio_vs_angle.png`
  - Stage 4 ideal vs LP vs CP dominant-to-residual ratio comparison vs angle
- `fig16_stage4_suppression_gain_ideal_lp_cp_raw_eff_vs_angle.png`
  - Stage 4 ideal vs LP vs CP raw/corrected suppression-gain comparison vs angle
- `fig17_stage4_ratio_ideal_lp_cp_raw_eff_vs_angle.png`
  - Stage 4 ideal vs LP vs CP raw/corrected dominant-to-residual ratio comparison vs angle

## Paired CSV

- figure-source CSV files are stored under `csv/`

## Export Note

- figure 1 to 4 were exported from the current Stage 7 script using the
  same/flip-safe Stage 2 truth, the raw-primary Stage 3 alias lock, and the
  raw-primary Stage 4 headline table
- figure 5 and 6 are final-setup R/T exports
- figure 7 is the additional ideal-source CP branch-separation export
- figure 8 is the Stage 4 decomposition audit export for `raw`, correction, and
  corrected residual magnitudes
- figure 9 to 11 are additional Stage 4 branch-comparison exports requested for
  material-wise anglewise interpretation
- figure 12 to 13 are additional LP-vs-ideal / LP-vs-raw material-wise
  anglewise exports
- figure 14 is the LP dominant-to-residual ratio export against the ideal ratio
- figure 15 combines the ideal, LP, and CP raw dominant-to-residual ratios in one material-wise view
- figure 16 to 17 extend the Stage 4 reporting-range comparison to ideal / LP raw / CP raw / CP corrected metrics
