from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

import numpy as np

SPEED_OF_LIGHT = 299_792_458.0


@dataclass(frozen=True)
class GeometryConfig:
    source_origin_m: np.ndarray
    surface_normal_m: np.ndarray
    reference_te_axis_m: np.ndarray
    source_origin_offset_along_incident_m: float = 0.0
    observation_distance_lambda_scale: float = 0.5
    baseline_case: str = "baseline"
    pec_case: str = "pec"
    refl_rect: str = "refl_rect"
    trans_rect: str = "trans_rect"
    pec_target_reflection_te: float = -1.0
    pec_target_reflection_tm: float = 1.0
    baseline_good_threshold: float = 1e-2
    baseline_warn_threshold: float = 1e-1
    fit_warn_threshold: float = 5e-2
    smoothness_jump_db: float = 3.0
    passivity_tolerance: float = 5e-2
    debug_maps: bool = False


def _parse_simple_yaml_value(text: str):
    value = text.strip()
    if not value:
        return ""
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        pass
    try:
        if "." in value or "e" in value.lower():
            return float(value)
        return int(value)
    except ValueError:
        return value.strip("\"'")


def _load_flat_yaml(path: Path) -> dict:
    data = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = _parse_simple_yaml_value(value)
    return data


def load_geometry_config(path: Path) -> GeometryConfig:
    if not path.exists():
        raise FileNotFoundError(f"Geometry config not found: {path}")

    data = _load_flat_yaml(path)
    source_origin = np.asarray(data.get("source_origin_m", [0.0, 0.0, 0.0]), dtype=float)
    if source_origin.shape != (3,):
        raise ValueError("source_origin_m must contain exactly three numeric values.")
    surface_normal = np.asarray(data.get("surface_normal_m", [0.0, 0.0, 1.0]), dtype=float)
    if surface_normal.shape != (3,):
        raise ValueError("surface_normal_m must contain exactly three numeric values.")
    reference_te_axis = np.asarray(data.get("reference_te_axis_m", [0.0, 1.0, 0.0]), dtype=float)
    if reference_te_axis.shape != (3,):
        raise ValueError("reference_te_axis_m must contain exactly three numeric values.")

    return GeometryConfig(
        source_origin_m=source_origin,
        surface_normal_m=_unit_vector(surface_normal, "surface_normal_m"),
        reference_te_axis_m=_unit_vector(reference_te_axis, "reference_te_axis_m"),
        source_origin_offset_along_incident_m=float(
            data.get("source_origin_offset_along_incident_m", 0.0)
        ),
        observation_distance_lambda_scale=float(
            data.get("observation_distance_lambda_scale", 0.5)
        ),
        baseline_case=str(data.get("baseline_case", "baseline")),
        pec_case=str(data.get("pec_case", "pec")),
        refl_rect=str(data.get("refl_rect", "refl_rect")),
        trans_rect=str(data.get("trans_rect", "trans_rect")),
        pec_target_reflection_te=float(data.get("pec_target_reflection_te", -1.0)),
        pec_target_reflection_tm=float(data.get("pec_target_reflection_tm", 1.0)),
        baseline_good_threshold=float(data.get("baseline_good_threshold", 1e-2)),
        baseline_warn_threshold=float(data.get("baseline_warn_threshold", 1e-1)),
        fit_warn_threshold=float(data.get("fit_warn_threshold", 5e-2)),
        smoothness_jump_db=float(data.get("smoothness_jump_db", 3.0)),
        passivity_tolerance=float(data.get("passivity_tolerance", 5e-2)),
        debug_maps=bool(data.get("debug_maps", False)),
    )


def theta_rad(theta_deg: float) -> float:
    return float(np.deg2rad(theta_deg))


def _unit_vector(vec: np.ndarray, name: str) -> np.ndarray:
    arr = np.asarray(vec, dtype=float)
    norm = float(np.linalg.norm(arr))
    if norm == 0.0:
        raise ValueError(f"{name} must be non-zero.")
    return arr / norm


def incident_hat(theta_deg: float) -> np.ndarray:
    theta = theta_rad(theta_deg)
    return np.array([np.sin(theta), 0.0, np.cos(theta)], dtype=float)


def reflected_hat(theta_deg: float) -> np.ndarray:
    theta = theta_rad(theta_deg)
    return np.array([np.sin(theta), 0.0, -np.cos(theta)], dtype=float)


def transmitted_hat(theta_deg: float) -> np.ndarray:
    return incident_hat(theta_deg)


def propagation_hat(theta_deg: float, mode: str) -> np.ndarray:
    if mode == "incident":
        return incident_hat(theta_deg)
    if mode == "reflected":
        return reflected_hat(theta_deg)
    if mode == "transmitted":
        return transmitted_hat(theta_deg)
    raise ValueError(f"Unsupported propagation mode: {mode}")


def te_basis(theta_deg: float, geom: GeometryConfig) -> np.ndarray:
    """
    Build the local TE basis from the surface normal and the incident wavevector.

    TE/TM are always defined with respect to the local plane of incidence.
    At normal incidence, the plane is degenerate, so we fall back to the
    configured reference TE axis projected onto the plane transverse to k_i.
    """

    k_inc = incident_hat(theta_deg)
    candidate = np.cross(geom.surface_normal_m, k_inc)
    if np.linalg.norm(candidate) > 0.0:
        return _unit_vector(candidate, "te_basis")

    fallback = geom.reference_te_axis_m - np.dot(geom.reference_te_axis_m, k_inc) * k_inc
    if np.linalg.norm(fallback) > 0.0:
        return _unit_vector(fallback, "reference_te_axis_m")

    global_x = np.array([1.0, 0.0, 0.0], dtype=float)
    fallback = global_x - np.dot(global_x, k_inc) * k_inc
    return _unit_vector(fallback, "normal-incidence fallback TE axis")


def tm_basis(theta_deg: float, mode: str, geom: GeometryConfig) -> np.ndarray:
    """
    Build the local TM basis for the requested propagation direction.

    We use e_TM,q = e_TE x k_q so the projector stays tied to the local
    plane-of-incidence definition instead of any global LP port axis.
    """

    te = te_basis(theta_deg, geom)
    k_q = propagation_hat(theta_deg, mode)
    return _unit_vector(np.cross(te, k_q), f"tm_basis[{mode}]")


def source_origin(theta_deg: float, geom: GeometryConfig) -> np.ndarray:
    """
    Return the phase reference point for the analytic incident field.

    The HFSS ideal-stage exports use a plane-wave reference point displaced
    along the incident direction. The configured offset lets us match that
    convention while still supporting a fixed absolute origin.
    """

    return geom.source_origin_m + geom.source_origin_offset_along_incident_m * incident_hat(theta_deg)


def observation_distance_m(freq_hz: float, geom: GeometryConfig) -> float:
    return geom.observation_distance_lambda_scale * SPEED_OF_LIGHT / float(freq_hz)


def plane_center(theta_deg: float, freq_hz: float, rect: str, geom: GeometryConfig) -> np.ndarray:
    if rect == geom.refl_rect:
        mode = "reflected"
    elif rect == geom.trans_rect:
        mode = "transmitted"
    else:
        raise ValueError(f"Unsupported rectangle label: {rect}")
    return observation_distance_m(freq_hz, geom) * propagation_hat(theta_deg, mode)


def wide_plane_axes(theta_deg: float, rect: str, geom: GeometryConfig) -> tuple[np.ndarray, np.ndarray]:
    """
    Map the HFSS wide-grid `_u/_v` coordinates into global XYZ.

    For the current ideal-stage export, the near rectangle is centered on a
    plane normal to the propagation direction. We use:
      - `_u` along the local TE axis
      - `_v` along the negative local TM axis

    This keeps the local rectangle basis right-handed with `u x v = k_q`.
    """

    if rect == geom.refl_rect:
        mode = "reflected"
    elif rect == geom.trans_rect:
        mode = "transmitted"
    else:
        raise ValueError(f"Unsupported rectangle label: {rect}")

    u_hat = te_basis(theta_deg, geom)
    v_hat = -tm_basis(theta_deg, mode, geom)
    return u_hat, v_hat
