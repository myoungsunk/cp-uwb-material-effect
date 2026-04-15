from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


VALID_MAX = {"concrete": 55.0, "glass": 60.0, "wood": 45.0}
MATERIALS = ["concrete", "glass", "wood"]


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "t", "yes", "y"}


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify LP-anchor branch mapping and export convention-locked patch aliases."
    )
    bundle_root = Path(__file__).resolve().parent.parent
    workspace_root = Path(__file__).resolve().parents[3]
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


def add_main_flag_columns(cp: pd.DataFrame, patch_cp: pd.DataFrame, patch_lp: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cp = cp.copy()
    patch_cp = patch_cp.copy()
    patch_lp = patch_lp.copy()
    cp["cp_use_for_main_claim"] = cp["cp_use_for_main_claim"].map(parse_bool)
    patch_cp["use_for_main_claim_candidate"] = patch_cp["use_for_main_claim_candidate"].map(
        parse_bool
    )
    patch_lp["use_for_main_claim_candidate"] = patch_lp["use_for_main_claim_candidate"].map(
        parse_bool
    )
    return cp, patch_cp, patch_lp


def pick_ideal_branch_columns(cp: pd.DataFrame) -> pd.DataFrame:
    if {"Gamma_same_mag", "Gamma_flip_mag"}.issubset(cp.columns):
        return cp[
            [
                "material",
                "theta_deg",
                "Gamma_same_mag",
                "Gamma_flip_mag",
                "cp_same_branch_source",
                "cp_flip_branch_source",
                "cp_use_for_main_claim",
            ]
        ].copy()
    return cp[
        ["material", "theta_deg", "Gamma_X_mag", "Gamma_C_mag", "cp_use_for_main_claim"]
    ].copy()


def main() -> None:
    args = build_argparser().parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[3]

    cp = pd.read_csv(args.cp_truth)
    patch_cp = pd.read_csv(args.patch_cp)
    patch_lp = pd.read_csv(args.patch_lp)
    cp, patch_cp, patch_lp = add_main_flag_columns(cp, patch_cp, patch_lp)

    cp = cp[cp["material"].isin(MATERIALS)].copy()
    patch_cp = patch_cp[patch_cp["material"].isin(MATERIALS)].copy()
    patch_lp = patch_lp[patch_lp["material"].isin(MATERIALS)].copy()

    cp_keep = pick_ideal_branch_columns(cp)
    patch_cp_keep = patch_cp[
        [
            "material",
            "theta_deg",
            "gamma_hat_x_cp_sys_mag",
            "gamma_hat_c_cp_raw_mag",
            "gamma_hat_c_cp_eff_mag",
            "use_for_main_claim_candidate",
        ]
    ].copy()
    patch_lp_keep = patch_lp[
        [
            "material",
            "theta_deg",
            "gamma_x_from_lp_mag",
            "gamma_c_from_lp_mag",
            "use_for_main_claim_candidate",
        ]
    ].copy()
    patch_lp_keep = patch_lp_keep.rename(
        columns={"use_for_main_claim_candidate": "lp_use_for_main_claim_candidate"}
    )

    merged = (
        cp_keep.merge(patch_cp_keep, on=["material", "theta_deg"], how="inner")
        .merge(patch_lp_keep, on=["material", "theta_deg"], how="inner")
        .sort_values(["material", "theta_deg"])
        .reset_index(drop=True)
    )

    if {"Gamma_same_mag", "Gamma_flip_mag"}.issubset(merged.columns):
        merged["ideal_residual_branch_label"] = merged["cp_same_branch_source"].fillna("Gamma_same")
        merged["ideal_dominant_branch_label"] = merged["cp_flip_branch_source"].fillna("Gamma_flip")
        merged["ideal_residual_branch_mag"] = merged["Gamma_same_mag"]
        merged["ideal_dominant_branch_mag"] = merged["Gamma_flip_mag"]
    else:
        merged["ideal_residual_branch_label"] = "Gamma_X"
        merged["ideal_dominant_branch_label"] = "Gamma_C"
        merged["ideal_residual_branch_mag"] = merged["Gamma_X_mag"]
        merged["ideal_dominant_branch_mag"] = merged["Gamma_C_mag"]
    merged["lp_small_branch_label"] = np.where(
        merged["gamma_x_from_lp_mag"] <= merged["gamma_c_from_lp_mag"],
        "gamma_x_from_lp",
        "gamma_c_from_lp",
    )
    merged["patch_eff_small_branch_label"] = np.where(
        merged["gamma_hat_c_cp_eff_mag"] <= merged["gamma_hat_x_cp_sys_mag"],
        "gamma_hat_c_cp_eff",
        "gamma_hat_x_cp_sys",
    )

    merged["lp_error_aligned"] = (
        (merged["gamma_x_from_lp_mag"] - merged["ideal_residual_branch_mag"]).abs()
        + (merged["gamma_c_from_lp_mag"] - merged["ideal_dominant_branch_mag"]).abs()
    )
    merged["lp_error_swapped"] = (
        (merged["gamma_x_from_lp_mag"] - merged["ideal_dominant_branch_mag"]).abs()
        + (merged["gamma_c_from_lp_mag"] - merged["ideal_residual_branch_mag"]).abs()
    )
    merged["patch_eff_error_aligned"] = (
        (merged["gamma_hat_x_cp_sys_mag"] - merged["ideal_residual_branch_mag"]).abs()
        + (merged["gamma_hat_c_cp_eff_mag"] - merged["ideal_dominant_branch_mag"]).abs()
    )
    merged["patch_eff_error_swapped"] = (
        (merged["gamma_hat_x_cp_sys_mag"] - merged["ideal_dominant_branch_mag"]).abs()
        + (merged["gamma_hat_c_cp_eff_mag"] - merged["ideal_residual_branch_mag"]).abs()
    )

    merged["lp_mapping_vote"] = np.where(
        merged["lp_error_aligned"] <= merged["lp_error_swapped"], "aligned", "swapped"
    )
    merged["patch_eff_mapping_vote"] = np.where(
        merged["patch_eff_error_aligned"] <= merged["patch_eff_error_swapped"],
        "aligned",
        "swapped",
    )

    merged["lp_anchor_lock_pass"] = (
        (merged["lp_small_branch_label"] == "gamma_x_from_lp")
        & (merged["lp_mapping_vote"] == "aligned")
    )
    merged["patch_eff_alias_lock_pass"] = (
        (merged["patch_eff_small_branch_label"] == "gamma_hat_c_cp_eff")
        & (merged["patch_eff_mapping_vote"] == "swapped")
    )

    merged["use_for_main_claim"] = (
        merged["cp_use_for_main_claim"]
        & merged["use_for_main_claim_candidate"]
        & merged["lp_use_for_main_claim_candidate"]
        & merged.apply(lambda row: row["theta_deg"] <= VALID_MAX[row["material"]], axis=1)
    )

    merged["cp_residual_branch_name"] = "gamma_hat_c_cp_raw"
    merged["cp_dominant_branch_name"] = "gamma_hat_x_cp_sys"
    merged["cp_residual_branch_mag"] = merged["gamma_hat_c_cp_raw_mag"]
    merged["cp_dominant_branch_mag"] = merged["gamma_hat_x_cp_sys_mag"]
    merged["branch_lock_method"] = "lp_anchor_branch_lock_20260414"
    merged["cp_residual_branch_supplementary_name"] = "gamma_hat_c_cp_eff"
    merged["cp_residual_branch_supplementary_mag"] = merged["gamma_hat_c_cp_eff_mag"]
    merged["branch_lock_note"] = (
        "LP-anchor swap evidence still identifies the RR-derived patch branch as the ideal residual-side channel; "
        "raw is now exported as the primary residual alias and eff is retained only as a supplementary corrected estimate."
    )

    full_df = merged.copy()
    main_df = merged[merged["use_for_main_claim"]].copy().reset_index(drop=True)

    summary_rows = []
    for material in MATERIALS + ["overall"]:
        if material == "overall":
            sub = main_df.copy()
        else:
            sub = main_df[main_df["material"] == material].copy()
        summary_rows.append(
            {
                "material": material,
                "n_rows": int(len(sub)),
                "ideal_residual_rows": int(len(sub)),
                "lp_small_gamma_x_rows": int((sub["lp_small_branch_label"] == "gamma_x_from_lp").sum()),
                "patch_eff_small_residual_rows": int((sub["patch_eff_small_branch_label"] == "gamma_hat_c_cp_eff").sum()),
                "lp_aligned_vote_rows": int((sub["lp_mapping_vote"] == "aligned").sum()),
                "patch_eff_swapped_vote_rows": int((sub["patch_eff_mapping_vote"] == "swapped").sum()),
                "lp_anchor_lock_pass_rows": int(sub["lp_anchor_lock_pass"].sum()),
                "patch_eff_alias_lock_pass_rows": int(sub["patch_eff_alias_lock_pass"].sum()),
                "lp_error_aligned_mean": float(sub["lp_error_aligned"].mean()),
                "lp_error_swapped_mean": float(sub["lp_error_swapped"].mean()),
                "patch_eff_error_aligned_mean": float(sub["patch_eff_error_aligned"].mean()),
                "patch_eff_error_swapped_mean": float(sub["patch_eff_error_swapped"].mean()),
            }
        )

    summary_df = pd.DataFrame(summary_rows)

    patch_cp_aliased = patch_cp.copy()
    patch_cp_aliased["cp_residual_branch_name"] = "gamma_hat_c_cp_raw"
    patch_cp_aliased["cp_dominant_branch_name"] = "gamma_hat_x_cp_sys"
    patch_cp_aliased["cp_residual_branch_real"] = patch_cp_aliased["gamma_hat_c_cp_raw_real"]
    patch_cp_aliased["cp_residual_branch_imag"] = patch_cp_aliased["gamma_hat_c_cp_raw_imag"]
    patch_cp_aliased["cp_residual_branch_mag"] = patch_cp_aliased["gamma_hat_c_cp_raw_mag"]
    patch_cp_aliased["cp_dominant_branch_real"] = patch_cp_aliased["gamma_hat_x_cp_sys_real"]
    patch_cp_aliased["cp_dominant_branch_imag"] = patch_cp_aliased["gamma_hat_x_cp_sys_imag"]
    patch_cp_aliased["cp_dominant_branch_mag"] = patch_cp_aliased["gamma_hat_x_cp_sys_mag"]
    patch_cp_aliased["branch_lock_method"] = "lp_anchor_branch_lock_20260414"
    patch_cp_aliased["cp_residual_branch_supplementary_name"] = "gamma_hat_c_cp_eff"
    patch_cp_aliased["cp_residual_branch_supplementary_real"] = patch_cp_aliased["gamma_hat_c_cp_eff_real"]
    patch_cp_aliased["cp_residual_branch_supplementary_imag"] = patch_cp_aliased["gamma_hat_c_cp_eff_imag"]
    patch_cp_aliased["cp_residual_branch_supplementary_mag"] = patch_cp_aliased["gamma_hat_c_cp_eff_mag"]
    patch_cp_aliased["branch_lock_note"] = (
        "Alias columns added after LP-derived bridge matched the ideal Gamma_X/Gamma_C convention; "
        "raw is the primary residual alias and eff is supplementary."
    )

    full_path = output_dir / "lp_anchor_branch_lock_full.csv"
    main_path = output_dir / "lp_anchor_branch_lock_main.csv"
    summary_path = output_dir / "lp_anchor_branch_lock_summary.csv"
    aliased_patch_path = output_dir / "patch_cp_extracted_with_lp_anchor_alias.csv"

    full_df.to_csv(full_path, index=False)
    main_df.to_csv(main_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    patch_cp_aliased.to_csv(aliased_patch_path, index=False)

    overall = summary_df[summary_df["material"] == "overall"].iloc[0]
    summary_md = output_dir / "LP_ANCHOR_BRANCH_LOCK_SUMMARY.md"
    summary_md.write_text(
        "\n".join(
            [
                "# LP Anchor Branch Lock Summary",
                "",
                "Execution date: `2026-04-14`",
                "",
                "This stage was executed in the isolated workspace:",
                "",
                "- `analysis_stages/lp_anchor_branch_lock_20260414`",
                "",
                "## Main-Range Verdict",
                "",
                f"- Main rows audited: `{int(overall['n_rows'])}`",
                f"- Ideal residual branch rows: `{int(overall['ideal_residual_rows'])}/{int(overall['n_rows'])}`",
                f"- LP small branch = `gamma_x_from_lp` rows: `{int(overall['lp_small_gamma_x_rows'])}/{int(overall['n_rows'])}`",
                f"- Patch eff small branch = `gamma_hat_c_cp_eff` rows: `{int(overall['patch_eff_small_residual_rows'])}/{int(overall['n_rows'])}`",
                f"- LP aligned-vote rows: `{int(overall['lp_aligned_vote_rows'])}/{int(overall['n_rows'])}`",
                f"- Patch eff swapped-vote rows: `{int(overall['patch_eff_swapped_vote_rows'])}/{int(overall['n_rows'])}`",
                "",
                "## Error Comparison",
                "",
                f"- LP aligned mean abs error: `{overall['lp_error_aligned_mean']:.6f}`",
                f"- LP swapped mean abs error: `{overall['lp_error_swapped_mean']:.6f}`",
                f"- Patch eff aligned mean abs error: `{overall['patch_eff_error_aligned_mean']:.6f}`",
                f"- Patch eff swapped mean abs error: `{overall['patch_eff_error_swapped_mean']:.6f}`",
                "",
                "## Locked Alias Decision",
                "",
                "- `cp_residual_branch = gamma_hat_c_cp_raw`",
                "- `cp_dominant_branch = gamma_hat_x_cp_sys`",
                "- `cp_residual_branch_supplementary = gamma_hat_c_cp_eff`",
                "- `patch_eff_*` audit columns above remain supplementary diagnostics only",
                "",
                "## Outputs",
                "",
                f"- Full audit: `{full_path.relative_to(repo_root)}`",
                f"- Main-range audit: `{main_path.relative_to(repo_root)}`",
                f"- Summary table: `{summary_path.relative_to(repo_root)}`",
                f"- Aliased patch CP export: `{aliased_patch_path.relative_to(repo_root)}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print("Wrote LP-anchor branch lock audit and aliased patch CP export.")


if __name__ == "__main__":
    main()
