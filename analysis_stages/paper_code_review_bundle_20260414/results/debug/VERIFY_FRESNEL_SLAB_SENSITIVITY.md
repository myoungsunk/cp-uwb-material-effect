# Verify Fresnel Slab Sensitivity

Execution date: `2026-04-16`

## Scope

- No new simulation is used.
- The comparison baseline is the current LP metal-normalized replay already exported in the debug bundle.
- The uncertainty sweep reuses the same slab Fresnel model structure used in the current bundle code:
  - `stage_1_sanity_check_fresnel.py`: `SLAB_THICKNESS_M = 0.1` with front/back-interface round-trip terms.
  - `verify_lp_metal_normalized.py`: `WALL_THICKNESS_MM = 100.0` and `fresnel_slab()` with the same finite-thickness form.
- Sweep range: `eps_r x [0.90, 1.10]`, thickness `[95, 105] mm`.

## Main Findings

- concrete: observed main-range TE/TM deviation `0.166 / 0.239 dB`; combined sensitivity envelope `0.614 / 1.264 dB`.
- glass: observed main-range TE/TM deviation `0.275 / 0.293 dB`; combined sensitivity envelope `1.844 / 2.424 dB`.
- wood: observed main-range TE/TM deviation `0.256 / 0.380 dB`; combined sensitivity envelope `5.729 / 6.348 dB`.
- All observed main-range deviations fit inside the combined `eps_r +/-10%` plus `thickness +/-5 mm` uncertainty envelope.
- Thickness-only variation is already enough for most rows, but concrete TM needs combined parameter drift to fully cover the observed `0.239 dB` deviation.

## Interpretation

- The current theory path is confirmed to be a finite-thickness slab model, not a half-space shortcut.
- The observed post-metal-normalization mismatch (`0.17` to `0.38 dB`) is small compared with the Fresnel sensitivity envelope induced by modest parameter uncertainty.
- This means slab-parameter uncertainty is a plausible explanation for the residual `R_TE / R_TM` disagreement that remains after same-angle metal normalization.

## Brewster Context

- concrete: Brewster `66.40 deg`, main limit `55 deg`, TM drop over next `5 deg` = `-3.977 dB`.
- glass: Brewster `68.29 deg`, main limit `60 deg`, TM drop over next `5 deg` = `-7.280 dB`.
- wood: Brewster `54.67 deg`, main limit `45 deg`, TM drop over next `5 deg` = `-7.334 dB`.

Wood remains the steepest TM case at the edge of the current main range,
which is consistent with the practical caution that its TM branch is the most fragile near the Brewster-side region.

## Outputs

- Full sweep CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_fresnel_slab_sensitivity_full.csv`
- Summary CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_fresnel_slab_sensitivity_summary.csv`
- Brewster summary CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_fresnel_brewster_summary.csv`
