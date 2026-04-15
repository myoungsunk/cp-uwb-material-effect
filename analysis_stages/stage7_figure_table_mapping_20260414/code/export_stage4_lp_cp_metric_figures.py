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
REPORT_MIN_DEG = 20.0
MAT_COLORS = {"concrete": "#dc2626", "glass": "#2563eb", "wood": "#059669"}


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return False
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y"}


def db20_ratio(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    num_safe = np.maximum(num.astype(float), 1e-12)
    den_safe = np.maximum(den.astype(float), 1e-12)
    return 20.0 * np.log10(num_safe / den_safe)


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export Stage 4 LP-vs-CP suppression/ratio comparison figures and CSVs."
    )
    repo_root = Path(__file__).resolve().parents[3]
    parser.add_argument(
        "--linear-truth",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "paper_code_review_bundle_20260414"
        / "data"
        / "stage_1"
        / "truth_table_linear_locked.csv",
    )
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

    linear = pd.read_csv(args.linear_truth)
    ideal = pd.read_csv(args.ideal_cp_truth)
    patch_cp = pd.read_csv(args.patch_cp)
    patch_lp = pd.read_csv(args.patch_lp)

    linear["use_for_main_claim_TE"] = linear["use_for_main_claim_TE"].map(parse_bool)
    linear["use_for_main_claim_TM"] = linear["use_for_main_claim_TM"].map(parse_bool)
    ideal["cp_use_for_main_claim"] = ideal["cp_use_for_main_claim"].map(parse_bool)
    patch_cp["use_for_main_claim_candidate"] = patch_cp["use_for_main_claim_candidate"].map(parse_bool)
    patch_lp["use_for_main_claim_candidate"] = patch_lp["use_for_main_claim_candidate"].map(parse_bool)

    linear = linear[linear["material"].isin(MATERIALS)].copy()
    ideal = ideal[ideal["material"].isin(MATERIALS)].copy()
    patch_cp = patch_cp[patch_cp["material"].isin(MATERIALS)].copy()
    patch_lp = patch_lp[patch_lp["material"].isin(MATERIALS)].copy()

    linear_keep = linear[
        [
            "material",
            "theta_deg",
            "R_TE_mag",
            "R_TM_mag",
            "use_for_main_claim_TE",
            "use_for_main_claim_TM",
        ]
    ].copy()
    linear_keep["B_mag"] = linear_keep[["R_TE_mag", "R_TM_mag"]].max(axis=1)

    ideal_keep = ideal[
        [
            "material",
            "theta_deg",
            "Gamma_same_mag",
            "Gamma_flip_mag",
            "cp_use_for_main_claim",
        ]
    ].copy()

    cp_keep = patch_cp[
        [
            "material",
            "theta_deg",
            "gamma_hat_cross_agm_cp_mag",
            "gamma_hat_rr_raw_cp_mag",
            "gamma_hat_rr_leakage_corrected_cp_mag",
            "use_for_main_claim_candidate",
        ]
    ].copy().rename(columns={"use_for_main_claim_candidate": "cp_use_for_main_claim_candidate"})

    lp_keep = patch_lp[
        [
            "material",
            "theta_deg",
            "gamma_x_from_lp_mag",
            "gamma_c_from_lp_mag",
            "use_for_main_claim_candidate",
        ]
    ].copy().rename(columns={"use_for_main_claim_candidate": "lp_use_for_main_claim_candidate"})

    df = (
        linear_keep.merge(ideal_keep, on=["material", "theta_deg"], how="inner")
        .merge(cp_keep, on=["material", "theta_deg"], how="inner")
        .merge(lp_keep, on=["material", "theta_deg"], how="inner")
        .sort_values(["material", "theta_deg"])
        .reset_index(drop=True)
    )

    df["use_for_report"] = (
        df["use_for_main_claim_TE"]
        & df["use_for_main_claim_TM"]
        & df["cp_use_for_main_claim"]
        & df["cp_use_for_main_claim_candidate"]
        & df["lp_use_for_main_claim_candidate"]
        & (df["theta_deg"] >= REPORT_MIN_DEG)
        & df.apply(lambda row: float(row["theta_deg"]) <= VALID_MAX[str(row["material"])], axis=1)
    )
    df = df[df["use_for_report"]].copy()

    df["G_ideal_db"] = db20_ratio(df["B_mag"].to_numpy(), df["Gamma_same_mag"].to_numpy())
    df["G_lp_raw_db"] = db20_ratio(df["B_mag"].to_numpy(), df["gamma_x_from_lp_mag"].to_numpy())
    df["G_cp_raw_db"] = db20_ratio(df["B_mag"].to_numpy(), df["gamma_hat_rr_raw_cp_mag"].to_numpy())
    df["G_cp_corr_db"] = db20_ratio(
        df["B_mag"].to_numpy(),
        df["gamma_hat_rr_leakage_corrected_cp_mag"].to_numpy(),
    )

    df["ideal_dom_res_ratio_db"] = db20_ratio(
        df["Gamma_flip_mag"].to_numpy(),
        df["Gamma_same_mag"].to_numpy(),
    )
    df["lp_dom_res_ratio_db"] = db20_ratio(
        df["gamma_c_from_lp_mag"].to_numpy(),
        df["gamma_x_from_lp_mag"].to_numpy(),
    )
    df["cp_raw_dom_res_ratio_db"] = db20_ratio(
        df["gamma_hat_cross_agm_cp_mag"].to_numpy(),
        df["gamma_hat_rr_raw_cp_mag"].to_numpy(),
    )
    df["cp_corr_dom_res_ratio_db"] = db20_ratio(
        df["gamma_hat_cross_agm_cp_mag"].to_numpy(),
        df["gamma_hat_rr_leakage_corrected_cp_mag"].to_numpy(),
    )

    suppress_csv = csv_dir / "fig16_stage4_suppression_gain_ideal_lp_cp_raw_eff_vs_angle.csv"
    df[
        [
            "material",
            "theta_deg",
            "B_mag",
            "Gamma_same_mag",
            "gamma_x_from_lp_mag",
            "gamma_hat_rr_raw_cp_mag",
            "gamma_hat_rr_leakage_corrected_cp_mag",
            "G_ideal_db",
            "G_lp_raw_db",
            "G_cp_raw_db",
            "G_cp_corr_db",
        ]
    ].to_csv(suppress_csv, index=False)

    ratio_csv = csv_dir / "fig17_stage4_ratio_ideal_lp_cp_raw_eff_vs_angle.csv"
    df[
        [
            "material",
            "theta_deg",
            "ideal_dom_res_ratio_db",
            "lp_dom_res_ratio_db",
            "cp_raw_dom_res_ratio_db",
            "cp_corr_dom_res_ratio_db",
        ]
    ].to_csv(ratio_csv, index=False)

    summary_rows = []
    for material in MATERIALS:
        sub = df[df["material"] == material].copy()
        summary_rows.append(
            {
                "material": material,
                "theta_min_deg": float(sub["theta_deg"].min()),
                "theta_max_deg": float(sub["theta_deg"].max()),
                "n_rows": int(len(sub)),
                "mean_G_ideal_db": float(sub["G_ideal_db"].mean()),
                "mean_G_lp_raw_db": float(sub["G_lp_raw_db"].mean()),
                "mean_G_cp_raw_db": float(sub["G_cp_raw_db"].mean()),
                "mean_G_cp_corr_db": float(sub["G_cp_corr_db"].mean()),
                "mean_lp_minus_cp_raw_G_db": float((sub["G_lp_raw_db"] - sub["G_cp_raw_db"]).mean()),
                "mean_cp_corr_minus_lp_G_db": float((sub["G_cp_corr_db"] - sub["G_lp_raw_db"]).mean()),
                "cp_raw_below_lp_G_rows": int((sub["G_cp_raw_db"] < sub["G_lp_raw_db"]).sum()),
                "cp_corr_above_lp_G_rows": int((sub["G_cp_corr_db"] > sub["G_lp_raw_db"]).sum()),
                "mean_ratio_ideal_db": float(sub["ideal_dom_res_ratio_db"].mean()),
                "mean_ratio_lp_db": float(sub["lp_dom_res_ratio_db"].mean()),
                "mean_ratio_cp_raw_db": float(sub["cp_raw_dom_res_ratio_db"].mean()),
                "mean_ratio_cp_corr_db": float(sub["cp_corr_dom_res_ratio_db"].mean()),
                "mean_lp_minus_cp_raw_ratio_db": float(
                    (sub["lp_dom_res_ratio_db"] - sub["cp_raw_dom_res_ratio_db"]).mean()
                ),
                "mean_cp_corr_minus_lp_ratio_db": float(
                    (sub["cp_corr_dom_res_ratio_db"] - sub["lp_dom_res_ratio_db"]).mean()
                ),
                "cp_raw_below_lp_ratio_rows": int(
                    (sub["cp_raw_dom_res_ratio_db"] < sub["lp_dom_res_ratio_db"]).sum()
                ),
                "cp_corr_above_lp_ratio_rows": int(
                    (sub["cp_corr_dom_res_ratio_db"] > sub["lp_dom_res_ratio_db"]).sum()
                ),
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    summary_csv = csv_dir / "stage4_lp_cp_metric_summary.csv"
    summary_df.to_csv(summary_csv, index=False)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
    fig.suptitle("Stage 4: Suppression Gain Comparison", fontweight="bold")
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = df[df["material"] == material].copy()
        x = sub["theta_deg"].to_numpy(dtype=float)
        ax.plot(x, sub["G_ideal_db"], "o-", color=MAT_COLORS[material], lw=1.8, label="Ideal")
        ax.plot(x, sub["G_lp_raw_db"], "s--", color="#111827", lw=1.6, label="LP raw")
        ax.plot(x, sub["G_cp_raw_db"], "d:", color="#6b7280", lw=1.8, label="CP raw")
        ax.plot(x, sub["G_cp_corr_db"], "^-.", color="#9ca3af", lw=1.5, label="CP corrected")
        ax.set_title(material.capitalize())
        ax.set_xlabel(r"$\theta_i$ [deg]")
        ax.grid(True, alpha=0.3)
        if idx == 0:
            ax.set_ylabel("Suppression gain [dB]")
            ax.legend(fontsize=7)
    fig.tight_layout()
    suppress_fig = output_dir / "fig16_stage4_suppression_gain_ideal_lp_cp_raw_eff_vs_angle.png"
    fig.savefig(suppress_fig, dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
    fig.suptitle("Stage 4: Dominant-to-Residual Ratio Comparison", fontweight="bold")
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
            label="Ideal",
        )
        ax.plot(x, sub["lp_dom_res_ratio_db"], "s--", color="#111827", lw=1.6, label="LP raw")
        ax.plot(
            x,
            sub["cp_raw_dom_res_ratio_db"],
            "d:",
            color="#6b7280",
            lw=1.8,
            label="CP raw",
        )
        ax.plot(
            x,
            sub["cp_corr_dom_res_ratio_db"],
            "^-.",
            color="#9ca3af",
            lw=1.5,
            label="CP corrected",
        )
        ax.set_title(material.capitalize())
        ax.set_xlabel(r"$\theta_i$ [deg]")
        ax.grid(True, alpha=0.3)
        if idx == 0:
            ax.set_ylabel("Dominant / residual ratio [dB]")
            ax.legend(fontsize=7)
    fig.tight_layout()
    ratio_fig = output_dir / "fig17_stage4_ratio_ideal_lp_cp_raw_eff_vs_angle.png"
    fig.savefig(ratio_fig, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote {suppress_csv}")
    print(f"Wrote {ratio_csv}")
    print(f"Wrote {summary_csv}")
    print(f"Wrote {suppress_fig}")
    print(f"Wrote {ratio_fig}")


if __name__ == "__main__":
    main()
