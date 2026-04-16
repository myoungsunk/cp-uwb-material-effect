# Stage 2-3 Code Review (2026-04-15)

Scope:
- `analysis_stages/paper_code_review_bundle_20260414/code/stage_2_cp_transform.py`
- `analysis_stages/paper_code_review_bundle_20260414/code/stage_3_cp_patch_extraction.py`
- `analysis_stages/paper_code_review_bundle_20260414/code/stage_3_lp_patch_extraction.py`
- `analysis_stages/paper_code_review_bundle_20260414/code/stage_3_export_cp_patch_stage3.py`
- `analysis_stages/paper_code_review_bundle_20260414/code/stage_3_export_lp_patch_stage3.py`
- `analysis_stages/paper_code_review_bundle_20260414/code/stage_3_verify_lp_anchor_branch_lock.py`

## Verdict

Stage 2 is still numerically simple and not the main bug source. The active risk remains concentrated in Stage 3.

The current priority order is:

1. Stage 3 branch alias export still hard-locks the corrected branch as the residual branch.
2. Stage 3 corrected residual still subtracts an LoS leakage proxy from a reflection-path contamination term.
3. Stage 3 geometric-mean sign selection still relies on a phase anchor that earlier audits already showed to be systematically mis-phased.
4. Stage 2 naming is still convention-ambiguous even though the transform itself is algebraically correct.

## Findings

### 1. Active P1: Stage 3 alias export still promotes the corrected branch as the residual branch

Reference:
- `stage_3_verify_lp_anchor_branch_lock.py:191-194`
- `stage_3_verify_lp_anchor_branch_lock.py:227-235`

Implemented behavior:
- `cp_residual_branch_name = "gamma_hat_c_cp_eff"`
- `cp_residual_branch_mag = gamma_hat_c_cp_eff_mag`

Why this is risky:
- The paper-safe conclusion was already switched to `raw-primary`.
- The same-angle audit showed that the corrected branch is the one that violates the ideal upper-bound ordering.
- If downstream Stage 4 or figure code reads the alias columns instead of the explicit raw columns, the old over-corrected path can silently return as the default residual definition.

Assessment:
- This is no longer a naming-only issue.
- It is a concrete propagation risk because the alias columns look authoritative.

### 2. Active P1: `eps_eff = h3["LR"] / h3["RR"]` is still a structural mismatch for reflective leakage subtraction

Reference:
- `stage_3_cp_patch_extraction.py:222-225`
- `stage_3_export_cp_patch_stage3.py:132, 140-143`
- same reuse in `stage_3_lp_patch_extraction.py:299-301`

Implemented model:
- `eps_eff = h3["LR"] / h3["RR"]`
- `gamma_c_eff = gamma_c_raw - eps_eff * gamma_x`

Why this is risky:
- `h3` is a LoS M3 measurement.
- `gamma_c_raw` contains leakage embedded in the reflection path.
- Earlier metal-proxy and Stage 4 audits already showed a magnitude bias of a few dB and a phase drift of roughly `10-20 deg`, which is more than enough to over-subtract when the correction term is of the same order as the raw residual.

Assessment:
- This is still the main physical reason the corrected branch cannot be promoted to the headline residual.

### 3. Active P1: the geometric-mean sign rule is still tied to a mis-phased anchor

Reference:
- `stage_3_cp_patch_extraction.py:72-84`
- `stage_3_cp_patch_extraction.py:196-197`
- same reuse in `stage_3_export_cp_patch_stage3.py:138-139`
- same reuse in `stage_3_lp_patch_extraction.py:99-111, 296-297`

Implemented logic:
- `candidate = sqrt(|ratio|) * exp(j * angle(ratio)/2)`
- flip sign if `|angle(candidate / anchor)| > pi/2`

Why this is risky:
- Earlier audit already showed the current anchor is nearly quadrature to the candidate, not phase-aligned to it.
- In that situation, the sign choice is not being made against a same-physics reference.

Assessment:
- This remains an unresolved convention bug, not just a numerical nuisance.
- LP-direct remains useful because it bypasses this path, but the CP extractor itself is still not convention-locked at the complex level.

### 4. Active P2: Stage 2 transform is algebraically fine, but the output naming is still convention-ambiguous

Reference:
- `stage_2_cp_transform.py:136-179`

Implemented behavior:
- outputs only `Gamma_X` and `Gamma_C`
- final note says: `CP convention should still be checked explicitly.`

Why this is risky:
- The transform formula itself is fine.
- But the output file still does not label which branch is same-hand and which is flipped-hand.
- For PEC rows, the practical interpretation is already clear from the numbers: the dominant branch is `Gamma_C`, not `Gamma_X`.

Assessment:
- This is the easiest place for downstream branch swap to reappear.
- The Stage 2 file should not be treated as self-describing in its current form.

## Not A Primary Bug

### Stage 2 transform itself

Reference:
- `stage_2_cp_transform.py:136-137`

Assessment:
- `Gamma_X = 0.5 * (R_TE + R_TM)`
- `Gamma_C = 0.5 * (R_TE - R_TM)`

This is still just a linear basis transform. No branch cut or calibration bug is introduced here.

### `h_tilde = h2 - m1`

Reference:
- `stage_3_cp_patch_extraction.py:173-178`
- `stage_3_export_cp_patch_stage3.py:136-137`
- `stage_3_export_lp_patch_stage3.py:150-153`

Assessment:
- This is still a modeling assumption, not a proven implementation bug.
- It remains worth documenting because the code does not prove that direct coupling is invariant between M1 and M2.
- But it is not the strongest current explanation for the observed over-correction.

## Recommended next fixes

1. Change the Stage 3 alias export so the authoritative residual alias points to `gamma_hat_c_cp_raw`, not `gamma_hat_c_cp_eff`.
2. Keep `gamma_hat_c_cp_eff` as a supplementary corrected estimate only.
3. Add same-hand / flipped-hand alias columns to Stage 2 CP output, plus a PEC sanity assert.
4. Keep LP-direct as the branch-lock reference path until a direct CP one-point sanity run closes the complex convention.
