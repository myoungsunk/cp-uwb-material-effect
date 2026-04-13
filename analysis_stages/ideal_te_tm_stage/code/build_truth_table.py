from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from cp_transform import build_cp_truth_table
from estimator import matched_plane_wave_estimator
from geometry import GeometryConfig, incident_hat, load_geometry_config, reflected_hat, transmitted_hat
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
    relative_l2_error,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


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
    points, total_field = extract_arrays(sub_df)
    incident_field = analytic_incident_field(points, f_hz, theta_deg, pol, geom)
    vector_mismatch = relative_l2_error(total_field, incident_field)

    if rect == geom.refl_rect:
        observation_field = total_field - incident_field
        observation_mode = "reflected"
        observation_hat = reflected_hat(theta_deg)
    elif rect == geom.trans_rect:
        observation_field = total_field
        observation_mode = "transmitted"
        observation_hat = transmitted_hat(theta_deg)
    else:
        raise ValueError(f"Unexpected rect value: {rect}")

    scalar_incident = project_vector_field(incident_field, theta_deg, pol, "incident", geom)
    scalar_observation = project_vector_field(observation_field, theta_deg, pol, observation_mode, geom)

    incident_estimate = matched_plane_wave_estimator(points, scalar_incident, f_hz, incident_hat(theta_deg))
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
        "vector_baseline_mismatch": vector_mismatch,
        "incident_amplitude": incident_estimate.amplitude,
        "incident_fit_residual": incident_estimate.residual,
        "observation_amplitude": observation_estimate.amplitude,
        "observation_fit_residual": observation_estimate.residual,
        "num_points": observation_estimate.num_points,
    }


def build_raw_truth_table(
    measurements: pd.DataFrame,
    geom: GeometryConfig,
    debug_dir: Path | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    grouped = {
        key: sub.sort_values(["point_id", "x", "y", "z"]).reset_index(drop=True)
        for key, sub in measurements.groupby(["case", "pol", "rect", "f_hz", "theta_deg"], sort=False)
    }

    truth_rows: list[dict] = []
    qc_rows: list[dict] = []
    run_keys = sorted({(case, pol, f_hz, theta_deg) for case, pol, _, f_hz, theta_deg in grouped})

    for case, pol, f_hz, theta_deg in run_keys:
        refl_key = (case, pol, geom.refl_rect, f_hz, theta_deg)
        trans_key = (case, pol, geom.trans_rect, f_hz, theta_deg)
        material = material_from_case(case)

        if refl_key not in grouped or trans_key not in grouped:
            qc_rows.append(
                {
                    "case": case,
                    "material": material,
                    "pol": pol,
                    "rect": "both",
                    "f_hz": float(f_hz),
                    "theta_deg": float(theta_deg),
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
                        "f_hz": float(f_hz),
                        "theta_deg": float(theta_deg),
                        "metric": "baseline_mismatch_vector",
                        "value": refl["vector_baseline_mismatch"],
                        "status": baseline_status(
                            refl["vector_baseline_mismatch"],
                            geom.baseline_good_threshold,
                            geom.baseline_warn_threshold,
                        ),
                        "detail": "Baseline total field vs analytic incident on reflection plane.",
                    },
                    {
                        "case": case,
                        "material": material,
                        "pol": pol,
                        "rect": geom.trans_rect,
                        "f_hz": float(f_hz),
                        "theta_deg": float(theta_deg),
                        "metric": "baseline_mismatch_vector",
                        "value": trans["vector_baseline_mismatch"],
                        "status": baseline_status(
                            trans["vector_baseline_mismatch"],
                            geom.baseline_good_threshold,
                            geom.baseline_warn_threshold,
                        ),
                        "detail": "Baseline total field vs analytic incident on transmission plane.",
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
                "f_hz": float(f_hz),
                "theta_deg": float(theta_deg),
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
                    "f_hz": float(f_hz),
                    "theta_deg": float(theta_deg),
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
                    "f_hz": float(f_hz),
                    "theta_deg": float(theta_deg),
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
                    "f_hz": float(f_hz),
                    "theta_deg": float(theta_deg),
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
                    "f_hz": float(f_hz),
                    "theta_deg": float(theta_deg),
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
        else pd.DataFrame(columns=["case", "material", "pol", "f_hz", "theta_deg", "R", "T"])
    )
    qc_report = pd.DataFrame(qc_rows)
    return raw_truth, qc_report


def apply_pec_phase_lock(raw_truth: pd.DataFrame, geom: GeometryConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    if raw_truth.empty:
        return raw_truth.copy(), pd.DataFrame()

    wide = (
        raw_truth.pivot(
            index=["case", "material", "f_hz", "theta_deg"],
            columns="pol",
            values=["R", "T"],
        )
        .sort_index()
    )
    wide.columns = [f"{left}_{right}" for left, right in wide.columns]
    wide = wide.reset_index()

    for expected in ["R_TE", "R_TM", "T_TE", "T_TM"]:
        if expected not in wide.columns:
            wide[expected] = np.nan + 1j * np.nan

    pec_rows = wide[wide["case"] == geom.pec_case].copy()
    phase_lock_rows: list[dict] = []

    if pec_rows.empty:
        return wide, pd.DataFrame(phase_lock_rows)

    phase_lock_map = {}
    for _, row in pec_rows.iterrows():
        key = (float(row["f_hz"]), float(row["theta_deg"]))
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
                    "f_hz": row["f_hz"],
                    "theta_deg": row["theta_deg"],
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
                    "f_hz": row["f_hz"],
                    "theta_deg": row["theta_deg"],
                    "metric": "pec_phase_lock_deg",
                    "value": float(np.rad2deg(np.angle(phase_lock_map[key]["TM"]))),
                    "status": "ok",
                    "detail": f"Phase-only correction applied so PEC R_TM approaches {geom.pec_target_reflection_tm:+.0f} on the real axis.",
                },
            ]
        )

    for index, row in wide.iterrows():
        key = (float(row["f_hz"]), float(row["theta_deg"]))
        if key not in phase_lock_map:
            continue
        wide.at[index, "R_TE"] = row["R_TE"] * phase_lock_map[key]["TE"]
        wide.at[index, "R_TM"] = row["R_TM"] * phase_lock_map[key]["TM"]

    return wide, pd.DataFrame(phase_lock_rows)


def finalize_truth_table(wide_truth: pd.DataFrame, geom: GeometryConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict] = []
    qc_rows: list[dict] = []

    if wide_truth.empty:
        empty_truth = pd.DataFrame(
            columns=[
                "case",
                "material",
                "f_hz",
                "theta_deg",
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
                "f_hz": float(row["f_hz"]),
                "theta_deg": float(row["theta_deg"]),
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
                    "f_hz": float(row["f_hz"]),
                    "theta_deg": float(row["theta_deg"]),
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
                    "f_hz": float(row["f_hz"]),
                    "theta_deg": float(row["theta_deg"]),
                    "metric": "passivity_excess",
                    "value": tm_passivity,
                    "status": passivity_status(tm_passivity, geom.passivity_tolerance),
                    "detail": "|R_TM|^2 + |T_TM|^2 - 1",
                },
            ]
        )

    truth_df = pd.DataFrame(rows).sort_values(["case", "f_hz", "theta_deg"]).reset_index(drop=True)
    qc_df = pd.DataFrame(qc_rows)
    return truth_df, qc_df


def main() -> None:
    stage_root = find_stage_root(Path(__file__))
    parser = argparse.ArgumentParser(
        description="Build linear-basis truth table from ideal incident plane-wave field exports."
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
    args = parser.parse_args()

    geom = load_geometry_config(args.geometry)
    manifest = read_manifest(args.manifest, stage_root)
    measurements = load_normalized_measurements(manifest, geom=geom)

    args.normalized_output.parent.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    debug_dir = args.output_dir / "debug_maps"
    if args.debug_maps or geom.debug_maps:
        debug_dir.mkdir(parents=True, exist_ok=True)
    else:
        debug_dir = None

    measurements.to_csv(args.normalized_output, index=False)

    raw_truth, qc_initial = build_raw_truth_table(measurements, geom, debug_dir)
    wide_truth, qc_phase = apply_pec_phase_lock(raw_truth, geom)
    truth_df, qc_final = finalize_truth_table(wide_truth, geom)

    qc_frames = [frame for frame in [qc_initial, qc_phase, qc_final] if not frame.empty]
    qc_report = pd.concat(qc_frames, ignore_index=True) if qc_frames else pd.DataFrame()

    extra_qc = pd.DataFrame(
        build_pec_rows(wide_truth, geom.pec_case)
        + build_smoothness_rows(
            wide_truth,
            quantity_columns=["R_TE", "R_TM", "T_TE", "T_TM"],
            jump_db_threshold=geom.smoothness_jump_db,
        )
    )
    if not extra_qc.empty:
        qc_report = pd.concat([qc_report, extra_qc], ignore_index=True) if not qc_report.empty else extra_qc

    linear_truth_path = args.output_dir / "truth_table_linear.csv"
    qc_report_path = args.output_dir / "qc_report.csv"
    truth_df.to_csv(linear_truth_path, index=False)
    qc_report.to_csv(qc_report_path, index=False)

    print("=" * 72)
    print("Ideal incident plane-wave TE/TM truth-table pipeline")
    print("=" * 72)
    print(f"Manifest rows:         {len(manifest)}")
    print(f"Normalized samples:    {len(measurements)}")
    print(f"Linear truth rows:     {len(truth_df)}")
    print(f"QC report rows:        {len(qc_report)}")
    print(f"Normalized dump:       {args.normalized_output}")
    print(f"Linear truth table:    {linear_truth_path}")
    print(f"QC report:             {qc_report_path}")

    if args.with_cp_transform:
        cp_truth = build_cp_truth_table(truth_df)
        cp_truth_path = args.output_dir / "truth_table_cp.csv"
        cp_truth.to_csv(cp_truth_path, index=False)
        print(f"CP truth table:        {cp_truth_path}")


if __name__ == "__main__":
    main()
