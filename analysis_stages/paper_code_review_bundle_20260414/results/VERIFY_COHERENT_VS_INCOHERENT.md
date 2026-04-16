# Verify Coherent vs Incoherent Band Average

Execution date: `2026-04-16`

## Scope

- Replay from existing Stage 3 frequency-resolved exports only.
- Incoherent band mean: `mean(|x(f)|)`.
- Coherent band mean: `|mean(x(f))|`.
- Materials included: `concrete, glass, wood`.
- Pass criterion: incoherent-coherent gap `>= 1.0 dB`.

## Core Finding

- `2` row(s) crossed the 1 dB threshold; cause #1 is directly evidenced at those rows.
- gamma_c_from_lp: 0/39 row(s) >= 1 dB, mean gap=0.155 dB, max gap=0.578 dB at 40 deg.
- gamma_hat_c_cp_eff: 2/39 row(s) >= 1 dB, mean gap=0.214 dB, max gap=1.016 dB at 40 deg.
- gamma_hat_c_cp_raw: 0/39 row(s) >= 1 dB, mean gap=0.129 dB, max gap=0.411 dB at 10 deg.
- gamma_hat_x_cp_sys: 0/39 row(s) >= 1 dB, mean gap=0.153 dB, max gap=0.552 dB at 40 deg.
- gamma_x_from_lp: 0/39 row(s) >= 1 dB, mean gap=0.161 dB, max gap=0.868 dB at 20 deg.

## Material Rollup

- concrete: 0/65 comparisons >= 1 dB, mean gap=0.012 dB, max gap=0.072 dB.
- glass: 2/65 comparisons >= 1 dB, mean gap=0.310 dB, max gap=1.016 dB.
- wood: 0/65 comparisons >= 1 dB, mean gap=0.165 dB, max gap=0.868 dB.

## Strongest Rows

- glass 40 deg gamma_hat_c_cp_eff: incoherent=-29.170 dB, coherent=-30.186 dB, gap=1.016 dB, flag=True.
- glass 35 deg gamma_hat_c_cp_eff: incoherent=-29.030 dB, coherent=-30.035 dB, gap=1.005 dB, flag=True.
- glass 30 deg gamma_hat_c_cp_eff: incoherent=-24.613 dB, coherent=-25.573 dB, gap=0.960 dB, flag=False.
- wood 20 deg gamma_x_from_lp: incoherent=-35.366 dB, coherent=-36.234 dB, gap=0.868 dB, flag=False.
- glass 25 deg gamma_hat_c_cp_eff: incoherent=-21.716 dB, coherent=-22.373 dB, gap=0.657 dB, flag=False.
- glass 40 deg gamma_c_from_lp: incoherent=-5.345 dB, coherent=-5.923 dB, gap=0.578 dB, flag=False.
- glass 30 deg gamma_x_from_lp: incoherent=-23.612 dB, coherent=-24.182 dB, gap=0.570 dB, flag=False.
- wood 30 deg gamma_hat_c_cp_eff: incoherent=-36.536 dB, coherent=-37.096 dB, gap=0.560 dB, flag=False.
- glass 40 deg gamma_hat_x_cp_sys: incoherent=-5.619 dB, coherent=-6.171 dB, gap=0.552 dB, flag=False.
- glass 10 deg gamma_hat_c_cp_eff: incoherent=-13.965 dB, coherent=-14.448 dB, gap=0.482 dB, flag=False.

## Outputs

- Detail CSV: `analysis_stages\paper_code_review_bundle_20260414\results\audit_coherent_vs_incoherent.csv`
- Variable/material summary CSV: `analysis_stages\paper_code_review_bundle_20260414\results\audit_coherent_vs_incoherent_summary_by_material.csv`
- Material rollup CSV: `analysis_stages\paper_code_review_bundle_20260414\results\audit_coherent_vs_incoherent_material_rollup.csv`
