# Residual Budget Final

Execution date: `2026-04-16`

## Scope

- This report consolidates the completed Stage 4 diagnostic work into one paper-facing residual budget summary.
- Counts are reported on the current main-range matched-angle subset unless explicitly noted: `23` rows total.
- No production headline value is modified here. The report is diagnostic-only.

## Final Budget Table

| Source | LP effect | CP raw effect | CP eff effect | Status |
| --- | --- | --- | --- | --- |
| Reference normalization mismatch | Same-angle metal normalization removes LP below-ideal rows: `15/23 -> 0/23`. Post-fix main-range Fresnel agreement stays within `0.166-0.380 dB`. | CP raw is already clean at the locked baseline: `0/23`. | Does not directly fix the shared-eff branch. | Resolved for LP. |
| Coherent vs incoherent band averaging (C2/V1) | Mean incoherent-minus-coherent gap for `gamma_x_from_lp` is `0.161 dB`; no LP row exceeds `1 dB`. | Mean gap for `gamma_hat_c_cp_raw` is `0.129 dB`; no raw row exceeds `1 dB`. | Only `2/23` rows exceed `1 dB` for `gamma_hat_c_cp_eff`; max gap `1.016 dB`. | Eliminated as dominant cause. |
| Single-frequency replay (V2) | LP below-ideal persists at all replay points: `6.24 GHz = 12/23`, `6.50 GHz = 15/23`, `6.74 GHz = 12/23`. | Raw stays clean at the center point: `6.50 GHz = 0/23`; band-summary raw replay stays `0/23`. | Eff remains below ideal at all replay points: `6.24 GHz = 9/23`, `6.50 GHz = 15/23`, `6.74 GHz = 12/23`. | Eliminated as sole explanation. |
| Estimator algebra / round-trip (V3) | LP synthetic replay keeps `R_TE` and `R_TM` exact at angle-resolved reference; the large error only appears in fixed single-reference replay. | CP raw angle-resolved round-trip is exact: `13/13` identity-pass rows, max complex abs error `2.27e-16`. | CP eff angle-resolved round-trip is exact: `13/13`, max complex abs error `2.28e-16`. Single-reference replay drifts catastrophically. | Algebra eliminated; supports reference-stack mismatch. |
| Cross-pol contamination | Main-range correlation with Fresnel deviation is limited: Pearson `0.389`, Spearman `0.402`. High-angle rows dominate the bad cases. | Not identified as a primary raw CP driver in current evidence. | Not identified as the dominant CP eff driver in current main-range evidence. | High-angle limiter only. |
| Stage 1 PEC truth accuracy | Current `6.50 GHz` main-use snapshot is clean: TE `0/11` and TM `0/13` above `||R|-1| < 0.05` threshold. | No raw CP contradiction attributable to current PEC truth in the main range. | High-angle TE uncertainty remains a caution term, not a main-range explanation. | Eliminated for current main-use range. |
| Fresnel slab parameter sensitivity | Observed post-metal-normalized LP deviation `0.166-0.380 dB` stays inside the combined `eps_r +/-10%` and thickness `95-105 mm` envelope for every material/polarization. | No direct raw CP impact demonstrated. | No direct CP eff impact demonstrated. | Absorbed into theory uncertainty. |
| Same-stage numerator vs residual decomposition | LP same-stage negative-gap rows remain `15/23`, showing the problem is not removed by using already-exported same-stage numerators alone. Residual mismatch, not numerator mismatch, is the dominant LP gap contributor. | Raw same-stage negative-gap rows: `0/23`. | Eff same-stage negative-gap rows: `6/23`. | Diagnostic split completed. |
| Shared `eps_eff` model mismatch | Not an LP corrective path. | Raw branch stays untouched and remains clean. | Back-solved target `eps` differs materially from shared current `eps_eff`: LP-target mean magnitude bias `-1.50 dB`, median `|phase drift| = 29.34 deg`; ideal-center mean magnitude bias `-4.31 dB`, median `|phase drift| = 22.49 deg`. Locked CP eff baseline is `16/23` below-ideal rows. | Open root cause for CP eff. |
| Material-specific `eps` replay (A1) | LP-target pointwise replay is a negative control and stays near the LP pattern: `15/23`. | Raw remains untouched. | Ideal-target constant replay sharply reduces CP eff below-ideal rows to `3/23` on the band summary and `2/23` at `6.5 GHz`. | Strong evidence that shared `eps_eff` is the dominant CP eff failure mode. |
| CP metal-floor cross-check (A2 independent replay) | Not applicable to LP. | Independent replay from the Stage 3 CP freq export reproduces the locked metal-floor branch to numerical precision: max magnitude diff `4.441e-16`, max gain diff `8.438e-15 dB`. | The replay gives `0/23` negative rows but remains larger than ideal in `23/23` rows, including the `6.5 GHz` replay point. It is therefore still not directly comparable to the Stage 4 absolute-like residual. | Exploratory cross-check only, not a production correction. |

## Main Conclusions

- LP is resolved at the diagnostic level. Same-angle metal normalization removes the below-ideal contradiction and leaves only a small residual agreement error that is already covered by plausible slab-parameter uncertainty.
- CP raw is clean. The locked baseline remains `0/23` below-ideal rows, and no new correction is needed there.
- CP eff remains an open correction-model issue, not an estimator issue and not a band-averaging artifact.
- The strongest current evidence points to the shared `eps_eff` model as the dominant cause of CP eff oversubtraction.
- The new material-specific ideal-target replay meets the current pass criterion:
  - locked CP eff baseline: `16/23`
  - ideal-target replay band summary: `3/23`
  - ideal-target replay at `6.5 GHz`: `2/23`

## Remaining CP Eff Caveats

- The ideal-target replay is still a diagnostic replay, not a production Stage 3/4 path.
- Three concrete rows remain slightly below ideal in the band replay:
  - `concrete 30 deg`: `-0.229 dB`
  - `concrete 40 deg`: `-0.158 dB`
  - `concrete 50 deg`: `-0.137 dB`
- There is a bookkeeping mismatch between the locked `stage4f` shared-eff snapshot and the refreshed shared-eff replay:
  - largest band-magnitude mismatch: `glass 50 deg`, `0.191417`
  - the mismatch is specific to the shared-eff branch; raw CP remains aligned

## Recommended Next Step

- If the next production-oriented diagnostic is requested, the most direct path is to formalize a material-specific or angle-specific `eps_eff` model and replay it against the locked CP eff baseline while preserving the CP raw branch and headline-safe exports.

## Primary Outputs

- A1 replay note: `analysis_stages/paper_code_review_bundle_20260414/results/debug/VERIFY_CP_EFF_MATERIAL_SPECIFIC_EPS.md`
- A1 summary CSV: `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_cp_eff_material_specific_eps_summary.csv`
- A2 replay note: `analysis_stages/paper_code_review_bundle_20260414/results/debug/VERIFY_CP_METAL_NORMALIZED_EXTENSION.md`
- A2 summary CSV: `analysis_stages/paper_code_review_bundle_20260414/results/debug/verify_cp_metal_normalized_extension_summary.csv`
- LP metal-normalized note: `analysis_stages/paper_code_review_bundle_20260414/results/debug/VERIFY_LP_METAL_NORMALIZED.md`
- Cross-pol note: `analysis_stages/paper_code_review_bundle_20260414/results/debug/VERIFY_LP_CROSSPOL_CONTAMINATION.md`
- PEC truth note: `analysis_stages/paper_code_review_bundle_20260414/results/debug/VERIFY_STAGE1_PEC_TRUTH_ACCURACY.md`
- Fresnel slab note: `analysis_stages/paper_code_review_bundle_20260414/results/debug/VERIFY_FRESNEL_SLAB_SENSITIVITY.md`
