# Stage 4c. Raw-Primary Dual Reporting

## Current Status

- Stage 4f was executed in the isolated workspace:
  - `analysis_stages/stage4f_raw_primary_dual_20260414`
- Outputs now exist:
  - `analysis_stages/stage4f_raw_primary_dual_20260414/results/stage4f_raw_primary_full.csv`
  - `analysis_stages/stage4f_raw_primary_dual_20260414/results/stage4f_raw_primary_summary.csv`
  - `analysis_stages/stage4f_raw_primary_dual_20260414/results/table1_raw_primary_means.csv`
  - `analysis_stages/stage4f_raw_primary_dual_20260414/results/stage4f_eff_negative_rows.csv`
  - `analysis_stages/stage4f_raw_primary_dual_20260414/results/stage4f_eff_negative_distribution.csv`
  - `analysis_stages/stage4f_raw_primary_dual_20260414/results/fig4f_raw_primary_dual.png`
  - `analysis_stages/stage4f_raw_primary_dual_20260414/results/STAGE4F_SUMMARY.md`

## Purpose

- Convert the Stage 4 outcome into a paper-safe reporting structure after the
  same-angle gap audits.
- Use the raw patch residual as the primary system-stage metric.
- Keep the corrected residual as a supplementary interpretation only.

## Current Reporting Rule

- ideal reference:
  - `Gamma_X`
- primary patch residual:
  - `Gamma_C_raw`
- supplementary corrected residual:
  - `Gamma_C_eff`
- diagnostic cross-check only:
  - `Gamma_C_metal_floor`

## Why Raw Is Primary

Same-angle negative-gap counts over the locked oblique main rows:

- raw:
  - `0 / 23`
- eff:
  - `16 / 23`
- metal-floor:
  - `0 / 23`, but metal-floor is metal-normalized and not absolute

So the raw branch is the only patch-stage absolute-like quantity that preserves
the intended matched-angle ordering against the ideal residual branch across the
full current paper range.

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
  - mean `G_supp_patch_eff`: `19.15 dB`
  - mean `Delta(ideal - raw)`: `6.78 dB`
  - negative rows raw / eff: `0 / 6`
- wood:
  - range: `20 to 45 deg`
  - mean `G_supp_ideal`: `14.05 dB`
  - mean `G_supp_patch_raw`: `8.01 dB`
  - mean `G_supp_patch_eff`: `18.63 dB`
  - mean `Delta(ideal - raw)`: `6.04 dB`
  - negative rows raw / eff: `0 / 5`

## Eff Negative-Row Distribution

The corrected residual failure is concentrated mainly in the oblique
mid-to-high-angle region:

- concrete:
  - `30 to 39 deg`: `1`
  - `40+ deg`: `4`
- glass:
  - `30 to 39 deg`: `1`
  - `40+ deg`: `5`
- wood:
  - `20 to 29 deg`: `1`
  - `30 to 39 deg`: `2`
  - `40+ deg`: `2`

This is consistent with an oblique-angle over-correction trend.

## Paper Use

- Use this stage for the current headline figure and Table I candidate.
- Cite Stage 4b as the branch-locked oblique comparison layer.
- Cite Stage 4c/4d/4e as the audit chain that justified the raw-primary switch.
