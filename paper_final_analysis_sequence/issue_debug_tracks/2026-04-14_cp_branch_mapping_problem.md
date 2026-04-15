# CP Branch Mapping Problem

## Status

This file preserves the problem statement as it stood on `2026-04-14` when
the mismatch was still the main paper-risk item.

As of `2026-04-14`, the critical path has already been closed by:

- LP-anchor branch lock
- Stage 4b convention-locked rerun

So this file should now be read as the locked problem definition, not as a
currently unresolved blocker.

## Problem

Stage 2 ideal CP and Stage 3 LP-derived CP agree on which branch is the small
residual branch, but Stage 3 patch CP uses the opposite `X/C` naming order.

Observed pattern:

| path | small branch | large branch |
| --- | --- | --- |
| ideal CP | `Gamma_X` | `Gamma_C` |
| LP-derived CP | `gamma_x_from_lp` | `gamma_c_from_lp` |
| patch CP | `gamma_hat_c_cp_eff` | `gamma_hat_x_cp_sys` |

So the current issue is not a physics mismatch first. It is a branch-label
mapping mismatch in the patch CP export layer.

## Physical Reading

For a planar isotropic slab, the ideal circular branches are defined as:

- `Gamma_X = (R_TE + R_TM) / 2`
- `Gamma_C = (R_TE - R_TM) / 2`

At general oblique incidence, `R_TE` and `R_TM` tend to have similar
magnitudes with opposite-sign tendency, so:

- the sum branch `Gamma_X` stays smaller
- the difference branch `Gamma_C` stays larger

That is exactly what the ideal and LP-derived paths show. So the patch CP
export is most plausibly a naming-layer swap, not a contradiction of the slab
physics.

## Why This Matters

If this mapping stays ambiguous:

- the headline suppression metric can still be computed numerically, but
  the physical interpretation becomes fragile
- reviewer questions about residual versus dominant CP branch naming become
  harder to answer
- Stage 4 gap interpretation can look like an antenna defect rather than a
  convention mismatch

## Stage 4 Reliability Warning

The original Stage 4a small-branch rule was numerically safe, but not
physically final.

Two warning points drove the follow-up action:

1. Ideal peak inflation at `10 deg`
2. Patch peak stability in the expected `25 deg to 40 deg` window

The first point is the real warning sign. In the ideal table:

- concrete: `|Gamma_X| = 0.0049` at `10 deg`
- glass: `|Gamma_X| = 0.0050` at `10 deg`
- wood: `|Gamma_X| = 0.0053` at `10 deg`

That makes `G_supp_ideal` blow up near the low-angle edge because the residual
branch becomes numerically tiny. But near normal incidence, the TE/TM basis is
not a strong physical descriptor because the plane of incidence becomes
ill-conditioned as `theta -> 0`.

So the Stage 4a ideal peak at `10 deg` had to be treated as a low-angle
artifact, not as the physical headline odd-bounce suppression result.

By contrast, the patch peaks remained stable in the predicted oblique window:

- concrete: `24.60 dB @ 35 deg`
- glass: `25.45 dB @ 40 deg`
- wood: `23.64 dB @ 30 deg`

That asymmetry is why the headline metric needed a second pass after branch
locking.

## Scope

This issue affects:

- Stage 3 patch CP naming
- Stage 4 suppression metric interpretation
- paper captions and methods wording that use `X/C` labels

This issue does not invalidate:

- Stage 1 linear truth
- Stage 2 ideal CP transform
- Stage 3 LP-derived bridge

## Required Acceptance

The issue is considered locked for paper use when all of the following are
true:

1. The ideal small branch is consistently `Gamma_X` in the paper main range.
2. The LP-derived small branch is consistently `gamma_x_from_lp` in the same
   range.
3. The patch CP residual alias is consistently `gamma_hat_c_cp_eff`.
4. The patch CP dominant alias is consistently `gamma_hat_x_cp_sys`.
5. Stage 4 headline reporting uses the locked residual branch explicitly, not
   a generic small-branch fallback rule.
6. Low-angle artifact rows are excluded from the headline claim range.

## Locked Resolution Path

- branch lock method:
  - LP-derived anchor first
- patch export action:
  - add alias columns only
- original Stage 3 script policy:
  - do not rename in place
- headline metric policy:
  - use Stage 4b convention-locked oblique range

## Rejected Alternative

A numerical floor on the residual branch was considered:

- `G_supp = 20 log10(B / max(|residual|, epsilon))`

That would reduce the low-angle spike, but it was not chosen as the primary
paper fix because it looks like a numerical patch.

The preferred decision was instead:

- keep the physics-based interpretation
- restrict the paper headline to the validated oblique range
- start the Stage 4b headline range at `20 deg`

## Paper-Facing Decision

Use these names in the paper-facing execution layer:

- ideal residual branch:
  - `Gamma_X`
- ideal dominant branch:
  - `Gamma_C`
- patch residual branch:
  - `cp_residual_branch`
- patch dominant branch:
  - `cp_dominant_branch`

Keep the legacy Stage 3 raw names only in audit/debug contexts.
