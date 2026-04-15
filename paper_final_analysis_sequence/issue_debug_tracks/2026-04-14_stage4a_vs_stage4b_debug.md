# Stage 4a vs Stage 4b Debug Comparison

## Purpose

Record why Stage 4a was preserved as an audit trail and why Stage 4b became the
paper headline source.

## Role Split

- Stage 4a:
  - branch-agnostic small-branch audit trail
- Stage 4b:
  - convention-locked oblique headline result

This split was introduced on `2026-04-14`.

## Why Stage 4a Was Not Enough

Stage 4a used the rule:

- `residual branch = smaller CP branch`

That was numerically safe while the branch labels were still ambiguous, but it
left two paper-facing problems:

1. The ideal peak moved to `10 deg`, where low-angle basis degeneracy makes the
   result hard to interpret physically.
2. `Delta_G` also peaked at `10 deg`, which could wrongly imply that the patch
   antenna underperforms at low angle rather than revealing a low-angle ideal
   artifact.

## Stage 4a vs Stage 4b Summary

| material | Stage 4a ideal peak | Stage 4b ideal peak | patch peak in both runs | Stage 4a gap peak | Stage 4b gap peak |
| --- | --- | --- | --- | --- | --- |
| concrete | `37.51 dB @ 10 deg` | `22.92 dB @ 20 deg` | `24.60 dB @ 35 deg` | `31.29 dB @ 10 deg` | `8.42 dB @ 20 deg` |
| glass | `36.75 dB @ 10 deg` | `23.55 dB @ 30 deg` | `25.45 dB @ 40 deg` | `32.09 dB @ 10 deg` | `8.09 dB @ 20 deg` |
| wood | `26.59 dB @ 10 deg` | `18.90 dB @ 20 deg` | `23.64 dB @ 30 deg` | `21.36 dB @ 10 deg` | `4.35 dB @ 20 deg` |

## Interpretation

The comparison shows that:

- the patch peak location was already stable
- the artificial low-angle inflation existed on the ideal side
- the gap compression in Stage 4b is mostly a cleanup of the low-angle
  artifact, not a reversal of the patch physics

So Stage 4b is the more defensible paper headline because it keeps the same
patch behavior while removing the misleading low-angle ideal spike.

## Final Usage Rule

- cite Stage 4a only when explaining the audit trail
- cite Stage 4b for the paper headline figure, Table I, and discussion text
