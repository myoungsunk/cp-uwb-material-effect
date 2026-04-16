# Stage Pipeline And Overcorrection Summary

Date: `2026-04-14`

Scope:
- This note consolidates the stage-by-stage paper pipeline status.
- It also consolidates the code-entry map and the full over-correction analysis history up to Stage 4l.
- The goal is to give one stable audit document inside `paper_code_review_bundle_20260414/`.

---

## 1. Bundle layout

This bundle is organized as:

- `code/`
  - centralized executable or review-wrapper scripts
- `data/`
  - stage-wise CSV and note outputs
- `code_manifest.csv`
  - source-to-bundle mapping for code
- `data_manifest.csv`
  - source-to-bundle mapping for data

Recommended reading order inside this bundle:

1. `README.md`
2. `code_manifest.csv`
3. `data_manifest.csv`
4. this summary note

---

## 2. Executive conclusion

Current paper-safe position is:

- `ideal` remains the material-only upper bound.
- `raw` remains the primary practical metric.
- current `eff` correction is supplementary only.
- `alpha/beta`-style kernels are physically promising, but not yet stable enough to replace `raw`.

The reason `eff` is not primary is no longer speculative:

- low angle: floor-dominated
- high angle: subtraction-dominated
- LoS proxy `eps_eff = h3_LR / h3_RR` does not match the actual reflective leakage embedded in `gamma_c_raw`

The best concise statement is:

`raw` is the headline system metric, `ideal` is the material limit, and `eff` is an exploratory de-leakage series with an explicit instability caveat.

---

## 3. Stage-by-stage status

| Stage | Goal | Main code | Current status |
|---|---|---|---|
| Stage 0 | notation lock | document-only | completed conceptually |
| Stage 1 | ideal TE/TM truth | `stage_1_*` | completed, rerun matches old lock exactly |
| Stage 2 | ideal CP transform | `stage_2_cp_transform.py` | completed, numerically safe |
| Stage 3 | patch CP/LP extraction | `stage_3_*` | completed, but CP `eff` interpretation limited |
| Stage 4 | suppression and audits | `stage_4_*` | completed through multiple substages |
| Stage 5 | odd-bounce wording | document-level | prepared in analysis flow |
| Stage 6 | UWB sensitivity | `stage_6_build_uwb_dispersion_sensitivity.py` | completed |
| Stage 7 | paper figure/table export | `stage_7_build_paper_figures_1_4.py` | completed |

---

## 4. Stage 1 summary

Main purpose:
- lock ideal TE/TM truth
- verify against Fresnel
- confirm Stage 1 code fixes do not change locked outputs

Important result:
- after Stage 1 code hardening, rerun outputs were identical to the previous locked outputs
- compared files were hash-identical and numerically identical

Relevant code:
- `code/stage_1_build_truth_table.py`
- `code/stage_1_projection.py`
- `code/stage_1_qc.py`
- `code/stage_1_sanity_check_fresnel.py`
- `code/stage_1_te_tm_extraction_ideal_plane_wave.py`

Important conclusion:
- Stage 1 truth is stable
- later issues are not coming from Stage 1 truth generation

---

## 5. Stage 2 summary

Main purpose:
- derive ideal CP truth from Stage 1 linear truth

Transform:
- `Gamma_X = 0.5 * (R_TE + R_TM)`
- `Gamma_C = 0.5 * (R_TE - R_TM)`

Relevant code:
- `code/stage_2_cp_transform.py`

Important conclusion:
- Stage 2 is numerically clean
- no sqrt branch, no leakage correction, no calibration instability
- Stage 2 is not the origin of the later mismatch

---

## 6. Stage 3 summary

Main purpose:
- extract patch CP and LP quantities
- align them to the ideal angle grid
- use LP direct as anchor

Relevant code:
- `code/stage_3_cp_patch_extraction.py`
- `code/stage_3_export_cp_patch_stage3.py`
- `code/stage_3_lp_patch_extraction.py`
- `code/stage_3_export_lp_patch_stage3.py`
- `code/stage_3_verify_lp_anchor_branch_lock.py`
- `code/stage_3_build_metal_leakage_proxy_audit.py`

Key Stage 3 finding:
- branch naming mismatch existed in patch CP
- ideal and LP-derived paths agreed
- patch CP labels were effectively swapped relative to ideal convention

Locked convention:
- residual branch = `gamma_hat_c_cp_eff`
- dominant branch = `gamma_hat_x_cp_sys`

Why LP mattered:
- LP direct does not use the `eps_eff` correction
- LP direct does not use the CP geometric-mean branch selection
- LP direct therefore served as the cleaner branch-lock anchor

---

## 7. Stage 4 substage summary

### Stage 4a

Purpose:
- initial suppression table using the small-branch rule

Current interpretation:
- preserved for audit trail only
- not the final convention-locked version

### Stage 4b

Purpose:
- convention-locked suppression rerun after branch naming was fixed

Main result:
- fixed the branch interpretation issue
- removed the low-angle headline inflation by moving to the oblique reporting frame

### Stage 4c

Purpose:
- same-angle upper-bound audit

Main result:
- `raw` preserved the expected ideal >= practical ordering
- `eff` broke that ordering in multiple rows

This is the first hard sign that `eff` is over-correcting.

### Stage 4d

Purpose:
- metal-floor audit

Main result:
- low-angle discrepancy is floor-driven
- PEC/metal residual floor is about `0.15-0.25` in magnitude
- this is about `-17 dB` to `-12 dB`

Interpretation:
- near normal incidence, ideal residual goes below the hardware floor
- neither `raw` nor `eff` can recover ideal there

### Stage 4e / 4f

Purpose:
- three-way comparison
- raw-primary reporting

Main result:
- `raw` is the most defensible practical metric
- `eff` and metal-floor normalized variants are useful only as supplementary checks

### Stage 4g

Purpose:
- audit the mechanism of `eff` over-correction

Main result:
- correction term size is routinely comparable to the whole raw residual
- even modest phase mismatch can drive subtraction past zero

### Stage 4h

Purpose:
- PEC-based CP correction test

Main result:
- PEC-based correction also over-corrected
- this reinforced that the problem is structural, not just a sign typo in the current `eps_eff`

### Stage 4i

Purpose:
- summarize the physical framing of `eff` instability

Important note:
- `data/stage_4/stage4i_eff_instability_framing_20260414/STAGE4I_EFF_INSTABILITY_FRAMING.md`

### Stage 4j

Purpose:
- quantify the mismatch signature

Relevant code:
- `code/stage_4_build_eff_mismatch_signature.py`

Main results:
- LoS proxy mismatch against actual metal leakage is about `3-5 dB` in magnitude
- phase drift is about `12-20 deg`
- fitted effective offset is about `-1.10 mm`

Interpretation:
- phase drift is consistent with a small effective path-center mismatch
- the proxy mismatch is not random noise

### Stage 4k

Purpose:
- test `alpha/beta`-style proxy decomposition

Relevant code:
- `code/stage_4_build_alpha_beta_proxy_test.py`

Tested proxies:
- current `eps_lr_rr = h3_LR / h3_RR`
- alternate `eps_rl_ll = h3_RL / h3_LL`
- `alpha + conj(beta)` no-phase
- `alpha + conj(beta) * exp(-2j k d_eff cos(theta))` phase-fit kernel

Main result:
- `eps_rl_ll` fixes magnitude bias but leaves about `90 deg` phase error
- `alpha/beta` kernels improve on current `eff`
- phase-fit `alpha/beta` reduces worst over-correction substantially
- but negative-gap rows still remain

Conclusion:
- physically promising
- not yet strong enough to replace `raw` as primary

### Stage 4l

Purpose:
- test Brewster-vicinity sensitivity
- test `d_eff(f)` stability

Relevant code:
- `code/stage_4_build_brewster_deff_checks.py`

Main results:
- excluding Brewster-vicinity rows does not remove the concrete main-range issue
- therefore concrete over-correction is not mainly a Brewster artifact
- `d_eff(f)` stays broadly mm-scale across the band
- mean about `-1.11 mm`, std about `0.23 mm`
- band edge fit quality degrades, so the phase-center interpretation is good but not perfect

---

## 8. Over-correction mechanism: final synthesis

Current correction:

- `gamma_c_eff = gamma_c_raw - eps_eff * gamma_x`
- with `eps_eff = h3_LR / h3_RR`

This is unstable for two separate reasons.

### 8.1 Low angle

Problem:
- ideal residual approaches zero
- measured system residual hits the antenna floor first

Meaning:
- low-angle disagreement is floor-dominated
- not a meaningful correction-quality region

### 8.2 High angle

Problem:
- correction term is large relative to the residual of interest
- proxy mismatch remains in both magnitude and phase

Typical oblique scale:
- `|gamma_x| ~ 0.4`
- `|eps_eff| ~ 0.4`
- correction size `|eps_eff * gamma_x| ~ 0.16`
- target residual `|Gamma_X| ~ 0.05-0.10`

Meaning:
- the correction term is already larger than the target residual
- a small phase or magnitude mismatch is enough to over-cancel

Observed mismatch:
- magnitude bias about `3-5 dB`
- phase drift about `12-20 deg`

This is why `eff` can become smaller than ideal.

---

## 9. Paper-safe framing

Recommended hierarchy:

1. `ideal`
   - plane-wave material-only limit
2. `raw`
   - primary practical metric
3. `eff`
   - supplementary de-leakage attempt only
4. `alpha/beta`
   - exploratory future-improvement direction

Recommended language:

- the practical headline claim should be based on `raw`
- the current `eff` series should be shown only with an instability caveat
- the hardware floor should be visible in the figure
- the high-angle de-leakage uncertainty should be described as coherence-limited subtraction, not as a simple coding bug

---

## 10. Reproducible code map

If only the bundle `code/` folder is used, the main audit scripts are:

- Stage 3 metal leakage audit
  - `python code/stage_3_build_metal_leakage_proxy_audit.py`
- Stage 4j mismatch signature
  - `python code/stage_4_build_eff_mismatch_signature.py`
- Stage 4k alpha/beta proxy test
  - `python code/stage_4_build_alpha_beta_proxy_test.py`
- Stage 4l Brewster and `d_eff(f)` checks
  - `python code/stage_4_build_brewster_deff_checks.py`

These scripts regenerate the corresponding outputs in the original stage folders under `analysis_stages/`.

---

## 11. Important outputs to inspect first

Core interpretation notes:

- `data/stage_4/stage4i_eff_instability_framing_20260414/STAGE4I_EFF_INSTABILITY_FRAMING.md`
- `data/stage_4/stage4j_eff_mismatch_signature_20260414/STAGE4J_EFF_MISMATCH_SIGNATURE.md`
- `data/stage_4/stage4k_alpha_beta_proxy_test_20260414/STAGE4K_ALPHA_BETA_PROXY_TEST.md`
- `data/stage_4/stage4l_brewster_deff_checks_20260414/STAGE4L_BREWSTER_DEFF_CHECKS.md`

Core CSV tables:

- `data/stage_3/metal_leakage_proxy_audit_20260414/metal_leakage_proxy_vs_actual_summary.csv`
- `data/stage_4/stage4j_eff_mismatch_signature_20260414/phase_drift_cos_theta_fit.csv`
- `data/stage_4/stage4k_alpha_beta_proxy_test_20260414/material_proxy_vs_ideal_summary.csv`
- `data/stage_4/stage4k_alpha_beta_proxy_test_20260414/material_proxy_phasefit_vs_ideal_summary.csv`
- `data/stage_4/stage4l_brewster_deff_checks_20260414/deff_frequency_summary.csv`

---

## 12. Final status

What is closed:

- Stage 1 truth stability
- Stage 2 transform correctness
- branch naming lock
- raw-primary decision
- `eff` over-correction as a real structural issue

What is not closed:

- a fully reliable CP de-leakage correction that can replace `raw`

Current best next-step, if correction research continues:

- improve the `alpha/beta` kernel beyond the current first-order approximation
- keep the paper headline on `raw`

