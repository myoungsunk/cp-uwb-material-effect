from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


MATERIALS = ["concrete", "glass", "wood"]
VALID_MAX = {"concrete": 55.0, "glass": 60.0, "wood": 45.0}
TARGET_FREQS_GHZ = [6.24, 6.50, 6.74]
PLOT_FREQ_GHZ = 6.50
MAG_PASS_DB = 1.0
PHASE_PASS_DEG = 15.0
SMALL_REF_MAG = 0.05
DB_FLOOR = 1e-12
EXECUTION_DATE = "2026-04-16"


def build_argparser() -> argparse.ArgumentParser:
    bundle_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description=(
            "Compare cross-dipole CP ideal-source replay against CP truth synthesized "
            "from the Stage 1 ideal TE/TM truth table."
        )
    )
    parser.add_argument(
        "--los-csv",
        type=Path,
        default=Path(
            r"D:\codex\ansys_automation\downloads\sparam_export_20260416_172332\1.LoS_only\1.LoS_only__Setup1_-_Sweep.csv"
        ),
    )
    parser.add_argument(
        "--metal-csv",
        type=Path,
        default=Path(
            r"D:\codex\ansys_automation\downloads\sparam_export_20260416_172332\2.metal_R\2.metal_R__Setup1_-_Sweep.csv"
        ),
    )
    parser.add_argument(
        "--concrete-csv",
        type=Path,
        default=Path(
            r"D:\codex\ansys_automation\downloads\sparam_export_20260416_172332\2.concrete_R\2.concrete_R__Setup1_-_Sweep.csv"
        ),
    )
    parser.add_argument(
        "--glass-csv",
        type=Path,
        default=Path(
            r"D:\codex\ansys_automation\downloads\sparam_export_20260416_172332\2.glass_R\2.glass_R__Setup1_-_Sweep.csv"
        ),
    )
    parser.add_argument(
        "--wood-csv",
        type=Path,
        default=Path(
            r"D:\codex\ansys_automation\downloads\sparam_export_20260416_172332\2.wood_R\2.wood_R__Setup1_-_Sweep.csv"
        ),
    )
    parser.add_argument(
        "--cp-truth",
        type=Path,
        default=bundle_root / "data" / "stage_2_multifreq_20260416" / "sameflip_alias_20260416" / "truth_table_cp_locked_sameflip.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=bundle_root / "results" / "debug",
    )
    return parser


def theta_token(theta_deg: float) -> str:
    theta_scalar = float(theta_deg)
    if theta_scalar.is_integer():
        return f"{int(theta_scalar)}deg"
    return f"{theta_scalar:g}deg"


def complex_from_mag_phase(mag: np.ndarray, phase_deg: np.ndarray) -> np.ndarray:
    return mag * np.exp(1j * np.deg2rad(phase_deg))


def add_complex_columns(df: pd.DataFrame, prefix: str, values: np.ndarray) -> None:
    df[f"{prefix}_real"] = np.real(values)
    df[f"{prefix}_imag"] = np.imag(values)
    df[f"{prefix}_mag"] = np.abs(values)
    df[f"{prefix}_phase_deg"] = np.rad2deg(np.angle(values))


def phase_diff_deg(measured_phase_deg: float, target_phase_deg: float) -> float:
    return float(((measured_phase_deg - target_phase_deg + 180.0) % 360.0) - 180.0)


def safe_db_mag_ratio(measured_mag: float, target_mag: float) -> float:
    return float(20.0 * np.log10(max(float(measured_mag), DB_FLOOR) / max(float(target_mag), DB_FLOOR)))


def in_main_range(material: str, theta_deg: float) -> bool:
    return float(theta_deg) >= 20.0 and float(theta_deg) <= VALID_MAX[str(material)]


def channel_complex(df: pd.DataFrame, *, rx: str, tx: str, theta_deg: float | None) -> np.ndarray:
    variation = "nominal" if theta_deg is None else f"theta_r={theta_token(theta_deg)}"
    mag_col = f"mag(S(RX_{rx}_p1,TX_{tx}_p1)) [] - {variation}"
    phase_col = f"ang_deg(S(RX_{rx}_p1,TX_{tx}_p1)) [deg] - {variation}"
    mag = df[mag_col].to_numpy(dtype=float)
    phase_deg = df[phase_col].to_numpy(dtype=float)
    return complex_from_mag_phase(mag, phase_deg)


def extract_thetas(df: pd.DataFrame) -> list[float]:
    theta_pattern = re.compile(r"theta_r=([-+]?[0-9]*\.?[0-9]+)deg")
    theta_values: set[float] = set()
    for column in df.columns:
        match = theta_pattern.search(column)
        if match is not None:
            theta_values.add(float(match.group(1)))
    return sorted(theta_values)


def build_ratio_row(
    *,
    material: str,
    theta_deg: float,
    freq_ghz: float,
    gamma_ll: complex,
    gamma_lr: complex,
    gamma_rl: complex,
    gamma_rr: complex,
    gamma_cross: complex,
    gamma_cross_geomean: complex,
    gamma_same_ideal_abs: complex,
    gamma_flip_ideal_abs: complex,
    gamma_same_pec_abs: complex,
    gamma_flip_pec_abs: complex,
) -> dict[str, object]:
    gamma_rr_ideal_rel = gamma_same_ideal_abs / gamma_same_pec_abs
    gamma_cross_ideal_rel = gamma_flip_ideal_abs / gamma_flip_pec_abs
    row: dict[str, object] = {
        "material": material,
        "theta_deg": float(theta_deg),
        "freq_ghz": float(freq_ghz),
        "in_main_range": bool(in_main_range(material, theta_deg)),
        "rr_reference_small_flag": bool(np.abs(gamma_same_pec_abs) < SMALL_REF_MAG),
        "cross_reference_small_flag": bool(np.abs(gamma_flip_pec_abs) < SMALL_REF_MAG),
        "ll_rr_ratio_abs_diff": float(np.abs(gamma_ll - gamma_rr)),
        "ll_rr_ratio_rel_diff": float(np.abs(gamma_ll - gamma_rr) / max(max(np.abs(gamma_ll), np.abs(gamma_rr)), DB_FLOOR)),
        "lr_rl_ratio_abs_diff": float(np.abs(gamma_lr - gamma_rl)),
        "lr_rl_ratio_rel_diff": float(np.abs(gamma_lr - gamma_rl) / max(max(np.abs(gamma_lr), np.abs(gamma_rl)), DB_FLOOR)),
    }

    complex_map = {
        "gamma_ll": gamma_ll,
        "gamma_lr": gamma_lr,
        "gamma_rl": gamma_rl,
        "gamma_rr": gamma_rr,
        "gamma_cross": gamma_cross,
        "gamma_cross_geomean": gamma_cross_geomean,
        "gamma_same_ideal_abs": gamma_same_ideal_abs,
        "gamma_flip_ideal_abs": gamma_flip_ideal_abs,
        "gamma_same_pec_abs": gamma_same_pec_abs,
        "gamma_flip_pec_abs": gamma_flip_pec_abs,
        "gamma_rr_ideal_rel": gamma_rr_ideal_rel,
        "gamma_cross_ideal_rel": gamma_cross_ideal_rel,
    }
    for prefix, value in complex_map.items():
        row[f"{prefix}_real"] = float(np.real(value))
        row[f"{prefix}_imag"] = float(np.imag(value))
        row[f"{prefix}_mag"] = float(np.abs(value))
        row[f"{prefix}_phase_deg"] = float(np.rad2deg(np.angle(value)))

    row["gamma_rr_mag_error_db"] = safe_db_mag_ratio(row["gamma_rr_mag"], row["gamma_rr_ideal_rel_mag"])
    row["gamma_cross_mag_error_db"] = safe_db_mag_ratio(row["gamma_cross_mag"], row["gamma_cross_ideal_rel_mag"])
    row["gamma_rr_abs_mag_error"] = float(abs(row["gamma_rr_mag"] - row["gamma_rr_ideal_rel_mag"]))
    row["gamma_cross_abs_mag_error"] = float(abs(row["gamma_cross_mag"] - row["gamma_cross_ideal_rel_mag"]))
    row["gamma_rr_phase_error_deg"] = abs(phase_diff_deg(row["gamma_rr_phase_deg"], row["gamma_rr_ideal_rel_phase_deg"]))
    row["gamma_cross_phase_error_deg"] = abs(phase_diff_deg(row["gamma_cross_phase_deg"], row["gamma_cross_ideal_rel_phase_deg"]))
    row["gamma_rr_mag_pass_1db_flag"] = bool(abs(row["gamma_rr_mag_error_db"]) <= MAG_PASS_DB)
    row["gamma_cross_mag_pass_1db_flag"] = bool(abs(row["gamma_cross_mag_error_db"]) <= MAG_PASS_DB)
    row["gamma_rr_phase_pass_15deg_flag"] = bool(row["gamma_rr_phase_error_deg"] <= PHASE_PASS_DEG)
    row["gamma_cross_phase_pass_15deg_flag"] = bool(row["gamma_cross_phase_error_deg"] <= PHASE_PASS_DEG)
    row["gamma_rr_joint_pass_flag"] = bool(row["gamma_rr_mag_pass_1db_flag"] and row["gamma_rr_phase_pass_15deg_flag"])
    row["gamma_cross_joint_pass_flag"] = bool(row["gamma_cross_mag_pass_1db_flag"] and row["gamma_cross_phase_pass_15deg_flag"])
    return row


def build_full_table(
    *,
    los_df: pd.DataFrame,
    metal_df: pd.DataFrame,
    material_csv_map: dict[str, Path],
    cp_truth: pd.DataFrame,
) -> pd.DataFrame:
    freq_axis = metal_df["Freq [GHz]"].to_numpy(dtype=float)
    target_indices = [int(np.argmin(np.abs(freq_axis - target_freq))) for target_freq in TARGET_FREQS_GHZ]

    los_channels = {
        "ll": channel_complex(los_df, rx="LH", tx="LH", theta_deg=None),
        "lr": channel_complex(los_df, rx="LH", tx="RH", theta_deg=None),
        "rl": channel_complex(los_df, rx="RH", tx="LH", theta_deg=None),
        "rr": channel_complex(los_df, rx="RH", tx="RH", theta_deg=None),
    }

    material_frames = {material: pd.read_csv(path) for material, path in material_csv_map.items()}
    theta_values = extract_thetas(metal_df)
    rows: list[dict[str, object]] = []

    truth_df = cp_truth.copy()
    truth_df["freq_ghz"] = truth_df["f_hz"] / 1e9

    for material, material_df in material_frames.items():
        for theta_deg in theta_values:
            metal_channels = {
                "ll": channel_complex(metal_df, rx="LH", tx="LH", theta_deg=theta_deg) - los_channels["ll"],
                "lr": channel_complex(metal_df, rx="LH", tx="RH", theta_deg=theta_deg) - los_channels["lr"],
                "rl": channel_complex(metal_df, rx="RH", tx="LH", theta_deg=theta_deg) - los_channels["rl"],
                "rr": channel_complex(metal_df, rx="RH", tx="RH", theta_deg=theta_deg) - los_channels["rr"],
            }
            material_channels = {
                "ll": channel_complex(material_df, rx="LH", tx="LH", theta_deg=theta_deg) - los_channels["ll"],
                "lr": channel_complex(material_df, rx="LH", tx="RH", theta_deg=theta_deg) - los_channels["lr"],
                "rl": channel_complex(material_df, rx="RH", tx="LH", theta_deg=theta_deg) - los_channels["rl"],
                "rr": channel_complex(material_df, rx="RH", tx="RH", theta_deg=theta_deg) - los_channels["rr"],
            }

            for target_index in target_indices:
                freq_ghz = float(freq_axis[target_index])
                material_truth = truth_df[
                    truth_df["material"].astype(str).str.lower().eq(material)
                    & np.isclose(truth_df["theta_deg"], theta_deg)
                    & np.isclose(truth_df["freq_ghz"], freq_ghz)
                ]
                pec_truth = truth_df[
                    truth_df["material"].astype(str).str.lower().eq("pec")
                    & np.isclose(truth_df["theta_deg"], theta_deg)
                    & np.isclose(truth_df["freq_ghz"], freq_ghz)
                ]
                if material_truth.empty or pec_truth.empty:
                    continue

                material_truth_row = material_truth.iloc[0]
                pec_truth_row = pec_truth.iloc[0]
                gamma_same_ideal_abs = complex(
                    material_truth_row["Gamma_same_real"],
                    material_truth_row["Gamma_same_imag"],
                )
                gamma_flip_ideal_abs = complex(
                    material_truth_row["Gamma_flip_real"],
                    material_truth_row["Gamma_flip_imag"],
                )
                gamma_same_pec_abs = complex(
                    pec_truth_row["Gamma_same_real"],
                    pec_truth_row["Gamma_same_imag"],
                )
                gamma_flip_pec_abs = complex(
                    pec_truth_row["Gamma_flip_real"],
                    pec_truth_row["Gamma_flip_imag"],
                )

                gamma_ll = material_channels["ll"][target_index] / metal_channels["ll"][target_index]
                gamma_lr = material_channels["lr"][target_index] / metal_channels["lr"][target_index]
                gamma_rl = material_channels["rl"][target_index] / metal_channels["rl"][target_index]
                gamma_rr = material_channels["rr"][target_index] / metal_channels["rr"][target_index]
                gamma_cross = 0.5 * (gamma_lr + gamma_rl)
                gamma_cross_geomean = np.sqrt(gamma_lr * gamma_rl)

                rows.append(
                    build_ratio_row(
                        material=material,
                        theta_deg=theta_deg,
                        freq_ghz=freq_ghz,
                        gamma_ll=gamma_ll,
                        gamma_lr=gamma_lr,
                        gamma_rl=gamma_rl,
                        gamma_rr=gamma_rr,
                        gamma_cross=gamma_cross,
                        gamma_cross_geomean=gamma_cross_geomean,
                        gamma_same_ideal_abs=gamma_same_ideal_abs,
                        gamma_flip_ideal_abs=gamma_flip_ideal_abs,
                        gamma_same_pec_abs=gamma_same_pec_abs,
                        gamma_flip_pec_abs=gamma_flip_pec_abs,
                    )
                )

    return pd.DataFrame(rows).sort_values(["material", "theta_deg", "freq_ghz"]).reset_index(drop=True)


def summarize_branch(
    sub: pd.DataFrame,
    *,
    branch_prefix: str,
    scope: str,
    material: str,
    freq_label: str,
) -> dict[str, object]:
    return {
        "scope": scope,
        "material": material,
        "freq_ghz": freq_label,
        "branch": branch_prefix,
        "n_rows": int(len(sub)),
        "rr_reference_small_rows": int(sub["rr_reference_small_flag"].sum()) if branch_prefix == "gamma_rr" else np.nan,
        "cross_reference_small_rows": int(sub["cross_reference_small_flag"].sum()) if branch_prefix == "gamma_cross" else np.nan,
        "mean_signed_mag_error_db": float(sub[f"{branch_prefix}_mag_error_db"].mean()),
        "mean_abs_mag_error_db": float(sub[f"{branch_prefix}_mag_error_db"].abs().mean()),
        "mean_abs_mag_error_linear": float(sub[f"{branch_prefix}_abs_mag_error"].mean()),
        "mean_phase_error_deg": float(sub[f"{branch_prefix}_phase_error_deg"].mean()),
        "rows_mag_pass_1db": int(sub[f"{branch_prefix}_mag_pass_1db_flag"].sum()),
        "rows_phase_pass_15deg": int(sub[f"{branch_prefix}_phase_pass_15deg_flag"].sum()),
        "rows_joint_pass": int(sub[f"{branch_prefix}_joint_pass_flag"].sum()),
        "joint_pass_rate": float(sub[f"{branch_prefix}_joint_pass_flag"].mean()),
    }


def build_summary(full_df: pd.DataFrame) -> pd.DataFrame:
    summary_rows: list[dict[str, object]] = []
    scope_map = {
        "all": full_df,
        "main_range": full_df[full_df["in_main_range"].astype(bool)].copy(),
    }
    for scope, scope_df in scope_map.items():
        for material in ["all", *MATERIALS]:
            material_df = scope_df if material == "all" else scope_df[scope_df["material"] == material].copy()
            if material_df.empty:
                continue
            for freq_label, freq_df in [("all", material_df)] + [
                (f"{target_freq:.2f}", material_df[np.isclose(material_df["freq_ghz"], target_freq)].copy())
                for target_freq in TARGET_FREQS_GHZ
            ]:
                if freq_df.empty:
                    continue
                for branch_prefix in ("gamma_rr", "gamma_cross"):
                    summary_rows.append(
                        summarize_branch(
                            freq_df,
                            branch_prefix=branch_prefix,
                            scope=scope,
                            material=material,
                            freq_label=freq_label,
                        )
                    )

    return pd.DataFrame(summary_rows)


def plot_6p5_magnitude(full_df: pd.DataFrame, output_path: Path) -> None:
    plot_df = full_df[np.isclose(full_df["freq_ghz"], PLOT_FREQ_GHZ)].copy()
    fig, axes = plt.subplots(2, len(MATERIALS), figsize=(16, 7), sharex=True, constrained_layout=True)

    for column_index, material in enumerate(MATERIALS):
        sub = plot_df[plot_df["material"] == material].sort_values("theta_deg")

        ax_cross = axes[0, column_index]
        ax_cross.plot(sub["theta_deg"], 20.0 * np.log10(sub["gamma_cross_mag"].clip(lower=DB_FLOOR)), marker="o", linewidth=2.0, label="Measured cross")
        ax_cross.plot(
            sub["theta_deg"],
            20.0 * np.log10(sub["gamma_cross_ideal_rel_mag"].clip(lower=DB_FLOOR)),
            marker="s",
            linewidth=2.0,
            linestyle="--",
            label="Ideal cross / PEC",
        )
        ax_cross.set_title(material.capitalize())
        ax_cross.grid(True, alpha=0.25, linewidth=0.8)
        if column_index == 0:
            ax_cross.set_ylabel("Cross mag (dB)")

        ax_rr = axes[1, column_index]
        ax_rr.plot(sub["theta_deg"], 20.0 * np.log10(sub["gamma_rr_mag"].clip(lower=DB_FLOOR)), marker="o", linewidth=2.0, label="Measured RR")
        ax_rr.plot(
            sub["theta_deg"],
            20.0 * np.log10(sub["gamma_rr_ideal_rel_mag"].clip(lower=DB_FLOOR)),
            marker="s",
            linewidth=2.0,
            linestyle="--",
            label="Ideal same / PEC",
        )
        ax_rr.grid(True, alpha=0.25, linewidth=0.8)
        ax_rr.set_xlabel("Theta (deg)")
        if column_index == 0:
            ax_rr.set_ylabel("RR mag (dB)")

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.03))
    fig.suptitle("Cross-Dipole CP vs TE/TM-Synthesized CP at 6.50 GHz", y=1.07)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_6p5_phase(full_df: pd.DataFrame, output_path: Path) -> None:
    plot_df = full_df[np.isclose(full_df["freq_ghz"], PLOT_FREQ_GHZ)].copy()
    fig, axes = plt.subplots(2, len(MATERIALS), figsize=(16, 7), sharex=True, constrained_layout=True)

    for column_index, material in enumerate(MATERIALS):
        sub = plot_df[plot_df["material"] == material].sort_values("theta_deg")

        ax_cross = axes[0, column_index]
        ax_cross.plot(sub["theta_deg"], sub["gamma_cross_phase_deg"], marker="o", linewidth=2.0, label="Measured cross")
        ax_cross.plot(sub["theta_deg"], sub["gamma_cross_ideal_rel_phase_deg"], marker="s", linewidth=2.0, linestyle="--", label="Ideal cross / PEC")
        ax_cross.set_title(material.capitalize())
        ax_cross.grid(True, alpha=0.25, linewidth=0.8)
        if column_index == 0:
            ax_cross.set_ylabel("Cross phase (deg)")

        ax_rr = axes[1, column_index]
        ax_rr.plot(sub["theta_deg"], sub["gamma_rr_phase_deg"], marker="o", linewidth=2.0, label="Measured RR")
        ax_rr.plot(sub["theta_deg"], sub["gamma_rr_ideal_rel_phase_deg"], marker="s", linewidth=2.0, linestyle="--", label="Ideal same / PEC")
        ax_rr.grid(True, alpha=0.25, linewidth=0.8)
        ax_rr.set_xlabel("Theta (deg)")
        if column_index == 0:
            ax_rr.set_ylabel("RR phase (deg)")

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.03))
    fig.suptitle("Cross-Dipole CP Phase vs TE/TM-Synthesized CP at 6.50 GHz", y=1.07)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def write_markdown(
    *,
    full_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    full_path: Path,
    summary_path: Path,
    magnitude_plot_path: Path,
    phase_plot_path: Path,
    output_path: Path,
    repo_root: Path,
) -> None:
    main_cross = summary_df[
        summary_df["scope"].eq("main_range")
        & summary_df["material"].eq("all")
        & summary_df["freq_ghz"].eq("all")
        & summary_df["branch"].eq("gamma_cross")
    ].iloc[0]
    main_rr = summary_df[
        summary_df["scope"].eq("main_range")
        & summary_df["material"].eq("all")
        & summary_df["freq_ghz"].eq("all")
        & summary_df["branch"].eq("gamma_rr")
    ].iloc[0]
    center_cross = summary_df[
        summary_df["scope"].eq("main_range")
        & summary_df["material"].eq("all")
        & summary_df["freq_ghz"].eq(f"{PLOT_FREQ_GHZ:.2f}")
        & summary_df["branch"].eq("gamma_cross")
    ].iloc[0]
    center_rr = summary_df[
        summary_df["scope"].eq("main_range")
        & summary_df["material"].eq("all")
        & summary_df["freq_ghz"].eq(f"{PLOT_FREQ_GHZ:.2f}")
        & summary_df["branch"].eq("gamma_rr")
    ].iloc[0]

    pec_same_min = float(full_df["gamma_same_pec_abs_mag"].min())
    pec_same_max = float(full_df["gamma_same_pec_abs_mag"].max())
    lr_rl_max_rel = float(full_df["lr_rl_ratio_rel_diff"].max())
    ll_rr_max_rel = float(full_df["ll_rr_ratio_rel_diff"].max())

    worst_rr = (
        full_df[full_df["in_main_range"].astype(bool)]
        .groupby(["material", "theta_deg"], as_index=False)["gamma_rr_mag_error_db"]
        .mean()
        .assign(abs_rr_mag_error_db=lambda df: df["gamma_rr_mag_error_db"].abs())
        .sort_values("abs_rr_mag_error_db", ascending=False)
        .head(5)
    )
    best_cross = (
        full_df[full_df["in_main_range"].astype(bool)]
        .groupby(["material", "theta_deg"], as_index=False)["gamma_cross_mag_error_db"]
        .mean()
        .sort_values("gamma_cross_mag_error_db", key=lambda s: s.abs())
        .head(5)
    )

    lines = [
        "# Verify Cross-Dipole CP vs Ideal TE/TM",
        "",
        f"Execution date: `{EXECUTION_DATE}`",
        "",
        "## Scope",
        "",
        "- External input is the cross-dipole CP ideal-source export with one LoS-only file plus metal/material reflection files.",
        "- Stage 1 ideal TE/TM truth is first synthesized into CP truth using:",
        "  - `Gamma_same = 0.5 * (R_TE + R_TM)`",
        "  - `Gamma_flip = 0.5 * (R_TE - R_TM)`",
        "- Because the external CP replay is built as `material / metal` channel ratios, the authoritative ideal target is also PEC-normalized:",
        "  - `gamma_rr_ideal = Gamma_same(material) / Gamma_same(PEC)`",
        "  - `gamma_cross_ideal = Gamma_flip(material) / Gamma_flip(PEC)`",
        "- Measurement-side definitions:",
        "  - `gamma_rr = h_tilde_RR(material) / h_tilde_RR(metal)`",
        "  - `gamma_cross = 0.5 * [h_tilde_LR(material) / h_tilde_LR(metal) + h_tilde_RL(material) / h_tilde_RL(metal)]`",
        "- Only the three available multifreq truth points are compared: `6.24`, `6.50`, `6.74 GHz`.",
        "",
        "## Main Findings",
        "",
        f"- `gamma_cross` tracks the PEC-normalized ideal CP target reasonably well in the current main range: mean abs magnitude error `{main_cross['mean_abs_mag_error_db']:.3f} dB`, mean phase error `{main_cross['mean_phase_error_deg']:.2f} deg`, joint pass `{int(main_cross['rows_joint_pass'])}/{int(main_cross['n_rows'])}`.",
        f"- At the center point `6.50 GHz`, `gamma_cross` stays similar: mean abs magnitude error `{center_cross['mean_abs_mag_error_db']:.3f} dB`, mean phase error `{center_cross['mean_phase_error_deg']:.2f} deg`.",
        f"- `gamma_rr` does not reproduce the PEC-normalized same-hand ideal target: main-range mean abs magnitude error `{main_rr['mean_abs_mag_error_db']:.3f} dB`, mean phase error `{main_rr['mean_phase_error_deg']:.2f} deg`, joint pass `{int(main_rr['rows_joint_pass'])}/{int(main_rr['n_rows'])}`.",
        f"- The same-hand PEC reference is intrinsically tiny in this dataset: `|Gamma_same(PEC)|` ranges from `{pec_same_min:.6f}` to `{pec_same_max:.6f}` across the compared rows. That makes the RR normalization path ill-conditioned.",
        f"- The cross-hand average is numerically safe because `LR` and `RL` remain symmetric: max relative mismatch `{lr_rl_max_rel:.3e}`. Same-hand `LL/RR` is much less stable once the reference branch approaches zero: max relative mismatch `{ll_rr_max_rel:.3e}`.",
        "",
        "## Interpretation",
        "",
        "- With the current cross-dipole ideal-source replay, the cross-hand CP branch behaves like a valid proxy for the TE/TM-synthesized CP dominant branch.",
        "- The same-hand RR branch is not a stable truth-comparable observable under the same PEC-normalized construction.",
        "- So this dataset supports `gamma_cross` as the cleaner comparison axis, while `gamma_rr` remains dominated by the small-reference same-hand residual problem.",
        "",
        "## Best Cross-Hand Rows",
        "",
    ]

    for _, row in best_cross.iterrows():
        lines.append(
            f"- {row['material']} {row['theta_deg']:.0f} deg: mean cross mag error `{row['gamma_cross_mag_error_db']:.3f} dB`"
        )

    lines.extend(["", "## Worst RR Rows", ""])
    for _, row in worst_rr.iterrows():
        lines.append(
            f"- {row['material']} {row['theta_deg']:.0f} deg: mean RR mag error `{row['gamma_rr_mag_error_db']:.3f} dB`"
        )

    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Full CSV: `{full_path.relative_to(repo_root)}`",
            f"- Summary CSV: `{summary_path.relative_to(repo_root)}`",
            f"- 6.50 GHz magnitude plot: `{magnitude_plot_path.relative_to(repo_root)}`",
            f"- 6.50 GHz phase plot: `{phase_plot_path.relative_to(repo_root)}`",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_argparser().parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[3]

    los_df = pd.read_csv(args.los_csv)
    metal_df = pd.read_csv(args.metal_csv)
    cp_truth = pd.read_csv(args.cp_truth)
    full_df = build_full_table(
        los_df=los_df,
        metal_df=metal_df,
        material_csv_map={
            "concrete": args.concrete_csv,
            "glass": args.glass_csv,
            "wood": args.wood_csv,
        },
        cp_truth=cp_truth,
    )
    summary_df = build_summary(full_df)

    full_path = output_dir / "verify_cross_dipole_cp_vs_ideal_te_tm_full.csv"
    summary_path = output_dir / "verify_cross_dipole_cp_vs_ideal_te_tm_summary.csv"
    magnitude_plot_path = output_dir / "verify_cross_dipole_cp_vs_ideal_te_tm_6p5ghz_mag.png"
    phase_plot_path = output_dir / "verify_cross_dipole_cp_vs_ideal_te_tm_6p5ghz_phase.png"
    md_path = output_dir / "VERIFY_CROSS_DIPOLE_CP_VS_IDEAL_TE_TM.md"

    full_df.to_csv(full_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    plot_6p5_magnitude(full_df, magnitude_plot_path)
    plot_6p5_phase(full_df, phase_plot_path)
    write_markdown(
        full_df=full_df,
        summary_df=summary_df,
        full_path=full_path,
        summary_path=summary_path,
        magnitude_plot_path=magnitude_plot_path,
        phase_plot_path=phase_plot_path,
        output_path=md_path,
        repo_root=repo_root,
    )

    print(f"Wrote {full_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {magnitude_plot_path}")
    print(f"Wrote {phase_plot_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
