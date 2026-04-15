# Consolidated review copy for paper-pipeline code assessment.
# Stage: 4
# Role: Initial dual-metric suppression-gain builder before convention lock.
# Source: analysis_stages/stage4_suppression_dual_20260414/code/build_suppression_gain_dual.py
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


def db20_ratio(num: float, den: float) -> float:
    return float(20.0 * np.log10(max(num, 1e-12) / max(den, 1e-12)))


def pick_small_branch(
    mag_a: float, label_a: str, mag_b: float, label_b: str
) -> tuple[float, str, float, str]:
    if mag_a <= mag_b:
        return mag_a, label_a, mag_b, label_b
    return mag_b, label_b, mag_a, label_a


def ideal_branch_mag_cols(df: pd.DataFrame) -> tuple[str, str]:
    if {"Gamma_same_mag", "Gamma_flip_mag"}.issubset(df.columns):
        return "Gamma_same_mag", "Gamma_flip_mag"
    return "Gamma_X_mag", "Gamma_C_mag"


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Stage 4 dual suppression gain tables in an isolated workspace."
    )
    bundle_root = Path(__file__).resolve().parent.parent
    workspace_root = Path(__file__).resolve().parents[3]
    parser.add_argument(
        "--linear-truth",
        type=Path,
        default=bundle_root
        / "data"
        / "stage_1"
        / "truth_table_linear_locked.csv",
    )
    parser.add_argument(
        "--cp-truth",
        type=Path,
        default=bundle_root
        / "data"
        / "stage_2"
        / "sameflip_alias_20260415"
        / "truth_table_cp_shared_common_sameflip.csv",
    )
    parser.add_argument(
        "--patch-cp",
        type=Path,
        default=workspace_root
        / "analysis_stages"
        / "stage3_patch_paper_final_20260414"
        / "cp"
        / "results"
        / "patch_cp_extracted.csv",
    )
    parser.add_argument(
        "--patch-lp",
        type=Path,
        default=workspace_root
        / "analysis_stages"
        / "stage3_patch_paper_final_20260414"
        / "lp"
        / "results"
        / "patch_lp_extracted.csv",
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
    patch_cp = pd.read_csv(args.patch_cp)
    patch_lp = pd.read_csv(args.patch_lp)

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

    same_col, flip_col = ideal_branch_mag_cols(cp)
    cp_keep = cp[
        [
            "material",
            "theta_deg",
            same_col,
            flip_col,
            "cp_use_for_main_claim",
        ]
    ].copy().rename(columns={same_col: "ideal_same_mag", flip_col: "ideal_flip_mag"})

    patch_cp_keep = patch_cp[
        [
            "material",
            "theta_deg",
            "gamma_hat_x_cp_sys_mag",
            "gamma_hat_c_cp_eff_mag",
            "xpd_eff_db",
            "reciprocity_dev_db",
            "leakage_lr_rr_db",
            "leakage_rl_ll_db",
            "port_asym_db",
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

    records: list[dict] = []
    for row in merged.to_dict(orient="records"):
        ideal_small_mag, ideal_small_label, ideal_large_mag, ideal_large_label = pick_small_branch(
            row["ideal_same_mag"], "ideal_same_mag", row["ideal_flip_mag"], "ideal_flip_mag"
        )
        patch_small_mag, patch_small_label, patch_large_mag, patch_large_label = pick_small_branch(
            row["gamma_hat_x_cp_sys_mag"],
            "gamma_hat_x_cp_sys_mag",
            row["gamma_hat_c_cp_eff_mag"],
            "gamma_hat_c_cp_eff_mag",
        )

        row["ideal_small_branch_mag"] = ideal_small_mag
        row["ideal_small_branch_label"] = ideal_small_label
        row["ideal_large_branch_mag"] = ideal_large_mag
        row["ideal_large_branch_label"] = ideal_large_label
        row["patch_small_branch_mag"] = patch_small_mag
        row["patch_small_branch_label"] = patch_small_label
        row["patch_large_branch_mag"] = patch_large_mag
        row["patch_large_branch_label"] = patch_large_label

        row["G_ideal_from_gamma_x_db"] = db20_ratio(row["B_mag"], row["ideal_same_mag"])
        row["G_ideal_from_gamma_c_db"] = db20_ratio(row["B_mag"], row["ideal_flip_mag"])
        row["G_patch_from_gamma_hat_x_db"] = db20_ratio(
            row["B_mag"], row["gamma_hat_x_cp_sys_mag"]
        )
        row["G_patch_from_gamma_hat_c_eff_db"] = db20_ratio(
            row["B_mag"], row["gamma_hat_c_cp_eff_mag"]
        )

        row["G_supp_ideal_db"] = db20_ratio(row["B_mag"], ideal_small_mag)
        row["G_supp_patch_db"] = db20_ratio(row["B_mag"], patch_small_mag)
        row["Delta_G_db"] = row["G_supp_ideal_db"] - row["G_supp_patch_db"]

        row["use_for_main_claim"] = bool(
            row["use_for_main_claim_TE"]
            and row["use_for_main_claim_TM"]
            and row["cp_use_for_main_claim"]
            and row["use_for_main_claim_candidate"]
            and row["lp_use_for_main_claim_candidate"]
            and row["theta_deg"] <= VALID_MAX[row["material"]]
        )

        if row["use_for_main_claim"]:
            row["stage4_note"] = "Main-claim row retained after ideal and patch joins."
        else:
            row["stage4_note"] = "Audit row outside final Stage 4 main-claim filter."
        records.append(row)

    full_df = pd.DataFrame(records)
    main_df = full_df[full_df["use_for_main_claim"]].copy().reset_index(drop=True)

    summary_rows = []
    for material in MATERIALS:
        sub = main_df[main_df["material"] == material].copy()
        peak_ideal_idx = sub["G_supp_ideal_db"].idxmax()
        peak_patch_idx = sub["G_supp_patch_db"].idxmax()
        peak_gap_idx = sub["Delta_G_db"].idxmax()
        summary_rows.append(
            {
                "material": material,
                "valid_theta_min_deg": float(sub["theta_deg"].min()),
                "valid_theta_max_deg": float(sub["theta_deg"].max()),
                "n_rows": int(len(sub)),
                "peak_G_supp_ideal_db": float(sub.loc[peak_ideal_idx, "G_supp_ideal_db"]),
                "peak_G_supp_ideal_theta_deg": float(sub.loc[peak_ideal_idx, "theta_deg"]),
                "peak_G_supp_patch_db": float(sub.loc[peak_patch_idx, "G_supp_patch_db"]),
                "peak_G_supp_patch_theta_deg": float(sub.loc[peak_patch_idx, "theta_deg"]),
                "peak_Delta_G_db": float(sub.loc[peak_gap_idx, "Delta_G_db"]),
                "peak_Delta_G_theta_deg": float(sub.loc[peak_gap_idx, "theta_deg"]),
                "worst_lp_leakage_max_db": float(sub["leakage_max_db"].max()),
                "ideal_small_branch_label": sub["ideal_small_branch_label"].mode().iloc[0],
                "patch_small_branch_label": sub["patch_small_branch_label"].mode().iloc[0],
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    summary_lines = [
        (
            f"- {row['material']}: range={row['valid_theta_min_deg']:.0f}-{row['valid_theta_max_deg']:.0f} deg, "
            f"n={int(row['n_rows'])}, "
            f"peak G_ideal={row['peak_G_supp_ideal_db']:.2f} dB @ {row['peak_G_supp_ideal_theta_deg']:.0f} deg, "
            f"peak G_patch={row['peak_G_supp_patch_db']:.2f} dB @ {row['peak_G_supp_patch_theta_deg']:.0f} deg, "
            f"peak Delta_G={row['peak_Delta_G_db']:.2f} dB @ {row['peak_Delta_G_theta_deg']:.0f} deg, "
            f"worst LP leakage={row['worst_lp_leakage_max_db']:.2f} dB, "
            f"ideal small={row['ideal_small_branch_label']}, patch small={row['patch_small_branch_label']}"
        )
        for _, row in summary_df.iterrows()
    ]

    full_path = output_dir / "suppression_gain_dual_full.csv"
    main_path = output_dir / "suppression_gain_dual.csv"
    table1_path = output_dir / "suppression_gain_table1.csv"

    full_df.to_csv(full_path, index=False)
    main_df.to_csv(main_path, index=False)
    summary_df.to_csv(table1_path, index=False)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    fig.suptitle("Stage 4 Dual Suppression Gain", fontweight="bold")
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
    fig_path = output_dir / "fig4_headline_suppression_dual.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    branch_audit = main_df.groupby(["material", "ideal_small_branch_label", "patch_small_branch_label"]).size()
    branch_audit_text = "\n".join(
        f"- {material}: ideal small={ideal_label}, patch small={patch_label}, rows={count}"
        for (material, ideal_label, patch_label), count in branch_audit.items()
    )

    summary_md = output_dir / "STAGE4_SUMMARY.md"
    summary_md.write_text(
        "\n".join(
            [
                "# Stage 4 Summary",
                "",
                "Execution date: `2026-04-14`",
                "",
                "This stage was executed in the isolated workspace:",
                "",
                "- `analysis_stages/stage4_suppression_dual_20260414`",
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
                "## Branch Mapping Used For Final Gain",
                "",
                "The headline suppression gain is computed from the smaller CP branch at each row.",
                "This is an inference from the locked data because the symbol naming in the ideal and",
                "patch stages is not numerically aligned.",
                "",
                branch_audit_text,
                "",
                "## Material Summary",
                "",
                *summary_lines,
                "",
                "## Notes",
                "",
                "- Audit columns using the raw label-based branches are also included in the CSV.",
                "- `G_supp_ideal_db` and `G_supp_patch_db` are the small-branch residual metrics used for the headline figure.",
                "- LP leakage diagnostics are attached row-wise for methods/supporting checks.",
            ]
        ),
        encoding="utf-8",
    )

    print(f"Wrote {full_path}")
    print(f"Wrote {main_path}")
    print(f"Wrote {table1_path}")
    print(f"Wrote {fig_path}")
    print(f"Wrote {summary_md}")
    print(f"Main rows: {len(main_df)}")


if __name__ == "__main__":
    main()
