# Stage 5. Odd-Bounce Extension Writing

## Current Status

- This stage is writing-only.
- No new simulation or extraction is required here.

## Purpose

- Extend the verified single-bounce result to an odd-bounce interpretation
  without overclaiming.

## Inputs

- Locked Stage 4 suppression results
- Locked Stage 0 notation
- Methods and limitations already established in Stages 1 to 4

## Execution

1. State exactly what has been validated:
   - single-bounce specular reflection
   - locally planar interface
   - CP co-pol residual suppression
2. State the extension logic only as a parity-based mechanism under the same
   local specular assumptions.
3. State exclusions explicitly:
   - rough surfaces
   - edge diffraction
   - grazing-limit behavior
   - strongly dispersive multilayer cases outside the current lock

## Outputs

- One discussion paragraph for the manuscript.
- Executed draft:
  - `analysis_stages/stage5_odd_bounce_extension_20260414/results/STAGE5_ODD_BOUNCE_EXTENSION.md`

## Pass Conditions

- The paragraph does not imply that multi-bounce environments were directly
  simulated or measured in this repository.
- The claim remains conditional on local specular TE/TM recombination.

## Next Stage Link

- Stage 6 adds the frequency-sensitivity support note.

## Locked Paragraph

The result validated in this work is the suppression of the CP co-polar
residual for a single specular reflection from a locally planar interface in
the oblique-incidence regime covered by the present lock. The extension to
odd-bounce propagation should therefore be read as a parity-based first-order
interpretation rather than as a separate full-wave validation of arbitrary
multi-bounce environments. When each interaction can still be approximated as
locally planar and specular, the reflected field remains governed by TE/TM
component-wise recombination, so the same handedness-parity mechanism that
suppresses the single-bounce residual remains the relevant path-level picture
for an odd number of reflections. This paper does not claim that the same
suppression survives unchanged in rough-surface, edge-dominated, grazing-limit,
or strongly dispersive multilayer environments, where non-specular scattering,
diffraction, and angle-dependent system effects can dominate.

## Current Interpretation Lock

- `ideal`: material-limited upper reference
- `raw`: conservative system lower layer
- `LP-derived`: practical estimate closest to the ideal trend
- `eff` and PEC-based CP correction: supplementary only, not safe headline
  layers
