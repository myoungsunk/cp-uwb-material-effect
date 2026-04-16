# Stage 1-3 Output Change Review (2026-04-15)

This note compares the pre-fix outputs against the post-fix outputs after the Stage 1 shared-common-lock update and the Stage 2/3 same-flip + raw-primary alias update.

## Stage 1

Compared:

- old: `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414/`
- new: `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_shared_common_ab_20260415/`

Result:

- `truth_table_linear_raw.csv`: hash-identical
- `truth_table_linear_locked.csv`: hash-identical
- `truth_table_cp.csv`: hash-identical

So the old authoritative outputs were preserved.

New files were added only:

- `truth_table_linear_shared_common_lock.csv`
- `truth_table_cp_raw.csv`
- `truth_table_cp_shared_common_lock.csv`
- `truth_table_cp_lock_variant_comparison.csv`
- `truth_table_cp_lock_variant_summary.csv`

Interpretation:

- Stage 1 changed by **adding variants**, not by changing the existing official outputs.

## Stage 2

Compared:

- old: `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414/truth_table_cp.csv`
- new: `analysis_stages/stage2_sameflip_alias_20260415/results/truth_table_cp_locked_sameflip.csv`

Result:

- row count unchanged: `52 -> 52`
- common CP numerics unchanged to machine precision:
  - `Gamma_X_mag max abs diff = 1.11e-16`
  - `Gamma_C_mag max abs diff = 2.22e-16`
  - phase diffs are also only roundoff-level

Added columns:

- `Gamma_same_real`, `Gamma_same_imag`, `Gamma_same_mag`, `Gamma_same_phase_deg`
- `Gamma_flip_real`, `Gamma_flip_imag`, `Gamma_flip_mag`, `Gamma_flip_phase_deg`
- `cp_same_branch_source`, `cp_flip_branch_source`
- `cp_same_branch_interpretation`, `cp_flip_branch_interpretation`
- `cp_pec_same_flip_sanity_pass`, `cp_pec_same_flip_sanity_note`

Interpretation:

- Stage 2 changed by **adding explicit same/flip semantics and PEC sanity metadata**.
- The underlying `Gamma_X / Gamma_C` values did not materially change.

## Stage 3

Compared:

- old: `analysis_stages/lp_anchor_branch_lock_20260414/results/`
- new: `analysis_stages/lp_anchor_branch_lock_raw_primary_20260415/results/`

### 3a. Branch-lock verdict

The headline mapping verdict stayed the same:

- main rows audited: `29`
- ideal small branch = `Gamma_X`: `29/29`
- LP small branch = `gamma_x_from_lp`: `29/29`
- patch small branch = `gamma_hat_c_cp_eff`: `29/29`
- LP aligned vote: `29/29`
- patch swapped vote: `29/29`

So the branch-mapping conclusion did not flip.

### 3b. Error means

The summary means shifted slightly:

- LP aligned mean abs error: `0.071598 -> 0.071366`
- LP swapped mean abs error: `0.579540 -> 0.578750`
- patch aligned mean abs error: `0.573917 -> 0.529120`
- patch swapped mean abs error: `0.106229 -> 0.109407`

Interpretation:

- The overall mapping verdict is unchanged.
- The small numeric shifts come from rerunning the audit against the Stage 2 shared-common/same-flip CP truth rather than the older locked-only CP reference.

### 3c. Alias export semantics

This is the main intentional output change.

Old alias export:

- `cp_residual_branch_name = gamma_hat_c_cp_eff`

New alias export:

- `cp_residual_branch_name = gamma_hat_c_cp_raw`
- `cp_residual_branch_supplementary_name = gamma_hat_c_cp_eff`

Example at `concrete / 10 deg`:

- old `cp_residual_branch_mag = 0.1808198363` (eff)
- new `cp_residual_branch_mag = 0.1084376540` (raw)

So the primary residual alias now follows the paper-safe raw-primary rule.

### 3d. Patch-stage source consistency

The new aliased patch export matches the current patch CP source exactly:

- `gamma_hat_x_cp_sys_mag alias_vs_patch max abs diff = 8.33e-17`
- `gamma_hat_c_cp_raw_mag alias_vs_patch max abs diff = 8.33e-17`
- `gamma_hat_c_cp_eff_mag alias_vs_patch max abs diff = 9.71e-17`
- `r_te_proxy_mag alias_vs_patch max abs diff = 8.33e-17`
- `r_tm_proxy_mag alias_vs_patch max abs diff = 8.33e-17`

Interpretation:

- The new Stage 3 alias export is internally consistent with the current `patch_cp_extracted.csv`.
- If some common columns differ versus the older 2026-04-14 alias artifact, that older alias file should be treated as stale rather than authoritative.

## Bottom Line

1. Stage 1 official outputs did not change; only new comparison variants were added.
2. Stage 2 CP numerics did not change; only same/flip aliases and PEC sanity metadata were added.
3. Stage 3 branch-mapping verdict did not change; the intended output change is that the exported primary residual alias is now `raw`, with `eff` preserved as supplementary.
