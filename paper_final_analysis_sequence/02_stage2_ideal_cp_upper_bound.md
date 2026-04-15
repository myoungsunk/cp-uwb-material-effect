# Stage 2. Ideal CP Upper Bound

## Current Status

- The paper-facing ideal CP lock now lives in the same/flip-safe tables:
  - `analysis_stages/paper_code_review_bundle_20260414/data/stage_2/sameflip_alias_20260415/truth_table_cp_shared_common_sameflip.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/data/stage_2/sameflip_alias_20260415/truth_table_cp_raw_sameflip.csv`
  - `analysis_stages/paper_code_review_bundle_20260414/data/stage_2/sameflip_alias_20260415/truth_table_cp_locked_sameflip.csv`
- The internal branch labels were refreshed on `2026-04-15`:
  - `Gamma_same` = paper `Gamma_X`
  - `Gamma_flip` = paper `Gamma_C`
- PEC anchor remains numerically unchanged:
  - `max |Gamma_same| = 0.0234`
  - `|Gamma_flip| = 0.9738 to 1.0100`
  - phase of `Gamma_flip` stays near `+/- 180 deg`

## Purpose

- Derive the ideal CP upper bound from the locked linear truth table.
- Keep the paper notation `Gamma_X / Gamma_C` while storing branch-safe internal
  aliases `Gamma_same / Gamma_flip`.

## Inputs

- Locked linear truth:
  - `analysis_stages/paper_code_review_bundle_20260414/data/stage_1/truth_table_linear_locked.csv`
- Stage 2 same/flip alias outputs:
  - `analysis_stages/paper_code_review_bundle_20260414/code/stage2_sameflip_alias_20260415/results/`

## Locked Mapping

- internal same-hand branch:
  - `Gamma_same`
  - paper symbol: `Gamma_X`
- internal flipped-hand branch:
  - `Gamma_flip`
  - paper symbol: `Gamma_C`

So manuscript text may keep using `Gamma_X / Gamma_C`, but any CSV-driven audit
or direct-CP sanity step should read `Gamma_same / Gamma_flip` first.

## Outputs

- primary paper-facing Stage 2 table:
  - `analysis_stages/paper_code_review_bundle_20260414/data/stage_2/sameflip_alias_20260415/truth_table_cp_shared_common_sameflip.csv`
- code-side mirror:
  - `analysis_stages/paper_code_review_bundle_20260414/code/stage2_sameflip_alias_20260415/results/truth_table_cp_shared_common_sameflip.csv`

## Pass Conditions

- material-specific CP ranges remain locked:
  - concrete: `10 deg to 55 deg`
  - glass: `10 deg to 60 deg`
  - wood: `10 deg to 45 deg`
- PEC same-hand branch stays near zero.
- PEC flipped-hand branch stays near unity.
- CSV source labels now read `Gamma_same / Gamma_flip`, not legacy
  `Gamma_X / Gamma_C`.

## Figure Rule

- Fig. 2 may still be captioned with paper symbols:
  - `|Gamma_X|`
  - `|Gamma_C|`
- but the data source should be the same/flip-safe Stage 2 table above.

## Direct-CP Note

- The direct CP one-point sanity is now executed as a supplement-side
  convention/implementation check.
- It does not change Stage 2 values; it only confirms that downstream CP
  handling is not a file-format accident.

