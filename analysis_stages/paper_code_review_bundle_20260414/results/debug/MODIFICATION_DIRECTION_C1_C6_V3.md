# Stage 4 Modification Direction And Current Status

Execution date: `2026-04-16`

## Applied Now

### C2 / V1

- Implemented code:
  - `analysis_stages/paper_code_review_bundle_20260414/code/audit_coherent_vs_incoherent.py`
  - `analysis_stages/paper_code_review_bundle_20260414/code/verify_coherent_vs_incoherent.py`
- Current outputs:
  - `analysis_stages/paper_code_review_bundle_20260414/results/audit_coherent_vs_incoherent.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/audit_coherent_vs_incoherent_summary_by_material.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/audit_coherent_vs_incoherent_material_rollup.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/AUDIT_COHERENT_VS_INCOHERENT.md`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_coherent_vs_incoherent.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_coherent_vs_incoherent_summary_by_material.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_coherent_vs_incoherent_material_rollup.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/VERIFY_COHERENT_VS_INCOHERENT.md`

Current main-range finding:

- `gamma_hat_c_cp_eff`: `2 / 23` rows exceed the `1 dB` coherent-vs-incoherent gap threshold.
- `gamma_hat_c_cp_raw`: `0 / 23`
- `gamma_hat_x_cp_sys`: `0 / 23`
- `gamma_x_from_lp`: `0 / 23`
- `gamma_c_from_lp`: `0 / 23`

Interpretation:

- Cause #1 is directly evidenced, but only locally.
- The current direct evidence is narrow and concentrated; it does not by itself explain the full Stage 4 ordering contradiction.

### V2

- Implemented code:
  - `analysis_stages/paper_code_review_bundle_20260414/code/verify_single_freq_grid.py`
- Current outputs:
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_single_freq_grid_mapping.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_single_freq_grid_full.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_single_freq_grid_summary.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/results/debug/VERIFY_SINGLE_FREQ_GRID.md`

Bundle limitation:

- Stage 3 freq-resolved data in the current bundle spans only `6.24 GHz` to `6.74 GHz`.
- The requested `5.0 / 6.5 / 8.0 GHz` grid therefore maps to actual `6.24 / 6.50 / 6.74 GHz`.
- Ideal truth in the current bundle is only frequency-matched at `6.50 GHz`.

Current `6.50 GHz` replay result:

- band-average raw violations: `0`
- band-average eff violations: `8`
- band-average LP violations: `15`
- single-frequency raw violations: `0`
- single-frequency eff violations: `16`
- single-frequency LP violations: `15`

Interpretation:

- The current single-frequency pass criterion fails.
- In this bundle, band averaging alone is not sufficient as the sole explanation.
- No further `V2`-style single-frequency extension should be applied until additional multi-frequency ideal simulation is provided.
- Current `ideal TE/TM` truth is still single-frequency only; treat that as a hard constraint in follow-up audits.

Status lock:

- `V2` is frozen at the current debug-note level.
- Do not extend the single-frequency replay logic until new multi-frequency ideal truth is supplied.

### Code-Level Fixes

Applied code:

- `analysis_stages/paper_code_review_bundle_20260414/code/stage_4_build_specular_rx_direct_cp_reanalysis.py`
- `analysis_stages/paper_code_review_bundle_20260414/code/stage_4_audit_eff_mechanism.py`

Applied fixes:

- fixed the confirmed `repo_root` / `--stage4f-summary` argparser bug in `stage_4_build_specular_rx_direct_cp_reanalysis.py`
- changed `stage_4_build_specular_rx_direct_cp_reanalysis.py` defaults to repo-local stage assets instead of the external `E:` path
- added `GLASS_SPECULAR_RX.csv` then `GLSASS_SPECULAR_RX.csv` fallback resolution so the current staged asset name remains compatible while allowing the likely corrected spelling
- fixed `stage_4_audit_eff_mechanism.py` so `--stage4f-full` points to the bundle `data/stage_4/stage4f_raw_primary_dual_20260414` snapshot instead of a non-existent `code/`-relative sibling stage

Status:

- both scripts now run with their default arguments in the current workspace

### V3

Implemented code:

- `analysis_stages/paper_code_review_bundle_20260414/code/verify_estimator_roundtrip.py`

Current outputs:

- `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_estimator_roundtrip_full.csv`
- `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_estimator_roundtrip_summary.csv`
- `analysis_stages/paper_code_review_bundle_20260414/results/debug/VERIFY_ESTIMATOR_ROUNDTRIP.md`

Applied scope:

- pure estimator round-trip identity test using synthetic `(h_tilde, h3)` pairs
- angle-resolved reference-stack replay
- fixed single-reference replay at `theta=20 deg`

Current result:

- CP angle-resolved identity is exact to numerical precision for:
  - `Gamma_C_raw`
  - `Gamma_C_eff`
  - `Gamma_X`
- LP angle-resolved identity is exact to numerical precision for:
  - `R_TE`
  - `R_TM`
- LP `Gamma_X` / `Gamma_C` remain non-zero against the Stage 2 CP-truth comparison target, so those rows should not be interpreted as LP extractor failure.
- fixed single-reference replay produces large errors for both LP and CP, which makes reference reuse a first-class distortion candidate.

Interpretation:

- The Stage 3 extractor formulas pass the intended synthetic identity check in the angle-resolved setting.
- The current contradiction is therefore not best explained as an intrinsic estimator-algebra bug.

### 2x2 Calibration

Implemented code:

- `analysis_stages/paper_code_review_bundle_20260414/code/prototype_2x2_calibration.py`

Current outputs:

- `analysis_stages/paper_code_review_bundle_20260414/results/debug/prototype_2x2_calibration_matrices.csv`
- `analysis_stages/paper_code_review_bundle_20260414/results/debug/prototype_2x2_calibration_sample_reconstruction.csv`
- `analysis_stages/paper_code_review_bundle_20260414/results/debug/prototype_2x2_calibration_theta_summary.csv`
- `analysis_stages/paper_code_review_bundle_20260414/results/debug/PROTOTYPE_2X2_CALIBRATION.md`

Applied scope:

- supervised single-frequency `6.5 GHz` prototype
- per-theta alternating least-squares fit of `J_rx` and `J_tx`
- reconstruction audit of `S_hat = J_rx^{-1} H J_tx^{-1}`

Current result:

- convergence is stable across all current thetas for both LP and CP
- matrix conditioning stays modest, roughly `1.3` to `1.6`
- recovered `S_hat` error remains non-zero but is still small enough to keep the calibration path plausible as a medium-term structural replacement for the current scalar branch estimators

Interpretation:

- a unified Jones-like `2x2` calibration path is feasible with the existing bundle data
- this remains prototype-only and should stay separate from the headline Stage 3/4 pipeline until the calibration objective and production export semantics are fixed

### C1 + C6

Applied decision:

- `C1` and `C6` are no longer treated as separate exporters.
- One new authoritative exporter now owns the residual ordering logic and the Stage 4e-style long-form schema.

Implemented code:

- `analysis_stages/paper_code_review_bundle_20260414/code/stage_4_build_residual_ordering_authoritative.py`
- `analysis_stages/paper_code_review_bundle_20260414/code/stage_4_build_residual_3way_comparison.py`
- `analysis_stages/paper_code_review_bundle_20260414/code/stage_4_build_raw_primary_dual_reporting.py`

Current outputs:

- `analysis_stages/paper_code_review_bundle_20260414/results/residual_ordering_authoritative_wide.csv`
- `analysis_stages/paper_code_review_bundle_20260414/results/residual_ordering_authoritative_branch_long.csv`
- `analysis_stages/paper_code_review_bundle_20260414/results/residual_ordering_authoritative_suppression_long.csv`
- `analysis_stages/paper_code_review_bundle_20260414/results/residual_ordering_authoritative_summary.csv`
- `analysis_stages/paper_code_review_bundle_20260414/results/residual_ordering_authoritative_band_summary.csv`
- `analysis_stages/paper_code_review_bundle_20260414/results/residual_ordering_authoritative_table_for_review.csv`
- `analysis_stages/paper_code_review_bundle_20260414/results/stage4f_raw_primary_full.csv`
- `analysis_stages/paper_code_review_bundle_20260414/results/stage4f_raw_primary_summary.csv`
- `analysis_stages/paper_code_review_bundle_20260414/results/debug/APPLIED_MODIFICATION_STATUS.md`

Authoritative schema decision:

- Long-form outputs reuse:
  - `series_id`
  - `series_label`
  - `method_family`
  - `normalization_scope`
  - `directly_comparable_to_ideal`

### Same-Stage Numerator And Gap Decomposition

Applied code:

- `analysis_stages/stage3_patch_paper_final_20260414/lp/code/export_patch_lp_stage3.py`
- `analysis_stages/stage3_patch_paper_final_20260414/cp/code/export_patch_cp_stage3.py`
- `analysis_stages/paper_code_review_bundle_20260414/code/stage_3_export_lp_patch_stage3.py`
- `analysis_stages/paper_code_review_bundle_20260414/code/stage_3_export_cp_patch_stage3.py`
- `analysis_stages/paper_code_review_bundle_20260414/code/stage_4_build_residual_ordering_authoritative.py`

Applied export additions:

- LP stage-consistent numerator:
  - `B_lp_sys_mag`
  - `G_lp_sys_db`
- CP stage-consistent numerator:
  - `B_cp_proxy_mag`
  - `G_cp_raw_sys_db`
  - `G_cp_eff_sys_db`
- Explicit magnitude semantics on Stage 3 complex exports:
  - `*_abs_of_mean`
  - `*_mean_of_abs`
  - legacy `*_mag` kept as the current `mean_of_abs` alias for backward compatibility

Snapshot refresh:

- regenerated `analysis_stages/stage3_patch_paper_final_20260414/lp/results/patch_lp_extracted.csv`
- regenerated `analysis_stages/stage3_patch_paper_final_20260414/lp/results/patch_lp_extracted_freq_resolved.csv`
- regenerated `analysis_stages/stage3_patch_paper_final_20260414/cp/results/patch_cp_extracted.csv`
- regenerated `analysis_stages/stage3_patch_paper_final_20260414/cp/results/patch_cp_extracted_freq_resolved.csv`
- mirrored those refreshed exports into the bundle snapshots under `analysis_stages/paper_code_review_bundle_20260414/data/stage_3`

Applied decomposition additions inside the authoritative Stage 4 table:

- numerator mismatch terms:
  - `Delta_G_cp_raw_numerator_mismatch_db`
  - `Delta_G_cp_eff_numerator_mismatch_db`
  - `Delta_G_lp_numerator_mismatch_db`
- residual mismatch terms:
  - `Delta_G_cp_raw_residual_mismatch_db`
  - `Delta_G_cp_eff_residual_mismatch_db`
  - `Delta_G_lp_residual_mismatch_db`
- full same-stage-vs-ideal gap terms:
  - `Delta_G_ideal_minus_cp_raw_sys_db`
  - `Delta_G_ideal_minus_cp_eff_sys_db`
  - `Delta_G_ideal_minus_lp_sys_db`

Current same-stage negative-gap counts:

- CP raw same-stage: `0 / 23`
- CP eff same-stage: `6 / 23`
- LP same-stage: `15 / 23`

Interpretation:

- `CP raw` does not exceed the ideal upper bound under the same-stage numerator in the current main range.
- `CP eff` still has a limited set of same-stage negative-gap rows.
- `LP` still exceeds the ideal upper bound on many rows even after numerator alignment, so the issue is not reducible to numerator mismatch alone.

Current ordering counts from the authoritative exporter:

- raw below ideal: `0 / 23`
- eff below ideal: `16 / 23`
- LP `Gamma_X` below ideal: `15 / 23`
- both LP and CP eff below ideal: `15 / 23`

Per-material split:

- concrete: raw=`0 / 8`, eff=`5 / 8`, LP=`4 / 8`
- glass: raw=`0 / 9`, eff=`6 / 9`, LP=`6 / 9`
- wood: raw=`0 / 6`, eff=`5 / 6`, LP=`5 / 6`

What changed in `stage4f_raw_primary_full.csv`:

- Headline `G_*_db` values remain unchanged.
- New audit-only columns are now exported:
  - `lp_residual_mag`
  - `lp_minus_ideal_residual_db`
  - `lp_below_ideal_flag`
  - `both_lp_and_cp_eff_below_ideal_flag`
- `stage4f` is now a derived projection from the authoritative table rather than a separate logic path.

## Direction Still Pending

### Namespace Control

Maintainability rule going forward:

- do not add parallel one-off scripts for mismatch-signature or Brewster-family checks if the same concern already has a Stage 4 namespace
- absorb those follow-up audits into the existing `stage4j_eff_mismatch_signature`, `stage4k_alpha_beta_proxy_test`, and `stage4l_brewster_deff_checks` lanes
- keep the bundle-first stabilization flow, then mirror the stabilized code back into the matching worktree stage

## Bottom Line

- `C2`, `V1`, `V2`, `V3`, the code-level path/argparser fixes, and the `C1+C6` unification direction are now reflected in code and outputs.
- The authoritative Stage 4 residual-ordering table is the new single source for downstream plotting and manuscript-safe `stage4f` export.
- same-stage numerator and gap-decomposition audit columns are now part of the current Stage 3 and Stage 4 export path.
- synthetic bridge and `2x2` calibration now exist as separate debug/prototype tracks.
- the main unresolved step is not estimator identity anymore; it is deciding whether and how the prototype calibration path should replace the current scalar production estimators.
