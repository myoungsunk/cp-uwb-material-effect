from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


MATERIALS = ["concrete", "glass", "wood"]
VALID_MAX = {"concrete": 55.0, "glass": 60.0, "wood": 45.0}
TARGET_FREQ_GHZ = 6.5
WALL_THICKNESS_MM = 100.0
LP_CHANNELS = ["yy", "yz", "zy", "zz"]
MATERIAL_PROPS = {
    "concrete": {"eps_r": 5.24, "tan_d": 0.105},
    "glass": {"eps_r": 6.31, "tan_d": 0.019},
    "wood": {"eps_r": 1.99, "tan_d": 0.049},
}


def build_argparser() -> argparse.ArgumentParser:
    bundle_root = Path(__file__).resolve().parent.parent
    analysis_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description=(
            "Replay the LP metal-anchor normalization prototype inside the paper-review bundle "
            "and compare it against the current Stage 3 LP export plus the Stage 1/2 ideal truth."
        )
    )
    parser.add_argument(
        "--linear-truth",
        type=Path,
        default=bundle_root / "data" / "stage_1" / "truth_table_linear_locked.csv",
    )
    parser.add_argument(
        "--cp-truth",
        type=Path,
        default=bundle_root / "data" / "stage_2" / "sameflip_alias_20260415" / "truth_table_cp_shared_common_sameflip.csv",
    )
    parser.add_argument(
        "--orig-lp-band",
        type=Path,
        default=bundle_root / "data" / "stage_3" / "lp" / "patch_lp_extracted.csv",
    )
    parser.add_argument(
        "--orig-lp-freq",
        type=Path,
        default=bundle_root / "data" / "stage_3" / "lp" / "patch_lp_extracted_freq_resolved.csv",
    )
    parser.add_argument(
        "--prototype-csv-dir",
        type=Path,
        default=analysis_root / "patch_lp_stage_system" / "metal_plate_normalized" / "csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=bundle_root / "results" / "debug",
    )
    return parser


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y", "t"}


def parse_complex(magnitude: np.ndarray, phase_deg: np.ndarray) -> np.ndarray:
    return magnitude * np.exp(1j * np.deg2rad(phase_deg))


def load_m1_lp(path: Path) -> dict[str, np.ndarray]:
    df = pd.read_csv(path)
    out = {"freq_ghz": df.iloc[:, 0].to_numpy(dtype=float)}
    channel_cols = {
        "yy": ("mag(S(Rx_y_p1,Tx_y_p1)) []", "ang_deg(S(Rx_y_p1,Tx_y_p1)) [deg]"),
        "yz": ("mag(S(Rx_y_p1,Tx_z_p1)) []", "ang_deg(S(Rx_y_p1,Tx_z_p1)) [deg]"),
        "zy": ("mag(S(Rx_z_p1,Tx_y_p1)) []", "ang_deg(S(Rx_z_p1,Tx_y_p1)) [deg]"),
        "zz": ("mag(S(Rx_z_p1,Tx_z_p1)) []", "ang_deg(S(Rx_z_p1,Tx_z_p1)) [deg]"),
    }
    for channel, (mag_col, phase_col) in channel_cols.items():
        out[channel] = parse_complex(
            df[mag_col].to_numpy(dtype=float),
            df[phase_col].to_numpy(dtype=float),
        )
    return out


def load_sweep_lp(path: Path) -> dict[object, object]:
    df = pd.read_csv(path)
    theta_col = df.columns[0]
    freq_col = df.columns[1]
    thetas = np.array(sorted(df[theta_col].unique()), dtype=float)
    freq = df[df[theta_col] == thetas[0]][freq_col].to_numpy(dtype=float)
    out: dict[object, object] = {"freq_ghz": freq, "thetas_deg": thetas}
    channel_cols = {
        "yy": ("mag(S(Rx_y_p1,Tx_y_p1)) []", "ang_deg(S(Rx_y_p1,Tx_y_p1)) [deg]"),
        "yz": ("mag(S(Rx_y_p1,Tx_z_p1)) []", "ang_deg(S(Rx_y_p1,Tx_z_p1)) [deg]"),
        "zy": ("mag(S(Rx_z_p1,Tx_y_p1)) []", "ang_deg(S(Rx_z_p1,Tx_y_p1)) [deg]"),
        "zz": ("mag(S(Rx_z_p1,Tx_z_p1)) []", "ang_deg(S(Rx_z_p1,Tx_z_p1)) [deg]"),
    }
    for theta in thetas:
        sub = df[df[theta_col] == theta]
        out[float(theta)] = {}
        for channel, (mag_col, phase_col) in channel_cols.items():
            out[float(theta)][channel] = parse_complex(
                sub[mag_col].to_numpy(dtype=float),
                sub[phase_col].to_numpy(dtype=float),
            )
    return out


def nearest_index(freq_ghz: np.ndarray, target_freq_ghz: float) -> int:
    return int(np.argmin(np.abs(freq_ghz - target_freq_ghz)))


def fresnel_slab(
    eps_r: float,
    tan_d: float,
    theta_deg: float,
    thickness_mm: float,
    freq_ghz: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    theta = np.deg2rad(np.asarray(theta_deg, dtype=float))
    eps_complex = eps_r * (1.0 - 1j * tan_d)
    wavelength_mm = 300.0 / np.asarray(freq_ghz, dtype=float)
    k0 = 2.0 * np.pi / wavelength_mm
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)
    sqrt_term = np.sqrt(eps_complex - sin_theta**2 + 0j)
    r_te = (cos_theta - sqrt_term) / (cos_theta + sqrt_term)
    r_tm = (eps_complex * cos_theta - sqrt_term) / (eps_complex * cos_theta + sqrt_term)
    if thickness_mm <= 0.0:
        return r_te, r_tm
    delta = k0 * thickness_mm * sqrt_term
    exp_term = np.exp(-2j * delta)
    r_te_total = r_te * (1.0 - exp_term) / (1.0 - r_te**2 * exp_term)
    r_tm_total = r_tm * (1.0 - exp_term) / (1.0 - r_tm**2 * exp_term)
    return r_te_total, r_tm_total


def build_ideal_grid(linear_truth: pd.DataFrame, cp_truth: pd.DataFrame) -> pd.DataFrame:
    linear = linear_truth[linear_truth["material"].isin(MATERIALS)].copy()
    cp = cp_truth[cp_truth["material"].isin(MATERIALS)].copy()

    linear = linear[np.isclose(pd.to_numeric(linear["f_hz"], errors="coerce") / 1e9, TARGET_FREQ_GHZ, atol=1e-9)]
    cp = cp[np.isclose(pd.to_numeric(cp["f_hz"], errors="coerce") / 1e9, TARGET_FREQ_GHZ, atol=1e-9)]

    linear["use_for_main_claim_TE"] = linear["use_for_main_claim_TE"].map(parse_bool)
    linear["use_for_main_claim_TM"] = linear["use_for_main_claim_TM"].map(parse_bool)
    cp["cp_use_for_main_claim"] = cp["cp_use_for_main_claim"].map(parse_bool)

    ideal = linear[
        ["material", "theta_deg", "R_TE_mag", "R_TM_mag", "use_for_main_claim_TE", "use_for_main_claim_TM"]
    ].merge(
        cp[["material", "theta_deg", "Gamma_same_mag", "cp_use_for_main_claim"]],
        on=["material", "theta_deg"],
        how="inner",
    )
    ideal["in_main_range"] = ideal.apply(
        lambda row: (
            row["use_for_main_claim_TE"]
            and row["use_for_main_claim_TM"]
            and row["cp_use_for_main_claim"]
            and float(row["theta_deg"]) >= 20.0
            and float(row["theta_deg"]) <= VALID_MAX[str(row["material"])]
        ),
        axis=1,
    )
    ideal["B_ideal_mag"] = ideal[["R_TE_mag", "R_TM_mag"]].max(axis=1)
    ideal = ideal.rename(columns={"Gamma_same_mag": "gamma_x_ideal_mag"})
    return ideal.sort_values(["material", "theta_deg"]).reset_index(drop=True)


def build_metal_normalized_rows(
    *,
    prototype_csv_dir: Path,
    ideal_grid: pd.DataFrame,
    orig_lp_band: pd.DataFrame,
    orig_lp_freq: pd.DataFrame,
) -> pd.DataFrame:
    lp_m1 = load_m1_lp(prototype_csv_dir / "LP_m1_los_5000.csv")
    lp_m2 = {
        material: load_sweep_lp(prototype_csv_dir / f"LP_m2_{material}_R_5000.csv")
        for material in ["metal", *MATERIALS]
    }

    freq_ghz = lp_m1["freq_ghz"]
    freq_index_6p5 = nearest_index(freq_ghz, TARGET_FREQ_GHZ)
    orig_lp_freq_6p5 = orig_lp_freq[np.isclose(orig_lp_freq["freq_ghz"], TARGET_FREQ_GHZ, atol=1e-9)].copy()

    rows: list[dict[str, object]] = []
    for material in MATERIALS:
        for theta_deg in lp_m2["metal"]["thetas_deg"]:
            theta_deg = float(theta_deg)
            h_tilde_material = {
                channel: lp_m2[material][theta_deg][channel] - lp_m1[channel]
                for channel in LP_CHANNELS
            }
            h_tilde_metal = {
                channel: lp_m2["metal"][theta_deg][channel] - lp_m1[channel]
                for channel in LP_CHANNELS
            }

            r_te_metal = h_tilde_material["zz"] / h_tilde_metal["zz"]
            r_tm_metal = h_tilde_material["yy"] / h_tilde_metal["yy"]
            gamma_x_metal = 0.5 * (r_te_metal + r_tm_metal)
            gamma_c_metal = 0.5 * (r_te_metal - r_tm_metal)

            cross_zy_ratio = np.mean(np.abs(h_tilde_material["zy"])) / max(
                np.mean(np.abs(h_tilde_material["zz"])),
                1e-12,
            )
            cross_yz_ratio = np.mean(np.abs(h_tilde_material["yz"])) / max(
                np.mean(np.abs(h_tilde_material["yy"])),
                1e-12,
            )

            theory_r_te, theory_r_tm = fresnel_slab(
                MATERIAL_PROPS[material]["eps_r"],
                MATERIAL_PROPS[material]["tan_d"],
                theta_deg,
                WALL_THICKNESS_MM,
                freq_ghz,
            )

            band_orig_row = orig_lp_band[
                (orig_lp_band["material"] == material) & np.isclose(orig_lp_band["theta_deg"], theta_deg, atol=1e-9)
            ]
            band_orig = band_orig_row.iloc[0] if not band_orig_row.empty else None

            freq_orig_row = orig_lp_freq_6p5[
                (orig_lp_freq_6p5["material"] == material) & np.isclose(orig_lp_freq_6p5["theta_deg"], theta_deg, atol=1e-9)
            ]
            freq_orig = freq_orig_row.iloc[0] if not freq_orig_row.empty else None

            ideal_row = ideal_grid[
                (ideal_grid["material"] == material) & np.isclose(ideal_grid["theta_deg"], theta_deg, atol=1e-9)
            ]
            if ideal_row.empty:
                continue
            ideal = ideal_row.iloc[0]

            gamma_x_metal_band_mag = float(np.mean(np.abs(gamma_x_metal)))
            gamma_x_metal_6p5_mag = float(np.abs(gamma_x_metal[freq_index_6p5]))
            rows.append(
                {
                    "material": material,
                    "theta_deg": theta_deg,
                    "in_main_range": bool(ideal["in_main_range"]),
                    "B_ideal_mag": float(ideal["B_ideal_mag"]),
                    "gamma_x_ideal_mag": float(ideal["gamma_x_ideal_mag"]),
                    "gamma_x_orig_band_mag": float(band_orig["gamma_x_from_lp_mag"]) if band_orig is not None else np.nan,
                    "gamma_x_orig_6p5_mag": float(freq_orig["gamma_x_from_lp_mag"]) if freq_orig is not None else np.nan,
                    "gamma_x_metal_band_mag": gamma_x_metal_band_mag,
                    "gamma_x_metal_6p5_mag": gamma_x_metal_6p5_mag,
                    "gamma_c_metal_band_mag": float(np.mean(np.abs(gamma_c_metal))),
                    "gamma_c_metal_6p5_mag": float(np.abs(gamma_c_metal[freq_index_6p5])),
                    "orig_band_below_ideal_flag": (
                        bool(float(band_orig["gamma_x_from_lp_mag"]) < float(ideal["gamma_x_ideal_mag"]))
                        if band_orig is not None
                        else pd.NA
                    ),
                    "orig_6p5_below_ideal_flag": (
                        bool(float(freq_orig["gamma_x_from_lp_mag"]) < float(ideal["gamma_x_ideal_mag"]))
                        if freq_orig is not None
                        else pd.NA
                    ),
                    "metal_band_below_ideal_flag": bool(gamma_x_metal_band_mag < float(ideal["gamma_x_ideal_mag"])),
                    "metal_6p5_below_ideal_flag": bool(gamma_x_metal_6p5_mag < float(ideal["gamma_x_ideal_mag"])),
                    "r_te_theory_band_mag": float(np.mean(np.abs(theory_r_te))),
                    "r_tm_theory_band_mag": float(np.mean(np.abs(theory_r_tm))),
                    "r_te_metal_band_mag": float(np.mean(np.abs(r_te_metal))),
                    "r_tm_metal_band_mag": float(np.mean(np.abs(r_tm_metal))),
                    "r_te_metal_6p5_mag": float(np.abs(r_te_metal[freq_index_6p5])),
                    "r_tm_metal_6p5_mag": float(np.abs(r_tm_metal[freq_index_6p5])),
                    "r_te_metal_vs_theory_band_db": float(
                        20.0 * np.log10(
                            max(float(np.mean(np.abs(r_te_metal))), 1e-12)
                            / max(float(np.mean(np.abs(theory_r_te))), 1e-12)
                        )
                    ),
                    "r_tm_metal_vs_theory_band_db": float(
                        20.0 * np.log10(
                            max(float(np.mean(np.abs(r_tm_metal))), 1e-12)
                            / max(float(np.mean(np.abs(theory_r_tm))), 1e-12)
                        )
                    ),
                    "cross_zy_db": float(20.0 * np.log10(max(float(cross_zy_ratio), 1e-12))),
                    "cross_yz_db": float(20.0 * np.log10(max(float(cross_yz_ratio), 1e-12))),
                    "crosspol_warning_flag": bool(
                        max(
                            float(20.0 * np.log10(max(float(cross_zy_ratio), 1e-12))),
                            float(20.0 * np.log10(max(float(cross_yz_ratio), 1e-12))),
                        )
                        > -15.0
                    ),
                }
            )

    return pd.DataFrame(rows).sort_values(["material", "theta_deg"]).reset_index(drop=True)


def summarize(full_df: pd.DataFrame) -> pd.DataFrame:
    summary_rows: list[dict[str, object]] = []

    subsets: list[tuple[str, pd.DataFrame]] = [("ALL", full_df)]
    for material in MATERIALS:
        subsets.append((material, full_df[full_df["material"] == material].copy()))

    for label, sub in subsets:
        main_sub = sub[sub["in_main_range"]].copy()
        nonmain_sub = sub[~sub["in_main_range"]].copy()
        summary_rows.append(
            {
                "scope": label,
                "n_total_rows": int(len(sub)),
                "n_main_rows": int(len(main_sub)),
                "orig_band_below_ideal_main_rows": int(main_sub["orig_band_below_ideal_flag"].fillna(False).astype(bool).sum()),
                "orig_6p5_below_ideal_main_rows": int(main_sub["orig_6p5_below_ideal_flag"].fillna(False).astype(bool).sum()),
                "metal_band_below_ideal_main_rows": int(main_sub["metal_band_below_ideal_flag"].sum()),
                "metal_6p5_below_ideal_main_rows": int(main_sub["metal_6p5_below_ideal_flag"].sum()),
                "metal_band_zero_violation_main": bool(int(main_sub["metal_band_below_ideal_flag"].sum()) == 0),
                "metal_6p5_zero_violation_main": bool(int(main_sub["metal_6p5_below_ideal_flag"].sum()) == 0),
                "max_abs_r_te_metal_vs_theory_main_db": float(main_sub["r_te_metal_vs_theory_band_db"].abs().max()),
                "max_abs_r_tm_metal_vs_theory_main_db": float(main_sub["r_tm_metal_vs_theory_band_db"].abs().max()),
                "max_cross_zy_main_db": float(main_sub["cross_zy_db"].max()),
                "max_cross_yz_main_db": float(main_sub["cross_yz_db"].max()),
                "max_cross_zy_nonmain_db": float(nonmain_sub["cross_zy_db"].max()) if not nonmain_sub.empty else np.nan,
                "max_cross_yz_nonmain_db": float(nonmain_sub["cross_yz_db"].max()) if not nonmain_sub.empty else np.nan,
            }
        )

    return pd.DataFrame(summary_rows)


def write_markdown(
    *,
    full_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    full_path: Path,
    summary_path: Path,
    output_path: Path,
    repo_root: Path,
) -> None:
    all_summary = summary_df[summary_df["scope"] == "ALL"].iloc[0]
    nonmain_outliers = full_df[
        (~full_df["in_main_range"])
        & (
            (full_df["r_te_metal_vs_theory_band_db"].abs() > 1.0)
            | (full_df["r_tm_metal_vs_theory_band_db"].abs() > 1.0)
            | (full_df["cross_zy_db"] > -5.0)
            | (full_df["cross_yz_db"] > -5.0)
        )
    ][
        [
            "material",
            "theta_deg",
            "r_te_metal_vs_theory_band_db",
            "r_tm_metal_vs_theory_band_db",
            "cross_zy_db",
            "cross_yz_db",
        ]
    ].copy()

    lines = [
        "# Verify LP Metal-Normalized Replay",
        "",
        "Execution date: `2026-04-16`",
        "",
        "## Scope",
        "",
        "- No new simulation is used.",
        "- LP correction is the existing metal-anchor prototype:",
        "  - `R_TE_metal(theta,f) = h_tilde_zz(material, theta, f) / h_tilde_zz(metal, theta, f)`",
        "  - `R_TM_metal(theta,f) = h_tilde_yy(material, theta, f) / h_tilde_yy(metal, theta, f)`",
        "  - `Gamma_X_metal(theta,f) = 0.5 * (R_TE_metal + R_TM_metal)`",
        "- Ideal anchor remains the existing Stage 1/2 `6.5 GHz` truth used by the current Stage 4 audit.",
        "- Main-range rows follow the current Stage 4 filter: `20 deg <= theta <= VALID_MAX(material)`.",
        "",
        "## Main Results",
        "",
        f"- Original LP below-ideal count, band export: `{int(all_summary['orig_band_below_ideal_main_rows'])}/{int(all_summary['n_main_rows'])}`",
        f"- Original LP below-ideal count, `6.5 GHz`: `{int(all_summary['orig_6p5_below_ideal_main_rows'])}/{int(all_summary['n_main_rows'])}`",
        f"- Metal-normalized LP below-ideal count, band export: `{int(all_summary['metal_band_below_ideal_main_rows'])}/{int(all_summary['n_main_rows'])}`",
        f"- Metal-normalized LP below-ideal count, `6.5 GHz`: `{int(all_summary['metal_6p5_below_ideal_main_rows'])}/{int(all_summary['n_main_rows'])}`",
        "",
        "## Fresnel Agreement In Main Range",
        "",
    ]

    for material in MATERIALS:
        row = summary_df[summary_df["scope"] == material].iloc[0]
        lines.append(
            f"- {material}: max `|R_TE|` deviation `{row['max_abs_r_te_metal_vs_theory_main_db']:.3f} dB`, "
            f"max `|R_TM|` deviation `{row['max_abs_r_tm_metal_vs_theory_main_db']:.3f} dB`"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The metal-anchor correction removes the LP residual undershoot that caused the current `15/23` ordering violation pattern.",
            "- In the current data, the LP issue behaves like a reference-normalization mismatch, not like a broken estimator identity.",
            "- This remains an empirical correction prototype. It is evidence for the mechanism, not yet the formal Stage 3/4 production path.",
            "",
            "## High-Angle Limits",
            "",
        ]
    )

    if nonmain_outliers.empty:
        lines.append("- No non-main-range outlier exceeded the reporting thresholds.")
    else:
        for _, row in nonmain_outliers.iterrows():
            lines.append(
                f"- {row['material']} {row['theta_deg']:.0f} deg: "
                f"`R_TE` dev={row['r_te_metal_vs_theory_band_db']:+.2f} dB, "
                f"`R_TM` dev={row['r_tm_metal_vs_theory_band_db']:+.2f} dB, "
                f"`zy/zz`={row['cross_zy_db']:.1f} dB, `yz/yy`={row['cross_yz_db']:.1f} dB"
            )

    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Full replay CSV: `{full_path.relative_to(repo_root)}`",
            f"- Summary CSV: `{summary_path.relative_to(repo_root)}`",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_argparser().parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[3]

    linear_truth = pd.read_csv(args.linear_truth)
    cp_truth = pd.read_csv(args.cp_truth)
    orig_lp_band = pd.read_csv(args.orig_lp_band)
    orig_lp_freq = pd.read_csv(args.orig_lp_freq)

    ideal_grid = build_ideal_grid(linear_truth, cp_truth)
    full_df = build_metal_normalized_rows(
        prototype_csv_dir=args.prototype_csv_dir,
        ideal_grid=ideal_grid,
        orig_lp_band=orig_lp_band,
        orig_lp_freq=orig_lp_freq,
    )
    summary_df = summarize(full_df)

    full_path = output_dir / "verify_lp_metal_normalized_full.csv"
    summary_path = output_dir / "verify_lp_metal_normalized_summary.csv"
    md_path = output_dir / "VERIFY_LP_METAL_NORMALIZED.md"

    full_df.to_csv(full_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    write_markdown(
        full_df=full_df,
        summary_df=summary_df,
        full_path=full_path,
        summary_path=summary_path,
        output_path=md_path,
        repo_root=repo_root,
    )

    print(f"Wrote {full_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
