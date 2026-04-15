# Stage 7. Figure and Table Mapping

Execution date: `2026-04-15`

## Current Status

- main-text mapping is now aligned to the current same/flip-safe Stage 2 tables
  and the raw-primary Stage 4 lock
- branch naming ambiguity is closed for paper use
- `eff` and PEC-based CP correction remain supplement-only

## Purpose

- bind each manuscript figure and table to one locked claim, one locked source
  set, and one reporting rule

## Inputs

- Stage 1 linear truth lock:
  - `analysis_stages/paper_code_review_bundle_20260414/data/stage_1/truth_table_linear_locked.csv`
- Stage 2 same/flip CP lock:
  - `analysis_stages/paper_code_review_bundle_20260414/data/stage_2/sameflip_alias_20260415/truth_table_cp_shared_common_sameflip.csv`
- Stage 3a raw-primary alias lock:
  - `analysis_stages/lp_anchor_branch_lock_20260414/results_sharedcommon_check_20260415/patch_cp_extracted_with_lp_anchor_alias.csv`
- Stage 4c raw-primary reporting:
  - `analysis_stages/paper_code_review_bundle_20260414/code/stage4f_raw_primary_dual_20260414/results_aliasfree_20260415/`
- direct CP one-point sanity:
  - `analysis_stages/paper_code_review_bundle_20260414/code/direct_cp_one_point_sanity_20260414/results_sharedcommon_check_20260415/`
- rejected correction-path audits:
  - `analysis_stages/paper_code_review_bundle_20260414/results/STAGE4G_EFF_MECHANISM_AUDIT.md`
  - `analysis_stages/paper_code_review_bundle_20260414/results/STAGE4H_PEC_BASED_CP_COMPARISON.md`

## Paper Element Map

| Paper element | Status | Locked source(s) | Claim / rule |
| --- | --- | --- | --- |
| Fig. 1 | locked | `analysis_stages/paper_code_review_bundle_20260414/data/stage_1/truth_table_linear_locked.csv` | `|R_TE|` and `|R_TM|` vs angle with Fresnel overlay. |
| Fig. 2 | locked | `analysis_stages/paper_code_review_bundle_20260414/data/stage_2/sameflip_alias_20260415/truth_table_cp_shared_common_sameflip.csv` | Ideal CP basis transform only. Manuscript labels may use `Gamma_X / Gamma_C`, but the CSV source is `Gamma_same / Gamma_flip`. |
| Fig. 3 | locked | `analysis_stages/paper_code_review_bundle_20260414/data/stage_2/sameflip_alias_20260415/truth_table_cp_shared_common_sameflip.csv`; `analysis_stages/lp_anchor_branch_lock_20260414/results_sharedcommon_check_20260415/patch_cp_extracted_with_lp_anchor_alias.csv`; `analysis_stages/lp_anchor_branch_lock_20260414/results_sharedcommon_check_20260415/lp_anchor_branch_lock_main.csv` | Overlay ideal residual, LP-derived residual, and CP raw residual. Do not use `eff` as a main curve. |
| Fig. 4 (headline) | locked | `analysis_stages/paper_code_review_bundle_20260414/code/stage4f_raw_primary_dual_20260414/results_aliasfree_20260415/stage4f_raw_primary_full.csv`; `analysis_stages/paper_code_review_bundle_20260414/results/pec_based_cp_comparison_long.csv` filtered to manuscript-safe curves only | Headline suppression plot over validated oblique ranges. |
| Table I | locked | `analysis_stages/paper_code_review_bundle_20260414/code/stage4f_raw_primary_dual_20260414/results_aliasfree_20260415/table1_raw_primary_means.csv` | Report range-wise mean suppression by material. Use ideal and CP raw as main columns; LP-derived may be added as a practical bridge column. |
| Supplement A | locked | `analysis_stages/lp_anchor_branch_lock_20260414/results_sharedcommon_check_20260415/LP_ANCHOR_BRANCH_LOCK_SUMMARY.md`; `analysis_stages/lp_anchor_branch_lock_20260414/results_sharedcommon_check_20260415/lp_anchor_branch_lock_full.csv` | Branch mapping resolution and raw-primary alias lock. |
| Supplement B | locked | `analysis_stages/paper_code_review_bundle_20260414/code/direct_cp_one_point_sanity_20260414/results_sharedcommon_check_20260415/DIRECT_CP_ONE_POINT_WITH_REFERENCES.md`; `analysis_stages/paper_code_review_bundle_20260414/code/direct_cp_one_point_sanity_20260414/results_sharedcommon_check_20260415/direct_cp_one_point_comparison.csv` | Direct CP one-point sanity for convention and implementation consistency. |
| Supplement C | locked | `analysis_stages/paper_code_review_bundle_20260414/results/STAGE4G_EFF_MECHANISM_AUDIT.md`; `analysis_stages/paper_code_review_bundle_20260414/results/STAGE4H_PEC_BASED_CP_COMPARISON.md` | Rejected correction paths. Show why `eff` and PEC-based CP subtraction remain supplementary. |

## Caption Guardrails

- use `upper bound` only for the ideal layer
- use `conservative system result` or `antenna-leakage-inclusive result` for
  CP raw
- do not describe `eff` as more physical than `raw`
- do not present PEC-based CP correction as a manuscript-facing improvement

