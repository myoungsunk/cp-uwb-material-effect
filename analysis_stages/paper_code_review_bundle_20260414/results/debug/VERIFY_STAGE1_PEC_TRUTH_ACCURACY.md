# Verify Stage 1 PEC Truth Accuracy

Execution date: `2026-04-16`

## Scope

- No new simulation is used.
- Inputs are the locked Stage 1 PEC truth tables already mirrored into the bundle.
- Both the single-frequency bundle snapshot and the `2026-04-16` multi-frequency snapshot are checked.
- Pass criterion from the review note: main-range PEC magnitude deviation `||R|-1| < 0.05`.
- The audit tracks both linear magnitude deviation and the QC complex target error against locked PEC targets (`R_TE=-1`, `R_TM=+1`).

## Main Findings

- The current single-frequency `6.50 GHz` bundle snapshot passes the requested main-range criterion:
  - TE main rows above threshold: `0/11`, max deviation `0.046291` at `55 deg`.
  - TM main rows above threshold: `0/13`, max deviation `0.029392` at `15 deg`.
- The multi-frequency snapshot shows that the TE branch, not TM, is where oblique-angle accuracy starts to tighten.
  - `6.24 GHz`: TE main max `0.075520` (1/11 above threshold), TM main max `0.030115` (0/13 above threshold).
  - `6.50 GHz`: TE main max `0.046292` (0/11 above threshold), TM main max `0.029339` (0/13 above threshold).
  - `6.74 GHz`: TE main max `0.067503` (1/11 above threshold), TM main max `0.027283` (0/13 above threshold).
- Only one QC fail exists in the multi-frequency PEC set: `1` row.

## Interpretation

- For the current `6.50 GHz` main-use bundle snapshot, the Stage 1 PEC truth is clean enough under the requested `0.05` linear threshold.
- Across frequency, TE at high oblique angle (`60 deg` and beyond) shows the first meaningful accuracy loss, while TM stays comfortably below the threshold over its full main range.
- The remaining explicit QC fail is `6.24 GHz / TE / 70 deg`, which sits outside the current TE main-claim range.
- This means Stage 1 PEC uncertainty should be treated as a high-angle TE caution term, not as the primary explanation for the current `6.50 GHz` LP main-range contradiction.

## QC Fail Rows

- `6.24 GHz`, `TE`, `70 deg`: target error `0.116676`, status=`fail`

## Worst PEC Rows

- `bundle_multifreq_20260416`, `6.24 GHz`, `70 deg`: TE `||R|-1|=0.116676`, TM `||R|-1|=0.006440`, max `0.116676`
- `bundle_multifreq_20260416`, `6.50 GHz`, `70 deg`: TE `||R|-1|=0.079603`, TM `||R|-1|=0.005138`, max `0.079603`
- `bundle_singlefreq_6p5ghz`, `6.50 GHz`, `70 deg`: TE `||R|-1|=0.079559`, TM `||R|-1|=0.005136`, max `0.079559`
- `bundle_multifreq_20260416`, `6.74 GHz`, `65 deg`: TE `||R|-1|=0.078403`, TM `||R|-1|=0.006121`, max `0.078403`
- `bundle_multifreq_20260416`, `6.24 GHz`, `65 deg`: TE `||R|-1|=0.077745`, TM `||R|-1|=0.007057`, max `0.077745`
- `bundle_multifreq_20260416`, `6.24 GHz`, `60 deg`: TE `||R|-1|=0.075520`, TM `||R|-1|=0.004831`, max `0.075520`
- `bundle_multifreq_20260416`, `6.74 GHz`, `60 deg`: TE `||R|-1|=0.067503`, TM `||R|-1|=0.005580`, max `0.067503`
- `bundle_multifreq_20260416`, `6.74 GHz`, `55 deg`: TE `||R|-1|=0.048578`, TM `||R|-1|=0.006640`, max `0.048578`

## Outputs

- Full CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_stage1_pec_truth_accuracy_full.csv`
- Summary CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_stage1_pec_truth_accuracy_summary.csv`
- QC subset CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_stage1_pec_truth_accuracy_qc_subset.csv`
- Plot PNG: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_stage1_pec_truth_accuracy.png`
