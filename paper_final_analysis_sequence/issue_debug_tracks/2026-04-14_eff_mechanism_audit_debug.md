# Eff Mechanism Audit Debug

## Purpose

Separate the cause of the `eff` failure into:

- branch aliasing
- `eps_eff` magnitude growth
- vector over-cancellation

## Core Result

The audit shows that `|eps_eff|` does not increase over the locked oblique
range. It decreases monotonically.

So the high-angle failure is not caused by `eps_eff` getting larger.

Instead, the failure appears when:

- `|eps_eff * Gamma_X|` stays comparable to `|Gamma_C_raw|`
- and the correction term stays close in phase to `Gamma_C_raw`

That produces strong subtraction cancellation and collapses `Gamma_C_eff`.

## Direct CP One-Point Status

The direct CP one-point sanity is now executed, not pending.

What it closed:

- convention / implementation consistency for the one-point patch-style reconstruction

What it did not close:

- the full-angle physical validity of the `eff` correction model

## Output References

- mechanism audit:
  - `analysis_stages/stage4g_eff_mechanism_audit_20260414/results/STAGE4G_EFF_MECHANISM_AUDIT.md`
- one-point sanity with references:
  - `analysis_stages/direct_cp_one_point_sanity_20260414/results/DIRECT_CP_ONE_POINT_WITH_REFERENCES.md`
