from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


MATERIALS = ["concrete", "glass", "wood"]
VALID_MAX = {"concrete": 55.0, "glass": 60.0, "wood": 45.0}
MAT_COLORS = {"concrete": "#dc2626", "glass": "#2563eb", "wood": "#059669"}


def mag_to_db(values: np.ndarray) -> np.ndarray:
    values_safe = np.maximum(values.astype(float), 1e-12)
    return 20.0 * np.log10(values_safe)


def db20_ratio(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    num_safe = np.maximum(num.astype(float), 1e-12)
    den_safe = np.maximum(den.astype(float), 1e-12)
    return 20.0 * np.log10(num_safe / den_safe)


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export LP-vs-CP / ideal Stage 4 comparison figures and CSVs."
    )
    repo_root = Path(__file__).resolve().parents[3]
    parser.add_argument(
        "--ideal-cp-truth",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "paper_code_review_bundle_20260414"
        / "data"
        / "stage_2"
        / "sameflip_alias_20260415"
        / "truth_table_cp_shared_common_sameflip.csv",
    )
    parser.add_argument(
        "--patch-cp",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "stage3_patch_paper_final_20260414"
        / "cp"
        / "results"
        / "patch_cp_extracted.csv",
    )
    parser.add_argument(
        "--patch-lp",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "stage3_patch_paper_final_20260414"
        / "lp"
        / "results"
        / "patch_lp_extracted.csv",
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
    output_dir = args.output_dir.resolve()
    csv_dir = args.csv_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_dir.mkdir(parents=True, exist_ok=True)

    ideal = pd.read_csv(args.ideal_cp_truth)
    patch_cp = pd.read_csv(args.patch_cp)
    patch_lp = pd.read_csv(args.patch_lp)

    ideal = ideal[ideal["material"].isin(MATERIALS)].copy()
    patch_cp = patch_cp[patch_cp["material"].isin(MATERIALS)].copy()
    patch_lp = patch_lp[patch_lp["material"].isin(MATERIALS)].copy()

    ideal_keep = ideal[
        ["material", "theta_deg", "Gamma_same_mag", "Gamma_flip_mag"]
    ].copy()
    cp_keep = patch_cp[
        [
            "material",
            "theta_deg",
            "gamma_hat_rr_raw_cp_mag",
            "gamma_hat_cross_agm_cp_mag",
        ]
    ].copy()
    lp_keep = patch_lp[
        [
            "material",
            "theta_deg",
            "gamma_x_from_lp_mag",
            "gamma_c_from_lp_mag",
        ]
    ].copy()

    df = (
        ideal_keep.merge(cp_keep, on=["material", "theta_deg"], how="inner")
        .merge(lp_keep, on=["material", "theta_deg"], how="inner")
        .sort_values(["material", "theta_deg"])
        .reset_index(drop=True)
    )
    df = df[
        df.apply(
            lambda row: float(row["theta_deg"]) <= VALID_MAX[str(row["material"])], axis=1
        )
    ].copy()

    df["Gamma_same_db"] = mag_to_db(df["Gamma_same_mag"].to_numpy())
    df["Gamma_flip_db"] = mag_to_db(df["Gamma_flip_mag"].to_numpy())
    df["gamma_hat_rr_raw_cp_db"] = mag_to_db(df["gamma_hat_rr_raw_cp_mag"].to_numpy())
    df["gamma_hat_cross_agm_cp_db"] = mag_to_db(
        df["gamma_hat_cross_agm_cp_mag"].to_numpy()
    )
    df["gamma_x_from_lp_db"] = mag_to_db(df["gamma_x_from_lp_mag"].to_numpy())
    df["gamma_c_from_lp_db"] = mag_to_db(df["gamma_c_from_lp_mag"].to_numpy())
    df["ideal_dom_res_ratio_db"] = db20_ratio(
        df["Gamma_flip_mag"].to_numpy(),
        df["Gamma_same_mag"].to_numpy(),
    )
    df["lp_dom_res_ratio_db"] = db20_ratio(
        df["gamma_c_from_lp_mag"].to_numpy(),
        df["gamma_x_from_lp_mag"].to_numpy(),
    )
    df["cp_dom_res_ratio_db"] = db20_ratio(
        df["gamma_hat_cross_agm_cp_mag"].to_numpy(),
        df["gamma_hat_rr_raw_cp_mag"].to_numpy(),
    )

    residual_csv = csv_dir / "fig12_stage4_ideal_lp_raw_residual_vs_angle.csv"
    df[
        [
            "material",
            "theta_deg",
            "Gamma_same_mag",
            "Gamma_same_db",
            "gamma_x_from_lp_mag",
            "gamma_x_from_lp_db",
            "gamma_hat_rr_raw_cp_mag",
            "gamma_hat_rr_raw_cp_db",
        ]
    ].to_csv(residual_csv, index=False)

    dominant_csv = csv_dir / "fig13_stage4_ideal_lp_dominant_vs_angle.csv"
    df[
        [
            "material",
            "theta_deg",
            "Gamma_flip_mag",
            "Gamma_flip_db",
            "gamma_c_from_lp_mag",
            "gamma_c_from_lp_db",
            "gamma_hat_cross_agm_cp_mag",
            "gamma_hat_cross_agm_cp_db",
        ]
    ].to_csv(dominant_csv, index=False)

    ratio_csv = csv_dir / "fig14_stage4_ideal_lp_dominant_residual_ratio_vs_angle.csv"
    df[
        [
            "material",
            "theta_deg",
            "ideal_dom_res_ratio_db",
            "lp_dom_res_ratio_db",
        ]
    ].to_csv(ratio_csv, index=False)

    combined_ratio_csv = csv_dir / "fig15_stage4_ideal_lp_cp_dominant_residual_ratio_vs_angle.csv"
    df[
        [
            "material",
            "theta_deg",
            "ideal_dom_res_ratio_db",
            "lp_dom_res_ratio_db",
            "cp_dom_res_ratio_db",
        ]
    ].to_csv(combined_ratio_csv, index=False)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
    fig.suptitle(
        "Stage 4: Ideal / LP / CP Raw Residual Comparison",
        fontweight="bold",
    )
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = df[df["material"] == material].copy()
        x = sub["theta_deg"].to_numpy(dtype=float)
        ax.plot(
            x,
            sub["Gamma_same_db"],
            "o-",
            color=MAT_COLORS[material],
            lw=1.8,
            label=r"Ideal $20\log_{10}|\Gamma_{same}|$",
        )
        ax.plot(
            x,
            sub["gamma_x_from_lp_db"],
            "s--",
            color="#111827",
            lw=1.6,
            label=r"LP residual $20\log_{10}|\hat{\gamma}_{x}^{LP}|$",
        )
        ax.plot(
            x,
            sub["gamma_hat_rr_raw_cp_db"],
            "d:",
            color="#6b7280",
            lw=1.8,
            label=r"CP raw $20\log_{10}|\hat{\gamma}_{rr,raw}^{CP}|$",
        )
        ax.set_title(material.capitalize())
        ax.set_xlabel(r"$\theta_i$ [deg]")
        ax.grid(True, alpha=0.3)
        if idx == 0:
            ax.set_ylabel("Magnitude [dB]")
            ax.legend(fontsize=7)
    fig.tight_layout()
    residual_fig = output_dir / "fig12_stage4_ideal_lp_raw_residual_vs_angle.png"
    fig.savefig(residual_fig, dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
    fig.suptitle(
        "Stage 4: Ideal / LP Dominant Comparison",
        fontweight="bold",
    )
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = df[df["material"] == material].copy()
        x = sub["theta_deg"].to_numpy(dtype=float)
        ax.plot(
            x,
            sub["Gamma_flip_db"],
            "o-",
            color=MAT_COLORS[material],
            lw=1.8,
            label=r"Ideal $20\log_{10}|\Gamma_{flip}|$",
        )
        ax.plot(
            x,
            sub["gamma_c_from_lp_db"],
            "s--",
            color="#111827",
            lw=1.6,
            label=r"LP dominant $20\log_{10}|\hat{\gamma}_{c}^{LP}|$",
        )
        ax.set_title(material.capitalize())
        ax.set_xlabel(r"$\theta_i$ [deg]")
        ax.grid(True, alpha=0.3)
        if idx == 0:
            ax.set_ylabel("Magnitude [dB]")
            ax.legend(fontsize=7)
    fig.tight_layout()
    dominant_fig = output_dir / "fig13_stage4_ideal_lp_dominant_vs_angle.png"
    fig.savefig(dominant_fig, dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
    fig.suptitle(
        "Stage 4: Ideal / LP Dominant-to-Residual Ratio",
        fontweight="bold",
    )
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = df[df["material"] == material].copy()
        x = sub["theta_deg"].to_numpy(dtype=float)
        ax.plot(
            x,
            sub["ideal_dom_res_ratio_db"],
            "o-",
            color=MAT_COLORS[material],
            lw=1.8,
            label="Ideal ratio",
        )
        ax.plot(
            x,
            sub["lp_dom_res_ratio_db"],
            "s--",
            color="#111827",
            lw=1.6,
            label="LP ratio",
        )
        ax.set_title(material.capitalize())
        ax.set_xlabel(r"$\theta_i$ [deg]")
        ax.grid(True, alpha=0.3)
        if idx == 0:
            ax.set_ylabel("Dominant / residual ratio [dB]")
            ax.legend(fontsize=7)
    fig.tight_layout()
    ratio_fig = output_dir / "fig14_stage4_ideal_lp_dominant_residual_ratio_vs_angle.png"
    fig.savefig(ratio_fig, dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
    fig.suptitle(
        "Stage 4: Ideal / LP / CP Dominant-to-Residual Ratio",
        fontweight="bold",
    )
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = df[df["material"] == material].copy()
        x = sub["theta_deg"].to_numpy(dtype=float)
        ax.plot(
            x,
            sub["ideal_dom_res_ratio_db"],
            "o-",
            color=MAT_COLORS[material],
            lw=1.8,
            label="Ideal ratio",
        )
        ax.plot(
            x,
            sub["lp_dom_res_ratio_db"],
            "s--",
            color="#111827",
            lw=1.6,
            label="LP ratio",
        )
        ax.plot(
            x,
            sub["cp_dom_res_ratio_db"],
            "d:",
            color="#6b7280",
            lw=1.8,
            label="CP raw ratio",
        )
        ax.set_title(material.capitalize())
        ax.set_xlabel(r"$\theta_i$ [deg]")
        ax.grid(True, alpha=0.3)
        if idx == 0:
            ax.set_ylabel("Dominant / residual ratio [dB]")
            ax.legend(fontsize=7)
    fig.tight_layout()
    combined_ratio_fig = output_dir / "fig15_stage4_ideal_lp_cp_dominant_residual_ratio_vs_angle.png"
    fig.savefig(combined_ratio_fig, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote {residual_csv}")
    print(f"Wrote {dominant_csv}")
    print(f"Wrote {ratio_csv}")
    print(f"Wrote {combined_ratio_csv}")
    print(f"Wrote {residual_fig}")
    print(f"Wrote {dominant_fig}")
    print(f"Wrote {ratio_fig}")
    print(f"Wrote {combined_ratio_fig}")


if __name__ == "__main__":
    main()
