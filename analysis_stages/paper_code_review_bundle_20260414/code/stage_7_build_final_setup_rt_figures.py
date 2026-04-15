# Consolidated review copy for paper-pipeline code assessment.
# Stage: 7
# Role: Export final-setup R/T figures for PEC and material cases, with paired CSVs.

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


MATERIALS = ["concrete", "glass", "wood"]
MATERIAL_LABELS = {
    "pec": "PEC",
    "concrete": "Concrete",
    "glass": "Glass",
    "wood": "Wood",
}
BRANCH_COLORS = {"TE": "#ea580c", "TM": "#2563eb"}
QUANTITY_STYLE = {"R": "-", "T": "--"}


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export final-setup R/T figures and paired CSVs."
    )
    repo_root = Path(__file__).resolve().parents[3]
    parser.add_argument(
        "--linear-truth",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "paper_code_review_bundle_20260414"
        / "data"
        / "stage_1"
        / "truth_table_linear_locked.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root / "paper_final_analysis_sequence" / "figures",
    )
    return parser


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_bool(series: pd.Series) -> pd.Series:
    lowered = series.astype(str).str.strip().str.lower()
    return lowered.isin({"true", "1", "yes"})


def mag_to_db(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    safe = np.maximum(arr, 1e-12)
    return 20.0 * np.log10(safe)


def build_rt_long(df: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for _, row in df.iterrows():
        theta = float(row["theta_deg"])
        material = str(row["material"]).lower()
        for branch in ("TE", "TM"):
            branch_flag = bool(row[f"use_for_main_claim_{branch}"])
            records.append(
                {
                    "material": material,
                    "theta_deg": theta,
                    "quantity": "R",
                    "branch": branch,
                    "magnitude": float(row[f"R_{branch}_locked_mag"]),
                    "magnitude_db": float(mag_to_db([row[f"R_{branch}_locked_mag"]])[0]),
                    "use_for_main_claim_branch": branch_flag,
                    "shared_use_for_main_claim": bool(row["use_for_main_claim"]),
                    "truth_region_branch": row[f"truth_region_{branch}"],
                }
            )
            records.append(
                {
                    "material": material,
                    "theta_deg": theta,
                    "quantity": "T",
                    "branch": branch,
                    "magnitude": float(row[f"T_{branch}_mag"]),
                    "magnitude_db": float(mag_to_db([row[f"T_{branch}_mag"]])[0]),
                    "use_for_main_claim_branch": branch_flag,
                    "shared_use_for_main_claim": bool(row["use_for_main_claim"]),
                    "truth_region_branch": row[f"truth_region_{branch}"],
                }
            )
    return (
        pd.DataFrame(records)
        .sort_values(["material", "branch", "quantity", "theta_deg"])
        .reset_index(drop=True)
    )


def export_pec_figure(rt_df: pd.DataFrame, csv_dir: Path, fig_dir: Path) -> tuple[Path, Path]:
    pec = rt_df[rt_df["material"] == "pec"].copy()
    csv_path = csv_dir / "fig5_pec_final_setup_rt_vs_angle.csv"
    pec.to_csv(csv_path, index=False)

    fig, ax = plt.subplots(1, 1, figsize=(7.2, 4.8))
    for branch in ("TE", "TM"):
        for quantity in ("R", "T"):
            sub = pec[(pec["branch"] == branch) & (pec["quantity"] == quantity)].sort_values("theta_deg")
            ax.plot(
                sub["theta_deg"],
                sub["magnitude"],
                QUANTITY_STYLE[quantity],
                color=BRANCH_COLORS[branch],
                lw=1.9,
                marker="o" if quantity == "R" else None,
                label=f"{quantity}_{branch}",
            )
    ax.set_title("PEC: Final Setup R/T")
    ax.set_xlabel("Incident angle [deg]")
    ax.set_ylabel("Magnitude")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig_path = fig_dir / "fig5_pec_final_setup_rt_vs_angle.png"
    fig.savefig(fig_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return csv_path, fig_path


def export_material_figure(rt_df: pd.DataFrame, csv_dir: Path, fig_dir: Path) -> tuple[Path, Path]:
    mat = rt_df[rt_df["material"].isin(MATERIALS)].copy()
    csv_path = csv_dir / "fig6_material_final_setup_rt_vs_angle.csv"
    mat.to_csv(csv_path, index=False)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub_mat = mat[mat["material"] == material].copy()
        for branch in ("TE", "TM"):
            for quantity in ("R", "T"):
                sub = sub_mat[(sub_mat["branch"] == branch) & (sub_mat["quantity"] == quantity)].sort_values("theta_deg")
                ax.plot(
                    sub["theta_deg"],
                    sub["magnitude"],
                    QUANTITY_STYLE[quantity],
                    color=BRANCH_COLORS[branch],
                    lw=1.8,
                    marker="o" if quantity == "R" else None,
                    label=f"{quantity}_{branch}" if idx == 0 else None,
                )
        ax.set_title(f"{MATERIAL_LABELS[material]}: Final Setup R/T")
        ax.set_xlabel("Incident angle [deg]")
        ax.grid(True, alpha=0.25)
        if idx == 0:
            ax.set_ylabel("Magnitude")
            ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig_path = fig_dir / "fig6_material_final_setup_rt_vs_angle.png"
    fig.savefig(fig_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return csv_path, fig_path


def main() -> None:
    args = build_argparser().parse_args()
    out_dir = ensure_dir(args.output_dir.resolve())
    csv_dir = ensure_dir(out_dir / "csv")
    fig_dir = out_dir

    truth = pd.read_csv(args.linear_truth)
    truth["material"] = truth["material"].astype(str).str.lower()
    truth["use_for_main_claim"] = normalize_bool(truth["use_for_main_claim"])
    truth["use_for_main_claim_TE"] = normalize_bool(truth["use_for_main_claim_TE"])
    truth["use_for_main_claim_TM"] = normalize_bool(truth["use_for_main_claim_TM"])

    rt_df = build_rt_long(truth)
    pec_csv, pec_fig = export_pec_figure(rt_df, csv_dir, fig_dir)
    mat_csv, mat_fig = export_material_figure(rt_df, csv_dir, fig_dir)

    summary = out_dir / "FIGURE_EXPORT_RT_SUMMARY_20260415.md"
    summary.write_text(
        "\n".join(
            [
                "# Final-Setup R/T Figure Export Summary",
                "",
                "- source: Stage 1 locked linear truth",
                "- reflection branch: `R_*_locked_mag`",
                "- transmission branch: `T_*_mag`",
                "",
                "## Outputs",
                "",
                f"- `{pec_fig.name}`",
                f"- `{mat_fig.name}`",
                f"- `csv/{pec_csv.name}`",
                f"- `csv/{mat_csv.name}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print("Wrote final-setup R/T figures and paired CSVs.")


if __name__ == "__main__":
    main()
