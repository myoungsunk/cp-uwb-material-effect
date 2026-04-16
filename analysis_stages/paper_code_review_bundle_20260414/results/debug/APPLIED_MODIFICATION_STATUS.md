# Applied Stage 4 Residual Ordering Status

Execution date: `2026-04-16`

## Applied Scope

- `C1` and `C6` are now unified in one authoritative exporter.
- Stage 4e schema fields `method_family`, `normalization_scope`, and `directly_comparable_to_ideal` are reused in the long-form outputs.
- `stage4f_raw_primary_full.csv` is now a derived headline-safe projection of the same authoritative table.
- same-stage numerator gains for LP and CP are exported before ideal-anchor gap interpretation.
- ideal-anchor gap decomposition now separates numerator mismatch from residual mismatch.
- synthetic stage bridge verification is now implemented as a separate debug workflow.
- supervised `2x2` calibration is now implemented as a separate prototype workflow.
- `ideal TE/TM` truth is now available for `6.24 / 6.50 / 6.74 GHz` in a separate multi-frequency snapshot.
- the multi-frequency snapshot is mirrored into bundle-local inputs without replacing the original single-frequency bundle snapshot:
  - `analysis_stages/paper_code_review_bundle_20260414/data/stage_1_multifreq_20260416`
  - `analysis_stages/paper_code_review_bundle_20260414/data/stage_2_multifreq_20260416/sameflip_alias_20260416`

## Code Fixes

- `stage_4_build_specular_rx_direct_cp_reanalysis.py`
  - fixed the `build_argparser()` `repo_root` bug affecting `--stage4f-summary`
  - switched default specular input CSVs to repo-local staged assets
  - added `GLASS_SPECULAR_RX.csv` then `GLSASS_SPECULAR_RX.csv` fallback handling
- `stage_4_audit_eff_mechanism.py`
  - fixed `--stage4f-full` default to use the bundle `data/stage_4/stage4f_raw_primary_dual_20260414` snapshot

## Stage 3 Export Refresh

- Stage 3 LP/CP exports now include:
  - `B_lp_sys_mag`, `G_lp_sys_db`
  - `B_cp_proxy_mag`, `G_cp_raw_sys_db`, `G_cp_eff_sys_db`
  - `*_abs_of_mean`, `*_mean_of_abs` alongside legacy `*_mag`
- Refreshed Stage 3 outputs were mirrored back into:
  - `analysis_stages/paper_code_review_bundle_20260414/data/stage_3/lp`
  - `analysis_stages/paper_code_review_bundle_20260414/data/stage_3/cp`

## Multi-Frequency Ideal TE/TM

- Added HFSS-driven Stage 1 ideal truth inputs for:
  - `6.24 GHz`
  - `6.50 GHz`
  - `6.74 GHz`
- Source folders used:
  - `D:/codex/ansys_automation/downloads/CP_global_test_copy2_apr16_export/copy2_20260416_final_complete/freq_6.24GHz_kobs5`
  - `D:/codex/ansys_automation/downloads/CP_global_test_copy2_apr16_export/copy2_20260416_final_complete/freq_6.5GHz_kobs5`
  - `D:/codex/ansys_automation/downloads/CP_global_test_copy2_apr16_export/copy2_20260416_final_complete/freq_6.74GHz_kobs5`
- Ideal-stage intake now collapses exact duplicate normalized rows from overlapping HFSS retry exports.
- The regenerated multi-frequency manifest contains `60` rows after overlap pruning.
- The multi-frequency truth build writes `156` locked rows.
- Final Stage 1 geometry-lock QC keeps one fail row:
  - `PEC / TE / 6.24 GHz / 70 deg / pec_locked_reflection_target_error = 0.116676`
- That remaining fail is outside the current main-truth region because `TE 70 deg` is excluded from main-use claims.

## V2 Replay With Multi-Frequency Ideal Truth

- `verify_single_freq_grid.py` now runs against same-frequency ideal truth at all three replay points:
  - requested `5.0 GHz` -> actual `6.24 GHz`
  - requested `6.5 GHz` -> actual `6.50 GHz`
  - requested `8.0 GHz` -> actual `6.74 GHz`
- Current per-frequency ordering counts:
  - `6.24 GHz`: raw=`1`, eff=`9`, LP=`12`
  - `6.50 GHz`: raw=`0`, eff=`15`, LP=`15`
  - `6.74 GHz`: raw=`0`, eff=`12`, LP=`12`
- Current interpretation:
  - the pass criterion is not met at any replay point
  - `6.50 GHz` single-frequency replay does not collapse the violation count to zero
  - band averaging alone is therefore not sufficient to explain the Stage 4 violation pattern

## LP Metal-Anchor Prototype

- Added bundle-local debug replay:
  - `analysis_stages/paper_code_review_bundle_20260414/code/verify_lp_metal_normalized.py`
- Current outputs:
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_lp_metal_normalized_full.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_lp_metal_normalized_summary.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/VERIFY_LP_METAL_NORMALIZED.md`

Current result:

- Existing LP below-ideal count remains:
  - band export: `15/23`
  - `6.5 GHz`: `15/23`
- Metal-normalized LP below-ideal count drops to:
  - band export: `0/23`
  - `6.5 GHz`: `0/23`
- Main-range Fresnel agreement after metal normalization is tight:
  - concrete: max `|R_TE|` deviation `0.166 dB`, max `|R_TM|` deviation `0.239 dB`
  - glass: max `|R_TE|` deviation `0.275 dB`, max `|R_TM|` deviation `0.293 dB`
  - wood: max `|R_TE|` deviation `0.256 dB`, max `|R_TM|` deviation `0.380 dB`

Interpretation:

- A same-angle metal anchor is sufficient to remove the LP residual undershoot in the current main-range rows.
- This strongly supports reference normalization mismatch as the dominant LP distortion source.
- This is still an empirical correction prototype, not yet the formal Stage 3/4 production path.
- High-angle rows remain caution-only because cross-pol contamination rises outside the current main range.

## Cross-Pol Contamination Audit

- Added bundle-local debug replay:
  - `analysis_stages/paper_code_review_bundle_20260414/code/verify_lp_crosspol_contamination.py`
- Current outputs:
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_lp_crosspol_contamination_map.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_lp_crosspol_contamination_theta_summary.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_lp_crosspol_contamination_overlap_summary.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/VERIFY_LP_CROSSPOL_CONTAMINATION.md`

Current result:

- `-15 dB` warning is non-discriminative in the current LP dataset:
  - all theta rows above threshold: `39/39`
  - main-range rows above threshold: `23/23`
- The stricter pass target also fails everywhere:
  - main-range rows above `-20 dB`: `23/23`
- Correlation with metal-normalized Fresnel deviation splits by scope:
  - main range: Pearson `0.389`, Spearman `0.402`
  - non-main range: Pearson `0.802`, Spearman `0.806`
- Large Fresnel-deviation rows (`>1 dB`) are concentrated outside the current main range:
  - total large-deviation rows: `2`
  - captured by `-10 dB` elevated leakage threshold: `2/2`
- Worst current theta rows are all outside the current main range:
  - wood `55 deg`: max cross-pol `22.811 dB`, max Fresnel dev `4.475 dB`
  - glass `70 deg`: max cross-pol `6.310 dB`, max Fresnel dev `1.213 dB`
  - glass `65 deg`: max cross-pol `6.570 dB`, max Fresnel dev `0.280 dB`
  - concrete `65 deg`: max cross-pol `6.235 dB`, max Fresnel dev `0.207 dB`

Interpretation:

- Cross-pol contamination is real and becomes severe at high angle.
- However, it does not explain the current main-range LP contradiction by itself, because the legacy `-15 dB` threshold fires everywhere and the main-range overlap with large Fresnel deviation is weak.
- Cross-pol is therefore best treated as a high-angle validity limiter, not the dominant driver of the remaining main-range LP mismatch after same-angle metal normalization.

## Stage 1 PEC Truth Accuracy Audit

- Added bundle-local debug replay:
  - `analysis_stages/paper_code_review_bundle_20260414/code/verify_stage1_pec_truth_accuracy.py`
- Current outputs:
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_stage1_pec_truth_accuracy_full.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_stage1_pec_truth_accuracy_summary.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_stage1_pec_truth_accuracy_qc_subset.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_stage1_pec_truth_accuracy.png`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/VERIFY_STAGE1_PEC_TRUTH_ACCURACY.md`

Current result:

- The current single-frequency bundle snapshot at `6.50 GHz` passes the requested main-range PEC magnitude criterion `||R|-1| < 0.05`:
  - TE main rows above threshold: `0/11`, max deviation `0.046291` at `55 deg`
  - TM main rows above threshold: `0/13`, max deviation `0.029392` at `15 deg`
- The multi-frequency snapshot shows that only the TE branch begins to tighten at high oblique angle:
  - `6.24 GHz`: TE main max `0.075520` (`1/11` above threshold), TM main max `0.030115` (`0/13`)
  - `6.50 GHz`: TE main max `0.046292` (`0/11` above threshold), TM main max `0.029339` (`0/13`)
  - `6.74 GHz`: TE main max `0.067503` (`1/11` above threshold), TM main max `0.027283` (`0/13`)
- Only one explicit QC fail exists in the multi-frequency PEC set:
  - `6.24 GHz / TE / 70 deg / pec_locked_reflection_target_error = 0.116676`

Interpretation:

- For the current `6.50 GHz` main-use bundle snapshot, Stage 1 PEC truth is clean enough under the requested `0.05` linear threshold.
- Across frequency, TE at high oblique angle (`60 deg` and beyond) is the first place where Stage 1 truth accuracy degrades, while TM remains comfortably inside the threshold.
- Stage 1 PEC uncertainty is therefore a high-angle TE caution term, not the primary explanation for the current `6.50 GHz` LP main-range contradiction.

## CP Eps-Eff Material Drift Replay

- Replayed current `eps_eff` mismatch audit with refreshed bundle exports:
  - `analysis_stages/paper_code_review_bundle_20260414/code/stage_4_audit_eff_mechanism.py`
- Current replay outputs:
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_cp_eps_material_drift/eff_mechanism_audit_full.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_cp_eps_material_drift/eff_mechanism_summary.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_cp_eps_material_drift/eff_mechanism_audit_freq_resolved.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_cp_eps_material_drift/eps_obs_lp_material_spread_freq.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_cp_eps_material_drift/eps_obs_lp_material_spread_theta_summary.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_cp_eps_material_drift/eps_obs_ideal_center_6p5ghz.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_cp_eps_material_drift/eps_obs_ideal_center_summary.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_cp_eps_material_drift/STAGE4G_EFF_MECHANISM_AUDIT.md`

Current result:

- Same-direction over-subtraction remains visible in the refreshed export:
  - freq points with `rho >= 1` and `|Delta_phi| <= 15 deg`: `34.0%`
  - angle rows with band-majority overcorrection: `8/23`
- LP-target back-solved `eps_obs_lp` still disagrees materially with the shared current `eps_eff`:
  - overall mean `|eps_obs_lp - eps_eff|`: `0.3221`
  - overall mean magnitude bias: `-1.50 dB`
  - overall median `|phase drift|`: `29.34 deg`
- Center-frequency ideal-target replay at `6.5 GHz` shows a larger shared-model mismatch:
  - overall mean `|eps_obs_ideal - eps_eff|`: `0.2794`
  - overall mean magnitude bias: `-4.31 dB`
  - overall median `|phase drift|`: `22.49 deg`
- Material spread remains real even though current `eps_eff` is shared:
  - same `(theta, f)` current `eps_eff` material spread mean max-pairwise diff: effectively `0.0000`
  - same `(theta, f)` LP-target back-solved `eps_obs` material spread mean max-pairwise diff: `0.3343`

Interpretation:

- The current CP `eff` problem is consistent with a shared-`eps_eff` model mismatch, not with simple high-angle growth of `|eps_eff|`.
- The refreshed replay still supports the earlier stage4j/stage4k direction: the required `eps` to hit either LP-bridge or ideal targets is materially different from the single shared current correction term.
- A direct "after metal normalization" `eps`-drift replay is not yet available from the current bundle because there is no CP metal-normalized freq-resolved `eps` export to compare against.
- The closest existing proxy remains the PEC-based correction branch:
  - `analysis_stages/paper_code_review_bundle_20260414/data/stage_4/stage4h_pec_based_cp_correction_20260414/pec_based_cp_comparison_summary.csv`
  - even there, corrected CP still remains below ideal in `21/23` rows for the ratio variant and `22/23` rows for the simple variant, so a simple anchor change does not remove the CP `eff` mismatch.

## Fresnel Slab Sensitivity Replay

- Added bundle-local debug replay:
  - `analysis_stages/paper_code_review_bundle_20260414/code/verify_fresnel_slab_sensitivity.py`
- Current outputs:
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_fresnel_slab_sensitivity_full.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_fresnel_slab_sensitivity_summary.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_fresnel_brewster_summary.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/VERIFY_FRESNEL_SLAB_SENSITIVITY.md`

Current result:

- The current theory path is confirmed to be a finite-thickness slab model in both the Stage 1 sanity code and the current LP metal-normalized replay:
  - `stage_1_sanity_check_fresnel.py`: `SLAB_THICKNESS_M = 0.1`
  - `verify_lp_metal_normalized.py`: `WALL_THICKNESS_MM = 100.0`
- Observed main-range LP metal-normalized Fresnel deviations remain small:
  - concrete TE/TM: `0.166 / 0.239 dB`
  - glass TE/TM: `0.275 / 0.293 dB`
  - wood TE/TM: `0.256 / 0.380 dB`
- Under `eps_r +/-10%` and thickness `95-105 mm`, the slab sensitivity envelope is larger than the observed deviation in every material/polarization:
  - concrete TE/TM envelope: `0.614 / 1.264 dB`
  - glass TE/TM envelope: `1.844 / 2.424 dB`
  - wood TE/TM envelope: `5.729 / 6.348 dB`
- Thickness-only variation already explains most rows; concrete TM is the only current case that needs combined `eps_r` plus thickness drift to fully cover the observed `0.239 dB`.
- Brewster-side TM steepness near the main-range edge is strongest for wood:
  - wood Brewster angle: `54.67 deg`, main limit `45 deg`, TM drop from `45 -> 50 deg`: `-7.334 dB`
  - glass TM drop from `60 -> 65 deg`: `-7.280 dB`
  - concrete TM drop from `55 -> 60 deg`: `-3.977 dB`

Interpretation:

- The remaining post-metal-normalization LP mismatch is plausibly explained by modest slab-parameter uncertainty.
- This supports treating the residual `0.17-0.38 dB` discrepancy as theory-parameter sensitivity rather than as a strong contradiction of the same-angle metal-anchor correction.
- Wood TM remains the most fragile branch near the Brewster-side region, consistent with its caution-only handling outside the current main range.

## Current Ordering Counts

- raw below ideal: `0/23`
- eff below ideal: `16/23`
- LP Gamma_X below ideal: `15/23`
- both LP and CP eff below ideal: `15/23`

## Same-Stage Gain Audit

- CP raw same-stage negative-gap rows: `0/23`
- CP eff same-stage negative-gap rows: `6/23`
- LP same-stage negative-gap rows: `15/23`

## Synthetic Bridge

- Implemented code:
  - `analysis_stages/paper_code_review_bundle_20260414/code/verify_estimator_roundtrip.py`
- Current outputs:
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_estimator_roundtrip_full.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_estimator_roundtrip_summary.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/VERIFY_ESTIMATOR_ROUNDTRIP.md`

Current result:

- CP angle-resolved replay remains numerically exact:
  - `Gamma_C_raw`: `13/13` identity-pass rows, max complex abs error `2.27e-16`
  - `Gamma_C_eff`: `13/13` identity-pass rows, max complex abs error `2.28e-16`
- Fixed single-reference replay remains catastrophically unstable:
  - LP `Gamma_X` max magnitude abs error: `5.016`
  - LP `Gamma_C` max magnitude abs error: `17.861`
  - CP `Gamma_C_raw` max magnitude abs error: `16.597`
  - CP `Gamma_C_eff` max magnitude abs error: `16.403`

Interpretation:

- The estimator algebra itself is not the dominant distortion source.
- The severe error appears when the reference stack is held fixed instead of angle-resolved, which reinforces the reference-normalization diagnosis.

## A1 Material-Specific CP Eff Replay

- Added bundle-local debug replay:
  - `analysis_stages/paper_code_review_bundle_20260414/code/verify_cp_eff_material_specific_eps.py`
- Current outputs:
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_cp_eff_material_specific_eps.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_cp_eff_material_specific_eps_freq.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_cp_eff_material_specific_eps_summary.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/VERIFY_CP_EFF_MATERIAL_SPECIFIC_EPS.md`

Current result:

- Locked Stage 4 CP eff baseline remains `16/23` below-ideal rows.
- Replayed current shared-`eps_eff` path from refreshed freq-resolved export gives `8/23` below-ideal rows.
- LP-target pointwise replay is a negative control and remains `15/23`.
- Ideal-target constant replay at `6.5 GHz` reduces the count to:
  - band replay: `3/23`
  - `6.5 GHz`: `2/23`
- The current `< 5/23` pass criterion is therefore met for the ideal-target replay.

Interpretation:

- The CP eff issue is now tightly localized to the shared `eps_eff` correction model.
- A material-specific ideal-target replay removes most violations without touching the CP raw branch.
- The LP-target replay confirms that simply forcing CP eff toward the LP bridge does not solve the CP problem.

Caveat:

- The locked `stage4f` shared-eff magnitude and the refreshed shared-eff replay are no longer identical for glass and wood.
- Largest current mismatch:
  - `glass 50 deg`: band magnitude difference `0.191417`
- Raw CP band magnitude remains aligned; the mismatch is specific to the shared-eff branch.

## A2 CP Metal-Normalized Extension Status

- Added independent bundle-local verifier:
  - `analysis_stages/paper_code_review_bundle_20260414/code/verify_cp_metal_normalized_extension.py`
- Current outputs:
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_cp_metal_normalized_extension.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_cp_metal_normalized_extension_freq.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_cp_metal_normalized_extension_summary.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/VERIFY_CP_METAL_NORMALIZED_EXTENSION.md`
- The replay is rebuilt directly from the Stage 3 CP freq-resolved export and then checked against the locked Stage 4 metal-floor branch.
- Legacy reference outputs remain:
  - `analysis_stages/paper_code_review_bundle_20260414/results/patch_cp_metal_floor_extracted.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/metal_floor_same_angle_audit_summary.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/STAGE4D_CP_METAL_FLOOR_AUDIT.md`

Current result:

- Independent replay reproduces the locked metal-floor branch to numerical precision:
  - max magnitude difference vs locked `stage4f`: `4.441e-16`
  - max gain difference vs locked `stage4f`: `8.438e-15 dB`
- Same-angle sign contradiction is removed in that legacy branch:
  - negative rows: `0/23`
- But the metal-floor branch is larger than ideal in every matched-angle row:
  - metal-floor residual > ideal residual: `23/23`
- This remains true at the `6.5 GHz` replay point as well:
  - negative rows: `0/23`
  - residual > ideal rows: `23/23`

Interpretation:

- The repository now has an independent verifier showing that the CP metal-anchored cross-check is numerically reproducible from the current Stage 3 export.
- It is still not directly comparable to the absolute-like Stage 4 headline residual.
- It remains useful as a diagnostic reference, not as a production correction path.

## Final Budget Report

- Added final consolidated report:
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/RESIDUAL_BUDGET_FINAL.md`
- This report consolidates LP, CP raw, and CP eff diagnostics into one paper-ready residual budget summary.
- Added final diagnostic closure note:
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/CP_MATERIAL_EFFECT_FINAL_DIAGNOSTIC_STATUS.md`
  - This note marks the end of the diagnostic phase and separates it from the remaining production-path decisions.

- CP angle-resolved synthetic identity is exact to numerical precision:
  - `Gamma_C_raw`: `13/13` pass
  - `Gamma_C_eff`: `13/13` pass
  - `Gamma_X`: `13/13` pass
- LP angle-resolved synthetic identity is exact for the Stage 1 linear truth:
  - `R_TE`: `13/13` pass
  - `R_TM`: `13/13` pass
- LP `Gamma_X` / `Gamma_C` do not show `13/13` because that comparison is against the Stage 2 CP-truth convention, not because the LP extractor fails its own injected Stage 1 truth.
- fixed single-reference replay shows large drift for both LP and CP, so reference reuse itself is a strong distortion source once the angle-resolved pairing is removed.

Interpretation:

- The extractor algebra is not the dominant failure mode in the current angle-resolved path.
- The current contradiction is more consistent with stage mismatch, reference handling, and system-level normalization than with a broken Stage 3 identity formula.

## 2x2 Calibration Prototype

- Implemented code:
  - `analysis_stages/paper_code_review_bundle_20260414/code/prototype_2x2_calibration.py`
- Current outputs:
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/prototype_2x2_calibration_matrices.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/prototype_2x2_calibration_sample_reconstruction.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/prototype_2x2_calibration_theta_summary.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/PROTOTYPE_2X2_CALIBRATION.md`

Current result:

- This is a supervised single-frequency prototype at `6.5 GHz` using existing truth and current Stage 3 raw stacks.
- Per-theta alternating least-squares fits converge with low residual:
  - LP fit RMS range: `3.213e-07` to `1.019e-04`
  - CP fit RMS range: `3.617e-07` to `1.095e-04`
- Estimated calibration matrices are not ill-conditioned in the current prototype:
  - LP `cond(J_rx)`: `1.34` to `1.66`, `cond(J_tx)`: `1.01` to `1.42`
  - CP `cond(J_rx)`: `1.31` to `1.58`, `cond(J_tx)`: `1.01` to `1.64`
- Reconstructed scattering error remains non-zero but bounded:
  - LP mean `S_hat` error: `8.310e-03` to `6.780e-02`
  - CP mean `S_hat` error: `9.207e-03` to `6.505e-02`

Interpretation:

- A shared `2x2` calibration framework is numerically plausible with the current data.
- This is still prototype-only and is not yet wired into the headline Stage 3 or Stage 4 exporters.
- Because current truth is still single-frequency, this prototype should be treated as structural feasibility evidence rather than final calibrated production logic.

## Outputs

- Authoritative wide: `analysis_stages\paper_code_review_bundle_20260414\results\residual_ordering_authoritative_wide.csv`
- Branch long: `analysis_stages\paper_code_review_bundle_20260414\results\residual_ordering_authoritative_branch_long.csv`
- Suppression long: `analysis_stages\paper_code_review_bundle_20260414\results\residual_ordering_authoritative_suppression_long.csv`
- Band summary: `analysis_stages\paper_code_review_bundle_20260414\results\residual_ordering_authoritative_band_summary.csv`
- Stage4f full: `analysis_stages\paper_code_review_bundle_20260414\results\stage4f_raw_primary_full.csv`
- Stage4f summary: `analysis_stages\paper_code_review_bundle_20260414\results\stage4f_raw_primary_summary.csv`
