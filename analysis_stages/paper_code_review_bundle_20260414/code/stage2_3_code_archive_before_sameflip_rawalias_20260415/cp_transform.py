from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


CP_MAIN_MAX_THETA_DEG = {
    "pec": 60.0,
    "concrete": 55.0,
    "glass": 60.0,
    "wood": 45.0,
}

CP_CAUTION_MAX_THETA_DEG = {
    "pec": 65.0,
    "concrete": 65.0,
    "glass": 65.0,
    "wood": 65.0,
}

CP_LIMITING_REASON = {
    "pec": "CP inherits the TE observation-limit branch; use PEC CP as main only through 60 deg.",
    "concrete": "CP main claim is limited by TM material sanity, which first fails at 60 deg.",
    "glass": "CP main claim is limited by TM material sanity at 65 deg and by the TE main region ending at 60 deg.",
    "wood": "CP main claim is limited by TM material sanity, which first fails at 50 deg.",
}


def _to_complex(df: pd.DataFrame, prefix: str) -> np.ndarray:
    return df[f"{prefix}_real"].to_numpy() + 1j * df[f"{prefix}_imag"].to_numpy()


def _classify_cp_truth_region(row: pd.Series) -> pd.Series:
    material = str(row.get("material", "")).strip().lower()
    theta_deg = float(row["theta_deg"])
    te_region = str(row.get("truth_region_TE", "")).strip().lower()
    tm_region = str(row.get("truth_region_TM", "")).strip().lower()
    main_max = CP_MAIN_MAX_THETA_DEG.get(material)
    caution_max = CP_CAUTION_MAX_THETA_DEG.get(material)
    reason = CP_LIMITING_REASON.get(
        material,
        "CP trust region falls back to the embedded linear truth-region classification.",
    )

    if material == "baseline":
        return pd.Series(
            {
                "cp_truth_region": "exclude",
                "cp_truth_region_reason": "Baseline rows are not CP reflection truth targets.",
                "cp_use_for_main_claim": False,
                "cp_use_for_caution_only": False,
            }
        )

    if te_region == "exclude" or tm_region == "exclude":
        return pd.Series(
            {
                "cp_truth_region": "exclude",
                "cp_truth_region_reason": "At least one linear branch is already excluded; CP cannot be a main or caution truth row.",
                "cp_use_for_main_claim": False,
                "cp_use_for_caution_only": False,
            }
        )

    if main_max is None or caution_max is None:
        if te_region == "main" and tm_region == "main":
            return pd.Series(
                {
                    "cp_truth_region": "main",
                    "cp_truth_region_reason": reason,
                    "cp_use_for_main_claim": True,
                    "cp_use_for_caution_only": False,
                }
            )
        if te_region in {"main", "caution"} and tm_region in {"main", "caution"}:
            return pd.Series(
                {
                    "cp_truth_region": "caution",
                    "cp_truth_region_reason": reason,
                    "cp_use_for_main_claim": False,
                    "cp_use_for_caution_only": True,
                }
            )
        return pd.Series(
            {
                "cp_truth_region": "exclude",
                "cp_truth_region_reason": reason,
                "cp_use_for_main_claim": False,
                "cp_use_for_caution_only": False,
            }
        )

    if theta_deg <= main_max and te_region == "main" and tm_region == "main":
        return pd.Series(
            {
                "cp_truth_region": "main",
                "cp_truth_region_reason": reason,
                "cp_use_for_main_claim": True,
                "cp_use_for_caution_only": False,
            }
        )

    if theta_deg <= caution_max:
        return pd.Series(
            {
                "cp_truth_region": "caution",
                "cp_truth_region_reason": f"{reason} Rows above the main-angle lock are caution-only.",
                "cp_use_for_main_claim": False,
                "cp_use_for_caution_only": True,
            }
        )

    return pd.Series(
        {
            "cp_truth_region": "exclude",
            "cp_truth_region_reason": "CP row is outside the locked main/caution angle range.",
            "cp_use_for_main_claim": False,
            "cp_use_for_caution_only": False,
        }
    )


def build_cp_truth_table(linear_truth: pd.DataFrame) -> pd.DataFrame:
    df = linear_truth.copy()
    r_te = _to_complex(df, "R_TE")
    r_tm = _to_complex(df, "R_TM")
    gamma_x = 0.5 * (r_te + r_tm)
    gamma_c = 0.5 * (r_te - r_tm)

    id_columns = ["case", "material", "f_hz", "theta_deg"]
    if "run_label" in df.columns:
        id_columns.append("run_label")
    if "observation_distance_lambda_scale" in df.columns:
        id_columns.append("observation_distance_lambda_scale")
    passthrough_columns = [
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
    out = df[id_columns + [column for column in passthrough_columns if column in df.columns]].copy()
    out["Gamma_X_real"] = np.real(gamma_x)
    out["Gamma_X_imag"] = np.imag(gamma_x)
    out["Gamma_X_mag"] = np.abs(gamma_x)
    out["Gamma_X_phase_deg"] = np.rad2deg(np.angle(gamma_x))
    out["Gamma_C_real"] = np.real(gamma_c)
    out["Gamma_C_imag"] = np.imag(gamma_c)
    out["Gamma_C_mag"] = np.abs(gamma_c)
    out["Gamma_C_phase_deg"] = np.rad2deg(np.angle(gamma_c))
    cp_truth = out.apply(_classify_cp_truth_region, axis=1)
    out = pd.concat([out, cp_truth], axis=1)
    out["note"] = "Derived from linear-basis reflection truth table; CP convention should still be checked explicitly."
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build CP truth table from linear TE/TM truth table.")
    parser.add_argument("linear_truth_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    args = parser.parse_args()

    linear_truth = pd.read_csv(args.linear_truth_csv)
    cp_truth = build_cp_truth_table(linear_truth)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    cp_truth.to_csv(args.output_csv, index=False)
    print(f"Wrote CP truth table: {args.output_csv}")


if __name__ == "__main__":
    main()
