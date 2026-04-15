# Paper Final Analysis Sequence

This folder is the paper-facing lock for the final CP odd-bounce analysis.

Numeric outputs remain under `analysis_stages/`. This folder records:

- notation
- execution status
- paper-safe branch mapping
- headline/supplement boundaries
- figure/table source mapping
- integrated CSV copies for stage-wise reading
- issue/debug status summaries

## Current Paper-Safe Lock

- Stage 2 internal CP labels are now explicit:
  - `Gamma_same` = paper `Gamma_X`
  - `Gamma_flip` = paper `Gamma_C`
- Stage 3a locks the manuscript-facing patch residual as:
  - `gamma_hat_rr_raw_cp`
- Stage 4 headline reporting is raw-primary:
  - ideal upper bound vs CP raw
- `gamma_hat_rr_leakage_corrected_cp` and PEC-based CP correction remain supplement-only
- the direct CP one-point sanity is closed for convention / implementation
  consistency

## Stage Status

| Stage | File | Status | Note |
| --- | --- | --- | --- |
| 0 | `00_stage0_notation_lock.md` | locked | Paper symbols and internal same/flip aliases are mapped explicitly. |
| 1 | `01_stage1_ideal_te_tm_truth.md` | rerun verified | Linear truth and Fresnel sanity remain the ideal anchor. |
| 2 | `02_stage2_ideal_cp_upper_bound.md` | relabeled and locked | Stage 2 now points to same/flip-safe CP truth tables. |
| 3 | `03_stage3_patch_system_practical_layer.md` | executed and locked | Stage 3 numeric exports exist; Stage 3a supplies the paper-facing alias export. |
| 3a | `03a_lp_anchor_branch_lock.md` | shared-common rerun locked | Raw-primary alias lock is decisive on `29 / 29` main rows. |
| 4 | `04_stage4_suppression_gain_dual_metric.md` | audit trail only | Historical small-branch / low-angle audit. |
| 4a | `04a_cp_branch_mapping_resolution_note.md` | closed for paper use | Remaining open issue is only `eff` correction validity. |
| 4b | `04b_stage4b_convention_locked_oblique.md` | audit layer only | Oblique alias-lock comparison using the raw-primary alias. |
| 4c | `04c_stage4f_raw_primary_dual_reporting.md` | current headline layer | Raw-primary reporting with latest alias-free Stage 4f outputs. |
| 5 | `05_stage5_odd_bounce_extension.md` | locked | Discussion scope text. |
| 6 | `06_stage6_uwb_dispersion_sensitivity.md` | supplement-side only | Internal robustness check, not externally calibrated dispersion proof. |
| 7 | `07_stage7_figure_table_mapping.md` | refreshed | Current figure/table map points to the active raw-primary lock. |

## Valid Ranges

- material validity from the ideal lock:
  - concrete: `10 deg to 55 deg`
  - glass: `10 deg to 60 deg`
  - wood: `10 deg to 45 deg`
- manuscript headline ranges:
  - concrete: `20 deg to 55 deg`
  - glass: `20 deg to 60 deg`
  - wood: `20 deg to 45 deg`

## Sequence

1. Use Stage 0 before touching captions, legends, or table symbols.
2. Use Stage 1 and 2 to anchor ideal TE/TM and ideal CP.
3. Use Stage 3 and 3a for patch-system exports and raw-primary alias lock.
4. Treat Stage 4 and 4b as audit layers only.
5. Use Stage 4c for the current paper headline.
6. Use Stage 7 for final manuscript figure/table binding.

## Support Artifacts

- integrated CSV package:
  - `stage_csv_integrated/`
  - entry manifest:
    - `stage_csv_integrated/stage_csv_manifest_20260415.csv`
- stagewise rationale and interpretation:
  - `08_stagewise_analysis_rationale_and_interpretation.md`
- issue/debug status:
  - `issue_debug_tracks/ISSUE_TRACK_STATUS_20260415.md`
  - `issue_debug_tracks/issue_track_manifest_20260415.csv`

## Remaining Gap

There is no remaining headline-blocking numeric issue in the current lock.

The remaining work is:

- manuscript assembly
- final figure rendering
- caption polishing
- optional reviewer-defense additions only

## Issue Track

- separate debug/problem markdown lives under:
  - `paper_final_analysis_sequence/issue_debug_tracks`
- branch mapping mismatch:
  - closed for paper use
- `eff` correction-model validity:
  - retained as supplement-only
