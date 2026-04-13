# Debugging Note

This file is the persistent debugging note for this folder.

Use this note as the canonical place to record:

- confirmed assumptions
- stage-specific interpretation rules
- debugging findings and their evidence
- repeatable debugging procedure
- unresolved items and next checks

## 0. Current Short Summary

### 2026-04-12 corrected `z_p` rerun (`a12_corr`)

- `actual_center5x5` manifest is now deleted from the active ideal-stage
  config because that dataset was confirmed as a wrong-extraction case.
- Active scattered-stage manifests are now grouped under:
  - `analysis_stages/ideal_te_tm_scattered_stage/config/current_manifests`
- Current rerun outputs from that grouped manifest set are now stored under:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/current_manifest_runs`
- Previous wide-grid `z_p` exports were taken from the wrong coordinates, so the
  earlier transmission-side validation is retired as a geometry-error case.
- The corrected export set was re-ingested from scratch under:
  - `analysis_stages/ideal_te_tm_scattered_stage/csv/raw/a12_corr`
- The corrected manifest is:
  - `analysis_stages/ideal_te_tm_scattered_stage/config/current_manifests/manifest_a12_corr.csv`
- The corrected results are:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/a12_corr_full/truth_table_linear.csv`
  - `analysis_stages/ideal_te_tm_scattered_stage/results/a12_corr_full/qc_report.csv`
- Current grouped-manifest rerun check:
  - `manifest_a12_corr.csv` rerun succeeded
  - `manifest_actual_new_runs_20260412.csv` rerun succeeded
  - `manifest_actual_new_runs_20260412.csv` is now locked to `field_type=scattered`
    for every row
  - both current manifests now exclude high-angle `TE PEC`:
    - `case=pec`, `pol=TE`, `theta_deg >= 80`
  - both keep baseline residuals at about `1e-5 ~ 1e-4`
  - high-angle `TE PEC` is retired from active PEC sanity-check use
  - the earlier gap between `a12_corr` and `actual_new_runs_20260412` at
    `theta=80/85 deg` remains a debug history item, not an active validation
    target
  - current interpretation:
    - the `__total__` label in those TE PEC filenames is treated as an
      export/report-label issue
    - the dataset still remains debug-only, not the material truth source

Current locked interpretation:

- baseline reconstruction is now clean again:
  - `baseline_residual_over_incident ~= 8.3e-6 ~ 1.22e-4`
- the coordinate error is therefore no longer the dominant blocker
- TM PEC behavior improves substantially for `kobs = 1, 2`
- TE PEC transmission residual still remains large at high angle, so the main
  unresolved issue is **not** fixed by the `z_p` coordinate correction alone
- the corrected dataset also revealed a pipeline requirement:
  - different `w_plane / l_plane / k_obs` runs must stay separated by
    `run_label`
  - grouping only by `(case, pol, rect, theta, kobs)` is invalid for this set
- TE PEC `80/85 deg` existing-report re-extracts are now archived under:
  - `analysis_stages/ideal_te_tm_scattered_stage/csv/raw/te_pec_existing_reports_80_85_20260412`
- current judgment on those added TE PEC re-extracts:
  - the previous exact duplicate-block symptom is gone inside the newly
    re-extracted `Near_E_Table_1/2` high-angle blocks
  - `Near_E_Table_3` and `Near_E_Table_3_1` are only dedicated subset exports
    of `Near_E_Table_1/2` at `kobs=2, w_plane=500 mm`
  - the new re-extracts do **not** directly replace the active merged TE PEC
    scattered CSV
  - the dominant `Ey` component becomes much closer only after a global sign
    flip (`new ~= -old`), so report-definition / sign-convention lock remains
    open
- TE PEC + TE baseline report-lock bundle is now archived under:
  - `analysis_stages/ideal_te_tm_scattered_stage/csv/raw/te_lock_0413`
- the report-lock bundle keeps the following mapping fixed:
  - `Near_E_Table_3 = z_m`
  - `Near_E_Table_3_1 = z_p`
  - both are `scattered`
- new baseline comparator judgment:
  - correct-surface comparison against the active merged baseline is relatively
    close
  - direct and sign-flipped comparisons are nearly identical at both
    `80 deg` and `85 deg`
  - this currently isolates the sign / report-definition ambiguity to the
    TE PEC re-extract path, not to the whole TE export chain
- `te_lock_0413` sanity check is now materialized under:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/te_lock_0413/SANITY_CHECK.md`
  - `analysis_stages/ideal_te_tm_scattered_stage/results/te_lock_0413/sanity_check.json`
- current sanity-check verdict:
  - baseline comparator path: `PASS`
  - PEC duplicate removal: `PASS`
  - PEC sign/report-definition shift still present: `PASS`
  - promotion of the new PEC re-extracts into the active truth source: `FAIL`
- additional lock from coefficient sensitivity check:
  - for the TE PEC path, treating `z_p` as a local-CS export rotated by `180 deg`
    about global `y` does **not** change the extracted `Gamma / R / T` values
  - therefore the current old/new **TE** discrepancy cannot be explained by a
    simple `global vs local` basis reinterpretation on `z_p`
  - the dominant coefficient-level difference remains on the transmission side,
    not on the reflection side

When future debugging is done in this folder, append the new result here and
update the affected stage README only when the folder scope or interpretation
changes.

## 1. Folder-Level Rules

- `patch_cp_stage_system` is the CP patch-inclusive system stage.
- `patch_lp_stage_system` is the LP patch-inclusive system stage.
- `ideal_te_tm_stage` is the ideal plane-wave / material-stage pipeline.
- `ideal_te_tm_scattered_stage` is the ideal plane-wave / material-stage
  pipeline for HFSS scattered-field exports.
- Patch-stage outputs must not be promoted to intrinsic material truth unless
  separately validated against the ideal/material stage.
- This note is the first debugging reference before editing code or
  reinterpreting results.

## 2. Confirmed Conventions

### Geometry / metadata

- CSV `theta_r` is treated as wall-normal incidence angle `theta_i`.
- `_R` means reflection case.
- `_T` means transmission case.

### HFSS material values

- `concrete`: `eps_r = 5.24`, `tan_d = 0.105`, `conductivity = 0`
- `glass`: `eps_r = 6.31`, `tan_d = 0.019`, `conductivity = 0`
- `wood`: `eps_r = 1.99`, `tan_d = 0.049`, `conductivity = 0`
- `metal`: existing `PEC`, do not overwrite material properties
- wall thickness: `0.1 m`

### Actual unfolded M3 setup

The actual M3 setup is:

- `TX' = (0, 2 y_w, 0)`, boresight `+x`
- `RX  = (d, 0, 0)`, boresight `-x`, fixed in place

This means:

- the previous `RX moved to (d, 2 y_w, 0)` wording is not the real setup
- `RX` sees `+y`-side arrival in both `M2` and `M3`
- the `M2/M3` azimuthal hemisphere flip happens on the `TX` side

## 3. Current Interpretation Lock

### CP stage

- `Gamma_X` is the most robust primary result.
- `Gamma_C` is an antenna-limited, first-order corrected co-term.
- CP-derived `R_TE` / `R_TM` are patch-based derived proxies, not material
  truth.

### LP stage

- LP `metal-plate` normalization is the most reliable TE/TM reference.
- LP `M3` is useful for comparison, but `R_TM` shows systematic bias.
- Current evidence supports using LP metal-normalized TE/TM as ground truth for
  validating CP calibration limits.

### Ideal stage

- Ideal plane-wave truth table is the material/slab stage.
- Primary outputs are `R_TE`, `T_TE`, `R_TM`, `T_TM`.
- CP transform is second-stage / optional, not the first output.
- Ideal stage must use the local plane-of-incidence projector, not the LP
  patch-stage port projection.
- If the HFSS export mode is `Scattered from SBR+ Regions`, use
  `ideal_te_tm_scattered_stage` and not `ideal_te_tm_stage`.

## 4. Debugging Findings So Far

### 4.1 Patch-stage vs material-stage separation

Finding:

- patch-stage outputs were initially too easy to read as reflection
  coefficients
- this interpretation was reduced to patch-stage system metrics

Decision:

- keep patch and ideal stages separated
- keep labels conservative

Status:

- active interpretation rule

### 4.2 CP cross-term vs co-term

Finding:

- `Gamma_X` is stable and matches LP-derived cross behavior well
- co-term remains the main source of error

Evidence:

- CP-derived `R_TE` and `R_TM` deviate from Fresnel with opposite-sign paired
  error
- `Gamma_X` itself stays comparatively well-behaved

Decision:

- report `Gamma_X` as the main CP result
- report `Gamma_C` as first-order corrected, antenna-limited

### 4.3 LP metal-plate vs LP M3

Finding:

- LP metal-plate calibration agrees with Fresnel theory at about `+/- 0.3 dB`
- LP M3-unfolded shows systematic `R_TM` overestimation of roughly `+1 ~ +3 dB`

Decision:

- use LP metal-plate as TE/TM ground truth
- keep LP M3 as comparison / diagnostic path

### 4.4 Actual cause of LP M3 `R_TM` bias

Previous assumption:

- mismatch was described as an RX-side azimuthal asymmetry effect

Corrected interpretation:

- under the real M3 setup, the mismatch is more correctly explained by
  TX-side `yz`-plane pattern asymmetry
- `M2`: TX radiates into `+y` hemisphere
- `M3`: TX radiates into `-y` hemisphere

Decision:

- use TX-side azimuthal hemisphere flip as the canonical explanation

### 4.5 `y-port` vs TM basis

Finding:

### 4.13 `CP_global_test_copy_20260412_152206` project audit

Source:

- `D:/codex/ansys_automation/downloads/remote_project_CP_global_test_copy_20260412_152206.zip`

Finding:

- the relevant ideal-stage designs inside this copied AEDT are internally
  configured with specular observation coordinate systems:
  - `z_smaller_0 -> RelativeCS1`
  - `z_larger_0 -> RelativeCS2`
- this is true for:
  - `0.TE_PEC`
  - `0.TM_PEC`
  - `1.TE_baseline`
  - `1.TM_baseline`
  - `2.TE_*`
  - `2.TM_*`
- the only block that still uses:
  - `z_larger_0 -> Global`
  is the composite design:
  - `BOTH`
- the copied project therefore does **not** support the earlier simplified
  claim that the active ideal PEC / baseline / material designs were exporting
  `z_p` from a global plane

Geometry evidence:

- `RelativeCS1`:
  - `Origin = (z_obs*sin(theta_k), 0, -z_obs*cos(theta_k))`
  - `Euler ZXZ = (Psi, Theta, Phi) = (270deg, 180deg-theta_k, 90deg)`
- `RelativeCS2`:
  - `Origin = (z_obs*sin(theta_k), 0, +z_obs*cos(theta_k))`
  - `Euler ZXZ = (Psi, Theta, Phi) = (270deg, theta_k, 90deg)`
- under the current HFSS Euler interpretation used in this audit:
  - local `y` stays aligned with global `y`
  - `RelativeCS1` local `z` becomes `(-sin(theta_k), 0, -cos(theta_k))`
  - `RelativeCS2` local `z` becomes `(-sin(theta_k), 0, +cos(theta_k))`
- therefore:
  - `RelativeCS1` XY plane is perpendicular to the reflected specular ray
  - `RelativeCS2` XY plane is perpendicular to the transmitted specular ray

Field-type evidence:

- in the copied AEDT itself, the relevant ideal-stage designs are saved as:
  - `FieldType='ScatteredFields'`
- this is consistent for the PEC / baseline / material ideal-stage designs

Export-path finding:

- the original `2026-04-11` 5x5 batch exporter
  - `hfss_export_center_grid_job.py`
  uses direct geometry contexts:
  - `z_m -> z_smaller_0`
  - `z_p -> z_larger_0`
  and does **not** depend on existing report names
- the later existing-report re-extracts use:
  - `Near_E_Table_*`
  as a separate path
- the later rerun log
  - `D:/codex/ansys_automation/downloads/CP_global_test_copy_new_runs_20260412_161830/hfss_export_new_runs.log`
  labels `0.TE_PEC` outputs as `total`, even though the copied AEDT stores
  `0.TE_PEC` as `ScatteredFields`

Decision:

- current priority moves away from
  - "the copied ideal project itself has the wrong `z_p` plane"
- current priority moves toward
  - export-path / report-definition / labeling mismatch
- the copied AEDT should be treated as geometry-consistent for the relevant
  ideal-stage designs unless contradicted by a separate direct HFSS export
  check

Archived detailed note:

- `analysis_stages/ideal_te_tm_scattered_stage/results/project_copy_20260412_geometry_audit.md`

- `y-port = TM` is not exact in basis language
- the accurate statement is that `y-port` couples exclusively to TM with a
  geometric projection factor proportional to `sin(theta_i)`

Key result:

- in ratio-based calibration, that projection factor cancels to first order
- therefore the good LP metal accuracy does not contradict `y-hat != u_TM`

Decision:

- use this wording in notes and methods:
  - `The y-polarized port couples exclusively to the TM component with a geometric projection factor proportional to sin(theta_i), which cancels in the ratio-based calibration.`

### 4.6 Ideal stage TE/TM projector

Finding:

- the ideal stage must not inherit the LP patch-stage port interpretation
- TE/TM there must be defined from the local incidence plane

Decision:

- use `e_TE = normalize(n x k_i)`
- use `e_TM,q = e_TE x k_q`
- keep PEC sign lock explicit and configurable

### 4.7 Corrected `z_p` dataset does not close the TE PEC problem

Finding:

- after replacing the mislocated `z_p` exports with the corrected set, baseline
  QC becomes clean but the high-angle TE PEC transmission residual remains

Evidence:

- corrected baseline residual:
  - about `8.3e-6 ~ 1.22e-4`
- TE PEC:
  - `|T_TE|` still stays large at high angle
  - examples:
    - `70 deg, kobs=0.5`: about `0.333`
    - `75 deg, kobs=1`: about `0.414`
    - `80 deg, kobs=2`: about `1.691`
    - `85 deg, kobs=2`: about `1.324`
- TM PEC:
  - improves strongly with larger `kobs`
  - examples:
    - `70 deg, kobs=1`: `|R_TM|-1 ~= 0.019`, `|T_TM| ~= 0.048`
    - `75 deg, kobs=1`: `|R_TM|-1 ~= 0.026`, `|T_TM| ~= 0.053`
    - `80 deg, kobs=2`: `|R_TM|-1 ~= 0.090`, `|T_TM| ~= 0.093`

Decision:

- treat the old `z_p` issue as a real coordinate bug that has now been removed
- keep the corrected `a12_corr` dataset as the active verification set for this
  branch of ideal-stage debugging
- do **not** claim that the TE PEC problem was caused only by the old `z_p`
  coordinates
- continue TE PEC diagnosis from the corrected dataset, not from the retired one

### 4.8 TE high-angle duplicate blocks are real and outrank the PEC-physics interpretation

Finding:

- the uploaded TE high-angle merged CSV blocks contain exact duplicate
  field payloads across different `kobs` / `w_plane` labels
- this makes the current TE high-angle cross-run comparison unfit for direct
  physical interpretation

Evidence:

- verified in merged CSVs:
  - `0.TE_PEC__z_p.csv`
  - `0.TE_PEC__z_m.csv`
  - `1.TE_baseline__z_p.csv`
  - `1.TE_baseline__z_m.csv`
- examples:
  - in `0.TE_PEC__z_p.csv`, `theta = 80 deg`:
    - `kobs=0.5`, `kobs=2`, and `kobs=8` blocks have identical complex
      `Ex/Ey/Ez` payloads even when coordinates differ
  - in `0.TE_PEC__z_p.csv`, `theta = 80 deg`:
    - `500 mm` and `1000 mm` blocks at the same `kobs=2` are exactly identical
      in both coordinates and field values
  - the same duplicate pattern repeats at `theta = 85 deg`
  - the same duplicate pattern also appears in:
    - `0.TE_PEC__z_m.csv`
    - `1.TE_baseline__z_p.csv`
    - `1.TE_baseline__z_m.csv`
- contrast:
  - `0.TM_PEC__z_p.csv` and `0.TM_PEC__z_m.csv` do **not** show the same
    duplicate pattern
- raw source nuance:
  - the problematic raw CSVs are not byte-identical files
  - so the duplicate effect is confirmed in the exported/normalized field
    content, but not yet pinned to one single layer such as:
    - raw export generation
    - file curation / folder mix
    - parser normalization

Decision:

- promote TE high-angle duplicate detection above the current PEC-physics
  interpretation in the debugging priority
- do **not** use current TE high-angle cross-`kobs` or cross-`w_plane`
  comparisons as physical evidence
- keep the scalar estimator itself as lower-risk:
  - it still reproduces the uploaded TE center-patch values consistently
  - therefore the first suspect is no longer the scalar estimator formula
  - current priority order:
    1. TE high-angle duplicate / export-normalization issue
    2. field-type / HFSS report-definition lock
    3. only then finite PEC grazing TE physics

### 4.9 TE PEC 80/85 existing-report re-extracts remove the duplicate symptom but do not yet close the report-definition issue

Finding:

- additional TE PEC `80/85 deg` existing-report exports were copied into the
  stage-local raw folder and rechecked
- these new files no longer show the old exact duplicate-block pattern across
  different `kobs / w_plane` settings
- however, the new `kobs=2, w_plane=500 mm` high-angle blocks do not directly
  match the active merged TE PEC scattered CSV
- the dominant `Ey` component is much closer only after a global sign flip
  (`new ~= -old`)

Evidence:

- archived raw copy:
  - `analysis_stages/ideal_te_tm_scattered_stage/csv/raw/te_pec_existing_reports_80_85_20260412`
- reproducible comparison script:
  - `analysis_stages/ideal_te_tm_scattered_stage/code/compare_extra_te_pec_existing_reports.py`
- result summary:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/te_pec_existing_reports_80_85_20260412/SUMMARY.md`
  - `analysis_stages/ideal_te_tm_scattered_stage/results/te_pec_existing_reports_80_85_20260412/comparison_summary.json`
- locked numerical checks:
  - `Near_E_Table_1.csv` and `Near_E_Table_2.csv` are byte-identical across the
    `80-folder` and `85-folder`
  - `Near_E_Table_3 == Near_E_Table_1(theta=80/85, kobs=2, w_plane=500 mm)`
  - `Near_E_Table_3_1 == Near_E_Table_2(theta=80/85, kobs=2, w_plane=500 mm)`
  - no exact duplicate block pairs remain inside the new `Near_E_Table_1/2`
    focus blocks
  - `Near_E_Table_1` and `Near_E_Table_2` are not identical:
    - `80 deg, kobs=2, 500 mm`: `max_abs ~= 0.214`, `mean_abs ~= 0.0367`
    - `85 deg, kobs=2, 500 mm`: `max_abs ~= 0.125`, `mean_abs ~= 0.0250`
  - sign-check against active merged `0.TE_PEC__z_p.csv`:
    - `80 deg`: direct `Ey mean_abs ~= 1.487`, negated-old `mean_abs ~= 0.113`
    - `85 deg`: direct `Ey mean_abs ~= 0.792`, negated-old `mean_abs ~= 0.0557`

Decision:

- treat the new TE PEC `80/85 deg` existing-report exports as a **debug-only
  comparator**, not as a replacement for the active TE PEC scattered dataset
- refine the priority order:
  1. old merged TE high-angle duplicate-block issue
  2. new existing-report sign / report-definition ambiguity
  3. only after that, finite-PEC grazing-TE physics

Follow-up:

- lock whether the new existing-report exports correspond to the same scattered
  quantity with a flipped sign, or to a different HFSS report definition
- determine which of `Near_E_Table_1/2` corresponds to `z_m` vs `z_p`
- only after that, decide whether these re-extracts should be promoted into the
  active ideal-stage TE PEC validation path

### 4.10 TE baseline existing-report comparator makes the current sign ambiguity look PEC-specific

Finding:

- TE baseline `80/85 deg` existing-report exports were added as a matching
  comparator beside the TE PEC re-extracts
- the mapping was locked from the user-provided report correspondence:
  - `Near_E_Table_3 = z_m`
  - `Near_E_Table_3_1 = z_p`
  - both are `scattered`
- unlike the TE PEC re-extracts, the new baseline comparator does **not** show
  a strong global sign-flip preference against the active merged baseline CSV

Evidence:

- combined raw bundle:
  - `analysis_stages/ideal_te_tm_scattered_stage/csv/raw/te_lock_0413`
- reproducible comparison code:
  - `analysis_stages/ideal_te_tm_scattered_stage/code/compare_te_report_lock_0413.py`
- result summary:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/te_lock_0413/SUMMARY.md`
  - `analysis_stages/ideal_te_tm_scattered_stage/results/te_lock_0413/comparison_summary.json`
- locked baseline checks on the correct surface mapping:
  - `80 deg`, `z_m`: direct `Ey mean_abs ~= 0.09142`, negated-old `~= 0.09145`
  - `80 deg`, `z_p`: direct `Ey mean_abs ~= 0.06623`, negated-old `~= 0.06622`
  - `85 deg`, `z_m`: direct `Ey mean_abs ~= 0.03842`, negated-old `~= 0.03843`
  - `85 deg`, `z_p`: direct `Ey mean_abs ~= 0.03222`, negated-old `~= 0.03221`
- these direct / negated differences are effectively the same order, unlike the
  TE PEC re-extracts where the sign-flipped comparison is much smaller

Decision:

- keep the TE PEC sign / report-definition ambiguity isolated as a **PEC-path
  issue** until proven otherwise
- do **not** generalize the PEC sign behavior into a blanket TE export sign
  rule
- keep `te_lock_0413` as the compact raw + result bundle for this report-lock
  debug path

Follow-up:

- when new TE baseline or TE PEC re-extracts arrive, append them into
  `te_lock_0413` first
- compare baseline before reinterpreting any PEC sign behavior
- only after a common field-definition lock is proven, decide whether the new
  PEC re-extracts should replace any active merged dataset

### 4.11 `te_lock_0413` sanity check locks the current decision boundary

Finding:

- a dedicated sanity-check layer was added on top of the combined
  `te_lock_0413` comparison result
- the sanity check converts the current numeric evidence into explicit
  `PASS / FAIL` decisions

Evidence:

- sanity-check code:
  - `analysis_stages/ideal_te_tm_scattered_stage/code/sanity_check_te_report_lock_0413.py`
- sanity-check outputs:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/te_lock_0413/SANITY_CHECK.md`
  - `analysis_stages/ideal_te_tm_scattered_stage/results/te_lock_0413/sanity_check.json`
- locked verdicts:
  - baseline correct-surface closeness to active merged baseline: `PASS`
  - baseline no-global-sign-flip preference: `PASS`
  - PEC duplicate-block removal in the new focus blocks: `PASS`
  - PEC subset report consistency (`Table3/3_1` vs parent tables): `PASS`
  - PEC sign/report-definition shift relative to active merged PEC CSV:
    `PASS` as a detected issue
  - promotion of the new PEC re-extracts into the active truth source: `FAIL`

Decision:

- use `te_lock_0413` as a valid sanity-check gate before any reinterpretation
  of the high-angle TE report path
- do **not** promote the new PEC re-extracts into the active dataset yet
- keep the active interpretation:
  - baseline path is healthy enough to act as a comparator
  - PEC path still contains a separate sign/report-definition ambiguity

Follow-up:

- any future TE PEC rerun should first be checked against this sanity-check
  gate
- only after the PEC sign/report-definition shift disappears should promotion
  into the active truth source be considered

### 4.12 TE PEC coefficient sensitivity check: `z_p` local/global reinterpretation does not explain the old/new TE gap

Finding:

- the old/new TE PEC difference was rechecked at the extracted coefficient
  level, not only at the raw pointwise field level
- under the user-provided assumption:
  - `z_m` uses the same coordinate-system basis
  - only `z_p` may differ by a local coordinate system
- a test was run with the standard global interpretation and with an
  alternative `z_p local` interpretation modeled as a `180 deg` rotation about
  global `y`:
  - `Ex -> -Ex`
  - `Ey -> Ey`
  - `Ez -> -Ez`

Evidence:

- the wide existing-report CSV header contains `_u / _v / Freq / k_obs / theta_k
  / w_plane`, but no explicit coordinate-system tag, so CSV alone does not
  prove whether the exported components are global or local
- the active merged old PEC files reconstruct absolute `x,y,z` from geometry;
  for example at `80 deg, kobs=2, w_plane=500 mm`:
  - old `z_m` sample points lie near `x ~= 0.0891 m`, `z ~= -0.0259 m`
  - old `z_p` sample points lie near `x ~= 0.0926 m`, `z ~= +0.00617 m`
- coefficient sensitivity on the active old PEC dataset (`a12_corr`, `80/85 deg,
  kobs=2`):
  - TE:
    - `R_mag` unchanged
    - `T_mag` unchanged
    - exact difference `0.0`
  - TM:
    - `80 deg`: `T_mag 0.0927 -> 1.9100`
    - `85 deg`: `T_mag 0.2685 -> 1.7331`
- old active TE PEC vs new TE PEC re-extract:
  - `80 deg`:
    - old `R_mag ~= 0.754`
    - new `R_mag ~= 0.732`
    - old `T_mag ~= 1.691`
    - new `T_mag ~= 0.534`
  - `85 deg`:
    - old `R_mag ~= 0.382`
    - new `R_mag ~= 0.409`
    - old `T_mag ~= 1.324`
    - new `T_mag ~= 0.721`
  - under the alternative `z_p local` assumption, the new TE values remain
    unchanged because TE uses the `Ey` component, which is invariant under this
    `y`-axis flip model

Decision:

- for the **TE PEC** path, the current old/new discrepancy is **not**
  explained by a simple `global vs local` reinterpretation of the `z_p`
  exported components
- coefficient-level evidence partially supports that the dominant mismatch is
  still on the transmission side:
  - reflection magnitude changes only by about `0.02 ~ 0.03`
  - transmission magnitude changes by about `0.60 ~ 1.16`
- therefore:
  - if the issue is on `z_p`, it is not merely a basis relabeling problem
  - it is more consistent with a different extracted field content, plane
    placement, or report-definition path on transmission

Follow-up:

- if TE is the current target, prioritize transmission-side report/plane checks
  over local/global basis reinterpretation
- if TM is revisited later, local/global basis handling on `z_p` becomes
  critical because TM changes strongly under the same assumption

## 5. Standard Debugging Procedure

Use this order unless there is a strong reason not to.

1. Confirm metadata first.
   - check `theta_r`, `_R`, `_T`, material assignment, thickness
2. Confirm geometry and basis.
   - verify actual M1/M2/M3 setup
   - verify whether the issue is on TX side, RX side, or both
3. Check antenna diagnostics / Phase 0.
   - leakage
   - port asymmetry
4. Compare LP metal-plate against Fresnel.
   - this is the first trust anchor
5. Compare LP M3 against LP metal.
   - isolate M3 geometry or pattern mismatch
6. Compare CP `Gamma_X` against LP-derived cross-equivalent quantity.
   - confirm whether cross-term is still trustworthy
7. Inspect CP co-term separately.
   - do not infer TE/TM validity from `Gamma_X` alone
8. Update this note.
   - add finding
   - add evidence
   - add decision
   - note whether interpretation changed

## 6. What To Record For Future Debugging

Append future sessions under this section using the template below.

### Session: 2026-04-12 High-Angle Ideal Rerun (`kobs = 0.5, 1, 2`)

- Date:
  - `2026-04-12`
- Stage:
  - `ideal_te_tm_scattered_stage`
- Input set / files:
  - `analysis_stages/ideal_te_tm_scattered_stage/csv/raw/actual_new_runs_20260412`
  - source export:
    - `D:/codex/ansys_automation/downloads/CP_global_test_copy_new_runs_20260412_161830/cp_global_test_copy_new_runs_exports`
- Symptom:
  - verify whether larger observation distance resolves the PEC `z_p`
    transmission residual at high incident angle
- Checks performed:
  - copied flat exports into the stage-local raw folder
  - added flat-manifest generation
  - extended stage code to support:
    - per-file `field_type` (`total` / `scattered`)
    - per-file `observation_distance_lambda_scale`
    - mixed TE/TM field modes in a single dataset
  - reran truth-table extraction on `theta = 70, 75, 80, 85 deg`,
    `kobs = 0.5, 1, 2`
  - checked baseline residual on both `z_m` and `z_p`
- Key evidence:
  - baseline residual stayed very small:
    - TE: about `9e-6 ~ 4e-5`
    - TM: about `9e-5 ~ 1.1e-4`
  - therefore the mixed-field interpretation and analytic reconstruction are
    behaving correctly
  - PEC TM improved with larger `kobs`:
    - `|T_TM|`:
      - `theta=75 deg`: `0.382 -> 0.053 -> 0.089`
      - `theta=80 deg`: `0.595 -> 0.243 -> 0.093`
      - `theta=85 deg`: `0.792 -> 0.619 -> 0.269`
    - `|R_TM|`:
      - `theta=70 deg`: `0.837 -> 1.019 -> 1.023`
      - `theta=75 deg`: `0.622 -> 0.974 -> 0.954`
      - `theta=80 deg`: `0.409 -> 0.758 -> 0.910`
  - PEC TE did not materially improve with larger `kobs`:
    - `|T_TE|` remained about `0.32 ~ 0.74`
    - `|R_TE|` still deviated strongly from 1, especially for `theta >= 80 deg`
  - TM fit residuals improved with larger `kobs`
  - TE transmission residual improved only slightly, and TE reflected fit
    residual remained large
  - `z_p` full-map diagnostics were generated:
    - `TE_z_p_total_norm_overview.png`
    - `TE_z_p_fit_residual_norm_overview.png`
    - `TM_z_p_total_norm_overview.png`
    - `TM_z_p_fit_residual_norm_overview.png`
  - map interpretation:
    - TE:
      - transmitted residual is broad across the whole aperture
      - edge-to-center ratio stays near `1.0`
      - `incident_corr_residual ~= 0.99+`
      - `residual_pw_fit_scalar ~= 0.07 ~ 0.14`
      - therefore the TE residual is a coherent forward / plane-wave-like term,
        not an edge-only signature
    - TM:
      - residual is much more sensitive to `kobs`
      - at `kobs = 1, 2` and lower `theta`, the residual also becomes strongly
        coherent with the forward plane wave and much smaller
      - high-angle TM still shows localized hot spots, but the dominant issue is
        far weaker than TE
- Root cause:
  - increasing observation distance reduces part of the TM shadow / near-region
    contamination
  - but the dominant TE PEC transmission residual is not explained by
    `z_obs = 0.5 lambda` alone
  - the remaining TE issue is likely a systematic forward coherent term tied to
    finite-plate / shadow / SBR field behavior, not to baseline reconstruction
    error
- Decision:
  - keep the new manifest-driven mixed-field support
  - treat the current rerun as confirmation that `kobs` increase alone is not
    sufficient to clean up TE PEC transmission at high angle
  - use the full-map result to separate:
    - TM: mostly boundary / shadow-region behavior
    - TE: aperture-wide residual behavior
- next rerun should prioritize TE-specific diagnosis, not just larger `kobs`

### Session: 2026-04-12 Corrected `z_p` coordinate rerun (`a12_corr`)

- Date:
  - `2026-04-12`
- Stage:
  - `ideal_te_tm_scattered_stage`
- Input set / files:
  - source export set:
    - `D:/codex/ansys_automation/downloads/cp_global_test_copy_all_available_exports/*`
  - copied under stage-local raw folder:
    - `analysis_stages/ideal_te_tm_scattered_stage/csv/raw/a12_corr`
  - manifest:
    - `analysis_stages/ideal_te_tm_scattered_stage/config/manifest_a12_corr.csv`
  - results:
    - `analysis_stages/ideal_te_tm_scattered_stage/results/a12_corr_full/truth_table_linear.csv`
    - `analysis_stages/ideal_te_tm_scattered_stage/results/a12_corr_full/qc_report.csv`
- Symptom:
  - earlier `z_p` data had wrong coordinates, so the transmission-side
    validation had to be rebuilt from the corrected export set
- Checks performed:
  - copied the corrected dataset into the stage-local raw folder
  - updated the wide-manifest parser to support:
    - `theta_k`
    - optional `k_obs`
    - `z_m1 / z_p1` prefixes
    - headers with extra tokens such as material thickness strings
  - updated the build pipeline so that each file stays separated by
    `run_label`
  - reran the full scattered-stage truth-table build on the corrected manifest
- Key evidence:
  - generated outputs:
    - manifest rows: `216`
    - normalized samples: `363096`
    - linear truth rows: `40`
    - QC rows: `558`
  - baseline residual is now clean:
    - about `8.301e-6 ~ 1.219e-4`
  - PEC TM is materially improved for `kobs = 1, 2`
  - PEC TE still remains problematic at high angle
  - examples from `truth_table_linear.csv`:
    - `theta=70 deg, kobs=1`: `R_TM ~= 1.019`, `T_TM ~= 0.048`
    - `theta=75 deg, kobs=1`: `R_TM ~= 0.974`, `T_TM ~= 0.053`
    - `theta=80 deg, kobs=2`: `R_TM ~= 0.910`, `T_TM ~= 0.093`
    - `theta=80 deg, kobs=2`: `T_TE ~= 1.691`
    - `theta=85 deg, kobs=2`: `T_TE ~= 1.324`
  - some high-distance / large-aperture runs are partial:
    - several `1000 mm` or `kobs=8` rows contain TE only and have no usable TM
      pair in the final truth table
- Root cause:
  - the earlier transmission-plane failure did include a real coordinate error
  - but after removing that error, the remaining TE PEC residual is still too
    large to attribute to coordinates alone
  - the corrected dataset therefore shifts the active root-cause target from
    `z_p` geometry error to TE-specific field behavior under the current finite
    PEC / SBR setup
- Decision:
  - use `a12_corr` as the active corrected verification dataset
  - keep `run_label` as a required grouping key for this dataset family
  - retire the old wrong-`z_p` transmission conclusions
  - keep the conclusion that high-angle TE PEC transmission is still unresolved
- Affected files / notes:
  - `analysis_stages/ideal_te_tm_scattered_stage/code/generate_hfss_wide_manifest.py`
  - `analysis_stages/ideal_te_tm_scattered_stage/code/io_adapter.py`
  - `analysis_stages/ideal_te_tm_scattered_stage/code/build_truth_table.py`
  - `analysis_stages/ideal_te_tm_scattered_stage/code/qc.py`
  - `analysis_stages/ideal_te_tm_scattered_stage/code/cp_transform.py`
  - this debugging note
- Follow-up:
  - focus the next ideal-stage debugging step on TE-specific PEC behavior
  - do not reuse the old mislocated `z_p` exports for any further conclusion

### Session Template

- Date:
- Stage:
- Input set / files:
- Symptom:
- Checks performed:
- Key evidence:
- Root cause:
- Decision:
- Affected files / notes:
- Follow-up:

### Session 2026-04-10 - New M3 replacement rerun

- Date: 2026-04-10
- Stage: `patch_cp_stage_system`, `patch_lp_stage_system`
- Input set / files:
  - `analysis_stages/patch_cp_stage_system/csv/m3_off-boresigjt.csv`
  - `analysis_stages/patch_lp_stage_system/csv/m3_off-boresigjt.csv`
  - `analysis_stages/patch_lp_stage_system/csv/LP_m3_off-boresigjt.csv`
- Symptom:
  - user provided new CP/LP M3 files and requested rerun and gamma evaluation
- Checks performed:
  - reran CP patch-stage pipeline
  - reran LP patch-stage pipeline with LP-direct enabled
  - compared CP `Gamma_X` against LP-direct `Gamma_X`
  - compared CP corrected co-term against LP-direct `Gamma_C`
  - compared LP-direct `R_TE` / `R_TM` against Fresnel theory
- Key evidence:
  - CP Phase 0 changed to:
    - A1 worst about `-10.0 dB`
    - A2 worst about `3.95 dB`
  - new CP M3 improves leakage magnitude relative to the old very-low-angle case,
    but introduces strong port asymmetry
  - CP vs LP `Gamma_X` deviation stayed moderate:
    - concrete: `-1.08 ~ +0.41 dB`
    - glass: `-1.08 ~ +0.42 dB`
    - wood: `-1.06 ~ +1.59 dB`
  - CP vs LP co-term deviation became large:
    - concrete mean about `11.07 dB`
    - glass mean about `11.21 dB`
    - wood mean about `9.16 dB`
  - LP-direct vs Fresnel with the new LP M3:
    - concrete `R_TE`: about `-1.22 ~ +0.66 dB`
    - concrete `R_TM`: about `+0.57 ~ +3.11 dB`
    - glass `R_TE`: about `-1.19 ~ +0.99 dB`
    - glass `R_TM`: about `+0.68 ~ +3.51 dB`
    - wood `R_TE`: about `-3.17 ~ +1.84 dB`
    - wood `R_TM`: about `-0.94 ~ +3.90 dB`
  - LP cross isolation is now fairly clean even at high angle:
    - around `-22.9 dB / -21.7 dB` at `70 deg`
  - CP XPD zero-cross moved to:
    - concrete near `56 deg`

### Session 2026-04-12 - Ideal 5x5 export field-type lock

- Date: 2026-04-12
- Stage: `ideal_te_tm_stage`, `ideal_te_tm_scattered_stage`
- Input set / files:
  - `D:/codex/ansys_automation/downloads/CP_global_test_center5x5_pipeline/20260411_104056/cp_global_test_exports_center5x5_freqall`
  - actual 5x5 manifest and normalized dumps
- Symptom:
  - ideal-stage PEC / baseline interpretation did not match the expected
    material-stage behavior
- Checks performed:
  - verified actual rect mapping:
    - `z_m = reflection`
    - `z_p = transmission`
  - inspected user HFSS screenshot for field export option
  - computed baseline `||E_scat|| / ||E_inc||` on both planes and both
    polarizations
- Key evidence:
  - HFSS export option was `Field Type = Scattered from SBR+ Regions`
  - baseline scattered ratio stayed near zero:
    - TE / refl: about `3.68e-05 ~ 1.25e-04`
    - TE / trans: about `3.55e-05 ~ 1.11e-04`
    - TM / refl: about `1.07e-04 ~ 1.27e-04`
    - TM / trans: about `1.04e-04 ~ 1.12e-04`
- Root cause:
  - the original ideal-stage pipeline interpreted `E_scat` as `E_total`
- Decision:
  - keep the old total-field pipeline untouched
  - create `ideal_te_tm_scattered_stage` for scattered-field exports
  - use these reconstruction rules there:
    - reflection plane: `E_refl = E_scat`
    - transmission plane: `E_trans,total = E_inc + E_scat`
    - baseline QC: `||E_scat|| / ||E_inc||`
- Affected files / notes:
  - `analysis_stages/ideal_te_tm_scattered_stage/*`
  - `analysis_stages/README.md`
  - this debugging note
- Follow-up:
  - rerun the scattered-stage truth-table extraction and inspect PEC / baseline
    QC there instead of the old total-field stage

### Session 2026-04-12 - Scattered-stage first full run

- Date: 2026-04-12
- Stage: `ideal_te_tm_scattered_stage`
- Input set / files:
  - `analysis_stages/ideal_te_tm_scattered_stage/csv/raw/actual_center5x5_20260411`
  - `analysis_stages/ideal_te_tm_scattered_stage/config/manifest_actual_center5x5.csv`
- Symptom:
  - new scattered-field stage needed to be verified on the actual 5x5 export set
- Checks performed:
  - generated stage-local manifest
  - ran full truth-table build with CP transform
  - inspected baseline QC and PEC sanity outputs
- Key evidence:
  - output generated successfully:
    - `truth_table_linear.csv`
    - `truth_table_cp.csv`
    - `qc_report.csv`
  - baseline scattered QC is clean and all `ok`
  - baseline `||E_scat|| / ||E_inc||` stayed near `1e-4`
  - PEC reflection magnitude is now near the expected unit magnitude after
    phase lock
  - PEC transmission still shows non-negligible residual in part of the sweep,
    so the field-type interpretation is fixed but PEC sanity is not yet fully
    closed
- Root cause:
  - not a stage construction failure; this is the next physical / export-side
    debugging target after the field-type mismatch was removed
- Decision:
  - keep `ideal_te_tm_scattered_stage` as the canonical path for the current
    HFSS export mode
  - use baseline QC from this stage as the confirmed reference
  - treat PEC transmission residual as an active follow-up item
- Affected files / notes:
  - `analysis_stages/ideal_te_tm_scattered_stage/*`
  - this debugging note
- Follow-up:
  - inspect why PEC `T` is not sufficiently close to zero after total-field
    reconstruction on `z_p`

### Session 2026-04-12 - PEC transmission residual root-cause split

- Date: 2026-04-12
- Stage: `ideal_te_tm_scattered_stage`
- Input set / files:
  - `analysis_stages/ideal_te_tm_scattered_stage/results/actual_center5x5_20260411_full/truth_table_linear.csv`
  - `analysis_stages/ideal_te_tm_scattered_stage/results/actual_center5x5_20260411_full/qc_report.csv`
  - `D:/codex/ansys_automation/downloads/CP_global_test_center5x5_pipeline/20260411_104056/CP_global_test.aedt`
- Symptom:
  - PEC `T` remained non-negligible even after switching to scattered-field
    reconstruction
- Checks performed:
  - computed baseline reconstructed transmission on `z_p`
  - compared PEC `T` magnitude and fit residual by angle / polarization
  - inspected AEDT geometry variables and near-field setup definitions
- Key evidence:
  - baseline reconstructed transmission is effectively perfect:
    - TE: `|T| ≈ 1.0000`, fit `≈ 0`
    - TM: `|T| ≈ 1.0000`, fit `≈ 0`
  - this closes the transmission-plane geometry / basis / phase-reference
    question
  - current physical setup in AEDT is finite:
    - wall width / height: `100 mm`
    - `z_obs = 0.5 * lambda(6.5 GHz) ≈ 23.1 mm`
    - transmission near rectangle width / length: `20 mm`
  - corresponding Fresnel number is about `2.35`, so the transmission plane is
    still in the near-field diffraction region
  - PEC transmitted field shows two distinct regimes:
    - `TE, 10 deg`: small `|T|` but large fit residual
      - example mean `|T_TE| ≈ 0.0785`, fit `≈ 0.178`
      - interpretation: weak residual field, not well represented by one plane wave
    - `TE, 70 deg`: large `|T|` with low fit residual
      - mean `|T_TE| ≈ 0.3616`, fit `≈ 0.031`
      - interpretation: coherent forward shadow / edge-diffracted field, not a coding error
    - `TM, 70 deg`: much smaller transmitted field
      - mean `|T_TM| ≈ 0.0668`, fit `≈ 0.054`
- Root cause:
  - the remaining PEC `T` issue is not caused by scattered-to-total
    reconstruction
  - current evidence points to finite-size PEC edge diffraction plus the very
    near observation distance
- Decision:
  - treat baseline `T ≈ 1` as the transmission-plane correctness lock
  - use PEC `R` for phase/sign locking
  - do not treat `PEC T ≈ 0` as a strict pass/fail criterion for this finite
    setup
- Affected files / notes:
  - `analysis_stages/ideal_te_tm_scattered_stage/README.md`
  - this debugging note
- Follow-up:
  - if a stricter PEC-zero-transmission sanity check is required, rerun with
    either:
    - much larger PEC plane, or
    - larger `z_obs`, or
    - both

### Session 2026-04-12 - `w_plane` design mapping correction

- Date: 2026-04-12
- Stage: `ideal_te_tm_scattered_stage`
- Input set / files:
  - `D:/codex/ansys_automation/downloads/CP_global_test_center5x5_pipeline/20260411_104056/CP_global_test.aedt`
- Symptom:
  - previous interpretation used `w_plane = 100 mm` as if it applied to the
    export designs
- Checks performed:
  - mapped every `VariableProp('w_plane', ...)` occurrence to the enclosing
    `HFSSModel Name=...`
- Key evidence:
  - `Name='BOTH'` uses `w_plane = 100 mm`
  - export designs use:
    - `0.TE_PEC`: `w_plane = (100*5) mm`
    - `0.TM_PEC`: `w_plane = (100*5) mm`
    - `2.TE_concrete`: `w_plane = (100*5) mm`
    - `2.TE_glass`: `w_plane = (100*5) mm`
    - `2.TE_wood`: `w_plane = (100*5) mm`
    - `2.TM_concrete1`: `w_plane = (100*5) mm`
    - `2.TM_glass1`: `w_plane = (100*5) mm`
    - `2.TM_wood1`: `w_plane = (100*5) mm`
  - baseline designs use:
    - `1.TE_baseline`: `w_plane = 1 mm`
    - `1.TM_baseline`: `w_plane = 1 mm`
  - `z_obs` remains `0.5 * lambda` in the design-specific blocks
- Root cause:
  - the first `HFSSModel` block (`BOTH`) was read too early and incorrectly
    generalized to the actual export designs
- Decision:
  - retire the earlier `100 mm PEC` explanation
  - treat all exported PEC / material runs as `500 mm` wall cases
  - keep `0.5 lambda` as the active `z_obs` interpretation
- Affected files / notes:
  - this debugging note
- Follow-up:
  - reinterpret the remaining PEC transmission residual under the corrected
    `500 mm, 0.5 lambda` setup
    - glass near `60 deg`
    - wood near `45 deg`
  - suppression using LP-direct worst reflection over CP corrected co-term
    collapsed to only a few dB in the main angle range:
    - concrete `25-45 deg`: about `3.6 ~ 4.7 dB`
    - glass `25-45 deg`: about `3.7 ~ 5.1 dB`
    - wood `25-45 deg`: about `2.9 ~ 3.5 dB`
- Root cause:
  - new CP M3 is acceptable for cross-term tracking but not for stable co-term
    interpretation
  - the strong A2 failure means the new CP M3 introduces a large TX/RX port
    imbalance into the unfolded reference
  - LP M3 remains geometrically usable, but `R_TM` still carries the known
    systematic bias relative to metal-plate calibration
- Decision:
  - keep using the new M3 only with a split interpretation
  - `Gamma_X` remains usable with caution
  - CP co-term, derived `R_TE/R_TM`, and suppression-gain claims should not be
    finalized from this new CP M3 alone
  - LP metal-plate remains the TE/TM ground truth
  - LP M3 remains a diagnostic / comparison path, not the primary truth path
- Affected files / notes:
  - stage-local M3 CSV files replaced
  - rerun results written to stage `results` folders
  - this debugging note updated
- Follow-up:
  - if suppression gain is the target claim, prefer LP metal-plate truth with
    CP cross-term discussion separated from CP co-term claims
  - investigate why the new CP M3 port asymmetry is roughly `2 to 4 dB`
    instead of near-symmetric

### Session 2026-04-10 - Active pipeline restored to OLD M3

- Date: 2026-04-10
- Stage: `patch_cp_stage_system`, `patch_lp_stage_system`
- Input set / files:
  - restored active CP M3 from:
    - `E:\\0. CP Antenna\\0. TRACK2_3_SIM\\ANTENNA_SOURCE\\csv\\m3_off-boresigjt.csv`
  - restored active LP M3 from:
    - `E:\\0. CP Antenna\\0. TRACK2_3_SIM\\ANTENNA_SOURCE\\csv\\LP_m3_off-boresigjt.csv`
  - preserved the new M3 files in stage-local backups:
    - `m3_off-boresigjt.NEW.csv`
    - `LP_m3_off-boresigjt.NEW.csv`
- Symptom:
  - new M3 improved A1 and `LR ~= RL`, but caused severe A2 failure and
    collapsed suppression-gain interpretation
- Checks performed:
  - restored old M3 files into active stage-local CSV paths
  - reran CP patch-stage pipeline
  - reran LP patch-stage pipeline
- Key evidence:
  - restored CP Phase 0:
    - A1 worst about `-4.1 dB`
    - A2 worst about `0.09 dB`
  - restored reciprocity deviation:
    - about `0.00 to 0.09 dB`
  - restored CP XPD behavior:
    - concrete reaches about `22.6 dB` near `35 deg`
    - glass reaches about `23.6 dB` near `40 deg`
    - wood reaches about `22.8 dB` near `30 deg`
  - restored CP-vs-theory pattern again matches the previous interpretation:
    - cross-term plausible
    - co-term still limited but not catastrophically inflated
  - LP M3 remains less trustworthy than LP metal-plate, but the overall
    patch-stage comparison returns to the previously usable regime
- Root cause:
  - the reciprocity estimator already handles `LR != RL` through the geometric
    mean form
  - sacrificing A2 to force `LR = RL` is the wrong trade
  - port symmetry is more critical than exact LR/RL equality for the current
    CP M3 estimator chain
- Decision:
  - OLD M3 is the active standard for this folder
  - NEW M3 is archived only as a comparison/debug case
  - active claims should be based on OLD M3 + LP metal-plate truth
- Affected files / notes:
  - active stage-local M3 CSV files restored
  - new M3 preserved as `.NEW.csv` backups
  - results folders regenerated from OLD M3
  - this debugging note updated
- Follow-up:
  - if a future M3 redesign is attempted, preserve A2 first
  - do not prefer a candidate M3 only because it improves A1 or `LR = RL`
    unless A2 stays near the old level

### Session 2026-04-12 - Actual HFSS ideal-stage 5x5 export integrated and evaluated

- Date: 2026-04-12
- Stage: `ideal_te_tm_stage`
- Input set / files:
  - source export set:
    - `D:\\codex\\ansys_automation\\downloads\\CP_global_test_center5x5_pipeline\\20260411_104056\\cp_global_test_exports_center5x5_freqall`
  - copied under stage-local raw folder:
    - `analysis_stages\\ideal_te_tm_stage\\csv\\raw\\actual_center5x5_20260411`
  - generated manifest:
    - `analysis_stages\\ideal_te_tm_stage\\config\\manifest_actual_center5x5_20260411.csv`
  - normalized dump:
    - `analysis_stages\\ideal_te_tm_stage\\csv\\normalized\\actual_center5x5_20260411_normalized_measurements.csv`
  - full-run outputs:
    - `analysis_stages\\ideal_te_tm_stage\\results\\actual_center5x5_20260411_full\\truth_table_linear.csv`
    - `analysis_stages\\ideal_te_tm_stage\\results\\actual_center5x5_20260411_full\\truth_table_cp.csv`
    - `analysis_stages\\ideal_te_tm_stage\\results\\actual_center5x5_20260411_full\\qc_report.csv`
- Code / pipeline changes made:
  - added HFSS wide-grid raw CSV support to `ideal_te_tm_stage`
  - added actual export manifest generator:
    - `analysis_stages\\ideal_te_tm_stage\\code\\generate_hfss_wide_manifest.py`
  - added wide-grid geometry helpers:
    - `_u -> local TE`
    - `_v -> -local TM`
    - observation center from `0.5 * lambda`
    - source phase origin from `-100 mm` along `k_i`
  - fixed `apply_pec_phase_lock()` to use `pivot()` instead of complex-breaking
    `pivot_table(..., aggfunc='first')`
- Run summary:
  - manifest rows: `140`
  - normalized samples: `1,753,500`
  - linear truth rows: `14,028`
  - QC rows: `183,366`
- Checks performed:
  - subset PEC 10 deg run to validate wide parser and point reconstruction
  - subset baseline 10 deg run to test analytic incident compatibility
  - full 140-row manifest run with optional CP transform output
- Key evidence:
  - baseline analytic-incident compatibility failed completely:
    - `baseline_mismatch_vector ~= 1.0` for all baseline rows
    - min about `0.999878`
    - max about `1.000106`
  - PEC sanity check failed for the assumed transmitted plane:
    - `|T_TE|` spans about `0.848 to 1.309`
    - `|T_TM|` spans about `0.854 to 1.134`
    - expected behavior for a validated ideal-stage PEC case would be `T ~= 0`
  - PEC reflection magnitudes are also not locked near `1`:
    - `pec_abs_R_TE_minus_1` spans about `0.104 to 1.247`
    - `pec_abs_R_TM_minus_1` spans about `0.019 to 0.898`
    - example at `theta = 10 deg`, `f = 6.24 GHz`:
      - `|R_TE| ~= 1.93`
      - `|R_TM| ~= 1.90`
      - `|T_TE| ~= 0.95`
      - `|T_TM| ~= 0.97`
  - fit residuals are only partially acceptable:
    - reflected fit residual about `0.014 to 0.386`
    - transmitted fit residual about `0.001 to 0.980`
  - observed baseline fields are on the order of `1e-4`, not unit-amplitude
    incident fields, so the present export convention does not match the current
    analytic-incident assumption
- Interpretation:
  - the importer and manifest generation are working
  - the actual HFSS export set itself does **not** satisfy the current ideal-stage
    physical assumptions
  - the most likely unresolved causes are:
    - HFSS report field convention mismatch:
      - total vs scattered vs another SBR-specific field normalization
    - `z_p` not being a valid transmitted observation plane under the current
      design / export setup
    - per-design coordinate-system differences inside the AEDT file
- Decision:
  - keep the wide-grid importer and generated manifest as the standard path for
    future actual ideal exports
  - keep the copied dataset under `ideal_te_tm_stage/csv/raw/actual_center5x5_20260411`
  - treat `actual_center5x5_20260411_full` outputs as **diagnostic only**
  - do **not** use this run as the material/slab truth table for paper claims
    until the HFSS field convention and `z_p` plane definition are explicitly
    locked
- Follow-up:
  - verify whether the exported near fields are total fields or scattered fields
  - lock the real geometry / coordinate-system definition of `z_m` and `z_p` for
    each exported design
  - rerun a PEC-only validation after that lock:
    - require `|R| ~= 1`
    - require `|T| ~= 0`
    - require baseline mismatch near `0`
  - only after the above, promote ideal-stage `R_TE / R_TM / T_TE / T_TM` to
    actual truth-table status

## 7. Active Open Items

- HFSS / SBR polarization basis convention still needs an explicit lock when
  comparing CP-derived quantities at the material stage.
- CP co-term still has an irreducible antenna-limited interpretation issue.
- Ideal stage now has a real manifest-connected HFSS wide-grid input path, but
  the actual export convention is still not validated well enough to use the
  outputs as material truth tables.
