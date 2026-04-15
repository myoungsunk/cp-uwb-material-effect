# Stage 4e Residual 3-Way Comparison

Execution date: `2026-04-14`

This stage was executed in the isolated workspace:

- `analysis_stages/stage4e_residual_3way_comparison_20260414`

## Core Finding

The three patch residual variants behave very differently under same-angle comparison:

- raw negative-gap rows: `0/23`
- eff negative-gap rows: `8/23`
- metal-floor negative-gap rows: `0/23`

## Material Summary

- concrete: range=20-55 deg, mean G_ideal=16.13 dB, mean G_raw=8.49 dB, mean G_eff=18.46 dB, mean G_metal_floor=-2.92 dB, neg rows raw/eff/metal=0/5/0
- glass: range=20-60 deg, mean G_ideal=16.31 dB, mean G_raw=9.53 dB, mean G_eff=10.91 dB, mean G_metal_floor=-2.20 dB, neg rows raw/eff/metal=0/1/0
- wood: range=20-45 deg, mean G_ideal=14.05 dB, mean G_raw=8.01 dB, mean G_eff=11.49 dB, mean G_metal_floor=-2.92 dB, neg rows raw/eff/metal=0/2/0

## Figure-Ready CSVs

- Branch magnitude long CSV: `analysis_stages\stage4e_residual_3way_comparison_20260414\results_aliasfree_20260415\residual_3way_branch_mag_long.csv`
- Suppression long CSV: `analysis_stages\stage4e_residual_3way_comparison_20260414\results_aliasfree_20260415\residual_3way_suppression_long.csv`

## Notes

- `patch_raw` and `patch_eff` are patch-stage absolute-like quantities tied to the M3-based extraction path.
- `patch_metal_floor` is a metal-normalized diagnostic series, not a direct replacement for the Stage 4b headline metric.
- Use the `directly_comparable_to_ideal` column to filter plotting logic when needed.

## Outputs

- Wide comparison table: `analysis_stages\stage4e_residual_3way_comparison_20260414\results_aliasfree_20260415\residual_3way_comparison_wide.csv`
- Summary by material: `analysis_stages\stage4e_residual_3way_comparison_20260414\results_aliasfree_20260415\residual_3way_summary_by_material.csv`
- Reviewer table CSV: `analysis_stages\stage4e_residual_3way_comparison_20260414\results_aliasfree_20260415\residual_3way_table_for_review.csv`
- Branch long CSV: `analysis_stages\stage4e_residual_3way_comparison_20260414\results_aliasfree_20260415\residual_3way_branch_mag_long.csv`
- Suppression long CSV: `analysis_stages\stage4e_residual_3way_comparison_20260414\results_aliasfree_20260415\residual_3way_suppression_long.csv`
