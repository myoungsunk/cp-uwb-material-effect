# Patch CP Stage System

This folder isolates the current patch-inclusive CP analysis pipeline.

## Scope

- Uses the measured/simulated patch-CP `M1`, `M2`, and `M3` CSV inputs
- Produces patch-CP stage system metrics such as:
  - `Gamma_X`
  - first-order corrected `Gamma_C`
  - derived TE/TM proxies

## Non-Scope

- Ideal plane-wave excitation
- Material-only / intrinsic TE/TM extraction
- Final slab-truth calibration without patch effects

## Main Script

- `gamma_extraction_v2.py`
