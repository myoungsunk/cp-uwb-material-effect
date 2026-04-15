# Consolidated review copy for paper-pipeline code assessment.
# Stage: 1
# Role: Fresnel sanity-check script for the locked ideal truth table.
# Source: analysis_stages/ideal_te_tm_scattered_stage/code/sanity_check_fresnel.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

from stage_1_geometry import SPEED_OF_LIGHT

matplotlib.use("Agg")
import matplotlib.pyplot as plt

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SLAB_THICKNESS_M = 0.1
DEFAULT_INPUT_RELATIVE = Path("results") / "a12_corr_full" / "truth_table_linear_locked.csv"
DEFAULT_OUTPUT_RELATIVE = Path("results")
MATERIAL_PERMITTIVITY = {
    "concrete": 5.24 * (1.0 - 1j * 0.105),
    "glass": 6.31 * (1.0 - 1j * 0.019),
    "wood": 1.99 * (1.0 - 1j * 0.049),
}
MATERIAL_THICKNESS_M = {
    "concrete": 0.1,
    "glass": 0.1,
    "wood": 0.1,
}
PEC_PHASE_TARGETS_DEG = {"TE": 180.0, "TM": 0.0}
PEC_KOBS_ANGLES_DEG = [70.0, 75.0, 80.0, 85.0]
R_MAG_TOL = 0.05
PASSIVITY_LIMIT = 1.01
T_MAG_LIMIT = 1.0
PEC_PHASE_TOL_DEG = 5.0
MATERIAL_PHASE_TOL_DEG = 10.0
PEC_PHASE_MAG_WINDOW = 0.10


@dataclass(frozen=True)
class SlabCoefficients:
    r_te: complex
    t_te: complex
    r_tm: complex
    t_tm: complex


def find_stage_root(start: Path) -> Path:
    return start.resolve().parents[1]


def parse_args() -> argparse.Namespace:
    stage_root = find_stage_root(Path(__file__))
    parser = argparse.ArgumentParser(
        description="Read-only Fresnel sanity checks for the ideal TE/TM scattered truth table."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=stage_root / DEFAULT_INPUT_RELATIVE,
        help="Input locked linear truth-table CSV path.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=stage_root / DEFAULT_OUTPUT_RELATIVE,
        help="Directory for comparison CSV and PEC convergence plot.",
    )
    parser.add_argument(
        "--slab-thickness-m",
        type=float,
        default=SLAB_THICKNESS_M,
        help="Physical slab thickness used by the Fresnel reference.",
    )
    return parser.parse_args()


def complex_series(df: pd.DataFrame, prefix: str) -> np.ndarray:
    return df[f"{prefix}_real"].to_numpy(dtype=float) + 1j * df[f"{prefix}_imag"].to_numpy(dtype=float)


def wrap_phase_delta_deg(measured_deg: float, target_deg: float) -> float:
    return float((measured_deg - target_deg + 180.0) % 360.0 - 180.0)


def phase_status(
    material: str,
    pol: str,
    measured_phase_deg: float,
    target_phase_deg: float,
    measured_mag: float,
) -> tuple[str, float]:
    if pd.isna(measured_phase_deg) or pd.isna(measured_mag):
        return "MISSING", math.nan
    if material == "pec":
        if abs(measured_mag - 1.0) > PEC_PHASE_MAG_WINDOW:
            return "SKIP", math.nan
        delta = wrap_phase_delta_deg(measured_phase_deg, target_phase_deg)
        return ("PASS" if abs(delta) <= PEC_PHASE_TOL_DEG else "FAIL"), delta

    delta = wrap_phase_delta_deg(measured_phase_deg, target_phase_deg)
    return ("PASS" if abs(delta) <= MATERIAL_PHASE_TOL_DEG else "FAIL"), delta


def overall_status(*checks: str) -> str:
    if any(status == "MISSING" for status in checks):
        return "MISSING"
    return "PASS" if all(status == "PASS" for status in checks if status != "SKIP") else "FAIL"


def slab_thickness_for_material(material: str, fallback_thickness_m: float) -> float:
    return float(MATERIAL_THICKNESS_M.get(str(material), fallback_thickness_m))


def choose_longitudinal_index(n_medium: complex, theta_deg: float) -> complex:
    sin_theta_i = math.sin(math.radians(theta_deg))
    q = np.lib.scimath.sqrt(n_medium * n_medium - sin_theta_i * sin_theta_i)
    if np.real(q) < 0.0:
        q = -q
    return complex(q)


def slab_fresnel_coefficients(
    material: str,
    theta_deg: float,
    freq_hz: float,
    slab_thickness_m: float,
) -> SlabCoefficients:
    if material == "pec":
        return SlabCoefficients(r_te=-1.0 + 0j, t_te=0.0 + 0j, r_tm=1.0 + 0j, t_tm=0.0 + 0j)

    if material not in MATERIAL_PERMITTIVITY:
        raise ValueError(f"Unsupported material: {material}")

    eps_r = MATERIAL_PERMITTIVITY[material]
    n_medium = np.lib.scimath.sqrt(eps_r)
    theta_i = math.radians(theta_deg)
    cos_theta_i = math.cos(theta_i)
    q = choose_longitudinal_index(n_medium, theta_deg)
    cos_theta_t = q / n_medium

    r12_te = (cos_theta_i - n_medium * cos_theta_t) / (cos_theta_i + n_medium * cos_theta_t)
    r12_tm = (n_medium * cos_theta_i - cos_theta_t) / (n_medium * cos_theta_i + cos_theta_t)
    r23_te = -r12_te
    r23_tm = -r12_tm

    t12_te = 2.0 * cos_theta_i / (cos_theta_i + n_medium * cos_theta_t)
    t23_te = 2.0 * n_medium * cos_theta_t / (n_medium * cos_theta_t + cos_theta_i)
    t12_tm = 2.0 * cos_theta_i / (n_medium * cos_theta_i + cos_theta_t)
    t23_tm = 2.0 * n_medium * cos_theta_t / (cos_theta_t + n_medium * cos_theta_i)

    k0 = 2.0 * math.pi * float(freq_hz) / SPEED_OF_LIGHT
    single_pass = np.exp(-1j * k0 * slab_thickness_m * q)
    round_trip = np.exp(-2j * k0 * slab_thickness_m * q)

    r_te = (r12_te + r23_te * round_trip) / (1.0 + r12_te * r23_te * round_trip)
    t_te = t12_te * t23_te * single_pass / (1.0 + r12_te * r23_te * round_trip)
    r_tm = (r12_tm + r23_tm * round_trip) / (1.0 + r12_tm * r23_tm * round_trip)
    t_tm = t12_tm * t23_tm * single_pass / (1.0 + r12_tm * r23_tm * round_trip)
    return SlabCoefficients(r_te=complex(r_te), t_te=complex(t_te), r_tm=complex(r_tm), t_tm=complex(t_tm))


def build_comparison_table(df: pd.DataFrame, slab_thickness_m: float) -> pd.DataFrame:
    df = df.reset_index(drop=True).copy()
    rows: list[dict] = []

    r_te_hfss = complex_series(df, "R_TE")
    t_te_hfss = complex_series(df, "T_TE")
    r_tm_hfss = complex_series(df, "R_TM")
    t_tm_hfss = complex_series(df, "T_TM")

    for idx, row in df.iterrows():
        material = str(row["material"])
        row_slab_thickness_m = slab_thickness_for_material(material, slab_thickness_m)
        theory = slab_fresnel_coefficients(
            material=material,
            theta_deg=float(row["theta_deg"]),
            freq_hz=float(row["f_hz"]),
            slab_thickness_m=row_slab_thickness_m,
        )

        passivity_te_hfss = float(abs(r_te_hfss[idx]) ** 2 + abs(t_te_hfss[idx]) ** 2)
        passivity_tm_hfss = float(abs(r_tm_hfss[idx]) ** 2 + abs(t_tm_hfss[idx]) ** 2)
        passivity_te_theory = float(abs(theory.r_te) ** 2 + abs(theory.t_te) ** 2)
        passivity_tm_theory = float(abs(theory.r_tm) ** 2 + abs(theory.t_tm) ** 2)

        te_available = pd.notna(row["R_TE_mag"]) and pd.notna(row["T_TE_mag"]) and pd.notna(row["R_TE_phase_deg"])
        tm_available = pd.notna(row["R_TM_mag"]) and pd.notna(row["T_TM_mag"]) and pd.notna(row["R_TM_phase_deg"])

        r_te_mag_status = (
            "PASS" if te_available and abs(abs(r_te_hfss[idx]) - abs(theory.r_te)) < R_MAG_TOL else "FAIL"
        )
        r_tm_mag_status = (
            "PASS" if tm_available and abs(abs(r_tm_hfss[idx]) - abs(theory.r_tm)) < R_MAG_TOL else "FAIL"
        )
        t_te_mag_status = "PASS" if te_available and abs(t_te_hfss[idx]) <= T_MAG_LIMIT else "FAIL"
        t_tm_mag_status = "PASS" if tm_available and abs(t_tm_hfss[idx]) <= T_MAG_LIMIT else "FAIL"
        passivity_te_status = "PASS" if te_available and passivity_te_hfss <= PASSIVITY_LIMIT else "FAIL"
        passivity_tm_status = "PASS" if tm_available and passivity_tm_hfss <= PASSIVITY_LIMIT else "FAIL"
        if not te_available:
            r_te_mag_status = "MISSING"
            t_te_mag_status = "MISSING"
            passivity_te_status = "MISSING"
        if not tm_available:
            r_tm_mag_status = "MISSING"
            t_tm_mag_status = "MISSING"
            passivity_tm_status = "MISSING"

        te_phase_target_deg = (
            PEC_PHASE_TARGETS_DEG["TE"] if material == "pec" else float(np.rad2deg(np.angle(theory.r_te)))
        )
        tm_phase_target_deg = (
            PEC_PHASE_TARGETS_DEG["TM"] if material == "pec" else float(np.rad2deg(np.angle(theory.r_tm)))
        )
        r_te_phase_status, r_te_phase_delta_deg = phase_status(
            material=material,
            pol="TE",
            measured_phase_deg=float(row["R_TE_phase_deg"]),
            target_phase_deg=te_phase_target_deg,
            measured_mag=float(row["R_TE_mag"]),
        )
        r_tm_phase_status, r_tm_phase_delta_deg = phase_status(
            material=material,
            pol="TM",
            measured_phase_deg=float(row["R_TM_phase_deg"]),
            target_phase_deg=tm_phase_target_deg,
            measured_mag=float(row["R_TM_mag"]),
        )

        rows.append(
            {
                "case": row["case"],
                "material": material,
                "run_label": row["run_label"],
                "f_hz": float(row["f_hz"]),
                "theta_deg": float(row["theta_deg"]),
                "observation_distance_lambda_scale": float(row["observation_distance_lambda_scale"]),
                "slab_thickness_m": row_slab_thickness_m,
                "R_TE_mag_HFSS": float(row["R_TE_mag"]),
                "R_TE_mag_theory": float(abs(theory.r_te)),
                "delta_R_TE_mag": float(abs(row["R_TE_mag"] - abs(theory.r_te))),
                "R_TM_mag_HFSS": float(row["R_TM_mag"]),
                "R_TM_mag_theory": float(abs(theory.r_tm)),
                "delta_R_TM_mag": float(abs(row["R_TM_mag"] - abs(theory.r_tm))),
                "T_TE_mag_HFSS": float(row["T_TE_mag"]),
                "T_TE_mag_theory": float(abs(theory.t_te)),
                "delta_T_TE_mag": float(abs(row["T_TE_mag"] - abs(theory.t_te))),
                "T_TM_mag_HFSS": float(row["T_TM_mag"]),
                "T_TM_mag_theory": float(abs(theory.t_tm)),
                "delta_T_TM_mag": float(abs(row["T_TM_mag"] - abs(theory.t_tm))),
                "R_TE_phase_deg_HFSS": float(row["R_TE_phase_deg"]),
                "R_TE_phase_deg_theory": te_phase_target_deg,
                "delta_R_TE_phase_deg_wrapped": r_te_phase_delta_deg,
                "R_TM_phase_deg_HFSS": float(row["R_TM_phase_deg"]),
                "R_TM_phase_deg_theory": tm_phase_target_deg,
                "delta_R_TM_phase_deg_wrapped": r_tm_phase_delta_deg,
                "passivity_TE_HFSS": passivity_te_hfss,
                "passivity_TE_theory": passivity_te_theory,
                "passivity_TM_HFSS": passivity_tm_hfss,
                "passivity_TM_theory": passivity_tm_theory,
                "R_TE_mag_status": r_te_mag_status,
                "R_TM_mag_status": r_tm_mag_status,
                "T_TE_mag_status": t_te_mag_status,
                "T_TM_mag_status": t_tm_mag_status,
                "passivity_TE_status": passivity_te_status,
                "passivity_TM_status": passivity_tm_status,
                "R_TE_phase_status": r_te_phase_status,
                "R_TM_phase_status": r_tm_phase_status,
                "overall_TE_status": overall_status(
                    r_te_mag_status,
                    t_te_mag_status,
                    passivity_te_status,
                    r_te_phase_status,
                ),
                "overall_TM_status": overall_status(
                    r_tm_mag_status,
                    t_tm_mag_status,
                    passivity_tm_status,
                    r_tm_phase_status,
                ),
            }
        )

    return pd.DataFrame(rows).sort_values(
        ["material", "theta_deg", "observation_distance_lambda_scale", "run_label"]
    ).reset_index(drop=True)


def print_row_table(comparison: pd.DataFrame) -> None:
    display_columns = [
        "material",
        "theta_deg",
        "observation_distance_lambda_scale",
        "R_TE_mag_HFSS",
        "R_TE_mag_theory",
        "T_TE_mag_HFSS",
        "passivity_TE_HFSS",
        "overall_TE_status",
        "R_TM_mag_HFSS",
        "R_TM_mag_theory",
        "T_TM_mag_HFSS",
        "passivity_TM_HFSS",
        "overall_TM_status",
    ]
    print("=" * 104)
    print("Row-Level Fresnel Sanity Check")
    print("=" * 104)
    print(comparison[display_columns].to_string(index=False))


def print_summary(comparison: pd.DataFrame) -> None:
    summary_rows: list[dict] = []

    for material in sorted(comparison["material"].unique()):
        material_rows = comparison[comparison["material"] == material]
        for pol in ["TE", "TM"]:
            overall_col = f"overall_{pol}_status"
            r_mag_col = f"R_{pol}_mag_status"
            t_mag_col = f"T_{pol}_mag_status"
            passivity_col = f"passivity_{pol}_status"
            phase_col = f"R_{pol}_phase_status"
            available_rows = int((material_rows[overall_col] != "MISSING").sum())
            phase_checked = int(material_rows[phase_col].isin(["PASS", "FAIL"]).sum())
            phase_pass = int((material_rows[phase_col] == "PASS").sum())
            summary_rows.append(
                {
                    "material": material,
                    "pol": pol,
                    "rows_total": int(len(material_rows)),
                    "rows_available": available_rows,
                    "overall_pass": int((material_rows[overall_col] == "PASS").sum()),
                    "R_mag_pass": int((material_rows[r_mag_col] == "PASS").sum()),
                    "T_mag_pass": int((material_rows[t_mag_col] == "PASS").sum()),
                    "passivity_pass": int((material_rows[passivity_col] == "PASS").sum()),
                    "phase_pass": phase_pass,
                    "phase_checked": phase_checked,
                }
            )

    summary_df = pd.DataFrame(summary_rows)
    print()
    print("=" * 104)
    print("Per-Material / Polarization Summary")
    print("=" * 104)
    print(summary_df.to_string(index=False))

    phase_fails = comparison[
        ((comparison["R_TE_phase_status"] == "FAIL") | (comparison["R_TM_phase_status"] == "FAIL"))
    ][
        [
            "material",
            "theta_deg",
            "observation_distance_lambda_scale",
            "R_TE_phase_deg_HFSS",
            "R_TE_phase_deg_theory",
            "delta_R_TE_phase_deg_wrapped",
            "R_TE_phase_status",
            "R_TM_phase_deg_HFSS",
            "R_TM_phase_deg_theory",
            "delta_R_TM_phase_deg_wrapped",
            "R_TM_phase_status",
        ]
    ]
    if not phase_fails.empty:
        print()
        print("=" * 104)
        print("Phase Failures")
        print("=" * 104)
        print(phase_fails.to_string(index=False))


def plot_pec_kobs_convergence(df: pd.DataFrame, output_path: Path) -> None:
    pec_rows = df[df["material"] == "pec"].copy()
    figure, axes = plt.subplots(2, 2, figsize=(11, 8.5), sharey=True)
    axes_flat = axes.flatten()
    handles = None
    labels = None

    for ax, theta_deg in zip(axes_flat, PEC_KOBS_ANGLES_DEG):
        sub = pec_rows[np.isclose(pec_rows["theta_deg"], theta_deg)].sort_values(
            "observation_distance_lambda_scale"
        )
        if sub.empty:
            ax.text(0.5, 0.5, f"No PEC rows for {theta_deg:.0f} deg", ha="center", va="center")
            ax.axis("off")
            continue

        x = sub["observation_distance_lambda_scale"].to_numpy(dtype=float)
        te_line = ax.plot(x, sub["R_TE_mag"].to_numpy(dtype=float), marker="o", linewidth=1.8, label="|R_TE|")
        tm_line = ax.plot(x, sub["R_TM_mag"].to_numpy(dtype=float), marker="s", linewidth=1.8, label="|R_TM|")
        ax.axhline(1.0, linestyle="--", color="0.35", linewidth=1.2, label="ideal PEC")
        ax.set_title(f"PEC theta = {theta_deg:.0f} deg")
        ax.set_xlabel("k_obs (lambda scale)")
        ax.set_ylabel("Magnitude")
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0.0)
        if handles is None:
            handles, labels = ax.get_legend_handles_labels()
        if len(x) == 1:
            ax.set_xlim(x[0] - 0.25, x[0] + 0.25)

    if handles and labels:
        figure.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.02), ncol=3, frameon=False)
    figure.suptitle("PEC reflection-magnitude convergence vs observation distance", y=0.97)
    figure.tight_layout(rect=[0.0, 0.06, 1.0, 0.94])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=220)
    plt.close(figure)


def main() -> None:
    args = parse_args()
    input_path = args.input.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Locked linear truth table not found: {input_path}")

    truth_df = pd.read_csv(input_path)
    comparison = build_comparison_table(truth_df, slab_thickness_m=float(args.slab_thickness_m))

    comparison_path = output_dir / "sanity_check_fresnel_comparison.csv"
    plot_path = output_dir / "pec_kobs_convergence.png"
    comparison.to_csv(comparison_path, index=False)
    plot_pec_kobs_convergence(truth_df, plot_path)

    print(f"Input truth table:      {input_path}")
    print(f"Comparison CSV:         {comparison_path}")
    print(f"PEC convergence plot:   {plot_path}")
    print(f"Rows analysed:          {len(comparison)}")
    print(
        "Material thicknesses:   "
        + ", ".join(f"{material}={thickness_m:.3f} m" for material, thickness_m in MATERIAL_THICKNESS_M.items())
    )
    print(f"Fallback thickness [m]: {float(args.slab_thickness_m):.6f}")
    print_row_table(comparison)
    print_summary(comparison)


if __name__ == "__main__":
    main()
