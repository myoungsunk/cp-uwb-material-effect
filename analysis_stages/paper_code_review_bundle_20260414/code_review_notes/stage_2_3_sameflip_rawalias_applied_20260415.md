# Stage 2-3 Fix Applied (2026-04-15)

Applied changes:

1. `Stage 2 / cp_transform.py`
   - added `Gamma_same_*` and `Gamma_flip_*` alias columns
   - added PEC same/flip sanity columns
   - locked the current interpretation:
     - `Gamma_same = Gamma_X`
     - `Gamma_flip = Gamma_C`

2. `Stage 3 / verify_lp_anchor_branch_lock.py`
   - changed the authoritative residual alias from `gamma_hat_c_cp_eff` to `gamma_hat_c_cp_raw`
   - kept `gamma_hat_c_cp_eff` as a supplementary corrected residual alias

Archived pre-edit code:

- `analysis_stages/stage2_3_code_archive_before_sameflip_rawalias_20260415/cp_transform.py`
- `analysis_stages/stage2_3_code_archive_before_sameflip_rawalias_20260415/verify_lp_anchor_branch_lock.py`

New outputs:

- Stage 2 alias rerun:
  - `analysis_stages/stage2_sameflip_alias_20260415/results/`
- Stage 3 raw-primary alias rerun:
  - `analysis_stages/lp_anchor_branch_lock_raw_primary_20260415/results/`

Quick verification:

- Stage 2 PEC row now explicitly shows `Gamma_same` small and `Gamma_flip` dominant.
- Stage 3 aliased patch export now shows:
  - `cp_residual_branch_name = gamma_hat_c_cp_raw`
  - `cp_residual_branch_supplementary_name = gamma_hat_c_cp_eff`
