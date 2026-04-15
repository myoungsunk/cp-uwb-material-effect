# Patch CP Effective Residual Over-Correction Debug Log

## Goal

Determine whether the post-alias Stage 4b same-angle gap behaves like a valid
ideal-versus-practical loss metric.

## Audit Result

The same-angle gap audit showed:

- with corrected residual `gamma_hat_c_cp_eff`:
  - negative `Delta_G` rows = `16 / 23`
- with raw residual `gamma_hat_c_cp_raw`:
  - negative `Delta_G` rows = `0 / 23`

So the failure is not caused by the LP-anchor branch alias. It appears only
after the effective correction step is applied.

## Material Breakdown

- concrete:
  - corrected negative rows = `5 / 8`
  - raw negative rows = `0 / 8`
- glass:
  - corrected negative rows = `6 / 9`
  - raw negative rows = `0 / 9`
- wood:
  - corrected negative rows = `5 / 6`
  - raw negative rows = `0 / 6`

## Strongest Evidence

Representative corrected negative-gap rows:

- concrete `40 deg`:
  - ideal residual = `0.089012`
  - raw patch residual = `0.194366`
  - corrected patch residual = `0.033411`
  - `Delta_G_raw = +6.78 dB`
  - `Delta_G_eff = -8.51 dB`
- glass `45 deg`:
  - ideal residual = `0.147371`
  - raw patch residual = `0.235215`
  - corrected patch residual = `0.052116`
  - `Delta_G_raw = +4.06 dB`
  - `Delta_G_eff = -9.03 dB`
- wood `35 deg`:
  - ideal residual = `0.067121`
  - raw patch residual = `0.106783`
  - corrected patch residual = `0.021751`
  - `Delta_G_raw = +4.03 dB`
  - `Delta_G_eff = -9.79 dB`

## Interpretation

The current evidence supports this ranking:

1. branch aliasing issue:
   - resolved by LP-anchor lock
2. low-angle artifact issue:
   - reduced by Stage 4b oblique filter
3. corrected residual over-suppression issue:
   - still active

The next technical question is therefore not
"which branch is residual?" but rather
"what physical quantity does `gamma_hat_c_cp_eff` represent after correction?"

## Output References

- audit workspace:
  - `analysis_stages/stage4c_same_angle_gap_audit_20260414`
- audit summary:
  - `analysis_stages/stage4c_same_angle_gap_audit_20260414/results/STAGE4C_SAME_ANGLE_GAP_AUDIT.md`
- full audit csv:
  - `analysis_stages/stage4c_same_angle_gap_audit_20260414/results/same_angle_gap_audit_full.csv`
- metal-floor cross-check:
  - `analysis_stages/stage4d_cp_metal_floor_audit_20260414/results/STAGE4D_CP_METAL_FLOOR_AUDIT.md`

## Metal-Floor Cross-Check

The legacy metal-floor CP ratio was also re-run as a diagnostic control.

Result:

- negative same-angle rows with metal-floor branch:
  - `0 / 23`

This strengthens the conclusion that the current sign failure is introduced by
the effective correction layer itself, not by the raw CP patch response in
general.

## Practical Consequence

For the moment:

- do not present `Delta_G` as a clean antenna-loss band
- do not use peak-to-peak ideal versus patch ordering as a headline
- keep direct CP one-point sanity as a high-priority supplement check
