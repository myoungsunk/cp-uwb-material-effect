# Stage 4c Same-Angle Gap Audit

This isolated workspace audits whether the Stage 4b same-angle gap

- `Delta_G(theta) = G_supp_ideal(theta) - G_supp_patch(theta)`

behaves like a physically defensible antenna-limited loss after the LP-anchor
branch lock.

The central question is:

- does the patched effective residual branch stay above the ideal residual
  branch at the same angle
- or does the correction layer over-suppress the residual and break the
  intended upper-bound interpretation

This workspace does not modify Stage 4b. It only audits it.
