# Paper Code Review Bundle

This folder centralizes the scripts that were actually used across the Stage 1 to Stage 7 paper-analysis workflow and the later debugging/validation passes.

## Intent

- Keep one flat review copy of the used analysis code.
- Prefix every filename with its stage so code review can follow the pipeline order quickly.
- Preserve the original staged directories untouched.

## Structure

- `code/`: centralized review copies of the used scripts.
- `code_manifest.csv`: source-to-bundle mapping and one-line role summary.

## Notes

- These are review copies, not the original execution locations.
- Each file header includes stage, role, and original source path.
- Stage 1 helper imports were rewritten to the local prefixed filenames so the dependency graph is readable inside this bundle.

## Stage Coverage

- Stage 1: ideal TE/TM truth extraction, projection, QC, and Fresnel sanity check.
- Stage 2: CP basis transform.
- Stage 3: CP/LP patch extraction and LP-anchor branch lock.
- Stage 4: suppression metrics, raw/eff/metal audits, PEC-based correction, direct-CP sanity scripts, and phase-anchor validation.
- Stage 6: UWB dispersion sensitivity.
- Stage 7: final Figure 1 to Figure 4 export.
