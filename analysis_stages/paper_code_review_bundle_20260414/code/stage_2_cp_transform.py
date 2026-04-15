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

PEC_CP_SAME_MAX_MAG = 0.1
PEC_CP_FLIP_MIN_MAG = 0.9


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


def _add_same_flip_aliases(out: pd.DataFrame) -> pd.DataFrame:
    aliased = out.copy()
    for component in ("real", "imag", "mag", "phase_deg"):
        aliased[f"Gamma_same_{component}"] = aliased[f"Gamma_X_{component}"]
        aliased[f"Gamma_flip_{component}"] = aliased[f"Gamma_C_{component}"]
    aliased["cp_same_branch_source"] = "Gamma_X"
    aliased["cp_flip_branch_source"] = "Gamma_C"
    aliased["cp_same_branch_interpretation"] = "same_hand"
    aliased["cp_flip_branch_interpretation"] = "flipped_hand"
    return aliased


def _validate_pec_cp_convention(cp_truth: pd.DataFrame) -> None:
    cp_truth["cp_pec_same_flip_sanity_pass"] = True
    cp_truth["cp_pec_same_flip_sanity_note"] = (
        f"PEC convention check expects |Gamma_same| <= {PEC_CP_SAME_MAX_MAG:.2f} and "
        f"|Gamma_flip| >= {PEC_CP_FLIP_MIN_MAG:.2f}; same-hand maps to Gamma_X, flipped-hand maps to Gamma_C."
    )
    pec_mask = cp_truth["case"].astype(str).str.strip().str.lower().eq("pec")
    if not pec_mask.any():
        return

    pec_rows = cp_truth.loc[pec_mask].copy()
    fail_mask = (
        (pec_rows["Gamma_same_mag"] > PEC_CP_SAME_MAX_MAG)
        | (pec_rows["Gamma_flip_mag"] < PEC_CP_FLIP_MIN_MAG)
        | (pec_rows["Gamma_flip_mag"] <= pec_rows["Gamma_same_mag"])
    )
    cp_truth.loc[pec_mask, "cp_pec_same_flip_sanity_pass"] = ~fail_mask.to_numpy()
    if fail_mask.any():
        fail_rows = pec_rows.loc[fail_mask, ["theta_deg", "Gamma_same_mag", "Gamma_flip_mag"]]
        raise ValueError(
            "PEC CP same/flip sanity failed. Under the current Stage 1 PEC sign convention, "
            "Gamma_same should stay small and Gamma_flip should stay dominant.\n"
            + fail_rows.to_string(index=False)
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
    out = _add_same_flip_aliases(out)
    _validate_pec_cp_convention(out)
    out["note"] = (
        "Derived from linear-basis reflection truth table; under the current PEC convention "
        "Gamma_same maps to Gamma_X and Gamma_flip maps to Gamma_C."
    )
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
