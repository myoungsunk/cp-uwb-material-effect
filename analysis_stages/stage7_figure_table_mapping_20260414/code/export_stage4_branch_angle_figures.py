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


def db20_ratio(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    den_safe = np.maximum(den.astype(float), 1e-12)
    num_safe = np.maximum(num.astype(float), 1e-12)
    return 20.0 * np.log10(num_safe / den_safe)


def mag_to_db(values: np.ndarray) -> np.ndarray:
    values_safe = np.maximum(values.astype(float), 1e-12)
    return 20.0 * np.log10(values_safe)


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export Stage 4 branch-angle comparison figures and CSVs."
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
    patch = pd.read_csv(args.patch_cp)

    ideal = ideal[ideal["material"].isin(MATERIALS)].copy()
    patch = patch[patch["material"].isin(MATERIALS)].copy()

    ideal_keep = ideal[
        ["material", "theta_deg", "Gamma_same_mag", "Gamma_flip_mag", "cp_use_for_main_claim"]
    ].copy()
    patch_keep = patch[
        [
            "material",
            "theta_deg",
            "gamma_hat_cross_agm_cp_mag",
            "gamma_hat_rr_raw_cp_mag",
            "gamma_hat_rr_leakage_corrected_cp_mag",
            "use_for_main_claim_candidate",
        ]
    ].copy()

    df = (
        ideal_keep.merge(patch_keep, on=["material", "theta_deg"], how="inner")
        .sort_values(["material", "theta_deg"])
        .reset_index(drop=True)
    )
    df = df[
        df.apply(
            lambda row: float(row["theta_deg"]) <= VALID_MAX[str(row["material"])], axis=1
        )
    ].copy()

    df["ideal_dom_res_ratio_db"] = db20_ratio(df["Gamma_flip_mag"].to_numpy(), df["Gamma_same_mag"].to_numpy())
    df["raw_dom_res_ratio_db"] = db20_ratio(
        df["gamma_hat_cross_agm_cp_mag"].to_numpy(), df["gamma_hat_rr_raw_cp_mag"].to_numpy()
    )
    df["eff_dom_res_ratio_db"] = db20_ratio(
        df["gamma_hat_cross_agm_cp_mag"].to_numpy(),
        df["gamma_hat_rr_leakage_corrected_cp_mag"].to_numpy(),
    )
    df["Gamma_same_db"] = mag_to_db(df["Gamma_same_mag"].to_numpy())
    df["gamma_hat_rr_raw_cp_db"] = mag_to_db(df["gamma_hat_rr_raw_cp_mag"].to_numpy())
    df["gamma_hat_rr_leakage_corrected_cp_db"] = mag_to_db(
        df["gamma_hat_rr_leakage_corrected_cp_mag"].to_numpy()
    )
    df["Gamma_flip_db"] = mag_to_db(df["Gamma_flip_mag"].to_numpy())
    df["gamma_hat_cross_agm_cp_db"] = mag_to_db(df["gamma_hat_cross_agm_cp_mag"].to_numpy())

    ratio_csv = csv_dir / "fig9_stage4_dominant_residual_ratio_vs_angle.csv"
    df[
        [
            "material",
            "theta_deg",
            "ideal_dom_res_ratio_db",
            "raw_dom_res_ratio_db",
            "eff_dom_res_ratio_db",
        ]
    ].to_csv(ratio_csv, index=False)

    residual_csv = csv_dir / "fig10_stage4_ideal_raw_eff_residual_vs_angle.csv"
    df[
        [
            "material",
            "theta_deg",
            "Gamma_same_mag",
            "Gamma_same_db",
            "gamma_hat_rr_raw_cp_mag",
            "gamma_hat_rr_raw_cp_db",
            "gamma_hat_rr_leakage_corrected_cp_mag",
            "gamma_hat_rr_leakage_corrected_cp_db",
        ]
    ].to_csv(residual_csv, index=False)

    dominant_csv = csv_dir / "fig11_stage4_ideal_cross_vs_angle.csv"
    df[
        [
            "material",
            "theta_deg",
            "Gamma_flip_mag",
            "Gamma_flip_db",
            "gamma_hat_cross_agm_cp_mag",
            "gamma_hat_cross_agm_cp_db",
        ]
    ].to_csv(dominant_csv, index=False)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
    fig.suptitle("Stage 4: Dominant / Residual Ratio vs Incident Angle", fontweight="bold")
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = df[df["material"] == material].copy()
        x = sub["theta_deg"].to_numpy(dtype=float)
        ax.plot(x, sub["ideal_dom_res_ratio_db"], "o-", color=MAT_COLORS[material], lw=1.8, label="Ideal")
        ax.plot(x, sub["raw_dom_res_ratio_db"], "s--", color="#111827", lw=1.6, label="Patch raw")
        ax.plot(x, sub["eff_dom_res_ratio_db"], "d:", color="#6b7280", lw=1.6, label="Patch corrected")
        ax.set_title(material.capitalize())
        ax.set_xlabel(r"$\theta_i$ [deg]")
        ax.grid(True, alpha=0.3)
        if idx == 0:
            ax.set_ylabel("Dominant / residual ratio [dB]")
            ax.legend(fontsize=7)
    fig.tight_layout()
    ratio_fig = output_dir / "fig9_stage4_dominant_residual_ratio_vs_angle.png"
    fig.savefig(ratio_fig, dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
    fig.suptitle("Stage 4: Ideal / Raw / Corrected Residual vs Incident Angle", fontweight="bold")
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = df[df["material"] == material].copy()
        x = sub["theta_deg"].to_numpy(dtype=float)
        ax.plot(x, sub["Gamma_same_db"], "o-", color=MAT_COLORS[material], lw=1.8, label=r"Ideal $20\log_{10}|\Gamma_{same}|$")
        ax.plot(x, sub["gamma_hat_rr_raw_cp_db"], "s--", color="#111827", lw=1.6, label=r"Patch $20\log_{10}|\hat{\gamma}_{rr,raw}^{CP}|$")
        ax.plot(
            x,
            sub["gamma_hat_rr_leakage_corrected_cp_db"],
            "d:",
            color="#6b7280",
            lw=1.6,
            label=r"Patch $20\log_{10}|\hat{\gamma}_{rr,leakage-corrected}^{CP}|$",
        )
        ax.set_title(material.capitalize())
        ax.set_xlabel(r"$\theta_i$ [deg]")
        ax.grid(True, alpha=0.3)
        if idx == 0:
            ax.set_ylabel("Magnitude [dB]")
            ax.legend(fontsize=7)
    fig.tight_layout()
    residual_fig = output_dir / "fig10_stage4_ideal_raw_eff_residual_vs_angle.png"
    fig.savefig(residual_fig, dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
    fig.suptitle("Stage 4: Ideal Dominant vs Patch Cross Dominant", fontweight="bold")
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = df[df["material"] == material].copy()
        x = sub["theta_deg"].to_numpy(dtype=float)
        ax.plot(x, sub["Gamma_flip_db"], "o-", color=MAT_COLORS[material], lw=1.8, label=r"Ideal $20\log_{10}|\Gamma_{flip}|$")
        ax.plot(
            x,
            sub["gamma_hat_cross_agm_cp_db"],
            "s--",
            color="#111827",
            lw=1.6,
            label=r"Patch $20\log_{10}|\hat{\gamma}_{cross,agm}^{CP}|$",
        )
        ax.set_title(material.capitalize())
        ax.set_xlabel(r"$\theta_i$ [deg]")
        ax.grid(True, alpha=0.3)
        if idx == 0:
            ax.set_ylabel("Magnitude [dB]")
            ax.legend(fontsize=7)
    fig.tight_layout()
    dominant_fig = output_dir / "fig11_stage4_ideal_cross_vs_angle.png"
    fig.savefig(dominant_fig, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote {ratio_csv}")
    print(f"Wrote {residual_csv}")
    print(f"Wrote {dominant_csv}")
    print(f"Wrote {ratio_fig}")
    print(f"Wrote {residual_fig}")
    print(f"Wrote {dominant_fig}")


if __name__ == "__main__":
    main()
