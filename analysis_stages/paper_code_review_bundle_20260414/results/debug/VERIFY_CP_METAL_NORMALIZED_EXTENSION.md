# Verify CP Metal-Normalized Extension

Execution date: `2026-04-16`

## Scope

- This is an independent verifier rebuilt from the Stage 3 CP freq-resolved export.
- No legacy isolated-workspace CSV is used to construct the replay quantity.
- Core replay quantity:
  - `Gamma_C_metal_norm(theta,f) = Gamma_C_raw(material, theta, f) / Gamma_C_raw(metal, theta, f)`
- The replay is then compared against the locked `stage4f_raw_primary_full.csv` metal-floor projection.
- For context, both ideal-anchor and same-stage CP numerator anchors are reported.

## Main Results

- Independent replay vs locked Stage 4 metal-floor max magnitude difference: `4.441e-16`
- Independent replay vs locked Stage 4 metal-floor max gain difference: `8.438e-15 dB`
- Ideal-anchor band replay negative rows: `0/23`
- Ideal-anchor band replay rows with residual larger than ideal: `23/23`
- Same-stage band replay negative rows: `0/23`
- `6.5 GHz` ideal-anchor replay negative rows: `0/23`

## Interpretation

- The rewritten replay reproduces the locked metal-floor branch to numerical precision, so the old Stage 4d result is not an artifact of that isolated script.
- The CP metal-normalized extension does remove the same-angle sign contradiction.
- But it remains larger than the ideal residual in every matched-angle row, so it is still not directly comparable to the absolute-like Stage 4 headline residual.
- Changing only the numerator anchor does not convert it into a production-safe correction path.

## Worst Replay-vs-Locked Difference

- `glass 60 deg`: mag diff `4.441e-16`, gain diff `-2.665e-15 dB`

## Outputs

- Angle summary CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_cp_metal_normalized_extension.csv`
- Freq detail CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_cp_metal_normalized_extension_freq.csv`
- Summary CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_cp_metal_normalized_extension_summary.csv`
