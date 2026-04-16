# Consolidated review copy for paper-pipeline code assessment.
# Stage: 4
# Role: Direct specular-RX CP reanalysis using ideal, raw, and calibrated branches.
# Source: analysis_stages/specular_rx_direct_cp_reanalysis_20260414/code/build_specular_rx_direct_cp_reanalysis.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


CHANNEL_MAP = {
    "LL": (
        "mag(S(RX_LH_p1,TX_LH_p1)) []",
        "ang_deg(S(RX_LH_p1,TX_LH_p1)) [deg]",
    ),
    "LR": (
        "mag(S(RX_LH_p1,TX_RH_p1)) []",
        "ang_deg(S(RX_LH_p1,TX_RH_p1)) [deg]",
    ),
    "RL": (
        "mag(S(RX_RH_p1,TX_LH_p1)) []",
        "ang_deg(S(RX_RH_p1,TX_LH_p1)) [deg]",
    ),
    "RR": (
        "mag(S(RX_RH_p1,TX_RH_p1)) []",
        "ang_deg(S(RX_RH_p1,TX_RH_p1)) [deg]",
    ),
}

VALID_MAX_THETA = {
    "concrete": 55.0,
    "glass": 60.0,
    "wood": 45.0,
}

MATERIALS = ["concrete", "glass", "wood"]
MATERIAL_LABELS = {"concrete": "Concrete", "glass": "Glass", "wood": "Wood"}
MATERIAL_COLORS = {"concrete": "#b91c1c", "glass": "#1d4ed8", "wood": "#047857"}


def first_existing_path(*candidates: Path) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def ideal_residual_mag_col(df: pd.DataFrame) -> str:
    return "Gamma_same_mag" if "Gamma_same_mag" in df.columns else "Gamma_X_mag"


def ideal_dominant_mag_col(df: pd.DataFrame) -> str:
    return "Gamma_flip_mag" if "Gamma_flip_mag" in df.columns else "Gamma_C_mag"


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild ideal / CP raw / CP calibrated comparisons from the new "
            "specular RX direct CP files."
        )
    )
    bundle_root = Path(__file__).resolve().parent.parent
    repo_root = Path(__file__).resolve().parents[3]
    specular_stage_root = repo_root / "analysis_stages" / "specular_rx_direct_cp_reanalysis_20260414"
    parser.add_argument(
        "--los-csv",
        type=Path,
        default=specular_stage_root / "LOS_SPECULAR_RX.csv",
    )
    parser.add_argument(
        "--m3-csv",
        type=Path,
        default=specular_stage_root / "M3_SPECULAR_RX.csv",
    )
    parser.add_argument(
        "--pec-csv",
        type=Path,
        default=specular_stage_root / "PEC_SPECULAR_RX.csv",
    )
    parser.add_argument(
        "--concrete-csv",
        type=Path,
        default=specular_stage_root / "CONCRETE_SPECULAR_RX.csv",
    )
    parser.add_argument(
        "--glass-csv",
        type=Path,
        default=first_existing_path(
            specular_stage_root / "GLASS_SPECULAR_RX.csv",
            specular_stage_root / "GLSASS_SPECULAR_RX.csv",
        ),
    )
    parser.add_argument(
        "--wood-csv",
        type=Path,
        default=specular_stage_root / "WOOD_SPECULAR_RX.csv",
    )
    parser.add_argument(
        "--linear-truth",
        type=Path,
        default=bundle_root
        / "data"
        / "stage_1"
        / "truth_table_linear_locked.csv",
    )
    parser.add_argument(
        "--cp-truth",
        type=Path,
        default=bundle_root
        / "data"
        / "stage_2"
        / "sameflip_alias_20260415"
        / "truth_table_cp_shared_common_sameflip.csv",
    )
    parser.add_argument(
        "--stage4f-summary",
        type=Path,
        default=bundle_root
        / "data"
        / "stage_4"
        / "stage4f_raw_primary_dual_20260414"
        / "table1_raw_primary_means.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
    )
    return parser


def load_specular_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    out = df[["theta_r [deg]", "Freq [GHz]"]].copy()
    out = out.rename(columns={"theta_r [deg]": "theta_deg", "Freq [GHz]": "freq_ghz"})
    for ch, (mag_key, phase_key) in CHANNEL_MAP.items():
        mag = df[mag_key].to_numpy(dtype=float)
        phase_deg = df[phase_key].to_numpy(dtype=float)
        out[ch] = mag * np.exp(1j * np.deg2rad(phase_deg))
    return out


def complex_mag_phase(value: complex) -> tuple[float, float]:
    mag = float(abs(value))
    phase_deg = float(np.rad2deg(np.angle(value)))
    return mag, phase_deg


def mag_to_db(values: pd.Series | np.ndarray | list[float]) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    safe = np.maximum(arr, 1e-12)
    return 20.0 * np.log10(safe)


def compute_gamma_x_principal(ht: dict[str, complex], m3_row: pd.Series) -> complex:
    ratio = (ht["LR"] * ht["RL"]) / (m3_row["RR"] * m3_row["LL"])
    return np.sqrt(abs(ratio)) * np.exp(1j * np.angle(ratio) / 2.0)


def compute_gamma_x_anchored(ht: dict[str, complex], m3_row: pd.Series) -> tuple[complex, dict[str, float | bool]]:
    ratio = (ht["LR"] * ht["RL"]) / (m3_row["RR"] * m3_row["LL"])
    mag = np.sqrt(abs(ratio))
    gamma_candidate = mag * np.exp(1j * np.angle(ratio) / 2.0)
    anchor_approx = ht["LR"] / m3_row["RR"]
    candidate_anchor_delta = float(np.rad2deg(np.angle(gamma_candidate / anchor_approx)))
    flip_applied = abs(np.angle(gamma_candidate / anchor_approx)) > (np.pi / 2.0)
    if flip_applied:
        gamma_candidate *= -1.0
    return gamma_candidate, {
        "candidate_anchor_delta_deg": candidate_anchor_delta,
        "anchor_phase_deg": float(np.rad2deg(np.angle(anchor_approx))),
        "flip_applied": bool(flip_applied),
    }


def find_row(df: pd.DataFrame, theta_deg: float) -> pd.Series:
    matched = df[np.isclose(df["theta_deg"].astype(float), theta_deg)]
    if len(matched) != 1:
        raise ValueError(f"Expected one row at theta={theta_deg}, found {len(matched)}")
    return matched.iloc[0]


def build_full_table(
    los: pd.DataFrame,
    m3: pd.DataFrame,
    pec: pd.DataFrame,
    material_dfs: dict[str, pd.DataFrame],
    linear_truth: pd.DataFrame,
    cp_truth: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for material, mat_df in material_dfs.items():
        for _, mat_row in mat_df.iterrows():
            theta_deg = float(np.real(mat_row["theta_deg"]))
            los_row = find_row(los, theta_deg)
            m3_row = find_row(m3, theta_deg)
            pec_row = find_row(pec, theta_deg)

            ht = {ch: mat_row[ch] - los_row[ch] for ch in CHANNEL_MAP}
            ht_pec = {ch: pec_row[ch] - los_row[ch] for ch in CHANNEL_MAP}

            gamma_d_principal = compute_gamma_x_principal(ht, m3_row)
            gamma_d, gamma_d_audit = compute_gamma_x_anchored(ht, m3_row)
            gamma_d_pec_principal = compute_gamma_x_principal(ht_pec, m3_row)
            gamma_d_pec, gamma_d_pec_audit = compute_gamma_x_anchored(ht_pec, m3_row)
            gamma_r_raw = ht["RR"] / m3_row["RR"]

            eps_eff = m3_row["LR"] / m3_row["RR"]
            gamma_r_cal_m3 = gamma_r_raw - eps_eff * gamma_d

            lambda_pec_simple = ht_pec["RR"] / m3_row["RR"]
            lambda_pec_ratio = lambda_pec_simple / gamma_d_pec
            gamma_r_cal_pec_simple = gamma_r_raw - lambda_pec_simple * gamma_d
            gamma_r_cal_pec_ratio = gamma_r_raw - lambda_pec_ratio * gamma_d

            truth_linear_row = linear_truth[
                (linear_truth["material"] == material) & np.isclose(linear_truth["theta_deg"], theta_deg)
            ].iloc[0]
            truth_cp_row = cp_truth[
                (cp_truth["material"] == material) & np.isclose(cp_truth["theta_deg"], theta_deg)
            ].iloc[0]

            B_mag = max(float(truth_linear_row["R_TE_mag"]), float(truth_linear_row["R_TM_mag"]))
            gamma_x_ideal_mag = float(truth_cp_row[ideal_residual_mag_col(cp_truth)])
            gamma_c_ideal_mag = float(truth_cp_row[ideal_dominant_mag_col(cp_truth)])

            gamma_d_mag, gamma_d_phase = complex_mag_phase(gamma_d)
            gamma_d_pec_mag, gamma_d_pec_phase = complex_mag_phase(gamma_d_pec)
            gamma_r_raw_mag, gamma_r_raw_phase = complex_mag_phase(gamma_r_raw)
            gamma_r_cal_m3_mag, gamma_r_cal_m3_phase = complex_mag_phase(gamma_r_cal_m3)
            gamma_r_cal_pec_simple_mag, gamma_r_cal_pec_simple_phase = complex_mag_phase(gamma_r_cal_pec_simple)
            gamma_r_cal_pec_ratio_mag, gamma_r_cal_pec_ratio_phase = complex_mag_phase(gamma_r_cal_pec_ratio)
            eps_eff_mag, eps_eff_phase = complex_mag_phase(eps_eff)
            lambda_pec_simple_mag, lambda_pec_simple_phase = complex_mag_phase(lambda_pec_simple)
            lambda_pec_ratio_mag, lambda_pec_ratio_phase = complex_mag_phase(lambda_pec_ratio)

            G_ideal_db = float(mag_to_db([B_mag / gamma_x_ideal_mag])[0])
            G_cp_raw_db = float(mag_to_db([B_mag / gamma_r_raw_mag])[0])
            G_cp_cal_m3_db = float(mag_to_db([B_mag / gamma_r_cal_m3_mag])[0])
            G_cp_cal_pec_simple_db = float(mag_to_db([B_mag / gamma_r_cal_pec_simple_mag])[0])
            G_cp_cal_pec_ratio_db = float(mag_to_db([B_mag / gamma_r_cal_pec_ratio_mag])[0])

            rows.append(
                {
                    "material": material,
                    "theta_deg": theta_deg,
                    "freq_ghz": float(np.real(mat_row["freq_ghz"])),
                    "valid_max_theta_deg": VALID_MAX_THETA[material],
                    "in_valid_range": theta_deg <= VALID_MAX_THETA[material],
                    "in_headline_oblique_range": (theta_deg >= 20.0) and (theta_deg <= VALID_MAX_THETA[material]),
                    "is_valid_edge_row": np.isclose(theta_deg, VALID_MAX_THETA[material]),
                    "B_mag": B_mag,
                    "gamma_x_ideal_mag": gamma_x_ideal_mag,
                    "gamma_c_ideal_mag": gamma_c_ideal_mag,
                    "gamma_d_principal_mag": float(abs(gamma_d_principal)),
                    "gamma_d_principal_phase_deg": float(np.rad2deg(np.angle(gamma_d_principal))),
                    "gamma_d_direct_mag": gamma_d_mag,
                    "gamma_d_direct_phase_deg": gamma_d_phase,
                    "gamma_d_anchor_phase_deg": float(gamma_d_audit["anchor_phase_deg"]),
                    "gamma_d_candidate_anchor_delta_deg": float(gamma_d_audit["candidate_anchor_delta_deg"]),
                    "gamma_d_phase_flip_applied": bool(gamma_d_audit["flip_applied"]),
                    "gamma_d_pec_principal_mag": float(abs(gamma_d_pec_principal)),
                    "gamma_d_pec_principal_phase_deg": float(np.rad2deg(np.angle(gamma_d_pec_principal))),
                    "gamma_d_pec_mag": gamma_d_pec_mag,
                    "gamma_d_pec_phase_deg": gamma_d_pec_phase,
                    "gamma_d_pec_anchor_phase_deg": float(gamma_d_pec_audit["anchor_phase_deg"]),
                    "gamma_d_pec_candidate_anchor_delta_deg": float(gamma_d_pec_audit["candidate_anchor_delta_deg"]),
                    "gamma_d_pec_phase_flip_applied": bool(gamma_d_pec_audit["flip_applied"]),
                    "gamma_r_raw_real": float(np.real(gamma_r_raw)),
                    "gamma_r_raw_imag": float(np.imag(gamma_r_raw)),
                    "gamma_r_raw_mag": gamma_r_raw_mag,
                    "gamma_r_raw_phase_deg": gamma_r_raw_phase,
                    "gamma_r_cal_m3_real": float(np.real(gamma_r_cal_m3)),
                    "gamma_r_cal_m3_imag": float(np.imag(gamma_r_cal_m3)),
                    "gamma_r_cal_m3_mag": gamma_r_cal_m3_mag,
                    "gamma_r_cal_m3_phase_deg": gamma_r_cal_m3_phase,
                    "gamma_r_cal_pec_simple_real": float(np.real(gamma_r_cal_pec_simple)),
                    "gamma_r_cal_pec_simple_imag": float(np.imag(gamma_r_cal_pec_simple)),
                    "gamma_r_cal_pec_simple_mag": gamma_r_cal_pec_simple_mag,
                    "gamma_r_cal_pec_simple_phase_deg": gamma_r_cal_pec_simple_phase,
                    "gamma_r_cal_pec_ratio_real": float(np.real(gamma_r_cal_pec_ratio)),
                    "gamma_r_cal_pec_ratio_imag": float(np.imag(gamma_r_cal_pec_ratio)),
                    "gamma_r_cal_pec_ratio_mag": gamma_r_cal_pec_ratio_mag,
                    "gamma_r_cal_pec_ratio_phase_deg": gamma_r_cal_pec_ratio_phase,
                    "eps_eff_mag": eps_eff_mag,
                    "eps_eff_phase_deg": eps_eff_phase,
                    "lambda_pec_simple_mag": lambda_pec_simple_mag,
                    "lambda_pec_simple_phase_deg": lambda_pec_simple_phase,
                    "lambda_pec_ratio_mag": lambda_pec_ratio_mag,
                    "lambda_pec_ratio_phase_deg": lambda_pec_ratio_phase,
                    "G_ideal_db": G_ideal_db,
                    "G_cp_raw_db": G_cp_raw_db,
                    "G_cp_cal_m3_db": G_cp_cal_m3_db,
                    "G_cp_cal_pec_simple_db": G_cp_cal_pec_simple_db,
                    "G_cp_cal_pec_ratio_db": G_cp_cal_pec_ratio_db,
                    "Delta_ideal_minus_raw_db": G_ideal_db - G_cp_raw_db,
                    "Delta_ideal_minus_cal_m3_db": G_ideal_db - G_cp_cal_m3_db,
                    "Delta_ideal_minus_cal_pec_simple_db": G_ideal_db - G_cp_cal_pec_simple_db,
                    "Delta_ideal_minus_cal_pec_ratio_db": G_ideal_db - G_cp_cal_pec_ratio_db,
                    "raw_negative_gap": G_ideal_db < G_cp_raw_db,
                    "cal_m3_negative_gap": G_ideal_db < G_cp_cal_m3_db,
                    "cal_pec_simple_negative_gap": G_ideal_db < G_cp_cal_pec_simple_db,
                    "cal_pec_ratio_negative_gap": G_ideal_db < G_cp_cal_pec_ratio_db,
                }
            )

    return pd.DataFrame(rows).sort_values(["material", "theta_deg"]).reset_index(drop=True)


def build_summary(
    full_df: pd.DataFrame,
    stage4f_summary: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    oblique = full_df[full_df["in_headline_oblique_range"]].copy()
    validated = full_df[full_df["in_valid_range"]].copy()

    for scope_name, scoped_df in [("validated_full", validated), ("headline_oblique", oblique)]:
        for material in MATERIALS:
            sub = scoped_df[scoped_df["material"] == material].copy()
            prior = stage4f_summary[stage4f_summary["material"] == material].iloc[0]
            summary_rows.append(
                {
                    "scope": scope_name,
                    "material": material,
                    "theta_min_deg": float(sub["theta_deg"].min()),
                    "theta_max_deg": float(sub["theta_deg"].max()),
                    "n_rows": int(len(sub)),
                    "mean_G_ideal_db": float(sub["G_ideal_db"].mean()),
                    "mean_G_cp_raw_db": float(sub["G_cp_raw_db"].mean()),
                    "mean_G_cp_cal_m3_db": float(sub["G_cp_cal_m3_db"].mean()),
                    "mean_G_cp_cal_pec_ratio_db": float(sub["G_cp_cal_pec_ratio_db"].mean()),
                    "mean_Delta_ideal_minus_raw_db": float(sub["Delta_ideal_minus_raw_db"].mean()),
                    "mean_Delta_ideal_minus_cal_m3_db": float(sub["Delta_ideal_minus_cal_m3_db"].mean()),
                    "mean_Delta_ideal_minus_cal_pec_ratio_db": float(sub["Delta_ideal_minus_cal_pec_ratio_db"].mean()),
                    "raw_negative_rows": int(sub["raw_negative_gap"].sum()),
                    "cal_m3_negative_rows": int(sub["cal_m3_negative_gap"].sum()),
                    "cal_pec_ratio_negative_rows": int(sub["cal_pec_ratio_negative_gap"].sum()),
                    "prior_stage4f_mean_G_cp_raw_db": float(prior["mean_G_patch_raw_db"]),
                    "specular_minus_prior_stage4f_raw_db": float(sub["G_cp_raw_db"].mean() - float(prior["mean_G_patch_raw_db"])),
                }
            )
    summary = pd.DataFrame(summary_rows)

    negative_rows = oblique[
        oblique[
            [
                "raw_negative_gap",
                "cal_m3_negative_gap",
                "cal_pec_simple_negative_gap",
                "cal_pec_ratio_negative_gap",
            ]
        ].any(axis=1)
    ].copy()
    return summary, negative_rows


def make_plots(full_df: pd.DataFrame, output_dir: Path) -> None:
    oblique = full_df[full_df["in_headline_oblique_range"]].copy()

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = oblique[oblique["material"] == material].sort_values("theta_deg")
        ax.plot(sub["theta_deg"], sub["G_ideal_db"], "o-", color="#111827", lw=1.8, label="Ideal")
        ax.plot(sub["theta_deg"], sub["G_cp_raw_db"], "s--", color="#7c2d12", lw=1.8, label="CP raw")
        ax.plot(sub["theta_deg"], sub["G_cp_cal_m3_db"], "d-.", color="#2563eb", lw=1.8, label="CP cal (M3)")
        ax.plot(sub["theta_deg"], sub["G_cp_cal_pec_ratio_db"], "^-", color="#059669", lw=1.6, label="CP cal (PEC ratio)")
        ax.set_title(MATERIAL_LABELS[material])
        ax.set_xlabel("Incident angle [deg]")
        ax.grid(True, alpha=0.25)
        if idx == 0:
            ax.set_ylabel("Suppression gain [dB]")
            ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "fig_specular_rx_suppression_comparison.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = oblique[oblique["material"] == material].sort_values("theta_deg")
        ax.plot(sub["theta_deg"], mag_to_db(sub["gamma_x_ideal_mag"]), "o-", color="#111827", lw=1.8, label="Ideal residual")
        ax.plot(sub["theta_deg"], mag_to_db(sub["gamma_r_raw_mag"]), "s--", color="#7c2d12", lw=1.8, label="CP raw residual")
        ax.plot(sub["theta_deg"], mag_to_db(sub["gamma_r_cal_m3_mag"]), "d-.", color="#2563eb", lw=1.8, label="CP cal (M3)")
        ax.plot(sub["theta_deg"], mag_to_db(sub["gamma_r_cal_pec_ratio_mag"]), "^-", color="#059669", lw=1.6, label="CP cal (PEC ratio)")
        ax.set_title(MATERIAL_LABELS[material])
        ax.set_xlabel("Incident angle [deg]")
        ax.grid(True, alpha=0.25)
        if idx == 0:
            ax.set_ylabel("Residual magnitude [dB]")
            ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "fig_specular_rx_residual_comparison.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def write_summary_markdown(
    full_df: pd.DataFrame,
    summary: pd.DataFrame,
    negative_rows: pd.DataFrame,
    output_dir: Path,
    repo_root: Path,
) -> None:
    oblique = summary[summary["scope"] == "headline_oblique"].copy()
    validated = summary[summary["scope"] == "validated_full"].copy()

    raw_neg_total = int(oblique["raw_negative_rows"].sum())
    cal_m3_neg_total = int(oblique["cal_m3_negative_rows"].sum())
    cal_pec_neg_total = int(oblique["cal_pec_ratio_negative_rows"].sum())
    oblique_rows = int(full_df["in_headline_oblique_range"].sum())
    gamma_d_flip_rows = int(full_df["gamma_d_phase_flip_applied"].sum())
    gamma_d_pec_flip_rows = int(full_df["gamma_d_pec_phase_flip_applied"].sum())

    lines = [
        "# Specular RX Direct CP Reanalysis",
        "",
        "Execution date: `2026-04-14`",
        "",
        "## Purpose",
        "",
        "Recompute the direct-CP `ideal / cp-raw / cp cal` comparison from the new",
        "specular RX files.",
        "",
        "## Calibration Paths Tested",
        "",
        "- `cp-raw`: `Gamma_r_raw = h_tilde_RR / h3_RR`",
        "- `cp cal (M3)`: `Gamma_r_raw - (h3_LR / h3_RR) * Gamma_d`",
        "- `cp cal (PEC ratio)`: `Gamma_r_raw - lambda_PEC * Gamma_d`, where",
        "  `lambda_PEC = Gamma_r_raw_PEC / Gamma_d_PEC`",
        "",
        "Here `Gamma_d` is the dominant direct-CP branch reconstructed from the",
        "reciprocal geometric mean of `LR` and `RL`.",
        "",
        "## Headline Oblique Result",
        "",
        f"- oblique row count: `{oblique_rows}`",
        f"- `Gamma_d` phase-anchor flips applied: `{gamma_d_flip_rows} / {len(full_df)}`",
        f"- `Gamma_d_PEC` phase-anchor flips applied: `{gamma_d_pec_flip_rows} / {len(full_df)}`",
        f"- negative-gap rows for `cp-raw`: `{raw_neg_total} / {oblique_rows}`",
        f"- negative-gap rows for `cp cal (M3)`: `{cal_m3_neg_total} / {oblique_rows}`",
        f"- negative-gap rows for `cp cal (PEC ratio)`: `{cal_pec_neg_total} / {oblique_rows}`",
        "",
        "So the phase-anchor guard is now in place, but for this specular RX dataset it",
        "does not change any row. The new direct specular RX data improve the raw branch",
        "slightly, while both calibrated branches still overshoot the ideal upper bound",
        "too often to be used as a safe headline layer.",
        "",
        "## Mean Suppression By Material (`20 deg` to valid max)",
        "",
    ]

    for _, row in oblique.iterrows():
        lines.extend(
            [
                f"### {row['material']}",
                "",
                f"- ideal mean: `{row['mean_G_ideal_db']:.2f} dB`",
                f"- CP raw mean: `{row['mean_G_cp_raw_db']:.2f} dB`",
                f"- CP cal (M3) mean: `{row['mean_G_cp_cal_m3_db']:.2f} dB`",
                f"- CP cal (PEC ratio) mean: `{row['mean_G_cp_cal_pec_ratio_db']:.2f} dB`",
                f"- raw negative rows: `{int(row['raw_negative_rows'])}`",
                f"- cal M3 negative rows: `{int(row['cal_m3_negative_rows'])}`",
                f"- cal PEC-ratio negative rows: `{int(row['cal_pec_ratio_negative_rows'])}`",
                f"- raw minus prior Stage 4f mean: `{row['specular_minus_prior_stage4f_raw_db']:+.2f} dB`",
                "",
            ]
        )

    lines.extend(
        [
            "## Validated Full-Range Mean (`10 deg` to valid max)",
            "",
        ]
    )
    for _, row in validated.iterrows():
        lines.append(
            f"- {row['material']}: ideal `{row['mean_G_ideal_db']:.2f} dB`, "
            f"raw `{row['mean_G_cp_raw_db']:.2f} dB`, "
            f"cal(M3) `{row['mean_G_cp_cal_m3_db']:.2f} dB`, "
            f"cal(PEC ratio) `{row['mean_G_cp_cal_pec_ratio_db']:.2f} dB`"
        )

    lines.extend(
        [
            "",
            "## Raw Negative-Gap Rows In The Oblique Window",
            "",
        ]
    )
    raw_neg = negative_rows[negative_rows["raw_negative_gap"]].copy()
    if raw_neg.empty:
        lines.append("- none")
    else:
        for _, row in raw_neg.iterrows():
            edge_tag = " (valid-range edge)" if bool(row["is_valid_edge_row"]) else ""
            lines.append(
                f"- {row['material']} / {int(row['theta_deg'])} deg: "
                f"`G_ideal={row['G_ideal_db']:.2f} dB`, `G_cp_raw={row['G_cp_raw_db']:.2f} dB`{edge_tag}"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `cp-raw` is the only branch that stays close to the ideal ordering on most",
            "  oblique rows.",
            "- The complex-square-root phase ambiguity is now explicitly guarded by a",
            "  single-branch phase anchor, but no flip was actually triggered on this",
            "  dataset. So the current calibration failure is not caused by the sqrt branch",
            "  cut here.",
            "- `cp cal (M3)` still shows the same over-subtraction pattern seen earlier.",
            "- `cp cal (PEC ratio)` uses the new matched-geometry PEC reference, but it",
            "  still overshoots the ideal upper bound on most rows.",
            "- So these new files strengthen the direct-CP reconstruction itself, but they",
            "  do not close the calibration-model problem.",
            "",
            "## Outputs",
            "",
            f"- full table: `{(output_dir / 'specular_rx_direct_cp_full.csv').relative_to(repo_root)}`",
            f"- oblique table: `{(output_dir / 'specular_rx_direct_cp_oblique.csv').relative_to(repo_root)}`",
            f"- summary: `{(output_dir / 'specular_rx_direct_cp_summary.csv').relative_to(repo_root)}`",
            f"- negative rows: `{(output_dir / 'specular_rx_direct_cp_negative_rows.csv').relative_to(repo_root)}`",
            f"- suppression figure: `{(output_dir / 'fig_specular_rx_suppression_comparison.png').relative_to(repo_root)}`",
            f"- residual figure: `{(output_dir / 'fig_specular_rx_residual_comparison.png').relative_to(repo_root)}`",
        ]
    )

    (output_dir / "SPECULAR_RX_DIRECT_CP_REANALYSIS.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    args = build_argparser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    los = load_specular_csv(args.los_csv)
    m3 = load_specular_csv(args.m3_csv)
    pec = load_specular_csv(args.pec_csv)
    material_dfs = {
        "concrete": load_specular_csv(args.concrete_csv),
        "glass": load_specular_csv(args.glass_csv),
        "wood": load_specular_csv(args.wood_csv),
    }
    linear_truth = pd.read_csv(args.linear_truth)
    cp_truth = pd.read_csv(args.cp_truth)
    stage4f_summary = pd.read_csv(args.stage4f_summary)

    full_df = build_full_table(los, m3, pec, material_dfs, linear_truth, cp_truth)
    oblique_df = full_df[full_df["in_headline_oblique_range"]].copy()
    summary_df, negative_rows_df = build_summary(full_df, stage4f_summary)

    full_df.to_csv(output_dir / "specular_rx_direct_cp_full.csv", index=False)
    oblique_df.to_csv(output_dir / "specular_rx_direct_cp_oblique.csv", index=False)
    summary_df.to_csv(output_dir / "specular_rx_direct_cp_summary.csv", index=False)
    negative_rows_df.to_csv(output_dir / "specular_rx_direct_cp_negative_rows.csv", index=False)
    full_df[
        [
            "material",
            "theta_deg",
            "gamma_d_principal_phase_deg",
            "gamma_d_direct_phase_deg",
            "gamma_d_anchor_phase_deg",
            "gamma_d_candidate_anchor_delta_deg",
            "gamma_d_phase_flip_applied",
            "gamma_d_pec_principal_phase_deg",
            "gamma_d_pec_phase_deg",
            "gamma_d_pec_anchor_phase_deg",
            "gamma_d_pec_candidate_anchor_delta_deg",
            "gamma_d_pec_phase_flip_applied",
        ]
    ].to_csv(output_dir / "specular_rx_gamma_d_phase_audit.csv", index=False)

    make_plots(full_df, output_dir)
    write_summary_markdown(full_df, summary_df, negative_rows_df, output_dir, repo_root)

    print("Wrote specular RX direct CP reanalysis outputs.")


if __name__ == "__main__":
    main()
