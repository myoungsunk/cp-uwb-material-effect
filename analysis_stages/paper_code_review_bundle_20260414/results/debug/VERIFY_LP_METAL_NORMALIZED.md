# Verify LP Metal-Normalized Replay

Execution date: `2026-04-16`

## Scope

- No new simulation is used.
- LP correction is the existing metal-anchor prototype:
  - `R_TE_metal(theta,f) = h_tilde_zz(material, theta, f) / h_tilde_zz(metal, theta, f)`
  - `R_TM_metal(theta,f) = h_tilde_yy(material, theta, f) / h_tilde_yy(metal, theta, f)`
  - `Gamma_X_metal(theta,f) = 0.5 * (R_TE_metal + R_TM_metal)`
- Ideal anchor remains the existing Stage 1/2 `6.5 GHz` truth used by the current Stage 4 audit.
- Main-range rows follow the current Stage 4 filter: `20 deg <= theta <= VALID_MAX(material)`.

## Main Results

- Original LP below-ideal count, band export: `15/23`
- Original LP below-ideal count, `6.5 GHz`: `15/23`
- Metal-normalized LP below-ideal count, band export: `0/23`
- Metal-normalized LP below-ideal count, `6.5 GHz`: `0/23`

## Fresnel Agreement In Main Range

- concrete: max `|R_TE|` deviation `0.166 dB`, max `|R_TM|` deviation `0.239 dB`
- glass: max `|R_TE|` deviation `0.275 dB`, max `|R_TM|` deviation `0.293 dB`
- wood: max `|R_TE|` deviation `0.256 dB`, max `|R_TM|` deviation `0.380 dB`

## Interpretation

- The metal-anchor correction removes the LP residual undershoot that caused the current `15/23` ordering violation pattern.
- In the current data, the LP issue behaves like a reference-normalization mismatch, not like a broken estimator identity.
- This remains an empirical correction prototype. It is evidence for the mechanism, not yet the formal Stage 3/4 production path.

## High-Angle Limits

- concrete 65 deg: `R_TE` dev=+0.21 dB, `R_TM` dev=+0.02 dB, `zy/zz`=-21.9 dB, `yz/yy`=4.9 dB
- concrete 70 deg: `R_TE` dev=+0.18 dB, `R_TM` dev=+0.83 dB, `zy/zz`=-20.1 dB, `yz/yy`=-1.0 dB
- glass 65 deg: `R_TE` dev=+0.28 dB, `R_TM` dev=+0.09 dB, `zy/zz`=-23.3 dB, `yz/yy`=-1.2 dB
- glass 70 deg: `R_TE` dev=+0.14 dB, `R_TM` dev=+1.21 dB, `zy/zz`=-20.8 dB, `yz/yy`=4.3 dB
- wood 50 deg: `R_TE` dev=+0.45 dB, `R_TM` dev=-0.16 dB, `zy/zz`=-23.5 dB, `yz/yy`=-2.6 dB
- wood 55 deg: `R_TE` dev=+0.13 dB, `R_TM` dev=+4.48 dB, `zy/zz`=-20.8 dB, `yz/yy`=10.5 dB
- wood 60 deg: `R_TE` dev=+0.02 dB, `R_TM` dev=+0.88 dB, `zy/zz`=-18.9 dB, `yz/yy`=-2.4 dB

## Outputs

- Full replay CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_lp_metal_normalized_full.csv`
- Summary CSV: `analysis_stages\paper_code_review_bundle_20260414\results\debug\verify_lp_metal_normalized_summary.csv`
