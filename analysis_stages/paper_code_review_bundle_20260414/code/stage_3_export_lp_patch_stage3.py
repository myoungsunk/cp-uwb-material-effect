# Consolidated review copy for paper-pipeline code assessment.
# Stage: 3
# Role: Export LP patch-stage tables aligned to the paper-final grid.
# Source: analysis_stages/stage3_patch_paper_final_20260414/lp/code/export_patch_lp_stage3.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


LP_CHANNELS = ["yy", "yz", "zy", "zz"]
MATERIALS = ["metal", "concrete", "glass", "wood"]
MATERIAL_MAIN_MAX = {"concrete": 55.0, "glass": 60.0, "wood": 45.0}


def parse_complex(magnitude: np.ndarray, phase_deg: np.ndarray) -> np.ndarray:
    return magnitude * np.exp(1j * np.deg2rad(phase_deg))


def load_m1_lp(path: Path) -> dict[str, np.ndarray]:
    df = pd.read_csv(path)
    out = {"freq_ghz": df.iloc[:, 0].to_numpy(dtype=float)}
    channel_cols = {
        "yy": (
            "mag(S(Rx_y_p1,Tx_y_p1)) []",
            "ang_deg(S(Rx_y_p1,Tx_y_p1)) [deg]",
        ),
        "yz": (
            "mag(S(Rx_y_p1,Tx_z_p1)) []",
            "ang_deg(S(Rx_y_p1,Tx_z_p1)) [deg]",
        ),
        "zy": (
            "mag(S(Rx_z_p1,Tx_y_p1)) []",
            "ang_deg(S(Rx_z_p1,Tx_y_p1)) [deg]",
        ),
        "zz": (
            "mag(S(Rx_z_p1,Tx_z_p1)) []",
            "ang_deg(S(Rx_z_p1,Tx_z_p1)) [deg]",
        ),
    }
    for ch, (mag_col, phase_col) in channel_cols.items():
        out[ch] = parse_complex(
            df[mag_col].to_numpy(dtype=float),
            df[phase_col].to_numpy(dtype=float),
        )
    return out


def load_sweep_lp(path: Path) -> dict:
    df = pd.read_csv(path)
    theta_col = df.columns[0]
    freq_col = df.columns[1]
    thetas = np.array(sorted(df[theta_col].unique()), dtype=float)
    freq = df[df[theta_col] == thetas[0]][freq_col].to_numpy(dtype=float)
    out = {"freq_ghz": freq, "thetas_deg": thetas}
    channel_cols = {
        "yy": (
            "mag(S(Rx_y_p1,Tx_y_p1)) []",
            "ang_deg(S(Rx_y_p1,Tx_y_p1)) [deg]",
        ),
        "yz": (
            "mag(S(Rx_y_p1,Tx_z_p1)) []",
            "ang_deg(S(Rx_y_p1,Tx_z_p1)) [deg]",
        ),
        "zy": (
            "mag(S(Rx_z_p1,Tx_y_p1)) []",
            "ang_deg(S(Rx_z_p1,Tx_y_p1)) [deg]",
        ),
        "zz": (
            "mag(S(Rx_z_p1,Tx_z_p1)) []",
            "ang_deg(S(Rx_z_p1,Tx_z_p1)) [deg]",
        ),
    }
    for theta in thetas:
        sub = df[df[theta_col] == theta]
        out[theta] = {}
        for ch, (mag_col, phase_col) in channel_cols.items():
            out[theta][ch] = parse_complex(
                sub[mag_col].to_numpy(dtype=float),
                sub[phase_col].to_numpy(dtype=float),
            )
    return out


def mean_complex(values: np.ndarray) -> complex:
    return complex(np.mean(values))


def mean_abs(values: np.ndarray) -> float:
    return float(np.mean(np.abs(values)))


def db20(value: float) -> float:
    return float(20.0 * np.log10(max(value, 1e-12)))


def cp_from_te_tm(r_te: np.ndarray, r_tm: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    gamma_x = (r_te + r_tm) / 2.0
    gamma_c = (r_te - r_tm) / 2.0
    return gamma_x, gamma_c


def add_band_complex_export(
    row: dict[str, float | bool | str],
    prefix: str,
    mean_value: complex,
    values: np.ndarray,
) -> None:
    mean_of_abs_value = mean_abs(values)
    row[f"{prefix}_real"] = float(mean_value.real)
    row[f"{prefix}_imag"] = float(mean_value.imag)
    row[f"{prefix}_mag"] = mean_of_abs_value
    row[f"{prefix}_abs_of_mean"] = float(np.abs(mean_value))
    row[f"{prefix}_mean_of_abs"] = mean_of_abs_value


def add_pointwise_complex_export(
    row: dict[str, float | bool | str],
    prefix: str,
    value: complex,
) -> None:
    mag = float(np.abs(value))
    row[f"{prefix}_real"] = float(np.real(value))
    row[f"{prefix}_imag"] = float(np.imag(value))
    row[f"{prefix}_mag"] = mag
    row[f"{prefix}_abs_of_mean"] = mag
    row[f"{prefix}_mean_of_abs"] = mag


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export paper-final Stage 3 LP patch tables in an isolated workspace."
    )
    stage_root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--csv-dir",
        type=Path,
        default=stage_root / "csv",
        help="Directory with copied LP patch CSV inputs.",
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

    m1 = load_m1_lp(csv_dir / "LP_m1_los_5000.csv")
    m3 = load_sweep_lp(csv_dir / "LP_m3_off-boresigjt.csv")
    m2 = {mat: load_sweep_lp(csv_dir / f"LP_m2_{mat}_R_5000.csv") for mat in MATERIALS}

    freq = m1["freq_ghz"]
    thetas = m3["thetas_deg"]

    band_rows: list[dict] = []
    freq_rows: list[dict] = []

    for material in MATERIALS:
        for theta in thetas:
            h2 = m2[material][theta]
            h3 = m3[theta]
            h_tilde = {ch: h2[ch] - m1[ch] for ch in LP_CHANNELS}

            r_yy = h_tilde["yy"] / h3["yy"]
            r_zz = h_tilde["zz"] / h3["zz"]
            r_yz = h_tilde["yz"] / h3["yy"]
            r_zy = h_tilde["zy"] / h3["zz"]
            gamma_x, gamma_c = cp_from_te_tm(r_zz, r_yy)

            r_yy_mean = mean_complex(r_yy)
            r_zz_mean = mean_complex(r_zz)
            r_yz_mean = mean_complex(r_yz)
            r_zy_mean = mean_complex(r_zy)
            gamma_x_mean = mean_complex(gamma_x)
            gamma_c_mean = mean_complex(gamma_c)

            leakage_yz_db = db20(mean_abs(r_yz))
            leakage_zy_db = db20(mean_abs(r_zy))
            leakage_max_db = max(leakage_yz_db, leakage_zy_db)

            use_for_main = (
                material in MATERIAL_MAIN_MAX
                and theta <= MATERIAL_MAIN_MAX[material]
                and leakage_max_db <= -15.0
            )

            if material == "metal":
                note = "Calibration/reference only; keep out of material main claims."
            elif use_for_main:
                note = "Candidate main-claim LP patch row after Stage 4 merge."
            else:
                note = "Outside the material-specific range or leakage threshold."

            band_row: dict[str, float | bool | str] = {
                "material": material,
                "theta_deg": float(theta),
                "freq_start_ghz": float(freq[0]),
                "freq_stop_ghz": float(freq[-1]),
                "freq_center_ghz": float(np.mean(freq)),
                "n_freq": int(len(freq)),
                "leakage_yz_db": leakage_yz_db,
                "leakage_zy_db": leakage_zy_db,
                "leakage_max_db": leakage_max_db,
                "use_for_main_claim_candidate": bool(use_for_main),
                "note": note,
            }
            add_band_complex_export(band_row, "r_hat_yy_sys", r_yy_mean, r_yy)
            add_band_complex_export(band_row, "r_hat_zz_sys", r_zz_mean, r_zz)
            add_band_complex_export(band_row, "r_hat_yz_sys", r_yz_mean, r_yz)
            add_band_complex_export(band_row, "r_hat_zy_sys", r_zy_mean, r_zy)
            add_band_complex_export(band_row, "gamma_x_from_lp", gamma_x_mean, gamma_x)
            add_band_complex_export(band_row, "gamma_c_from_lp", gamma_c_mean, gamma_c)
            band_row["B_lp_sys_mag"] = max(
                float(band_row["r_hat_yy_sys_mag"]),
                float(band_row["r_hat_zz_sys_mag"]),
            )
            band_row["G_lp_sys_db"] = db20(
                float(band_row["B_lp_sys_mag"]) / max(float(band_row["gamma_x_from_lp_mag"]), 1e-12)
            )
            band_rows.append(band_row)

            if args.write_freq_resolved:
                for idx, freq_ghz in enumerate(freq):
                    freq_row: dict[str, float | bool | str] = {
                        "material": material,
                        "theta_deg": float(theta),
                        "freq_ghz": float(freq_ghz),
                    }
                    add_pointwise_complex_export(freq_row, "r_hat_yy_sys", r_yy[idx])
                    add_pointwise_complex_export(freq_row, "r_hat_zz_sys", r_zz[idx])
                    add_pointwise_complex_export(freq_row, "r_hat_yz_sys", r_yz[idx])
                    add_pointwise_complex_export(freq_row, "r_hat_zy_sys", r_zy[idx])
                    add_pointwise_complex_export(freq_row, "gamma_x_from_lp", gamma_x[idx])
                    add_pointwise_complex_export(freq_row, "gamma_c_from_lp", gamma_c[idx])
                    freq_row["B_lp_sys_mag"] = max(
                        float(freq_row["r_hat_yy_sys_mag"]),
                        float(freq_row["r_hat_zz_sys_mag"]),
                    )
                    freq_row["G_lp_sys_db"] = db20(
                        float(freq_row["B_lp_sys_mag"]) / max(float(freq_row["gamma_x_from_lp_mag"]), 1e-12)
                    )
                    freq_rows.append(freq_row)

    band_df = pd.DataFrame(band_rows).sort_values(["material", "theta_deg"]).reset_index(drop=True)
    band_path = output_dir / "patch_lp_extracted.csv"
    band_df.to_csv(band_path, index=False)
    print(f"Wrote {band_path}")
    print(f"Rows: {len(band_df)}")

    if args.write_freq_resolved:
        freq_df = pd.DataFrame(freq_rows).sort_values(["material", "theta_deg", "freq_ghz"]).reset_index(drop=True)
        freq_path = output_dir / "patch_lp_extracted_freq_resolved.csv"
        freq_df.to_csv(freq_path, index=False)
        print(f"Wrote {freq_path}")
        print(f"Rows: {len(freq_df)}")


if __name__ == "__main__":
    main()
