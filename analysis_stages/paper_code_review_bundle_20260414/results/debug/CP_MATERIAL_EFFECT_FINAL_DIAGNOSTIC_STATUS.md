# CP Material Effect - Final Diagnostic Status

Execution date: `2026-04-16`

## Context

Stage 1/2 ideal TE/TM suppression gain upper bound that appeared smaller than the LP-derived and CP-derived gain curves has now been fully diagnosed.

This note is the diagnostic closure summary. The remaining work is no longer root-cause diagnosis; it is a production-path decision on which corrective path, if any, should be promoted into the paper pipeline.

---

## Final Result Summary

| Branch | Locked baseline | After diagnostic fix | Root cause | Status |
| --- | --- | --- | --- | --- |
| LP | `15/23` below ideal | `0/23` after same-angle metal normalization | Reference normalization mismatch between pure Fresnel truth and antenna-system patch ratios | **RESOLVED** |
| CP raw | `0/23` below ideal | N/A | N/A | **CLEAN** |
| CP eff | `16/23` below ideal | `3/23` on the band replay, `2/23` at `6.5 GHz` with ideal-target material-specific `eps` replay | Shared `eps_eff` correction-model mismatch | **ROOT CAUSE IDENTIFIED** |

---

## Completed Diagnostic Items

### Category 1 - Code Improvements

- `C1 + C6`: unified authoritative ordering table using the Stage 4e schema
- `C2`: coherent vs incoherent band-average audit
- code fixes:
  - `stage_4_build_specular_rx_direct_cp_reanalysis.py` argparser bug
  - `stage_4_audit_eff_mechanism.py` default path fix
- Stage 3 export refresh:
  - same-stage numerator fields
  - `*_abs_of_mean` and `*_mean_of_abs` semantics
- gap decomposition added to the authoritative export:
  - numerator mismatch
  - residual mismatch
  - full gap terms

### Category 3 - Verification

- `V1`: coherent vs incoherent replay
  - not the dominant cause
  - max gap `1.016 dB`
  - only `2/23` rows exceed `1 dB`
- `V2`: single-frequency grid replay at `6.24 / 6.50 / 6.74 GHz`
  - band averaging eliminated as the sole explanation
- `V3`: estimator round-trip
  - angle-resolved identity exact
  - `13/13` pass
- LP metal normalization
  - `15/23 -> 0/23`
  - Fresnel agreement `0.17-0.38 dB`
- cross-pol contamination
  - high-angle limiter only
  - main-range Pearson `0.389`
- Stage 1 PEC truth
  - main-range clean at `6.50 GHz`
  - TE `0/11`, TM `0/13` above threshold
- `eps` drift replay
  - shared-model mismatch confirmed
  - mean magnitude bias `-1.50 dB`
  - median phase drift `29.34 deg`
- slab sensitivity replay
  - residual stays inside the `eps_r +/-10%`, thickness `+/-5 mm` envelope
- `2x2` calibration prototype
  - numerically feasible
  - condition number roughly `1.3-1.6`

### Additional Analysis

- `A1`: material-specific `eps` replay
  - locked `16/23`
  - ideal-target replay `3/23` band, `2/23` at `6.5 GHz`
  - current `< 5/23` pass criterion satisfied
- `A2`: CP metal-normalized extension
  - independent verifier reproduces the locked branch with max diff `4.441e-16`
  - `0/23` negative rows
  - but `23/23` rows remain larger than ideal
  - diagnostic-only, not production-safe
- `A3`: consolidated residual budget
  - paper-ready diagnostic budget table completed

---

## Eliminated Causes

1. Band averaging is not the dominant cause.
   max gap `1.016 dB`, only `2/23` rows exceed `1 dB`.
2. Estimator algebra is not the cause.
   round-trip identity is exact at angle-resolved reference, `13/13` pass.
3. Cross-pol contamination is not the main-range driver.
   it is a high-angle limiter only.
4. Stage 1 PEC truth is not the main-range cause at `6.50 GHz`.
   TE `0/11`, TM `0/13` above threshold.
5. Slab parameter sensitivity is not the main contradiction.
   observed deviation remains inside the uncertainty envelope.

## Confirmed Causes

1. LP branch:
   reference normalization mismatch between broadside/patch-system normalization and pure Fresnel truth.
   same-angle metal normalization removes the contradiction.
2. CP eff branch:
   shared `eps_eff` correction-model mismatch.
   material-specific ideal-target replay reduces `16/23` to `3/23`.

---

## Diagnostic Closure State

- LP: resolved
- CP raw: clean
- CP eff: root cause identified
- Diagnostic phase: complete

The next step is not more diagnosis. The next step is a production-path decision.

---

## Remaining Production Decisions

1. Whether same-angle metal normalization should be promoted into the Stage 3 LP production path.
2. Whether material-specific `eps_eff` should be promoted into the Stage 3 CP production path.
3. Whether the `2x2` calibration path should be developed as the medium-term unified alternative.
4. Whether manuscript headline `G_supp_db` values should be changed.
5. How to resolve the bookkeeping mismatch between locked `stage4f` and the refreshed shared-eff replay.
   current largest mismatch: `glass 50 deg`, magnitude diff `0.191417`.

---

## Key Output Files

- `results/debug/RESIDUAL_BUDGET_FINAL.md`
- `results/debug/APPLIED_MODIFICATION_STATUS.md`
- `results/debug/VERIFY_CP_EFF_MATERIAL_SPECIFIC_EPS.md`
- `results/debug/VERIFY_CP_METAL_NORMALIZED_EXTENSION.md`
- `results/debug/VERIFY_LP_METAL_NORMALIZED.md`
- `results/debug/VERIFY_LP_CROSSPOL_CONTAMINATION.md`
- `results/debug/VERIFY_STAGE1_PEC_TRUTH_ACCURACY.md`
- `results/debug/VERIFY_FRESNEL_SLAB_SENSITIVITY.md`
- `results/debug/VERIFY_ESTIMATOR_ROUNDTRIP.md`
- `results/debug/PROTOTYPE_2X2_CALIBRATION.md`
