# Direct CP One-Point Run Spec

## Objective

Lock the CP handedness and branch convention at one explicit point, then use it
to decide whether the current Stage 3 patch labels should be renamed or only
aliased.

## Fixed Point

- material: `concrete`
- incidence angle: `30 deg`
- frequency: `6.5 GHz`

## Geometry Lock

Inherited from the locked Stage 2 geometry file:

- `observation_distance_lambda_scale = 5.0`
- `surface_normal_m = [0, 0, 1]`
- `reference_te_axis_m = [0, 1, 0]`
- `plane_of_incidence_axis_m = [1, 0, 0]`

The direct-CP point must reuse the same wall, source placement, observation
distance, and reflected observation setup as the locked ideal stage.

## HFSS Export Requirement

Use one explicit CP transmit state and export both reflected receive CP
branches at the fixed point.

Preferred labels:

- transmit: `RHCP`
- receive branches: `RHCP`, `LHCP`

Any equivalent handedness naming is acceptable if the labels are written
explicitly in the CSV.

## Required CSV Fields

Populate `data/direct_cp_measurement_template.csv` with exactly two rows for
the fixed point:

- `material`
- `theta_deg`
- `freq_ghz`
- `tx_cp`
- `rx_cp`
- either `coeff_real` and `coeff_imag`
- or `coeff_mag` and `coeff_phase_deg`

## Frozen Ideal Target At The Fixed Point

From Stage 2 ideal CP truth:

- `Gamma_X = -0.0365814292 + j0.0029613367`
- `|Gamma_X| = 0.0367010964`
- `phase(Gamma_X) = 175.371889 deg`
- `Gamma_C = -0.3950856264 + j0.0322195124`
- `|Gamma_C| = 0.3963972114`
- `phase(Gamma_C) = 175.337806 deg`

So the current ideal ordering is:

- small branch: `Gamma_X`
- large branch: `Gamma_C`

## Current Bridge Snapshot At The Same Point

From Stage 3 patch CP:

- `gamma_hat_c_cp_eff` magnitude: `0.0439916616`
- `gamma_hat_x_cp_sys` magnitude: `0.4288091857`

From Stage 3 LP bridge:

- `gamma_x_from_lp` magnitude: `0.0550778552`
- `gamma_c_from_lp` magnitude: `0.4512782020`

This is why the current working hypothesis is:

- patch small branch: `gamma_hat_c_cp_eff`
- patch large branch: `gamma_hat_x_cp_sys`

## Acceptance Rule

The direct-CP sanity is considered locked when all of the following hold:

1. The measured receive CP channels split cleanly into one smaller branch and
   one larger branch.
2. The smaller measured branch is closer in magnitude to ideal `Gamma_X` than
   to ideal `Gamma_C`.
3. The larger measured branch is closer in magnitude to ideal `Gamma_C` than
   to ideal `Gamma_X`.
4. The smaller measured branch corresponds uniquely to one current Stage 3
   patch branch.
5. The LP bridge ordering stays consistent with the same assignment.

Phase should be reported, but branch locking should rely first on ordering and
magnitude correspondence because global handedness sign conventions can shift
the absolute phase reference.
