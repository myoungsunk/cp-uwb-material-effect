# Direct CP Sanity Check File Note

## Source

- external file:
  - `E:\0. CP Antenna\0. TRACK2_3_SIM\ANTENNA_SOURCE\csv\sending\sanity check.csv`

## Fixed Point

- material: `concrete`
- theta: `30 deg`
- frequency: `6.5 GHz`

## Extracted CP Matrix

From the single row in the file:

- `S(RX_LH, TX_LH) = 0.0042599413 ∠ 48.2534 deg`
- `S(RX_LH, TX_RH) = 0.0008430962 ∠ 47.7733 deg`
- `S(RX_RH, TX_LH) = 0.0008430497 ∠ 47.7822 deg`
- `S(RX_RH, TX_RH) = 0.0043383149 ∠ -132.0568 deg`

## Immediate Interpretation

Branch ordering is clear:

- smaller branches:
  - `LR`
  - `RL`
- larger branches:
  - `LL`
  - `RR`

So for this direct sanity point:

- if `TX = RHCP`, then `RX = LHCP` is the smaller branch and `RX = RHCP` is the larger branch
- if `TX = LHCP`, then `RX = RHCP` is the smaller branch and `RX = LHCP` is the larger branch

## Important Limitation

This file is directly usable for:

- handedness / co-cross branch ordering
- reciprocity symmetry check at one point

This file is not yet directly usable for:

- absolute magnitude comparison against Stage 2 ideal `Gamma_X / Gamma_C`
- raw-vs-eff correction validation

because the exported S-parameters are not normalized to the same reflection
coefficient convention used by the Stage 2/3 locked tables.

## Saved Conversion Files

- RHCP transmit subset:
  - `analysis_stages/direct_cp_one_point_sanity_20260414/data/direct_cp_measurement_from_sanity_check_rhcp.csv`
- LHCP transmit subset:
  - `analysis_stages/direct_cp_one_point_sanity_20260414/data/direct_cp_measurement_from_sanity_check_lhcp.csv`
