from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


MATERIALS = ["concrete", "glass", "wood"]
RESIDUAL_FLOOR = 1e-12

BRANCH_SERIES_SPECS = [
    ("ideal_gamma_x", "Ideal residual (Gamma_X)", "ideal", "absolute_interface_truth", True, "gamma_x_ideal_mag"),
    ("patch_raw", "Patch residual raw", "patch_raw", "patch_stage_absolute_like", True, "gamma_c_patch_raw_mag"),
    ("patch_eff", "Patch residual corrected", "patch_eff", "patch_stage_absolute_like", True, "gamma_c_patch_eff_mag"),
    ("lp_gamma_x", "LP-derived residual (Gamma_X)", "lp_gamma_x", "patch_stage_absolute_like", True, "gamma_x_from_lp_mag"),
    ("lp_gamma_c", "LP-derived co-term (Gamma_C)", "lp_gamma_c", "patch_stage_absolute_like", False, "gamma_c_from_lp_mag"),
    (
        "patch_metal_floor",
        "Patch residual metal-floor",
        "patch_metal_floor",
        "metal_normalized_diagnostic",
        False,
        "gamma_hat_c_metal_floor_mag",
    ),
]

SUPPRESSION_SERIES_SPECS = [
    ("ideal", "Ideal upper bound", "ideal", "absolute_interface_truth", True, "G_ideal_db"),
    ("patch_raw", "Patch raw", "patch_raw", "patch_stage_absolute_like", True, "G_patch_raw_db"),
    ("patch_eff", "Patch corrected", "patch_eff", "patch_stage_absolute_like", True, "G_patch_eff_db"),
    ("lp_gamma_x", "LP-derived Gamma_X", "lp_gamma_x", "patch_stage_absolute_like", True, "G_lp_gamma_x_db"),
    ("lp_gamma_c", "LP-derived Gamma_C", "lp_gamma_c", "patch_stage_absolute_like", False, "G_lp_gamma_c_db"),
    (
        "patch_metal_floor",
        "Patch metal-floor",
        "patch_metal_floor",
        "metal_normalized_diagnostic",
        False,
        "G_patch_metal_floor_db",
    ),
    (
        "patch_raw_sys",
        "Patch raw (same-stage numerator)",
        "patch_raw",
        "patch_stage_self_normalized",
        False,
        "G_cp_raw_sys_db",
    ),
    (
        "patch_eff_sys",
        "Patch corrected (same-stage numerator)",
        "patch_eff",
        "patch_stage_self_normalized",
        False,
        "G_cp_eff_sys_db",
    ),
    (
        "lp_gamma_x_sys",
        "LP-derived Gamma_X (same-stage numerator)",
        "lp_gamma_x",
        "patch_stage_self_normalized",
        False,
        "G_lp_sys_db",
    ),
]


def build_argparser() -> argparse.ArgumentParser:
    bundle_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description=(
            "Build a single authoritative residual-ordering export that unifies "
            "the prior Stage 4e (3-way comparison) and Stage 4f (raw-primary view) logic."
        )
    )
    parser.add_argument(
        "--stage4c-full",
        type=Path,
        default=bundle_root
        / "data"
        / "stage_4"
        / "stage4c_same_angle_gap_audit_20260414"
        / "same_angle_gap_audit_full.csv",
    )
    parser.add_argument(
        "--stage4d-full",
        type=Path,
        default=bundle_root
        / "data"
        / "stage_4"
        / "stage4d_cp_metal_floor_audit_20260414"
        / "metal_floor_same_angle_audit.csv",
    )
    parser.add_argument(
        "--patch-lp-band",
        type=Path,
        default=bundle_root / "data" / "stage_3" / "lp" / "patch_lp_extracted.csv",
    )
    parser.add_argument(
        "--patch-cp-band",
        type=Path,
        default=bundle_root / "data" / "stage_3" / "cp" / "patch_cp_extracted.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=bundle_root / "results",
    )
    parser.add_argument(
        "--debug-dir",
        type=Path,
        default=bundle_root / "results" / "debug",
    )
    return parser


def db20_ratio(numerator: float, denominator: float) -> float:
    return float(20.0 * np.log10(max(float(numerator), RESIDUAL_FLOOR) / max(float(denominator), RESIDUAL_FLOOR)))


def suppression_gain_db(b_mag: float, residual_mag: float) -> float:
    return db20_ratio(b_mag, residual_mag)


def build_authoritative_wide(
    stage4c: pd.DataFrame,
    stage4d: pd.DataFrame,
    patch_lp: pd.DataFrame,
    patch_cp: pd.DataFrame,
) -> pd.DataFrame:
    stage4c = stage4c[stage4c["material"].isin(MATERIALS)].copy()
    stage4d = stage4d[stage4d["material"].isin(MATERIALS)].copy()
    patch_lp = patch_lp[patch_lp["material"].isin(MATERIALS)].copy()
    patch_cp = patch_cp[patch_cp["material"].isin(MATERIALS)].copy()

    keep4c = stage4c[
        [
            "material",
            "theta_deg",
            "B_mag",
            "ideal_residual_branch_mag",
            "gamma_hat_c_cp_raw_mag",
            "gamma_hat_c_cp_eff_mag",
            "G_supp_ideal_db",
            "G_patch_raw_db",
            "G_supp_patch_db",
            "Delta_G_raw_db",
            "Delta_G_db",
            "Delta_G_raw_negative",
            "Delta_G_eff_negative",
            "raw_smaller_than_ideal",
            "eff_smaller_than_ideal",
            "raw_closer_to_ideal_than_eff",
        ]
    ].rename(
        columns={
            "ideal_residual_branch_mag": "gamma_x_ideal_mag",
            "gamma_hat_c_cp_raw_mag": "gamma_c_patch_raw_mag",
            "gamma_hat_c_cp_eff_mag": "gamma_c_patch_eff_mag",
            "G_supp_ideal_db": "G_ideal_db",
            "G_supp_patch_db": "G_patch_eff_db",
            "Delta_G_raw_db": "Delta_ideal_minus_raw_db",
            "Delta_G_db": "Delta_ideal_minus_eff_db",
            "Delta_G_raw_negative": "delta_raw_negative",
            "Delta_G_eff_negative": "delta_eff_negative",
        }
    )

    keep4d = stage4d[
        [
            "material",
            "theta_deg",
            "gamma_hat_c_metal_floor_mag",
            "G_patch_metal_floor_db",
            "Delta_G_ideal_minus_metal_floor_db",
            "negative_delta_rows",
            "metal_floor_gt_ideal_residual",
        ]
    ].rename(columns={"negative_delta_rows": "delta_metal_floor_negative"})

    keep_lp = patch_lp[
        [
            "material",
            "theta_deg",
            "freq_start_ghz",
            "freq_stop_ghz",
            "freq_center_ghz",
            "n_freq",
            "gamma_x_from_lp_mag",
            "gamma_c_from_lp_mag",
            "B_lp_sys_mag",
            "G_lp_sys_db",
            "use_for_main_claim_candidate",
        ]
    ].rename(columns={"use_for_main_claim_candidate": "lp_use_for_main_claim_candidate"})

    keep_cp = patch_cp[
        [
            "material",
            "theta_deg",
            "gamma_hat_x_cp_sys_mag",
            "gamma_hat_c_cp_raw_mag",
            "gamma_hat_c_cp_eff_mag",
            "r_te_proxy_mag",
            "r_tm_proxy_mag",
            "B_cp_proxy_mag",
            "G_cp_raw_sys_db",
            "G_cp_eff_sys_db",
            "use_for_main_claim_candidate",
        ]
    ].rename(columns={"use_for_main_claim_candidate": "cp_use_for_main_claim_candidate"})

    wide = (
        keep4c.merge(keep_cp, on=["material", "theta_deg"], how="left")
        .merge(keep_lp, on=["material", "theta_deg"], how="left")
        .merge(keep4d, on=["material", "theta_deg"], how="left")
        .sort_values(["material", "theta_deg"])
        .reset_index(drop=True)
    )

    wide["lp_residual_mag"] = wide["gamma_x_from_lp_mag"]
    wide["lp_minus_ideal_residual_db"] = wide.apply(
        lambda row: db20_ratio(row["lp_residual_mag"], row["gamma_x_ideal_mag"]), axis=1
    )
    wide["Delta_ideal_minus_lp_db"] = wide["lp_minus_ideal_residual_db"]
    wide["lp_below_ideal_flag"] = wide["lp_residual_mag"] < wide["gamma_x_ideal_mag"]
    wide["both_lp_and_cp_eff_below_ideal_flag"] = (
        wide["lp_below_ideal_flag"] & wide["eff_smaller_than_ideal"].astype(bool)
    )
    wide["any_directly_comparable_below_ideal_flag"] = (
        wide["raw_smaller_than_ideal"].astype(bool)
        | wide["eff_smaller_than_ideal"].astype(bool)
        | wide["lp_below_ideal_flag"].astype(bool)
    )

    wide["G_lp_gamma_x_db"] = wide.apply(
        lambda row: suppression_gain_db(row["B_mag"], row["gamma_x_from_lp_mag"]), axis=1
    )
    wide["G_lp_gamma_c_db"] = wide.apply(
        lambda row: suppression_gain_db(row["B_mag"], row["gamma_c_from_lp_mag"]), axis=1
    )
    wide["Delta_G_cp_raw_residual_mismatch_db"] = wide["Delta_ideal_minus_raw_db"]
    wide["Delta_G_cp_eff_residual_mismatch_db"] = wide["Delta_ideal_minus_eff_db"]
    wide["Delta_G_lp_residual_mismatch_db"] = wide["Delta_ideal_minus_lp_db"]
    wide["Delta_G_cp_raw_numerator_mismatch_db"] = wide.apply(
        lambda row: db20_ratio(row["B_mag"], row["B_cp_proxy_mag"]), axis=1
    )
    wide["Delta_G_cp_eff_numerator_mismatch_db"] = wide["Delta_G_cp_raw_numerator_mismatch_db"]
    wide["Delta_G_lp_numerator_mismatch_db"] = wide.apply(
        lambda row: db20_ratio(row["B_mag"], row["B_lp_sys_mag"]), axis=1
    )
    wide["Delta_G_ideal_minus_cp_raw_sys_db"] = wide["G_ideal_db"] - wide["G_cp_raw_sys_db"]
    wide["Delta_G_ideal_minus_cp_eff_sys_db"] = wide["G_ideal_db"] - wide["G_cp_eff_sys_db"]
    wide["Delta_G_ideal_minus_lp_sys_db"] = wide["G_ideal_db"] - wide["G_lp_sys_db"]
    wide["delta_cp_raw_sys_negative"] = wide["Delta_G_ideal_minus_cp_raw_sys_db"] < 0.0
    wide["delta_cp_eff_sys_negative"] = wide["Delta_G_ideal_minus_cp_eff_sys_db"] < 0.0
    wide["delta_lp_sys_negative"] = wide["Delta_G_ideal_minus_lp_sys_db"] < 0.0
    wide["delta_lp_negative"] = wide["lp_below_ideal_flag"].astype(bool)
    wide["delta_raw_sign"] = np.where(wide["Delta_ideal_minus_raw_db"] < 0.0, "negative", "nonnegative")
    wide["delta_eff_sign"] = np.where(wide["Delta_ideal_minus_eff_db"] < 0.0, "negative", "nonnegative")
    wide["delta_lp_sign"] = np.where(wide["lp_minus_ideal_residual_db"] < 0.0, "negative", "nonnegative")
    wide["delta_cp_raw_sys_sign"] = np.where(
        wide["Delta_G_ideal_minus_cp_raw_sys_db"] < 0.0, "negative", "nonnegative"
    )
    wide["delta_cp_eff_sys_sign"] = np.where(
        wide["Delta_G_ideal_minus_cp_eff_sys_db"] < 0.0, "negative", "nonnegative"
    )
    wide["delta_lp_sys_sign"] = np.where(
        wide["Delta_G_ideal_minus_lp_sys_db"] < 0.0, "negative", "nonnegative"
    )
    wide["delta_metal_floor_sign"] = np.where(
        wide["Delta_G_ideal_minus_metal_floor_db"] < 0.0, "negative", "nonnegative"
    )
    return wide


def build_branch_long(wide: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in wide.iterrows():
        for series_id, series_label, method_family, normalization_scope, comparable, value_col in BRANCH_SERIES_SPECS:
            residual_mag = row.get(value_col)
            if pd.isna(residual_mag):
                continue
            rows.append(
                {
                    "material": row["material"],
                    "theta_deg": float(row["theta_deg"]),
                    "freq_start_ghz": row.get("freq_start_ghz"),
                    "freq_stop_ghz": row.get("freq_stop_ghz"),
                    "freq_center_ghz": row.get("freq_center_ghz"),
                    "n_freq": row.get("n_freq"),
                    "series_id": series_id,
                    "series_label": series_label,
                    "method_family": method_family,
                    "normalization_scope": normalization_scope,
                    "directly_comparable_to_ideal": comparable,
                    "residual_mag": float(residual_mag),
                    "residual_minus_ideal_db": db20_ratio(residual_mag, row["gamma_x_ideal_mag"]),
                    "below_ideal_flag": bool(comparable and residual_mag < row["gamma_x_ideal_mag"]),
                }
            )
    return pd.DataFrame(rows).sort_values(["material", "theta_deg", "series_id"]).reset_index(drop=True)


def build_suppression_long(wide: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in wide.iterrows():
        for series_id, series_label, method_family, normalization_scope, comparable, value_col in SUPPRESSION_SERIES_SPECS:
            gain_db = row.get(value_col)
            if pd.isna(gain_db):
                continue
            rows.append(
                {
                    "material": row["material"],
                    "theta_deg": float(row["theta_deg"]),
                    "freq_start_ghz": row.get("freq_start_ghz"),
                    "freq_stop_ghz": row.get("freq_stop_ghz"),
                    "freq_center_ghz": row.get("freq_center_ghz"),
                    "n_freq": row.get("n_freq"),
                    "series_id": series_id,
                    "series_label": series_label,
                    "method_family": method_family,
                    "normalization_scope": normalization_scope,
                    "directly_comparable_to_ideal": comparable,
                    "G_supp_db": float(gain_db),
                    "delta_vs_ideal_db": float(row["G_ideal_db"] - gain_db),
                    "delta_vs_ideal_negative": bool((row["G_ideal_db"] - gain_db) < 0.0),
                    "delta_negative": bool(comparable and (row["G_ideal_db"] - gain_db) < 0.0),
                }
            )
    return pd.DataFrame(rows).sort_values(["material", "theta_deg", "series_id"]).reset_index(drop=True)


def build_summary_tables(wide: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    review_rows: list[dict[str, object]] = []
    band_rows: list[dict[str, object]] = []

    for material in [*MATERIALS, "overall"]:
        sub = wide if material == "overall" else wide[wide["material"] == material]
        if sub.empty:
            continue
        summary_rows.append(
            {
                "material": material,
                "n_rows": int(len(sub)),
                "range_theta_min_deg": float(sub["theta_deg"].min()),
                "range_theta_max_deg": float(sub["theta_deg"].max()),
                "freq_start_ghz": float(sub["freq_start_ghz"].min()),
                "freq_stop_ghz": float(sub["freq_stop_ghz"].max()),
                "freq_center_ghz": float(sub["freq_center_ghz"].mean()),
                "mean_G_ideal_db": float(sub["G_ideal_db"].mean()),
                "mean_G_patch_raw_db": float(sub["G_patch_raw_db"].mean()),
                "mean_G_patch_eff_db": float(sub["G_patch_eff_db"].mean()),
                "mean_G_lp_gamma_x_db": float(sub["G_lp_gamma_x_db"].mean()),
                "mean_G_cp_raw_sys_db": float(sub["G_cp_raw_sys_db"].mean()),
                "mean_G_cp_eff_sys_db": float(sub["G_cp_eff_sys_db"].mean()),
                "mean_G_lp_sys_db": float(sub["G_lp_sys_db"].mean()),
                "mean_Delta_ideal_minus_raw_db": float(sub["Delta_ideal_minus_raw_db"].mean()),
                "mean_Delta_ideal_minus_eff_db": float(sub["Delta_ideal_minus_eff_db"].mean()),
                "mean_Delta_ideal_minus_lp_db": float(sub["Delta_ideal_minus_lp_db"].mean()),
                "mean_Delta_G_cp_raw_numerator_mismatch_db": float(sub["Delta_G_cp_raw_numerator_mismatch_db"].mean()),
                "mean_Delta_G_cp_eff_numerator_mismatch_db": float(sub["Delta_G_cp_eff_numerator_mismatch_db"].mean()),
                "mean_Delta_G_lp_numerator_mismatch_db": float(sub["Delta_G_lp_numerator_mismatch_db"].mean()),
                "mean_Delta_G_ideal_minus_cp_raw_sys_db": float(sub["Delta_G_ideal_minus_cp_raw_sys_db"].mean()),
                "mean_Delta_G_ideal_minus_cp_eff_sys_db": float(sub["Delta_G_ideal_minus_cp_eff_sys_db"].mean()),
                "mean_Delta_G_ideal_minus_lp_sys_db": float(sub["Delta_G_ideal_minus_lp_sys_db"].mean()),
                "raw_below_ideal_rows": int(sub["raw_smaller_than_ideal"].sum()),
                "eff_below_ideal_rows": int(sub["eff_smaller_than_ideal"].sum()),
                "lp_below_ideal_rows": int(sub["lp_below_ideal_flag"].sum()),
                "cp_raw_sys_negative_rows": int(sub["delta_cp_raw_sys_negative"].sum()),
                "cp_eff_sys_negative_rows": int(sub["delta_cp_eff_sys_negative"].sum()),
                "lp_sys_negative_rows": int(sub["delta_lp_sys_negative"].sum()),
                "both_lp_and_cp_eff_below_ideal_rows": int(sub["both_lp_and_cp_eff_below_ideal_flag"].sum()),
                "any_directly_comparable_below_ideal_rows": int(sub["any_directly_comparable_below_ideal_flag"].sum()),
                "metal_floor_gt_ideal_rows": int(sub["metal_floor_gt_ideal_residual"].fillna(False).sum()),
            }
        )
        band_rows.append(
            {
                "material": material,
                "freq_start_ghz": float(sub["freq_start_ghz"].min()),
                "freq_stop_ghz": float(sub["freq_stop_ghz"].max()),
                "freq_center_ghz": float(sub["freq_center_ghz"].mean()),
                "n_freq": int(sub["n_freq"].max()),
                "n_rows": int(len(sub)),
                "raw_below_ideal_rows": int(sub["raw_smaller_than_ideal"].sum()),
                "eff_below_ideal_rows": int(sub["eff_smaller_than_ideal"].sum()),
                "lp_below_ideal_rows": int(sub["lp_below_ideal_flag"].sum()),
                "cp_raw_sys_negative_rows": int(sub["delta_cp_raw_sys_negative"].sum()),
                "cp_eff_sys_negative_rows": int(sub["delta_cp_eff_sys_negative"].sum()),
                "lp_sys_negative_rows": int(sub["delta_lp_sys_negative"].sum()),
                "both_lp_and_cp_eff_below_ideal_rows": int(sub["both_lp_and_cp_eff_below_ideal_flag"].sum()),
            }
        )
        if material != "overall":
            review_rows.append(
                {
                    "material": material,
                    "range_deg": f"{int(sub['theta_deg'].min())}-{int(sub['theta_deg'].max())}",
                    "mean_G_ideal_db": float(sub["G_ideal_db"].mean()),
                    "mean_G_patch_raw_db": float(sub["G_patch_raw_db"].mean()),
                    "mean_G_patch_eff_db": float(sub["G_patch_eff_db"].mean()),
                    "mean_G_lp_gamma_x_db": float(sub["G_lp_gamma_x_db"].mean()),
                    "mean_G_cp_raw_sys_db": float(sub["G_cp_raw_sys_db"].mean()),
                    "mean_G_cp_eff_sys_db": float(sub["G_cp_eff_sys_db"].mean()),
                    "mean_G_lp_sys_db": float(sub["G_lp_sys_db"].mean()),
                    "raw_below_ideal_rows": int(sub["raw_smaller_than_ideal"].sum()),
                    "eff_below_ideal_rows": int(sub["eff_smaller_than_ideal"].sum()),
                    "lp_below_ideal_rows": int(sub["lp_below_ideal_flag"].sum()),
                    "cp_raw_sys_negative_rows": int(sub["delta_cp_raw_sys_negative"].sum()),
                    "cp_eff_sys_negative_rows": int(sub["delta_cp_eff_sys_negative"].sum()),
                    "lp_sys_negative_rows": int(sub["delta_lp_sys_negative"].sum()),
                    "both_lp_and_cp_eff_below_ideal_rows": int(sub["both_lp_and_cp_eff_below_ideal_flag"].sum()),
                }
            )
    return pd.DataFrame(summary_rows), pd.DataFrame(review_rows), pd.DataFrame(band_rows)


def build_stage4f_view(wide: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_primary = wide[
        [
            "material",
            "theta_deg",
            "B_mag",
            "gamma_x_ideal_mag",
            "gamma_c_patch_raw_mag",
            "gamma_c_patch_eff_mag",
            "gamma_hat_c_metal_floor_mag",
            "lp_residual_mag",
            "B_cp_proxy_mag",
            "B_lp_sys_mag",
            "G_ideal_db",
            "G_patch_raw_db",
            "G_patch_eff_db",
            "G_patch_metal_floor_db",
            "G_lp_gamma_x_db",
            "G_cp_raw_sys_db",
            "G_cp_eff_sys_db",
            "G_lp_sys_db",
            "Delta_ideal_minus_raw_db",
            "Delta_ideal_minus_eff_db",
            "Delta_G_ideal_minus_metal_floor_db",
            "lp_minus_ideal_residual_db",
            "Delta_ideal_minus_lp_db",
            "Delta_G_cp_raw_numerator_mismatch_db",
            "Delta_G_cp_eff_numerator_mismatch_db",
            "Delta_G_lp_numerator_mismatch_db",
            "Delta_G_cp_raw_residual_mismatch_db",
            "Delta_G_cp_eff_residual_mismatch_db",
            "Delta_G_lp_residual_mismatch_db",
            "Delta_G_ideal_minus_cp_raw_sys_db",
            "Delta_G_ideal_minus_cp_eff_sys_db",
            "Delta_G_ideal_minus_lp_sys_db",
            "delta_raw_negative",
            "delta_eff_negative",
            "delta_metal_floor_negative",
            "delta_cp_raw_sys_negative",
            "delta_cp_eff_sys_negative",
            "delta_lp_sys_negative",
            "lp_below_ideal_flag",
            "both_lp_and_cp_eff_below_ideal_flag",
        ]
    ].copy()
    raw_primary["headline_use_primary"] = True
    raw_primary["headline_note"] = (
        "Raw patch residual remains the locked headline series; LP-vs-CP-vs-ideal columns are audit-only."
    )

    summary_rows: list[dict[str, object]] = []
    for material in MATERIALS:
        sub = raw_primary[raw_primary["material"] == material]
        if sub.empty:
            continue
        summary_rows.append(
            {
                "material": material,
                "range_theta_min_deg": float(sub["theta_deg"].min()),
                "range_theta_max_deg": float(sub["theta_deg"].max()),
                "n_rows": int(len(sub)),
                "mean_G_ideal_db": float(sub["G_ideal_db"].mean()),
                "mean_G_patch_raw_db": float(sub["G_patch_raw_db"].mean()),
                "mean_G_patch_eff_db": float(sub["G_patch_eff_db"].mean()),
                "mean_G_lp_gamma_x_db": float(sub["G_lp_gamma_x_db"].mean()),
                "mean_G_cp_raw_sys_db": float(sub["G_cp_raw_sys_db"].mean()),
                "mean_G_cp_eff_sys_db": float(sub["G_cp_eff_sys_db"].mean()),
                "mean_G_lp_sys_db": float(sub["G_lp_sys_db"].mean()),
                "negative_delta_raw_rows": int(sub["delta_raw_negative"].sum()),
                "negative_delta_eff_rows": int(sub["delta_eff_negative"].sum()),
                "negative_delta_cp_raw_sys_rows": int(sub["delta_cp_raw_sys_negative"].sum()),
                "negative_delta_cp_eff_sys_rows": int(sub["delta_cp_eff_sys_negative"].sum()),
                "negative_delta_lp_sys_rows": int(sub["delta_lp_sys_negative"].sum()),
                "lp_below_ideal_rows": int(sub["lp_below_ideal_flag"].sum()),
                "both_lp_and_cp_eff_below_ideal_rows": int(sub["both_lp_and_cp_eff_below_ideal_flag"].sum()),
            }
        )
    return raw_primary, pd.DataFrame(summary_rows)


def write_authoritative_md(
    *,
    summary_df: pd.DataFrame,
    wide_path: Path,
    branch_long_path: Path,
    suppression_long_path: Path,
    stage4f_full_path: Path,
    stage4f_summary_path: Path,
    band_summary_path: Path,
    output_path: Path,
    repo_root: Path,
) -> None:
    overall = summary_df[summary_df["material"] == "overall"].iloc[0]
    lines = [
        "# Applied Stage 4 Residual Ordering Status",
        "",
        "Execution date: `2026-04-16`",
        "",
        "## Applied Scope",
        "",
        "- `C1` and `C6` are now unified in one authoritative exporter.",
        "- Stage 4e schema fields `method_family`, `normalization_scope`, and `directly_comparable_to_ideal` are reused in the long-form outputs.",
        "- `stage4f_raw_primary_full.csv` is now a derived headline-safe projection of the same authoritative table.",
        "- same-stage numerator gains for LP and CP are exported before ideal-anchor gap interpretation.",
        "- ideal-anchor gap decomposition now separates numerator mismatch from residual mismatch.",
        "",
        "## Current Ordering Counts",
        "",
        f"- raw below ideal: `{int(overall['raw_below_ideal_rows'])}/{int(overall['n_rows'])}`",
        f"- eff below ideal: `{int(overall['eff_below_ideal_rows'])}/{int(overall['n_rows'])}`",
        f"- LP Gamma_X below ideal: `{int(overall['lp_below_ideal_rows'])}/{int(overall['n_rows'])}`",
        f"- both LP and CP eff below ideal: `{int(overall['both_lp_and_cp_eff_below_ideal_rows'])}/{int(overall['n_rows'])}`",
        "",
        "## Same-Stage Gain Audit",
        "",
        f"- CP raw same-stage negative-gap rows: `{int(overall['cp_raw_sys_negative_rows'])}/{int(overall['n_rows'])}`",
        f"- CP eff same-stage negative-gap rows: `{int(overall['cp_eff_sys_negative_rows'])}/{int(overall['n_rows'])}`",
        f"- LP same-stage negative-gap rows: `{int(overall['lp_sys_negative_rows'])}/{int(overall['n_rows'])}`",
        "",
        "## Outputs",
        "",
        f"- Authoritative wide: `{wide_path.relative_to(repo_root)}`",
        f"- Branch long: `{branch_long_path.relative_to(repo_root)}`",
        f"- Suppression long: `{suppression_long_path.relative_to(repo_root)}`",
        f"- Band summary: `{band_summary_path.relative_to(repo_root)}`",
        f"- Stage4f full: `{stage4f_full_path.relative_to(repo_root)}`",
        f"- Stage4f summary: `{stage4f_summary_path.relative_to(repo_root)}`",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_authoritative_export(
    *,
    stage4c_full: Path,
    stage4d_full: Path,
    patch_lp_band: Path,
    patch_cp_band: Path,
    output_dir: Path,
    debug_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[3]

    wide = build_authoritative_wide(
        pd.read_csv(stage4c_full),
        pd.read_csv(stage4d_full),
        pd.read_csv(patch_lp_band),
        pd.read_csv(patch_cp_band),
    )
    branch_long = build_branch_long(wide)
    suppression_long = build_suppression_long(wide)
    summary_df, review_df, band_summary_df = build_summary_tables(wide)
    stage4f_full, stage4f_summary = build_stage4f_view(wide)

    outputs = {
        "wide_path": output_dir / "residual_ordering_authoritative_wide.csv",
        "branch_long_path": output_dir / "residual_ordering_authoritative_branch_long.csv",
        "suppression_long_path": output_dir / "residual_ordering_authoritative_suppression_long.csv",
        "summary_path": output_dir / "residual_ordering_authoritative_summary.csv",
        "review_path": output_dir / "residual_ordering_authoritative_table_for_review.csv",
        "band_summary_path": output_dir / "residual_ordering_authoritative_band_summary.csv",
        "legacy_wide_path": output_dir / "residual_3way_comparison_wide.csv",
        "legacy_branch_long_path": output_dir / "residual_3way_branch_mag_long.csv",
        "legacy_suppression_long_path": output_dir / "residual_3way_suppression_long.csv",
        "legacy_summary_path": output_dir / "residual_3way_summary_by_material.csv",
        "legacy_review_path": output_dir / "residual_3way_table_for_review.csv",
        "stage4f_full_path": output_dir / "stage4f_raw_primary_full.csv",
        "stage4f_summary_path": output_dir / "stage4f_raw_primary_summary.csv",
        "debug_md_path": debug_dir / "APPLIED_MODIFICATION_STATUS.md",
    }

    wide.to_csv(outputs["wide_path"], index=False)
    wide.to_csv(outputs["legacy_wide_path"], index=False)
    branch_long.to_csv(outputs["branch_long_path"], index=False)
    branch_long.to_csv(outputs["legacy_branch_long_path"], index=False)
    suppression_long.to_csv(outputs["suppression_long_path"], index=False)
    suppression_long.to_csv(outputs["legacy_suppression_long_path"], index=False)
    summary_df.to_csv(outputs["summary_path"], index=False)
    summary_df.to_csv(outputs["legacy_summary_path"], index=False)
    review_df.to_csv(outputs["review_path"], index=False)
    review_df.to_csv(outputs["legacy_review_path"], index=False)
    band_summary_df.to_csv(outputs["band_summary_path"], index=False)
    stage4f_full.to_csv(outputs["stage4f_full_path"], index=False)
    stage4f_summary.to_csv(outputs["stage4f_summary_path"], index=False)

    write_authoritative_md(
        summary_df=summary_df,
        wide_path=outputs["wide_path"],
        branch_long_path=outputs["branch_long_path"],
        suppression_long_path=outputs["suppression_long_path"],
        stage4f_full_path=outputs["stage4f_full_path"],
        stage4f_summary_path=outputs["stage4f_summary_path"],
        band_summary_path=outputs["band_summary_path"],
        output_path=outputs["debug_md_path"],
        repo_root=repo_root,
    )
    return outputs


def main() -> None:
    args = build_argparser().parse_args()
    outputs = run_authoritative_export(
        stage4c_full=args.stage4c_full.resolve(),
        stage4d_full=args.stage4d_full.resolve(),
        patch_lp_band=args.patch_lp_band.resolve(),
        patch_cp_band=args.patch_cp_band.resolve(),
        output_dir=args.output_dir.resolve(),
        debug_dir=args.debug_dir.resolve(),
    )
    print(f"Wrote authoritative residual-ordering outputs to {outputs['wide_path'].parent}")


if __name__ == "__main__":
    main()
