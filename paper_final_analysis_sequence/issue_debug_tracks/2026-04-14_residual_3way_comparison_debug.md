# Residual 3-Way Comparison Debug

## Purpose

Put the three patch residual variants on the same locked oblique grid:

- raw
- eff
- metal-floor

This is the compact reviewer-facing comparison layer after:

- branch alias lock
- same-angle gap audit
- metal-floor cross-check

## Core Outcome

Same-angle negative-gap counts on the locked main rows:

- raw:
  - `0 / 23`
- eff:
  - `16 / 23`
- metal-floor:
  - `0 / 23`

So the sign failure is isolated to the corrected residual branch.

## Output References

- workspace:
  - `analysis_stages/stage4e_residual_3way_comparison_20260414`
- summary:
  - `analysis_stages/stage4e_residual_3way_comparison_20260414/results/STAGE4E_RESIDUAL_3WAY_COMPARISON.md`
- wide table:
  - `analysis_stages/stage4e_residual_3way_comparison_20260414/results/residual_3way_comparison_wide.csv`
- branch long CSV:
  - `analysis_stages/stage4e_residual_3way_comparison_20260414/results/residual_3way_branch_mag_long.csv`
- suppression long CSV:
  - `analysis_stages/stage4e_residual_3way_comparison_20260414/results/residual_3way_suppression_long.csv`
