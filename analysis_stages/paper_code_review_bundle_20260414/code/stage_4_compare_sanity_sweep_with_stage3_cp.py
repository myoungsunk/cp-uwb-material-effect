# Consolidated review copy for paper-pipeline code assessment.
# Stage: 4
# Role: Compare sanity-check sweep exports against Stage 3 CP outputs.
# Source: analysis_stages/sanity_check_sweep_vs_stage3_20260414/code/compare_sanity_sweep_with_stage3_cp.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd


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


def load_one_row(path: Path) -> dict[str, complex]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        row = next(csv.DictReader(f))
    out: dict[str, complex] = {}
    for ch, (mag_key, phase_key) in CHANNEL_MAP.items():
        mag = float(row[mag_key])
        phase_deg = float(row[phase_key])
        out[ch] = mag * np.exp(1j * np.deg2rad(phase_deg))
    out["freq_ghz"] = complex(float(row["Freq [GHz]"]), 0.0)
    return out


def load_sweep(path: Path, material: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["material"] = material
    return df


def complex_from_mag_phase(mag: float, phase_deg: float) -> complex:
    return mag * np.exp(1j * np.deg2rad(phase_deg))


def mag_phase(z: complex) -> tuple[float, float]:
    return float(abs(z)), float(np.rad2deg(np.angle(z)))


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    out_dir = Path(__file__).resolve().parents[1] / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    external_dir = Path(r"E:\0. CP Antenna\0. TRACK2_3_SIM\ANTENNA_SOURCE\sending")
    los_path = external_dir / "sanity check_LOS.csv"
    m3_path = external_dir / "sanity check_M3_SWEEP.csv"
    sweep_paths = {
        "concrete": external_dir / "sanity check_CONCRETE_SWEEP.csv",
        "glass": external_dir / "sanity check_GLASS_SWEEP.csv",
        "wood": external_dir / "sanity check_WOOD_SWEEP.csv",
        "metal": external_dir / "sanity check_PEC_SWEEP.csv",
    }

    stage3_path = (
        repo_root
        / "analysis_stages"
        / "stage3_patch_paper_final_20260414"
        / "cp"
        / "results"
        / "patch_cp_extracted_freq_resolved.csv"
    )

    los = load_one_row(los_path)
    m3 = load_one_row(m3_path)
    stage3 = pd.read_csv(stage3_path)
    stage3 = stage3[np.isclose(stage3["freq_ghz"], 6.5)].copy()

    reconstructed_rows: list[dict[str, float | str]] = []
    for material, path in sweep_paths.items():
        sweep_df = load_sweep(path, material)
        for row in sweep_df.to_dict("records"):
            ht = {}
            for ch, (mag_key, phase_key) in CHANNEL_MAP.items():
                ht[ch] = complex_from_mag_phase(float(row[mag_key]), float(row[phase_key])) - los[ch]
            ratio_x = (ht["LR"] * ht["RL"]) / (m3["RR"] * m3["LL"])
            gamma_x = np.sqrt(abs(ratio_x)) * np.exp(1j * np.angle(ratio_x) / 2)
            gamma_c_raw = ht["RR"] / m3["RR"]
            eps_eff = m3["LR"] / m3["RR"]
            gamma_c_eff = gamma_c_raw - eps_eff * gamma_x
            reconstructed_rows.append(
                {
                    "material": material,
                    "theta_deg": float(row.get("theta_r [deg]", np.nan)),
                    "freq_ghz": float(row["Freq [GHz]"]),
                    "gamma_x_recon_real": float(np.real(gamma_x)),
                    "gamma_x_recon_imag": float(np.imag(gamma_x)),
                    "gamma_x_recon_mag": float(abs(gamma_x)),
                    "gamma_c_raw_recon_real": float(np.real(gamma_c_raw)),
                    "gamma_c_raw_recon_imag": float(np.imag(gamma_c_raw)),
                    "gamma_c_raw_recon_mag": float(abs(gamma_c_raw)),
                    "gamma_c_eff_recon_real": float(np.real(gamma_c_eff)),
                    "gamma_c_eff_recon_imag": float(np.imag(gamma_c_eff)),
                    "gamma_c_eff_recon_mag": float(abs(gamma_c_eff)),
                    "eps_eff_mag": float(abs(eps_eff)),
                    "eps_eff_phase_deg": float(np.rad2deg(np.angle(eps_eff))),
                }
            )

    recon = pd.DataFrame(reconstructed_rows)
    recon.to_csv(out_dir / "sweep_reconstructed_cp_6p5ghz.csv", index=False)

    merged = recon.merge(
        stage3,
        on=["material", "theta_deg", "freq_ghz"],
        how="inner",
        validate="one_to_one",
    )

    for base in ["gamma_hat_x_cp_sys", "gamma_hat_c_cp_raw", "gamma_hat_c_cp_eff"]:
        recon_base = base.replace("gamma_hat_", "").replace("_cp_sys", "_recon").replace("_cp_raw", "_raw_recon").replace("_cp_eff", "_eff_recon")
        if base == "gamma_hat_x_cp_sys":
            recon_prefix = "gamma_x_recon"
        elif base == "gamma_hat_c_cp_raw":
            recon_prefix = "gamma_c_raw_recon"
        else:
            recon_prefix = "gamma_c_eff_recon"
        merged[f"{base}_mag_abs_diff"] = (merged[f"{recon_prefix}_mag"] - merged[f"{base}_mag"]).abs()
        merged[f"{base}_mag_rel_diff_pct"] = merged[f"{base}_mag_abs_diff"] / merged[f"{base}_mag"].clip(lower=1e-12) * 100.0

    merged.to_csv(out_dir / "sweep_vs_stage3_cp_full.csv", index=False)

    summary_rows = []
    for material, group in merged.groupby("material", sort=True):
        row: dict[str, float | str] = {
            "material": material,
            "n_rows": int(len(group)),
        }
        for base in ["gamma_hat_x_cp_sys", "gamma_hat_c_cp_raw", "gamma_hat_c_cp_eff"]:
            row[f"{base}_mae"] = float(group[f"{base}_mag_abs_diff"].mean())
            row[f"{base}_max_abs_diff"] = float(group[f"{base}_mag_abs_diff"].max())
            row[f"{base}_mean_rel_diff_pct"] = float(group[f"{base}_mag_rel_diff_pct"].mean())
            row[f"{base}_max_rel_diff_pct"] = float(group[f"{base}_mag_rel_diff_pct"].max())
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(out_dir / "sweep_vs_stage3_cp_summary.csv", index=False)

    exact_checks = []
    for material, theta in [("concrete", 30.0)]:
        row = merged[(merged["material"] == material) & (merged["theta_deg"] == theta)].iloc[0]
        exact_checks.append(
            {
                "material": material,
                "theta_deg": theta,
                "gamma_x_diff": float(row["gamma_hat_x_cp_sys_mag_abs_diff"]),
                "gamma_c_raw_diff": float(row["gamma_hat_c_cp_raw_mag_abs_diff"]),
                "gamma_c_eff_diff": float(row["gamma_hat_c_cp_eff_mag_abs_diff"]),
            }
        )
    pd.DataFrame(exact_checks).to_csv(out_dir / "sweep_exact_checks.csv", index=False)

    md_lines = [
        "# Sanity Sweep vs Existing Stage 3 CP",
        "",
        "Execution date: `2026-04-14`",
        "",
        "## Purpose",
        "",
        "Check whether the newly provided `sanity check_*_SWEEP.csv` files are in the same convention and numerically consistent with the existing Stage 3 CP pipeline at `6.5 GHz`.",
        "",
        "## Inputs",
        "",
        f"- LOS reference: `{los_path}`",
        f"- M3 reference: `{m3_path}`",
        f"- sweep files: `{external_dir}`",
        f"- Stage 3 reference: `{stage3_path}`",
        "",
        "## Method",
        "",
        "- Reconstruct `Gamma_X`, `Gamma_C_raw`, and `Gamma_C_eff` from the sweep CSVs using the same patch-style formulas already locked in the direct CP one-point sanity.",
        "- Compare those reconstructed values against `patch_cp_extracted_freq_resolved.csv` at the same `(material, theta, 6.5 GHz)` points.",
        "- Use `PEC_SWEEP` as the `metal` row for the Stage 3 comparison.",
        "",
        "## Key Result",
        "",
    ]
    for _, row in summary.iterrows():
        md_lines.extend(
            [
                f"### {row['material']}",
                "",
                f"- rows compared: `{int(row['n_rows'])}`",
                f"- `Gamma_X` MAE: `{row['gamma_hat_x_cp_sys_mae']:.6f}` (max `{row['gamma_hat_x_cp_sys_max_abs_diff']:.6f}`)",
                f"- `Gamma_C_raw` MAE: `{row['gamma_hat_c_cp_raw_mae']:.6f}` (max `{row['gamma_hat_c_cp_raw_max_abs_diff']:.6f}`)",
                f"- `Gamma_C_eff` MAE: `{row['gamma_hat_c_cp_eff_mae']:.6f}` (max `{row['gamma_hat_c_cp_eff_max_abs_diff']:.6f}`)",
                "",
            ]
        )
    md_lines.extend(
        [
            "## Interpretation",
            "",
            "- If the absolute differences stay at only a few `1e-3` to `1e-2`, the new sweep files are effectively the same CP dataset expressed in the same normalization convention.",
            "- Any residual mismatch then comes from Stage 3 band processing / interpolation / frequency-window handling, not from a different branch convention.",
            "",
            "## Outputs",
            "",
            f"- full comparison: `{out_dir / 'sweep_vs_stage3_cp_full.csv'}`",
            f"- summary: `{out_dir / 'sweep_vs_stage3_cp_summary.csv'}`",
            f"- reconstructed sweep CP: `{out_dir / 'sweep_reconstructed_cp_6p5ghz.csv'}`",
        ]
    )
    (out_dir / "SANITY_SWEEP_VS_STAGE3_CP.md").write_text("\n".join(md_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
