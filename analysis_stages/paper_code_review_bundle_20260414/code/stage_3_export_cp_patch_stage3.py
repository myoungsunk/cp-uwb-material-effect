# Consolidated review copy for paper-pipeline code assessment.
# Stage: 3
# Role: Export band-averaged CP patch-stage tables used by later suppression analyses.
# Source: analysis_stages/stage3_patch_paper_final_20260414/cp/code/export_patch_cp_stage3.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


CHANNELS = ["LL", "LR", "RL", "RR"]
MATERIALS = ["metal", "concrete", "glass", "wood"]
MATERIAL_MAIN_MAX = {"concrete": 55.0, "glass": 60.0, "wood": 45.0}


def parse_complex(magnitude: np.ndarray, phase_deg: np.ndarray) -> np.ndarray:
    return magnitude * np.exp(1j * np.deg2rad(phase_deg))


def load_m1(path: Path) -> dict[str, np.ndarray]:
    df = pd.read_csv(path)
    cols = df.columns.tolist()
    out = {"freq_ghz": df[cols[0]].to_numpy(dtype=float)}
    for i, ch in enumerate(CHANNELS):
        out[ch] = parse_complex(
            df[cols[1 + 2 * i]].to_numpy(dtype=float),
            df[cols[2 + 2 * i]].to_numpy(dtype=float),
        )
    return out


def load_sweep(path: Path) -> dict:
    df = pd.read_csv(path)
    cols = df.columns.tolist()
    thetas = np.array(sorted(df[cols[0]].unique()), dtype=float)
    freq = df[df[cols[0]] == thetas[0]][cols[1]].to_numpy(dtype=float)
    out = {"freq_ghz": freq, "thetas_deg": thetas}
    for theta in thetas:
        sub = df[df[cols[0]] == theta]
        out[theta] = {}
        for i, ch in enumerate(CHANNELS):
            out[theta][ch] = parse_complex(
                sub[cols[2 + 2 * i]].to_numpy(dtype=float),
                sub[cols[3 + 2 * i]].to_numpy(dtype=float),
            )
    return out


def db20(value: float) -> float:
    return float(20.0 * np.log10(max(value, 1e-12)))


def mean_complex(values: np.ndarray) -> complex:
    return complex(np.mean(values))


def mean_abs(values: np.ndarray) -> float:
    return float(np.mean(np.abs(values)))


def anchored_geometric_mean(ratio, anchor_approx):
    """Resolve the sqrt-branch sign using a single-branch phase anchor."""
    candidate = np.sqrt(np.abs(ratio)) * np.exp(1j * np.angle(ratio) / 2)
    candidate_arr = np.atleast_1d(np.asarray(candidate, dtype=complex)).copy()
    anchor_arr = np.atleast_1d(np.asarray(anchor_approx, dtype=complex))
    valid = np.abs(anchor_arr) > 1e-18
    phase_delta = np.zeros(candidate_arr.shape, dtype=float)
    phase_delta[valid] = np.angle(candidate_arr[valid] / anchor_arr[valid])
    flip = valid & (np.abs(phase_delta) > (np.pi / 2))
    candidate_arr[flip] *= -1.0
    if np.ndim(candidate) == 0:
        return complex(candidate_arr[0])
    return candidate_arr


def keep_final_theta(theta_deg: float) -> bool:
    nearest = round(theta_deg / 5.0) * 5.0
    return abs(theta_deg - nearest) < 1e-9


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export paper-final Stage 3 CP patch tables in an isolated workspace."
    )
    stage_root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--csv-dir",
        type=Path,
        default=stage_root / "csv",
        help="Directory with copied CP patch CSV inputs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=stage_root / "results",
        help="Directory where exported tables are written.",
    )
    parser.add_argument(
        "--write-freq-resolved",
        action="store_true",
        help="Also write a frequency-resolved auxiliary CSV.",
    )
    return parser


def main() -> None:
    args = build_argparser().parse_args()
    csv_dir = args.csv_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    m1 = load_m1(csv_dir / "m1_los_5000.csv")
    m3 = load_sweep(csv_dir / "m3_off-boresigjt.csv")
    m2 = {mat: load_sweep(csv_dir / f"m2_{mat}_R_5000.csv") for mat in MATERIALS}

    freq = m1["freq_ghz"]
    thetas = m3["thetas_deg"]

    band_rows: list[dict] = []
    freq_rows: list[dict] = []

    for theta in thetas:
        h3 = m3[theta]
        leakage_lr_rr_db = db20(np.mean(np.abs(h3["LR"]) / np.maximum(np.abs(h3["RR"]), 1e-12)))
        leakage_rl_ll_db = db20(np.mean(np.abs(h3["RL"]) / np.maximum(np.abs(h3["LL"]), 1e-12)))
        port_asym_db = db20(np.mean(np.abs(h3["RR"])) / max(np.mean(np.abs(h3["LL"])), 1e-12))
        eps_eff = h3["LR"] / h3["RR"]

        for material in MATERIALS:
            h2 = m2[material][theta]
            h_tilde = {ch: h2[ch] - m1[ch] for ch in CHANNELS}

            ratio = (h_tilde["LR"] * h_tilde["RL"]) / (h3["RR"] * h3["LL"])
            gamma_x = anchored_geometric_mean(ratio, h_tilde["LR"] / h3["RR"])
            gamma_c_raw = h_tilde["RR"] / h3["RR"]
            gamma_c_eff = gamma_c_raw - eps_eff * gamma_x
            r_te_proxy = gamma_x + gamma_c_eff
            r_tm_proxy = gamma_x - gamma_c_eff
            gamma_lr_single = h_tilde["LR"] / h3["RR"]
            gamma_rl_single = h_tilde["RL"] / h3["LL"]

            reciprocity_dev_db = db20(
                mean_abs(gamma_lr_single) / max(mean_abs(gamma_rl_single), 1e-12)
            )

            gamma_x_mean = mean_complex(gamma_x)
            gamma_c_raw_mean = mean_complex(gamma_c_raw)
            gamma_c_eff_mean = mean_complex(gamma_c_eff)
            r_te_mean = mean_complex(r_te_proxy)
            r_tm_mean = mean_complex(r_tm_proxy)

            use_for_main = (
                material in MATERIAL_MAIN_MAX
                and theta <= MATERIAL_MAIN_MAX[material]
                and keep_final_theta(theta)
            )

            if material == "metal":
                note = "Calibration/reference only; keep out of material main claims."
            elif not keep_final_theta(theta):
                note = "Dropped from paper-final angle lock because theta is not on the ideal 5 deg grid."
            elif use_for_main:
                note = "Candidate main-claim patch CP row after Stage 4 merge."
            else:
                note = "Outside the material-specific paper main range."

            if keep_final_theta(theta):
                band_rows.append(
                    {
                        "material": material,
                        "theta_deg": float(theta),
                        "freq_start_ghz": float(freq[0]),
                        "freq_stop_ghz": float(freq[-1]),
                        "freq_center_ghz": float(np.mean(freq)),
                        "n_freq": int(len(freq)),
                        "gamma_hat_x_cp_sys_real": float(gamma_x_mean.real),
                        "gamma_hat_x_cp_sys_imag": float(gamma_x_mean.imag),
                        "gamma_hat_x_cp_sys_mag": mean_abs(gamma_x),
                        "gamma_hat_c_cp_raw_real": float(gamma_c_raw_mean.real),
                        "gamma_hat_c_cp_raw_imag": float(gamma_c_raw_mean.imag),
                        "gamma_hat_c_cp_raw_mag": mean_abs(gamma_c_raw),
                        "gamma_hat_c_cp_eff_real": float(gamma_c_eff_mean.real),
                        "gamma_hat_c_cp_eff_imag": float(gamma_c_eff_mean.imag),
                        "gamma_hat_c_cp_eff_mag": mean_abs(gamma_c_eff),
                        "r_te_proxy_real": float(r_te_mean.real),
                        "r_te_proxy_imag": float(r_te_mean.imag),
                        "r_te_proxy_mag": mean_abs(r_te_proxy),
                        "r_tm_proxy_real": float(r_tm_mean.real),
                        "r_tm_proxy_imag": float(r_tm_mean.imag),
                        "r_tm_proxy_mag": mean_abs(r_tm_proxy),
                        "xpd_eff_db": db20(
                            mean_abs(gamma_x) / max(mean_abs(gamma_c_eff), 1e-12)
                        ),
                        "reciprocity_dev_db": reciprocity_dev_db,
                        "leakage_lr_rr_db": leakage_lr_rr_db,
                        "leakage_rl_ll_db": leakage_rl_ll_db,
                        "port_asym_db": port_asym_db,
                        "use_for_main_claim_candidate": bool(use_for_main),
                        "note": note,
                    }
                )

            if args.write_freq_resolved and keep_final_theta(theta):
                for idx, freq_ghz in enumerate(freq):
                    freq_rows.append(
                        {
                            "material": material,
                            "theta_deg": float(theta),
                            "freq_ghz": float(freq_ghz),
                            "gamma_hat_x_cp_sys_real": float(np.real(gamma_x[idx])),
                            "gamma_hat_x_cp_sys_imag": float(np.imag(gamma_x[idx])),
                            "gamma_hat_x_cp_sys_mag": float(np.abs(gamma_x[idx])),
                            "gamma_hat_c_cp_raw_real": float(np.real(gamma_c_raw[idx])),
                            "gamma_hat_c_cp_raw_imag": float(np.imag(gamma_c_raw[idx])),
                            "gamma_hat_c_cp_raw_mag": float(np.abs(gamma_c_raw[idx])),
                            "gamma_hat_c_cp_eff_real": float(np.real(gamma_c_eff[idx])),
                            "gamma_hat_c_cp_eff_imag": float(np.imag(gamma_c_eff[idx])),
                            "gamma_hat_c_cp_eff_mag": float(np.abs(gamma_c_eff[idx])),
                            "r_te_proxy_real": float(np.real(r_te_proxy[idx])),
                            "r_te_proxy_imag": float(np.imag(r_te_proxy[idx])),
                            "r_te_proxy_mag": float(np.abs(r_te_proxy[idx])),
                            "r_tm_proxy_real": float(np.real(r_tm_proxy[idx])),
                            "r_tm_proxy_imag": float(np.imag(r_tm_proxy[idx])),
                            "r_tm_proxy_mag": float(np.abs(r_tm_proxy[idx])),
                        }
                    )

    band_df = pd.DataFrame(band_rows).sort_values(["material", "theta_deg"]).reset_index(drop=True)
    band_path = output_dir / "patch_cp_extracted.csv"
    band_df.to_csv(band_path, index=False)
    print(f"Wrote {band_path}")
    print(f"Rows: {len(band_df)}")

    if args.write_freq_resolved:
        freq_df = pd.DataFrame(freq_rows).sort_values(["material", "theta_deg", "freq_ghz"]).reset_index(drop=True)
        freq_path = output_dir / "patch_cp_extracted_freq_resolved.csv"
        freq_df.to_csv(freq_path, index=False)
        print(f"Wrote {freq_path}")
        print(f"Rows: {len(freq_df)}")


if __name__ == "__main__":
    main()
