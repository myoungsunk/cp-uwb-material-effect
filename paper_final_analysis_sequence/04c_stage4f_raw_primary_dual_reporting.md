# Stage 4c. Raw-Primary Dual Reporting

## Current Status

- Latest paper-safe Stage 4f outputs:
  - `analysis_stages/paper_code_review_bundle_20260414/code/stage4f_raw_primary_dual_20260414/results_aliasfree_20260415/stage4f_raw_primary_full.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/code/stage4f_raw_primary_dual_20260414/results_aliasfree_20260415/stage4f_raw_primary_summary.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/code/stage4f_raw_primary_dual_20260414/results_aliasfree_20260415/table1_raw_primary_means.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/code/stage4f_raw_primary_dual_20260414/results_aliasfree_20260415/fig4f_raw_primary_dual.png`

## Purpose

- Keep the manuscript headline on the only patch residual that remains
  same-angle ordered against the ideal layer.
- Report `eff` only as a supplementary corrected interpretation.

## Current Reporting Rule

- ideal reference:
  - `Gamma_same` (paper `Gamma_X`)
- primary patch residual:
  - `gamma_hat_rr_raw_cp`
- supplementary corrected residual:
  - `gamma_hat_rr_leakage_corrected_cp`
- diagnostic cross-check:
  - `gamma_hat_c_metal_floor`

## Why Raw Is Primary

Same-angle negative-gap rows over the oblique locked main rows:

- raw:
  - `0 / 23`
- eff:
  - `8 / 23`
- metal-floor:
  - `0 / 23`, but metal-floor is normalized and not absolute

So raw remains the only manuscript-safe absolute-like patch residual.

## Material Summary

- concrete:
  - range: `20 to 55 deg`
  - mean `G_supp_ideal`: `16.13 dB`
  - mean `G_supp_patch_raw`: `8.49 dB`
  - mean `G_supp_patch_eff`: `18.46 dB`
  - mean `Delta(ideal - raw)`: `7.64 dB`
  - negative rows raw / eff: `0 / 5`
- glass:
  - range: `20 to 60 deg`
  - mean `G_supp_ideal`: `16.31 dB`
  - mean `G_supp_patch_raw`: `9.53 dB`
  - mean `G_supp_patch_eff`: `10.91 dB`
  - mean `Delta(ideal - raw)`: `6.78 dB`
  - negative rows raw / eff: `0 / 1`
- wood:
  - range: `20 to 45 deg`
  - mean `G_supp_ideal`: `14.05 dB`
  - mean `G_supp_patch_raw`: `8.01 dB`
  - mean `G_supp_patch_eff`: `11.49 dB`
  - mean `Delta(ideal - raw)`: `6.04 dB`
  - negative rows raw / eff: `0 / 2`

## Eff Failure Pattern

- concrete:
  - `30 to 39 deg`: `1`
  - `40+ deg`: `4`
- glass:
  - `40+ deg`: `1`
- wood:
  - `30 to 39 deg`: `1`
  - `40+ deg`: `1`

The corrected residual still fails mainly in the oblique mid/high-angle region,
even after the later semantic cleanup.

## Direct CP One-Point Sanity

- executed and closed for convention / implementation consistency:
  - `analysis_stages/paper_code_review_bundle_20260414/code/direct_cp_one_point_sanity_20260414/results_sharedcommon_check_20260415/DIRECT_CP_ONE_POINT_WITH_REFERENCES.md`
- current closed reading:
  - branch convention is no longer the blocker
  - `eff` remains supplementary because of correction-model validity, not
    because of a file-format or handedness accident

## Paper Use

- use this stage for the current headline figure and Table I means
- cite Stage 4b only as the oblique alias-lock comparison
- keep `eff` and PEC-based correction in supplement-side discussion only
