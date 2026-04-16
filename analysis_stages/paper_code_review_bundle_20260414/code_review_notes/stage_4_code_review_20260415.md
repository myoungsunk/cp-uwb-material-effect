# Stage 4 Code Review (2026-04-15)

## Scope

Reviewed Stage 4 core chain and direct-CP comparator:

- `analysis_stages/stage4b_convention_locked_20260414/code/build_suppression_gain_convention_locked.py`
- `analysis_stages/stage4c_same_angle_gap_audit_20260414/code/audit_same_angle_gap.py`
- `analysis_stages/stage4e_residual_3way_comparison_20260414/code/build_residual_3way_comparison.py`
- `analysis_stages/stage4f_raw_primary_dual_20260414/code/build_raw_primary_dual_reporting.py`
- `analysis_stages/stage4g_eff_mechanism_audit_20260414/code/audit_eff_mechanism.py`
- `analysis_stages/direct_cp_one_point_sanity_20260414/code/compare_direct_cp_one_point.py`
- `analysis_stages/direct_cp_one_point_sanity_20260414/code/build_direct_cp_one_point_from_references.py`

Also spot-checked the supplementary helpers:

- `analysis_stages/stage4d_cp_metal_floor_audit_20260414/code/build_cp_metal_floor_audit.py`
- `analysis_stages/stage4h_pec_based_cp_correction_20260414/code/build_pec_based_cp_comparison.py`
- `analysis_stages/stage4j_eff_mismatch_signature_20260414/code/build_eff_mismatch_signature.py`
- `analysis_stages/stage4k_alpha_beta_proxy_test_20260414/code/build_alpha_beta_proxy_test.py`
- `analysis_stages/stage4l_brewster_deff_checks_20260414/code/build_brewster_deff_checks.py`

## Findings

### P1. Stage 4 still depends on the pre-raw-primary Stage 3 alias export

`stage4b` still defaults to the old alias-locked Stage 3 folder:

- `build_suppression_gain_convention_locked.py:60-67`

```python
default=repo_root
    / "analysis_stages"
    / "lp_anchor_branch_lock_20260414"
    / "results"
    / "patch_cp_extracted_with_lp_anchor_alias.csv"
```

After the Stage 3 raw-primary fix, the authoritative alias export lives in:

- `analysis_stages/lp_anchor_branch_lock_raw_primary_20260415/results/patch_cp_extracted_with_lp_anchor_alias.csv`

So the Stage 4 default chain still boots from the stale `20260414` alias snapshot, not from the raw-primary lock. That means Stage 4 can silently rebuild headline metrics from the obsolete `cp_residual_branch = gamma_hat_c_cp_eff` interpretation even after Stage 3 semantics were corrected.

Impact:

- `stage4b` is not consuming the currently authoritative Stage 3 alias lock.
- any rerun without explicit CLI overrides can regress to the old eff-based residual semantics.

Recommendation:

- repoint Stage 4 defaults to the `lp_anchor_branch_lock_raw_primary_20260415` export
- or make the input path mandatory so Stage 4 never falls back silently

### P1. `stage4c -> stage4e -> stage4f` still carries eff semantics implicitly through alias-coupled columns

The core coupling is:

- `stage4b` builds `G_supp_patch_db` from `cp_residual_branch_mag`
  - `build_suppression_gain_convention_locked.py:191-194`
- `stage4c` treats inherited `G_supp_patch_db` and `Delta_G_db` as the effective branch
  - `audit_same_angle_gap.py:85, 104-109, 127-129`
- `stage4e` renames those inherited columns to `G_patch_eff_db` / `Delta_ideal_minus_eff_db`
  - `build_residual_3way_comparison.py:63-87`
- `stage4f` then treats the renamed columns as authoritative eff metrics
  - `build_raw_primary_dual_reporting.py:58-67`

This is fragile because the meaning of `G_supp_patch_db` is not intrinsic. It depends entirely on what `stage4b` happened to bind to `cp_residual_branch_mag` upstream. If the Stage 3 alias flips from eff to raw, `stage4c/e/f` will still label the inherited numbers as eff unless someone manually rewires every downstream stage.

Impact:

- the Stage 4 chain is alias-sensitive instead of quantity-explicit
- raw/eff semantics can change without a numeric failure or exception
- reviewer-facing tables can silently drift out of sync with Stage 3 naming decisions

Recommendation:

- in `stage4c`, compute both paths directly:
  - `G_patch_raw_db = db_ratio(B_mag, gamma_hat_c_cp_raw_mag)`
  - `G_patch_eff_db = db_ratio(B_mag, gamma_hat_c_cp_eff_mag)`
  - and derive both deltas explicitly
- in `stage4e/f`, stop renaming inherited alias-coupled columns; consume the explicit raw/eff columns only
- keep `stage4b` audit-only, or rename its patch column to something like `G_supp_patch_alias_db`

### P1. Direct CP one-point comparator cannot answer the question Stage 4f says it should answer

`stage4f` says the one-point sanity should answer:

- which receive branch is physically the residual branch
- whether the directly observed CP residual is closer to `raw` or `eff`

But `compare_direct_cp_one_point.py` does not currently support that.

Problems:

1. Patch candidates omit the raw residual branch
   - `compare_direct_cp_one_point.py:200-220`
   - only `gamma_hat_x_cp_sys` and `gamma_hat_c_cp_eff` are included
2. Branch matching is magnitude-only
   - `compare_direct_cp_one_point.py:278-286`
3. The markdown explicitly reports “closest locked branch by magnitude”
   - `compare_direct_cp_one_point.py:355-366`
4. Acceptance checks also compare only small/large magnitude ordering
   - `compare_direct_cp_one_point.py:469-516`

This means the comparator cannot distinguish:

- `raw` vs `eff` closeness
- receive-handedness mapping
- same magnitude but opposite/rotated complex phase

By contrast, `build_direct_cp_one_point_from_references.py` already reconstructs both `gamma_c_raw` and `gamma_c_eff`, so the missing piece is comparator logic rather than data availability.

Recommendation:

- add `gamma_hat_c_cp_raw` to patch candidates
- compare in complex space, not only by `|delta mag|`
- preserve `rx_cp` handedness labels in the decision logic

### P2. Stage 4f summary hard-codes row counts instead of reading the computed tables

`build_raw_primary_dual_reporting.py:213-217` writes:

```python
- same-angle negative-gap rows for `raw`: `0 / 23`
- same-angle negative-gap rows for `eff`: `16 / 23`
- same-angle negative-gap rows for `metal-floor`: `0 / 23`
```

These are literal strings, not values derived from `raw_primary` or `summary_df`.

Impact:

- if input rows, angle filters, or branch definitions change, the markdown can become stale while the CSVs update
- this is especially risky now that Stage 1-3 semantics have already been revised

Recommendation:

- compute these counts directly from the loaded data before writing the markdown

### P2. Stage 4b still hard-codes `Gamma_X`/`Gamma_C` semantics instead of consuming the explicit same/flip alias from Stage 2

`build_suppression_gain_convention_locked.py:183-186` hard-codes:

```python
merged["ideal_residual_branch_name"] = "Gamma_X"
merged["ideal_dominant_branch_name"] = "Gamma_C"
merged["ideal_residual_branch_mag"] = merged["Gamma_X_mag"]
merged["ideal_dominant_branch_mag"] = merged["Gamma_C_mag"]
```

That was workable before Stage 2 same/flip aliasing existed. After the Stage 2 update, the paper-safe semantics are available explicitly via the PEC-asserted same/flip mapping, but Stage 4 still bypasses them and assumes the old names.

Impact:

- current numerics happen to agree with the lock, but the semantic contract is still implicit
- Stage 4 will not automatically inherit future convention tightening from Stage 2

Recommendation:

- have Stage 4 consume the Stage 2 same/flip alias columns directly
- or at minimum assert that PEC rows still imply `same -> Gamma_X`, `flip -> Gamma_C` before building Stage 4 outputs

## What Looks Sound

### Stage 4g is doing the right kind of root-cause decomposition

`audit_eff_mechanism.py` is the strongest physical-diagnosis file in Stage 4.

It explicitly computes:

- `correction = gamma_res_raw - gamma_res_eff`
- `rho = |correction| / |gamma_res_raw|`
- `delta_phi`
- LP-target back-solved `eps_obs_lp`
- material spread of the required `eps`

Relevant lines:

- `audit_eff_mechanism.py:149-176`
- `audit_eff_mechanism.py:183-221`
- `audit_eff_mechanism.py:260-327`

So Stage 4g is not just plotting the symptom; it is actually separating:

- same-direction over-subtraction
- shared-`eps_eff` mismatch versus LP-target back-solved `eps`

That file should remain the primary root-cause note for why `eff` fails.

### Stage 4j / 4k / 4l are real helper analyses, not empty wrappers

The current `analysis_stages` copies contain actual logic:

- `stage4j` fits metal phase drift and checks circularity sensitivity
- `stage4k` tests alpha/beta proxy kernels
- `stage4l` checks Brewster exclusion and `d_eff(f)`

So these are reviewable helper stages. They are not import-only placeholders in the current workspace copy.

## Recommended Role Split

### Authoritative

- `stage4c`: physical gate on same-angle `ideal >= patch`
- `stage4e`: explicit raw/eff/metal-floor exports
- `stage4f`: raw-primary reporting only if fed explicit raw/eff columns
- `stage4g`: eff failure mechanism audit

### Audit-only

- `stage4a`
- `stage4b`
- `stage4d`
- `stage4h`
- direct CP one-point sanity
- specular reanalysis branches

## Immediate Fix Order

1. Repoint Stage 4 defaults to the raw-primary Stage 3 alias export.
2. Make `stage4c` compute raw/eff directly from `gamma_hat_c_cp_raw_mag` and `gamma_hat_c_cp_eff_mag`.
3. Make `stage4e/f` consume only explicit raw/eff columns.
4. Update the one-point comparator to include raw and use complex-distance matching.
5. Remove hard-coded row counts from Stage 4f markdown.
