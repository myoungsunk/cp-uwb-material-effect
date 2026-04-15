from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


MATERIALS = ["concrete", "glass", "wood"]
MATERIAL_LABELS = {"concrete": "Concrete", "glass": "Glass", "wood": "Wood"}
MATERIAL_COLORS = {"concrete": "#b91c1c", "glass": "#1d4ed8", "wood": "#047857"}
BRANCH_COLORS = {"TE": "#ea580c", "TM": "#2563eb"}
PRACTICAL_COLORS = {"ideal": "#111827", "lp": "#0f766e", "cp_raw": "#7c2d12"}


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export manuscript-ready CSVs and plots for paper Figures 1 to 4."
    )
    repo_root = Path(__file__).resolve().parents[3]
    default_stage_dir = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--linear-truth",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "ideal_te_tm_scattered_stage"
        / "results"
        / "current_manifest_runs"
        / "material_5000mm_kobs5_phase0_nominal_rerun_20260414"
        / "truth_table_linear_locked.csv",
    )
    parser.add_argument(
        "--cp-truth",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "ideal_te_tm_scattered_stage"
        / "results"
        / "current_manifest_runs"
        / "material_5000mm_kobs5_phase0_nominal_rerun_20260414"
        / "truth_table_cp_recomputed_20260414.csv",
    )
    parser.add_argument(
        "--fresnel-check",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "ideal_te_tm_scattered_stage"
        / "results"
        / "current_manifest_runs"
        / "material_5000mm_kobs5_phase0_nominal_rerun_20260414"
        / "sanity_check"
        / "sanity_check_fresnel_comparison.csv",
    )
    parser.add_argument(
        "--lp-anchor-main",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "lp_anchor_branch_lock_20260414"
        / "results"
        / "lp_anchor_branch_lock_main.csv",
    )
    parser.add_argument(
        "--patch-cp-alias",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "lp_anchor_branch_lock_20260414"
        / "results"
        / "patch_cp_extracted_with_lp_anchor_alias.csv",
    )
    parser.add_argument(
        "--stage4f-full",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "stage4f_raw_primary_dual_20260414"
        / "results"
        / "stage4f_raw_primary_full.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_stage_dir / "results",
    )
    parser.add_argument(
        "--truth-min-deg",
        type=float,
        default=10.0,
        help="Minimum angle used in the Stage 1 truth figure export.",
    )
    parser.add_argument(
        "--oblique-min-deg",
        type=float,
        default=20.0,
        help="Minimum angle used in Figures 2 to 4.",
    )
    return parser


def normalize_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    lowered = series.astype(str).str.strip().str.lower()
    return lowered.isin({"true", "1", "yes"})


def mag_to_db(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    safe = np.maximum(arr, 1e-12)
    return 20.0 * np.log10(safe)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def export_fig1(
    linear_truth: pd.DataFrame,
    fresnel_check: pd.DataFrame,
    csv_dir: Path,
    fig_dir: Path,
    truth_min_deg: float,
) -> Path:
    merged = linear_truth.merge(
        fresnel_check[
            [
                "material",
                "theta_deg",
                "R_TE_mag_theory",
                "R_TM_mag_theory",
                "overall_TE_status",
                "overall_TM_status",
            ]
        ],
        on=["material", "theta_deg"],
        how="left",
    )
    merged = merged[
        (merged["material"].isin(MATERIALS)) & (merged["theta_deg"].astype(float) >= truth_min_deg)
    ].copy()
    merged["use_for_main_claim"] = normalize_bool(merged["use_for_main_claim"])
    merged["use_for_main_claim_TE"] = normalize_bool(merged["use_for_main_claim_TE"])
    merged["use_for_main_claim_TM"] = normalize_bool(merged["use_for_main_claim_TM"])

    records: list[dict[str, object]] = []
    for branch in ("TE", "TM"):
        hfss_col = f"R_{branch}_locked_mag"
        theory_col = f"R_{branch}_mag_theory"
        branch_flag_col = f"use_for_main_claim_{branch}"
        status_col = f"overall_{branch}_status"
        for _, row in merged.iterrows():
            records.append(
                {
                    "material": row["material"],
                    "theta_deg": float(row["theta_deg"]),
                    "branch": branch,
                    "source": "HFSS",
                    "magnitude": float(row[hfss_col]),
                    "magnitude_db": float(mag_to_db([row[hfss_col]])[0]),
                    "branch_use_for_main_claim": bool(row[branch_flag_col]),
                    "shared_use_for_main_claim": bool(row["use_for_main_claim"]),
                    "comparison_status": row.get(status_col, ""),
                }
            )
            records.append(
                {
                    "material": row["material"],
                    "theta_deg": float(row["theta_deg"]),
                    "branch": branch,
                    "source": "Fresnel",
                    "magnitude": float(row[theory_col]),
                    "magnitude_db": float(mag_to_db([row[theory_col]])[0]),
                    "branch_use_for_main_claim": bool(row[branch_flag_col]),
                    "shared_use_for_main_claim": bool(row["use_for_main_claim"]),
                    "comparison_status": row.get(status_col, ""),
                }
            )

    fig1_df = pd.DataFrame(records).sort_values(["material", "branch", "source", "theta_deg"]).reset_index(drop=True)
    fig1_csv = csv_dir / "fig1_linear_truth_vs_fresnel.csv"
    fig1_df.to_csv(fig1_csv, index=False)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = fig1_df[
            (fig1_df["material"] == material) & (fig1_df["branch_use_for_main_claim"])
        ].copy()
        for branch in ("TE", "TM"):
            for source, linestyle, alpha in (("HFSS", "-", 1.0), ("Fresnel", "--", 0.85)):
                curve = sub[(sub["branch"] == branch) & (sub["source"] == source)].sort_values("theta_deg")
                ax.plot(
                    curve["theta_deg"],
                    curve["magnitude"],
                    linestyle=linestyle,
                    marker="o" if source == "HFSS" else None,
                    linewidth=1.8,
                    color=BRANCH_COLORS[branch],
                    alpha=alpha,
                    label=f"{branch} {source}" if idx == 0 else None,
                )
        ax.set_title(MATERIAL_LABELS[material])
        ax.set_xlabel("Incident angle [deg]")
        ax.grid(True, alpha=0.25)
        if idx == 0:
            ax.set_ylabel("Reflection magnitude")
            ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig1_linear_truth_vs_fresnel.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    return fig1_csv


def export_fig2(
    cp_truth: pd.DataFrame,
    csv_dir: Path,
    fig_dir: Path,
    oblique_min_deg: float,
) -> Path:
    cp = cp_truth[(cp_truth["material"].isin(MATERIALS))].copy()
    cp["cp_use_for_main_claim"] = normalize_bool(cp["cp_use_for_main_claim"])
    cp = cp[
        cp["cp_use_for_main_claim"] & (cp["theta_deg"].astype(float) >= oblique_min_deg)
    ].copy()
    cp["Gamma_X_db"] = mag_to_db(cp["Gamma_X_mag"])
    cp["Gamma_C_db"] = mag_to_db(cp["Gamma_C_mag"])
    cp["xpd_residual_over_dominant_db"] = mag_to_db(cp["Gamma_X_mag"] / cp["Gamma_C_mag"])
    cp["xpd_dominant_over_residual_db"] = mag_to_db(cp["Gamma_C_mag"] / cp["Gamma_X_mag"])

    fig2_df = cp[
        [
            "material",
            "theta_deg",
            "Gamma_X_mag",
            "Gamma_C_mag",
            "Gamma_X_db",
            "Gamma_C_db",
            "xpd_residual_over_dominant_db",
            "xpd_dominant_over_residual_db",
            "cp_use_for_main_claim",
            "cp_truth_region",
        ]
    ].sort_values(["material", "theta_deg"])
    fig2_csv = csv_dir / "fig2_ideal_cp_oblique.csv"
    fig2_df.to_csv(fig2_csv, index=False)

    fig, axes = plt.subplots(2, 3, figsize=(15, 7), sharex="col")
    for idx, material in enumerate(MATERIALS):
        sub = fig2_df[fig2_df["material"] == material].sort_values("theta_deg")
        ax_top = axes[0, idx]
        ax_bot = axes[1, idx]

        ax_top.plot(sub["theta_deg"], sub["Gamma_X_mag"], "o-", color="#b45309", lw=1.8, label="Residual")
        ax_top.plot(sub["theta_deg"], sub["Gamma_C_mag"], "s-", color="#1d4ed8", lw=1.8, label="Dominant")
        ax_top.set_title(MATERIAL_LABELS[material])
        ax_top.grid(True, alpha=0.25)
        if idx == 0:
            ax_top.set_ylabel("Magnitude")
            ax_top.legend(fontsize=8)

        ax_bot.plot(
            sub["theta_deg"],
            sub["xpd_dominant_over_residual_db"],
            "o-",
            color=MATERIAL_COLORS[material],
            lw=1.8,
        )
        ax_bot.grid(True, alpha=0.25)
        ax_bot.set_xlabel("Incident angle [deg]")
        if idx == 0:
            ax_bot.set_ylabel("Dominant / residual [dB]")

    fig.tight_layout()
    fig.savefig(fig_dir / "fig2_ideal_cp_oblique.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    return fig2_csv


def export_fig3(
    cp_truth: pd.DataFrame,
    lp_anchor_main: pd.DataFrame,
    patch_cp_alias: pd.DataFrame,
    csv_dir: Path,
    fig_dir: Path,
    oblique_min_deg: float,
) -> Path:
    ideal = cp_truth[["material", "theta_deg", "Gamma_X_mag"]].copy()
    lp = lp_anchor_main[
        ["material", "theta_deg", "gamma_x_from_lp_mag", "use_for_main_claim"]
    ].copy()
    patch = patch_cp_alias[
        ["material", "theta_deg", "gamma_hat_c_cp_raw_mag", "use_for_main_claim_candidate"]
    ].copy()

    lp["use_for_main_claim"] = normalize_bool(lp["use_for_main_claim"])
    patch["use_for_main_claim_candidate"] = normalize_bool(patch["use_for_main_claim_candidate"])

    fig3_df = (
        ideal.merge(lp, on=["material", "theta_deg"], how="inner")
        .merge(patch, on=["material", "theta_deg"], how="inner")
        .sort_values(["material", "theta_deg"])
        .reset_index(drop=True)
    )
    fig3_df = fig3_df[
        fig3_df["material"].isin(MATERIALS)
        & fig3_df["use_for_main_claim"]
        & fig3_df["use_for_main_claim_candidate"]
        & (fig3_df["theta_deg"].astype(float) >= oblique_min_deg)
    ].copy()
    fig3_df["ideal_residual_db"] = mag_to_db(fig3_df["Gamma_X_mag"])
    fig3_df["lp_residual_db"] = mag_to_db(fig3_df["gamma_x_from_lp_mag"])
    fig3_df["cp_raw_residual_db"] = mag_to_db(fig3_df["gamma_hat_c_cp_raw_mag"])

    fig3_csv = csv_dir / "fig3_practical_branch_overlay.csv"
    fig3_df.to_csv(fig3_csv, index=False)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = fig3_df[fig3_df["material"] == material].sort_values("theta_deg")
        ax.plot(sub["theta_deg"], sub["ideal_residual_db"], "o-", color=PRACTICAL_COLORS["ideal"], lw=1.8, label="Ideal")
        ax.plot(sub["theta_deg"], sub["lp_residual_db"], "s--", color=PRACTICAL_COLORS["lp"], lw=1.8, label="LP-derived")
        ax.plot(sub["theta_deg"], sub["cp_raw_residual_db"], "d-.", color=PRACTICAL_COLORS["cp_raw"], lw=1.8, label="CP raw")
        ax.set_title(MATERIAL_LABELS[material])
        ax.set_xlabel("Incident angle [deg]")
        ax.grid(True, alpha=0.25)
        if idx == 0:
            ax.set_ylabel("Residual magnitude [dB]")
            ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig3_practical_branch_overlay.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    return fig3_csv


def export_fig4_and_table1(
    lp_anchor_main: pd.DataFrame,
    stage4f_full: pd.DataFrame,
    csv_dir: Path,
    fig_dir: Path,
) -> tuple[Path, Path]:
    lp = lp_anchor_main[["material", "theta_deg", "gamma_x_from_lp_mag", "use_for_main_claim"]].copy()
    lp["use_for_main_claim"] = normalize_bool(lp["use_for_main_claim"])

    raw = stage4f_full.copy()
    raw["headline_use_primary"] = normalize_bool(raw["headline_use_primary"])

    fig4_df = (
        raw.merge(lp, on=["material", "theta_deg"], how="inner")
        .sort_values(["material", "theta_deg"])
        .reset_index(drop=True)
    )
    fig4_df = fig4_df[
        fig4_df["material"].isin(MATERIALS) & fig4_df["headline_use_primary"] & fig4_df["use_for_main_claim"]
    ].copy()
    fig4_df["G_lp_db"] = mag_to_db(fig4_df["B_mag"] / fig4_df["gamma_x_from_lp_mag"])
    fig4_df["Delta_ideal_minus_lp_db"] = fig4_df["G_ideal_db"] - fig4_df["G_lp_db"]

    fig4_csv = csv_dir / "fig4_headline_suppression.csv"
    fig4_df[
        [
            "material",
            "theta_deg",
            "B_mag",
            "gamma_x_ideal_mag",
            "gamma_x_from_lp_mag",
            "gamma_c_patch_raw_mag",
            "G_ideal_db",
            "G_lp_db",
            "G_patch_raw_db",
            "Delta_ideal_minus_lp_db",
            "Delta_ideal_minus_raw_db",
        ]
    ].to_csv(fig4_csv, index=False)

    table1_rows = []
    for material in MATERIALS:
        sub = fig4_df[fig4_df["material"] == material].sort_values("theta_deg")
        table1_rows.append(
            {
                "material": material,
                "range_deg": f"{int(sub['theta_deg'].min())}-{int(sub['theta_deg'].max())}",
                "mean_G_ideal_db": float(sub["G_ideal_db"].mean()),
                "mean_G_lp_db": float(sub["G_lp_db"].mean()),
                "mean_G_cp_raw_db": float(sub["G_patch_raw_db"].mean()),
                "mean_Delta_ideal_minus_lp_db": float(sub["Delta_ideal_minus_lp_db"].mean()),
                "mean_Delta_ideal_minus_raw_db": float(sub["Delta_ideal_minus_raw_db"].mean()),
            }
        )
    table1_df = pd.DataFrame(table1_rows)
    table1_csv = csv_dir / "table1_maintext_means.csv"
    table1_df.to_csv(table1_csv, index=False)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = fig4_df[fig4_df["material"] == material].sort_values("theta_deg")
        ax.plot(sub["theta_deg"], sub["G_ideal_db"], "o-", color=PRACTICAL_COLORS["ideal"], lw=1.8, label="Ideal")
        ax.plot(sub["theta_deg"], sub["G_lp_db"], "s--", color=PRACTICAL_COLORS["lp"], lw=1.8, label="LP-derived")
        ax.plot(sub["theta_deg"], sub["G_patch_raw_db"], "d-.", color=PRACTICAL_COLORS["cp_raw"], lw=1.8, label="CP raw")
        ax.fill_between(
            sub["theta_deg"],
            sub["G_patch_raw_db"],
            sub["G_ideal_db"],
            color=MATERIAL_COLORS[material],
            alpha=0.12,
            label="Ideal-raw gap" if idx == 0 else None,
        )
        ax.set_title(MATERIAL_LABELS[material])
        ax.set_xlabel("Incident angle [deg]")
        ax.grid(True, alpha=0.25)
        if idx == 0:
            ax.set_ylabel("Suppression gain [dB]")
            ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig4_headline_suppression.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    return fig4_csv, table1_csv


def write_summary(
    repo_root: Path,
    output_dir: Path,
    csv_paths: list[Path],
    fig_paths: list[Path],
    table1_csv: Path,
) -> None:
    summary_path = output_dir / "STAGE7_FIGURE_EXPORT_SUMMARY.md"
    lines = [
        "# Stage 7 Figure Export Summary",
        "",
        "Execution date: `2026-04-14`",
        "",
        "This export layer organizes manuscript-facing CSVs and plotting outputs",
        "for Figures 1 to 4.",
        "",
        "## Reporting Lock",
        "",
        "- Fig. 1 uses the Stage 1 HFSS truth with Fresnel overlay.",
        "- Fig. 2 is restricted to the oblique ideal CP branch view.",
        "- Fig. 3 compares ideal, LP-derived, and CP raw residual branches.",
        "- Fig. 4 and Table I use `ideal`, `LP-derived`, and `CP raw` only.",
        "- `eff` and PEC-based CP corrections remain supplement-only.",
        "",
        "## CSV Outputs",
        "",
    ]
    for path in csv_paths:
        lines.append(f"- `{path.relative_to(repo_root)}`")
    lines.extend(
        [
            "",
            "## Figure Outputs",
            "",
        ]
    )
    for path in fig_paths:
        lines.append(f"- `{path.relative_to(repo_root)}`")
    lines.extend(
        [
            "",
            "## Main-Text Table",
            "",
            f"- `{table1_csv.relative_to(repo_root)}`",
        ]
    )
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_argparser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]

    output_dir = ensure_dir(args.output_dir.resolve())
    csv_dir = ensure_dir(output_dir / "csv")
    fig_dir = ensure_dir(output_dir / "figures")

    linear_truth = pd.read_csv(args.linear_truth)
    cp_truth = pd.read_csv(args.cp_truth)
    fresnel_check = pd.read_csv(args.fresnel_check)
    lp_anchor_main = pd.read_csv(args.lp_anchor_main)
    patch_cp_alias = pd.read_csv(args.patch_cp_alias)
    stage4f_full = pd.read_csv(args.stage4f_full)

    fig1_csv = export_fig1(linear_truth, fresnel_check, csv_dir, fig_dir, args.truth_min_deg)
    fig2_csv = export_fig2(cp_truth, csv_dir, fig_dir, args.oblique_min_deg)
    fig3_csv = export_fig3(cp_truth, lp_anchor_main, patch_cp_alias, csv_dir, fig_dir, args.oblique_min_deg)
    fig4_csv, table1_csv = export_fig4_and_table1(lp_anchor_main, stage4f_full, csv_dir, fig_dir)

    fig_paths = [
        fig_dir / "fig1_linear_truth_vs_fresnel.png",
        fig_dir / "fig2_ideal_cp_oblique.png",
        fig_dir / "fig3_practical_branch_overlay.png",
        fig_dir / "fig4_headline_suppression.png",
    ]
    write_summary(repo_root, output_dir, [fig1_csv, fig2_csv, fig3_csv, fig4_csv], fig_paths, table1_csv)

    print("Wrote Stage 7 paper figure CSV and plot exports.")


if __name__ == "__main__":
    main()
