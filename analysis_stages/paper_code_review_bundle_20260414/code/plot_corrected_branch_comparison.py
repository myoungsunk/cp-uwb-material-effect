from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


MATERIAL_ORDER = ["concrete", "glass", "wood"]
BRANCH_ORDER = [
    "ideal",
    "cp_raw",
    "cp_eff_locked",
    "cp_eff_corrected",
    "lp_raw",
    "lp_metal_norm",
]
BRANCH_LABELS = {
    "ideal": "Ideal",
    "cp_raw": "CP raw",
    "cp_eff_locked": "CP eff locked",
    "cp_eff_corrected": "CP eff corrected",
    "lp_raw": "LP raw",
    "lp_metal_norm": "LP metal norm",
}
BRANCH_COLORS = {
    "ideal": "#1f77b4",
    "cp_raw": "#ff7f0e",
    "cp_eff_locked": "#d62728",
    "cp_eff_corrected": "#d62728",
    "lp_raw": "#2ca02c",
    "lp_metal_norm": "#2ca02c",
}
BRANCH_MARKERS = {
    "ideal": "o",
    "cp_raw": "s",
    "cp_eff_locked": "^",
    "cp_eff_corrected": "v",
    "lp_raw": "D",
    "lp_metal_norm": "P",
}
BRANCH_LINESTYLES = {
    "ideal": "-",
    "cp_raw": "-",
    "cp_eff_locked": "-",
    "cp_eff_corrected": "--",
    "lp_raw": "-",
    "lp_metal_norm": "--",
}
DB_FLOOR = 1e-12
EXECUTION_DATE = "2026-04-16"


def build_argparser() -> argparse.ArgumentParser:
    bundle_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description=(
            "Plot before/after final branch metrics using the locked stage4f baseline "
            "plus the A1 CP eff corrected replay and the LP metal-normalized replay."
        )
    )
    parser.add_argument(
        "--stage4f-full",
        type=Path,
        default=bundle_root / "results" / "stage4f_raw_primary_full.csv",
    )
    parser.add_argument(
        "--cp-eff-corrected",
        type=Path,
        default=bundle_root / "results" / "debug" / "verify_cp_eff_material_specific_eps.csv",
    )
    parser.add_argument(
        "--lp-metal",
        type=Path,
        default=bundle_root / "results" / "debug" / "verify_lp_metal_normalized_full.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=bundle_root / "results" / "debug",
    )
    return parser


def db20(value: pd.Series | np.ndarray | float) -> pd.Series | np.ndarray | float:
    if isinstance(value, pd.Series):
        return 20.0 * np.log10(value.clip(lower=DB_FLOOR))
    array = np.asarray(value, dtype=float)
    return 20.0 * np.log10(np.clip(array, DB_FLOOR, None))


def build_plot_df(stage4f: pd.DataFrame, cp_eff_corrected: pd.DataFrame, lp_metal: pd.DataFrame) -> pd.DataFrame:
    cp_keep = cp_eff_corrected[
        [
            "material",
            "theta_deg",
            "gamma_c_eff_ideal_center_band_mag",
            "G_cp_eff_ideal_center_band_db",
        ]
    ].copy()

    lp_keep = lp_metal[lp_metal["in_main_range"].astype(bool)].copy()[
        [
            "material",
            "theta_deg",
            "gamma_x_metal_band_mag",
        ]
    ]

    merged = (
        stage4f.merge(cp_keep, on=["material", "theta_deg"], how="left")
        .merge(lp_keep, on=["material", "theta_deg"], how="left")
        .sort_values(["material", "theta_deg"])
        .reset_index(drop=True)
    )

    rows: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        material = str(row["material"])
        theta_deg = float(row["theta_deg"])

        branch_map = {
            "ideal": {
                "suppression_gain_db": float(row["G_ideal_db"]),
                "dominant_to_residual_gain_db": float(row["G_ideal_db"]),
                "dominant_db": float(db20(float(row["B_mag"]))),
                "residual_db": float(db20(float(row["gamma_x_ideal_mag"]))),
            },
            "cp_raw": {
                "suppression_gain_db": float(row["G_patch_raw_db"]),
                "dominant_to_residual_gain_db": float(row["G_cp_raw_sys_db"]),
                "dominant_db": float(db20(float(row["B_cp_proxy_mag"]))),
                "residual_db": float(db20(float(row["gamma_c_patch_raw_mag"]))),
            },
            "cp_eff_locked": {
                "suppression_gain_db": float(row["G_patch_eff_db"]),
                "dominant_to_residual_gain_db": float(row["G_cp_eff_sys_db"]),
                "dominant_db": float(db20(float(row["B_cp_proxy_mag"]))),
                "residual_db": float(db20(float(row["gamma_c_patch_eff_mag"]))),
            },
            "cp_eff_corrected": {
                "suppression_gain_db": float(row["G_cp_eff_ideal_center_band_db"]),
                "dominant_to_residual_gain_db": float(
                    20.0 * np.log10(max(float(row["B_cp_proxy_mag"]), DB_FLOOR) / max(float(row["gamma_c_eff_ideal_center_band_mag"]), DB_FLOOR))
                ),
                "dominant_db": float(db20(float(row["B_cp_proxy_mag"]))),
                "residual_db": float(db20(float(row["gamma_c_eff_ideal_center_band_mag"]))),
            },
            "lp_raw": {
                "suppression_gain_db": float(row["G_lp_gamma_x_db"]),
                "dominant_to_residual_gain_db": float(row["G_lp_sys_db"]),
                "dominant_db": float(db20(float(row["B_lp_sys_mag"]))),
                "residual_db": float(db20(float(row["lp_residual_mag"]))),
            },
            "lp_metal_norm": {
                "suppression_gain_db": float(
                    20.0 * np.log10(max(float(row["B_mag"]), DB_FLOOR) / max(float(row["gamma_x_metal_band_mag"]), DB_FLOOR))
                ),
                "dominant_to_residual_gain_db": float(
                    20.0 * np.log10(max(float(row["B_lp_sys_mag"]), DB_FLOOR) / max(float(row["gamma_x_metal_band_mag"]), DB_FLOOR))
                ),
                "dominant_db": float(db20(float(row["B_lp_sys_mag"]))),
                "residual_db": float(db20(float(row["gamma_x_metal_band_mag"]))),
            },
        }

        for branch_id in BRANCH_ORDER:
            metric_row = branch_map[branch_id]
            rows.append(
                {
                    "material": material,
                    "theta_deg": theta_deg,
                    "branch_id": branch_id,
                    "branch_label": BRANCH_LABELS[branch_id],
                    **metric_row,
                }
            )

    return pd.DataFrame(rows)


def plot_metric(
    plot_df: pd.DataFrame,
    metric_col: str,
    ylabel: str,
    title: str,
    output_path: Path,
) -> None:
    fig, axes = plt.subplots(
        1,
        len(MATERIAL_ORDER),
        figsize=(17, 5.2),
        sharey=True,
        constrained_layout=True,
    )

    for ax, material in zip(axes, MATERIAL_ORDER):
        sub = plot_df[plot_df["material"] == material].copy()
        for branch_id in BRANCH_ORDER:
            branch = sub[sub["branch_id"] == branch_id].sort_values("theta_deg")
            ax.plot(
                branch["theta_deg"],
                branch[metric_col],
                color=BRANCH_COLORS[branch_id],
                linestyle=BRANCH_LINESTYLES[branch_id],
                marker=BRANCH_MARKERS[branch_id],
                linewidth=2.0,
                markersize=5.0,
                label=BRANCH_LABELS[branch_id],
            )

        ax.set_title(material.capitalize())
        ax.set_xlabel("Theta (deg)")
        ax.grid(True, alpha=0.25, linewidth=0.8)

    axes[0].set_ylabel(ylabel)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=3, loc="upper center", frameon=False, bbox_to_anchor=(0.5, 1.10))
    fig.suptitle(title, fontsize=14, y=1.18)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def write_markdown(output_dir: Path, repo_root: Path) -> None:
    md_path = output_dir / "CORRECTED_BRANCH_COMPARISON_PLOTS.md"
    lines = [
        "# Corrected Branch Comparison Plots",
        "",
        f"Execution date: `{EXECUTION_DATE}`",
        "",
        "## Scope",
        "",
        "- Baseline source: locked `stage4f_raw_primary_full.csv`",
        "- Corrected CP branch: A1 ideal-target material-specific replay",
        "- Corrected LP branch: same-angle metal-normalized replay",
        "- Materials plotted: `concrete`, `glass`, `wood`",
        "",
        "## Branches",
        "",
        "- `Ideal`",
        "- `CP raw`",
        "- `CP eff locked`",
        "- `CP eff corrected`",
        "- `LP raw`",
        "- `LP metal norm`",
        "",
        "## Outputs",
        "",
        f"- Plot data CSV: `{(output_dir / 'corrected_branch_comparison_plot_data.csv').relative_to(repo_root)}`",
        f"- Suppression gain comparison: `{(output_dir / 'corrected_suppression_gain.png').relative_to(repo_root)}`",
        f"- Dominant-to-residual gain comparison: `{(output_dir / 'corrected_dominant_to_residual_gain.png').relative_to(repo_root)}`",
        f"- Dominant comparison: `{(output_dir / 'corrected_dominant_db.png').relative_to(repo_root)}`",
        f"- Residual comparison: `{(output_dir / 'corrected_residual_db.png').relative_to(repo_root)}`",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_argparser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    stage4f = pd.read_csv(args.stage4f_full)
    stage4f = stage4f[stage4f["material"].isin(MATERIAL_ORDER)].copy()
    stage4f = stage4f.sort_values(["material", "theta_deg"]).reset_index(drop=True)

    cp_eff_corrected = pd.read_csv(args.cp_eff_corrected)
    cp_eff_corrected = cp_eff_corrected[cp_eff_corrected["material"].isin(MATERIAL_ORDER)].copy()

    lp_metal = pd.read_csv(args.lp_metal)
    lp_metal = lp_metal[lp_metal["material"].isin(MATERIAL_ORDER)].copy()

    plot_df = build_plot_df(stage4f, cp_eff_corrected, lp_metal)
    plot_data_path = output_dir / "corrected_branch_comparison_plot_data.csv"
    plot_df.to_csv(plot_data_path, index=False)

    plot_metric(
        plot_df=plot_df,
        metric_col="suppression_gain_db",
        ylabel="Gain (dB)",
        title="Suppression Gain Comparison",
        output_path=output_dir / "corrected_suppression_gain.png",
    )
    plot_metric(
        plot_df=plot_df,
        metric_col="dominant_to_residual_gain_db",
        ylabel="Gain (dB)",
        title="Dominant-to-Residual Gain Comparison",
        output_path=output_dir / "corrected_dominant_to_residual_gain.png",
    )
    plot_metric(
        plot_df=plot_df,
        metric_col="dominant_db",
        ylabel="Magnitude (dB)",
        title="Dominant Magnitude Comparison",
        output_path=output_dir / "corrected_dominant_db.png",
    )
    plot_metric(
        plot_df=plot_df,
        metric_col="residual_db",
        ylabel="Magnitude (dB)",
        title="Residual Magnitude Comparison",
        output_path=output_dir / "corrected_residual_db.png",
    )
    write_markdown(output_dir=output_dir, repo_root=repo_root)

    print(f"Wrote {plot_data_path}")
    print(f"Wrote {output_dir / 'corrected_suppression_gain.png'}")
    print(f"Wrote {output_dir / 'corrected_dominant_to_residual_gain.png'}")
    print(f"Wrote {output_dir / 'corrected_dominant_db.png'}")
    print(f"Wrote {output_dir / 'corrected_residual_db.png'}")
    print(f"Wrote {output_dir / 'CORRECTED_BRANCH_COMPARISON_PLOTS.md'}")


if __name__ == "__main__":
    main()
