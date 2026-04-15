# Direct CP One-Point With References

Execution date: `2026-04-14`

Fixed point:

- material: `concrete`
- theta: `30 deg`
- frequency: `6.500 GHz`

## External Inputs

- LOS: `E:\0. CP Antenna\0. TRACK2_3_SIM\ANTENNA_SOURCE\sending\sanity check_LOS.csv`
- M3: `E:\0. CP Antenna\0. TRACK2_3_SIM\ANTENNA_SOURCE\sending\sanity check_M3.csv`
- PEC: `E:\0. CP Antenna\0. TRACK2_3_SIM\ANTENNA_SOURCE\sending\sanity check_PEC.csv`
- CONCRETE: `E:\0. CP Antenna\0. TRACK2_3_SIM\ANTENNA_SOURCE\sending\sanity check_CONCRETE.csv`

## Direct Patch-Style Reconstruction

- Gamma_X_direct: `0.435082 @ -1.23 deg`
- Gamma_C_raw_direct: `0.172914 @ -165.11 deg`
- Gamma_C_eff_direct: `0.041597 @ -29.06 deg`
- eps_eff_from_M3: `0.470963 @ -171.98 deg`

## Stage 3 Locked Reference At The Same Point

- `gamma_hat_x_cp_sys_mag`: `0.428809`
- `gamma_hat_c_cp_raw_mag`: `0.168656`
- `gamma_hat_c_cp_eff_mag`: `0.043992`

## Agreement

- direct vs Stage 3 `Gamma_X` magnitude diff: `0.006272`
- direct vs Stage 3 `Gamma_C_raw` magnitude diff: `0.004258`
- direct vs Stage 3 `Gamma_C_eff` magnitude diff: `0.002394`

This one-point sanity therefore validates the Stage 3 patch-style normalization path itself.

## What It Does And Does Not Prove

- proves:
  - the provided LOS/M3/PEC/CONCRETE files are in the same convention needed to reconstruct the Stage 3 patch metrics
  - the direct one-point patch-style reconstruction reproduces the locked Stage 3 values closely
- does not yet prove:
  - that the direct one-point normalized patch metric must match the ideal plane-wave `Gamma_X/Gamma_C` truth in absolute magnitude
  - that `eff` is more physical than `raw`

## Interpretation

- direct one-point sanity is now closed for convention and implementation consistency
- it supports the statement that the current `raw` and `eff` numbers are not file-format accidents
- the remaining question is the correction-model validity of `eff`, not the existence of the patch-style normalization itself

## Outputs

- normalized direct one-point: `analysis_stages\direct_cp_one_point_sanity_20260414\results_aliasfree_20260415\with_references\direct_cp_one_point_normalized.csv`
- comparison table: `analysis_stages\direct_cp_one_point_sanity_20260414\results_aliasfree_20260415\with_references\direct_cp_one_point_comparison.csv`
- source channels: `analysis_stages\direct_cp_one_point_sanity_20260414\results_aliasfree_20260415\with_references\direct_cp_reference_channels.csv`
- PEC-normalized channels: `analysis_stages\direct_cp_one_point_sanity_20260414\results_aliasfree_20260415\with_references\direct_cp_one_point_pec_normalized_channels.csv`
