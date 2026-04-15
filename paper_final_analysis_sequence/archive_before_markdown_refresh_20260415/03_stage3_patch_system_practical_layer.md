# Stage 3. Patch System Practical Layer

## Current Status

- An isolated execution workspace now exists at:
  - `analysis_stages/stage3_patch_paper_final_20260414`
- Stage 3 paper-final exports were generated there without modifying the
  original patch stage folders.
- Patch-stage raw CSV inputs are present under:
  - `analysis_stages/patch_cp_stage_system/csv`
  - `analysis_stages/patch_lp_stage_system/csv`
- Current patch scripts exist:
  - `analysis_stages/patch_cp_stage_system/code/gamma_extraction_v2.py`
  - `analysis_stages/patch_lp_stage_system/code/gamma_extraction_lp.py`
- Current repository outputs are mainly figures, not locked extraction tables:
  - CP figures in `analysis_stages/patch_cp_stage_system/results`
  - LP figures in `analysis_stages/patch_lp_stage_system/results`
- Therefore `patch_cp_extracted.csv` and `patch_lp_extracted.csv` are still
  target deliverables in the original stage folders, but they now exist in the
  isolated execution workspace:
  - `analysis_stages/stage3_patch_paper_final_20260414/cp/results/patch_cp_extracted.csv`
  - `analysis_stages/stage3_patch_paper_final_20260414/lp/results/patch_lp_extracted.csv`
- Current angle-grid facts:
  - CP patch M2/M3 grid: `10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 56, 60, 65, 70 deg`
  - LP patch `LP_m3` grid: `10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70 deg`
  - ideal Stage 1 grid is the standard `5 deg` grid, so `56 deg` is not a
    paper-final lock angle and should be dropped during alignment

## Purpose

- Quantify how far the practical patch system sits below the ideal CP upper
  bound.
- Separate system-stage effects from material-only truth.

## Inputs

- CP patch CSV directory:
  - `analysis_stages/patch_cp_stage_system/csv`
- LP patch CSV directory:
  - `analysis_stages/patch_lp_stage_system/csv`
- CP extraction code:
  - `analysis_stages/patch_cp_stage_system/code/gamma_extraction_v2.py`
- LP extraction code:
  - `analysis_stages/patch_lp_stage_system/code/gamma_extraction_lp.py`
- Ideal references from Stages 1 and 2:
  - locked linear truth table
  - locked CP truth table

## Execution

1. Audit M1, M2, and M3 alignment:
   - delay consistency
   - off-boresight angle convention
   - shared theta grid
2. Refactor the CP extraction into a reusable export path:
   - keep existing figures unchanged
   - add a structured export layer for:
     - `Gamma_hat_X_CP_sys`
     - `Gamma_hat_C_CP_raw`
     - `Gamma_hat_C_CP_eff`
     - `R_TE_proxy`
     - `R_TM_proxy`
     - reciprocity diagnostics
     - M3 leakage ratios
   - add CLI arguments for `--csv-dir` and `--output-dir`
3. Re-run the CP patch extraction:

```powershell
python .\analysis_stages\patch_cp_stage_system\code\gamma_extraction_v2.py
```

4. Extend the LP extraction export path:
   - keep existing figures unchanged
   - add a structured export layer for:
     - `R_hat_yy_sys`
     - `R_hat_zz_sys`
     - `R_hat_yz_sys`
     - `R_hat_zy_sys`
     - derived LP `Gamma_X`
     - derived LP `Gamma_C`
   - export both complex values and band-mean magnitudes
5. Re-run the LP patch extraction:

```powershell
python .\analysis_stages\patch_lp_stage_system\code\gamma_extraction_lp.py `
  --csv-dir .\analysis_stages\patch_lp_stage_system\csv `
  --output-dir .\analysis_stages\patch_lp_stage_system\results `
  --with-lp
```

6. Add a paper-lock export layer so the patch stage writes aligned tables:
   - `patch_cp_extracted.csv`
   - `patch_lp_extracted.csv`
7. Align patch outputs to the Stage 1 theta grid:
   - drop `56 deg`
   - keep only angles also present in the ideal lock
   - later Stage 4 filtering still applies the material main ranges
8. Apply only the combined symmetry correction that is supportable from M3.
9. Keep the methods limitation explicit:
   - per-antenna separation is not identifiable from M3 alone

## Planned Work Packages

### WP-1. Input Lock

- Freeze Stage 3 inputs to the current stage-local CSV directories.
- Do not introduce any new simulation exports for Stage 3.
- Record one input manifest note in the results directory so the paper-final
  extraction can be reproduced from the current files only.

### WP-2. CP Export Upgrade

- Convert `gamma_extraction_v2.py` from a figure-only script into:
  - figure generation
  - CSV export
  - summary printout
- Keep the current internal definitions:
  - `Gamma_X` from reciprocity geometric mean
  - `Gamma_C_raw` from `RR`
  - `Gamma_C_corr` from M3 leakage correction
- Export both frequency-resolved and band-mean outputs if practical.
- Minimum required paper-final table is the band-mean table.

### WP-3. LP Export Upgrade

- Extend `gamma_extraction_lp.py` so that the existing LP-direct extraction
  writes a locked table.
- Preserve current leakage terms:
  - `cross_zy`
  - `cross_yz`
- Rename them in the paper-final export as:
  - `R_hat_zy_sys`
  - `R_hat_yz_sys`

### WP-4. Paper-Final Alignment

- Create one row per:
  - material
  - angle
  - stage
- Use the same material naming as Stage 1 and 2:
  - `concrete`
  - `glass`
  - `wood`
  - optional `metal` for calibration/reference only
- Carry enough metadata to allow Stage 4 to merge without ad hoc code.

### WP-5. Stage 3 QA Lock

- Verify that the patch exports can be joined to the ideal tables by:
  - `material`
  - `theta_deg`
- Verify that the LP leakage monitor is present on every main-claim row.
- Emit one short Stage 3 summary note after the CSVs are produced.

## Outputs

- Target CP extraction table:
  - `analysis_stages/patch_cp_stage_system/results/patch_cp_extracted.csv`
- Target LP extraction table:
  - `analysis_stages/patch_lp_stage_system/results/patch_lp_extracted.csv`
- Isolated workspace CP extraction table:
  - `analysis_stages/stage3_patch_paper_final_20260414/cp/results/patch_cp_extracted.csv`
- Isolated workspace LP extraction table:
  - `analysis_stages/stage3_patch_paper_final_20260414/lp/results/patch_lp_extracted.csv`
- Recommended auxiliary artifacts:
  - `analysis_stages/patch_cp_stage_system/results/patch_cp_extracted_freq_resolved.csv`
  - `analysis_stages/patch_lp_stage_system/results/patch_lp_extracted_freq_resolved.csv`
  - `analysis_stages/patch_cp_stage_system/results/STAGE3_SUMMARY.md`
- Isolated workspace summary note:
  - `analysis_stages/stage3_patch_paper_final_20260414/STAGE3_SUMMARY.md`
- Existing figure outputs already useful as staging material:
  - `analysis_stages/patch_cp_stage_system/results/fig3_main_results.png`
  - `analysis_stages/patch_lp_stage_system/results/lp_fig3_suppression_gain.png`

## Recommended Output Schema

### `patch_cp_extracted.csv`

- `material`
- `theta_deg`
- `freq_center_ghz`
- `gamma_hat_x_cp_sys_real`
- `gamma_hat_x_cp_sys_imag`
- `gamma_hat_x_cp_sys_mag`
- `gamma_hat_c_cp_raw_real`
- `gamma_hat_c_cp_raw_imag`
- `gamma_hat_c_cp_raw_mag`
- `gamma_hat_c_cp_eff_real`
- `gamma_hat_c_cp_eff_imag`
- `gamma_hat_c_cp_eff_mag`
- `r_te_proxy_real`
- `r_te_proxy_imag`
- `r_te_proxy_mag`
- `r_tm_proxy_real`
- `r_tm_proxy_imag`
- `r_tm_proxy_mag`
- `xpd_eff_db`
- `reciprocity_dev_db`
- `leakage_lr_rr_db`
- `leakage_rl_ll_db`
- `port_asym_db`
- `use_for_main_claim_candidate`
- `note`

### `patch_lp_extracted.csv`

- `material`
- `theta_deg`
- `freq_center_ghz`
- `r_hat_yy_sys_real`
- `r_hat_yy_sys_imag`
- `r_hat_yy_sys_mag`
- `r_hat_zz_sys_real`
- `r_hat_zz_sys_imag`
- `r_hat_zz_sys_mag`
- `r_hat_yz_sys_real`
- `r_hat_yz_sys_imag`
- `r_hat_yz_sys_mag`
- `r_hat_zy_sys_real`
- `r_hat_zy_sys_imag`
- `r_hat_zy_sys_mag`
- `gamma_x_from_lp_real`
- `gamma_x_from_lp_imag`
- `gamma_x_from_lp_mag`
- `gamma_c_from_lp_real`
- `gamma_c_from_lp_imag`
- `gamma_c_from_lp_mag`
- `leakage_max_db`
- `use_for_main_claim_candidate`
- `note`

## Pass Conditions

- PEC patch `|Gamma_hat_C_CP_eff|` stays within a few dB of ideal PEC
  `|Gamma_C|`.
- Leakage monitors stay below the paper-wide threshold in the main range.
- Patch tables are emitted on the same angle grid and material naming used by
  the ideal stage.
- `56 deg` does not leak into the paper-final join keys.
- Stage 4 can merge the ideal and patch tables without manual spreadsheet work.

## Next Stage Link

- Stage 4 requires the exported CP and LP patch tables from this stage.

## Implementation Note

- The current CP script writes figures only.
- The current LP script writes figures only.
- For paper-final reproducibility, Stage 3 is not complete until the extracted
  numeric tables are written and locked.

## Concrete Execution Order

1. Update `gamma_extraction_v2.py` to support CSV export without changing the
   current figure outputs.
2. Run CP extraction and inspect the emitted `patch_cp_extracted.csv`.
3. Update `gamma_extraction_lp.py` to export LP-direct tables.
4. Run LP extraction and inspect the emitted `patch_lp_extracted.csv`.
5. Join both tables with the Stage 1/2 ideal lock on `material, theta_deg`.
6. Freeze a short Stage 3 summary note and hand off to Stage 4.

## Expected Risk

- Low risk:
  - input CSVs already exist
  - the current scripts already compute most needed quantities
- Medium risk:
  - CP script is not yet structured as a CLI/export pipeline
  - LP angle coverage and `56 deg` mismatch require explicit alignment logic
- Main technical caution:
  - Stage 3 outputs remain system-stage quantities and must not be relabeled as
    material ground truth
