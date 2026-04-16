# Stage 1 Shared-Common-Lock A/B Check (2026-04-15)

Scope:
- modified file: `analysis_stages/ideal_te_tm_scattered_stage/code/build_truth_table.py`
- archived pre-mod code: `analysis_stages/ideal_te_tm_scattered_stage/code_archive_before_shared_common_lock_20260415/`
- authoritative rerun with added variants:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs/material_5000mm_kobs5_phase0_nominal_shared_common_ab_20260415/`

## What changed

The Stage 1 pipeline now writes three linear/CP variants from the same raw truth table:

- `truth_table_linear_raw.csv` and `truth_table_cp_raw.csv`
  - no PEC lock on `R_TE` / `R_TM`
- `truth_table_linear_shared_common_lock.csv` and `truth_table_cp_shared_common_lock.csv`
  - one shared PEC phase lock applied to both TE and TM
- `truth_table_linear_locked.csv` and `truth_table_cp.csv`
  - legacy independent TE/TM PEC lock, kept for backward compatibility

The pipeline also writes:

- `truth_table_cp_lock_variant_comparison.csv`
- `truth_table_cp_lock_variant_summary.csv`

## Safety check

The legacy official outputs are unchanged.

Hash comparison against the previous authoritative run:

- `truth_table_linear_raw.csv`: identical
- `truth_table_linear_locked.csv`: identical
- `truth_table_cp.csv`: identical

So this change adds variants without altering the prior independent-lock result.

## Main result

### 1. Shared common lock removes CP magnitude inflation

Compared against raw:

- `Gamma_X` shared-common max abs delta: `1.08e-16`
- `Gamma_C` shared-common max abs delta: `2.22e-16`

This is machine-precision zero. As expected, a shared common phase lock preserves CP magnitudes.

### 2. Independent lock still perturbs CP magnitude

Main-claim non-PEC rows:

- `Gamma_C` locked minus raw:
  - mean: `+1.107e-4`
  - median: `+4.637e-5`
  - max: `+1.042e-3`
  - increased in `26 / 29` rows
- `Gamma_X` locked minus raw:
  - mean: `-6.789e-4`
  - median: `-3.967e-4`
  - max abs: `4.996e-3`
  - increased in `3 / 29` rows

Non-PEC all rows:

- `Gamma_C` locked minus raw:
  - mean: `+4.232e-4`
  - median: `+6.860e-5`
  - max: `+2.713e-3`
  - increased in `36 / 39` rows

Largest main-claim non-PEC `Gamma_C` inflation:

- `glass, 60 deg`: `+1.042e-3`

## Interpretation

The Stage 1 conclusion is now much cleaner:

1. `raw` and `shared common lock` are equivalent for CP magnitude.
2. The old independent TE/TM lock injects a small but systematic CP-magnitude perturbation.
3. That perturbation is not the dominant source of the large practical over-correction seen later in Stage 3/4, but it is real and should not be used for the safest CP-magnitude comparison path.

## Paper-safe usage

- For CP magnitude comparison, use `truth_table_cp_raw.csv` or `truth_table_cp_shared_common_lock.csv`.
- Keep legacy `truth_table_cp.csv` only for backward compatibility with the old Stage 1 lock convention.
- If a single lock-based Stage 1 output must be reported, the shared-common-lock variant is the defensible one because it aligns PEC phase reference without changing CP magnitudes.
