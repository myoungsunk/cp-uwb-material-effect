from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


MATERIALS = ["concrete", "glass", "wood"]
MAT_COLORS = {"concrete": "#dc2626", "glass": "#2563eb", "wood": "#059669"}


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the raw-primary dual-reporting Stage 4 summary."
    )
    repo_root = Path(__file__).resolve().parents[3]
    parser.add_argument(
        "--wide-comparison",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "stage4e_residual_3way_comparison_20260414"
        / "results"
        / "residual_3way_comparison_wide.csv",
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

    wide = pd.read_csv(args.wide_comparison)
    df = wide[wide["material"].isin(MATERIALS)].copy().sort_values(["material", "theta_deg"]).reset_index(drop=True)

    raw_primary = df[
        [
            "material",
            "theta_deg",
            "B_mag",
            "gamma_x_ideal_mag",
            "gamma_c_patch_raw_mag",
            "gamma_c_patch_eff_mag",
            "gamma_hat_c_metal_floor_mag",
            "G_ideal_db",
            "G_patch_raw_db",
            "G_patch_eff_db",
            "G_patch_metal_floor_db",
            "Delta_ideal_minus_raw_db",
            "Delta_ideal_minus_eff_db",
            "Delta_G_ideal_minus_metal_floor_db",
            "delta_raw_negative",
            "delta_eff_negative",
            "delta_metal_floor_negative",
        ]
    ].copy()
    raw_primary["headline_use_primary"] = True
    raw_primary["headline_note"] = (
        "Raw patch residual is the current paper-safe primary series because same-angle ideal>=raw holds on all locked oblique rows."
    )

    full_path = output_dir / "stage4f_raw_primary_full.csv"
    raw_primary.to_csv(full_path, index=False)

    summary_rows = []
    for material in MATERIALS:
        sub = raw_primary[raw_primary["material"] == material].copy()
        peak_ideal_idx = sub["G_ideal_db"].idxmax()
        peak_raw_idx = sub["G_patch_raw_db"].idxmax()
        peak_eff_idx = sub["G_patch_eff_db"].idxmax()
        peak_gap_raw_idx = sub["Delta_ideal_minus_raw_db"].idxmax()
        summary_rows.append(
            {
                "material": material,
                "range_theta_min_deg": float(sub["theta_deg"].min()),
                "range_theta_max_deg": float(sub["theta_deg"].max()),
                "n_rows": int(len(sub)),
                "mean_G_ideal_db": float(sub["G_ideal_db"].mean()),
                "mean_G_patch_raw_db": float(sub["G_patch_raw_db"].mean()),
                "mean_G_patch_eff_db": float(sub["G_patch_eff_db"].mean()),
                "mean_Delta_ideal_minus_raw_db": float(sub["Delta_ideal_minus_raw_db"].mean()),
                "mean_Delta_ideal_minus_eff_db": float(sub["Delta_ideal_minus_eff_db"].mean()),
                "median_Delta_ideal_minus_raw_db": float(sub["Delta_ideal_minus_raw_db"].median()),
                "negative_delta_raw_rows": int(sub["delta_raw_negative"].sum()),
                "negative_delta_eff_rows": int(sub["delta_eff_negative"].sum()),
                "peak_G_ideal_db": float(sub.loc[peak_ideal_idx, "G_ideal_db"]),
                "peak_G_ideal_theta_deg": float(sub.loc[peak_ideal_idx, "theta_deg"]),
                "peak_G_patch_raw_db": float(sub.loc[peak_raw_idx, "G_patch_raw_db"]),
                "peak_G_patch_raw_theta_deg": float(sub.loc[peak_raw_idx, "theta_deg"]),
                "peak_G_patch_eff_db": float(sub.loc[peak_eff_idx, "G_patch_eff_db"]),
                "peak_G_patch_eff_theta_deg": float(sub.loc[peak_eff_idx, "theta_deg"]),
                "peak_Delta_ideal_minus_raw_db": float(sub.loc[peak_gap_raw_idx, "Delta_ideal_minus_raw_db"]),
                "peak_Delta_ideal_minus_raw_theta_deg": float(sub.loc[peak_gap_raw_idx, "theta_deg"]),
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    summary_path = output_dir / "stage4f_raw_primary_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    table1_df = summary_df[
        [
            "material",
            "range_theta_min_deg",
            "range_theta_max_deg",
            "mean_G_ideal_db",
            "mean_G_patch_raw_db",
            "mean_G_patch_eff_db",
            "mean_Delta_ideal_minus_raw_db",
            "negative_delta_raw_rows",
            "negative_delta_eff_rows",
        ]
    ].copy()
    table1_df["range_deg"] = table1_df.apply(
        lambda row: f"{int(row['range_theta_min_deg'])}-{int(row['range_theta_max_deg'])}", axis=1
    )
    table1_df = table1_df[
        [
            "material",
            "range_deg",
            "mean_G_ideal_db",
            "mean_G_patch_raw_db",
            "mean_G_patch_eff_db",
            "mean_Delta_ideal_minus_raw_db",
            "negative_delta_raw_rows",
            "negative_delta_eff_rows",
        ]
    ]
    table1_path = output_dir / "table1_raw_primary_means.csv"
    table1_df.to_csv(table1_path, index=False)

    eff_negative_rows = raw_primary[raw_primary["delta_eff_negative"]].copy()
    eff_negative_rows["angle_bucket"] = np.where(
        eff_negative_rows["theta_deg"] < 30.0,
        "20-29",
        np.where(eff_negative_rows["theta_deg"] < 40.0, "30-39", "40+"),
    )
    eff_negative_rows_path = output_dir / "stage4f_eff_negative_rows.csv"
    eff_negative_rows.to_csv(eff_negative_rows_path, index=False)

    eff_negative_dist = (
        eff_negative_rows.groupby(["material", "angle_bucket"])
        .size()
        .reset_index(name="n_rows")
        .sort_values(["material", "angle_bucket"])
    )
    eff_negative_dist_path = output_dir / "stage4f_eff_negative_distribution.csv"
    eff_negative_dist.to_csv(eff_negative_dist_path, index=False)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    fig.suptitle("Stage 4f Raw-Primary Dual Reporting", fontweight="bold")
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = raw_primary[raw_primary["material"] == material].sort_values("theta_deg")
        x = sub["theta_deg"].to_numpy(dtype=float)
        y_ideal = sub["G_ideal_db"].to_numpy(dtype=float)
        y_raw = sub["G_patch_raw_db"].to_numpy(dtype=float)
        y_eff = sub["G_patch_eff_db"].to_numpy(dtype=float)

        ax.plot(x, y_ideal, "o-", color=MAT_COLORS[material], lw=1.8, label="Ideal upper bound")
        ax.plot(x, y_raw, "s--", color="#111827", lw=1.6, label="Patch raw (primary)")
        ax.plot(x, y_eff, "d:", color="#6b7280", lw=1.5, label="Patch eff (supplement)")
        ax.fill_between(x, y_raw, y_ideal, color=MAT_COLORS[material], alpha=0.12, label="Ideal-raw gap")
        neg = sub[sub["delta_eff_negative"]]
        if not neg.empty:
            ax.scatter(
                neg["theta_deg"].to_numpy(dtype=float),
                neg["G_patch_eff_db"].to_numpy(dtype=float),
                marker="x",
                color="#b91c1c",
                s=40,
                label="Eff negative-gap rows" if idx == 0 else None,
            )
        ax.set_title(material.capitalize())
        ax.set_xlabel(r"$\theta_i$ [deg]")
        ax.grid(True, alpha=0.3)
        if idx == 0:
            ax.set_ylabel("Suppression gain [dB]")
            ax.legend(fontsize=7)
    fig.tight_layout()
    fig_path = output_dir / "fig4f_raw_primary_dual.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    total_rows = int(len(raw_primary))
    overall_negative_raw_rows = int(raw_primary["delta_raw_negative"].sum())
    overall_negative_eff_rows = int(raw_primary["delta_eff_negative"].sum())
    overall_negative_metal_rows = int(raw_primary["delta_metal_floor_negative"].sum())

    summary_md_lines = [
        "# Stage 4f Summary",
        "",
        "Execution date: `2026-04-14`",
        "",
        "This stage was executed in the isolated workspace:",
        "",
        "- `analysis_stages/stage4f_raw_primary_dual_20260414`",
        "",
        "## Current Reporting Rule",
        "",
        "- primary patch series: `raw`",
        "- supplementary patch series: `eff`",
        "- diagnostic cross-check: `metal-floor`",
        "",
        "## Why Raw Is Primary",
        "",
        f"- same-angle negative-gap rows for `raw`: `{overall_negative_raw_rows} / {total_rows}`",
        f"- same-angle negative-gap rows for `eff`: `{overall_negative_eff_rows} / {total_rows}`",
        f"- same-angle negative-gap rows for `metal-floor`: `{overall_negative_metal_rows} / {total_rows}`, but metal-floor is normalized and not absolute",
        "",
        "## Material Summary",
        "",
    ]
    for _, row in summary_df.iterrows():
        summary_md_lines.append(
            f"- {row['material']}: range={int(row['range_theta_min_deg'])}-{int(row['range_theta_max_deg'])} deg, "
            f"mean G_ideal={row['mean_G_ideal_db']:.2f} dB, "
            f"mean G_raw={row['mean_G_patch_raw_db']:.2f} dB, "
            f"mean G_eff={row['mean_G_patch_eff_db']:.2f} dB, "
            f"mean Delta(ideal-raw)={row['mean_Delta_ideal_minus_raw_db']:.2f} dB, "
            f"neg rows raw/eff={int(row['negative_delta_raw_rows'])}/{int(row['negative_delta_eff_rows'])}"
        )

    summary_md_lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Full audit: `{full_path.relative_to(repo_root)}`",
            f"- Summary table: `{summary_path.relative_to(repo_root)}`",
            f"- Table I candidate: `{table1_path.relative_to(repo_root)}`",
            f"- Eff negative rows: `{eff_negative_rows_path.relative_to(repo_root)}`",
            f"- Eff negative distribution: `{eff_negative_dist_path.relative_to(repo_root)}`",
            f"- Raw-primary figure: `{fig_path.relative_to(repo_root)}`",
            "",
            "## Direct CP One-Point Sanity",
            "",
            "This remains a supplement-side convention check.",
            "",
            "At one fixed point (recommended: concrete, 30 deg, 6.5 GHz), run an explicit",
            "direct CP excitation in HFSS and export both reflected CP receive branches.",
            "",
            "Use that one point to answer two questions:",
            "",
            "- which receive branch is physically the residual branch",
            "- whether the directly observed CP residual is closer to `raw` or to `eff`",
            "",
            "So it is not a full new stage sweep. It is one spot-check used to lock",
            "handedness/co-cross convention and to sanity-check the correction model.",
        ]
    )
    (output_dir / "STAGE4F_SUMMARY.md").write_text("\n".join(summary_md_lines) + "\n", encoding="utf-8")

    print("Wrote Stage 4f raw-primary dual-reporting outputs.")


if __name__ == "__main__":
    main()
