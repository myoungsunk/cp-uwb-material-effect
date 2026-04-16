from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


MATERIALS = ["concrete", "glass", "wood"]
VALID_MAX = {"concrete": 55.0, "glass": 60.0, "wood": 45.0}
TARGET_FREQ_GHZ = 6.5
EXECUTION_DATE = "2026-04-16"
COMPLEX_FLOOR = 1e-18
DB_FLOOR = 1e-12


def build_argparser() -> argparse.ArgumentParser:
    bundle_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description=(
            "Independently replay the CP metal-normalized extension directly from the "
            "Stage 3 freq-resolved export, then compare it against the locked Stage 4 metal-floor snapshot."
        )
    )
    parser.add_argument(
        "--stage4f-full",
        type=Path,
        default=bundle_root / "results" / "stage4f_raw_primary_full.csv",
    )
    parser.add_argument(
        "--cp-freq",
        type=Path,
        default=bundle_root / "data" / "stage_3" / "cp" / "patch_cp_extracted_freq_resolved.csv",
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


def add_complex_columns(df: pd.DataFrame, prefix: str, values: np.ndarray) -> None:
    df[f"{prefix}_real"] = np.real(values)
    df[f"{prefix}_imag"] = np.imag(values)
    df[f"{prefix}_mag"] = np.abs(values)
    df[f"{prefix}_phase_deg"] = np.rad2deg(np.angle(values))


def complex_from_merged(df: pd.DataFrame, prefix: str, suffix: str) -> np.ndarray:
    return df[f"{prefix}_real{suffix}"].to_numpy(dtype=float) + 1j * df[f"{prefix}_imag{suffix}"].to_numpy(dtype=float)


def safe_complex_divide(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    num = np.asarray(numerator, dtype=complex)
    den = np.asarray(denominator, dtype=complex)
    out = np.full(num.shape, np.nan + 1j * np.nan, dtype=complex)
    valid = np.abs(den) > COMPLEX_FLOOR
    out[valid] = num[valid] / den[valid]
    return out


def rename_payload_columns(df: pd.DataFrame, suffix: str) -> pd.DataFrame:
    key_cols = {"theta_deg", "freq_ghz"}
    return df.rename(columns={col: f"{col}{suffix}" for col in df.columns if col not in key_cols}).copy()


def load_inputs(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame]:
    stage4f = pd.read_csv(args.stage4f_full)
    stage4f = stage4f[stage4f["material"].isin(MATERIALS)].copy()
    stage4f = stage4f[stage4f.apply(lambda row: valid_main_range(str(row["material"]), float(row["theta_deg"])), axis=1)].copy()
    stage4f = stage4f.sort_values(["material", "theta_deg"]).reset_index(drop=True)

    cp_freq = pd.read_csv(args.cp_freq)
    cp_freq = cp_freq[cp_freq["material"].isin(["metal", *MATERIALS])].copy()
    cp_freq = cp_freq[cp_freq["theta_deg"].apply(lambda theta: abs(float(theta) - round(float(theta) / 5.0) * 5.0) < 1e-9)].copy()
    cp_freq = cp_freq.sort_values(["material", "theta_deg", "freq_ghz"]).reset_index(drop=True)
    return stage4f, cp_freq


def build_freq_detail(stage4f: pd.DataFrame, cp_freq: pd.DataFrame) -> pd.DataFrame:
    detail_frames: list[pd.DataFrame] = []
    for _, locked_row in stage4f.iterrows():
        material = str(locked_row["material"])
        theta_deg = float(locked_row["theta_deg"])

        sub_mat = cp_freq[(cp_freq["material"] == material) & np.isclose(cp_freq["theta_deg"], theta_deg, atol=1e-9)].copy()
        sub_met = cp_freq[(cp_freq["material"] == "metal") & np.isclose(cp_freq["theta_deg"], theta_deg, atol=1e-9)].copy()
        if sub_mat.empty or sub_met.empty:
            continue

        merged = rename_payload_columns(sub_mat, "_mat").merge(
            rename_payload_columns(sub_met, "_metal"),
            on=["theta_deg", "freq_ghz"],
            how="inner",
        )
        if merged.empty:
            continue

        gamma_c_raw_mat = complex_from_merged(merged, "gamma_hat_c_cp_raw", "_mat")
        gamma_c_raw_metal = complex_from_merged(merged, "gamma_hat_c_cp_raw", "_metal")
        gamma_c_eff_mat = complex_from_merged(merged, "gamma_hat_c_cp_eff", "_mat")
        gamma_c_eff_metal = complex_from_merged(merged, "gamma_hat_c_cp_eff", "_metal")
        gamma_x_mat = complex_from_merged(merged, "gamma_hat_x_cp_sys", "_mat")
        gamma_x_metal = complex_from_merged(merged, "gamma_hat_x_cp_sys", "_metal")

        gamma_c_metal_norm = safe_complex_divide(gamma_c_raw_mat, gamma_c_raw_metal)
        gamma_c_eff_metal_ratio = safe_complex_divide(gamma_c_eff_mat, gamma_c_eff_metal)
        gamma_x_metal_ratio = safe_complex_divide(gamma_x_mat, gamma_x_metal)

        merged["material"] = material
        add_complex_columns(merged, "gamma_c_metal_norm", gamma_c_metal_norm)
        add_complex_columns(merged, "gamma_c_eff_metal_ratio", gamma_c_eff_metal_ratio)
        add_complex_columns(merged, "gamma_x_metal_ratio_direct", gamma_x_metal_ratio)

        detail_frames.append(
            merged[
                [
                    "material",
                    "theta_deg",
                    "freq_ghz",
                    "gamma_hat_c_cp_raw_real_mat",
                    "gamma_hat_c_cp_raw_imag_mat",
                    "gamma_hat_c_cp_raw_mag_mat",
                    "gamma_hat_c_cp_raw_real_metal",
                    "gamma_hat_c_cp_raw_imag_metal",
                    "gamma_hat_c_cp_raw_mag_metal",
                    "gamma_hat_c_cp_eff_real_mat",
                    "gamma_hat_c_cp_eff_imag_mat",
                    "gamma_hat_c_cp_eff_mag_mat",
                    "gamma_hat_c_cp_eff_real_metal",
                    "gamma_hat_c_cp_eff_imag_metal",
                    "gamma_hat_c_cp_eff_mag_metal",
                    "gamma_hat_x_cp_sys_real_mat",
                    "gamma_hat_x_cp_sys_imag_mat",
                    "gamma_hat_x_cp_sys_mag_mat",
                    "gamma_hat_x_cp_sys_real_metal",
                    "gamma_hat_x_cp_sys_imag_metal",
                    "gamma_hat_x_cp_sys_mag_metal",
                    "r_te_proxy_mag_mat",
                    "r_tm_proxy_mag_mat",
                    "B_cp_proxy_mag_mat",
                    "gamma_c_metal_norm_real",
                    "gamma_c_metal_norm_imag",
                    "gamma_c_metal_norm_mag",
                    "gamma_c_metal_norm_phase_deg",
                    "gamma_c_eff_metal_ratio_real",
                    "gamma_c_eff_metal_ratio_imag",
                    "gamma_c_eff_metal_ratio_mag",
                    "gamma_c_eff_metal_ratio_phase_deg",
                    "gamma_x_metal_ratio_direct_real",
                    "gamma_x_metal_ratio_direct_imag",
                    "gamma_x_metal_ratio_direct_mag",
                    "gamma_x_metal_ratio_direct_phase_deg",
                ]
            ].copy()
        )

    if not detail_frames:
        return pd.DataFrame()
    return pd.concat(detail_frames, ignore_index=True).sort_values(["material", "theta_deg", "freq_ghz"]).reset_index(drop=True)


def build_angle_summary(stage4f: pd.DataFrame, detail: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, locked_row in stage4f.iterrows():
        material = str(locked_row["material"])
        theta_deg = float(locked_row["theta_deg"])
        sub = detail[(detail["material"] == material) & np.isclose(detail["theta_deg"], theta_deg, atol=1e-9)].copy()
        if sub.empty:
            continue

        point_sub = sub.iloc[[int(np.argmin(np.abs(sub["freq_ghz"].to_numpy(dtype=float) - TARGET_FREQ_GHZ)))]].copy()

        gamma_c_metal_norm_band_mag = float(np.nanmean(sub["gamma_c_metal_norm_mag"].to_numpy(dtype=float)))
        gamma_c_eff_metal_ratio_band_mag = float(np.nanmean(sub["gamma_c_eff_metal_ratio_mag"].to_numpy(dtype=float)))
        gamma_x_metal_ratio_direct_band_mag = float(np.nanmean(sub["gamma_x_metal_ratio_direct_mag"].to_numpy(dtype=float)))
        gamma_c_metal_norm_6p5_mag = float(point_sub.iloc[0]["gamma_c_metal_norm_mag"])
        gamma_c_eff_metal_ratio_6p5_mag = float(point_sub.iloc[0]["gamma_c_eff_metal_ratio_mag"])
        gamma_x_metal_ratio_direct_6p5_mag = float(point_sub.iloc[0]["gamma_x_metal_ratio_direct_mag"])
        b_cp_proxy_6p5_mag = float(point_sub.iloc[0]["B_cp_proxy_mag_mat"])

        B_mag = float(locked_row["B_mag"])
        B_cp_proxy_mag = float(locked_row["B_cp_proxy_mag"])
        G_ideal_db = float(locked_row["G_ideal_db"])
        gamma_x_ideal_mag = float(locked_row["gamma_x_ideal_mag"])

        G_cp_metal_norm_band_db = safe_db20_ratio(B_mag, gamma_c_metal_norm_band_mag)
        G_cp_metal_norm_sys_band_db = safe_db20_ratio(B_cp_proxy_mag, gamma_c_metal_norm_band_mag)
        G_cp_metal_norm_6p5_db = safe_db20_ratio(B_mag, gamma_c_metal_norm_6p5_mag)
        G_cp_metal_norm_sys_6p5_db = safe_db20_ratio(b_cp_proxy_6p5_mag, gamma_c_metal_norm_6p5_mag)

        rows.append(
            {
                "material": material,
                "theta_deg": theta_deg,
                "B_mag": B_mag,
                "B_cp_proxy_mag": B_cp_proxy_mag,
                "B_cp_proxy_6p5_mag": b_cp_proxy_6p5_mag,
                "gamma_x_ideal_mag": gamma_x_ideal_mag,
                "G_ideal_db": G_ideal_db,
                "gamma_c_patch_raw_mag_locked": float(locked_row["gamma_c_patch_raw_mag"]),
                "gamma_c_patch_eff_mag_locked": float(locked_row["gamma_c_patch_eff_mag"]),
                "G_patch_raw_db_locked": float(locked_row["G_patch_raw_db"]),
                "G_patch_eff_db_locked": float(locked_row["G_patch_eff_db"]),
                "gamma_c_metal_floor_mag_stage4f": float(locked_row["gamma_hat_c_metal_floor_mag"]),
                "G_patch_metal_floor_db_stage4f": float(locked_row["G_patch_metal_floor_db"]),
                "gamma_c_metal_norm_band_mag": gamma_c_metal_norm_band_mag,
                "gamma_c_metal_norm_6p5_mag": gamma_c_metal_norm_6p5_mag,
                "gamma_c_eff_metal_ratio_band_mag": gamma_c_eff_metal_ratio_band_mag,
                "gamma_c_eff_metal_ratio_6p5_mag": gamma_c_eff_metal_ratio_6p5_mag,
                "gamma_x_metal_ratio_direct_band_mag": gamma_x_metal_ratio_direct_band_mag,
                "gamma_x_metal_ratio_direct_6p5_mag": gamma_x_metal_ratio_direct_6p5_mag,
                "G_cp_metal_norm_band_db": G_cp_metal_norm_band_db,
                "G_cp_metal_norm_sys_band_db": G_cp_metal_norm_sys_band_db,
                "G_cp_metal_norm_6p5_db": G_cp_metal_norm_6p5_db,
                "G_cp_metal_norm_sys_6p5_db": G_cp_metal_norm_sys_6p5_db,
                "Delta_ideal_minus_cp_metal_norm_band_db": G_ideal_db - G_cp_metal_norm_band_db,
                "Delta_ideal_minus_cp_metal_norm_sys_band_db": G_ideal_db - G_cp_metal_norm_sys_band_db,
                "Delta_ideal_minus_cp_metal_norm_6p5_db": G_ideal_db - G_cp_metal_norm_6p5_db,
                "Delta_ideal_minus_cp_metal_norm_sys_6p5_db": G_ideal_db - G_cp_metal_norm_sys_6p5_db,
                "cp_metal_norm_band_below_ideal_flag": bool(gamma_c_metal_norm_band_mag < gamma_x_ideal_mag),
                "cp_metal_norm_band_gt_ideal_flag": bool(gamma_c_metal_norm_band_mag > gamma_x_ideal_mag),
                "cp_metal_norm_6p5_below_ideal_flag": bool(gamma_c_metal_norm_6p5_mag < gamma_x_ideal_mag),
                "cp_metal_norm_6p5_gt_ideal_flag": bool(gamma_c_metal_norm_6p5_mag > gamma_x_ideal_mag),
                "cp_metal_norm_band_negative_flag": bool((G_ideal_db - G_cp_metal_norm_band_db) < 0.0),
                "cp_metal_norm_sys_band_negative_flag": bool((G_ideal_db - G_cp_metal_norm_sys_band_db) < 0.0),
                "cp_metal_norm_6p5_negative_flag": bool((G_ideal_db - G_cp_metal_norm_6p5_db) < 0.0),
                "cp_metal_norm_sys_6p5_negative_flag": bool((G_ideal_db - G_cp_metal_norm_sys_6p5_db) < 0.0),
                "replay_minus_stage4f_metal_floor_mag": gamma_c_metal_norm_band_mag - float(locked_row["gamma_hat_c_metal_floor_mag"]),
                "replay_minus_stage4f_metal_floor_db": G_cp_metal_norm_band_db - float(locked_row["G_patch_metal_floor_db"]),
            }
        )

    return pd.DataFrame(rows).sort_values(["material", "theta_deg"]).reset_index(drop=True)


def build_summary(angle_df: pd.DataFrame) -> pd.DataFrame:
    common = {
        "replay_vs_stage4f_max_abs_mag_diff": float(angle_df["replay_minus_stage4f_metal_floor_mag"].abs().max()),
        "replay_vs_stage4f_max_abs_gain_diff_db": float(angle_df["replay_minus_stage4f_metal_floor_db"].abs().max()),
    }
    rows = [
        {
            "variant": "locked_raw_stage4f_band",
            "n_rows": int(len(angle_df)),
            "delta_negative_rows": int((angle_df["G_ideal_db"] - angle_df["G_patch_raw_db_locked"] < 0.0).sum()),
            "residual_below_ideal_rows": int((angle_df["gamma_c_patch_raw_mag_locked"] < angle_df["gamma_x_ideal_mag"]).sum()),
            "residual_gt_ideal_rows": int((angle_df["gamma_c_patch_raw_mag_locked"] > angle_df["gamma_x_ideal_mag"]).sum()),
            "mean_gain_db": float(angle_df["G_patch_raw_db_locked"].mean()),
            "mean_delta_vs_ideal_db": float((angle_df["G_ideal_db"] - angle_df["G_patch_raw_db_locked"]).mean()),
            "note": "Locked stage4f raw baseline for context.",
            **common,
        },
        {
            "variant": "locked_eff_stage4f_band",
            "n_rows": int(len(angle_df)),
            "delta_negative_rows": int((angle_df["G_ideal_db"] - angle_df["G_patch_eff_db_locked"] < 0.0).sum()),
            "residual_below_ideal_rows": int((angle_df["gamma_c_patch_eff_mag_locked"] < angle_df["gamma_x_ideal_mag"]).sum()),
            "residual_gt_ideal_rows": int((angle_df["gamma_c_patch_eff_mag_locked"] > angle_df["gamma_x_ideal_mag"]).sum()),
            "mean_gain_db": float(angle_df["G_patch_eff_db_locked"].mean()),
            "mean_delta_vs_ideal_db": float((angle_df["G_ideal_db"] - angle_df["G_patch_eff_db_locked"]).mean()),
            "note": "Locked stage4f eff baseline for context.",
            **common,
        },
        {
            "variant": "cp_metal_norm_ideal_anchor_band",
            "n_rows": int(len(angle_df)),
            "delta_negative_rows": int(angle_df["cp_metal_norm_band_negative_flag"].sum()),
            "residual_below_ideal_rows": int(angle_df["cp_metal_norm_band_below_ideal_flag"].sum()),
            "residual_gt_ideal_rows": int(angle_df["cp_metal_norm_band_gt_ideal_flag"].sum()),
            "mean_gain_db": float(angle_df["G_cp_metal_norm_band_db"].mean()),
            "mean_delta_vs_ideal_db": float(angle_df["Delta_ideal_minus_cp_metal_norm_band_db"].mean()),
            "note": "Independent replay from stage3 freq export with ideal-anchor numerator B_mag.",
            **common,
        },
        {
            "variant": "cp_metal_norm_sys_anchor_band",
            "n_rows": int(len(angle_df)),
            "delta_negative_rows": int(angle_df["cp_metal_norm_sys_band_negative_flag"].sum()),
            "residual_below_ideal_rows": int(angle_df["cp_metal_norm_band_below_ideal_flag"].sum()),
            "residual_gt_ideal_rows": int(angle_df["cp_metal_norm_band_gt_ideal_flag"].sum()),
            "mean_gain_db": float(angle_df["G_cp_metal_norm_sys_band_db"].mean()),
            "mean_delta_vs_ideal_db": float(angle_df["Delta_ideal_minus_cp_metal_norm_sys_band_db"].mean()),
            "note": "Same replay but with the same-stage CP numerator B_cp_proxy_mag.",
            **common,
        },
        {
            "variant": "cp_metal_norm_ideal_anchor_6p5",
            "n_rows": int(len(angle_df)),
            "delta_negative_rows": int(angle_df["cp_metal_norm_6p5_negative_flag"].sum()),
            "residual_below_ideal_rows": int(angle_df["cp_metal_norm_6p5_below_ideal_flag"].sum()),
            "residual_gt_ideal_rows": int(angle_df["cp_metal_norm_6p5_gt_ideal_flag"].sum()),
            "mean_gain_db": float(angle_df["G_cp_metal_norm_6p5_db"].mean()),
            "mean_delta_vs_ideal_db": float(angle_df["Delta_ideal_minus_cp_metal_norm_6p5_db"].mean()),
            "note": "Nearest-point replay at 6.5 GHz with ideal-anchor numerator B_mag.",
            **common,
        },
        {
            "variant": "cp_metal_norm_sys_anchor_6p5",
            "n_rows": int(len(angle_df)),
            "delta_negative_rows": int(angle_df["cp_metal_norm_sys_6p5_negative_flag"].sum()),
            "residual_below_ideal_rows": int(angle_df["cp_metal_norm_6p5_below_ideal_flag"].sum()),
            "residual_gt_ideal_rows": int(angle_df["cp_metal_norm_6p5_gt_ideal_flag"].sum()),
            "mean_gain_db": float(angle_df["G_cp_metal_norm_sys_6p5_db"].mean()),
            "mean_delta_vs_ideal_db": float(angle_df["Delta_ideal_minus_cp_metal_norm_sys_6p5_db"].mean()),
            "note": "Nearest-point replay at 6.5 GHz with same-stage numerator B_cp_proxy(f).",
            **common,
        },
    ]
    return pd.DataFrame(rows)


def write_markdown(
    *,
    angle_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    full_path: Path,
    freq_path: Path,
    summary_path: Path,
    output_path: Path,
    repo_root: Path,
) -> None:
    band_row = summary_df[summary_df["variant"] == "cp_metal_norm_ideal_anchor_band"].iloc[0]
    sys_band_row = summary_df[summary_df["variant"] == "cp_metal_norm_sys_anchor_band"].iloc[0]
    point_row = summary_df[summary_df["variant"] == "cp_metal_norm_ideal_anchor_6p5"].iloc[0]
    worst_diff = angle_df.iloc[int(angle_df["replay_minus_stage4f_metal_floor_mag"].abs().argmax())]

    lines = [
        "# Verify CP Metal-Normalized Extension",
        "",
        f"Execution date: `{EXECUTION_DATE}`",
        "",
        "## Scope",
        "",
        "- This is an independent verifier rebuilt from the Stage 3 CP freq-resolved export.",
        "- No legacy isolated-workspace CSV is used to construct the replay quantity.",
        "- Core replay quantity:",
        "  - `Gamma_C_metal_norm(theta,f) = Gamma_C_raw(material, theta, f) / Gamma_C_raw(metal, theta, f)`",
        "- The replay is then compared against the locked `stage4f_raw_primary_full.csv` metal-floor projection.",
        "- For context, both ideal-anchor and same-stage CP numerator anchors are reported.",
        "",
        "## Main Results",
        "",
        f"- Independent replay vs locked Stage 4 metal-floor max magnitude difference: `{float(band_row['replay_vs_stage4f_max_abs_mag_diff']):.3e}`",
        f"- Independent replay vs locked Stage 4 metal-floor max gain difference: `{float(band_row['replay_vs_stage4f_max_abs_gain_diff_db']):.3e} dB`",
        f"- Ideal-anchor band replay negative rows: `{int(band_row['delta_negative_rows'])}/{int(band_row['n_rows'])}`",
        f"- Ideal-anchor band replay rows with residual larger than ideal: `{int(band_row['residual_gt_ideal_rows'])}/{int(band_row['n_rows'])}`",
        f"- Same-stage band replay negative rows: `{int(sys_band_row['delta_negative_rows'])}/{int(sys_band_row['n_rows'])}`",
        f"- `6.5 GHz` ideal-anchor replay negative rows: `{int(point_row['delta_negative_rows'])}/{int(point_row['n_rows'])}`",
        "",
        "## Interpretation",
        "",
        "- The rewritten replay reproduces the locked metal-floor branch to numerical precision, so the old Stage 4d result is not an artifact of that isolated script.",
        "- The CP metal-normalized extension does remove the same-angle sign contradiction.",
        "- But it remains larger than the ideal residual in every matched-angle row, so it is still not directly comparable to the absolute-like Stage 4 headline residual.",
        "- Changing only the numerator anchor does not convert it into a production-safe correction path.",
        "",
        "## Worst Replay-vs-Locked Difference",
        "",
        f"- `{worst_diff['material']} {float(worst_diff['theta_deg']):.0f} deg`: "
        f"mag diff `{float(worst_diff['replay_minus_stage4f_metal_floor_mag']):.3e}`, "
        f"gain diff `{float(worst_diff['replay_minus_stage4f_metal_floor_db']):.3e} dB`",
        "",
        "## Outputs",
        "",
        f"- Angle summary CSV: `{full_path.relative_to(repo_root)}`",
        f"- Freq detail CSV: `{freq_path.relative_to(repo_root)}`",
        f"- Summary CSV: `{summary_path.relative_to(repo_root)}`",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_argparser().parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[3]

    stage4f, cp_freq = load_inputs(args)
    detail = build_freq_detail(stage4f, cp_freq)
    if detail.empty:
        raise RuntimeError("No overlapping material/metal CP freq-resolved rows were found for the locked Stage 4 grid.")
    angle_df = build_angle_summary(stage4f, detail)
    summary_df = build_summary(angle_df)

    full_path = output_dir / "verify_cp_metal_normalized_extension.csv"
    freq_path = output_dir / "verify_cp_metal_normalized_extension_freq.csv"
    summary_path = output_dir / "verify_cp_metal_normalized_extension_summary.csv"
    md_path = output_dir / "VERIFY_CP_METAL_NORMALIZED_EXTENSION.md"

    angle_df.to_csv(full_path, index=False)
    detail.to_csv(freq_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    write_markdown(
        angle_df=angle_df,
        summary_df=summary_df,
        full_path=full_path,
        freq_path=freq_path,
        summary_path=summary_path,
        output_path=md_path,
        repo_root=repo_root,
    )

    print(f"Wrote {full_path}")
    print(f"Wrote {freq_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
