# Stage 2-3 Code Audit (2026-04-14)

Scope:
- Stage 2 ideal CP transform: `analysis_stages/ideal_te_tm_scattered_stage/code/cp_transform.py`
- Stage 3 CP patch extraction: `analysis_stages/stage3_patch_paper_final_20260414/cp/code/gamma_extraction_v2.py`
- Stage 3 LP patch extraction / cross-check: `analysis_stages/stage3_patch_paper_final_20260414/lp/code/gamma_extraction_lp.py`

## Verdict

Stage 2 is numerically clean. The active code risk is concentrated in Stage 3, specifically:
- the `eps_eff = h3["LR"] / h3["RR"]` leakage model,
- the `anchored_geometric_mean(...)` phase-anchor logic,
- and the unverified assumption that `h_tilde = h2 - m1` isolates reflection without changing direct coupling.

## 1. Stage 2 status: no active bug found

Reference:
- `cp_transform.py:126-131`

Implemented transform:
- `Gamma_X = 0.5 * (R_TE + R_TM)`
- `Gamma_C = 0.5 * (R_TE - R_TM)`

Assessment:
- This is a direct linear basis transform on locked TE/TM truth.
- No square root, branch cut, or estimator calibration appears in Stage 2.
- The code itself is not the source of the later branch-mapping or over-correction problems.

Conclusion:
- Stage 2 is safe as written.

## 2. Stage 3 confirmed issue: M3-based `eps_eff` is not reflection-case leakage

Reference:
- `gamma_extraction_v2.py:140-147`
- `gamma_extraction_v2.py:216-219`
- same reuse in `gamma_extraction_lp.py:293-295`

Implemented model:
- `eps_eff = h3["LR"] / h3["RR"]`
- `Gamma_C_corr = Gamma_C_raw - eps_eff * Gamma_X`

What was checked:
- Compared M3-derived `eps_eff` against metal-derived leakage
- `eps_eff_metal = Gamma_C_raw_metal / Gamma_X_metal`
- evaluated from the existing Stage 3 CP CSV inputs

Observed mismatch:
- 30 deg: magnitude offset = `-4.07 dB`, mean phase offset = `11.74 deg`
- 10-56 deg main/caution region: magnitude offset ranges about `-3.15` to `-8.52 dB`
- 10-56 deg main/caution region: mean phase offset ranges about `11` to `23 deg`

Interpretation:
- The free-space M3 leakage ratio is not the same complex coefficient as the reflection-path leakage embedded in `Gamma_C_raw`.
- This is consistent with the previously observed `eff` over-correction.

Conclusion:
- The user’s concern here is valid.
- `eps_eff` is not just a noisy estimate; it is a structurally different reference.

## 3. Stage 3 confirmed issue: current phase anchor is not phase-aligned to `Gamma_X`

Reference:
- `gamma_extraction_v2.py:66-78`
- `gamma_extraction_v2.py:190-191`
- same reuse in `gamma_extraction_lp.py:93-105` and `gamma_extraction_lp.py:290-291`

Implemented logic:
- `candidate = sqrt(|ratio|) * exp(j * angle(ratio) / 2)`
- `anchor_approx = h_tilde["LR"] / h3["RR"]`
- flip sign if `abs(angle(candidate / anchor_approx)) > pi/2`

Single-point check:
- case: `concrete / 30 deg / 6.5 GHz`
- `anchor phase = -91.17 deg`
- `sqrt candidate phase = -1.31 deg`
- phase delta = `89.85 deg`

Whole-dataset check:
- Across all materials and angles, post-flip `|angle(final / anchor)|` stays near `89.7-89.9 deg`
- p95 is also about `89.9 deg`

Interpretation:
- The current anchor is nearly in quadrature with the geometric-mean candidate.
- That means the code is not comparing two same-physics phase references.
- The sign-selection rule is therefore not physically anchored in the current channel convention.

Conclusion:
- The user’s suspicion about branch instability is valid.
- More strongly: the current anchor is systematically mis-phased, not just noisy near a few bins.

## 4. Stage 3 confirmed issue: correction term is often as large as or larger than raw residual

Reference:
- `gamma_extraction_v2.py:216-219`

Audited quantity:
- `|eps_eff * Gamma_X| / |Gamma_C_raw|`

Dataset-average result:
- concrete: mean `0.999`, fraction `> 1` = `0.390`
- glass: mean `1.036`, fraction `> 1` = `0.433`
- wood: mean `0.847`, fraction `> 1` = `0.330`
- metal: mean `1.736`, fraction `> 1` = `1.000`

Interpretation:
- The correction term is routinely comparable to the entire raw residual.
- In that regime, even a modest phase error in `eps_eff` or `Gamma_X` will flip subtraction into over-subtraction.

Conclusion:
- This supports the earlier Stage 4 observation that `eff` is structurally fragile.

## 5. Stage 3 partially closed issue: frequency-grid mismatch

Reference:
- `gamma_extraction_v2.py:81-104`
- `gamma_extraction_lp.py:112-180`

Checked directly:
- `m1`, `m3`, and all `m2_*` files use the same 501-point frequency grid
- max absolute difference = `0.0`

Conclusion:
- The silent elementwise frequency-misalignment bug is not present in the current dataset.

## 6. Stage 3 still-open assumption: `h_tilde = h2 - m1` isolates reflection

Reference:
- `gamma_extraction_v2.py:166-172`
- `gamma_extraction_lp.py:288`
- `gamma_extraction_lp.py:356`

What is true:
- The subtraction is implemented consistently.
- Frequency alignment is fine.

What is not checked in code:
- whether wall insertion changes the direct Tx-Rx coupling itself,
- whether geometry equality between M1 and M2 is exact,
- whether the subtraction leaves only specular reflection rather than `reflection + delta direct coupling`.

Conclusion:
- This remains a physical assumption, not a validated property of the implementation.
- It is not a proven bug, but it is still an exposed modeling assumption.

## 7. LP direct path is cleaner than CP-derived proxy path

Reference:
- `gamma_extraction_lp.py:345-369`

LP-direct logic:
- `R_TE = h_tilde["zz"] / h3["zz"]`
- `R_TM = h_tilde["yy"] / h3["yy"]`
- then `Gamma_X, Gamma_C = cp_from_te_tm(R_TE, R_TM)`

Assessment:
- LP direct does not use the `eps_eff` correction.
- LP direct does not use the geometric-mean branch selection.
- This is why LP worked well as the branch-lock anchor.

Conclusion:
- For Stage 3 cross-checking, LP direct should remain the cleaner reference path.

## Practical implication

Safe to keep:
- Stage 2 ideal CP truth
- Stage 3 LP direct cross-check
- Stage 4 raw-primary reporting

Unsafe to promote as primary without further fix:
- `Gamma_C_corr` / `cp cal` as an absolute residual
- any claim that relies on the current `eps_eff` subtraction being physically calibrated
- any complex-phase interpretation that depends on the current `anchored_geometric_mean` sign logic

## Recommended next fixes

1. Replace the current phase anchor with a convention-correct anchor, or explicitly include the missing fixed phase factor if the current channel definition implies a `±j` relation.
2. Add explicit frequency-grid assertions before any elementwise subtraction/division.
3. Add a metal-derived leakage path alongside M3-derived `eps_eff` and export both for comparison.
4. Keep `raw` primary and `eff` supplementary until a direct CP one-point sanity run confirms the complex convention.
