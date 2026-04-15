# Raw-Primary Dual Reporting Debug

## Purpose

Close the Stage 4 reporting question after:

- branch alias lock
- same-angle raw/eff audit
- metal-floor cross-check

## Final Reporting Decision

- primary:
  - `raw`
- supplement:
  - `eff`
- diagnostic only:
  - `metal-floor`

## Why

Same-angle negative-gap counts on the locked oblique main rows:

- raw:
  - `0 / 23`
- eff:
  - `16 / 23`
- metal-floor:
  - `0 / 23`, but not an absolute metric

So the raw branch is the only patch-stage absolute-like residual that remains
compatible with the intended ideal-versus-practical ordering.

## Output References

- workspace:
  - `analysis_stages/stage4f_raw_primary_dual_20260414`
- summary:
  - `analysis_stages/stage4f_raw_primary_dual_20260414/results/STAGE4F_SUMMARY.md`
- table:
  - `analysis_stages/stage4f_raw_primary_dual_20260414/results/table1_raw_primary_means.csv`
