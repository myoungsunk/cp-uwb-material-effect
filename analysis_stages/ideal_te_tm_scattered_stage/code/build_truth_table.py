from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from cp_transform import build_cp_truth_table
from estimator import matched_plane_wave_estimator
from geometry import (
    GeometryConfig,
    incident_hat,
    load_geometry_config,
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
    incident_field = analytic_incident_field(points, f_hz, theta_deg, pol, geom)
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


def apply_pec_phase_lock(wide_truth: pd.DataFrame, geom: GeometryConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    if wide_truth.empty:
        return wide_truth.copy(), pd.DataFrame()

    wide = wide_truth.copy()
    pec_rows = wide[wide["case"] == geom.pec_case].copy()
    phase_lock_rows: list[dict] = []

    if pec_rows.empty:
        return wide, pd.DataFrame(phase_lock_rows)

    phase_lock_map = {}
    for _, row in pec_rows.iterrows():
        key = (
            float(row["f_hz"]),
            float(row["theta_deg"]),
            float(row["observation_distance_lambda_scale"]),
            str(row.get("run_label", "")),
        )
        phase_lock_map[key] = {
            "TE": geom.pec_target_reflection_te * np.exp(-1j * np.angle(row["R_TE"])) if pd.notna(row["R_TE"]) else 1.0 + 0j,
            "TM": geom.pec_target_reflection_tm * np.exp(-1j * np.angle(row["R_TM"])) if pd.notna(row["R_TM"]) else 1.0 + 0j,
        }
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
                    "metric": "pec_phase_lock_deg",
                    "value": float(np.rad2deg(np.angle(phase_lock_map[key]["TE"]))),
                    "status": "ok",
                    "detail": f"Phase-only correction applied so PEC R_TE approaches {geom.pec_target_reflection_te:+.0f} on the real axis.",
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
                    "metric": "pec_phase_lock_deg",
                    "value": float(np.rad2deg(np.angle(phase_lock_map[key]["TM"]))),
                    "status": "ok",
                    "detail": f"Phase-only correction applied so PEC R_TM approaches {geom.pec_target_reflection_tm:+.0f} on the real axis.",
                },
            ]
        )

    for index, row in wide.iterrows():
        key = (
            float(row["f_hz"]),
            float(row["theta_deg"]),
            float(row["observation_distance_lambda_scale"]),
            str(row.get("run_label", "")),
        )
        if key not in phase_lock_map:
            continue
        wide.at[index, "R_TE"] = row["R_TE"] * phase_lock_map[key]["TE"]
        wide.at[index, "R_TM"] = row["R_TM"] * phase_lock_map[key]["TM"]

    return wide, pd.DataFrame(phase_lock_rows)


def augment_locked_truth_table(locked_truth: pd.DataFrame, raw_truth: pd.DataFrame) -> pd.DataFrame:
    if locked_truth.empty:
        return locked_truth.copy()

    augmented = locked_truth.copy()
    id_columns = truth_table_id_columns(locked_truth)
    raw_reflection_columns: list[str] = []
    rename_map: dict[str, str] = {}

    for prefix in ("R_TE", "R_TM"):
        for suffix in COMPLEX_COMPONENT_SUFFIXES:
            column = f"{prefix}_{suffix}"
            if column not in augmented.columns or column not in raw_truth.columns:
                continue
            augmented[f"{prefix}_locked_{suffix}"] = augmented[column]
            raw_reflection_columns.append(column)
            rename_map[column] = f"{prefix}_raw_{suffix}"

    if raw_reflection_columns:
        raw_reflections = raw_truth[id_columns + raw_reflection_columns].rename(columns=rename_map)
        augmented = augmented.merge(raw_reflections, on=id_columns, how="left")

    return augmented


def save_raw_and_locked_truth_tables(
    raw_truth: pd.DataFrame,
    locked_truth: pd.DataFrame,
    output_dir: Path,
) -> tuple[Path, Path, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "truth_table_linear_raw.csv"
    locked_path = output_dir / "truth_table_linear_locked.csv"
    locked_augmented = augment_locked_truth_table(locked_truth, raw_truth)
    raw_truth.to_csv(raw_path, index=False)
    locked_augmented.to_csv(locked_path, index=False)
    return raw_path, locked_path, locked_augmented


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

        rows.append(
            {
                "case": row["case"],
                "material": row["material"],
                "run_label": row.get("run_label", ""),
                "f_hz": float(row["f_hz"]),
                "theta_deg": float(row["theta_deg"]),
                "observation_distance_lambda_scale": float(row["observation_distance_lambda_scale"]),
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
                    "f_hz": float(row["f_hz"]),
                    "theta_deg": float(row["theta_deg"]),
                    "observation_distance_lambda_scale": float(row["observation_distance_lambda_scale"]),
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
                    "f_hz": float(row["f_hz"]),
                    "theta_deg": float(row["theta_deg"]),
                    "observation_distance_lambda_scale": float(row["observation_distance_lambda_scale"]),
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
    wide_truth_locked, qc_phase = apply_pec_phase_lock(wide_truth_raw, geom)
    raw_truth_df, _ = finalize_truth_table(wide_truth_raw, geom)
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

    raw_truth_path, locked_truth_path, locked_truth_df = save_raw_and_locked_truth_tables(
        raw_truth_df,
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
    print(f"Locked truth table:    {locked_truth_path}")
    print(f"QC report:             {qc_report_path}")

    if args.with_cp_transform:
        cp_truth = build_cp_truth_table(locked_truth_df)
        cp_truth_path = args.output_dir / "truth_table_cp.csv"
        cp_truth.to_csv(cp_truth_path, index=False)
        print(f"CP truth table:        {cp_truth_path}")

    if not qc_geometry_locked.empty and (qc_geometry_locked["status"] == "fail").any():
        if args.allow_final_qc_failures:
            print(f"Final geometry lock QC contains fail rows. See {qc_report_path}")
        else:
            raise ValueError(f"Geometry lock QC failed after PEC locking. See {qc_report_path}")


if __name__ == "__main__":
    main()
