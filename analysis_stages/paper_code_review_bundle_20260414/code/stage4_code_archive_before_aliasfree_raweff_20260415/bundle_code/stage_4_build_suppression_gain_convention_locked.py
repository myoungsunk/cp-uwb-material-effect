# Consolidated review copy for paper-pipeline code assessment.
# Stage: 4
# Role: Convention-locked suppression-gain builder after branch naming was fixed.
# Source: analysis_stages/stage4b_convention_locked_20260414/code/build_suppression_gain_convention_locked.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


VALID_MAX = {"concrete": 55.0, "glass": 60.0, "wood": 45.0}
MATERIALS = ["concrete", "glass", "wood"]
MAT_COLORS = {"concrete": "#dc2626", "glass": "#2563eb", "wood": "#059669"}


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "t", "yes", "y"}


def db20_ratio(num: float, den: float) -> float:
    return float(20.0 * np.log10(max(num, 1e-12) / max(den, 1e-12)))


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Stage 4b suppression gain tables with convention-locked CP branches."
    )
    repo_root = Path(__file__).resolve().parents[3]
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
        "--patch-cp-aliased",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "lp_anchor_branch_lock_20260414"
        / "results"
        / "patch_cp_extracted_with_lp_anchor_alias.csv",
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
        "--theta-min-deg",
        type=float,
        default=20.0,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
    )
    return parser


def main() -> None:
    args = build_argparser().parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[3]

    linear = pd.read_csv(args.linear_truth)
    cp = pd.read_csv(args.cp_truth)
    patch_cp = pd.read_csv(args.patch_cp_aliased)
    patch_lp = pd.read_csv(args.patch_lp)

    cp["cp_use_for_main_claim"] = cp["cp_use_for_main_claim"].map(parse_bool)
    patch_cp["use_for_main_claim_candidate"] = patch_cp["use_for_main_claim_candidate"].map(
        parse_bool
    )
    patch_lp["use_for_main_claim_candidate"] = patch_lp["use_for_main_claim_candidate"].map(
        parse_bool
    )
    linear["use_for_main_claim_TE"] = linear["use_for_main_claim_TE"].map(parse_bool)
    linear["use_for_main_claim_TM"] = linear["use_for_main_claim_TM"].map(parse_bool)

    linear = linear[linear["material"].isin(MATERIALS)].copy()
    cp = cp[cp["material"].isin(MATERIALS)].copy()
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

    cp_keep = cp[
        [
            "material",
            "theta_deg",
            "Gamma_X_mag",
            "Gamma_C_mag",
            "cp_use_for_main_claim",
        ]
    ].copy()

    patch_cp_keep = patch_cp[
        [
            "material",
            "theta_deg",
            "cp_residual_branch_name",
            "cp_dominant_branch_name",
            "cp_residual_branch_mag",
            "cp_dominant_branch_mag",
            "xpd_eff_db",
            "reciprocity_dev_db",
            "leakage_lr_rr_db",
            "leakage_rl_ll_db",
            "port_asym_db",
            "branch_lock_method",
            "use_for_main_claim_candidate",
        ]
    ].copy()

    patch_lp_keep = patch_lp[
        [
            "material",
            "theta_deg",
            "r_hat_yy_sys_mag",
            "r_hat_zz_sys_mag",
            "gamma_x_from_lp_mag",
            "gamma_c_from_lp_mag",
            "leakage_yz_db",
            "leakage_zy_db",
            "leakage_max_db",
            "use_for_main_claim_candidate",
        ]
    ].copy()
    patch_lp_keep = patch_lp_keep.rename(
        columns={"use_for_main_claim_candidate": "lp_use_for_main_claim_candidate"}
    )

    merged = (
        linear_keep.merge(cp_keep, on=["material", "theta_deg"], how="inner")
        .merge(patch_cp_keep, on=["material", "theta_deg"], how="inner")
        .merge(patch_lp_keep, on=["material", "theta_deg"], how="inner")
        .sort_values(["material", "theta_deg"])
        .reset_index(drop=True)
    )

    merged["ideal_residual_branch_name"] = "Gamma_X"
    merged["ideal_dominant_branch_name"] = "Gamma_C"
    merged["ideal_residual_branch_mag"] = merged["Gamma_X_mag"]
    merged["ideal_dominant_branch_mag"] = merged["Gamma_C_mag"]

    merged["G_supp_ideal_db"] = merged.apply(
        lambda row: db20_ratio(row["B_mag"], row["ideal_residual_branch_mag"]), axis=1
    )
    merged["G_supp_patch_db"] = merged.apply(
        lambda row: db20_ratio(row["B_mag"], row["cp_residual_branch_mag"]), axis=1
    )
    merged["Delta_G_db"] = merged["G_supp_ideal_db"] - merged["G_supp_patch_db"]

    merged["use_for_main_claim"] = (
        merged["use_for_main_claim_TE"]
        & merged["use_for_main_claim_TM"]
        & merged["cp_use_for_main_claim"]
        & merged["use_for_main_claim_candidate"]
        & merged["lp_use_for_main_claim_candidate"]
        & (merged["theta_deg"] >= float(args.theta_min_deg))
        & merged.apply(lambda row: row["theta_deg"] <= VALID_MAX[row["material"]], axis=1)
    )

    merged["stage4b_note"] = np.where(
        merged["use_for_main_claim"],
        "Main-claim row retained after LP-anchored branch lock and oblique-range filter.",
        "Audit row outside Stage 4b main-claim filter.",
    )

    full_df = merged.copy()
    main_df = merged[merged["use_for_main_claim"]].copy().reset_index(drop=True)

    summary_rows = []
    for material in MATERIALS:
        sub = main_df[main_df["material"] == material].copy()
        peak_ideal_idx = sub["G_supp_ideal_db"].idxmax()
        peak_patch_idx = sub["G_supp_patch_db"].idxmax()
        peak_gap_idx = sub["Delta_G_db"].idxmax()
        summary_rows.append(
            {
                "material": material,
                "reporting_theta_min_deg": float(sub["theta_deg"].min()),
                "reporting_theta_max_deg": float(sub["theta_deg"].max()),
                "n_rows": int(len(sub)),
                "peak_G_supp_ideal_db": float(sub.loc[peak_ideal_idx, "G_supp_ideal_db"]),
                "peak_G_supp_ideal_theta_deg": float(sub.loc[peak_ideal_idx, "theta_deg"]),
                "peak_G_supp_patch_db": float(sub.loc[peak_patch_idx, "G_supp_patch_db"]),
                "peak_G_supp_patch_theta_deg": float(sub.loc[peak_patch_idx, "theta_deg"]),
                "peak_Delta_G_db": float(sub.loc[peak_gap_idx, "Delta_G_db"]),
                "peak_Delta_G_theta_deg": float(sub.loc[peak_gap_idx, "theta_deg"]),
                "worst_lp_leakage_max_db": float(sub["leakage_max_db"].max()),
                "ideal_residual_branch_name": "Gamma_X",
                "patch_residual_branch_name": sub["cp_residual_branch_name"].mode().iloc[0],
                "branch_lock_method": sub["branch_lock_method"].mode().iloc[0],
            }
        )

    summary_df = pd.DataFrame(summary_rows)

    full_path = output_dir / "suppression_gain_stage4b_full.csv"
    main_path = output_dir / "suppression_gain_stage4b.csv"
    table1_path = output_dir / "suppression_gain_stage4b_table1.csv"

    full_df.to_csv(full_path, index=False)
    main_df.to_csv(main_path, index=False)
    summary_df.to_csv(table1_path, index=False)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    fig.suptitle("Stage 4b Convention-Locked Suppression Gain", fontweight="bold")
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = main_df[main_df["material"] == material].sort_values("theta_deg")
        x = sub["theta_deg"].to_numpy(dtype=float)
        y_ideal = sub["G_supp_ideal_db"].to_numpy(dtype=float)
        y_patch = sub["G_supp_patch_db"].to_numpy(dtype=float)
        ax.plot(x, y_ideal, "o-", color=MAT_COLORS[material], lw=1.8, label="Ideal upper bound")
        ax.plot(x, y_patch, "s--", color="#111827", lw=1.5, label="Patch achievable")
        ax.fill_between(x, y_patch, y_ideal, color=MAT_COLORS[material], alpha=0.16, label="Gap")
        ax.set_title(material.capitalize())
        ax.set_xlabel(r"$\theta_i$ [deg]")
        ax.grid(True, alpha=0.3)
        if idx == 0:
            ax.set_ylabel("Suppression gain [dB]")
            ax.legend(fontsize=8)
    fig.tight_layout()
    fig_path = output_dir / "fig4b_headline_suppression_locked.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    summary_lines = [
        (
            f"- {row['material']}: range={row['reporting_theta_min_deg']:.0f}-{row['reporting_theta_max_deg']:.0f} deg, "
            f"n={int(row['n_rows'])}, "
            f"peak G_ideal={row['peak_G_supp_ideal_db']:.2f} dB @ {row['peak_G_supp_ideal_theta_deg']:.0f} deg, "
            f"peak G_patch={row['peak_G_supp_patch_db']:.2f} dB @ {row['peak_G_supp_patch_theta_deg']:.0f} deg, "
            f"peak Delta_G={row['peak_Delta_G_db']:.2f} dB @ {row['peak_Delta_G_theta_deg']:.0f} deg, "
            f"worst LP leakage={row['worst_lp_leakage_max_db']:.2f} dB"
        )
        for _, row in summary_df.iterrows()
    ]

    summary_md = output_dir / "STAGE4B_SUMMARY.md"
    summary_md.write_text(
        "\n".join(
            [
                "# Stage 4b Summary",
                "",
                "Execution date: `2026-04-14`",
                "",
                "This stage was executed in the isolated workspace:",
                "",
                "- `analysis_stages/stage4b_convention_locked_20260414`",
                "",
                "The original Stage 4a workspace is preserved as:",
                "",
                "- `analysis_stages/stage4_suppression_dual_20260414`",
                "",
                "## Main-Claim Lock",
                "",
                "- ideal residual branch: `Gamma_X`",
                "- patch residual branch: `cp_residual_branch`",
                "- branch lock source: `lp_anchor_branch_lock_20260414`",
                f"- headline reporting lower bound: `{float(args.theta_min_deg):.0f} deg`",
                "",
                "## Outputs",
                "",
                f"- Full audit table: `{full_path.relative_to(repo_root)}`",
                f"- Main claim table: `{main_path.relative_to(repo_root)}`",
                f"- Table I summary: `{table1_path.relative_to(repo_root)}`",
                f"- Headline figure: `{fig_path.relative_to(repo_root)}`",
                "",
                "## Row Counts",
                "",
                f"- Full audit rows: `{len(full_df)}`",
                f"- Main-claim rows: `{len(main_df)}`",
                "",
                "## Material Summary",
                "",
                *summary_lines,
                "",
                "## Notes",
                "",
                "- Stage 4b removes the small-angle peak inflation by restricting the headline range to oblique incidence.",
                "- The raw label-based branches remain available in the Stage 4a audit trail.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print("Wrote Stage 4b convention-locked suppression outputs.")


if __name__ == "__main__":
    main()
