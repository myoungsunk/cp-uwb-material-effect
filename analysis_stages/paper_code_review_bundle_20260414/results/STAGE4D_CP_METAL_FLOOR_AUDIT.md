# Stage 4d CP Metal-Floor Audit

Execution date: `2026-04-14`

This stage was executed in the isolated workspace:

- `analysis_stages/stage4d_cp_metal_floor_audit_20260414`

## Core Finding

Using the legacy metal-floor CP ratio removes the same-angle sign problem,
but the resulting quantity is not a direct substitute for the Stage 4b
patch residual magnitude.

- negative same-angle rows: `0/23`
- rows with metal-floor residual > ideal residual: `23/23`

## Summary By Material

- concrete: n=8, negative delta=0/8, mean G_patch_metal_floor=-2.92 dB, mean Delta(ideal-metal_floor)=18.99 dB
- glass: n=9, negative delta=0/9, mean G_patch_metal_floor=-2.20 dB, mean Delta(ideal-metal_floor)=18.43 dB
- wood: n=6, negative delta=0/6, mean G_patch_metal_floor=-2.92 dB, mean Delta(ideal-metal_floor)=16.93 dB

## Interpretation

- The metal-floor branch stays larger than the ideal residual branch at matched angle.
- That removes the `Delta_G < 0` contradiction seen with `gamma_hat_c_cp_eff`.
- But the metal-floor quantity is normalized to the metal response, not to an absolute interface reflection coefficient.
- So it should be treated as a cross-check reference, not as a drop-in replacement for the paper headline suppression metric.

## Outputs

- CP metal-floor export: `analysis_stages\paper_code_review_bundle_20260414\results\patch_cp_metal_floor_extracted.csv`
- Same-angle audit: `analysis_stages\paper_code_review_bundle_20260414\results\metal_floor_same_angle_audit.csv`
- Summary table: `analysis_stages\paper_code_review_bundle_20260414\results\metal_floor_same_angle_audit_summary.csv`
