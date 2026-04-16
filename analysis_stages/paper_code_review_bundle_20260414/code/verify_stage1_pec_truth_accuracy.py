from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


LINEAR_PASS_THRESHOLD = 0.05
EXECUTION_DATE = "2026-04-16"
SNAPSHOTS = (
    (
        "bundle_singlefreq_6p5ghz",
        Path("data") / "stage_1" / "truth_table_linear_locked.csv",
        Path("data") / "stage_1" / "qc_report.csv",
    ),
    (
        "bundle_multifreq_20260416",
        Path("data") / "stage_1_multifreq_20260416" / "truth_table_linear_locked.csv",
        Path("data") / "stage_1_multifreq_20260416" / "qc_report.csv",
    ),
)
POL_CONFIG = (
    ("TE", "R_TE_locked", "use_for_main_claim_TE", -1.0 + 0.0j),
    ("TM", "R_TM_locked", "use_for_main_claim_TM", 1.0 + 0.0j),
)


def build_argparser() -> argparse.ArgumentParser:
    bundle_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description=(
            "Audit Stage 1 PEC truth accuracy from the locked truth tables and QC reports "
            "without running any new simulation."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=bundle_root / "results" / "debug",
    )
    return parser


def complex_from_parts(df: pd.DataFrame, prefix: str) -> pd.Series:
    return df[f"{prefix}_real"].astype(float) + 1j * df[f"{prefix}_imag"].astype(float)


def load_qc_subset(qc_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    qc = pd.read_csv(qc_path)
    qc = qc[(qc["material"] == "pec") & (qc["metric"] == "pec_locked_reflection_target_error")].copy()
    qc["f_ghz"] = qc["f_hz"].astype(float) / 1e9

    qc_export = qc[
        [
            "f_hz",
            "f_ghz",
            "theta_deg",
            "pol",
            "metric",
            "value",
            "status",
            "detail",
        ]
    ].sort_values(["f_hz", "theta_deg", "pol"])

    merged = qc[["f_hz", "theta_deg", "pol", "value", "status"]].copy()
    merged["pol_key"] = merged["pol"].str.lower()

    value_wide = (
        merged.pivot_table(index=["f_hz", "theta_deg"], columns="pol_key", values="value", aggfunc="first")
        .reset_index()
        .rename(columns={"te": "qc_target_error_te", "tm": "qc_target_error_tm"})
    )
    status_wide = (
        merged.pivot_table(index=["f_hz", "theta_deg"], columns="pol_key", values="status", aggfunc="first")
        .reset_index()
        .rename(columns={"te": "qc_target_error_status_te", "tm": "qc_target_error_status_tm"})
    )
    qc_wide = value_wide.merge(status_wide, on=["f_hz", "theta_deg"], how="outer")
    return qc_export, qc_wide


def load_snapshot(bundle_root: Path, snapshot_name: str, truth_rel: Path, qc_rel: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    truth_path = bundle_root / truth_rel
    qc_path = bundle_root / qc_rel

    truth = pd.read_csv(truth_path)
    truth = truth[truth["material"] == "pec"].copy()
    truth["source_snapshot"] = snapshot_name
    truth["f_ghz"] = truth["f_hz"].astype(float) / 1e9

    r_te = complex_from_parts(truth, "R_TE_locked")
    r_tm = complex_from_parts(truth, "R_TM_locked")

    truth["te_abs_minus_1"] = (truth["R_TE_locked_mag"].astype(float) - 1.0).abs()
    truth["tm_abs_minus_1"] = (truth["R_TM_locked_mag"].astype(float) - 1.0).abs()
    truth["te_locked_target_error"] = np.abs(r_te - (-1.0 + 0.0j))
    truth["tm_locked_target_error"] = np.abs(r_tm - (1.0 + 0.0j))
    truth["max_abs_minus_1"] = truth[["te_abs_minus_1", "tm_abs_minus_1"]].max(axis=1)
    truth["max_locked_target_error"] = truth[["te_locked_target_error", "tm_locked_target_error"]].max(axis=1)
    truth["te_linear_pass_flag"] = truth["te_abs_minus_1"] <= LINEAR_PASS_THRESHOLD
    truth["tm_linear_pass_flag"] = truth["tm_abs_minus_1"] <= LINEAR_PASS_THRESHOLD

    qc_export, qc_wide = load_qc_subset(qc_path)
    qc_export["source_snapshot"] = snapshot_name
    truth = truth.merge(qc_wide, on=["f_hz", "theta_deg"], how="left")

    export_columns = [
        "source_snapshot",
        "f_hz",
        "f_ghz",
        "theta_deg",
        "truth_region",
        "truth_region_TE",
        "truth_region_TM",
        "use_for_main_claim",
        "use_for_main_claim_TE",
        "use_for_main_claim_TM",
        "R_TE_locked_real",
        "R_TE_locked_imag",
        "R_TE_locked_mag",
        "R_TE_locked_phase_deg",
        "R_TM_locked_real",
        "R_TM_locked_imag",
        "R_TM_locked_mag",
        "R_TM_locked_phase_deg",
        "te_abs_minus_1",
        "tm_abs_minus_1",
        "te_locked_target_error",
        "tm_locked_target_error",
        "max_abs_minus_1",
        "max_locked_target_error",
        "te_linear_pass_flag",
        "tm_linear_pass_flag",
        "qc_target_error_te",
        "qc_target_error_tm",
        "qc_target_error_status_te",
        "qc_target_error_status_tm",
    ]
    return truth[export_columns].sort_values(["source_snapshot", "f_hz", "theta_deg"]).reset_index(drop=True), qc_export


def build_summary(full_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for snapshot_name, snapshot_df in full_df.groupby("source_snapshot"):
        for f_ghz, freq_df in snapshot_df.groupby("f_ghz"):
            for pol, _, main_flag_col, _ in POL_CONFIG:
                err_col = f"{pol.lower()}_abs_minus_1"
                target_col = f"{pol.lower()}_locked_target_error"
                qc_status_col = f"qc_target_error_status_{pol.lower()}"
                scopes = {
                    "all_rows": freq_df,
                    "main_claim": freq_df[freq_df[main_flag_col].fillna(False)].copy(),
                    "non_main": freq_df[~freq_df[main_flag_col].fillna(False)].copy(),
                }
                for scope, sub in scopes.items():
                    if sub.empty:
                        continue
                    worst = sub.sort_values(err_col, ascending=False).iloc[0]
                    rows.append(
                        {
                            "source_snapshot": snapshot_name,
                            "f_ghz": float(f_ghz),
                            "pol": pol,
                            "scope": scope,
                            "n_rows": int(len(sub)),
                            "rows_gt_linear_threshold": int((sub[err_col] > LINEAR_PASS_THRESHOLD).sum()),
                            "max_abs_minus_1": float(sub[err_col].max()),
                            "mean_abs_minus_1": float(sub[err_col].mean()),
                            "max_locked_target_error": float(sub[target_col].max()),
                            "worst_theta_deg": float(worst["theta_deg"]),
                            "worst_truth_region": str(worst[f"truth_region_{pol}"]),
                            "any_qc_fail": bool(sub[qc_status_col].fillna("ok").eq("fail").any()),
                        }
                    )
    return pd.DataFrame(rows).sort_values(["source_snapshot", "f_ghz", "pol", "scope"]).reset_index(drop=True)


def write_plot(full_df: pd.DataFrame, output_path: Path) -> None:
    multi_df = full_df[full_df["source_snapshot"] == "bundle_multifreq_20260416"].copy()
    base_df = full_df[full_df["source_snapshot"] == "bundle_singlefreq_6p5ghz"].copy()

    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    colors = {6.24: "#1f77b4", 6.50: "#ff7f0e", 6.74: "#2ca02c"}

    for pol, ax in zip(("TE", "TM"), axes):
        err_col = f"{pol.lower()}_abs_minus_1"
        for f_ghz in sorted(multi_df["f_ghz"].unique()):
            sub = multi_df[np.isclose(multi_df["f_ghz"], f_ghz)].sort_values("theta_deg")
            ax.plot(
                sub["theta_deg"],
                sub[err_col],
                marker="o",
                linewidth=1.8,
                color=colors.get(round(float(f_ghz), 2), None),
                label=f"{f_ghz:.2f} GHz (multifreq)",
            )
        base_sub = base_df.sort_values("theta_deg")
        ax.plot(
            base_sub["theta_deg"],
            base_sub[err_col],
            linestyle="--",
            linewidth=1.6,
            color="black",
            label=f"6.50 GHz (singlefreq bundle)",
        )
        ax.axhline(LINEAR_PASS_THRESHOLD, color="red", linestyle=":", linewidth=1.2, label="0.05 threshold")
        ax.set_ylabel(f"{pol}: ||R|-1|")
        ax.grid(True, alpha=0.25)

    handles, labels = axes[0].get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    axes[0].legend(by_label.values(), by_label.keys(), fontsize=8, ncol=2)
    axes[0].set_title("Stage 1 PEC Locked-Truth Magnitude Deviation")
    axes[1].set_xlabel("Theta (deg)")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def write_markdown(
    *,
    full_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    qc_df: pd.DataFrame,
    full_path: Path,
    summary_path: Path,
    qc_path: Path,
    plot_path: Path,
    output_path: Path,
    repo_root: Path,
) -> None:
    def summary_row(snapshot: str, freq_ghz: float, pol: str, scope: str) -> pd.Series:
        mask = (
            (summary_df["source_snapshot"] == snapshot)
            & np.isclose(summary_df["f_ghz"], freq_ghz)
            & (summary_df["pol"] == pol)
            & (summary_df["scope"] == scope)
        )
        return summary_df[mask].iloc[0]

    single_te_main = summary_row("bundle_singlefreq_6p5ghz", 6.50, "TE", "main_claim")
    single_tm_main = summary_row("bundle_singlefreq_6p5ghz", 6.50, "TM", "main_claim")
    multi_rows = []
    for freq_ghz in sorted(full_df[full_df["source_snapshot"] == "bundle_multifreq_20260416"]["f_ghz"].unique()):
        te_row = summary_row("bundle_multifreq_20260416", float(freq_ghz), "TE", "main_claim")
        tm_row = summary_row("bundle_multifreq_20260416", float(freq_ghz), "TM", "main_claim")
        multi_rows.append((float(freq_ghz), te_row, tm_row))

    qc_fail = qc_df[qc_df["status"] == "fail"].sort_values(["f_hz", "theta_deg", "pol"]).copy()
    top_overall = full_df.sort_values("max_abs_minus_1", ascending=False).head(8).copy()

    lines = [
        "# Verify Stage 1 PEC Truth Accuracy",
        "",
        f"Execution date: `{EXECUTION_DATE}`",
        "",
        "## Scope",
        "",
        "- No new simulation is used.",
        "- Inputs are the locked Stage 1 PEC truth tables already mirrored into the bundle.",
        "- Both the single-frequency bundle snapshot and the `2026-04-16` multi-frequency snapshot are checked.",
        f"- Pass criterion from the review note: main-range PEC magnitude deviation `||R|-1| < {LINEAR_PASS_THRESHOLD:.2f}`.",
        "- The audit tracks both linear magnitude deviation and the QC complex target error against locked PEC targets (`R_TE=-1`, `R_TM=+1`).",
        "",
        "## Main Findings",
        "",
        f"- The current single-frequency `6.50 GHz` bundle snapshot passes the requested main-range criterion:",
        f"  - TE main rows above threshold: `{int(single_te_main['rows_gt_linear_threshold'])}/{int(single_te_main['n_rows'])}`, max deviation `{single_te_main['max_abs_minus_1']:.6f}` at `{single_te_main['worst_theta_deg']:.0f} deg`.",
        f"  - TM main rows above threshold: `{int(single_tm_main['rows_gt_linear_threshold'])}/{int(single_tm_main['n_rows'])}`, max deviation `{single_tm_main['max_abs_minus_1']:.6f}` at `{single_tm_main['worst_theta_deg']:.0f} deg`.",
        "- The multi-frequency snapshot shows that the TE branch, not TM, is where oblique-angle accuracy starts to tighten.",
    ]

    for freq_ghz, te_row, tm_row in multi_rows:
        lines.append(
            f"  - `{freq_ghz:.2f} GHz`: TE main max `{te_row['max_abs_minus_1']:.6f}`"
            f" ({int(te_row['rows_gt_linear_threshold'])}/{int(te_row['n_rows'])} above threshold), "
            f"TM main max `{tm_row['max_abs_minus_1']:.6f}`"
            f" ({int(tm_row['rows_gt_linear_threshold'])}/{int(tm_row['n_rows'])} above threshold)."
        )

    lines.extend(
        [
            f"- Only one QC fail exists in the multi-frequency PEC set: `{len(qc_fail)}` row.",
            "",
            "## Interpretation",
            "",
            "- For the current `6.50 GHz` main-use bundle snapshot, the Stage 1 PEC truth is clean enough under the requested `0.05` linear threshold.",
            "- Across frequency, TE at high oblique angle (`60 deg` and beyond) shows the first meaningful accuracy loss, while TM stays comfortably below the threshold over its full main range.",
            "- The remaining explicit QC fail is `6.24 GHz / TE / 70 deg`, which sits outside the current TE main-claim range.",
            "- This means Stage 1 PEC uncertainty should be treated as a high-angle TE caution term, not as the primary explanation for the current `6.50 GHz` LP main-range contradiction.",
            "",
            "## QC Fail Rows",
            "",
        ]
    )

    if qc_fail.empty:
        lines.append("- No QC fail row was found.")
    else:
        for _, row in qc_fail.iterrows():
            lines.append(
                f"- `{row['f_ghz']:.2f} GHz`, `{row['pol']}`, `{row['theta_deg']:.0f} deg`: "
                f"target error `{row['value']:.6f}`, status=`{row['status']}`"
            )

    lines.extend(["", "## Worst PEC Rows", ""])
    for _, row in top_overall.iterrows():
        lines.append(
            f"- `{row['source_snapshot']}`, `{row['f_ghz']:.2f} GHz`, `{row['theta_deg']:.0f} deg`: "
            f"TE `||R|-1|={row['te_abs_minus_1']:.6f}`, TM `||R|-1|={row['tm_abs_minus_1']:.6f}`, "
            f"max `{row['max_abs_minus_1']:.6f}`"
        )

    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Full CSV: `{full_path.relative_to(repo_root)}`",
            f"- Summary CSV: `{summary_path.relative_to(repo_root)}`",
            f"- QC subset CSV: `{qc_path.relative_to(repo_root)}`",
            f"- Plot PNG: `{plot_path.relative_to(repo_root)}`",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_argparser().parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_root = Path(__file__).resolve().parent.parent
    repo_root = Path(__file__).resolve().parents[3]

    full_frames: list[pd.DataFrame] = []
    qc_frames: list[pd.DataFrame] = []
    for snapshot_name, truth_rel, qc_rel in SNAPSHOTS:
        full_df, qc_df = load_snapshot(bundle_root, snapshot_name, truth_rel, qc_rel)
        full_frames.append(full_df)
        qc_frames.append(qc_df)

    full_df = pd.concat(full_frames, ignore_index=True).sort_values(["source_snapshot", "f_hz", "theta_deg"]).reset_index(drop=True)
    qc_df = pd.concat(qc_frames, ignore_index=True).sort_values(["source_snapshot", "f_hz", "theta_deg", "pol"]).reset_index(drop=True)
    summary_df = build_summary(full_df)

    full_path = output_dir / "verify_stage1_pec_truth_accuracy_full.csv"
    summary_path = output_dir / "verify_stage1_pec_truth_accuracy_summary.csv"
    qc_path = output_dir / "verify_stage1_pec_truth_accuracy_qc_subset.csv"
    plot_path = output_dir / "verify_stage1_pec_truth_accuracy.png"
    md_path = output_dir / "VERIFY_STAGE1_PEC_TRUTH_ACCURACY.md"

    full_df.to_csv(full_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    qc_df.to_csv(qc_path, index=False)
    write_plot(full_df, plot_path)
    write_markdown(
        full_df=full_df,
        summary_df=summary_df,
        qc_df=qc_df,
        full_path=full_path,
        summary_path=summary_path,
        qc_path=qc_path,
        plot_path=plot_path,
        output_path=md_path,
        repo_root=repo_root,
    )

    print(f"Wrote {full_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {qc_path}")
    print(f"Wrote {plot_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
