# Consolidated review copy for paper-pipeline code assessment.
# Stage: 1
# Role: Quality-control helpers for passivity, smoothness, PEC checks, and baseline checks.
# Source: analysis_stages/ideal_te_tm_scattered_stage/code/qc.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

import numpy as np
import pandas as pd


def _complex_row_value(row: pd.Series, prefix: str) -> complex:
    if prefix in row:
        return complex(row[prefix])
    real_key = f"{prefix}_real"
    imag_key = f"{prefix}_imag"
    if real_key in row and imag_key in row:
        return complex(float(row[real_key]), float(row[imag_key]))
    locked_real_key = f"{prefix}_locked_real"
    locked_imag_key = f"{prefix}_locked_imag"
    if locked_real_key in row and locked_imag_key in row:
        return complex(float(row[locked_real_key]), float(row[locked_imag_key]))
    raise KeyError(f"Could not reconstruct complex column '{prefix}' from row.")


def relative_l2_error(observed: np.ndarray, reference: np.ndarray) -> float:
    obs = np.asarray(observed, dtype=complex)
    ref = np.asarray(reference, dtype=complex)
    denom = np.linalg.norm(ref)
    if denom == 0:
        return 0.0
    return float(np.linalg.norm(obs - ref) / denom)


def baseline_status(value: float, good_threshold: float, warn_threshold: float) -> str:
    if value < good_threshold:
        return "ok"
    if value < warn_threshold:
        return "warn"
    return "fail"


def fit_status(value: float, warn_threshold: float) -> str:
    return "ok" if value < warn_threshold else "warn"


def passivity_excess(reflection_coeff: complex, transmission_coeff: complex) -> float:
    return float(np.abs(reflection_coeff) ** 2 + np.abs(transmission_coeff) ** 2 - 1.0)


def passivity_status(excess: float, tolerance: float) -> str:
    return "ok" if excess <= tolerance else "warn"


def magnitude_db(values: np.ndarray) -> np.ndarray:
    arr = np.abs(np.asarray(values, dtype=complex))
    return 20.0 * np.log10(np.maximum(arr, 1e-15))


def build_smoothness_rows(truth_df: pd.DataFrame, quantity_columns: list[str], jump_db_threshold: float) -> list[dict]:
    rows: list[dict] = []
    if truth_df.empty:
        return rows

    group_columns = ["case", "f_hz"]
    if "observation_distance_lambda_scale" in truth_df.columns:
        group_columns.append("observation_distance_lambda_scale")
    if "run_label" in truth_df.columns:
        group_columns.append("run_label")

    for quantity in quantity_columns:
        for group_key, sub in truth_df.groupby(group_columns, dropna=False):
            case = group_key[0]
            f_hz = group_key[1]
            observation_distance_lambda_scale = group_key[2] if len(group_key) > 2 else np.nan
            run_label = group_key[3] if len(group_key) > 3 else ""
            ordered = sub.sort_values("theta_deg")
            if len(ordered) < 2:
                continue
            jumps = np.abs(np.diff(magnitude_db(ordered[quantity].to_numpy())))
            max_jump = float(jumps.max()) if len(jumps) else 0.0
            rows.append(
                {
                    "case": case,
                    "material": ordered["material"].iloc[0],
                    "pol": quantity.split("_", 1)[1],
                    "rect": "theta_sweep",
                    "run_label": run_label,
                    "f_hz": float(f_hz),
                    "theta_deg": np.nan,
                    "observation_distance_lambda_scale": observation_distance_lambda_scale,
                    "metric": f"smoothness_max_jump_db_{quantity}",
                    "value": max_jump,
                    "status": "ok" if max_jump <= jump_db_threshold else "warn",
                    "detail": "Adjacent-theta magnitude jump in dB.",
                }
            )
    return rows


def build_pec_rows(truth_df: pd.DataFrame, pec_case: str) -> list[dict]:
    rows: list[dict] = []
    if truth_df.empty or "case" not in truth_df.columns:
        rows.append(
            {
                "case": pec_case,
                "material": pec_case,
                "pol": "both",
                "rect": "both",
                "run_label": "",
                "f_hz": np.nan,
                "theta_deg": np.nan,
                "metric": "pec_presence",
                "value": np.nan,
                "status": "warn",
                "detail": "PEC case missing; phase/sign convention could not be locked.",
            }
        )
        return rows
    pec_df = truth_df[truth_df["case"] == pec_case].copy()
    if pec_df.empty:
        rows.append(
            {
                "case": pec_case,
                "material": pec_case,
                "pol": "both",
                "rect": "both",
                "run_label": "",
                "f_hz": np.nan,
                "theta_deg": np.nan,
                "metric": "pec_presence",
                "value": np.nan,
                "status": "warn",
                "detail": "PEC case missing; phase/sign convention could not be locked.",
            }
        )
        return rows

    for _, row in pec_df.iterrows():
        r_te = _complex_row_value(row, "R_TE")
        r_tm = _complex_row_value(row, "R_TM")
        t_te = _complex_row_value(row, "T_TE")
        t_tm = _complex_row_value(row, "T_TM")
        rows.extend(
            [
                {
                    "case": pec_case,
                    "material": row["material"],
                    "pol": "TE",
                    "rect": "refl_rect",
                    "run_label": row.get("run_label", ""),
                    "f_hz": row["f_hz"],
                    "theta_deg": row["theta_deg"],
                    "observation_distance_lambda_scale": row.get("observation_distance_lambda_scale", np.nan),
                    "metric": "pec_abs_R_TE_minus_1",
                    "value": abs(abs(r_te) - 1.0),
                    "status": "ok" if abs(abs(r_te) - 1.0) <= 0.1 else "warn",
                    "detail": "PEC reflection magnitude should be close to 1.",
                },
                {
                    "case": pec_case,
                    "material": row["material"],
                    "pol": "TM",
                    "rect": "refl_rect",
                    "run_label": row.get("run_label", ""),
                    "f_hz": row["f_hz"],
                    "theta_deg": row["theta_deg"],
                    "observation_distance_lambda_scale": row.get("observation_distance_lambda_scale", np.nan),
                    "metric": "pec_abs_R_TM_minus_1",
                    "value": abs(abs(r_tm) - 1.0),
                    "status": "ok" if abs(abs(r_tm) - 1.0) <= 0.1 else "warn",
                    "detail": "PEC reflection magnitude should be close to 1.",
                },
                {
                    "case": pec_case,
                    "material": row["material"],
                    "pol": "TE",
                    "rect": "trans_rect",
                    "run_label": row.get("run_label", ""),
                    "f_hz": row["f_hz"],
                    "theta_deg": row["theta_deg"],
                    "observation_distance_lambda_scale": row.get("observation_distance_lambda_scale", np.nan),
                    "metric": "pec_abs_T_TE",
                    "value": abs(t_te),
                    "status": "ok" if abs(t_te) <= 0.1 else "warn",
                    "detail": "PEC transmission magnitude should be close to 0.",
                },
                {
                    "case": pec_case,
                    "material": row["material"],
                    "pol": "TM",
                    "rect": "trans_rect",
                    "run_label": row.get("run_label", ""),
                    "f_hz": row["f_hz"],
                    "theta_deg": row["theta_deg"],
                    "observation_distance_lambda_scale": row.get("observation_distance_lambda_scale", np.nan),
                    "metric": "pec_abs_T_TM",
                    "value": abs(t_tm),
                    "status": "ok" if abs(t_tm) <= 0.1 else "warn",
                    "detail": "PEC transmission magnitude should be close to 0.",
                },
            ]
        )
    return rows
