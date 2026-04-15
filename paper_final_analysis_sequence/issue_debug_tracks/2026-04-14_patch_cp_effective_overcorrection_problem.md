# Patch CP Effective Residual Over-Correction Problem

## Problem

After the LP-anchor branch lock, the branch naming ambiguity is resolved.
However, the corrected patch residual branch

- `gamma_hat_c_cp_eff`

still produces a new paper-risk issue:

- at many same-angle rows, the corrected patch residual is smaller than the
  ideal residual branch `Gamma_X`
- therefore `Delta_G(theta) = G_supp_ideal(theta) - G_supp_patch(theta)` turns
  negative

That breaks the intended reading that the patch result is a practical,
antenna-limited version of an ideal upper bound.

## Why This Matters

If `Delta_G < 0` at the same angle, then the current paper-safe sentence

- "the ideal-to-patch gap quantifies antenna-limited loss"

is not generally valid.

This is a stronger issue than the earlier Stage 4a low-angle artifact because
it survives even after:

- the branch alias is locked
- the headline range is restricted to oblique incidence

## Observed Pattern

Stage 4c same-angle audit found:

- corrected residual negative-gap rows:
  - `16 / 23`
- raw residual negative-gap rows:
  - `0 / 23`

So the sign problem is introduced by the effective correction layer, not by the
raw patch residual branch itself.

## Immediate Paper Constraint

Until this is explained or repaired, do not claim:

- `Delta_G` as a universal antenna-limited loss metric
- peak-to-peak ideal versus patch ordering as if ideal were always higher
- range-mean ideal versus patch ordering as if ideal were always higher

## Safe Interim Use

Still safe:

- branch alias lock itself
- Stage 4a as audit trail
- Stage 4b as an oblique comparison figure
- reporting patch suppression on its own

Not yet safe:

- interpreting corrected-patch suppression as a strict achievable lower bound
  to the ideal residual at matched angle

## Next Acceptance Target

This issue is closed only if one of the following becomes true:

1. The correction model is revised and same-angle `Delta_G >= 0` is restored
   over the paper main range.
2. A direct CP sanity check shows that the corrected branch is the physically
   right observable, and the comparison metric is reformulated so that negative
   `Delta_G` is not treated as a contradiction.
3. The paper drops the upper-bound/gap interpretation and uses a more limited
   empirical comparison framing.
