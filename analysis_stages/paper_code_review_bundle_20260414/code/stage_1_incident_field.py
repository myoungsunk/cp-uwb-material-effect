# Consolidated review copy for paper-pipeline code assessment.
# Stage: 1
# Role: Analytic incident-field model used by Stage 1 truth reconstruction.
# Source: analysis_stages/ideal_te_tm_scattered_stage/code/incident_field.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

import numpy as np

from stage_1_geometry import GeometryConfig, SPEED_OF_LIGHT, incident_hat, source_origin, te_basis, tm_basis


def incident_polarization_vector(theta_deg: float, pol: str, geom: GeometryConfig) -> np.ndarray:
    pol_upper = pol.upper()
    if pol_upper == "TE":
        return te_basis(theta_deg, geom)
    if pol_upper == "TM":
        return tm_basis(theta_deg, "incident", geom)
    raise ValueError(f"Unsupported polarization: {pol}")


def analytic_incident_field(
    points_xyz: np.ndarray,
    freq_hz: float,
    theta_deg: float,
    pol: str,
    geom: GeometryConfig,
) -> np.ndarray:
    points = np.asarray(points_xyz, dtype=float)
    source_origin_xyz = np.asarray(source_origin(theta_deg, geom), dtype=float)
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("points_xyz must have shape (N, 3).")

    khat = incident_hat(theta_deg, geom)
    e0 = incident_polarization_vector(theta_deg, pol, geom).astype(complex)
    orthogonality = float(np.abs(np.vdot(khat, e0)))
    if orthogonality > 1e-9:
        raise ValueError("Incident polarization vector must stay orthogonal to the propagation vector.")
    k0 = 2.0 * np.pi * float(freq_hz) / SPEED_OF_LIGHT
    phase_argument = (points - source_origin_xyz) @ khat
    phase = np.exp(-1j * k0 * phase_argument)
    return phase[:, None] * e0[None, :]
