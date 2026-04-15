# Stagewise Analysis Rationale And Interpretation

This note explains why the analysis is split into stages and how each stage
should be interpreted in the current paper-safe workflow.

The integrated CSV copies live under `stage_csv_integrated/`. This note is the
reading guide for those tables and for the active outputs under
`analysis_stages/`.

## Stage 0

- Role:
  - notation lock
- Why it exists:
  - The manuscript, captions, scripts, and CSV exports were using partially
    different branch names.
  - Without a notation lock, the same physical branch can be renamed several
    times across the pipeline and create artificial branch-mismatch problems.
- Current lock:
  - ideal same-hand branch: `Gamma_same` = paper `Gamma_X`
  - ideal flipped-hand branch: `Gamma_flip` = paper `Gamma_C`
  - dominant patch CP branch: `gamma_hat_cross_agm_cp`
  - primary residual patch CP branch: `gamma_hat_rr_raw_cp`
  - supplementary corrected residual: `gamma_hat_rr_leakage_corrected_cp`
  - Stage 3 leakage coefficient: `m3_leakage_lr_over_rr`

## Stage 1

- Role:
  - lock the linear TE/TM truth
- Why it exists:
  - Every later CP result is derived from this linear truth.
  - Fresnel agreement and phase handling must be checked here, before any CP
    interpretation is attempted.
- Reading rule:
  - Treat Stage 1 as the authoritative ideal/material anchor.
  - Treat lock-variant and phase-audit outputs as diagnostic support, not as
    headline evidence.

## Stage 2

- Role:
  - derive ideal CP upper bounds from the locked linear TE/TM truth
- Why it exists:
  - The CP upper bound is not a directly simulated truth table. It is a basis
    transform of the Stage 1 TE/TM truth.
  - This is the point where same-hand and flipped-hand branch meanings must be
    fixed explicitly.
- Current reading rule:
  - `Gamma_same = (R_TE + R_TM) / 2`
  - `Gamma_flip = (R_TE - R_TM) / 2`
  - paper aliases remain:
    - `Gamma_X := Gamma_same`
    - `Gamma_C := Gamma_flip`

## Stage 3

- Role:
  - extract practical patch-system estimators
- Why it exists:
  - The ideal CP bound alone does not tell us what a practical antenna-patch
    system will estimate.
  - This is where leakage, reciprocity deviation, and branch ambiguity enter.
- Current estimator lock:
  - `gamma_hat_cross_agm_cp`:
    - cross-channel AGM estimator built from LR/RL
  - `gamma_hat_rr_raw_cp`:
    - RR-only raw estimator
  - `gamma_hat_rr_leakage_corrected_cp`:
    - RR-only estimator after subtracting
      `m3_leakage_lr_over_rr * gamma_hat_cross_agm_cp`
- Legacy compatibility:
  - `gamma_hat_x_cp_sys` -> `gamma_hat_cross_agm_cp`
  - `gamma_hat_c_cp_raw` -> `gamma_hat_rr_raw_cp`
  - `gamma_hat_c_cp_eff` -> `gamma_hat_rr_leakage_corrected_cp`
  - `eps_eff` -> `m3_leakage_lr_over_rr`

## Stage 3a

- Role:
  - lock the dominant/residual branch interpretation
- Why it exists:
  - The practical estimators do not inherit the ideal branch labels by name.
  - LP-anchor evidence is used to decide which practical estimator tracks the
    ideal residual branch and which tracks the dominant branch.
- Current locked result:
  - `cp_dominant_branch_name = gamma_hat_cross_agm_cp`
  - `cp_residual_branch_name = gamma_hat_rr_raw_cp`
  - `cp_residual_branch_supplementary_name = gamma_hat_rr_leakage_corrected_cp`
- Main-range evidence:
  - LP aligned vote: `29 / 29`
  - patch corrected branch swapped vote: `29 / 29`

## Stage 4

- Role:
  - compute suppression-style paper metrics
- Why it exists:
  - Once ideal and practical branches are both locked, the paper needs a
    same-angle metric that can be reported safely.
- Current reading rule:
  - headline metric uses the raw-primary residual branch
  - corrected residual stays supplementary only
- Reason:
  - `gamma_hat_rr_raw_cp` preserves same-angle ordering against the ideal layer
    on the locked headline set
  - `gamma_hat_rr_leakage_corrected_cp` can over-correct and create
    negative-gap rows

## Stage 5

- Role:
  - extend the interpretation to odd-bounce discussion
- Why it exists:
  - The paper needs a constrained statement about how the single-bounce result
    informs odd-bounce behavior.
- Reading rule:
  - treat this as claim-scope control, not as a new numeric proof stage

## Stage 6

- Role:
  - internal robustness / dispersion sensitivity
- Why it exists:
  - to test whether the 6.5 GHz-centered result collapses immediately under
    band variation
- Reading rule:
  - supplement-side robustness only
  - not a substitute for externally calibrated broadband measurement

## Stage 7

- Role:
  - bind figures and tables to explicit CSV sources
- Why it exists:
  - the manuscript needs a traceable mapping from each figure/table to a locked
    export
- Reading rule:
  - Stage 7 is a binding/export layer
  - it does not change the physical interpretation already decided in Stages
    1 to 4

## Why The Three-Step CP Approach Exists

The CP pipeline is intentionally separated into three logical steps:

1. Ideal truth construction:
   - derive `R_TE`, `R_TM`, then `Gamma_same`, `Gamma_flip`
2. Practical estimator construction:
   - build measurable patch-system estimators from LL/LR/RL/RR
3. Branch interpretation and paper metric lock:
   - decide which practical estimator is dominant or residual, then build the
     final paper-safe suppression metrics

This split is necessary because the ideal CP branches are physics-side objects,
while the practical patch estimators are measurement-side objects. They are
related, but they are not named or ordered identically by construction.

## Current Paper-Safe Reading Rule

1. Read ideal material behavior from Stage 1 and Stage 2.
2. Read practical dominant/residual mapping from Stage 3a.
3. Read headline suppression numbers from Stage 4 raw-primary reporting.
4. Read corrected residual, metal-floor, PEC-based correction, and direct-CP
   sanity only as audit or supplement layers.
