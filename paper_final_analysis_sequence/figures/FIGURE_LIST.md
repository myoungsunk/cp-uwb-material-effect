# Figure List

Current paper-facing figure inventory.

## Main Figures

1. `fig1_linear_truth_vs_fresnel.png`
   - Stage 1 ideal TE/TM truth
   - `|R_TE|`, `|R_TM|` vs incident angle
   - HFSS truth with Fresnel overlay

2. `fig2_ideal_cp_oblique.png`
   - Stage 2 ideal CP upper bound
   - oblique-angle ideal CP branch view
   - same/flip-safe truth source

3. `fig3_practical_branch_overlay.png`
   - Stage 3 practical comparison
   - ideal residual, LP-derived residual, CP raw residual overlay

4. `fig4_headline_suppression.png`
   - Stage 4 headline figure
   - raw-primary suppression gain
   - ideal / LP-derived / CP raw comparison

5. `fig5_pec_final_setup_rt_vs_angle.png`
   - PEC final-setup R/T
   - incident angle on x-axis

6. `fig6_material_final_setup_rt_vs_angle.png`
   - material final-setup R/T
   - incident angle on x-axis

7. `fig7_ideal_cp_branch_separation.png`
   - ideal CP branch-separation metric
   - `20 log10(|Gamma_flip| / |Gamma_same|)` vs incident angle
   - solid line: main claim range, dashed line: caution/excluded

8. `fig8_stage4_three_component_vs_angle.png`
   - Stage 4 residual decomposition audit
   - anglewise comparison of `raw`, `correction term`, and `corrected`
   - material-wise subplot view

9. `fig9_stage4_dominant_residual_ratio_vs_angle.png`
   - Stage 4 dominant/residual ratio audit
   - ideal / raw / corrected ratio vs incident angle
   - material-wise subplot view

10. `fig10_stage4_ideal_raw_eff_residual_vs_angle.png`
   - Stage 4 residual-branch comparison
   - ideal residual, raw residual, corrected residual vs incident angle
   - material-wise subplot view

11. `fig11_stage4_ideal_cross_vs_angle.png`
   - Stage 4 dominant-branch comparison
   - ideal dominant vs patch cross-dominant vs incident angle
   - material-wise subplot view

12. `fig12_stage4_ideal_lp_raw_residual_vs_angle.png`
   - Stage 4 residual comparison
   - ideal residual, LP residual, and CP raw residual vs incident angle
   - material-wise subplot view

13. `fig13_stage4_ideal_lp_dominant_vs_angle.png`
   - Stage 4 dominant comparison
   - ideal dominant vs LP dominant vs incident angle
   - material-wise subplot view

14. `fig14_stage4_ideal_lp_dominant_residual_ratio_vs_angle.png`
   - Stage 4 dominant/residual ratio comparison
   - ideal ratio vs LP ratio
   - material-wise subplot view

15. `fig15_stage4_ideal_lp_cp_dominant_residual_ratio_vs_angle.png`
   - Stage 4 dominant/residual ratio comparison
   - ideal ratio vs LP ratio vs CP raw ratio
   - material-wise subplot view

16. `fig16_stage4_suppression_gain_ideal_lp_cp_raw_eff_vs_angle.png`
   - Stage 4 suppression-gain comparison on the reporting range
   - ideal vs LP raw vs CP raw vs CP corrected
   - material-wise subplot view

17. `fig17_stage4_ratio_ideal_lp_cp_raw_eff_vs_angle.png`
   - Stage 4 dominant/residual ratio comparison on the reporting range
   - ideal vs LP raw vs CP raw vs CP corrected
   - material-wise subplot view

## Related Files

- `csv/fig1_linear_truth_vs_fresnel.csv`
- `csv/fig2_ideal_cp_oblique.csv`
- `csv/fig3_practical_branch_overlay.csv`
- `csv/fig4_headline_suppression.csv`
- `csv/fig5_pec_final_setup_rt_vs_angle.csv`
- `csv/fig6_material_final_setup_rt_vs_angle.csv`
- `csv/fig7_ideal_cp_branch_separation.csv`
- `csv/fig8_stage4_three_component_vs_angle.csv`
- `csv/fig9_stage4_dominant_residual_ratio_vs_angle.csv`
- `csv/fig10_stage4_ideal_raw_eff_residual_vs_angle.csv`
- `csv/fig11_stage4_ideal_cross_vs_angle.csv`
- `csv/fig12_stage4_ideal_lp_raw_residual_vs_angle.csv`
- `csv/fig13_stage4_ideal_lp_dominant_vs_angle.csv`
- `csv/fig14_stage4_ideal_lp_dominant_residual_ratio_vs_angle.csv`
- `csv/fig15_stage4_ideal_lp_cp_dominant_residual_ratio_vs_angle.csv`
- `csv/fig16_stage4_suppression_gain_ideal_lp_cp_raw_eff_vs_angle.csv`
- `csv/fig17_stage4_ratio_ideal_lp_cp_raw_eff_vs_angle.csv`
- `csv/stage4_lp_cp_metric_summary.csv`
- `csv/table1_maintext_means.csv`

## Current Rule

- Figure 1: Stage 1 truth anchor
- Figure 2: Stage 2 ideal CP same/flip-safe truth
- Figure 3: Stage 3 raw-primary practical overlay
- Figure 4: Stage 4 raw-primary headline
- Figure 5: PEC final-setup R/T
- Figure 6: material final-setup R/T
- Figure 7: ideal CP branch separation
- Figure 8: Stage 4 raw/correction/corrected anglewise comparison
- Figure 9: Stage 4 ideal/raw/corrected dominant-to-residual ratio
- Figure 10: Stage 4 ideal/raw/corrected residual magnitude comparison
- Figure 11: Stage 4 ideal-vs-cross dominant magnitude comparison
- Figure 12: Stage 4 ideal-vs-LP-vs-CP-raw residual comparison
- Figure 13: Stage 4 ideal-vs-LP dominant comparison
- Figure 14: Stage 4 ideal-vs-LP dominant-to-residual ratio comparison
- Figure 15: Stage 4 ideal-vs-LP-vs-CP dominant-to-residual ratio comparison
- Figure 16: Stage 4 ideal-vs-LP-vs-CP(raw/corrected) suppression gain comparison
- Figure 17: Stage 4 ideal-vs-LP-vs-CP(raw/corrected) dominant-to-residual ratio comparison
- `eff` and PEC-based correction remain supplement/audit-only, not main figures
