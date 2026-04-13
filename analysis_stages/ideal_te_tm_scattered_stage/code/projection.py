from __future__ import annotations

import numpy as np

from geometry import GeometryConfig, te_basis, tm_basis


def projection_basis(theta_deg: float, pol: str, mode: str, geom: GeometryConfig) -> np.ndarray:
    pol_upper = pol.upper()
    if pol_upper == "TE":
        return te_basis(theta_deg, geom)
    if pol_upper == "TM":
        return tm_basis(theta_deg, mode, geom)
    raise ValueError(f"Unsupported polarization: {pol}")


def project_vector_field(
    field_xyz: np.ndarray,
    theta_deg: float,
    pol: str,
    mode: str,
    geom: GeometryConfig,
) -> np.ndarray:
    field = np.asarray(field_xyz, dtype=complex)
    if field.ndim != 2 or field.shape[1] != 3:
        raise ValueError("field_xyz must have shape (N, 3).")
    basis = projection_basis(theta_deg, pol, mode, geom).astype(complex)
    return field @ basis
