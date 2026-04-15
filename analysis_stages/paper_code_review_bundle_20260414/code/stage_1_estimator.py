# Consolidated review copy for paper-pipeline code assessment.
# Stage: 1
# Role: Matched plane-wave estimator used by the ideal truth-table builder.
# Source: analysis_stages/ideal_te_tm_scattered_stage/code/estimator.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from stage_1_geometry import SPEED_OF_LIGHT


@dataclass(frozen=True)
class PlaneWaveEstimate:
    amplitude: complex
    residual: float
    center_xyz: np.ndarray
    num_points: int


def matched_plane_wave_estimator(
    points_xyz: np.ndarray,
    scalar_field: np.ndarray,
    freq_hz: float,
    direction_hat: np.ndarray,
) -> PlaneWaveEstimate:
    points = np.asarray(points_xyz, dtype=float)
    samples = np.asarray(scalar_field, dtype=complex)
    direction = np.asarray(direction_hat, dtype=float)

    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("points_xyz must have shape (N, 3).")
    if samples.ndim != 1 or samples.shape[0] != points.shape[0]:
        raise ValueError("scalar_field must have shape (N,).")

    center = points.mean(axis=0)
    k0 = 2.0 * np.pi * float(freq_hz) / SPEED_OF_LIGHT
    phase = np.exp(1j * k0 * ((points - center) @ direction))
    amplitude = np.mean(samples * phase)
    model = amplitude * np.exp(-1j * k0 * ((points - center) @ direction))

    denom = np.linalg.norm(samples)
    residual = 0.0 if denom == 0 else float(np.linalg.norm(samples - model) / denom)

    return PlaneWaveEstimate(
        amplitude=complex(amplitude),
        residual=residual,
        center_xyz=center,
        num_points=int(points.shape[0]),
    )
