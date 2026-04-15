from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import pandas as pd
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


MATERIALS = ["concrete", "glass", "wood"]
MAT_COLORS = {"concrete": "#dc2626", "glass": "#2563eb", "wood": "#059669"}
VALID_MAX = {"concrete": 55.0, "glass": 60.0, "wood": 45.0}


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export Stage 4 raw/correction/eff anglewise comparison figure and CSV."
    )
    repo_root = Path(__file__).resolve().parents[3]
    parser.add_argument(
        "--patch-cp-freq",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "stage3_patch_paper_final_20260414"
        / "cp"
        / "results"
        / "patch_cp_extracted_freq_resolved.csv",
    )
    parser.add_argument(
        "--stage4f-full",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "paper_code_review_bundle_20260414"
        / "code"
        / "stage4f_raw_primary_dual_20260414"
        / "results_aliasfree_20260415"
        / "stage4f_raw_primary_full.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root / "paper_final_analysis_sequence" / "figures",
    )
    parser.add_argument(
        "--csv-dir",
        type=Path,
        default=repo_root / "paper_final_analysis_sequence" / "figures" / "csv",
    )
    return parser


def main() -> None:
    args = build_argparser().parse_args()
    patch_cp_freq = args.patch_cp_freq.resolve()
    stage4f_full = args.stage4f_full.resolve()
    output_dir = args.output_dir.resolve()
    csv_dir = args.csv_dir.resolve()

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_dir.mkdir(parents=True, exist_ok=True)

    freq_df = pd.read_csv(patch_cp_freq)
    freq_df = freq_df[freq_df["material"].isin(MATERIALS)].copy()
    freq_df = freq_df[
        freq_df.apply(
            lambda row: float(row["theta_deg"]) >= 20.0
            and float(row["theta_deg"]) <= VALID_MAX[str(row["material"])],
            axis=1,
        )
    ].copy()

    gamma_raw = (
        freq_df["gamma_hat_rr_raw_cp_real"].to_numpy(dtype=float)
        + 1j * freq_df["gamma_hat_rr_raw_cp_imag"].to_numpy(dtype=float)
    )
    gamma_eff = (
        freq_df["gamma_hat_rr_leakage_corrected_cp_real"].to_numpy(dtype=float)
        + 1j * freq_df["gamma_hat_rr_leakage_corrected_cp_imag"].to_numpy(dtype=float)
    )
    correction = gamma_raw - gamma_eff
    phase_diff = np.rad2deg(np.angle(correction) - np.angle(gamma_raw))
    phase_diff = (phase_diff + 180.0) % 360.0 - 180.0

    freq_df["_gamma_raw"] = gamma_raw
    freq_df["_gamma_eff"] = gamma_eff
    freq_df["_correction"] = correction
    freq_df["_rho"] = np.abs(correction) / np.maximum(np.abs(gamma_raw), 1e-12)
    freq_df["_phase_diff_deg"] = phase_diff
    freq_df["_predicted_overcorrection_point"] = (
        (freq_df["_rho"] >= 1.0) & (np.abs(freq_df["_phase_diff_deg"]) <= 15.0)
    )

    angle_df = (
        freq_df.groupby(["material", "theta_deg"], sort=True)
        .agg(
            gamma_hat_rr_raw_cp_mag_mean=("_gamma_raw", lambda s: float(np.mean(np.abs(np.asarray(s, dtype=complex))))),
            correction_term_mag_mean=("_correction", lambda s: float(np.mean(np.abs(np.asarray(s, dtype=complex))))),
            gamma_hat_rr_leakage_corrected_cp_mag_mean=("_gamma_eff", lambda s: float(np.mean(np.abs(np.asarray(s, dtype=complex))))),
            correction_to_raw_ratio=("_rho", "mean"),
            phase_diff_raw_vs_correction_deg=("_phase_diff_deg", "median"),
            predicted_overcorrection_region=("_predicted_overcorrection_point", "mean"),
        )
        .reset_index()
    )
    angle_df["predicted_overcorrection_region"] = (
        angle_df["predicted_overcorrection_region"] >= 0.5
    )

    stage4f = pd.read_csv(stage4f_full)
    stage4f = stage4f[
        ["material", "theta_deg", "Delta_ideal_minus_eff_db", "delta_eff_negative"]
    ].copy()
    stage4f["delta_eff_negative"] = stage4f["delta_eff_negative"].astype(bool)

    export_df = (
        angle_df.merge(stage4f, on=["material", "theta_deg"], how="left")
        .sort_values(["material", "theta_deg"])
        .reset_index(drop=True)
    )

    csv_path = csv_dir / "fig8_stage4_three_component_vs_angle.csv"
    export_df.to_csv(csv_path, index=False)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
    fig.suptitle("Stage 4: Raw / Correction / Corrected vs Incident Angle", fontweight="bold")

    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = export_df[export_df["material"] == material].copy()
        x = sub["theta_deg"].to_numpy(dtype=float)
        raw = sub["gamma_hat_rr_raw_cp_mag_mean"].to_numpy(dtype=float)
        corr = sub["correction_term_mag_mean"].to_numpy(dtype=float)
        eff = sub["gamma_hat_rr_leakage_corrected_cp_mag_mean"].to_numpy(dtype=float)
        neg = sub[sub["delta_eff_negative"].astype(bool)]

        ax.plot(
            x,
            raw,
            "o-",
            color=MAT_COLORS[material],
            lw=1.8,
            label=r"$|\hat{\gamma}_{rr,raw}^{CP}|$",
        )
        ax.plot(
            x,
            corr,
            "s--",
            color="#111827",
            lw=1.5,
            label=r"$|\epsilon_{M3}\hat{\gamma}_{cross,agm}^{CP}|$",
        )
        ax.plot(
            x,
            eff,
            "d:",
            color="#6b7280",
            lw=1.8,
            label=r"$|\hat{\gamma}_{rr,leakage-corrected}^{CP}|$",
        )

        if not neg.empty:
            ax.scatter(
                neg["theta_deg"].to_numpy(dtype=float),
                neg["gamma_hat_rr_leakage_corrected_cp_mag_mean"].to_numpy(dtype=float),
                marker="x",
                color="#b91c1c",
                s=42,
                label="eff negative-gap row" if idx == 0 else None,
            )

        ax.set_title(material.capitalize())
        ax.set_xlabel(r"$\theta_i$ [deg]")
        ax.grid(True, alpha=0.3)
        if idx == 0:
            ax.set_ylabel("Band-mean magnitude")
            ax.legend(fontsize=7)

    fig.tight_layout()
    fig_path = output_dir / "fig8_stage4_three_component_vs_angle.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote {csv_path}")
    print(f"Wrote {fig_path}")


if __name__ == "__main__":
    main()
