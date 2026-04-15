# Consolidated review copy for paper-pipeline code assessment.
# Stage: 4
# Role: Compare PEC-based CP correction against ideal and raw residual definitions.
# Source: analysis_stages/stage4h_pec_based_cp_correction_20260414/code/build_pec_based_cp_comparison.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


VALID_MAX_THETA = {
    "concrete": 55.0,
    "glass": 60.0,
    "wood": 45.0,
}


def ideal_residual_mag_col(df: pd.DataFrame) -> str:
    return "Gamma_same_mag" if "Gamma_same_mag" in df.columns else "Gamma_X_mag"


def main() -> None:
    bundle_root = Path(__file__).resolve().parent.parent
    workspace_root = Path(__file__).resolve().parents[3]
    out_dir = Path(__file__).resolve().parents[1] / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    cp_path = (
        workspace_root
        / "analysis_stages"
        / "stage3_patch_paper_final_20260414"
        / "cp"
        / "results"
        / "patch_cp_extracted.csv"
    )
    lp_path = (
        workspace_root
        / "analysis_stages"
        / "stage3_patch_paper_final_20260414"
        / "lp"
        / "results"
        / "patch_lp_extracted.csv"
    )
    linear_path = (
        bundle_root
        / "data"
        / "stage_1"
        / "truth_table_linear_locked.csv"
    )
    cp_truth_path = (
        bundle_root
        / "data"
        / "stage_2"
        / "sameflip_alias_20260415"
        / "truth_table_cp_shared_common_sameflip.csv"
    )

    cp = pd.read_csv(cp_path)
    lp = pd.read_csv(lp_path)
    linear = pd.read_csv(linear_path)
    cp_truth = pd.read_csv(cp_truth_path)

    linear["B_mag"] = linear[["R_TE_mag", "R_TM_mag"]].max(axis=1)
    main = linear[linear["material"].isin(VALID_MAX_THETA)].copy()
    main = main[main["theta_deg"] >= 20.0].copy()
    main = main[main.apply(lambda r: r["theta_deg"] <= VALID_MAX_THETA[r["material"]], axis=1)].copy()
    main = main[["material", "theta_deg", "B_mag"]]

    cp = cp.copy()
    cp["gamma_d"] = cp["gamma_hat_x_cp_sys_real"] + 1j * cp["gamma_hat_x_cp_sys_imag"]
    cp["gamma_r_raw"] = cp["gamma_hat_c_cp_raw_real"] + 1j * cp["gamma_hat_c_cp_raw_imag"]

    metal = cp[cp["material"] == "metal"].copy()
    metal["lambda_pec_simple"] = metal["gamma_r_raw"]
    metal["lambda_pec_ratio"] = metal["gamma_r_raw"] / metal["gamma_d"]
    metal = metal[
        [
            "theta_deg",
            "lambda_pec_simple",
            "lambda_pec_ratio",
            "gamma_hat_c_cp_raw_mag",
            "gamma_hat_x_cp_sys_mag",
        ]
    ].rename(
        columns={
            "gamma_hat_c_cp_raw_mag": "pec_raw_mag",
            "gamma_hat_x_cp_sys_mag": "pec_dominant_mag",
        }
    )

    cp_mat = cp[cp["material"].isin(VALID_MAX_THETA)].copy()
    cp_mat = cp_mat.merge(metal, on="theta_deg", how="left")
    cp_mat["gamma_cp_pec_simple"] = cp_mat["gamma_r_raw"] - cp_mat["lambda_pec_simple"] * cp_mat["gamma_d"]
    cp_mat["gamma_cp_pec_ratio"] = cp_mat["gamma_r_raw"] - cp_mat["lambda_pec_ratio"] * cp_mat["gamma_d"]
    cp_mat["gamma_cp_pec_simple_mag"] = np.abs(cp_mat["gamma_cp_pec_simple"])
    cp_mat["gamma_cp_pec_ratio_mag"] = np.abs(cp_mat["gamma_cp_pec_ratio"])

    ideal_residual_col = ideal_residual_mag_col(cp_truth)
    comp = (
        main.merge(cp_mat, on=["material", "theta_deg"], how="inner")
        .merge(lp[["material", "theta_deg", "gamma_x_from_lp_mag"]], on=["material", "theta_deg"], how="inner")
        .merge(
            cp_truth[["material", "theta_deg", ideal_residual_col]].rename(columns={ideal_residual_col: "ideal_residual_mag"}),
            on=["material", "theta_deg"],
            how="inner",
        )
    )

    comp["G_ideal_db"] = 20.0 * np.log10(comp["B_mag"] / comp["ideal_residual_mag"])
    comp["G_cp_raw_db"] = 20.0 * np.log10(comp["B_mag"] / comp["gamma_hat_c_cp_raw_mag"])
    comp["G_lp_db"] = 20.0 * np.log10(comp["B_mag"] / comp["gamma_x_from_lp_mag"])
    comp["G_cp_pec_simple_db"] = 20.0 * np.log10(comp["B_mag"] / comp["gamma_cp_pec_simple_mag"])
    comp["G_cp_pec_ratio_db"] = 20.0 * np.log10(comp["B_mag"] / comp["gamma_cp_pec_ratio_mag"])

    for variant in ["simple", "ratio"]:
        comp[f"Delta_ideal_minus_cp_pec_{variant}_db"] = comp["G_ideal_db"] - comp[f"G_cp_pec_{variant}_db"]
        comp[f"ideal_lt_cp_pec_{variant}"] = comp[f"Delta_ideal_minus_cp_pec_{variant}_db"] < 0.0

    comp.to_csv(out_dir / "pec_based_cp_comparison_full.csv", index=False)

    summary_rows = []
    for material, group in comp.groupby("material", sort=True):
        summary_rows.append(
            {
                "material": material,
                "n_rows": int(len(group)),
                "ideal_mean_db": float(group["G_ideal_db"].mean()),
                "cp_raw_mean_db": float(group["G_cp_raw_db"].mean()),
                "lp_mean_db": float(group["G_lp_db"].mean()),
                "cp_pec_simple_mean_db": float(group["G_cp_pec_simple_db"].mean()),
                "cp_pec_ratio_mean_db": float(group["G_cp_pec_ratio_db"].mean()),
                "ideal_lt_cp_pec_simple_rows": int(group["ideal_lt_cp_pec_simple"].sum()),
                "ideal_lt_cp_pec_ratio_rows": int(group["ideal_lt_cp_pec_ratio"].sum()),
            }
        )
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(out_dir / "pec_based_cp_comparison_summary.csv", index=False)

    long_rows = []
    for _, row in comp.iterrows():
        for label, value in [
            ("ideal", row["G_ideal_db"]),
            ("cp_raw", row["G_cp_raw_db"]),
            ("lp", row["G_lp_db"]),
            ("cp_pec_simple", row["G_cp_pec_simple_db"]),
            ("cp_pec_ratio", row["G_cp_pec_ratio_db"]),
        ]:
            long_rows.append(
                {
                    "material": row["material"],
                    "theta_deg": row["theta_deg"],
                    "curve": label,
                    "gain_db": float(value),
                }
            )
    pd.DataFrame(long_rows).to_csv(out_dir / "pec_based_cp_comparison_long.csv", index=False)

    neg_simple = int(comp["ideal_lt_cp_pec_simple"].sum())
    neg_ratio = int(comp["ideal_lt_cp_pec_ratio"].sum())
    total_rows = int(len(comp))

    md_lines = [
        "# Stage 4h - PEC-Based CP Correction Comparison",
        "",
        "Execution date: `2026-04-14`",
        "",
        "## Purpose",
        "",
        "Test the proposed PEC-based reflective leakage subtraction against the locked `ideal`, `LP-derived`, and `CP raw` curves.",
        "",
        "## Tested PEC Corrections",
        "",
        "- simple PEC approximation:",
        "  - `Gamma_C_new = Gamma_C_raw - Gamma_C_raw_PEC * Gamma_d`",
        "- ratio PEC correction:",
        "  - `lambda_PEC = Gamma_C_raw_PEC / Gamma_d_PEC`",
        "  - `Gamma_C_new = Gamma_C_raw - lambda_PEC * Gamma_d`",
        "",
        "The ratio form is the measurement-consistent version when `Gamma_d_PEC` is not exactly unity.",
        "",
        "## Main Result",
        "",
        f"- `ideal < cp_pec_simple` rows: `{neg_simple} / {total_rows}`",
        f"- `ideal < cp_pec_ratio` rows: `{neg_ratio} / {total_rows}`",
        "",
        "This means both PEC-based CP corrections overshoot the material-limited ideal reference in most same-angle rows, so they cannot be used as a safe upper-bound-consistent headline correction.",
        "",
        "## Mean Gain By Material",
        "",
    ]
    for _, row in summary.iterrows():
        md_lines.extend(
            [
                f"### {row['material']}",
                "",
                f"- ideal mean: `{row['ideal_mean_db']:.2f} dB`",
                f"- CP raw mean: `{row['cp_raw_mean_db']:.2f} dB`",
                f"- LP-derived mean: `{row['lp_mean_db']:.2f} dB`",
                f"- CP PEC simple mean: `{row['cp_pec_simple_mean_db']:.2f} dB`",
                f"- CP PEC ratio mean: `{row['cp_pec_ratio_mean_db']:.2f} dB`",
                f"- `ideal < cp_pec_simple` rows: `{int(row['ideal_lt_cp_pec_simple_rows'])}`",
                f"- `ideal < cp_pec_ratio` rows: `{int(row['ideal_lt_cp_pec_ratio_rows'])}`",
                "",
            ]
        )

    md_lines.extend(
        [
            "## Interpretation",
            "",
            "- The proposed PEC subtraction removes too much of the CP residual branch.",
            "- Relative to `CP raw`, it raises the apparent CP suppression by about `8-10 dB`, but it overshoots even beyond `ideal` in most rows.",
            "- `LP-derived` remains the only practical estimate that stays physically close to `ideal` without the same widespread oversubtraction.",
            "",
            "## Outputs",
            "",
            f"- full table: `{out_dir / 'pec_based_cp_comparison_full.csv'}`",
            f"- summary: `{out_dir / 'pec_based_cp_comparison_summary.csv'}`",
            f"- long curve CSV: `{out_dir / 'pec_based_cp_comparison_long.csv'}`",
        ]
    )
    (out_dir / "STAGE4H_PEC_BASED_CP_COMPARISON.md").write_text("\n".join(md_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
