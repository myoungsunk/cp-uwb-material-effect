# Stage 0. Notation Lock

## Current Status

- This file is the paper-wide notation lock.
- On `2026-04-15`, the Stage 2 same/flip CSV labels were refreshed so the
  internal branch labels are now:
  - `cp_same_branch_source = Gamma_same`
  - `cp_flip_branch_source = Gamma_flip`
- Paper symbols remain:
  - `Gamma_X`
  - `Gamma_C`

## Core Rule

- Manuscript notation uses ideal/material symbols:
  - `R_TE(f, theta_i)`
  - `R_TM(f, theta_i)`
  - `Gamma_X = (R_TE + R_TM) / 2`
  - `Gamma_C = (R_TE - R_TM) / 2`
- Internal locked CSV aliases use branch-safe names:
  - `Gamma_same` = paper `Gamma_X`
  - `Gamma_flip` = paper `Gamma_C`
- Patch/system quantities stay explicitly system-stage:
  - `gamma_hat_cross_agm_cp`: dominant patch CP branch
  - `gamma_hat_rr_raw_cp`: primary residual patch CP branch
  - `gamma_hat_rr_leakage_corrected_cp`: supplementary corrected residual branch
  - legacy compatibility columns remain:
    - `gamma_hat_x_cp_sys`
    - `gamma_hat_c_cp_raw`
    - `gamma_hat_c_cp_eff`
  - Stage 3 leakage coefficient:
    - `m3_leakage_lr_over_rr`
  - `R_hat_yy_sys`, `R_hat_zz_sys`: LP system co-pol branches
  - `R_hat_yz_sys`, `R_hat_zy_sys`: LP leakage monitors

## Terminology Lock

- `ground truth`: Fresnel / ideal TE-TM only
- `upper bound`: ideal CP derived from the locked linear truth
- `system result`: patch-stage extracted quantity
- `conservative system result`: CP raw residual
- `supplementary corrected result`: CP eff residual
- `calibration / consistency reference`: PEC or LP metal reference

## Locked Symbol Map

| Paper symbol | Internal lock / CSV label | Meaning |
| --- | --- | --- |
| `R_TE`, `R_TM` | `R_TE_*`, `R_TM_*` | ideal complex reflection coefficients |
| `Gamma_X` | `Gamma_same` | ideal same-hand CP branch |
| `Gamma_C` | `Gamma_flip` | ideal flipped-hand CP branch |
| `gamma_hat_cross_agm_cp` | legacy alias: `gamma_hat_x_cp_sys` | dominant patch CP branch |
| `gamma_hat_rr_raw_cp` | legacy alias: `gamma_hat_c_cp_raw` | primary patch residual branch |
| `gamma_hat_rr_leakage_corrected_cp` | legacy alias: `gamma_hat_c_cp_eff` | supplementary corrected residual branch |
| `m3_leakage_lr_over_rr` | legacy local name: `eps_eff` | Stage 3 LR/RR leakage coefficient |
| `B(theta)` | same | worst-case linear benchmark `max(|R_TE|, |R_TM|)` |
| `G_supp_ideal` | same | ideal suppression gain vs `B(theta)` |
| `G_supp_patch_raw` | same | raw-primary patch suppression gain |
| `Delta_G` | same | ideal-minus-raw same-angle gap |

## Output Anchor

- Stage 2 internal alias tables:
  - `analysis_stages/paper_code_review_bundle_20260414/data/stage_2/sameflip_alias_20260415/`
- Stage 3a raw-primary alias export:
  - `analysis_stages/lp_anchor_branch_lock_20260414/results_sharedcommon_check_20260415/patch_cp_extracted_with_lp_anchor_alias.csv`

## Pass Conditions

- No manuscript-facing figure or table mixes paper symbols and internal alias
  names without a stated mapping.
- No manuscript headline uses `gamma_hat_rr_leakage_corrected_cp` as the primary patch
  residual.
