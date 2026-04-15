# Stage 2. Ideal CP Upper Bound

## Current Status

- The active ideal CP table already exists at:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal/truth_table_cp.csv`
- Stage 2 recomputation completed on `2026-04-14` at:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414/truth_table_cp_recomputed_20260414.csv`
- The valid-range diagnosis is already locked in:
  - `analysis_stages/ideal_te_tm_scattered_stage/data/material_cp_valid_range_diagnosis_20260413.md`
- The `2026-04-14` verification confirmed:
  - recomputed CP table = locked CP table exactly
  - material-specific CP main ranges:
    - concrete: `10 deg to 55 deg`
    - glass: `10 deg to 60 deg`
    - wood: `10 deg to 45 deg`
  - PEC main-range anchor:
    - `max |Gamma_X| = 0.0234`
    - `|Gamma_C| = 0.9738 to 1.0100`
    - `arg(Gamma_C)` stays at `+/- 180 deg`

## Purpose

- Derive `Gamma_X` and `Gamma_C` from the locked linear truth table.
- Freeze the ideal CP response as the material-limited upper bound.

## Inputs

- Linear truth table:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal/truth_table_linear_locked.csv`
- Code:
  - `analysis_stages/ideal_te_tm_scattered_stage/code/cp_transform.py`
- Diagnosis lock:
  - `analysis_stages/ideal_te_tm_scattered_stage/data/material_cp_valid_range_diagnosis_20260413.md`

## Execution

1. Rebuild the CP transform from the locked linear table if needed:

```powershell
python .\analysis_stages\ideal_te_tm_scattered_stage\code\cp_transform.py `
  .\analysis_stages\ideal_te_tm_scattered_stage\results\current_manifest_runs\material_5000mm_kobs5_phase0_nominal_rerun_20260414\truth_table_linear_locked.csv `
  .\analysis_stages\ideal_te_tm_scattered_stage\results\current_manifest_runs\material_5000mm_kobs5_phase0_nominal_rerun_20260414\truth_table_cp_recomputed_20260414.csv
```

2. Confirm the CP valid range inherits the weaker linear branch:
   - concrete: `10 deg to 55 deg`
   - glass: `10 deg to 60 deg`
   - wood: `10 deg to 45 deg`
   - shared conservative range: `10 deg to 45 deg`
3. Reconfirm the PEC CP anchor:
   - `|Gamma_X_PEC| -> 0`
   - `|Gamma_C_PEC| -> 1`
   - phase of `Gamma_C_PEC` stays near `180 deg`

## Outputs

- Locked CP truth table:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal/truth_table_cp.csv`
- Recomputed verification table:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_rerun_20260414/truth_table_cp_recomputed_20260414.csv`
- Figure source for paper Fig. 2:
  - `|Gamma_X|`
  - `|Gamma_C|`
  - `XPD = 20 log10(|Gamma_X| / |Gamma_C|)`

## Pass Conditions

- CP main-claim ranges remain material-specific and unchanged from the active
  diagnosis lock.
- Concrete still shows the strongest ideal suppression window in the
  `30 deg to 40 deg` region.
- Wood and glass still show earlier `Gamma_C` growth when the TM branch loses
  stability.
- Recomputed CP table matches the locked CP table exactly.

## Next Stage Link

- Stage 3 compares practical patch outputs against this ideal CP upper bound.

## Sign Convention Note

- With the currently written quantity
  `XPD = 20 log10(|Gamma_X| / |Gamma_C|)`, the strongest suppression region
  appears as a large negative value because `|Gamma_X| << |Gamma_C|`.
- If Fig. 2 should display a positive isolation-style number, use either:
  - `20 log10(|Gamma_C| / |Gamma_X|)`, or
  - `-XPD`
- This is a plotting/sign convention issue, not a Stage 2 extraction error.

## Optional Spot Check

- A one-point direct CP HFSS rerun at `theta = 30 deg`, concrete, remains
  optional.
- Its only role is convention validation:
  - handedness sign
  - half-sum / half-difference consistency
