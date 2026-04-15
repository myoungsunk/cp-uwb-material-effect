# Stage 4i: EFF Instability Framing

Date: `2026-04-14`

## Purpose

Document why the current `eff` correction

`gamma_c_eff = gamma_c_raw - eps_eff * gamma_x`

is structurally unstable at high angle, and how that should be framed in the paper.

## Core claim

The current `eff` correction is not failing because of a small implementation bug. It is structurally fragile because the subtraction term is large compared with the residual of interest, while `eps_eff = h3_LR / h3_RR` is only a proxy for the true reflection-path leakage.

## Quantitative reason

Using the convention-locked branch mapping:
- patch dominant branch: `gamma_hat_x_cp_sys ~ Gamma_C_ideal`
- patch residual branch: `gamma_hat_c_cp_eff ~ Gamma_X_ideal`

Typical oblique-angle magnitudes are:
- `|gamma_x_cp| ~ |Gamma_C_ideal| ~ 0.4`
- `|eps_eff| ~ 0.4` (about `-7.6 dB` over the 20-60 deg oblique range)
- therefore `|eps_eff * gamma_x| ~ 0.16`

Target residual magnitude is much smaller:
- `|Gamma_X_ideal| ~ 0.05-0.10`

So the correction term is already about `1.6x` to `3.2x` larger than the residual of interest. In that regime, stable subtraction requires very tight complex-phase agreement between:
- the actual leakage embedded in `gamma_c_raw`
- and the LoS-derived proxy `eps_eff * gamma_x`

## Concrete example

`concrete @ 40 deg`
- `|Gamma_X_ideal| = 0.089`
- `|gamma_hat_c_cp_raw| = 0.194`
- `|gamma_hat_c_cp_eff| = 0.033`

This means the corrected residual is smaller than the ideal residual by about:
- `0.089 - 0.033 = 0.056`

Relative to the nominal correction scale `|eps_eff * gamma_x| ~ 0.16`, that is roughly a `35-40%` overshoot. That level of overshoot is consistent with a phase mismatch on the order of only a few tens of degrees; it does not require a catastrophic coding error.

## Metal audit evidence

To test whether `eps_eff` is actually measuring the same leakage that contaminates `gamma_c_raw`, compare:
- `leakage_actual = gamma_c_raw_PEC / gamma_x_PEC`
- `leakage_proxy = h3_LR / h3_RR`

Results from the metal audit show systematic mismatch even inside the main oblique region:
- `20 deg`: magnitude mismatch `-5.26 dB`, phase mismatch `13.58 deg`
- `30 deg`: magnitude mismatch `-4.07 dB`, phase mismatch `11.74 deg`
- `40 deg`: magnitude mismatch `-3.71 dB`, phase mismatch `14.55 deg`
- `50 deg`: magnitude mismatch `-3.96 dB`, phase mismatch `17.48 deg`
- `55 deg`: magnitude mismatch `-3.64 dB`, phase mismatch `20.14 deg`

That is strong evidence that `eps_eff` is not the same complex quantity as the actual reflection-path leakage.

Related files:
- `analysis_stages/stage3_metal_leakage_proxy_audit_20260414/results/metal_leakage_proxy_vs_actual_summary.csv`
- `analysis_stages/stage3_metal_leakage_proxy_audit_20260414/results/metal_leakage_proxy_vs_actual_6p5ghz.csv`

## Low-angle interpretation

The low-angle problem is different. There the issue is not over-correction but floor dominance.

Observed metal floor:
- `|gamma_hat_c_cp_eff| ~ 0.15-0.25`
- about `-17 dB` to `-12 dB`

Meanwhile `|Gamma_X_ideal|` approaches zero near normal incidence. Once the ideal residual falls below the antenna floor, neither `raw` nor `eff` can recover the true residual. That region is information-limited, not correction-limited.

## Practical interpretation

The two tails of the `eff` curve are not equally meaningful:
- low angle: floor-dominated
- high angle: subtraction-dominated

Only a narrower middle region can be treated as potentially informative, and even that region is material-dependent.

## Paper framing

Keep:
- `ideal` as the plane-wave material limit
- `raw` as the primary practical metric
- `eff` as a supplementary de-leakage attempt

Recommended figure annotations:
1. Antenna floor line
   Use the PEC/metal CP residual level as a horizontal floor reference.
   Practical level is roughly `0.15-0.25` in magnitude, or around `-17` to `-12 dB`.

2. High-angle de-leakage uncertainty band
   Use a band derived from a fraction of `|eps_eff * gamma_x|` to visualize subtraction sensitivity.
   A simple working approximation is `0.3 * |eps_eff * gamma_x|`, which represents typical coherence mismatch rather than thermal noise.

This supports the following interpretation:
- `ideal`: material-only upper bound
- `raw`: conservative system-level achievable value
- `eff`: optimistic estimate under stronger phase-coherence assumptions
- floor line: hardware-limited residual ceiling

## Bottom line

The current `eff` path should not be treated as a primary absolute residual estimate. The data support using:
- `raw` for the headline claim
- `eff` only as supplementary context with an explicit instability caveat
