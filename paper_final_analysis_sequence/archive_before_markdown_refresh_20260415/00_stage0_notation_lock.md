# Stage 0. Notation Lock

## Current Status

- This file is the paper-wide notation lock draft.
- It should be treated as the reference for figure captions, table headers,
  and method text unless a later manuscript-specific revision explicitly
  overrides it.

## Purpose

- Freeze one notation system for the full paper.
- Prevent mixed use of ideal/material truth symbols and patch/system symbols.

## Inputs

- Existing stage code and outputs under `analysis_stages/`.
- Current diagnosis notes:
  - `analysis_stages/ideal_te_tm_scattered_stage/data/material_cp_valid_range_diagnosis_20260413.md`
  - `analysis_stages/ideal_te_tm_scattered_stage/data/pec_observation_setup_diagnosis_20260413.md`

## Execution

1. Use a local basis tied to the reflecting wall:
   - `n_hat`: wall normal
   - plane of incidence: defined by incident and reflected rays
   - `TE`: perpendicular to plane of incidence
   - `TM`: parallel to plane of incidence
2. Reserve ideal/material truth for interface-level coefficients:
   - `R_TE(f, theta_i)`
   - `R_TM(f, theta_i)`
3. Reserve CP quantities derived from the linear truth basis transform for:
   - `Gamma_X = (R_TE + R_TM) / 2`
   - `Gamma_C = (R_TE - R_TM) / 2`
4. Reserve patch/system quantities for practical extracted responses:
   - `Gamma_hat_X_CP_sys`
   - `Gamma_hat_C_CP_eff`
   - `R_hat_yy_sys`
   - `R_hat_zz_sys`
   - optional leakage monitors:
     - `R_hat_yz_sys`
     - `R_hat_zy_sys`
5. Keep terminology locked:
   - `ground truth`: Fresnel or ideal TE/TM only
   - `calibration / consistency reference`: LP metal or PEC patch reference
   - `upper bound`: ideal CP derived from linear truth
   - `effective / antenna-limited`: patch CP co-term quantity

## Outputs

- This file itself as the notation lock.
- All downstream report files in this folder should follow the same symbols.

## Pass Conditions

- Variable names in active scripts can be mapped one-to-one to the locked paper
  notation.
- No figure or table caption mixes `ground truth` with patch-stage outputs.

## Next Stage Link

- Stage 1 uses this lock when naming the ideal TE/TM truth table and its
  Fresnel comparison.

## Locked Symbol Map

| Paper symbol | Meaning | Repository anchor |
| --- | --- | --- |
| `R_TE`, `R_TM` | Ideal complex reflection coefficients in the local linear basis | `truth_table_linear_locked.csv` |
| `Gamma_X`, `Gamma_C` | CP-basis transform of ideal TE/TM truth | `truth_table_cp.csv` |
| `Gamma_hat_X_CP_sys` | Patch CP system co-term | Stage 3 target CSV |
| `Gamma_hat_C_CP_eff` | Patch CP effective cross-term upper bound | Stage 3 target CSV |
| `R_hat_yy_sys`, `R_hat_zz_sys` | LP patch co-pol system responses | Stage 3 target CSV |
| `B(theta)` | Worst-case linear benchmark `max(|R_TE|, |R_TM|)` | Stage 4 target CSV |
| `G_supp_ideal` | Ideal suppression gain relative to `B(theta)` | Stage 4 target CSV |
| `G_supp_patch` | Patch suppression gain relative to `B(theta)` | Stage 4 target CSV |
| `Delta_G` | Antenna-limited suppression gap | Stage 4 target CSV |
