# Stage 4f Summary

Execution date: `2026-04-14`

This stage was executed in the isolated workspace:

- `analysis_stages/stage4f_raw_primary_dual_20260414`

## Current Reporting Rule

- primary patch series: `raw`
- supplementary patch series: `eff`
- diagnostic cross-check: `metal-floor`

## Why Raw Is Primary

- same-angle negative-gap rows for `raw`: `0 / 23`
- same-angle negative-gap rows for `eff`: `16 / 23`
- same-angle negative-gap rows for `metal-floor`: `0 / 23`, but metal-floor is normalized and not absolute

## Material Summary

- concrete: range=20-55 deg, mean G_ideal=16.13 dB, mean G_raw=8.49 dB, mean G_eff=18.46 dB, mean Delta(ideal-raw)=7.64 dB, neg rows raw/eff=0/5
- glass: range=20-60 deg, mean G_ideal=16.31 dB, mean G_raw=9.53 dB, mean G_eff=19.15 dB, mean Delta(ideal-raw)=6.78 dB, neg rows raw/eff=0/6
- wood: range=20-45 deg, mean G_ideal=14.05 dB, mean G_raw=8.01 dB, mean G_eff=18.63 dB, mean Delta(ideal-raw)=6.04 dB, neg rows raw/eff=0/5

## Outputs

- Full audit: `analysis_stages\stage4f_raw_primary_dual_20260414\results\stage4f_raw_primary_full.csv`
- Summary table: `analysis_stages\stage4f_raw_primary_dual_20260414\results\stage4f_raw_primary_summary.csv`
- Table I candidate: `analysis_stages\stage4f_raw_primary_dual_20260414\results\table1_raw_primary_means.csv`
- Eff negative rows: `analysis_stages\stage4f_raw_primary_dual_20260414\results\stage4f_eff_negative_rows.csv`
- Eff negative distribution: `analysis_stages\stage4f_raw_primary_dual_20260414\results\stage4f_eff_negative_distribution.csv`
- Raw-primary figure: `analysis_stages\stage4f_raw_primary_dual_20260414\results\fig4f_raw_primary_dual.png`

## Direct CP One-Point Sanity

This remains a supplement-side convention check.

At one fixed point (recommended: concrete, 30 deg, 6.5 GHz), run an explicit
direct CP excitation in HFSS and export both reflected CP receive branches.

Use that one point to answer two questions:

- which receive branch is physically the residual branch
- whether the directly observed CP residual is closer to `raw` or to `eff`

So it is not a full new stage sweep. It is one spot-check used to lock
handedness/co-cross convention and to sanity-check the correction model.
