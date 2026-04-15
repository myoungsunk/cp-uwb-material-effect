# Consolidated review copy for paper-pipeline code assessment.
# Stage: 4
# Role: Audit the eff correction mechanism and decompose why over-correction occurs.
# Source: analysis_stages/stage4g_eff_mechanism_audit_20260414/code/audit_eff_mechanism.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


MATERIALS = ["concrete", "glass", "wood"]
VALID_MAX = {"concrete": 55.0, "glass": 60.0, "wood": 45.0}
FREQ_CENTER_GHZ = 6.5
OVERCORRECTION_RHO_MIN = 1.0
PHASE_ALIGN_MAX_DEG = 15.0
ANGLE_OVERCORRECTION_FRAC_MIN = 0.5


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Audit the Stage 4 eff-correction mechanism using freq-resolved patch CP "
            "and LP bridge exports."
        )
    )
    bundle_root = Path(__file__).resolve().parent.parent
    parser.add_argument(
        "--patch-cp-freq",
        type=Path,
        default=bundle_root
        / "data"
        / "stage_3"
        / "cp"
        / "patch_cp_extracted_freq_resolved.csv",
    )
    parser.add_argument(
        "--patch-lp-freq",
        type=Path,
        default=bundle_root
        / "data"
        / "stage_3"
        / "lp"
        / "patch_lp_extracted_freq_resolved.csv",
    )
    parser.add_argument(
        "--stage4f-full",
        type=Path,
        default=Path(__file__).resolve().parent
        / "stage4f_raw_primary_dual_20260414"
        / "results"
        / "stage4f_raw_primary_full.csv",
    )
    parser.add_argument(
        "--ideal-cp-truth",
        type=Path,
        default=bundle_root
        / "data"
        / "stage_2"
        / "sameflip_alias_20260415"
        / "truth_table_cp_shared_common_sameflip.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
    )
    return parser


def complex_from_cols(df: pd.DataFrame, prefix: str) -> np.ndarray:
    return df[f"{prefix}_real"].to_numpy(dtype=float) + 1j * df[f"{prefix}_imag"].to_numpy(dtype=float)


def add_complex_columns(df: pd.DataFrame, prefix: str, values: np.ndarray) -> None:
    df[f"{prefix}_real"] = np.real(values)
    df[f"{prefix}_imag"] = np.imag(values)
    df[f"{prefix}_mag"] = np.abs(values)
    df[f"{prefix}_phase_deg"] = np.rad2deg(np.angle(values))


def wrap_phase_deg(phase_deg: float | np.ndarray) -> float | np.ndarray:
    wrapped = (np.asarray(phase_deg, dtype=float) + 180.0) % 360.0 - 180.0
    if np.isscalar(phase_deg):
        return float(wrapped)
    return wrapped


def valid_main_range(material: str, theta_deg: float) -> bool:
    return float(theta_deg) >= 20.0 and float(theta_deg) <= VALID_MAX[str(material)]


def pairwise_abs_max(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=complex)
    values = values[np.isfinite(values)]
    if values.size < 2:
        return 0.0
    max_diff = 0.0
    for idx in range(values.size):
        diffs = np.abs(values[idx + 1 :] - values[idx])
        if diffs.size:
            max_diff = max(max_diff, float(diffs.max()))
    return max_diff


def safe_complex_ratio(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    out = np.full(num.shape, np.nan + 1j * np.nan, dtype=complex)
    valid = np.abs(den) > 1e-12
    out[valid] = num[valid] / den[valid]
    return out


def ideal_same_prefix(df: pd.DataFrame) -> str:
    return "Gamma_same" if {"Gamma_same_real", "Gamma_same_imag"}.issubset(df.columns) else "Gamma_X"


def main() -> None:
    args = build_argparser().parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[3]

    patch_cp = pd.read_csv(args.patch_cp_freq)
    patch_lp = pd.read_csv(args.patch_lp_freq)
    stage4f = pd.read_csv(args.stage4f_full)
    ideal_cp = pd.read_csv(args.ideal_cp_truth)

    keep_lp = patch_lp[
        [
            "material",
            "theta_deg",
            "freq_ghz",
            "gamma_x_from_lp_real",
            "gamma_x_from_lp_imag",
            "gamma_x_from_lp_mag",
            "gamma_c_from_lp_real",
            "gamma_c_from_lp_imag",
            "gamma_c_from_lp_mag",
        ]
    ].copy()

    freq_df = (
        patch_cp.merge(keep_lp, on=["material", "theta_deg", "freq_ghz"], how="inner")
        .sort_values(["material", "theta_deg", "freq_ghz"])
        .reset_index(drop=True)
    )
    freq_df = freq_df[freq_df["material"].isin(MATERIALS)].copy()
    freq_df = freq_df[freq_df.apply(lambda row: valid_main_range(row["material"], row["theta_deg"]), axis=1)].copy()

    gamma_dom = complex_from_cols(freq_df, "gamma_hat_x_cp_sys")
    gamma_res_raw = complex_from_cols(freq_df, "gamma_hat_c_cp_raw")
    gamma_res_eff = complex_from_cols(freq_df, "gamma_hat_c_cp_eff")
    gamma_target_lp = complex_from_cols(freq_df, "gamma_x_from_lp")
    correction = gamma_res_raw - gamma_res_eff
    eps_eff_current = safe_complex_ratio(correction, gamma_dom)
    eps_obs_lp = safe_complex_ratio(gamma_res_raw - gamma_target_lp, gamma_dom)

    freq_df["_gamma_dom"] = gamma_dom
    freq_df["_gamma_res_raw"] = gamma_res_raw
    freq_df["_gamma_res_eff"] = gamma_res_eff
    freq_df["_gamma_target_lp"] = gamma_target_lp
    freq_df["_correction"] = correction
    freq_df["_eps_eff_current"] = eps_eff_current
    freq_df["_eps_obs_lp"] = eps_obs_lp

    rho = np.abs(correction) / np.maximum(np.abs(gamma_res_raw), 1e-12)
    delta_phi_deg = wrap_phase_deg(np.rad2deg(np.angle(correction) - np.angle(gamma_res_raw)))

    add_complex_columns(freq_df, "correction_term", correction)
    add_complex_columns(freq_df, "eps_eff_current", eps_eff_current)
    add_complex_columns(freq_df, "eps_obs_lp", eps_obs_lp)
    freq_df["rho"] = rho
    freq_df["delta_phi_deg"] = delta_phi_deg
    freq_df["rho_ge_1"] = freq_df["rho"] >= OVERCORRECTION_RHO_MIN
    freq_df["phase_near_zero"] = freq_df["delta_phi_deg"].abs() <= PHASE_ALIGN_MAX_DEG
    freq_df["predicted_overcorrection_point"] = freq_df["rho_ge_1"] & freq_df["phase_near_zero"]
    freq_df["eps_obs_lp_vs_current_abs_diff"] = np.abs(eps_obs_lp - eps_eff_current)

    stage4f = stage4f[stage4f["material"].isin(MATERIALS)][
        ["material", "theta_deg", "Delta_ideal_minus_eff_db", "delta_eff_negative"]
    ].copy()
    stage4f["delta_eff_negative"] = stage4f["delta_eff_negative"].astype(bool)

    angle_rows = []
    for (material, theta_deg), sub in freq_df.groupby(["material", "theta_deg"], sort=True):
        z_raw = sub["_gamma_res_raw"].to_numpy(dtype=complex).mean()
        z_corr = sub["_correction"].to_numpy(dtype=complex).mean()
        phase_diff = wrap_phase_deg(np.rad2deg(np.angle(z_corr) - np.angle(z_raw)))
        angle_rows.append(
            {
                "material": material,
                "theta_deg": float(theta_deg),
                "n_freq": int(len(sub)),
                "eps_eff_mag_mean": float(np.nanmean(np.abs(sub["_eps_eff_current"].to_numpy(dtype=complex)))),
                "eps_eff_db": float(
                    20.0 * np.log10(max(np.nanmean(np.abs(sub["_eps_eff_current"].to_numpy(dtype=complex))), 1e-12))
                ),
                "gamma_x_mag_mean": float(np.mean(np.abs(sub["_gamma_dom"].to_numpy(dtype=complex)))),
                "gamma_c_raw_mag_mean": float(np.mean(np.abs(sub["_gamma_res_raw"].to_numpy(dtype=complex)))),
                "correction_mag_mean": float(np.mean(np.abs(sub["_correction"].to_numpy(dtype=complex)))),
                "gamma_c_eff_mag_mean": float(np.mean(np.abs(sub["_gamma_res_eff"].to_numpy(dtype=complex)))),
                "correction_to_raw_ratio": float(np.mean(sub["rho"])),
                "phase_diff_raw_vs_correction_deg": float(phase_diff),
                "rho_mean": float(np.mean(sub["rho"])),
                "rho_median": float(np.median(sub["rho"])),
                "rho_ge_1_freq_frac": float(np.mean(sub["rho_ge_1"])),
                "aligned_phase_freq_frac": float(np.mean(sub["phase_near_zero"])),
                "overcorrection_freq_frac": float(np.mean(sub["predicted_overcorrection_point"])),
                "abs_delta_phi_median_deg": float(np.median(np.abs(sub["delta_phi_deg"]))),
                "eps_obs_lp_mag_mean": float(np.nanmean(np.abs(sub["_eps_obs_lp"].to_numpy(dtype=complex)))),
                "eps_obs_lp_mag_std": float(np.nanstd(np.abs(sub["_eps_obs_lp"].to_numpy(dtype=complex)))),
                "eps_obs_lp_vs_current_mean_abs_diff": float(np.nanmean(sub["eps_obs_lp_vs_current_abs_diff"])),
                "eps_obs_lp_vs_current_p90_abs_diff": float(np.nanpercentile(sub["eps_obs_lp_vs_current_abs_diff"], 90)),
            }
        )

    angle_df = pd.DataFrame(angle_rows).sort_values(["material", "theta_deg"]).reset_index(drop=True)
    angle_df = angle_df.merge(stage4f, on=["material", "theta_deg"], how="left")
    angle_df["high_cancellation_flag"] = angle_df["correction_to_raw_ratio"] >= 0.95
    angle_df["near_aligned_phase_flag"] = angle_df["phase_diff_raw_vs_correction_deg"].abs() <= PHASE_ALIGN_MAX_DEG
    angle_df["predicted_overcorrection_region"] = angle_df["high_cancellation_flag"] & angle_df["near_aligned_phase_flag"]
    angle_df["overcorrection_majority_row"] = angle_df["overcorrection_freq_frac"] >= ANGLE_OVERCORRECTION_FRAC_MIN

    freq_export_cols = [
        "material",
        "theta_deg",
        "freq_ghz",
        "gamma_hat_x_cp_sys_real",
        "gamma_hat_x_cp_sys_imag",
        "gamma_hat_x_cp_sys_mag",
        "gamma_hat_c_cp_raw_real",
        "gamma_hat_c_cp_raw_imag",
        "gamma_hat_c_cp_raw_mag",
        "gamma_hat_c_cp_eff_real",
        "gamma_hat_c_cp_eff_imag",
        "gamma_hat_c_cp_eff_mag",
        "gamma_x_from_lp_real",
        "gamma_x_from_lp_imag",
        "gamma_x_from_lp_mag",
        "correction_term_real",
        "correction_term_imag",
        "correction_term_mag",
        "correction_term_phase_deg",
        "eps_eff_current_real",
        "eps_eff_current_imag",
        "eps_eff_current_mag",
        "eps_eff_current_phase_deg",
        "eps_obs_lp_real",
        "eps_obs_lp_imag",
        "eps_obs_lp_mag",
        "eps_obs_lp_phase_deg",
        "rho",
        "delta_phi_deg",
        "rho_ge_1",
        "phase_near_zero",
        "predicted_overcorrection_point",
        "eps_obs_lp_vs_current_abs_diff",
    ]
    freq_export = freq_df[freq_export_cols].copy()

    spread_rows = []
    for (theta_deg, freq_ghz), sub in freq_df.groupby(["theta_deg", "freq_ghz"], sort=True):
        spread_rows.append(
            {
                "theta_deg": float(theta_deg),
                "freq_ghz": float(freq_ghz),
                "n_materials": int(len(sub)),
                "eps_eff_current_pairwise_max_abs_diff": pairwise_abs_max(
                    sub["_eps_eff_current"].to_numpy(dtype=complex)
                ),
                "eps_obs_lp_pairwise_max_abs_diff": pairwise_abs_max(sub["_eps_obs_lp"].to_numpy(dtype=complex)),
                "eps_obs_lp_mag_std_across_material": float(
                    np.nanstd(np.abs(sub["_eps_obs_lp"].to_numpy(dtype=complex)))
                ),
                "eps_obs_lp_vs_current_mean_abs_diff_across_material": float(
                    np.nanmean(sub["eps_obs_lp_vs_current_abs_diff"])
                ),
            }
        )
    spread_df = pd.DataFrame(spread_rows).sort_values(["theta_deg", "freq_ghz"]).reset_index(drop=True)

    spread_theta_df = (
        spread_df.groupby("theta_deg", as_index=False)
        .agg(
            n_freq=("freq_ghz", "size"),
            mean_eps_eff_current_pairwise_max_abs_diff=("eps_eff_current_pairwise_max_abs_diff", "mean"),
            max_eps_eff_current_pairwise_max_abs_diff=("eps_eff_current_pairwise_max_abs_diff", "max"),
            mean_eps_obs_lp_pairwise_max_abs_diff=("eps_obs_lp_pairwise_max_abs_diff", "mean"),
            max_eps_obs_lp_pairwise_max_abs_diff=("eps_obs_lp_pairwise_max_abs_diff", "max"),
            mean_eps_obs_lp_mag_std_across_material=("eps_obs_lp_mag_std_across_material", "mean"),
            mean_eps_obs_lp_vs_current_abs_diff_across_material=(
                "eps_obs_lp_vs_current_mean_abs_diff_across_material",
                "mean",
            ),
        )
        .sort_values("theta_deg")
        .reset_index(drop=True)
    )

    material_summary_rows = []
    for material in MATERIALS + ["overall"]:
        angle_sub = angle_df if material == "overall" else angle_df[angle_df["material"] == material]
        freq_sub = freq_df if material == "overall" else freq_df[freq_df["material"] == material]
        if angle_sub.empty or freq_sub.empty:
            continue
        angle_sub = angle_sub.sort_values("theta_deg")
        material_summary_rows.append(
            {
                "material": material,
                "n_rows": int(len(angle_sub)),
                "n_freq_points": int(len(freq_sub)),
                "eps_eff_db_start": float(angle_sub.iloc[0]["eps_eff_db"]),
                "eps_eff_db_end": float(angle_sub.iloc[-1]["eps_eff_db"]),
                "eps_eff_db_monotonic_decrease": bool((angle_sub["eps_eff_db"].diff().dropna() < 0).all()),
                "mean_correction_to_raw_ratio": float(angle_sub["correction_to_raw_ratio"].mean()),
                "max_correction_to_raw_ratio": float(angle_sub["correction_to_raw_ratio"].max()),
                "negative_eff_rows": int(angle_sub["delta_eff_negative"].fillna(False).sum()),
                "predicted_overcorrection_rows": int(angle_sub["predicted_overcorrection_region"].sum()),
                "overcorrection_majority_rows": int(angle_sub["overcorrection_majority_row"].sum()),
                "rho_ge_1_freq_frac": float(freq_sub["rho_ge_1"].mean()),
                "phase_near_zero_freq_frac": float(freq_sub["phase_near_zero"].mean()),
                "predicted_overcorrection_freq_frac": float(freq_sub["predicted_overcorrection_point"].mean()),
                "mean_eps_obs_lp_vs_current_abs_diff": float(freq_sub["eps_obs_lp_vs_current_abs_diff"].mean()),
                "p90_eps_obs_lp_vs_current_abs_diff": float(np.percentile(freq_sub["eps_obs_lp_vs_current_abs_diff"], 90)),
            }
        )
    summary_df = pd.DataFrame(material_summary_rows)

    ideal_prefix = ideal_same_prefix(ideal_cp)
    ideal_keep = ideal_cp[
        [
            "material",
            "theta_deg",
            "f_hz",
            f"{ideal_prefix}_real",
            f"{ideal_prefix}_imag",
            f"{ideal_prefix}_mag",
            f"{ideal_prefix}_phase_deg",
            "cp_use_for_main_claim",
        ]
    ].copy()
    ideal_keep = ideal_keep[ideal_keep["material"].isin(MATERIALS)].copy()
    ideal_keep["freq_ghz"] = ideal_keep["f_hz"] / 1e9
    ideal_keep = ideal_keep.rename(
        columns={
            f"{ideal_prefix}_real": "ideal_same_real",
            f"{ideal_prefix}_imag": "ideal_same_imag",
            f"{ideal_prefix}_mag": "ideal_same_mag",
            f"{ideal_prefix}_phase_deg": "ideal_same_phase_deg",
        }
    )

    ideal_center = freq_df[np.isclose(freq_df["freq_ghz"], FREQ_CENTER_GHZ, atol=5e-4)].copy()
    ideal_center = ideal_center.merge(
        ideal_keep[["material", "theta_deg", "freq_ghz", "ideal_same_real", "ideal_same_imag", "ideal_same_mag", "ideal_same_phase_deg"]],
        on=["material", "theta_deg", "freq_ghz"],
        how="inner",
    )
    gamma_target_ideal = complex_from_cols(ideal_center, "ideal_same")
    eps_obs_ideal = safe_complex_ratio(complex_from_cols(ideal_center, "gamma_hat_c_cp_raw") - gamma_target_ideal, complex_from_cols(ideal_center, "gamma_hat_x_cp_sys"))
    add_complex_columns(ideal_center, "eps_obs_ideal", eps_obs_ideal)
    ideal_center["eps_obs_ideal_vs_current_abs_diff"] = np.abs(eps_obs_ideal - ideal_center["_eps_eff_current"].to_numpy(dtype=complex))
    ideal_center_export = ideal_center[
        [
            "material",
            "theta_deg",
            "freq_ghz",
            "gamma_hat_x_cp_sys_real",
            "gamma_hat_x_cp_sys_imag",
            "gamma_hat_x_cp_sys_mag",
            "gamma_hat_c_cp_raw_real",
            "gamma_hat_c_cp_raw_imag",
            "gamma_hat_c_cp_raw_mag",
            "ideal_same_real",
            "ideal_same_imag",
            "ideal_same_mag",
            "ideal_same_phase_deg",
            "eps_eff_current_real",
            "eps_eff_current_imag",
            "eps_eff_current_mag",
            "eps_eff_current_phase_deg",
            "eps_obs_ideal_real",
            "eps_obs_ideal_imag",
            "eps_obs_ideal_mag",
            "eps_obs_ideal_phase_deg",
            "eps_obs_ideal_vs_current_abs_diff",
        ]
    ].copy()

    ideal_summary_rows = []
    for material in MATERIALS + ["overall"]:
        sub = ideal_center_export if material == "overall" else ideal_center_export[ideal_center_export["material"] == material]
        if sub.empty:
            continue
        ideal_summary_rows.append(
            {
                "material": material,
                "n_rows": int(len(sub)),
                "mean_eps_obs_ideal_mag": float(sub["eps_obs_ideal_mag"].mean()),
                "mean_eps_obs_ideal_vs_current_abs_diff": float(sub["eps_obs_ideal_vs_current_abs_diff"].mean()),
                "max_eps_obs_ideal_vs_current_abs_diff": float(sub["eps_obs_ideal_vs_current_abs_diff"].max()),
            }
        )
    ideal_summary_df = pd.DataFrame(ideal_summary_rows)

    full_path = output_dir / "eff_mechanism_audit_full.csv"
    summary_path = output_dir / "eff_mechanism_summary.csv"
    freq_path = output_dir / "eff_mechanism_audit_freq_resolved.csv"
    spread_path = output_dir / "eps_obs_lp_material_spread_freq.csv"
    spread_theta_path = output_dir / "eps_obs_lp_material_spread_theta_summary.csv"
    ideal_center_path = output_dir / "eps_obs_ideal_center_6p5ghz.csv"
    ideal_summary_path = output_dir / "eps_obs_ideal_center_summary.csv"

    angle_df.to_csv(full_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    freq_export.to_csv(freq_path, index=False)
    spread_df.to_csv(spread_path, index=False)
    spread_theta_df.to_csv(spread_theta_path, index=False)
    ideal_center_export.to_csv(ideal_center_path, index=False)
    ideal_summary_df.to_csv(ideal_summary_path, index=False)

    overall_summary = summary_df[summary_df["material"] == "overall"].iloc[0]
    spread_overall = {
        "mean_current": float(spread_df["eps_eff_current_pairwise_max_abs_diff"].mean()),
        "max_current": float(spread_df["eps_eff_current_pairwise_max_abs_diff"].max()),
        "mean_obs": float(spread_df["eps_obs_lp_pairwise_max_abs_diff"].mean()),
        "max_obs": float(spread_df["eps_obs_lp_pairwise_max_abs_diff"].max()),
    }
    ideal_overall = ideal_summary_df[ideal_summary_df["material"] == "overall"]

    md_lines = [
        "# Stage 4g Eff Mechanism Audit",
        "",
        "Execution date: `2026-04-14`",
        "",
        "This stage was executed in the isolated workspace:",
        "",
        "- `analysis_stages/stage4g_eff_mechanism_audit_20260414`",
        "",
        "## Core Findings",
        "",
        "The Stage 4 `eff` failure is now separated into two mechanisms:",
        "",
        "1. same-direction over-subtraction:",
        f"   freq points with `rho >= 1` and `|Delta_phi| <= {PHASE_ALIGN_MAX_DEG:.0f} deg`: "
        f"`{overall_summary['predicted_overcorrection_freq_frac'] * 100.0:.1f}%`",
        f"   angle rows with overcorrection on at least `{ANGLE_OVERCORRECTION_FRAC_MIN * 100.0:.0f}%` of the band: "
        f"`{int(overall_summary['overcorrection_majority_rows'])}/{int(overall_summary['n_rows'])}`",
        "",
        "2. shared-`eps_eff` model mismatch:",
        f"   same `(theta,f)` current `eps_eff` material spread mean max-pairwise diff: `{spread_overall['mean_current']:.4f}`",
        f"   same `(theta,f)` back-solved `eps_obs` from LP bridge mean max-pairwise diff: `{spread_overall['mean_obs']:.4f}`",
        "",
        "So the correction worsens because the subtraction term often reaches raw-residual scale with near-zero phase gap,",
        "and the `eps` required to hit the LP-derived residual target is materially different from the single shared current `eps_eff`.",
        "",
        "## Material Summary",
        "",
    ]

    for _, row in summary_df[summary_df["material"] != "overall"].iterrows():
        md_lines.append(
            f"- {row['material']}: eps_eff {row['eps_eff_db_start']:.2f} dB -> {row['eps_eff_db_end']:.2f} dB "
            f"(monotonic decrease={row['eps_eff_db_monotonic_decrease']}), "
            f"negative eff rows={int(row['negative_eff_rows'])}, "
            f"band-majority overcorrection rows={int(row['overcorrection_majority_rows'])}, "
            f"mean |eps_obs_lp - eps_eff|={row['mean_eps_obs_lp_vs_current_abs_diff']:.4f}"
        )

    md_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `|eps_eff|` itself still decreases with angle; the failure is not high-angle growth of the current correction coefficient.",
            "- The first practical proof of over-correction is the freq-resolved pattern `rho >= 1` together with `Delta_phi ~= 0 deg`.",
            "- The second practical proof is the LP-target back-solved `eps_obs`: it varies with `(theta, f, material)` even though the current `eps_eff` is shared across materials at the same `(theta, f)`.",
            "- Ideal-target back-solving is also exported at `6.5 GHz` only. Use it as a diagnostic fit-style reference, not as calibration.",
            "",
            "## Ideal 6.5 GHz Diagnostic",
            "",
        ]
    )

    if not ideal_overall.empty:
        ideal_row = ideal_overall.iloc[0]
        md_lines.append(
            f"- center-frequency `eps_obs_ideal` mean |difference vs current eps_eff|: "
            f"`{ideal_row['mean_eps_obs_ideal_vs_current_abs_diff']:.4f}`"
        )
    else:
        md_lines.append("- center-frequency ideal diagnostic could not be joined to the patch freq grid.")

    md_lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Angle summary: `{full_path.relative_to(repo_root)}`",
            f"- Material summary: `{summary_path.relative_to(repo_root)}`",
            f"- Freq-resolved `rho / Delta_phi / eps_obs_lp`: `{freq_path.relative_to(repo_root)}`",
            f"- LP-target material spread by `(theta, f)`: `{spread_path.relative_to(repo_root)}`",
            f"- LP-target material spread by `theta`: `{spread_theta_path.relative_to(repo_root)}`",
            f"- Ideal-target center-frequency diagnostic: `{ideal_center_path.relative_to(repo_root)}`",
            f"- Ideal-target center-frequency summary: `{ideal_summary_path.relative_to(repo_root)}`",
        ]
    )

    (output_dir / "STAGE4G_EFF_MECHANISM_AUDIT.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print("Wrote Stage 4g eff mechanism audit with freq-resolved rho/Delta_phi/eps_obs outputs.")


if __name__ == "__main__":
    main()
