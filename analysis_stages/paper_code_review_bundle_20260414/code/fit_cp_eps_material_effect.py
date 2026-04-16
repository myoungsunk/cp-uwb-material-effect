from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


MATERIALS = ["concrete", "glass", "wood"]
VALID_MAX = {"concrete": 55.0, "glass": 60.0, "wood": 45.0}
TARGET_FREQ_GHZ = 6.5
EXECUTION_DATE = "2026-04-16"
DB_FLOOR = 1e-12


def build_argparser() -> argparse.ArgumentParser:
    bundle_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description=(
            "Fit low-dimensional material-effect models on top of the shared eps_eff CP correction "
            "and compare them against the locked Stage 4 baseline."
        )
    )
    parser.add_argument(
        "--stage4f-full",
        type=Path,
        default=bundle_root / "results" / "stage4f_raw_primary_full.csv",
    )
    parser.add_argument(
        "--eps-freq",
        type=Path,
        default=bundle_root / "results" / "debug" / "verify_cp_eps_material_drift" / "eff_mechanism_audit_freq_resolved.csv",
    )
    parser.add_argument(
        "--eps-ideal-center",
        type=Path,
        default=bundle_root / "results" / "debug" / "verify_cp_eps_material_drift" / "eps_obs_ideal_center_6p5ghz.csv",
    )
    parser.add_argument(
        "--a1-angle-summary",
        type=Path,
        default=bundle_root / "results" / "debug" / "verify_cp_eff_material_specific_eps.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=bundle_root / "results" / "debug",
    )
    return parser


def valid_main_range(material: str, theta_deg: float) -> bool:
    return 20.0 <= float(theta_deg) <= VALID_MAX[str(material)]


def safe_db20_ratio(numerator: float, denominator: float) -> float:
    return float(20.0 * np.log10(max(float(numerator), DB_FLOOR) / max(float(denominator), DB_FLOOR)))


def complex_cols(df: pd.DataFrame, real_col: str, imag_col: str) -> np.ndarray:
    return df[real_col].to_numpy(dtype=float) + 1j * df[imag_col].to_numpy(dtype=float)


def fit_scale_model(ideal_center: pd.DataFrame) -> dict[str, dict[str, complex]]:
    params: dict[str, dict[str, complex]] = {}
    for material, sub in ideal_center.groupby("material"):
        x = sub["_eps_shared"].to_numpy(dtype=complex)
        y = sub["_eps_target"].to_numpy(dtype=complex)
        denom = np.vdot(x, x)
        a = complex(np.vdot(x, y) / denom) if abs(denom) > 0.0 else 0.0j
        params[material] = {"a": a, "b": 0.0j}
    return params


def fit_offset_model(ideal_center: pd.DataFrame) -> dict[str, dict[str, complex]]:
    params: dict[str, dict[str, complex]] = {}
    for material, sub in ideal_center.groupby("material"):
        b = complex((sub["_eps_target"] - sub["_eps_shared"]).mean())
        params[material] = {"a": 1.0 + 0.0j, "b": b}
    return params


def fit_affine_model(ideal_center: pd.DataFrame) -> dict[str, dict[str, complex]]:
    params: dict[str, dict[str, complex]] = {}
    for material, sub in ideal_center.groupby("material"):
        x = sub["_eps_shared"].to_numpy(dtype=complex)
        y = sub["_eps_target"].to_numpy(dtype=complex)
        A = np.column_stack([x, np.ones(len(x), dtype=complex)])
        coef = np.linalg.lstsq(A, y, rcond=None)[0]
        params[material] = {"a": complex(coef[0]), "b": complex(coef[1])}
    return params


def apply_model(freq_df: pd.DataFrame, params: dict[str, dict[str, complex]]) -> pd.DataFrame:
    out = freq_df.copy()
    out["_eps_fit"] = out.apply(
        lambda row: params[str(row["material"])]["a"] * row["_eps_shared"] + params[str(row["material"])]["b"],
        axis=1,
    )
    out["_gamma_eff_fit"] = out["_gamma_raw"] - out["_eps_fit"] * out["_gamma_x"]
    out["gamma_eff_fit_mag"] = np.abs(out["_gamma_eff_fit"])
    out["eps_fit_real"] = np.real(out["_eps_fit"])
    out["eps_fit_imag"] = np.imag(out["_eps_fit"])
    out["eps_fit_mag"] = np.abs(out["_eps_fit"])
    out["eps_fit_phase_deg"] = np.rad2deg(np.angle(out["_eps_fit"]))
    return out


def build_angle_summary(stage4f: pd.DataFrame, freq_df: pd.DataFrame, model_name: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, locked_row in stage4f.iterrows():
        material = str(locked_row["material"])
        theta_deg = float(locked_row["theta_deg"])
        sub = freq_df[(freq_df["material"] == material) & np.isclose(freq_df["theta_deg"], theta_deg, atol=1e-9)].copy()
        if sub.empty:
            continue

        band_mag = float(sub["gamma_eff_fit_mag"].mean())
        point_idx = int(np.argmin(np.abs(sub["freq_ghz"].to_numpy(dtype=float) - TARGET_FREQ_GHZ)))
        point_mag = float(sub.iloc[point_idx]["gamma_eff_fit_mag"])

        G_band = safe_db20_ratio(float(locked_row["B_mag"]), band_mag)
        G_6p5 = safe_db20_ratio(float(locked_row["B_mag"]), point_mag)
        delta_band = float(locked_row["G_ideal_db"]) - G_band
        delta_6p5 = float(locked_row["G_ideal_db"]) - G_6p5
        rows.append(
            {
                "model_name": model_name,
                "material": material,
                "theta_deg": theta_deg,
                "B_mag": float(locked_row["B_mag"]),
                "G_ideal_db": float(locked_row["G_ideal_db"]),
                "gamma_eff_fit_band_mag": band_mag,
                "G_eff_fit_band_db": G_band,
                "Delta_ideal_minus_eff_fit_band_db": delta_band,
                "band_violation_flag": bool(delta_band < 0.0),
                "gamma_eff_fit_6p5_mag": point_mag,
                "G_eff_fit_6p5_db": G_6p5,
                "Delta_ideal_minus_eff_fit_6p5_db": delta_6p5,
                "point_violation_flag": bool(delta_6p5 < 0.0),
            }
        )
    return pd.DataFrame(rows).sort_values(["material", "theta_deg"]).reset_index(drop=True)


def build_summary_rows(
    *,
    model_name: str,
    angle_df: pd.DataFrame,
    params: dict[str, dict[str, complex]] | None,
    ideal_center: pd.DataFrame,
) -> list[dict[str, object]]:
    if params is None:
        center_rmse_abs = np.nan
        center_mean_abs_diff = np.nan
    else:
        diffs: list[complex] = []
        for _, row in ideal_center.iterrows():
            param = params[str(row["material"])]
            eps_fit = param["a"] * row["_eps_shared"] + param["b"]
            diffs.append(eps_fit - row["_eps_target"])
        diff_arr = np.asarray(diffs, dtype=complex)
        center_rmse_abs = float(np.sqrt(np.mean(np.abs(diff_arr) ** 2)))
        center_mean_abs_diff = float(np.mean(np.abs(diff_arr)))

    return [
        {
            "model_name": model_name,
            "scope": "band",
            "n_rows": int(len(angle_df)),
            "violation_rows": int(angle_df["band_violation_flag"].sum()),
            "pass_lt_5_rows": bool(int(angle_df["band_violation_flag"].sum()) < 5),
            "center_fit_rmse_abs": center_rmse_abs,
            "center_fit_mean_abs_diff": center_mean_abs_diff,
        },
        {
            "model_name": model_name,
            "scope": "6p5",
            "n_rows": int(len(angle_df)),
            "violation_rows": int(angle_df["point_violation_flag"].sum()),
            "pass_lt_5_rows": bool(int(angle_df["point_violation_flag"].sum()) < 5),
            "center_fit_rmse_abs": center_rmse_abs,
            "center_fit_mean_abs_diff": center_mean_abs_diff,
        },
    ]


def write_markdown(
    *,
    summary_df: pd.DataFrame,
    coeff_df: pd.DataFrame,
    detail_path: Path,
    summary_path: Path,
    coeff_path: Path,
    md_path: Path,
    repo_root: Path,
) -> None:
    def pick(model_name: str, scope: str) -> pd.Series:
        return summary_df[(summary_df["model_name"] == model_name) & (summary_df["scope"] == scope)].iloc[0]

    band_shared = pick("shared_current", "band")
    band_scale = pick("material_scale_centerfit", "band")
    band_offset = pick("material_offset_centerfit", "band")
    band_affine = pick("material_affine_centerfit", "band")
    band_a1 = pick("a1_ideal_center_const_reference", "band")
    point_scale = pick("material_scale_centerfit", "6p5")

    lines = [
        "# Fit CP Eps Material Effect",
        "",
        f"Execution date: `{EXECUTION_DATE}`",
        "",
        "## Scope",
        "",
        "- Fit simple material-effect models on top of the shared `eps_eff` CP correction.",
        "- Fit target is the existing `eps_obs_ideal` center-frequency replay at `6.5 GHz`.",
        "- Evaluation uses the locked Stage 4 ideal-anchor gain baseline on the current main-range `23` rows.",
        "- The A1 ideal-center replay is included as a high-flexibility reference row, not as a low-dimensional fit.",
        "",
        "## Model Family",
        "",
        "- `shared_current`: no material effect, current shared model",
        "- `material_scale_centerfit`: `eps_fit = a_m * eps_shared`",
        "- `material_offset_centerfit`: `eps_fit = eps_shared + b_m`",
        "- `material_affine_centerfit`: `eps_fit = a_m * eps_shared + b_m`",
        "- `a1_ideal_center_const_reference`: per-(material, theta) ideal-center replay from A1",
        "",
        "## Main Result",
        "",
        f"- Shared current baseline: `{int(band_shared['violation_rows'])}/23` band violations",
        f"- Best low-dimensional material-effect fit in this sweep: `material_scale_centerfit`, `{int(band_scale['violation_rows'])}/23` band violations",
        f"- The same scale model gives `{int(point_scale['violation_rows'])}/23` violations at `6.5 GHz`",
        f"- Offset model: `{int(band_offset['violation_rows'])}/23` band violations",
        f"- Affine model: `{int(band_affine['violation_rows'])}/23` band violations",
        f"- A1 high-flexibility reference remains better: `{int(band_a1['violation_rows'])}/23` band violations",
        "",
        "## Interpretation",
        "",
        "- A material effect does help. Even a single complex scale per material reduces the band violation count substantially relative to the shared baseline.",
        "- But a material-only low-dimensional model is not enough to fully match the A1 replay quality.",
        "- In the current data, `material_scale_centerfit` is the best simple model among the tested families.",
        "- This suggests that the CP eff failure is not just a single shared coefficient problem; there is real material dependence, but one complex degree of freedom per material still leaves residual angle-dependent mismatch.",
        "",
        "## Best Material-Scale Coefficients",
        "",
    ]

    best_coeff = coeff_df[coeff_df["model_name"] == "material_scale_centerfit"].copy()
    for _, row in best_coeff.iterrows():
        lines.append(
            f"- {row['material']}: "
            f"`a = {row['a_real']:.6f} + {row['a_imag']:.6f}j`, "
            f"`|a| = {row['a_mag']:.6f}`, "
            f"`phase = {row['a_phase_deg']:.2f} deg`"
        )

    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Angle detail CSV: `{detail_path.relative_to(repo_root)}`",
            f"- Summary CSV: `{summary_path.relative_to(repo_root)}`",
            f"- Coefficients CSV: `{coeff_path.relative_to(repo_root)}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_argparser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    stage4f = pd.read_csv(args.stage4f_full)
    stage4f = stage4f[stage4f["material"].isin(MATERIALS)].copy()
    stage4f = stage4f[stage4f.apply(lambda row: valid_main_range(str(row["material"]), float(row["theta_deg"])), axis=1)].copy()
    stage4f = stage4f.sort_values(["material", "theta_deg"]).reset_index(drop=True)

    freq_df = pd.read_csv(args.eps_freq)
    freq_df = freq_df[freq_df["material"].isin(MATERIALS)].copy()
    freq_df = freq_df[freq_df.apply(lambda row: valid_main_range(str(row["material"]), float(row["theta_deg"])), axis=1)].copy()
    freq_df["_eps_shared"] = complex_cols(freq_df, "eps_eff_current_real", "eps_eff_current_imag")
    freq_df["_gamma_raw"] = complex_cols(freq_df, "gamma_hat_c_cp_raw_real", "gamma_hat_c_cp_raw_imag")
    freq_df["_gamma_x"] = complex_cols(freq_df, "gamma_hat_x_cp_sys_real", "gamma_hat_x_cp_sys_imag")

    ideal_center = pd.read_csv(args.eps_ideal_center)
    ideal_center = ideal_center[ideal_center["material"].isin(MATERIALS)].copy()
    ideal_center = ideal_center[ideal_center.apply(lambda row: valid_main_range(str(row["material"]), float(row["theta_deg"])), axis=1)].copy()
    ideal_center["_eps_shared"] = complex_cols(ideal_center, "eps_eff_current_real", "eps_eff_current_imag")
    ideal_center["_eps_target"] = complex_cols(ideal_center, "eps_obs_ideal_real", "eps_obs_ideal_imag")

    a1_angle = pd.read_csv(args.a1_angle_summary)
    a1_angle = a1_angle[a1_angle["material"].isin(MATERIALS)].copy()

    model_param_map = {
        "material_scale_centerfit": fit_scale_model(ideal_center),
        "material_offset_centerfit": fit_offset_model(ideal_center),
        "material_affine_centerfit": fit_affine_model(ideal_center),
    }

    detail_frames: list[pd.DataFrame] = []
    summary_rows: list[dict[str, object]] = []
    coeff_rows: list[dict[str, object]] = []

    shared_params = {material: {"a": 1.0 + 0.0j, "b": 0.0 + 0.0j} for material in MATERIALS}
    shared_freq = apply_model(freq_df, shared_params)
    shared_angle = build_angle_summary(stage4f, shared_freq, "shared_current")
    detail_frames.append(shared_angle)
    summary_rows.extend(
        build_summary_rows(
            model_name="shared_current",
            angle_df=shared_angle,
            params=shared_params,
            ideal_center=ideal_center,
        )
    )
    for material, param in shared_params.items():
        coeff_rows.append(
            {
                "model_name": "shared_current",
                "material": material,
                "a_real": float(np.real(param["a"])),
                "a_imag": float(np.imag(param["a"])),
                "a_mag": float(np.abs(param["a"])),
                "a_phase_deg": float(np.rad2deg(np.angle(param["a"]))),
                "b_real": float(np.real(param["b"])),
                "b_imag": float(np.imag(param["b"])),
                "b_mag": float(np.abs(param["b"])),
                "b_phase_deg": float(np.rad2deg(np.angle(param["b"]))),
            }
        )

    for model_name, params in model_param_map.items():
        fitted_freq = apply_model(freq_df, params)
        angle_df = build_angle_summary(stage4f, fitted_freq, model_name)
        detail_frames.append(angle_df)
        summary_rows.extend(
            build_summary_rows(
                model_name=model_name,
                angle_df=angle_df,
                params=params,
                ideal_center=ideal_center,
            )
        )
        for material, param in params.items():
            coeff_rows.append(
                {
                    "model_name": model_name,
                    "material": material,
                    "a_real": float(np.real(param["a"])),
                    "a_imag": float(np.imag(param["a"])),
                    "a_mag": float(np.abs(param["a"])),
                    "a_phase_deg": float(np.rad2deg(np.angle(param["a"]))),
                    "b_real": float(np.real(param["b"])),
                    "b_imag": float(np.imag(param["b"])),
                    "b_mag": float(np.abs(param["b"])),
                    "b_phase_deg": float(np.rad2deg(np.angle(param["b"]))),
                }
            )

    a1_reference = a1_angle[
        [
            "material",
            "theta_deg",
            "gamma_c_eff_ideal_center_band_mag",
            "G_cp_eff_ideal_center_band_db",
            "Delta_ideal_minus_eff_ideal_center_band_db",
            "ideal_center_band_violation_flag",
            "gamma_c_eff_ideal_center_6p5_mag",
            "G_cp_eff_ideal_center_6p5_db",
            "Delta_ideal_minus_eff_ideal_center_6p5_db",
            "ideal_center_6p5_violation_flag",
        ]
    ].copy()
    a1_reference = a1_reference.rename(
        columns={
            "gamma_c_eff_ideal_center_band_mag": "gamma_eff_fit_band_mag",
            "G_cp_eff_ideal_center_band_db": "G_eff_fit_band_db",
            "Delta_ideal_minus_eff_ideal_center_band_db": "Delta_ideal_minus_eff_fit_band_db",
            "ideal_center_band_violation_flag": "band_violation_flag",
            "gamma_c_eff_ideal_center_6p5_mag": "gamma_eff_fit_6p5_mag",
            "G_cp_eff_ideal_center_6p5_db": "G_eff_fit_6p5_db",
            "Delta_ideal_minus_eff_ideal_center_6p5_db": "Delta_ideal_minus_eff_fit_6p5_db",
            "ideal_center_6p5_violation_flag": "point_violation_flag",
        }
    )
    a1_reference["model_name"] = "a1_ideal_center_const_reference"
    detail_frames.append(a1_reference.sort_values(["material", "theta_deg"]).reset_index(drop=True))
    summary_rows.extend(
        build_summary_rows(
            model_name="a1_ideal_center_const_reference",
            angle_df=a1_reference,
            params=None,
            ideal_center=ideal_center,
        )
    )

    detail_df = pd.concat(detail_frames, ignore_index=True)
    summary_df = pd.DataFrame(summary_rows).sort_values(["model_name", "scope"]).reset_index(drop=True)
    coeff_df = pd.DataFrame(coeff_rows).sort_values(["model_name", "material"]).reset_index(drop=True)

    detail_path = output_dir / "fit_cp_eps_material_effect_detail.csv"
    summary_path = output_dir / "fit_cp_eps_material_effect_summary.csv"
    coeff_path = output_dir / "fit_cp_eps_material_effect_coefficients.csv"
    md_path = output_dir / "FIT_CP_EPS_MATERIAL_EFFECT.md"

    detail_df.to_csv(detail_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    coeff_df.to_csv(coeff_path, index=False)
    write_markdown(
        summary_df=summary_df,
        coeff_df=coeff_df,
        detail_path=detail_path,
        summary_path=summary_path,
        coeff_path=coeff_path,
        md_path=md_path,
        repo_root=repo_root,
    )

    print(f"Wrote {detail_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {coeff_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
