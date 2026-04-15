# LP Anchor Branch Lock Summary

Execution date: `2026-04-14`

This stage was executed in the isolated workspace:

- `analysis_stages/lp_anchor_branch_lock_20260414`

## Main-Range Verdict

- Main rows audited: `29`
- Ideal residual branch rows: `29/29`
- LP small branch = `gamma_x_from_lp` rows: `29/29`
- Patch eff small branch = `gamma_hat_c_cp_eff` rows: `29/29`
- LP aligned-vote rows: `29/29`
- Patch eff swapped-vote rows: `29/29`

## Error Comparison

- LP aligned mean abs error: `0.071366`
- LP swapped mean abs error: `0.578750`
- Patch eff aligned mean abs error: `0.529120`
- Patch eff swapped mean abs error: `0.109407`

## Locked Alias Decision

- `cp_residual_branch = gamma_hat_c_cp_raw`
- `cp_dominant_branch = gamma_hat_x_cp_sys`
- `cp_residual_branch_supplementary = gamma_hat_c_cp_eff`
- `patch_eff_*` audit columns above remain supplementary diagnostics only

## Outputs

- Full audit: `analysis_stages\paper_code_review_bundle_20260414\code\stage3_verify_sharedcommon_check_20260415\lp_anchor_branch_lock_full.csv`
- Main-range audit: `analysis_stages\paper_code_review_bundle_20260414\code\stage3_verify_sharedcommon_check_20260415\lp_anchor_branch_lock_main.csv`
- Summary table: `analysis_stages\paper_code_review_bundle_20260414\code\stage3_verify_sharedcommon_check_20260415\lp_anchor_branch_lock_summary.csv`
- Aliased patch CP export: `analysis_stages\paper_code_review_bundle_20260414\code\stage3_verify_sharedcommon_check_20260415\patch_cp_extracted_with_lp_anchor_alias.csv`
