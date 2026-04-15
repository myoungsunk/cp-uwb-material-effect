from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


MATERIALS = ["concrete", "glass", "wood"]


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit same-angle Delta_G signs for Stage 4b and compare raw vs corrected patch residual branches."
    )
    repo_root = Path(__file__).resolve().parents[3]
    parser.add_argument(
        "--stage4b",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "stage4b_convention_locked_20260414"
        / "results"
        / "suppression_gain_stage4b.csv",
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
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
    )
    return parser


def db_ratio(num: pd.Series, den: pd.Series) -> pd.Series:
    return 20.0 * np.log10(num.clip(lower=1e-12) / den.clip(lower=1e-12))


def main() -> None:
    args = build_argparser().parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[3]

    stage4b = pd.read_csv(args.stage4b)
    patch = pd.read_csv(args.patch_cp_aliased)

    keep_patch = patch[
        [
            "material",
            "theta_deg",
            "gamma_hat_c_cp_raw_mag",
            "gamma_hat_c_cp_eff_mag",
            "gamma_hat_x_cp_sys_mag",
        ]
    ].copy()

    df = (
        stage4b.merge(keep_patch, on=["material", "theta_deg"], how="left")
        .sort_values(["material", "theta_deg"])
        .reset_index(drop=True)
    )

    df["G_patch_raw_db"] = db_ratio(df["B_mag"], df["gamma_hat_c_cp_raw_mag"])
    df["Delta_G_raw_db"] = df["G_supp_ideal_db"] - df["G_patch_raw_db"]
    df["raw_closer_to_ideal_than_eff"] = (
        (df["gamma_hat_c_cp_raw_mag"] - df["ideal_residual_branch_mag"]).abs()
        < (df["gamma_hat_c_cp_eff_mag"] - df["ideal_residual_branch_mag"]).abs()
    )
    df["eff_smaller_than_ideal"] = (
        df["gamma_hat_c_cp_eff_mag"] < df["ideal_residual_branch_mag"]
    )
    df["raw_smaller_than_ideal"] = (
        df["gamma_hat_c_cp_raw_mag"] < df["ideal_residual_branch_mag"]
    )
    df["Delta_G_eff_negative"] = df["Delta_G_db"] < 0.0
    df["Delta_G_raw_negative"] = df["Delta_G_raw_db"] < 0.0

    material_rows = []
    for material in MATERIALS + ["overall"]:
        sub = df if material == "overall" else df[df["material"] == material]
        material_rows.append(
            {
                "material": material,
                "n_rows": int(len(sub)),
                "negative_delta_eff_rows": int(sub["Delta_G_eff_negative"].sum()),
                "negative_delta_eff_frac": float(sub["Delta_G_eff_negative"].mean()),
                "negative_delta_raw_rows": int(sub["Delta_G_raw_negative"].sum()),
                "negative_delta_raw_frac": float(sub["Delta_G_raw_negative"].mean()),
                "eff_smaller_than_ideal_rows": int(sub["eff_smaller_than_ideal"].sum()),
                "raw_smaller_than_ideal_rows": int(sub["raw_smaller_than_ideal"].sum()),
                "raw_closer_to_ideal_than_eff_rows": int(
                    sub["raw_closer_to_ideal_than_eff"].sum()
                ),
                "mean_Delta_G_eff_db": float(sub["Delta_G_db"].mean()),
                "mean_Delta_G_raw_db": float(sub["Delta_G_raw_db"].mean()),
                "min_Delta_G_eff_db": float(sub["Delta_G_db"].min()),
                "min_Delta_G_raw_db": float(sub["Delta_G_raw_db"].min()),
                "max_Delta_G_eff_db": float(sub["Delta_G_db"].max()),
                "max_Delta_G_raw_db": float(sub["Delta_G_raw_db"].max()),
            }
        )

    summary_df = pd.DataFrame(material_rows)

    full_path = output_dir / "same_angle_gap_audit_full.csv"
    summary_path = output_dir / "same_angle_gap_audit_summary.csv"
    full_df = df[
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
    full_df.to_csv(full_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    overall = summary_df[summary_df["material"] == "overall"].iloc[0]
    negative_rows = full_df[full_df["Delta_G_eff_negative"]].copy()
    sample_lines = []
    for _, row in negative_rows.iterrows():
        sample_lines.append(
            f"- {row['material']} {row['theta_deg']:.0f} deg: "
            f"ideal={row['ideal_residual_branch_mag']:.6f}, "
            f"raw={row['gamma_hat_c_cp_raw_mag']:.6f}, "
            f"eff={row['gamma_hat_c_cp_eff_mag']:.6f}, "
            f"Delta_raw={row['Delta_G_raw_db']:.2f} dB, "
            f"Delta_eff={row['Delta_G_db']:.2f} dB"
        )

    md = output_dir / "STAGE4C_SAME_ANGLE_GAP_AUDIT.md"
    md.write_text(
        "\n".join(
            [
                "# Stage 4c Same-Angle Gap Audit",
                "",
                "Execution date: `2026-04-14`",
                "",
                "This stage was executed in the isolated workspace:",
                "",
                "- `analysis_stages/stage4c_same_angle_gap_audit_20260414`",
                "",
                "## Core Finding",
                "",
                "The same-angle gap stays physically consistent only for the raw patch residual branch.",
                "",
                f"- corrected residual (`gamma_hat_c_cp_eff`) negative-gap rows: `{int(overall['negative_delta_eff_rows'])}/{int(overall['n_rows'])}`",
                f"- raw residual (`gamma_hat_c_cp_raw`) negative-gap rows: `{int(overall['negative_delta_raw_rows'])}/{int(overall['n_rows'])}`",
                "",
                "So the current effective correction layer breaks the intended",
                "`ideal >= patch` same-angle interpretation over most of the oblique main range.",
                "",
                "## Summary By Material",
                "",
                *[
                    (
                        f"- {row['material']}: n={int(row['n_rows'])}, "
                        f"eff negative={int(row['negative_delta_eff_rows'])}/{int(row['n_rows'])}, "
                        f"raw negative={int(row['negative_delta_raw_rows'])}/{int(row['n_rows'])}, "
                        f"mean Delta_eff={row['mean_Delta_G_eff_db']:.2f} dB, "
                        f"mean Delta_raw={row['mean_Delta_G_raw_db']:.2f} dB"
                    )
                    for _, row in summary_df[summary_df["material"] != "overall"].iterrows()
                ],
                "",
                "## Interpretation",
                "",
                "- LP-anchor aliasing solved the branch-name mismatch.",
                "- It did not prove that the corrected patch residual branch is a strict practical lower-bound to the ideal residual branch.",
                "- The sign flip appears only after applying the effective correction layer.",
                "- That makes over-correction or quantity mismatch the next active issue, not branch aliasing.",
                "",
                "## Negative-Gap Rows",
                "",
                *sample_lines,
                "",
                "## Outputs",
                "",
                f"- Full audit: `{full_path.relative_to(repo_root)}`",
                f"- Summary table: `{summary_path.relative_to(repo_root)}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print("Wrote Stage 4c same-angle gap audit.")


if __name__ == "__main__":
    main()
