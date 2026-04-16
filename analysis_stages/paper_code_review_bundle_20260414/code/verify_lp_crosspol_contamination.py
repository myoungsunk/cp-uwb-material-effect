from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


MATERIALS = ["concrete", "glass", "wood"]
VALID_MAX = {"concrete": 55.0, "glass": 60.0, "wood": 45.0}
PASS_DB = -20.0
WARNING_DB = -15.0
ELEVATED_DB = -10.0
DOMINANT_DB = 0.0
LARGE_FRESNEL_DEV_DB = 1.0


def build_argparser() -> argparse.ArgumentParser:
    bundle_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description=(
            "Audit LP cross-polar contamination from the existing Stage 3 frequency-resolved "
            "LP export and compare it against the metal-normalized Fresnel deviation replay."
        )
    )
    parser.add_argument(
        "--lp-freq",
        type=Path,
        default=bundle_root / "data" / "stage_3" / "lp" / "patch_lp_extracted_freq_resolved.csv",
    )
    parser.add_argument(
        "--metal-normalized-full",
        type=Path,
        default=bundle_root / "results" / "debug" / "verify_lp_metal_normalized_full.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=bundle_root / "results" / "debug",
    )
    return parser


def build_main_range_flag(material: str, theta_deg: float) -> bool:
    return str(material) in VALID_MAX and float(theta_deg) >= 20.0 and float(theta_deg) <= VALID_MAX[str(material)]


def overlap_count(sub: pd.DataFrame, threshold_db: float) -> int:
    warn = sub["max_cross_any_db"] > threshold_db
    dev = sub["large_fresnel_dev_flag"].fillna(False).astype(bool)
    return int((warn & dev).sum())


def build_overlap_summary(theta_df: pd.DataFrame) -> pd.DataFrame:
    summary_rows: list[dict[str, object]] = []
    scopes = {
        "all": theta_df,
        "main_range": theta_df[theta_df["in_main_range"]].copy(),
        "nonmain_range": theta_df[~theta_df["in_main_range"]].copy(),
    }

    for scope, sub in scopes.items():
        if sub.empty:
            continue
        pearson = float(sub["max_cross_any_db"].corr(sub["max_abs_fresnel_dev_db"], method="pearson")) if len(sub) > 1 else np.nan
        spearman = float(sub["max_cross_any_db"].corr(sub["max_abs_fresnel_dev_db"], method="spearman")) if len(sub) > 1 else np.nan
        summary_rows.append(
            {
                "scope": scope,
                "n_rows": int(len(sub)),
                "large_fresnel_dev_rows": int(sub["large_fresnel_dev_flag"].fillna(False).astype(bool).sum()),
                "pearson_corr_max_cross_vs_fresnel_dev": pearson,
                "spearman_corr_max_cross_vs_fresnel_dev": spearman,
                "rows_gt_pass_db": int((sub["max_cross_any_db"] > PASS_DB).sum()),
                "rows_gt_warning_db": int((sub["max_cross_any_db"] > WARNING_DB).sum()),
                "rows_gt_elevated_db": int((sub["max_cross_any_db"] > ELEVATED_DB).sum()),
                "rows_gt_dominant_db": int((sub["max_cross_any_db"] > DOMINANT_DB).sum()),
                "overlap_warning_large_dev_rows": overlap_count(sub, WARNING_DB),
                "overlap_elevated_large_dev_rows": overlap_count(sub, ELEVATED_DB),
                "overlap_dominant_large_dev_rows": overlap_count(sub, DOMINANT_DB),
            }
        )

    return pd.DataFrame(summary_rows)


def write_markdown(
    *,
    theta_df: pd.DataFrame,
    overlap_df: pd.DataFrame,
    map_path: Path,
    theta_path: Path,
    overlap_path: Path,
    output_path: Path,
    repo_root: Path,
) -> None:
    all_summary = overlap_df[overlap_df["scope"] == "all"].iloc[0]
    main_summary = overlap_df[overlap_df["scope"] == "main_range"].iloc[0]
    nonmain_summary = overlap_df[overlap_df["scope"] == "nonmain_range"].iloc[0]

    top_cross = theta_df.sort_values("max_cross_any_db", ascending=False).head(10).copy()
    top_large_dev = theta_df[theta_df["large_fresnel_dev_flag"].fillna(False)].copy()

    lines = [
        "# Verify LP Cross-Pol Contamination",
        "",
        "Execution date: `2026-04-16`",
        "",
        "## Scope",
        "",
        "- No new simulation is used.",
        "- Source map is the existing Stage 3 LP frequency-resolved export.",
        "- The audit reconstructs the LP internal cross-pol ratios from the exported Stage 3 ratios:",
        "  - `|h_tilde_zy / h_tilde_zz| = |r_hat_zy_sys / r_hat_zz_sys|`",
        "  - `|h_tilde_yz / h_tilde_yy| = |r_hat_yz_sys / r_hat_yy_sys|`",
        "- Fresnel deviation overlap uses the existing metal-normalized replay output.",
        f"- Pass target from the review note: main-range cross-pol `<= {PASS_DB:.0f} dB`.",
        f"- Legacy warning threshold: `{WARNING_DB:.0f} dB`.",
        f"- Elevated threshold used for discrimination: `{ELEVATED_DB:.0f} dB`.",
        f"- Large Fresnel deviation threshold: `>{LARGE_FRESNEL_DEV_DB:.1f} dB`.",
        "",
        "## Main Findings",
        "",
        f"- `-15 dB` warning is non-discriminative in this dataset: `{int(all_summary['rows_gt_warning_db'])}/{int(all_summary['n_rows'])}` theta-rows exceed it.",
        f"- The stricter pass target also fails everywhere: `{int(main_summary['rows_gt_pass_db'])}/{int(main_summary['n_rows'])}` main-range rows exceed `-20 dB`.",
        f"- Main-range correlation between max cross-pol and metal-normalized Fresnel deviation is only moderate: Pearson `{main_summary['pearson_corr_max_cross_vs_fresnel_dev']:.3f}`, Spearman `{main_summary['spearman_corr_max_cross_vs_fresnel_dev']:.3f}`.",
        f"- Non-main-range correlation is strong: Pearson `{nonmain_summary['pearson_corr_max_cross_vs_fresnel_dev']:.3f}`, Spearman `{nonmain_summary['spearman_corr_max_cross_vs_fresnel_dev']:.3f}`.",
        f"- All large-deviation rows (`>{LARGE_FRESNEL_DEV_DB:.1f} dB`) are captured by the elevated `-10 dB` threshold: `{int(nonmain_summary['overlap_elevated_large_dev_rows'])}/{int(nonmain_summary['large_fresnel_dev_rows'])}` in the non-main range.",
        "",
        "## Interpretation",
        "",
        "- Cross-pol contamination is real and becomes severe at high angle.",
        "- However, `-15 dB` alone does not explain the current LP main-range contradiction because every theta-row already exceeds that threshold.",
        "- The overlap with large Fresnel deviation becomes informative only once leakage rises to about `-10 dB` or worse, and that pattern is concentrated outside the current main range.",
        "- This means cross-pol is a credible high-angle validity limiter, but not the primary cause of the main-range LP ordering failure after metal normalization.",
        "",
        "## Worst Theta Rows",
        "",
    ]

    for _, row in top_cross.iterrows():
        lines.append(
            f"- {row['material']} {row['theta_deg']:.0f} deg: "
            f"max cross-pol `{row['max_cross_any_db']:.2f} dB`, "
            f"mean cross-pol `{row['mean_cross_any_db']:.2f} dB`, "
            f"main-range=`{bool(row['in_main_range'])}`, "
            f"max Fresnel dev `{row['max_abs_fresnel_dev_db']:.3f} dB`"
        )

    lines.extend(["", "## Large-Deviation Overlap", ""])
    if top_large_dev.empty:
        lines.append("- No row exceeded the large-deviation threshold.")
    else:
        for _, row in top_large_dev.iterrows():
            lines.append(
                f"- {row['material']} {row['theta_deg']:.0f} deg: "
                f"max Fresnel dev `{row['max_abs_fresnel_dev_db']:.3f} dB`, "
                f"max cross-pol `{row['max_cross_any_db']:.2f} dB`, "
                f"`-10 dB` exceeded=`{bool(row['max_cross_any_db'] > ELEVATED_DB)}`"
            )

    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Map CSV: `{map_path.relative_to(repo_root)}`",
            f"- Theta summary CSV: `{theta_path.relative_to(repo_root)}`",
            f"- Overlap summary CSV: `{overlap_path.relative_to(repo_root)}`",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_argparser().parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[3]

    freq_df = pd.read_csv(args.lp_freq)
    freq_df = freq_df[freq_df["material"].isin(MATERIALS)].copy()

    freq_df["cross_zy_over_zz_mag"] = freq_df["r_hat_zy_sys_mag"].clip(lower=1e-12) / freq_df["r_hat_zz_sys_mag"].clip(lower=1e-12)
    freq_df["cross_yz_over_yy_mag"] = freq_df["r_hat_yz_sys_mag"].clip(lower=1e-12) / freq_df["r_hat_yy_sys_mag"].clip(lower=1e-12)
    freq_df["cross_zy_over_zz_db"] = 20.0 * np.log10(freq_df["cross_zy_over_zz_mag"].clip(lower=1e-12))
    freq_df["cross_yz_over_yy_db"] = 20.0 * np.log10(freq_df["cross_yz_over_yy_mag"].clip(lower=1e-12))
    freq_df["cross_any_db"] = freq_df[["cross_zy_over_zz_db", "cross_yz_over_yy_db"]].max(axis=1)
    freq_df["in_main_range"] = freq_df.apply(lambda row: build_main_range_flag(str(row["material"]), float(row["theta_deg"])), axis=1)
    freq_df["pass_target_failed_flag"] = freq_df["cross_any_db"] > PASS_DB
    freq_df["warning_flag"] = freq_df["cross_any_db"] > WARNING_DB
    freq_df["elevated_flag"] = freq_df["cross_any_db"] > ELEVATED_DB
    freq_df["dominant_flag"] = freq_df["cross_any_db"] > DOMINANT_DB

    theta_df = (
        freq_df.groupby(["material", "theta_deg", "in_main_range"], as_index=False)
        .agg(
            max_cross_zy_db=("cross_zy_over_zz_db", "max"),
            mean_cross_zy_db=("cross_zy_over_zz_db", "mean"),
            max_cross_yz_db=("cross_yz_over_yy_db", "max"),
            mean_cross_yz_db=("cross_yz_over_yy_db", "mean"),
            max_cross_any_db=("cross_any_db", "max"),
            mean_cross_any_db=("cross_any_db", "mean"),
            frac_freq_gt_pass_db=("pass_target_failed_flag", "mean"),
            frac_freq_gt_warning_db=("warning_flag", "mean"),
            frac_freq_gt_elevated_db=("elevated_flag", "mean"),
            frac_freq_gt_dominant_db=("dominant_flag", "mean"),
        )
        .sort_values(["material", "theta_deg"])
        .reset_index(drop=True)
    )

    metal_df = pd.read_csv(args.metal_normalized_full)
    metal_df["max_abs_fresnel_dev_db"] = metal_df[
        ["r_te_metal_vs_theory_band_db", "r_tm_metal_vs_theory_band_db"]
    ].abs().max(axis=1)
    theta_df = theta_df.merge(
        metal_df[
            [
                "material",
                "theta_deg",
                "max_abs_fresnel_dev_db",
                "cross_zy_db",
                "cross_yz_db",
            ]
        ].rename(
            columns={
                "cross_zy_db": "band_cross_zy_db",
                "cross_yz_db": "band_cross_yz_db",
            }
        ),
        on=["material", "theta_deg"],
        how="left",
    )
    theta_df["large_fresnel_dev_flag"] = theta_df["max_abs_fresnel_dev_db"] > LARGE_FRESNEL_DEV_DB

    overlap_df = build_overlap_summary(theta_df)

    map_path = output_dir / "verify_lp_crosspol_contamination_map.csv"
    theta_path = output_dir / "verify_lp_crosspol_contamination_theta_summary.csv"
    overlap_path = output_dir / "verify_lp_crosspol_contamination_overlap_summary.csv"
    md_path = output_dir / "VERIFY_LP_CROSSPOL_CONTAMINATION.md"

    freq_df.to_csv(map_path, index=False)
    theta_df.to_csv(theta_path, index=False)
    overlap_df.to_csv(overlap_path, index=False)
    write_markdown(
        theta_df=theta_df,
        overlap_df=overlap_df,
        map_path=map_path,
        theta_path=theta_path,
        overlap_path=overlap_path,
        output_path=md_path,
        repo_root=repo_root,
    )

    print(f"Wrote {map_path}")
    print(f"Wrote {theta_path}")
    print(f"Wrote {overlap_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
