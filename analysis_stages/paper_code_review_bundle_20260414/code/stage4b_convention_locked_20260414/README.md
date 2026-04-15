# Stage 4b Convention-Locked

This isolated workspace reruns the headline suppression analysis after the CP
branch mapping is explicitly locked by the LP-derived bridge.

Differences from Stage 4a:

- ideal residual branch is fixed to `Gamma_X`
- patch residual branch is fixed to `cp_residual_branch`
- patch dominant branch is fixed to `cp_dominant_branch`
- headline reporting range starts at `20 deg` to exclude the small-angle
  polarization-basis artifact

The original `analysis_stages/stage4_suppression_dual_20260414` workspace is
preserved as the Stage 4a small-branch audit trail.
