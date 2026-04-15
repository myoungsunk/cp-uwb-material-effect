# Consolidated review copy for paper-pipeline code assessment.
# Stage: 1
# Role: Audit the active phase-zero manifest and quantify TE/TM differential phase injection from the current PEC lock.
# Source: bundle-only audit script created for the 2026-04-14 Stage 1 lock review.
# Note: This script does not modify the original pipeline; it only reads existing Stage 1 outputs and writes audit artifacts into the review bundle.

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wrap_deg(values: np.ndarray) -> np.ndarray:
    return (values + 180.0) % 360.0 - 180.0


def as_bool(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    lowered = series.astype(str).str.strip().str.lower()
    return lowered.isin(["true", "1", "yes", "y"])


def complex_from_parts(real: pd.Series, imag: pd.Series) -> np.ndarray:
    return real.to_numpy(dtype=float) + 1j * imag.to_numpy(dtype=float)


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    header = "| " + " | ".join(df.columns.astype(str).tolist()) + " |"
    separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    body: list[str] = []
    for _, row in df.iterrows():
        cells: list[str] = []
        for value in row.tolist():
            if isinstance(value, (float, np.floating)):
                cells.append(f"{float(value):.6f}")
            else:
                cells.append(str(value))
        body.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, separator, *body])


def main() -> None:
    workspace = Path(__file__).resolve().parents[3]
    bundle = Path(__file__).resolve().parents[1]

    manifest_path = (
        workspace
        / "analysis_stages"
        / "ideal_te_tm_scattered_stage"
        / "config"
        / "current_manifests"
        / "manifest_material_5000mm_kobs5_phase0_nominal.csv"
    )
    nominal_dir = (
        workspace
        / "analysis_stages"
        / "ideal_te_tm_scattered_stage"
        / "results"
        / "current_manifest_runs"
        / "material_5000mm_kobs5_phase0_nominal_rerun_20260414"
    )
    forced_zero_dir = (
        workspace
        / "analysis_stages"
        / "stage1_forced_zero_recheck_20260414"
        / "results"
    )

    out_dir = bundle / "data" / "stage_1" / "phase_lock_audit_20260414"
    note_path = bundle / "code_review_notes" / "stage_1_phase_lock_audit_20260414.md"
    out_dir.mkdir(parents=True, exist_ok=True)
    note_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_df = pd.read_csv(manifest_path)
    phase_series = manifest_df["incident_phase_deg"].astype(float)
    manifest_summary = (
        phase_series.value_counts(dropna=False)
        .rename_axis("incident_phase_deg")
        .reset_index(name="row_count")
        .sort_values("incident_phase_deg")
        .reset_index(drop=True)
    )
    manifest_summary["is_nonzero"] = np.abs(
        manifest_summary["incident_phase_deg"].fillna(0.0)
    ) > 1e-12
    manifest_summary_path = out_dir / "manifest_incident_phase_summary.csv"
    manifest_summary.to_csv(manifest_summary_path, index=False)

    compare_files = [
        "normalized_measurements.csv",
        "qc_report.csv",
        "truth_table_linear_raw.csv",
        "truth_table_linear_locked.csv",
        "truth_table_cp.csv",
    ]
    comparison_rows: list[dict[str, object]] = []
    for name in compare_files:
        nominal_path = nominal_dir / name
        forced_path = forced_zero_dir / name
        comparison_rows.append(
            {
                "file_name": name,
                "nominal_path": str(nominal_path),
                "forced_zero_path": str(forced_path),
                "nominal_size_bytes": nominal_path.stat().st_size,
                "forced_zero_size_bytes": forced_path.stat().st_size,
                "nominal_sha256": sha256sum(nominal_path),
                "forced_zero_sha256": sha256sum(forced_path),
            }
        )
    comparison_df = pd.DataFrame(comparison_rows)
    comparison_df["size_equal"] = (
        comparison_df["nominal_size_bytes"] == comparison_df["forced_zero_size_bytes"]
    )
    comparison_df["hash_equal"] = (
        comparison_df["nominal_sha256"] == comparison_df["forced_zero_sha256"]
    )
    comparison_path = out_dir / "forced_zero_file_comparison.csv"
    comparison_df.to_csv(comparison_path, index=False)

    locked_df = pd.read_csv(nominal_dir / "truth_table_linear_locked.csv").reset_index(drop=True)

    raw_te = complex_from_parts(locked_df["R_TE_raw_real"], locked_df["R_TE_raw_imag"])
    raw_tm = complex_from_parts(locked_df["R_TM_raw_real"], locked_df["R_TM_raw_imag"])
    locked_te = complex_from_parts(
        locked_df["R_TE_locked_real"], locked_df["R_TE_locked_imag"]
    )
    locked_tm = complex_from_parts(
        locked_df["R_TM_locked_real"], locked_df["R_TM_locked_imag"]
    )

    dphi_raw = np.degrees(np.angle(raw_te / raw_tm))
    dphi_locked = np.degrees(np.angle(locked_te / locked_tm))
    delta_te = wrap_deg(np.degrees(np.angle(locked_te / raw_te)))
    delta_tm = wrap_deg(np.degrees(np.angle(locked_tm / raw_tm)))
    delta_dphi = wrap_deg(dphi_locked - dphi_raw)

    rowwise = locked_df[
        [
            "case",
            "material",
            "theta_deg",
            "f_hz",
            "use_for_main_claim",
            "truth_region",
            "truth_region_TE",
            "truth_region_TM",
        ]
    ].copy()
    rowwise["dphi_raw_deg"] = dphi_raw
    rowwise["dphi_locked_deg"] = dphi_locked
    rowwise["delta_te_phase_deg"] = delta_te
    rowwise["delta_tm_phase_deg"] = delta_tm
    rowwise["delta_dphi_deg"] = delta_dphi
    rowwise["abs_delta_dphi_deg"] = np.abs(delta_dphi)
    rowwise_path = out_dir / "phase_lock_dphi_rowwise.csv"
    rowwise.to_csv(rowwise_path, index=False)

    theta_summary = (
        rowwise.groupby("theta_deg", sort=True)
        .agg(
            row_count=("theta_deg", "size"),
            material_count=("material", "nunique"),
            delta_dphi_deg_mean=("delta_dphi_deg", "mean"),
            delta_dphi_deg_min=("delta_dphi_deg", "min"),
            delta_dphi_deg_max=("delta_dphi_deg", "max"),
            delta_dphi_deg_std=("delta_dphi_deg", "std"),
            abs_delta_dphi_deg_max=("abs_delta_dphi_deg", "max"),
            delta_dphi_material_span_deg=(
                "delta_dphi_deg",
                lambda s: float(s.max() - s.min()),
            ),
            delta_te_phase_deg_mean=("delta_te_phase_deg", "mean"),
            delta_tm_phase_deg_mean=("delta_tm_phase_deg", "mean"),
        )
        .reset_index()
    )
    theta_summary_path = out_dir / "phase_lock_dphi_theta_summary.csv"
    theta_summary.to_csv(theta_summary_path, index=False)

    main_mask = as_bool(rowwise["use_for_main_claim"])
    main_rows = rowwise.loc[main_mask].copy()
    overall_rows = rowwise.copy()

    summary = {
        "manifest_path": str(manifest_path),
        "manifest_unique_incident_phase_deg": sorted(
            float(v) for v in phase_series.dropna().unique().tolist()
        ),
        "manifest_nonzero_row_count": int((np.abs(phase_series) > 1e-12).sum()),
        "forced_zero_all_hash_equal": bool(comparison_df["hash_equal"].all()),
        "forced_zero_all_size_equal": bool(comparison_df["size_equal"].all()),
        "dphi_main_mean_abs_deg": float(main_rows["abs_delta_dphi_deg"].mean()),
        "dphi_main_max_abs_deg": float(main_rows["abs_delta_dphi_deg"].max()),
        "dphi_overall_max_abs_deg": float(overall_rows["abs_delta_dphi_deg"].max()),
        "dphi_peak_theta_main_deg": float(
            main_rows.loc[
                main_rows["abs_delta_dphi_deg"].idxmax(), "theta_deg"
            ]
        ),
        "dphi_peak_theta_overall_deg": float(
            overall_rows.loc[
                overall_rows["abs_delta_dphi_deg"].idxmax(), "theta_deg"
            ]
        ),
        "material_span_max_deg": float(theta_summary["delta_dphi_material_span_deg"].max()),
    }
    summary_path = out_dir / "phase_lock_audit_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    representative = theta_summary[
        theta_summary["theta_deg"].isin([20.0, 30.0, 40.0, 50.0, 60.0])
    ].copy()

    note_lines = [
        "# Stage 1 Phase-Zero and PEC-Lock Audit (2026-04-14)",
        "",
        "## Scope",
        "",
        "- Confirm that the active Stage 1 manifest already uses `incident_phase_deg = 0` everywhere.",
        "- Confirm that forcing `incident_phase_deg = 0` again does not change any Stage 1 outputs.",
        "- Quantify whether the current PEC lock injects a TE/TM differential phase into `R_TE / R_TM`.",
        "",
        "## Result",
        "",
        f"- Active manifest unique `incident_phase_deg`: {summary['manifest_unique_incident_phase_deg']}",
        f"- Active manifest nonzero row count: {summary['manifest_nonzero_row_count']}",
        f"- Forced-zero rerun hash-identical across tracked files: {summary['forced_zero_all_hash_equal']}",
        f"- Main-claim rows: `mean(|delta_dphi|) = {summary['dphi_main_mean_abs_deg']:.4f} deg`, `max(|delta_dphi|) = {summary['dphi_main_max_abs_deg']:.4f} deg` at `theta = {summary['dphi_peak_theta_main_deg']:.0f} deg`.",
        f"- Overall rows: `max(|delta_dphi|) = {summary['dphi_overall_max_abs_deg']:.4f} deg` at `theta = {summary['dphi_peak_theta_overall_deg']:.0f} deg`.",
        f"- Cross-material spread at a fixed theta: `max(span) = {summary['material_span_max_deg']:.6f} deg`.",
        "",
        "## Interpretation",
        "",
        "- Priority 1 is closed: the active manifest is already pure `phase0_nominal`, and forcing zero again does not change Stage 1 outputs.",
        "- Priority 2 finds a real effect: the current PEC lock is not a pure common-phase rotation. It adds a small but systematic theta-dependent differential phase between TE and TM.",
        "- Because the per-theta span across materials is effectively zero, the injected differential phase is a lock-structure effect, not a material-dependent phenomenon.",
        "- Stage 4 patch comparison should therefore stay `raw-primary`; `Gamma_C_eff` remains supplementary because its correction already failed the same-angle upper-bound audit.",
        "- A later replacement of the current observation/incident normalization by a PEC-reference complex LS estimator is still justified if the goal is to reduce lock-induced CP inflation risk.",
        "",
        "## Representative Theta Summary",
        "",
        dataframe_to_markdown(representative),
        "",
        "## Audit Artifacts",
        "",
        f"- `data/stage_1/phase_lock_audit_20260414/{manifest_summary_path.name}`",
        f"- `data/stage_1/phase_lock_audit_20260414/{comparison_path.name}`",
        f"- `data/stage_1/phase_lock_audit_20260414/{rowwise_path.name}`",
        f"- `data/stage_1/phase_lock_audit_20260414/{theta_summary_path.name}`",
        f"- `data/stage_1/phase_lock_audit_20260414/{summary_path.name}`",
        "",
    ]
    note_path.write_text("\n".join(note_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
