from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


MATERIALS = ["concrete", "glass", "wood"]


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build raw/eff/metal-floor 3-way comparison tables and figure-ready CSVs."
    )
    repo_root = Path(__file__).resolve().parents[3]
    parser.add_argument(
        "--stage4c-full",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "stage4c_same_angle_gap_audit_20260414"
        / "results"
        / "same_angle_gap_audit_full.csv",
    )
    parser.add_argument(
        "--stage4d-full",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "stage4d_cp_metal_floor_audit_20260414"
        / "results"
        / "metal_floor_same_angle_audit.csv",
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

    stage4c = pd.read_csv(args.stage4c_full)
    stage4d = pd.read_csv(args.stage4d_full)

    stage4c = stage4c[stage4c["material"].isin(MATERIALS)].copy()
    stage4d = stage4d[stage4d["material"].isin(MATERIALS)].copy()

    keep4c = stage4c[
        [
            "material",
            "theta_deg",
            "B_mag",
            "ideal_residual_branch_mag",
            "gamma_hat_c_cp_raw_mag",
            "gamma_hat_c_cp_eff_mag",
            "G_supp_ideal_db",
            "G_patch_raw_db",
            "G_supp_patch_db",
            "Delta_G_raw_db",
            "Delta_G_db",
            "Delta_G_raw_negative",
            "Delta_G_eff_negative",
            "raw_smaller_than_ideal",
            "eff_smaller_than_ideal",
            "raw_closer_to_ideal_than_eff",
        ]
    ].copy()
    keep4c = keep4c.rename(
        columns={
            "ideal_residual_branch_mag": "gamma_x_ideal_mag",
            "gamma_hat_c_cp_raw_mag": "gamma_c_patch_raw_mag",
            "gamma_hat_c_cp_eff_mag": "gamma_c_patch_eff_mag",
            "G_supp_ideal_db": "G_ideal_db",
            "G_patch_raw_db": "G_patch_raw_db",
            "G_supp_patch_db": "G_patch_eff_db",
            "Delta_G_raw_db": "Delta_ideal_minus_raw_db",
            "Delta_G_db": "Delta_ideal_minus_eff_db",
            "Delta_G_raw_negative": "delta_raw_negative",
            "Delta_G_eff_negative": "delta_eff_negative",
        }
    )

    keep4d = stage4d[
        [
            "material",
            "theta_deg",
            "gamma_hat_c_metal_floor_mag",
            "G_patch_metal_floor_db",
            "Delta_G_ideal_minus_metal_floor_db",
            "negative_delta_rows",
            "metal_floor_gt_ideal_residual",
        ]
    ].copy()
    keep4d = keep4d.rename(
        columns={
            "negative_delta_rows": "delta_metal_floor_negative",
        }
    )

    wide = (
        keep4c.merge(keep4d, on=["material", "theta_deg"], how="inner")
        .sort_values(["material", "theta_deg"])
        .reset_index(drop=True)
    )

    wide["delta_raw_sign"] = wide["Delta_ideal_minus_raw_db"].apply(lambda v: "negative" if v < 0 else "nonnegative")
    wide["delta_eff_sign"] = wide["Delta_ideal_minus_eff_db"].apply(lambda v: "negative" if v < 0 else "nonnegative")
    wide["delta_metal_floor_sign"] = wide["Delta_G_ideal_minus_metal_floor_db"].apply(
        lambda v: "negative" if v < 0 else "nonnegative"
    )

    wide_path = output_dir / "residual_3way_comparison_wide.csv"
    wide.to_csv(wide_path, index=False)

    summary_rows = []
    for material in MATERIALS + ["overall"]:
        sub = wide if material == "overall" else wide[wide["material"] == material]
        summary_rows.append(
            {
                "material": material,
                "n_rows": int(len(sub)),
                "range_theta_min_deg": float(sub["theta_deg"].min()),
                "range_theta_max_deg": float(sub["theta_deg"].max()),
                "mean_G_ideal_db": float(sub["G_ideal_db"].mean()),
                "mean_G_patch_raw_db": float(sub["G_patch_raw_db"].mean()),
                "mean_G_patch_eff_db": float(sub["G_patch_eff_db"].mean()),
                "mean_G_patch_metal_floor_db": float(sub["G_patch_metal_floor_db"].mean()),
                "mean_Delta_ideal_minus_raw_db": float(sub["Delta_ideal_minus_raw_db"].mean()),
                "mean_Delta_ideal_minus_eff_db": float(sub["Delta_ideal_minus_eff_db"].mean()),
                "mean_Delta_ideal_minus_metal_floor_db": float(sub["Delta_G_ideal_minus_metal_floor_db"].mean()),
                "negative_delta_raw_rows": int(sub["delta_raw_negative"].sum()),
                "negative_delta_eff_rows": int(sub["delta_eff_negative"].sum()),
                "negative_delta_metal_floor_rows": int(sub["delta_metal_floor_negative"].sum()),
                "raw_closer_to_ideal_than_eff_rows": int(sub["raw_closer_to_ideal_than_eff"].sum()),
                "eff_smaller_than_ideal_rows": int(sub["eff_smaller_than_ideal"].sum()),
                "metal_floor_gt_ideal_rows": int(sub["metal_floor_gt_ideal_residual"].sum()),
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    summary_path = output_dir / "residual_3way_summary_by_material.csv"
    summary_df.to_csv(summary_path, index=False)

    branch_long_rows = []
    for _, row in wide.iterrows():
        branch_long_rows.extend(
            [
                {
                    "material": row["material"],
                    "theta_deg": row["theta_deg"],
                    "series_id": "ideal_gamma_x",
                    "series_label": "Ideal residual (Gamma_X)",
                    "method_family": "ideal",
                    "normalization_scope": "absolute_interface_truth",
                    "directly_comparable_to_ideal": True,
                    "residual_mag": row["gamma_x_ideal_mag"],
                },
                {
                    "material": row["material"],
                    "theta_deg": row["theta_deg"],
                    "series_id": "patch_raw",
                    "series_label": "Patch residual raw",
                    "method_family": "patch_raw",
                    "normalization_scope": "patch_stage_absolute_like",
                    "directly_comparable_to_ideal": True,
                    "residual_mag": row["gamma_c_patch_raw_mag"],
                },
                {
                    "material": row["material"],
                    "theta_deg": row["theta_deg"],
                    "series_id": "patch_eff",
                    "series_label": "Patch residual corrected",
                    "method_family": "patch_eff",
                    "normalization_scope": "patch_stage_absolute_like",
                    "directly_comparable_to_ideal": True,
                    "residual_mag": row["gamma_c_patch_eff_mag"],
                },
                {
                    "material": row["material"],
                    "theta_deg": row["theta_deg"],
                    "series_id": "patch_metal_floor",
                    "series_label": "Patch residual metal-floor",
                    "method_family": "patch_metal_floor",
                    "normalization_scope": "metal_normalized_diagnostic",
                    "directly_comparable_to_ideal": False,
                    "residual_mag": row["gamma_hat_c_metal_floor_mag"],
                },
            ]
        )
    branch_long_df = pd.DataFrame(branch_long_rows)
    branch_long_path = output_dir / "residual_3way_branch_mag_long.csv"
    branch_long_df.to_csv(branch_long_path, index=False)

    supp_long_rows = []
    for _, row in wide.iterrows():
        supp_long_rows.extend(
            [
                {
                    "material": row["material"],
                    "theta_deg": row["theta_deg"],
                    "series_id": "ideal",
                    "series_label": "Ideal upper bound",
                    "method_family": "ideal",
                    "normalization_scope": "absolute_interface_truth",
                    "directly_comparable_to_ideal": True,
                    "G_supp_db": row["G_ideal_db"],
                    "delta_vs_ideal_db": 0.0,
                    "delta_negative": False,
                },
                {
                    "material": row["material"],
                    "theta_deg": row["theta_deg"],
                    "series_id": "patch_raw",
                    "series_label": "Patch raw",
                    "method_family": "patch_raw",
                    "normalization_scope": "patch_stage_absolute_like",
                    "directly_comparable_to_ideal": True,
                    "G_supp_db": row["G_patch_raw_db"],
                    "delta_vs_ideal_db": row["Delta_ideal_minus_raw_db"],
                    "delta_negative": bool(row["delta_raw_negative"]),
                },
                {
                    "material": row["material"],
                    "theta_deg": row["theta_deg"],
                    "series_id": "patch_eff",
                    "series_label": "Patch corrected",
                    "method_family": "patch_eff",
                    "normalization_scope": "patch_stage_absolute_like",
                    "directly_comparable_to_ideal": True,
                    "G_supp_db": row["G_patch_eff_db"],
                    "delta_vs_ideal_db": row["Delta_ideal_minus_eff_db"],
                    "delta_negative": bool(row["delta_eff_negative"]),
                },
                {
                    "material": row["material"],
                    "theta_deg": row["theta_deg"],
                    "series_id": "patch_metal_floor",
                    "series_label": "Patch metal-floor",
                    "method_family": "patch_metal_floor",
                    "normalization_scope": "metal_normalized_diagnostic",
                    "directly_comparable_to_ideal": False,
                    "G_supp_db": row["G_patch_metal_floor_db"],
                    "delta_vs_ideal_db": row["Delta_G_ideal_minus_metal_floor_db"],
                    "delta_negative": bool(row["delta_metal_floor_negative"]),
                },
            ]
        )
    supp_long_df = pd.DataFrame(supp_long_rows)
    supp_long_path = output_dir / "residual_3way_suppression_long.csv"
    supp_long_df.to_csv(supp_long_path, index=False)

    table_rows = []
    for _, row in summary_df[summary_df["material"] != "overall"].iterrows():
        table_rows.append(
            {
                "material": row["material"],
                "range_deg": f"{int(row['range_theta_min_deg'])}-{int(row['range_theta_max_deg'])}",
                "mean_G_ideal_db": row["mean_G_ideal_db"],
                "mean_G_patch_raw_db": row["mean_G_patch_raw_db"],
                "mean_G_patch_eff_db": row["mean_G_patch_eff_db"],
                "mean_G_patch_metal_floor_db": row["mean_G_patch_metal_floor_db"],
                "negative_delta_raw_rows": row["negative_delta_raw_rows"],
                "negative_delta_eff_rows": row["negative_delta_eff_rows"],
                "negative_delta_metal_floor_rows": row["negative_delta_metal_floor_rows"],
            }
        )
    table_df = pd.DataFrame(table_rows)
    table_path = output_dir / "residual_3way_table_for_review.csv"
    table_df.to_csv(table_path, index=False)

    overall = summary_df[summary_df["material"] == "overall"].iloc[0]
    md_lines = [
        "# Stage 4e Residual 3-Way Comparison",
        "",
        "Execution date: `2026-04-14`",
        "",
        "This stage was executed in the isolated workspace:",
        "",
        "- `analysis_stages/stage4e_residual_3way_comparison_20260414`",
        "",
        "## Core Finding",
        "",
        "The three patch residual variants behave very differently under same-angle comparison:",
        "",
        f"- raw negative-gap rows: `{int(overall['negative_delta_raw_rows'])}/{int(overall['n_rows'])}`",
        f"- eff negative-gap rows: `{int(overall['negative_delta_eff_rows'])}/{int(overall['n_rows'])}`",
        f"- metal-floor negative-gap rows: `{int(overall['negative_delta_metal_floor_rows'])}/{int(overall['n_rows'])}`",
        "",
        "## Material Summary",
        "",
    ]
    for _, row in summary_df[summary_df["material"] != "overall"].iterrows():
        md_lines.append(
            f"- {row['material']}: range={int(row['range_theta_min_deg'])}-{int(row['range_theta_max_deg'])} deg, "
            f"mean G_ideal={row['mean_G_ideal_db']:.2f} dB, "
            f"mean G_raw={row['mean_G_patch_raw_db']:.2f} dB, "
            f"mean G_eff={row['mean_G_patch_eff_db']:.2f} dB, "
            f"mean G_metal_floor={row['mean_G_patch_metal_floor_db']:.2f} dB, "
            f"neg rows raw/eff/metal={int(row['negative_delta_raw_rows'])}/{int(row['negative_delta_eff_rows'])}/{int(row['negative_delta_metal_floor_rows'])}"
        )

    md_lines.extend(
        [
            "",
            "## Figure-Ready CSVs",
            "",
            f"- Branch magnitude long CSV: `{branch_long_path.relative_to(repo_root)}`",
            f"- Suppression long CSV: `{supp_long_path.relative_to(repo_root)}`",
            "",
            "## Notes",
            "",
            "- `patch_raw` and `patch_eff` are patch-stage absolute-like quantities tied to the M3-based extraction path.",
            "- `patch_metal_floor` is a metal-normalized diagnostic series, not a direct replacement for the Stage 4b headline metric.",
            "- Use the `directly_comparable_to_ideal` column to filter plotting logic when needed.",
            "",
            "## Outputs",
            "",
            f"- Wide comparison table: `{wide_path.relative_to(repo_root)}`",
            f"- Summary by material: `{summary_path.relative_to(repo_root)}`",
            f"- Reviewer table CSV: `{table_path.relative_to(repo_root)}`",
            f"- Branch long CSV: `{branch_long_path.relative_to(repo_root)}`",
            f"- Suppression long CSV: `{supp_long_path.relative_to(repo_root)}`",
        ]
    )
    (output_dir / "STAGE4E_RESIDUAL_3WAY_COMPARISON.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print("Wrote residual 3-way comparison tables and figure-ready CSVs.")


if __name__ == "__main__":
    main()
