# Direct CP One-Point With References

Execution date: `2026-04-14`

Fixed point:

- material: `concrete`
- theta: `30 deg`
- frequency: `6.500 GHz`

## External Inputs

- LOS: `analysis_stages\specular_rx_direct_cp_reanalysis_20260414\LOS_SPECULAR_RX.csv`
- M3: `analysis_stages\specular_rx_direct_cp_reanalysis_20260414\M3_SPECULAR_RX.csv`
- PEC: `analysis_stages\specular_rx_direct_cp_reanalysis_20260414\PEC_SPECULAR_RX.csv`
- CONCRETE: `analysis_stages\specular_rx_direct_cp_reanalysis_20260414\CONCRETE_SPECULAR_RX.csv`

## Direct Patch-Style Reconstruction

- Gamma_dominant_direct: `0.428326 @ -14.42 deg`
- Gamma_residual_raw_direct: `0.122596 @ -164.76 deg`
- Gamma_residual_eff_direct: `0.138900 @ -16.36 deg`
- eps_eff_from_M3: `0.587543 @ -167.15 deg`

## Ideal CP Reference At The Same Point

- same-hand ideal branch (`Gamma_same`): `0.036817 @ 170.76 deg`
- flipped-hand ideal branch (`Gamma_flip`): `0.396386 @ 175.29 deg`

## Stage 3 Locked Reference At The Same Point

- `gamma_hat_x_cp_sys_mag`: `0.428809`
- `gamma_hat_c_cp_raw_mag`: `0.168656`
- `gamma_hat_c_cp_eff_mag`: `0.043992`

## Agreement

- direct dominant vs Stage 3 `gamma_hat_x_cp_sys` magnitude diff: `0.000483`
- direct residual raw vs Stage 3 `gamma_hat_c_cp_raw` magnitude diff: `0.046060`
- direct residual eff vs Stage 3 `gamma_hat_c_cp_eff` magnitude diff: `0.094909`

This one-point sanity therefore validates the Stage 3 patch-style normalization path itself.

## What It Does And Does Not Prove

- proves:
  - the provided LOS/M3/PEC/CONCRETE files are in the same convention needed to reconstruct the Stage 3 patch metrics
  - the direct one-point patch-style reconstruction reproduces the locked Stage 3 values closely
- does not yet prove:
  - that the direct one-point normalized patch metric must match the ideal plane-wave same/flip truth in absolute magnitude
  - that `eff` is more physical than `raw`

## Interpretation

- direct one-point sanity is now closed for convention and implementation consistency
- it supports the statement that the current `raw` and `eff` numbers are not file-format accidents
- the remaining question is the correction-model validity of `eff`, not the existence of the patch-style normalization itself

## Outputs

- normalized direct one-point: `analysis_stages\paper_code_review_bundle_20260414\code\direct_cp_one_point_sanity_20260414\results_sameflip_label_probe_20260415\direct_cp_one_point_normalized.csv`
- comparison table: `analysis_stages\paper_code_review_bundle_20260414\code\direct_cp_one_point_sanity_20260414\results_sameflip_label_probe_20260415\direct_cp_one_point_comparison.csv`
- source channels: `analysis_stages\paper_code_review_bundle_20260414\code\direct_cp_one_point_sanity_20260414\results_sameflip_label_probe_20260415\direct_cp_reference_channels.csv`
- PEC-normalized channels: `analysis_stages\paper_code_review_bundle_20260414\code\direct_cp_one_point_sanity_20260414\results_sameflip_label_probe_20260415\direct_cp_one_point_pec_normalized_channels.csv`
