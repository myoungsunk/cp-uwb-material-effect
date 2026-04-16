from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


MATERIAL_ORDER = ["concrete", "glass", "wood"]
BRANCH_ORDER = ["ideal", "cp_raw", "cp_eff", "lp_raw"]
BRANCH_LABELS = {
    "ideal": "Ideal",
    "cp_raw": "CP raw",
    "cp_eff": "CP eff",
    "lp_raw": "LP raw",
}
BRANCH_COLORS = {
    "ideal": "#1f77b4",
    "cp_raw": "#ff7f0e",
    "cp_eff": "#d62728",
    "lp_raw": "#2ca02c",
}
BRANCH_MARKERS = {
    "ideal": "o",
    "cp_raw": "s",
    "cp_eff": "^",
    "lp_raw": "D",
}
DB_FLOOR = 1e-12
EXECUTION_DATE = "2026-04-16"


def build_argparser() -> argparse.ArgumentParser:
    bundle_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description=(
            "Plot final Stage 4 branch metrics for ideal, CP raw, CP eff, and LP raw "
            "using the locked stage4f export."
        )
    )
    parser.add_argument(
        "--stage4f-full",
        type=Path,
        default=bundle_root / "results" / "stage4f_raw_primary_full.csv",
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


def build_plot_df(stage4f: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in stage4f.sort_values(["material", "theta_deg"]).iterrows():
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
            "cp_eff": {
                "suppression_gain_db": float(row["G_patch_eff_db"]),
                "dominant_to_residual_gain_db": float(row["G_cp_eff_sys_db"]),
                "dominant_db": float(db20(float(row["B_cp_proxy_mag"]))),
                "residual_db": float(db20(float(row["gamma_c_patch_eff_mag"]))),
            },
            "lp_raw": {
                "suppression_gain_db": float(row["G_lp_gamma_x_db"]),
                "dominant_to_residual_gain_db": float(row["G_lp_sys_db"]),
                "dominant_db": float(db20(float(row["B_lp_sys_mag"]))),
                "residual_db": float(db20(float(row["lp_residual_mag"]))),
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
        figsize=(16, 4.8),
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
    fig.legend(handles, labels, ncol=4, loc="upper center", frameon=False, bbox_to_anchor=(0.5, 1.06))
    fig.suptitle(title, fontsize=14, y=1.12)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def write_markdown(
    *,
    output_dir: Path,
    repo_root: Path,
) -> None:
    md_path = output_dir / "FINAL_BRANCH_METRICS_PLOTS.md"
    lines = [
        "# Final Branch Metrics Plots",
        "",
        f"Execution date: `{EXECUTION_DATE}`",
        "",
        "## Scope",
        "",
        "- Source table: locked `stage4f_raw_primary_full.csv`",
        "- Branches plotted: `Ideal`, `CP raw`, `CP eff`, `LP raw`",
        "- Materials plotted: `concrete`, `glass`, `wood`",
        "",
        "## Metrics",
        "",
        "- `suppression_gain_db`: Stage 4 ideal-anchor suppression gain",
        "- `dominant_to_residual_gain_db`: branch-consistent dominant-to-residual gain",
        "- `dominant_db`: branch dominant magnitude in dB",
        "- `residual_db`: branch residual magnitude in dB",
        "",
        "## Outputs",
        "",
        f"- Plot data CSV: `{(output_dir / 'final_branch_metric_plot_data.csv').relative_to(repo_root)}`",
        f"- Suppression gain plot: `{(output_dir / 'final_suppression_gain.png').relative_to(repo_root)}`",
        f"- Dominant-to-residual gain plot: `{(output_dir / 'final_dominant_to_residual_gain.png').relative_to(repo_root)}`",
        f"- Dominant plot: `{(output_dir / 'final_dominant_db.png').relative_to(repo_root)}`",
        f"- Residual plot: `{(output_dir / 'final_residual_db.png').relative_to(repo_root)}`",
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

    plot_df = build_plot_df(stage4f)
    plot_data_path = output_dir / "final_branch_metric_plot_data.csv"
    plot_df.to_csv(plot_data_path, index=False)

    plot_metric(
        plot_df=plot_df,
        metric_col="suppression_gain_db",
        ylabel="Gain (dB)",
        title="Suppression Gain",
        output_path=output_dir / "final_suppression_gain.png",
    )
    plot_metric(
        plot_df=plot_df,
        metric_col="dominant_to_residual_gain_db",
        ylabel="Gain (dB)",
        title="Dominant-to-Residual Gain",
        output_path=output_dir / "final_dominant_to_residual_gain.png",
    )
    plot_metric(
        plot_df=plot_df,
        metric_col="dominant_db",
        ylabel="Magnitude (dB)",
        title="Dominant Magnitude",
        output_path=output_dir / "final_dominant_db.png",
    )
    plot_metric(
        plot_df=plot_df,
        metric_col="residual_db",
        ylabel="Magnitude (dB)",
        title="Residual Magnitude",
        output_path=output_dir / "final_residual_db.png",
    )
    write_markdown(output_dir=output_dir, repo_root=repo_root)

    print(f"Wrote {plot_data_path}")
    print(f"Wrote {output_dir / 'final_suppression_gain.png'}")
    print(f"Wrote {output_dir / 'final_dominant_to_residual_gain.png'}")
    print(f"Wrote {output_dir / 'final_dominant_db.png'}")
    print(f"Wrote {output_dir / 'final_residual_db.png'}")
    print(f"Wrote {output_dir / 'FINAL_BRANCH_METRICS_PLOTS.md'}")


if __name__ == "__main__":
    main()
