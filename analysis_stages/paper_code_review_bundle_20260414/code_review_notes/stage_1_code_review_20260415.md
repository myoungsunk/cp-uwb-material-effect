# Stage 1 Code Review (2026-04-15)

Scope:
- `analysis_stages/paper_code_review_bundle_20260414/code/stage_1_build_truth_table.py`
- `analysis_stages/paper_code_review_bundle_20260414/code/stage_1_incident_field.py`
- `analysis_stages/paper_code_review_bundle_20260414/code/stage_1_geometry.py`
- `analysis_stages/paper_code_review_bundle_20260414/code/stage_1_estimator.py`

## Verdict

The phase-path concern is real, but only one part of it is currently active as a paper-risk.

- `incident_phase_deg` is **not** the active culprit in the authoritative run.
- `source_origin_offset_along_incident_m` is a **real phase-reference knob**, but it behaves as a common incident-phase reference, not as a TE/TM differential term by itself.
- `apply_pec_phase_lock()` is the **strongest active Stage 1 risk**, because it rotates TE and TM independently and therefore changes the relative phase that later feeds the CP transform.
- The already-observed practical `cp cal > ideal` problem is still primarily a **Stage 3 corrected-residual over-correction** problem, not a Stage 1-only bug.

## 1. Manifest legacy phase offset: structurally possible, currently inactive

Reference:
- `stage_1_build_truth_table.py:708-715`

Implemented path:
- `incident_phase_deg` is read from the manifest.
- The analytic incident field is multiplied by `exp(j * incident_phase_deg)`.

Code fact:
- This knob exists and is additive with the geometry-based source-origin reference.

Current status:
- The active manifest is already `phase0_nominal`.
- A forced-zero rerun was hash-identical to the nominal Stage 1 rerun.
- Therefore, a leftover legacy `+90 deg` offset is **not** active in the current authoritative run.

Conclusion:
- Keep this as a structural risk, but not as the present explanation for the current results.

## 2. Geometry source-origin offset: real phase knob, but common-phase only

Reference:
- `stage_1_geometry.py:238-247`
- `stage_1_incident_field.py:31-42`
- active geometry file: `ideal_te_tm_scattered_stage/config/geometry_material_5000mm_kobs5.yaml`

Implemented path:
- `source_origin(theta) = source_origin_m + source_origin_offset_along_incident_m * incident_hat(theta)`
- active config uses `source_origin_offset_along_incident_m: -0.1`

Interpretation:
- Because the offset is applied along `incident_hat`, the analytic incident field gets one global phase shift per row.
- That shift is common to the incident field and enters the coefficient only through the incident amplitude estimate.

Assessment:
- This is a legitimate phase-reference choice.
- It is not, by itself, a TE/TM relative-phase injector.
- It only becomes dangerous if it is tuned together with another external phase knob and later "fixed again" by PEC locking.

Conclusion:
- This is part of the overall phase-reference stack, but not the strongest active bug candidate.

## 3. Strongest active Stage 1 risk: independent TE/TM PEC phase lock

Reference:
- `stage_1_build_truth_table.py:1078-1080`
- `stage_1_build_truth_table.py:1141-1142`

Implemented logic:
- `lock["TE"] = target_TE * exp(-j * angle(R_TE_pec))`
- `lock["TM"] = target_TM * exp(-j * angle(R_TM_pec))`
- The code then multiplies **all** rows by those separate TE/TM locks.

Why this is risky:
- The CP transform depends directly on the relative phase between `R_TE` and `R_TM`.
- A polarization-specific PEC lock is not a common phase correction; it can inject differential phase.

Measured effect:
- Stage 1 phase-lock audit already confirmed:
  - main-claim rows: `mean(|delta_dphi|) = 1.5135 deg`
  - main-claim rows: `max(|delta_dphi|) = 3.8956 deg @ 60 deg`
  - overall rows: `max(|delta_dphi|) = 4.8422 deg @ 65 deg`
  - cross-material span at fixed `theta`: essentially zero

Interpretation:
- This is a real theta-dependent differential phase injection created by the lock structure itself.
- It is not a material-specific physics effect.

Conclusion:
- If one Stage 1 mechanism must be treated as the primary active code risk, it is `apply_pec_phase_lock()`.

## 4. Why the estimator makes a common lock plausible, but not a polarization-specific lock

Reference:
- `stage_1_estimator.py:39-43`
- `stage_1_build_truth_table.py:766-767`
- `stage_1_build_truth_table.py:907-908`

Implemented path:
- `matched_plane_wave_estimator()` uses `center = points.mean(axis=0)`.
- Reflection/transmission coefficients are then formed as:
  - `R = observation_amplitude / incident_amplitude`
  - `T = observation_amplitude / incident_amplitude`

Interpretation:
- This leaves any absolute observation-plane phase reference inside the raw complex coefficient.
- A later **common** phase alignment to a PEC anchor is therefore understandable.

Problem:
- The current lock is not common; it is TE-specific and TM-specific.
- That means it corrects more than a plane-reference mismatch. It also modifies the quantity that the CP transform is physically sensitive to.

Conclusion:
- The estimator design supports a shared phase-reference correction.
- It does **not** justify an unconstrained independent TE/TM phase lock if the downstream observable is CP branch separation.

## 5. Practical `cp cal > ideal`: mostly not a Stage 1-only bug

Reference:
- downstream Stage 4 audits already locked in the bundle

What is already known:
- Same-angle audit: corrected residual branch produced negative-gap rows in `16 / 23`.
- Raw residual branch produced negative-gap rows in `0 / 23`.

Interpretation:
- The practical `Gamma_C_eff` issue is already independently diagnosed as oblique-angle over-correction in Stage 3.
- Therefore, seeing `cp cal > ideal` in a practical comparison should **not** be assigned to Stage 1 first.

Conclusion:
- Stage 1 differential phase injection is real and should be tracked.
- But the paper-safe reporting rule still remains:
  - use `raw-primary`
  - keep corrected residual supplementary

## Paper-safe conclusion

1. There is no evidence that a leftover manifest `+90 deg` phase is still active.
2. There is clear evidence that Stage 1 PEC locking injects a small but real TE/TM differential phase.
3. The strongest immediate mitigation is not to trust corrected CP residual as the headline metric.
4. The longer-term Stage 1 fix candidate is a shared PEC-reference complex estimator or shared-phase PEC alignment, not the current polarization-by-polarization lock.
