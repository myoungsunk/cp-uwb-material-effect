# TE report-lock bundle (`te_lock_0413`)

This folder is the compact raw-data bundle for the TE high-angle
report-definition debug path.

It is intentionally separate from the active truth-table input sets.

## Purpose

Keep the added TE PEC and TE baseline existing-report exports in one place so
they can be checked together before any promotion into the active scattered
stage.

## Contents

- `pec/`
  - copied TE PEC `80/85 deg` existing-report re-extracts
- `baseline/`
  - copied TE baseline `80/85 deg` existing-report exports

## Locked mapping

- `Near_E_Table_3.csv = z_m`
- `Near_E_Table_3_1.csv = z_p`
- both are treated as `scattered` exports

## Companion files

- comparison code:
  - `analysis_stages/ideal_te_tm_scattered_stage/code/compare_te_report_lock_0413.py`
- sanity-check code:
  - `analysis_stages/ideal_te_tm_scattered_stage/code/sanity_check_te_report_lock_0413.py`
- comparison outputs:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/te_lock_0413/SUMMARY.md`
  - `analysis_stages/ideal_te_tm_scattered_stage/results/te_lock_0413/comparison_summary.json`
- sanity-check outputs:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/te_lock_0413/SANITY_CHECK.md`
  - `analysis_stages/ideal_te_tm_scattered_stage/results/te_lock_0413/sanity_check.json`
- persistent folder-level debugging note:
  - `DEBUGGING_NOTE.md`

## Current interpretation

- PEC re-extracts:
  - the old duplicate-block symptom is gone inside the new `Near_E_Table_1/2`
    focus blocks
  - the dominant `Ey` component is still much closer only after a global sign
    flip against the active merged TE PEC CSV
- baseline re-extracts:
  - correct-surface comparison against the active merged baseline is relatively
    close
  - direct and sign-flipped comparisons are nearly the same
  - this currently makes the sign/report-definition ambiguity look PEC-specific
    rather than a blanket TE export issue
- sanity-check lock:
  - baseline comparator path: `PASS`
  - PEC duplicate removal: `PASS`
  - PEC sign/report-definition shift still present: `PASS`
  - promotion of new PEC re-extracts to active truth source: `FAIL`
