# Stage 1 Phase-Zero and PEC-Lock Audit (2026-04-14)

## Scope

- Confirm that the active Stage 1 manifest already uses `incident_phase_deg = 0` everywhere.
- Confirm that forcing `incident_phase_deg = 0` again does not change any Stage 1 outputs.
- Quantify whether the current PEC lock injects a TE/TM differential phase into `R_TE / R_TM`.

## Result

- Active manifest unique `incident_phase_deg`: [0.0]
- Active manifest nonzero row count: 0
- Forced-zero rerun hash-identical across tracked files: True
- Main-claim rows: `mean(|delta_dphi|) = 1.5135 deg`, `max(|delta_dphi|) = 3.8956 deg` at `theta = 60 deg`.
- Overall rows: `max(|delta_dphi|) = 4.8422 deg` at `theta = 65 deg`.
- Cross-material spread at a fixed theta: `max(span) = 0.000000 deg`.

## Interpretation

- Priority 1 is closed: the active manifest is already pure `phase0_nominal`, and forcing zero again does not change Stage 1 outputs.
- Priority 2 finds a real effect: the current PEC lock is not a pure common-phase rotation. It adds a small but systematic theta-dependent differential phase between TE and TM.
- Because the per-theta span across materials is effectively zero, the injected differential phase is a lock-structure effect, not a material-dependent phenomenon.
- Stage 4 patch comparison should therefore stay `raw-primary`; `Gamma_C_eff` remains supplementary because its correction already failed the same-angle upper-bound audit.
- A later replacement of the current observation/incident normalization by a PEC-reference complex LS estimator is still justified if the goal is to reduce lock-induced CP inflation risk.

## Representative Theta Summary

| theta_deg | row_count | material_count | delta_dphi_deg_mean | delta_dphi_deg_min | delta_dphi_deg_max | delta_dphi_deg_std | abs_delta_dphi_deg_max | delta_dphi_material_span_deg | delta_te_phase_deg_mean | delta_tm_phase_deg_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20.000000 | 4.000000 | 4.000000 | -0.551126 | -0.551126 | -0.551126 | 0.000000 | 0.551126 | 0.000000 | -59.291488 | -58.740362 |
| 30.000000 | 4.000000 | 4.000000 | 0.854106 | 0.854106 | 0.854106 | 0.000000 | 0.854106 | 0.000000 | -178.516890 | -179.370996 |
| 40.000000 | 4.000000 | 4.000000 | 1.200589 | 1.200589 | 1.200589 | 0.000000 | 1.200589 | 0.000000 | -43.826482 | -45.027072 |
| 50.000000 | 4.000000 | 4.000000 | 2.430453 | 2.430453 | 2.430453 | 0.000000 | 2.430453 | 0.000000 | 50.821607 | 48.391155 |
| 60.000000 | 4.000000 | 4.000000 | 3.895604 | 3.895604 | 3.895604 | 0.000000 | 3.895604 | 0.000000 | -174.819080 | -178.714684 |

## Audit Artifacts

- `data/stage_1/phase_lock_audit_20260414/manifest_incident_phase_summary.csv`
- `data/stage_1/phase_lock_audit_20260414/forced_zero_file_comparison.csv`
- `data/stage_1/phase_lock_audit_20260414/phase_lock_dphi_rowwise.csv`
- `data/stage_1/phase_lock_audit_20260414/phase_lock_dphi_theta_summary.csv`
- `data/stage_1/phase_lock_audit_20260414/phase_lock_audit_summary.json`
