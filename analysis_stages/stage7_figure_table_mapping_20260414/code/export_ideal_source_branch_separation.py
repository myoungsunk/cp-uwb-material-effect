from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


MATERIALS = ["concrete", "glass", "wood"]
MATERIAL_LABELS = {"concrete": "Concrete", "glass": "Glass", "wood": "Wood"}
MATERIAL_COLORS = {"concrete": "#dc2626", "glass": "#2563eb", "wood": "#059669"}


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export the ideal-source CP branch-separation figure and paired CSV."
    )
    repo_root = Path(__file__).resolve().parents[3]
    parser.add_argument(
        "--cp-truth",
        type=Path,
        default=repo_root
        / "analysis_stages"
        / "paper_code_review_bundle_20260414"
        / "data"
        / "stage_2"
        / "sameflip_alias_20260415"
        / "truth_table_cp_shared_common_sameflip.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root / "paper_final_analysis_sequence" / "figures",
    )
    return parser


def normalize_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    lowered = series.astype(str).str.strip().str.lower()
    return lowered.isin({"true", "1", "yes"})


def mag_to_db(values: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    safe = np.maximum(arr, 1e-12)
    return 20.0 * np.log10(safe)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def main() -> None:
    args = build_argparser().parse_args()
    output_dir = ensure_dir(args.output_dir.resolve())
    csv_dir = ensure_dir(output_dir / "csv")

    cp_truth = pd.read_csv(args.cp_truth)
    cp = cp_truth[cp_truth["material"].isin(MATERIALS)].copy()
    cp["cp_use_for_main_claim"] = normalize_bool(cp["cp_use_for_main_claim"])
    cp["cp_use_for_caution_only"] = normalize_bool(cp["cp_use_for_caution_only"])
    cp["Gamma_same_db"] = mag_to_db(cp["Gamma_same_mag"])
    cp["Gamma_flip_db"] = mag_to_db(cp["Gamma_flip_mag"])
    cp["ideal_branch_separation_db"] = mag_to_db(cp["Gamma_flip_mag"] / cp["Gamma_same_mag"])

    fig7_df = cp[
        [
            "material",
            "theta_deg",
            "Gamma_same_mag",
            "Gamma_flip_mag",
            "Gamma_same_db",
            "Gamma_flip_db",
            "ideal_branch_separation_db",
            "cp_truth_region",
            "cp_truth_region_reason",
            "cp_use_for_main_claim",
            "cp_use_for_caution_only",
        ]
    ].sort_values(["material", "theta_deg"]).reset_index(drop=True)

    fig7_csv = csv_dir / "fig7_ideal_cp_branch_separation.csv"
    fig7_df.to_csv(fig7_csv, index=False)

    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    for material in MATERIALS:
        sub = fig7_df[fig7_df["material"] == material].sort_values("theta_deg")
        main = sub[sub["cp_use_for_main_claim"]]
        caution = sub[~sub["cp_use_for_main_claim"]]

        ax.plot(
            main["theta_deg"],
            main["ideal_branch_separation_db"],
            "o-",
            lw=2.0,
            color=MATERIAL_COLORS[material],
            label=MATERIAL_LABELS[material],
        )
        if not caution.empty:
            ax.plot(
                caution["theta_deg"],
                caution["ideal_branch_separation_db"],
                "o--",
                lw=1.5,
                color=MATERIAL_COLORS[material],
                alpha=0.45,
            )

    ax.set_title("Ideal CP Branch Separation")
    ax.set_xlabel("Incident angle [deg]")
    ax.set_ylabel(r"$20 \log_{10}(|\Gamma_{flip}| / |\Gamma_{same}|)$ [dB]")
    ax.grid(True, alpha=0.28)
    ax.legend()
    ax.text(
        0.99,
        0.02,
        "Solid: main claim range\nDashed: caution/excluded",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": "white",
            "alpha": 0.85,
            "edgecolor": "#d1d5db",
        },
    )
    fig.tight_layout()
    fig_path = output_dir / "fig7_ideal_cp_branch_separation.png"
    fig.savefig(fig_path, dpi=160, bbox_inches="tight")
    plt.close(fig)

    summary_lines = [
        "# Ideal CP Branch Separation Export Summary",
        "",
        "- source: Stage 2 same/flip-safe ideal CP truth",
        "- metric: `20 log10(|Gamma_flip| / |Gamma_same|)`",
        "- interpretation:",
        "  - larger value = stronger dominant-to-residual CP separation",
        "  - this is the cleanest stage-local ideal metric because it uses only Stage 2 outputs",
        "- caution:",
        "  - this is an ideal CP branch-separation metric, not the final system suppression gain",
        "",
        "## Outputs",
        "",
        "- `fig7_ideal_cp_branch_separation.png`",
        "- `csv/fig7_ideal_cp_branch_separation.csv`",
    ]
    (output_dir / "FIGURE_EXPORT_CP_BRANCH_SUMMARY_20260415.md").write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
    )

    print("Wrote fig7 ideal CP branch-separation plot and CSV.")


if __name__ == "__main__":
    main()
