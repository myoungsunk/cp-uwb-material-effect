from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd

from cp_transform import build_cp_truth_table
from estimator import matched_plane_wave_estimator
from geometry import (
    GeometryConfig,
    incident_hat,
    load_geometry_config,
    observation_distance_m,
    plane_center,
    reflected_hat,
    te_basis,
    tm_basis,
    transmitted_hat,
)
from incident_field import analytic_incident_field
from io_adapter import load_normalized_measurements, read_manifest
from projection import project_vector_field
from qc import (
    baseline_status,
    build_pec_rows,
    build_smoothness_rows,
    fit_status,
    passivity_excess,
    passivity_status,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

COMPLEX_COMPONENT_SUFFIXES = ("real", "imag", "mag", "phase_deg")
RUN_LABEL_W_PLANE_RE = re.compile(r"(?:^|__)w_(?P<width_mm>[0-9.]+)mm(?:__|$)", re.IGNORECASE)
TRUTH_REGION_COLUMNS = [
    "truth_region",
    "truth_region_reason",
    "use_for_main_claim",
    "use_for_caution_only",
    "truth_region_TE",
    "truth_region_reason_TE",
    "use_for_main_claim_TE",
    "use_for_caution_only_TE",
    "truth_region_TM",
    "truth_region_reason_TM",
    "use_for_main_claim_TM",
    "use_for_caution_only_TM",
]
OBSERVATION_METADATA_COLUMNS = [
    "observation_distance_m",
    "surface_reference_point_x_m",
    "surface_reference_point_y_m",
    "surface_reference_point_z_m",
    "refl_plane_center_x_m",
    "refl_plane_center_y_m",
    "refl_plane_center_z_m",
    "trans_plane_center_x_m",
    "trans_plane_center_y_m",
    "trans_plane_center_z_m",
]


def find_stage_root(start: Path) -> Path:
    return start.resolve().parents[1]


def material_from_case(case: str) -> str:
    return case[5:] if case.startswith("slab_") else case


def complex_columns(prefix: str, value: complex) -> dict:
    return {
        f"{prefix}_real": float(np.real(value)),
        f"{prefix}_imag": float(np.imag(value)),
        f"{prefix}_mag": float(np.abs(value)),
        f"{prefix}_phase_deg": float(np.rad2deg(np.angle(value))),
    }


def _theta_close(theta_deg: float, target_deg: float, atol: float = 1e-9) -> bool:
    return bool(np.isclose(float(theta_deg), float(target_deg), atol=atol, rtol=0.0))


def infer_w_plane_mm(run_label: str) -> float | None:
    match = RUN_LABEL_W_PLANE_RE.search(str(run_label))
    if match is None:
        return None
    return float(match.group("width_mm"))


def truth_region_for_polarization(
    pol: str,
    theta_deg: float,
    observation_distance_lambda_scale: float,
    run_label: str,
) -> dict[str, object]:
    pol_upper = str(pol).upper()
    theta = float(theta_deg)
    obs_scale = float(observation_distance_lambda_scale)

    if not _theta_close(obs_scale, 5.0):
        return {
            "truth_region": "exclude_setup_mismatch",
            "truth_region_reason": "Truth-region policy is only validated for the k_obs=5 material setup.",
            "use_for_main_claim": False,
            "use_for_caution_only": False,
        }
    w_plane_mm = infer_w_plane_mm(run_label)
    if w_plane_mm is not None and not _theta_close(w_plane_mm, 5000.0, atol=1e-6):
        return {
            "truth_region": "exclude_setup_mismatch",
            "truth_region_reason": "Truth-region policy is only validated for the recommended 5000 mm observation plane.",
            "use_for_main_claim": False,
            "use_for_caution_only": False,
        }

    if pol_upper == "TM":
        if theta <= 70.0 + 1e-9:
            return {
                "truth_region": "main",
                "truth_region_reason": "TM is validated through 70 deg under the PEC setup (w_plane=5000 mm, k_obs=5).",
                "use_for_main_claim": True,
                "use_for_caution_only": False,
            }
        return {
            "truth_region": "exclude",
            "truth_region_reason": "TM is outside the validated PEC range (>70 deg).",
            "use_for_main_claim": False,
            "use_for_caution_only": False,
        }

    if pol_upper != "TE":
        raise ValueError(f"Unsupported polarization for truth-region classification: {pol!r}")

    if theta <= 60.0 + 1e-9:
        return {
            "truth_region": "main",
            "truth_region_reason": "TE is validated through 60 deg under the PEC setup (w_plane=5000 mm, k_obs=5).",
            "use_for_main_claim": True,
            "use_for_caution_only": False,
        }
    if _theta_close(theta, 65.0):
        return {
            "truth_region": "caution",
            "truth_region_reason": "TE 65 deg is near the PEC transmission limit; keep it out of main claims.",
            "use_for_main_claim": False,
            "use_for_caution_only": True,
        }
    if _theta_close(theta, 70.0):
        return {
            "truth_region": "exclude",
            "truth_region_reason": "TE 70 deg is beyond the reliable PEC trust region for main use.",
            "use_for_main_claim": False,
            "use_for_caution_only": False,
        }
    if theta < 70.0:
        return {
            "truth_region": "caution_high_angle",
            "truth_region_reason": "TE above 60 deg is high-angle territory; treat as caution only unless explicitly re-validated.",
            "use_for_main_claim": False,
            "use_for_caution_only": True,
        }
    return {
        "truth_region": "exclude",
        "truth_region_reason": "TE is outside the validated PEC range (>70 deg).",
        "use_for_main_claim": False,
        "use_for_caution_only": False,
    }


def combined_truth_region(te_meta: dict[str, object], tm_meta: dict[str, object]) -> dict[str, object]:
    te_region = str(te_meta["truth_region"])
    tm_region = str(tm_meta["truth_region"])
    te_main = bool(te_meta["use_for_main_claim"])
    tm_main = bool(tm_meta["use_for_main_claim"])
    te_caution = bool(te_meta["use_for_caution_only"])
    tm_caution = bool(tm_meta["use_for_caution_only"])

    if te_region == tm_region and te_main == tm_main and te_caution == tm_caution:
        return {
            "truth_region": te_region,
            "truth_region_reason": f"TE and TM both classified as {te_region}.",
            "use_for_main_claim": te_main,
            "use_for_caution_only": te_caution,
        }

    if te_main and tm_main:
        return {
            "truth_region": "main",
            "truth_region_reason": "TE and TM are both within the validated main-truth region.",
            "use_for_main_claim": True,
            "use_for_caution_only": False,
        }

    if te_caution or tm_caution:
        return {
            "truth_region": "mixed",
            "truth_region_reason": f"Polarization split: TE={te_region}, TM={tm_region}. Use row-level results only as caution.",
            "use_for_main_claim": False,
            "use_for_caution_only": True,
        }

    if te_main or tm_main:
        return {
            "truth_region": "mixed",
            "truth_region_reason": f"Polarization split: TE={te_region}, TM={tm_region}. Main-use eligibility differs by polarization.",
            "use_for_main_claim": False,
            "use_for_caution_only": True,
        }

    return {
        "truth_region": "exclude",
        "truth_region_reason": f"TE={te_region} and TM={tm_region}; neither polarization is in the row-level main region.",
        "use_for_main_claim": False,
        "use_for_caution_only": False,
    }


def build_truth_region_columns(
    theta_deg: float,
    observation_distance_lambda_scale: float,
    run_label: str,
) -> dict[str, object]:
    te_meta = truth_region_for_polarization("TE", theta_deg, observation_distance_lambda_scale, run_label)
    tm_meta = truth_region_for_polarization("TM", theta_deg, observation_distance_lambda_scale, run_label)
    row_meta = combined_truth_region(te_meta, tm_meta)
    return {
        **row_meta,
        "truth_region_TE": te_meta["truth_region"],
        "truth_region_reason_TE": te_meta["truth_region_reason"],
        "use_for_main_claim_TE": bool(te_meta["use_for_main_claim"]),
        "use_for_caution_only_TE": bool(te_meta["use_for_caution_only"]),
        "truth_region_TM": tm_meta["truth_region"],
        "truth_region_reason_TM": tm_meta["truth_region_reason"],
        "use_for_main_claim_TM": bool(tm_meta["use_for_main_claim"]),
        "use_for_caution_only_TM": bool(tm_meta["use_for_caution_only"]),
    }


def build_observation_metadata(
    theta_deg: float,
    freq_hz: float,
    observation_distance_lambda_scale: float,
    geom: GeometryConfig,
) -> dict[str, float]:
    obs_distance_m = observation_distance_m(
        freq_hz,
        geom,
        observation_distance_lambda_scale=observation_distance_lambda_scale,
    )
    refl_center = plane_center(
        theta_deg,
        freq_hz,
        geom.refl_rect,
        geom,
        observation_distance_lambda_scale=observation_distance_lambda_scale,
    )
    trans_center = plane_center(
        theta_deg,
        freq_hz,
        geom.trans_rect,
        geom,
        observation_distance_lambda_scale=observation_distance_lambda_scale,
    )
    return {
        "observation_distance_m": float(obs_distance_m),
        "surface_reference_point_x_m": float(geom.surface_reference_point_m[0]),
        "surface_reference_point_y_m": float(geom.surface_reference_point_m[1]),
        "surface_reference_point_z_m": float(geom.surface_reference_point_m[2]),
        "refl_plane_center_x_m": float(refl_center[0]),
        "refl_plane_center_y_m": float(refl_center[1]),
        "refl_plane_center_z_m": float(refl_center[2]),
        "trans_plane_center_x_m": float(trans_center[0]),
        "trans_plane_center_y_m": float(trans_center[1]),
        "trans_plane_center_z_m": float(trans_center[2]),
    }


def truth_table_id_columns(df: pd.DataFrame) -> list[str]:
    columns = ["case", "material", "f_hz", "theta_deg", "observation_distance_lambda_scale"]
    if "run_label" in df.columns:
        columns.insert(2, "run_label")
    return [column for column in columns if column in df.columns]


def measurement_dataset_columns(df: pd.DataFrame) -> list[str]:
    columns = ["case", "pol", "rect", "f_hz", "theta_deg", "observation_distance_lambda_scale"]
    if "run_label" in df.columns:
        columns.append("run_label")
    return columns


def measurement_grid_columns(df: pd.DataFrame) -> list[str]:
    columns = ["rect", "f_hz", "theta_deg", "observation_distance_lambda_scale"]
    if "run_label" in df.columns and df["run_label"].fillna("").astype(str).str.strip().ne("").any():
        columns.append("run_label")
    return columns


def theta_grid_from_measurements(measurements: pd.DataFrame) -> list[float]:
    return sorted(float(value) for value in measurements["theta_deg"].dropna().unique())


def point_cloud_signature(sub_df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    ordered = sub_df.sort_values(["point_id", "x", "y", "z"]).reset_index(drop=True)
    point_ids = pd.to_numeric(ordered["point_id"], errors="coerce").to_numpy(dtype=float)
    xyz = ordered[["x", "y", "z"]].to_numpy(dtype=float)
    signature = np.column_stack([point_ids, xyz])
    return signature, xyz


def validate_point_cloud_consistency(df: pd.DataFrame, expected_n: int = 401) -> list[dict]:
    qc_rows: list[dict] = []
    dataset_columns = measurement_dataset_columns(df)
    grid_columns = measurement_grid_columns(df)
    reference_signatures: dict[tuple, tuple[tuple, np.ndarray]] = {}

    for dataset_key, sub in df.groupby(dataset_columns, dropna=False, sort=False):
        ordered = sub.sort_values(["point_id", "x", "y", "z"]).reset_index(drop=True)
        key_map = dict(zip(dataset_columns, dataset_key))
        material = material_from_case(str(key_map["case"]))
        run_label = str(key_map.get("run_label", ""))
        num_points = int(len(ordered))
        unique_point_ids = int(ordered["point_id"].nunique(dropna=False))

        qc_rows.append(
            {
                "case": key_map["case"],
                "material": material,
                "pol": key_map["pol"],
                "rect": key_map["rect"],
                "run_label": run_label,
                "f_hz": float(key_map["f_hz"]),
                "theta_deg": float(key_map["theta_deg"]),
                "observation_distance_lambda_scale": float(key_map["observation_distance_lambda_scale"]),
                "metric": "unexpected_point_count",
                "value": num_points,
                "status": "ok" if num_points == expected_n else "fail",
                "detail": f"Expected {expected_n} points per normalized rect export.",
            }
        )
        qc_rows.append(
            {
                "case": key_map["case"],
                "material": material,
                "pol": key_map["pol"],
                "rect": key_map["rect"],
                "run_label": run_label,
                "f_hz": float(key_map["f_hz"]),
                "theta_deg": float(key_map["theta_deg"]),
                "observation_distance_lambda_scale": float(key_map["observation_distance_lambda_scale"]),
                "metric": "duplicate_point_id_count",
                "value": float(num_points - unique_point_ids),
                "status": "ok" if num_points == unique_point_ids else "fail",
                "detail": "Duplicate point_id values must not exist within one rect export.",
            }
        )

        signature, _ = point_cloud_signature(ordered)
        grid_key = tuple(key_map[column] for column in grid_columns)
        reference = reference_signatures.get(grid_key)
        if reference is None:
            reference_signatures[grid_key] = (dataset_key, signature)
            continue

        reference_key, reference_signature = reference
        same_shape = signature.shape == reference_signature.shape
        same_order = same_shape and np.array_equal(signature[:, 0], reference_signature[:, 0])
        same_xyz = same_shape and np.allclose(signature[:, 1:], reference_signature[:, 1:], atol=1e-12, rtol=0.0)
        reference_case = reference_key[dataset_columns.index("case")]
        reference_pol = reference_key[dataset_columns.index("pol")]

        qc_rows.extend(
            [
                {
                    "case": key_map["case"],
                    "material": material,
                    "pol": key_map["pol"],
                    "rect": key_map["rect"],
                    "run_label": run_label,
                    "f_hz": float(key_map["f_hz"]),
                    "theta_deg": float(key_map["theta_deg"]),
                    "observation_distance_lambda_scale": float(key_map["observation_distance_lambda_scale"]),
                    "metric": "point_id_order_match",
                    "value": float(same_order),
                    "status": "ok" if same_order else "fail",
                    "detail": f"point_id ordering must match the reference grid ({reference_case}, {reference_pol}).",
                },
                {
                    "case": key_map["case"],
                    "material": material,
                    "pol": key_map["pol"],
                    "rect": key_map["rect"],
                    "run_label": run_label,
                    "f_hz": float(key_map["f_hz"]),
                    "theta_deg": float(key_map["theta_deg"]),
                    "observation_distance_lambda_scale": float(key_map["observation_distance_lambda_scale"]),
                    "metric": "xyz_grid_match",
                    "value": float(same_xyz),
                    "status": "ok" if same_xyz else "fail",
                    "detail": f"XYZ samples must match the reference grid ({reference_case}, {reference_pol}).",
                },
            ]
        )

    return qc_rows


def infer_field_type_from_pec_trans(exported_field: np.ndarray, incident_field: np.ndarray) -> str:
    incident_norm = float(np.linalg.norm(incident_field))
    if incident_norm == 0.0:
        raise ValueError("Incident field norm is zero; cannot infer field type from PEC transmission data.")
    rho_total = float(np.linalg.norm(exported_field) / incident_norm)
    rho_scattered = float(np.linalg.norm(exported_field + incident_field) / incident_norm)
    return "total" if rho_total < rho_scattered else "scattered"


def validate_pec_field_type_lock(measurements: pd.DataFrame, geom: GeometryConfig) -> list[dict]:
    qc_rows: list[dict] = []
    dataset_columns = measurement_dataset_columns(measurements)
    pec_trans = measurements[
        (measurements["case"] == geom.pec_case) & (measurements["rect"] == geom.trans_rect)
    ].copy()

    if pec_trans.empty:
        qc_rows.append(
            {
                "case": geom.pec_case,
                "material": geom.pec_case,
                "pol": "both",
                "rect": geom.trans_rect,
                "run_label": "",
                "f_hz": np.nan,
                "theta_deg": np.nan,
                "observation_distance_lambda_scale": np.nan,
                "metric": "pec_trans_field_type_reference_presence",
                "value": np.nan,
                "status": "warn",
                "detail": "No PEC transmission-plane export was available for field-type inference.",
            }
        )
        return qc_rows

    for dataset_key, sub in pec_trans.groupby(dataset_columns, dropna=False, sort=False):
        key_map = dict(zip(dataset_columns, dataset_key))
        material = material_from_case(str(key_map["case"]))
        run_label = str(key_map.get("run_label", ""))
        ordered = sub.sort_values(["point_id", "x", "y", "z"]).reset_index(drop=True)
        field_types = ordered["field_type"].dropna().astype(str).str.lower().unique()
        if len(field_types) != 1:
            qc_rows.append(
                {
                    "case": key_map["case"],
                    "material": material,
                    "pol": key_map["pol"],
                    "rect": key_map["rect"],
                    "run_label": run_label,
                    "f_hz": float(key_map["f_hz"]),
                    "theta_deg": float(key_map["theta_deg"]),
                    "observation_distance_lambda_scale": float(key_map["observation_distance_lambda_scale"]),
                    "metric": "manifest_field_type_cardinality",
                    "value": float(len(field_types)),
                    "status": "fail",
                    "detail": "Each normalized dataset must carry exactly one manifest field_type value.",
                }
            )
            continue

        manifest_field_type = str(field_types[0])
        points, exported_field = extract_arrays(ordered)
        incident_field = analytic_incident_field(
            points,
            float(key_map["f_hz"]),
            float(key_map["theta_deg"]),
            str(key_map["pol"]),
            geom,
        )
        incident_norm = float(np.linalg.norm(incident_field))
        rho_total = float(np.linalg.norm(exported_field) / incident_norm)
        rho_scattered = float(np.linalg.norm(exported_field + incident_field) / incident_norm)
        inferred_field_type = infer_field_type_from_pec_trans(exported_field, incident_field)

        qc_rows.extend(
            [
                {
                    "case": key_map["case"],
                    "material": material,
                    "pol": key_map["pol"],
                    "rect": key_map["rect"],
                    "run_label": run_label,
                    "f_hz": float(key_map["f_hz"]),
                    "theta_deg": float(key_map["theta_deg"]),
                    "observation_distance_lambda_scale": float(key_map["observation_distance_lambda_scale"]),
                    "metric": "pec_trans_rho_total",
                    "value": rho_total,
                    "status": "ok",
                    "detail": "||E_export|| / ||E_inc|| on the PEC transmission plane.",
                },
                {
                    "case": key_map["case"],
                    "material": material,
                    "pol": key_map["pol"],
                    "rect": key_map["rect"],
                    "run_label": run_label,
                    "f_hz": float(key_map["f_hz"]),
                    "theta_deg": float(key_map["theta_deg"]),
                    "observation_distance_lambda_scale": float(key_map["observation_distance_lambda_scale"]),
                    "metric": "pec_trans_rho_scattered",
                    "value": rho_scattered,
                    "status": "ok",
                    "detail": "||E_export + E_inc|| / ||E_inc|| on the PEC transmission plane.",
                },
                {
                    "case": key_map["case"],
                    "material": material,
                    "pol": key_map["pol"],
                    "rect": key_map["rect"],
                    "run_label": run_label,
                    "f_hz": float(key_map["f_hz"]),
                    "theta_deg": float(key_map["theta_deg"]),
                    "observation_distance_lambda_scale": float(key_map["observation_distance_lambda_scale"]),
                    "metric": "field_type_manifest_lock",
                    "value": float(manifest_field_type == inferred_field_type),
                    "status": "ok" if manifest_field_type == inferred_field_type else "fail",
                    "detail": (
                        f"Manifest field_type={manifest_field_type!r}, "
                        f"inferred from PEC transmission data={inferred_field_type!r}."
                    ),
                },
            ]
        )

    return qc_rows


def validate_geometry_lock(
    theta_grid: list[float] | np.ndarray,
    geom: GeometryConfig,
    locked_wide_truth: pd.DataFrame | None = None,
) -> list[dict]:
    qc_rows: list[dict] = []
    tolerance = 1e-9
    theta_values = [float(theta) for theta in theta_grid]

    for theta_deg in theta_values:
        k_inc = incident_hat(theta_deg, geom)
        te = te_basis(theta_deg, geom)
        tm_inc = tm_basis(theta_deg, "incident", geom)
        tm_refl = tm_basis(theta_deg, "reflected", geom)
        tm_trans = tm_basis(theta_deg, "transmitted", geom)

        geometry_checks = [
            ("TE", "incident", float(abs(np.dot(te, k_inc))), "e_TE dot k_incident"),
            ("TM", "incident", float(abs(np.dot(tm_inc, k_inc))), "e_TM,incident dot k_incident"),
            ("TM", "reflected", float(abs(np.dot(tm_refl, reflected_hat(theta_deg, geom)))), "e_TM,reflected dot k_reflected"),
            ("TM", "transmitted", float(abs(np.dot(tm_trans, transmitted_hat(theta_deg, geom)))), "e_TM,transmitted dot k_transmitted"),
            ("TE_TM", "incident", float(abs(np.dot(te, tm_inc))), "e_TE dot e_TM,incident"),
            ("TE_TM", "reflected", float(abs(np.dot(te, tm_refl))), "e_TE dot e_TM,reflected"),
            ("TE_TM", "transmitted", float(abs(np.dot(te, tm_trans))), "e_TE dot e_TM,transmitted"),
        ]

        for pol, rect, value, label in geometry_checks:
            qc_rows.append(
                {
                    "case": "geometry",
                    "material": "geometry",
                    "pol": pol,
                    "rect": rect,
                    "run_label": "",
                    "f_hz": np.nan,
                    "theta_deg": theta_deg,
                    "observation_distance_lambda_scale": np.nan,
                    "metric": "geometry_lock",
                    "value": value,
                    "status": "ok" if value <= tolerance else "fail",
                    "detail": f"{label} must stay within {tolerance:.1e}.",
                }
            )

    if locked_wide_truth is None:
        return qc_rows

    pec_rows = locked_wide_truth[locked_wide_truth["case"] == geom.pec_case].copy()
    if pec_rows.empty:
        qc_rows.append(
            {
                "case": geom.pec_case,
                "material": geom.pec_case,
                "pol": "both",
                "rect": geom.refl_rect,
                "run_label": "",
                "f_hz": np.nan,
                "theta_deg": np.nan,
                "observation_distance_lambda_scale": np.nan,
                "metric": "pec_locked_reflection_target_error",
                "value": np.nan,
                "status": "warn",
                "detail": "No PEC rows were available to verify the locked reflection sign convention.",
            }
        )
        return qc_rows

    for _, row in pec_rows.iterrows():
        te_error = float(abs(complex(row["R_TE"]) - geom.pec_target_reflection_te))
        tm_error = float(abs(complex(row["R_TM"]) - geom.pec_target_reflection_tm))
        qc_rows.extend(
            [
                {
                    "case": row["case"],
                    "material": row["material"],
                    "pol": "TE",
                    "rect": geom.refl_rect,
                    "run_label": row.get("run_label", ""),
                    "f_hz": float(row["f_hz"]),
                    "theta_deg": float(row["theta_deg"]),
                    "observation_distance_lambda_scale": float(row["observation_distance_lambda_scale"]),
                    "metric": "pec_locked_reflection_target_error",
                    "value": te_error,
                    "status": "ok" if te_error <= 0.1 else "fail",
                    "detail": f"Locked PEC R_TE should approach {geom.pec_target_reflection_te:+.1f}.",
                },
                {
                    "case": row["case"],
                    "material": row["material"],
                    "pol": "TM",
                    "rect": geom.refl_rect,
                    "run_label": row.get("run_label", ""),
                    "f_hz": float(row["f_hz"]),
                    "theta_deg": float(row["theta_deg"]),
                    "observation_distance_lambda_scale": float(row["observation_distance_lambda_scale"]),
                    "metric": "pec_locked_reflection_target_error",
                    "value": tm_error,
                    "status": "ok" if tm_error <= 0.1 else "fail",
                    "detail": f"Locked PEC R_TM should approach {geom.pec_target_reflection_tm:+.1f}.",
                },
            ]
        )

    return qc_rows


def extract_arrays(sub_df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    points = sub_df[["x", "y", "z"]].to_numpy(dtype=float)
    field = np.column_stack(
        [
            sub_df["Ex"].to_numpy(dtype=complex),
            sub_df["Ey"].to_numpy(dtype=complex),
            sub_df["Ez"].to_numpy(dtype=complex),
        ]
    )
    return points, field


def write_debug_map(
    output_dir: Path,
    case: str,
    pol: str,
    rect: str,
    f_hz: float,
    theta_deg: float,
    points: np.ndarray,
    scalar_field: np.ndarray,
    model_field: np.ndarray,
) -> None:
    filename = (
        f"{case}__{pol}__{rect}__"
        f"f_{int(round(f_hz))}__theta_{str(theta_deg).replace('.', 'p')}.csv"
    )
    debug_df = pd.DataFrame(
        {
            "x": points[:, 0],
            "y": points[:, 1],
            "z": points[:, 2],
            "scalar_real": np.real(scalar_field),
            "scalar_imag": np.imag(scalar_field),
            "model_real": np.real(model_field),
            "model_imag": np.imag(model_field),
            "residual_real": np.real(scalar_field - model_field),
            "residual_imag": np.imag(scalar_field - model_field),
        }
    )
    debug_df.to_csv(output_dir / filename, index=False)


def extract_rect_amplitudes(
    sub_df: pd.DataFrame,
    geom: GeometryConfig,
    case: str,
    pol: str,
    rect: str,
    f_hz: float,
    theta_deg: float,
    debug_dir: Path | None,
) -> dict:
    points, exported_field = extract_arrays(sub_df)
    incident_phase_deg = (
        float(sub_df["incident_phase_deg"].dropna().iloc[0])
        if "incident_phase_deg" in sub_df.columns and not sub_df["incident_phase_deg"].dropna().empty
        else 0.0
    )
    incident_field = (
        analytic_incident_field(points, f_hz, theta_deg, pol, geom)
        * np.exp(1j * np.deg2rad(incident_phase_deg))
    )
    incident_norm = float(np.linalg.norm(incident_field))
    if "field_type" not in sub_df.columns or sub_df["field_type"].dropna().empty:
        raise ValueError("Each normalized dataset must carry an explicit field_type.")
    field_types = sub_df["field_type"].dropna().astype(str).str.lower().unique()
    if len(field_types) != 1:
        raise ValueError(
            f"Expected exactly one field_type for case={case} pol={pol} rect={rect} "
            f"f_hz={f_hz} theta_deg={theta_deg}, got {field_types.tolist()!r}."
        )
    field_type = str(field_types[0])
    observation_distance_lambda_scale = (
        float(sub_df["observation_distance_lambda_scale"].dropna().iloc[0])
        if "observation_distance_lambda_scale" in sub_df.columns
        and not sub_df["observation_distance_lambda_scale"].dropna().empty
        else float(geom.observation_distance_lambda_scale)
    )

    if rect == geom.refl_rect:
        if field_type == "scattered":
            observation_field = exported_field
            baseline_residual_field = exported_field
        elif field_type == "total":
            observation_field = exported_field - incident_field
            baseline_residual_field = exported_field - incident_field
        else:
            raise ValueError(f"Unsupported field_type: {field_type!r}")
        observation_mode = "reflected"
        observation_hat = reflected_hat(theta_deg, geom)
    elif rect == geom.trans_rect:
        if field_type == "scattered":
            observation_field = incident_field + exported_field
            baseline_residual_field = exported_field
        elif field_type == "total":
            observation_field = exported_field
            baseline_residual_field = exported_field - incident_field
        else:
            raise ValueError(f"Unsupported field_type: {field_type!r}")
        observation_mode = "transmitted"
        observation_hat = transmitted_hat(theta_deg, geom)
    else:
        raise ValueError(f"Unexpected rect value: {rect}")

    baseline_residual_over_incident = (
        float(np.linalg.norm(baseline_residual_field) / incident_norm) if incident_norm > 0.0 else 0.0
    )

    scalar_incident = project_vector_field(incident_field, theta_deg, pol, "incident", geom)
    scalar_observation = project_vector_field(observation_field, theta_deg, pol, observation_mode, geom)

    incident_estimate = matched_plane_wave_estimator(points, scalar_incident, f_hz, incident_hat(theta_deg, geom))
    observation_estimate = matched_plane_wave_estimator(points, scalar_observation, f_hz, observation_hat)

    k0 = 2.0 * np.pi * float(f_hz) / 299_792_458.0
    phase_argument = (points - observation_estimate.center_xyz) @ observation_hat
    observation_model = observation_estimate.amplitude * np.exp(-1j * k0 * phase_argument)

    if debug_dir is not None:
        write_debug_map(
            output_dir=debug_dir,
            case=case,
            pol=pol,
            rect=rect,
            f_hz=f_hz,
            theta_deg=theta_deg,
            points=points,
            scalar_field=scalar_observation,
            model_field=observation_model,
        )

    return {
        "incident_amplitude": incident_estimate.amplitude,
        "incident_fit_residual": incident_estimate.residual,
        "observation_amplitude": observation_estimate.amplitude,
        "observation_fit_residual": observation_estimate.residual,
        "field_type": field_type,
        "incident_phase_deg": incident_phase_deg,
        "observation_distance_lambda_scale": observation_distance_lambda_scale,
        "baseline_residual_over_incident": baseline_residual_over_incident,
        "num_points": observation_estimate.num_points,
    }


def build_raw_truth_table(
    measurements: pd.DataFrame,
    geom: GeometryConfig,
    debug_dir: Path | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    group_columns = ["case", "pol", "rect", "f_hz", "theta_deg", "observation_distance_lambda_scale"]
    if "run_label" in measurements.columns:
        group_columns.append("run_label")
    grouped = {
        key: sub.sort_values(["point_id", "x", "y", "z"]).reset_index(drop=True)
        for key, sub in measurements.groupby(group_columns, sort=False, dropna=False)
    }

    truth_rows: list[dict] = []
    qc_rows: list[dict] = []
    run_key_columns = ["case", "pol", "f_hz", "theta_deg", "observation_distance_lambda_scale"]
    if "run_label" in measurements.columns:
        run_key_columns.append("run_label")
    run_keys = sorted({tuple(key[group_columns.index(column)] for column in run_key_columns) for key in grouped})

    for run_key in run_keys:
        run_key_map = dict(zip(run_key_columns, run_key))
        case = run_key_map["case"]
        pol = run_key_map["pol"]
        f_hz = run_key_map["f_hz"]
        theta_deg = run_key_map["theta_deg"]
        observation_distance_lambda_scale = run_key_map["observation_distance_lambda_scale"]
        run_label = run_key_map.get("run_label", "")

        refl_key = tuple(
            run_key_map.get(column, geom.refl_rect if column == "rect" else "")
            if column != "rect"
            else geom.refl_rect
            for column in group_columns
        )
        trans_key = tuple(
            run_key_map.get(column, geom.trans_rect if column == "rect" else "")
            if column != "rect"
            else geom.trans_rect
            for column in group_columns
        )
        material = material_from_case(case)

        if refl_key not in grouped or trans_key not in grouped:
            qc_rows.append(
                {
                    "case": case,
                    "material": material,
                    "pol": pol,
                    "rect": "both",
                    "run_label": run_label,
                    "f_hz": float(f_hz),
                    "theta_deg": float(theta_deg),
                    "observation_distance_lambda_scale": observation_distance_lambda_scale,
                    "metric": "missing_rect_pair",
                    "value": np.nan,
                    "status": "fail",
                    "detail": f"Missing {'refl_rect' if refl_key not in grouped else 'trans_rect'} dataset.",
                }
            )
            continue

        refl = extract_rect_amplitudes(grouped[refl_key], geom, case, pol, geom.refl_rect, f_hz, theta_deg, debug_dir)
        trans = extract_rect_amplitudes(grouped[trans_key], geom, case, pol, geom.trans_rect, f_hz, theta_deg, debug_dir)

        if case == geom.baseline_case:
            qc_rows.extend(
                [
                    {
                        "case": case,
                        "material": material,
                        "pol": pol,
                        "rect": geom.refl_rect,
                        "run_label": run_label,
                        "f_hz": float(f_hz),
                        "theta_deg": float(theta_deg),
                        "observation_distance_lambda_scale": observation_distance_lambda_scale,
                        "metric": "baseline_residual_over_incident",
                        "value": refl["baseline_residual_over_incident"],
                        "status": baseline_status(
                            refl["baseline_residual_over_incident"],
                            geom.baseline_good_threshold,
                            geom.baseline_warn_threshold,
                        ),
                        "detail": f"Baseline residual norm divided by analytic incident norm on reflection plane ({refl['field_type']} export).",
                    },
                    {
                        "case": case,
                        "material": material,
                        "pol": pol,
                        "rect": geom.trans_rect,
                        "run_label": run_label,
                        "f_hz": float(f_hz),
                        "theta_deg": float(theta_deg),
                        "observation_distance_lambda_scale": observation_distance_lambda_scale,
                        "metric": "baseline_residual_over_incident",
                        "value": trans["baseline_residual_over_incident"],
                        "status": baseline_status(
                            trans["baseline_residual_over_incident"],
                            geom.baseline_good_threshold,
                            geom.baseline_warn_threshold,
                        ),
                        "detail": f"Baseline residual norm divided by analytic incident norm on transmission plane ({trans['field_type']} export).",
                    },
                ]
            )
            continue

        reflection_coeff = refl["observation_amplitude"] / refl["incident_amplitude"]
        transmission_coeff = trans["observation_amplitude"] / trans["incident_amplitude"]
        truth_rows.append(
            {
                "case": case,
                "material": material,
                "pol": pol,
                "run_label": run_label,
                "f_hz": float(f_hz),
                "theta_deg": float(theta_deg),
                "observation_distance_lambda_scale": observation_distance_lambda_scale,
                "field_type_refl": refl["field_type"],
                "field_type_trans": trans["field_type"],
                "R": reflection_coeff,
                "T": transmission_coeff,
            }
        )
        qc_rows.extend(
            [
                {
                    "case": case,
                    "material": material,
                    "pol": pol,
                    "rect": geom.refl_rect,
                    "run_label": run_label,
                    "f_hz": float(f_hz),
                    "theta_deg": float(theta_deg),
                    "observation_distance_lambda_scale": observation_distance_lambda_scale,
                    "metric": "fit_residual_reflected",
                    "value": refl["observation_fit_residual"],
                    "status": fit_status(refl["observation_fit_residual"], geom.fit_warn_threshold),
                    "detail": "Matched reflected plane-wave residual on reflection plane.",
                },
                {
                    "case": case,
                    "material": material,
                    "pol": pol,
                    "rect": geom.trans_rect,
                    "run_label": run_label,
                    "f_hz": float(f_hz),
                    "theta_deg": float(theta_deg),
                    "observation_distance_lambda_scale": observation_distance_lambda_scale,
                    "metric": "fit_residual_transmitted",
                    "value": trans["observation_fit_residual"],
                    "status": fit_status(trans["observation_fit_residual"], geom.fit_warn_threshold),
                    "detail": "Matched transmitted plane-wave residual on transmission plane.",
                },
                {
                    "case": case,
                    "material": material,
                    "pol": pol,
                    "rect": geom.refl_rect,
                    "run_label": run_label,
                    "f_hz": float(f_hz),
                    "theta_deg": float(theta_deg),
                    "observation_distance_lambda_scale": observation_distance_lambda_scale,
                    "metric": "incident_fit_residual",
                    "value": refl["incident_fit_residual"],
                    "status": fit_status(refl["incident_fit_residual"], geom.fit_warn_threshold),
                    "detail": "Analytic incident plane-wave residual on reflection plane.",
                },
                {
                    "case": case,
                    "material": material,
                    "pol": pol,
                    "rect": geom.trans_rect,
                    "run_label": run_label,
                    "f_hz": float(f_hz),
                    "theta_deg": float(theta_deg),
                    "observation_distance_lambda_scale": observation_distance_lambda_scale,
                    "metric": "incident_fit_residual",
                    "value": trans["incident_fit_residual"],
                    "status": fit_status(trans["incident_fit_residual"], geom.fit_warn_threshold),
                    "detail": "Analytic incident plane-wave residual on transmission plane.",
                },
            ]
        )

    raw_truth = (
        pd.DataFrame(truth_rows)
        if truth_rows
        else pd.DataFrame(
            columns=[
                "case",
                "material",
                "pol",
                "run_label",
                "f_hz",
                "theta_deg",
                "observation_distance_lambda_scale",
                "field_type_refl",
                "field_type_trans",
                "R",
                "T",
            ]
        )
    )
    qc_report = pd.DataFrame(qc_rows)
    return raw_truth, qc_report


def build_wide_truth(raw_truth: pd.DataFrame) -> pd.DataFrame:
    if raw_truth.empty:
        return raw_truth.copy()

    merge_columns = [
        "case",
        "material",
        "run_label",
        "f_hz",
        "theta_deg",
        "observation_distance_lambda_scale",
    ]
    te_rows = (
        raw_truth[raw_truth["pol"] == "TE"][merge_columns + ["R", "T", "field_type_refl", "field_type_trans"]]
        .rename(
            columns={
                "R": "R_TE",
                "T": "T_TE",
                "field_type_refl": "field_type_TE_refl",
                "field_type_trans": "field_type_TE_trans",
            }
        )
        .copy()
    )
    tm_rows = (
        raw_truth[raw_truth["pol"] == "TM"][merge_columns + ["R", "T", "field_type_refl", "field_type_trans"]]
        .rename(
            columns={
                "R": "R_TM",
                "T": "T_TM",
                "field_type_refl": "field_type_TM_refl",
                "field_type_trans": "field_type_TM_trans",
            }
        )
        .copy()
    )
    wide = te_rows.merge(tm_rows, on=merge_columns, how="outer").sort_values(merge_columns).reset_index(drop=True)

    for expected in ["R_TE", "R_TM", "T_TE", "T_TM"]:
        if expected not in wide.columns:
            wide[expected] = np.nan + 1j * np.nan

    return wide


def _independent_pec_phase_lock(row: pd.Series, geom: GeometryConfig) -> dict[str, complex]:
    return {
        "TE": geom.pec_target_reflection_te * np.exp(-1j * np.angle(row["R_TE"])) if pd.notna(row["R_TE"]) else 1.0 + 0j,
        "TM": geom.pec_target_reflection_tm * np.exp(-1j * np.angle(row["R_TM"])) if pd.notna(row["R_TM"]) else 1.0 + 0j,
    }


def _shared_common_pec_phase_lock(row: pd.Series, geom: GeometryConfig) -> dict[str, complex]:
    align_terms: list[complex] = []
    if pd.notna(row["R_TE"]):
        align_terms.append(complex(geom.pec_target_reflection_te) * np.conj(complex(row["R_TE"])))
    if pd.notna(row["R_TM"]):
        align_terms.append(complex(geom.pec_target_reflection_tm) * np.conj(complex(row["R_TM"])))
    if not align_terms:
        common_lock = 1.0 + 0j
    else:
        align = sum(align_terms)
        common_lock = align / abs(align) if abs(align) > 0.0 else 1.0 + 0j
    return {"TE": common_lock, "TM": common_lock}


def apply_pec_phase_lock(
    wide_truth: pd.DataFrame,
    geom: GeometryConfig,
    mode: str = "independent",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if wide_truth.empty:
        return wide_truth.copy(), pd.DataFrame()

    if mode not in {"independent", "shared_common"}:
        raise ValueError(f"Unsupported PEC phase-lock mode: {mode!r}")

    wide = wide_truth.copy()
    pec_rows = wide[wide["case"] == geom.pec_case].copy()
    phase_lock_rows: list[dict] = []

    if pec_rows.empty:
        return wide, pd.DataFrame(phase_lock_rows)

    exact_phase_lock_map = {}
    shared_phase_lock_candidates: dict[tuple[float, float, float], list[dict[str, complex]]] = {}
    shared_phase_lock_map: dict[tuple[float, float, float], dict[str, complex]] = {}
    shared_phase_lock_tol = 1e-12
    for _, row in pec_rows.iterrows():
        shared_key = (
            float(row["f_hz"]),
            float(row["theta_deg"]),
            float(row["observation_distance_lambda_scale"]),
        )
        exact_key = (
            *shared_key,
            str(row.get("run_label", "")),
        )
        lock = (
            _independent_pec_phase_lock(row, geom)
            if mode == "independent"
            else _shared_common_pec_phase_lock(row, geom)
        )
        exact_phase_lock_map[exact_key] = lock
        shared_phase_lock_candidates.setdefault(shared_key, []).append(lock)
        phase_lock_rows.extend(
            [
                {
                    "case": geom.pec_case,
                    "material": row["material"],
                    "pol": "TE",
                    "rect": geom.refl_rect,
                    "run_label": row.get("run_label", ""),
                    "f_hz": row["f_hz"],
                    "theta_deg": row["theta_deg"],
                    "observation_distance_lambda_scale": row["observation_distance_lambda_scale"],
                    "metric": "pec_phase_lock_deg" if mode == "independent" else "pec_phase_lock_shared_common_deg",
                    "value": float(np.rad2deg(np.angle(lock["TE"]))),
                    "status": "ok",
                    "detail": (
                        f"Independent phase-only correction applied so PEC R_TE approaches {geom.pec_target_reflection_te:+.0f} on the real axis."
                        if mode == "independent"
                        else "Shared common phase-only correction applied to both TE and TM using the PEC row."
                    ),
                },
                {
                    "case": geom.pec_case,
                    "material": row["material"],
                    "pol": "TM",
                    "rect": geom.refl_rect,
                    "run_label": row.get("run_label", ""),
                    "f_hz": row["f_hz"],
                    "theta_deg": row["theta_deg"],
                    "observation_distance_lambda_scale": row["observation_distance_lambda_scale"],
                    "metric": "pec_phase_lock_deg" if mode == "independent" else "pec_phase_lock_shared_common_deg",
                    "value": float(np.rad2deg(np.angle(lock["TM"]))),
                    "status": "ok",
                    "detail": (
                        f"Independent phase-only correction applied so PEC R_TM approaches {geom.pec_target_reflection_tm:+.0f} on the real axis."
                        if mode == "independent"
                        else "Shared common phase-only correction applied to both TE and TM using the PEC row."
                    ),
                },
            ]
        )

    for shared_key, candidates in shared_phase_lock_candidates.items():
        reference = candidates[0]
        if all(
            abs(candidate["TE"] - reference["TE"]) <= shared_phase_lock_tol
            and abs(candidate["TM"] - reference["TM"]) <= shared_phase_lock_tol
            for candidate in candidates[1:]
        ):
            shared_phase_lock_map[shared_key] = reference

    for index, row in wide.iterrows():
        shared_key = (
            float(row["f_hz"]),
            float(row["theta_deg"]),
            float(row["observation_distance_lambda_scale"]),
        )
        exact_key = (
            *shared_key,
            str(row.get("run_label", "")),
        )
        lock = exact_phase_lock_map.get(exact_key)
        if lock is None:
            lock = shared_phase_lock_map.get(shared_key)
        if lock is None:
            continue
        wide.at[index, "R_TE"] = row["R_TE"] * lock["TE"]
        wide.at[index, "R_TM"] = row["R_TM"] * lock["TM"]

    return wide, pd.DataFrame(phase_lock_rows)


def augment_truth_table_with_raw_reference(
    truth: pd.DataFrame,
    raw_truth: pd.DataFrame,
    current_label: str,
) -> pd.DataFrame:
    if truth.empty:
        return truth.copy()

    augmented = truth.copy()
    id_columns = truth_table_id_columns(truth)
    raw_reflection_columns: list[str] = []
    rename_map: dict[str, str] = {}

    for prefix in ("R_TE", "R_TM"):
        for suffix in COMPLEX_COMPONENT_SUFFIXES:
            column = f"{prefix}_{suffix}"
            if column not in augmented.columns or column not in raw_truth.columns:
                continue
            augmented[f"{prefix}_{current_label}_{suffix}"] = augmented[column]
            raw_reflection_columns.append(column)
            rename_map[column] = f"{prefix}_raw_{suffix}"

    if raw_reflection_columns:
        raw_reflections = raw_truth[id_columns + raw_reflection_columns].rename(columns=rename_map)
        augmented = augmented.merge(raw_reflections, on=id_columns, how="left")

    return augmented


def save_truth_tables(
    raw_truth: pd.DataFrame,
    shared_common_truth: pd.DataFrame,
    locked_truth: pd.DataFrame,
    output_dir: Path,
) -> tuple[Path, Path, Path, pd.DataFrame, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "truth_table_linear_raw.csv"
    shared_common_path = output_dir / "truth_table_linear_shared_common_lock.csv"
    locked_path = output_dir / "truth_table_linear_locked.csv"
    shared_common_augmented = augment_truth_table_with_raw_reference(
        shared_common_truth,
        raw_truth,
        "shared_common_lock",
    )
    locked_augmented = augment_truth_table_with_raw_reference(
        locked_truth,
        raw_truth,
        "locked",
    )
    raw_truth.to_csv(raw_path, index=False)
    shared_common_augmented.to_csv(shared_common_path, index=False)
    locked_augmented.to_csv(locked_path, index=False)
    return raw_path, shared_common_path, locked_path, shared_common_augmented, locked_augmented


def build_cp_lock_variant_comparison(
    cp_raw: pd.DataFrame,
    cp_shared_common: pd.DataFrame,
    cp_locked: pd.DataFrame,
) -> pd.DataFrame:
    id_columns = ["case", "material", "f_hz", "theta_deg"]
    if "run_label" in cp_raw.columns:
        id_columns.append("run_label")
    if "observation_distance_lambda_scale" in cp_raw.columns:
        id_columns.append("observation_distance_lambda_scale")

    meta_columns = [
        "cp_truth_region",
        "cp_truth_region_reason",
        "cp_use_for_main_claim",
        "cp_use_for_caution_only",
    ]
    base = cp_raw[id_columns + [column for column in meta_columns if column in cp_raw.columns]].copy()

    def rename_variant(df: pd.DataFrame, suffix: str) -> pd.DataFrame:
        keep = id_columns + [
            "Gamma_X_real",
            "Gamma_X_imag",
            "Gamma_X_mag",
            "Gamma_X_phase_deg",
            "Gamma_C_real",
            "Gamma_C_imag",
            "Gamma_C_mag",
            "Gamma_C_phase_deg",
        ]
        out = df[keep].copy()
        rename_map = {column: f"{column}_{suffix}" for column in keep if column not in id_columns}
        return out.rename(columns=rename_map)

    merged = base.merge(rename_variant(cp_raw, "raw"), on=id_columns, how="left")
    merged = merged.merge(rename_variant(cp_shared_common, "shared_common"), on=id_columns, how="left")
    merged = merged.merge(rename_variant(cp_locked, "locked"), on=id_columns, how="left")

    for branch in ("Gamma_X", "Gamma_C"):
        merged[f"delta_{branch}_mag_shared_common_minus_raw"] = (
            merged[f"{branch}_mag_shared_common"] - merged[f"{branch}_mag_raw"]
        )
        merged[f"delta_{branch}_mag_locked_minus_raw"] = (
            merged[f"{branch}_mag_locked"] - merged[f"{branch}_mag_raw"]
        )
        merged[f"abs_delta_{branch}_mag_shared_common_minus_raw"] = np.abs(
            merged[f"delta_{branch}_mag_shared_common_minus_raw"]
        )
        merged[f"abs_delta_{branch}_mag_locked_minus_raw"] = np.abs(
            merged[f"delta_{branch}_mag_locked_minus_raw"]
        )
        merged[f"{branch}_mag_locked_gt_raw"] = (
            merged[f"{branch}_mag_locked"] > merged[f"{branch}_mag_raw"]
        )
        merged[f"{branch}_mag_shared_common_gt_raw"] = (
            merged[f"{branch}_mag_shared_common"] > merged[f"{branch}_mag_raw"]
        )

    return merged


def build_cp_lock_variant_summary(comparison: pd.DataFrame) -> pd.DataFrame:
    subset_masks = {
        "all_rows": pd.Series(True, index=comparison.index),
        "main_claim_rows": comparison["cp_use_for_main_claim"].fillna(False).astype(bool),
        "nonpec_rows": comparison["case"].astype(str).str.lower() != "pec",
        "main_claim_nonpec_rows": comparison["cp_use_for_main_claim"].fillna(False).astype(bool)
        & (comparison["case"].astype(str).str.lower() != "pec"),
    }
    summary_rows: list[dict[str, object]] = []

    for subset_name, mask in subset_masks.items():
        subset = comparison.loc[mask].copy()
        if subset.empty:
            continue
        for branch in ("Gamma_X", "Gamma_C"):
            for variant in ("shared_common", "locked"):
                delta_col = f"delta_{branch}_mag_{variant}_minus_raw"
                abs_delta_col = f"abs_delta_{branch}_mag_{variant}_minus_raw"
                gt_col = f"{branch}_mag_{variant}_gt_raw"
                summary_rows.append(
                    {
                        "subset": subset_name,
                        "branch": branch,
                        "variant": variant,
                        "row_count": int(len(subset)),
                        "mean_delta_mag": float(subset[delta_col].mean()),
                        "median_delta_mag": float(subset[delta_col].median()),
                        "max_delta_mag": float(subset[delta_col].max()),
                        "min_delta_mag": float(subset[delta_col].min()),
                        "max_abs_delta_mag": float(subset[abs_delta_col].max()),
                        "mean_abs_delta_mag": float(subset[abs_delta_col].mean()),
                        "gt_raw_count": int(subset[gt_col].sum()),
                    }
                )

    return pd.DataFrame(summary_rows)


def finalize_truth_table(wide_truth: pd.DataFrame, geom: GeometryConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict] = []
    qc_rows: list[dict] = []

    if wide_truth.empty:
        empty_truth = pd.DataFrame(
            columns=[
                "case",
                "material",
                "run_label",
                "f_hz",
                "theta_deg",
                "observation_distance_lambda_scale",
                *TRUTH_REGION_COLUMNS,
                *OBSERVATION_METADATA_COLUMNS,
                "field_type_TE_refl",
                "field_type_TE_trans",
                "field_type_TM_refl",
                "field_type_TM_trans",
                "R_TE_real",
                "R_TE_imag",
                "R_TE_mag",
                "R_TE_phase_deg",
                "T_TE_real",
                "T_TE_imag",
                "T_TE_mag",
                "T_TE_phase_deg",
                "R_TM_real",
                "R_TM_imag",
                "R_TM_mag",
                "R_TM_phase_deg",
                "T_TM_real",
                "T_TM_imag",
                "T_TM_mag",
                "T_TM_phase_deg",
            ]
        )
        return empty_truth, pd.DataFrame(qc_rows)

    for _, row in wide_truth.iterrows():
        r_te = complex(row["R_TE"])
        r_tm = complex(row["R_TM"])
        t_te = complex(row["T_TE"])
        t_tm = complex(row["T_TM"])
        theta_deg = float(row["theta_deg"])
        freq_hz = float(row["f_hz"])
        obs_scale = float(row["observation_distance_lambda_scale"])

        rows.append(
            {
                "case": row["case"],
                "material": row["material"],
                "run_label": row.get("run_label", ""),
                "f_hz": freq_hz,
                "theta_deg": theta_deg,
                "observation_distance_lambda_scale": obs_scale,
                **build_truth_region_columns(theta_deg, obs_scale, str(row.get("run_label", ""))),
                **build_observation_metadata(theta_deg, freq_hz, obs_scale, geom),
                "field_type_TE_refl": row.get("field_type_TE_refl", ""),
                "field_type_TE_trans": row.get("field_type_TE_trans", ""),
                "field_type_TM_refl": row.get("field_type_TM_refl", ""),
                "field_type_TM_trans": row.get("field_type_TM_trans", ""),
                **complex_columns("R_TE", r_te),
                **complex_columns("T_TE", t_te),
                **complex_columns("R_TM", r_tm),
                **complex_columns("T_TM", t_tm),
            }
        )

        te_passivity = passivity_excess(r_te, t_te)
        tm_passivity = passivity_excess(r_tm, t_tm)
        qc_rows.extend(
            [
                {
                    "case": row["case"],
                    "material": row["material"],
                    "pol": "TE",
                    "rect": "both",
                    "run_label": row.get("run_label", ""),
                    "f_hz": freq_hz,
                    "theta_deg": theta_deg,
                    "observation_distance_lambda_scale": obs_scale,
                    "metric": "passivity_excess",
                    "value": te_passivity,
                    "status": passivity_status(te_passivity, geom.passivity_tolerance),
                    "detail": "|R_TE|^2 + |T_TE|^2 - 1",
                },
                {
                    "case": row["case"],
                    "material": row["material"],
                    "pol": "TM",
                    "rect": "both",
                    "run_label": row.get("run_label", ""),
                    "f_hz": freq_hz,
                    "theta_deg": theta_deg,
                    "observation_distance_lambda_scale": obs_scale,
                    "metric": "passivity_excess",
                    "value": tm_passivity,
                    "status": passivity_status(tm_passivity, geom.passivity_tolerance),
                    "detail": "|R_TM|^2 + |T_TM|^2 - 1",
                },
            ]
        )

    truth_df = pd.DataFrame(rows).sort_values(
        ["case", "f_hz", "observation_distance_lambda_scale", "theta_deg", "run_label"]
    ).reset_index(drop=True)
    qc_df = pd.DataFrame(qc_rows)
    return truth_df, qc_df


def main() -> None:
    stage_root = find_stage_root(Path(__file__))
    parser = argparse.ArgumentParser(
        description="Build linear-basis truth table from ideal incident plane-wave scattered-field exports."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=stage_root / "config" / "manifest.csv",
        help="Manifest describing case/pol/rect/f/theta/csv mapping.",
    )
    parser.add_argument(
        "--geometry",
        type=Path,
        default=stage_root / "config" / "geometry.yaml",
        help="Geometry / QC configuration file.",
    )
    parser.add_argument(
        "--normalized-output",
        type=Path,
        default=stage_root / "csv" / "normalized" / "normalized_measurements.csv",
        help="Optional normalized field dump path.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=stage_root / "results",
        help="Directory for truth table, QC report, and debug maps.",
    )
    parser.add_argument(
        "--with-cp-transform",
        action="store_true",
        help="Also derive truth_table_cp.csv from the linear reflection table.",
    )
    parser.add_argument(
        "--debug-maps",
        action="store_true",
        help="Write pointwise scalar/model/residual maps into results/debug_maps.",
    )
    parser.add_argument(
        "--allow-final-qc-failures",
        action="store_true",
        help="Keep written outputs even if the post-lock geometry QC still contains fail rows.",
    )
    args = parser.parse_args()

    geom = load_geometry_config(args.geometry)
    manifest = read_manifest(args.manifest, stage_root)
    measurements = load_normalized_measurements(manifest, geom=geom)

    args.normalized_output.parent.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    qc_report_path = args.output_dir / "qc_report.csv"
    debug_dir = args.output_dir / "debug_maps"
    if args.debug_maps or geom.debug_maps:
        debug_dir.mkdir(parents=True, exist_ok=True)
    else:
        debug_dir = None

    measurements.to_csv(args.normalized_output, index=False)

    theta_grid = theta_grid_from_measurements(measurements)
    qc_pre = pd.DataFrame(
        validate_point_cloud_consistency(measurements, expected_n=geom.expected_point_count)
        + validate_pec_field_type_lock(measurements, geom)
        + validate_geometry_lock(theta_grid, geom)
    )
    if not qc_pre.empty and (qc_pre["status"] == "fail").any():
        qc_pre.to_csv(qc_report_path, index=False)
        raise ValueError(f"Pre-estimation QC failed. See {qc_report_path}")

    raw_truth, qc_initial = build_raw_truth_table(measurements, geom, debug_dir)
    wide_truth_raw = build_wide_truth(raw_truth)
    wide_truth_shared_common, qc_phase_shared_common = apply_pec_phase_lock(
        wide_truth_raw,
        geom,
        mode="shared_common",
    )
    wide_truth_locked, qc_phase = apply_pec_phase_lock(wide_truth_raw, geom)
    raw_truth_df, _ = finalize_truth_table(wide_truth_raw, geom)
    shared_common_truth_base, qc_final_shared_common = finalize_truth_table(wide_truth_shared_common, geom)
    locked_truth_base, qc_final = finalize_truth_table(wide_truth_locked, geom)
    qc_geometry_locked = pd.DataFrame(validate_geometry_lock(theta_grid, geom, wide_truth_locked))

    qc_frames = [frame for frame in [qc_pre, qc_initial, qc_phase, qc_final, qc_geometry_locked] if not frame.empty]
    qc_report = pd.concat(qc_frames, ignore_index=True) if qc_frames else pd.DataFrame()

    extra_qc = pd.DataFrame(
        build_pec_rows(wide_truth_locked, geom.pec_case)
        + build_smoothness_rows(
            wide_truth_locked,
            quantity_columns=["R_TE", "R_TM", "T_TE", "T_TM"],
            jump_db_threshold=geom.smoothness_jump_db,
        )
    )
    if not extra_qc.empty:
        qc_report = pd.concat([qc_report, extra_qc], ignore_index=True) if not qc_report.empty else extra_qc

    raw_truth_path, shared_common_truth_path, locked_truth_path, shared_common_truth_df, locked_truth_df = save_truth_tables(
        raw_truth_df,
        shared_common_truth_base,
        locked_truth_base,
        args.output_dir,
    )
    qc_report.to_csv(qc_report_path, index=False)

    print("=" * 72)
    print("Ideal incident plane-wave TE/TM scattered-field truth-table pipeline")
    print("=" * 72)
    print(f"Manifest rows:         {len(manifest)}")
    print(f"Normalized samples:    {len(measurements)}")
    print(f"Raw truth rows:        {len(raw_truth_df)}")
    print(f"Locked truth rows:     {len(locked_truth_df)}")
    print(f"QC report rows:        {len(qc_report)}")
    print(f"Normalized dump:       {args.normalized_output}")
    print(f"Raw truth table:       {raw_truth_path}")
    print(f"Shared common lock:    {shared_common_truth_path}")
    print(f"Locked truth table:    {locked_truth_path}")
    print(f"QC report:             {qc_report_path}")

    if args.with_cp_transform:
        cp_truth_raw = build_cp_truth_table(raw_truth_df)
        cp_truth_raw_path = args.output_dir / "truth_table_cp_raw.csv"
        cp_truth_raw.to_csv(cp_truth_raw_path, index=False)

        cp_truth_shared_common = build_cp_truth_table(shared_common_truth_df)
        cp_truth_shared_common_path = args.output_dir / "truth_table_cp_shared_common_lock.csv"
        cp_truth_shared_common.to_csv(cp_truth_shared_common_path, index=False)

        cp_truth = build_cp_truth_table(locked_truth_df)
        cp_truth_path = args.output_dir / "truth_table_cp.csv"
        cp_truth.to_csv(cp_truth_path, index=False)
        cp_variant_comparison = build_cp_lock_variant_comparison(
            cp_truth_raw,
            cp_truth_shared_common,
            cp_truth,
        )
        cp_variant_comparison_path = args.output_dir / "truth_table_cp_lock_variant_comparison.csv"
        cp_variant_comparison.to_csv(cp_variant_comparison_path, index=False)
        cp_variant_summary = build_cp_lock_variant_summary(cp_variant_comparison)
        cp_variant_summary_path = args.output_dir / "truth_table_cp_lock_variant_summary.csv"
        cp_variant_summary.to_csv(cp_variant_summary_path, index=False)
        print(f"CP raw truth table:    {cp_truth_raw_path}")
        print(f"CP shared common:      {cp_truth_shared_common_path}")
        print(f"CP truth table:        {cp_truth_path}")
        print(f"CP variant compare:    {cp_variant_comparison_path}")
        print(f"CP variant summary:    {cp_variant_summary_path}")

    if not qc_geometry_locked.empty and (qc_geometry_locked["status"] == "fail").any():
        if args.allow_final_qc_failures:
            print(f"Final geometry lock QC contains fail rows. See {qc_report_path}")
        else:
            raise ValueError(f"Geometry lock QC failed after PEC locking. See {qc_report_path}")


if __name__ == "__main__":
    main()
