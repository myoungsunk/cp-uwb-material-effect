# CP Metal-Floor Cross-Check Debug

## Purpose

Check whether the same-angle sign failure seen with

- `gamma_hat_c_cp_eff`

is specific to the effective correction layer, by re-running the CP patch
branch using the legacy metal-floor normalization.

## Result

The metal-floor cross-check removed the same-angle sign flip:

- negative same-angle rows:
  - `0 / 23`

That means the Stage 4c sign problem is not a general CP patch issue. It is
specific to the corrected residual branch.

## Important Limitation

The metal-floor branch is not directly the same observable as the ideal
residual branch because it is normalized to the metal response:

- `Gamma_C_metal_floor = h_tilde_RR(material) / h_tilde_RR(metal)`

So it should be used as:

- a diagnostic cross-check

not as:

- a drop-in replacement for the paper headline suppression metric

## Output References

- workspace:
  - `analysis_stages/stage4d_cp_metal_floor_audit_20260414`
- summary:
  - `analysis_stages/stage4d_cp_metal_floor_audit_20260414/results/STAGE4D_CP_METAL_FLOOR_AUDIT.md`
