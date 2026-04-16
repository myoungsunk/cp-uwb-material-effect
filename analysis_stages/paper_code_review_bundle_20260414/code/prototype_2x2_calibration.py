from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


STAGE_TO_TRUTH_MATERIAL = {
    "metal": "pec",
    "concrete": "concrete",
    "glass": "glass",
    "wood": "wood",
}
CP_CHANNELS = ["LL", "LR", "RL", "RR"]
LP_CHANNELS = ["yy", "yz", "zy", "zz"]
SYSTEMS = ["lp", "cp"]
TARGET_FREQ_GHZ = 6.5
ALS_MAX_ITER = 100
ALS_TOL = 1e-12


def build_argparser() -> argparse.ArgumentParser:
    bundle_root = Path(__file__).resolve().parent.parent
    stage3_root = Path(__file__).resolve().parents[2] / "stage3_patch_paper_final_20260414"
    parser = argparse.ArgumentParser(
        description=(
            "Prototype 2x2 calibration fit using single-frequency truth at 6.5 GHz. "
            "This is a supervised prototype, not a headline-ready pipeline replacement."
        )
    )
    parser.add_argument(
        "--linear-truth",
        type=Path,
        default=bundle_root / "data" / "stage_1" / "truth_table_linear_locked.csv",
    )
    parser.add_argument(
        "--cp-truth",
        type=Path,
        default=bundle_root / "data" / "stage_2" / "sameflip_alias_20260415" / "truth_table_cp_shared_common_sameflip.csv",
    )
    parser.add_argument(
        "--cp-csv-dir",
        type=Path,
        default=stage3_root / "cp" / "csv",
    )
    parser.add_argument(
        "--lp-csv-dir",
        type=Path,
        default=stage3_root / "lp" / "csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=bundle_root / "results" / "debug",
    )
    return parser


def parse_complex(magnitude: np.ndarray, phase_deg: np.ndarray) -> np.ndarray:
    return magnitude * np.exp(1j * np.deg2rad(phase_deg))


def load_m1_cp(path: Path) -> dict[str, np.ndarray]:
    df = pd.read_csv(path)
    cols = df.columns.tolist()
    out = {"freq_ghz": df[cols[0]].to_numpy(dtype=float)}
    for idx, ch in enumerate(CP_CHANNELS):
        out[ch] = parse_complex(
            df[cols[1 + 2 * idx]].to_numpy(dtype=float),
            df[cols[2 + 2 * idx]].to_numpy(dtype=float),
        )
    return out


def load_sweep_cp(path: Path) -> dict[float, dict[str, np.ndarray]] | dict[str, np.ndarray]:
    df = pd.read_csv(path)
    cols = df.columns.tolist()
    thetas = np.array(sorted(df[cols[0]].unique()), dtype=float)
    freq = df[df[cols[0]] == thetas[0]][cols[1]].to_numpy(dtype=float)
    out: dict[object, object] = {"freq_ghz": freq, "thetas_deg": thetas}
    for theta in thetas:
        sub = df[df[cols[0]] == theta]
        out[float(theta)] = {}
        for idx, ch in enumerate(CP_CHANNELS):
            out[float(theta)][ch] = parse_complex(
                sub[cols[2 + 2 * idx]].to_numpy(dtype=float),
                sub[cols[3 + 2 * idx]].to_numpy(dtype=float),
            )
    return out


def load_m1_lp(path: Path) -> dict[str, np.ndarray]:
    df = pd.read_csv(path)
    out = {"freq_ghz": df.iloc[:, 0].to_numpy(dtype=float)}
    channel_cols = {
        "yy": ("mag(S(Rx_y_p1,Tx_y_p1)) []", "ang_deg(S(Rx_y_p1,Tx_y_p1)) [deg]"),
        "yz": ("mag(S(Rx_y_p1,Tx_z_p1)) []", "ang_deg(S(Rx_y_p1,Tx_z_p1)) [deg]"),
        "zy": ("mag(S(Rx_z_p1,Tx_y_p1)) []", "ang_deg(S(Rx_z_p1,Tx_y_p1)) [deg]"),
        "zz": ("mag(S(Rx_z_p1,Tx_z_p1)) []", "ang_deg(S(Rx_z_p1,Tx_z_p1)) [deg]"),
    }
    for ch, (mag_col, phase_col) in channel_cols.items():
        out[ch] = parse_complex(
            df[mag_col].to_numpy(dtype=float),
            df[phase_col].to_numpy(dtype=float),
        )
    return out


def load_sweep_lp(path: Path) -> dict[float, dict[str, np.ndarray]] | dict[str, np.ndarray]:
    df = pd.read_csv(path)
    theta_col = df.columns[0]
    freq_col = df.columns[1]
    thetas = np.array(sorted(df[theta_col].unique()), dtype=float)
    freq = df[df[theta_col] == thetas[0]][freq_col].to_numpy(dtype=float)
    out: dict[object, object] = {"freq_ghz": freq, "thetas_deg": thetas}
    channel_cols = {
        "yy": ("mag(S(Rx_y_p1,Tx_y_p1)) []", "ang_deg(S(Rx_y_p1,Tx_y_p1)) [deg]"),
        "yz": ("mag(S(Rx_y_p1,Tx_z_p1)) []", "ang_deg(S(Rx_y_p1,Tx_z_p1)) [deg]"),
        "zy": ("mag(S(Rx_z_p1,Tx_y_p1)) []", "ang_deg(S(Rx_z_p1,Tx_y_p1)) [deg]"),
        "zz": ("mag(S(Rx_z_p1,Tx_z_p1)) []", "ang_deg(S(Rx_z_p1,Tx_z_p1)) [deg]"),
    }
    for theta in thetas:
        sub = df[df[theta_col] == theta]
        out[float(theta)] = {}
        for ch, (mag_col, phase_col) in channel_cols.items():
            out[float(theta)][ch] = parse_complex(
                sub[mag_col].to_numpy(dtype=float),
                sub[phase_col].to_numpy(dtype=float),
            )
    return out


def nearest_index(freq: np.ndarray, target_freq_ghz: float) -> int:
    return int(np.argmin(np.abs(freq - target_freq_ghz)))


def matrix_rows_to_dict(prefix: str, matrix: np.ndarray) -> dict[str, float]:
    return {
        f"{prefix}_11_real": float(np.real(matrix[0, 0])),
        f"{prefix}_11_imag": float(np.imag(matrix[0, 0])),
        f"{prefix}_12_real": float(np.real(matrix[0, 1])),
        f"{prefix}_12_imag": float(np.imag(matrix[0, 1])),
        f"{prefix}_21_real": float(np.real(matrix[1, 0])),
        f"{prefix}_21_imag": float(np.imag(matrix[1, 0])),
        f"{prefix}_22_real": float(np.real(matrix[1, 1])),
        f"{prefix}_22_imag": float(np.imag(matrix[1, 1])),
        f"{prefix}_fro_norm": float(np.linalg.norm(matrix)),
    }


def solve_j_rx(samples: list[tuple[np.ndarray, np.ndarray]], j_tx: np.ndarray) -> np.ndarray:
    j_rx = np.zeros((2, 2), dtype=complex)
    for row_idx in range(2):
        a_stack = []
        b_stack = []
        for h_meas, s_truth in samples:
            a_stack.append((s_truth @ j_tx).T)
            b_stack.append(h_meas[row_idx, :])
        solution, *_ = np.linalg.lstsq(np.vstack(a_stack), np.concatenate(b_stack), rcond=None)
        j_rx[row_idx, :] = solution
    return j_rx


def solve_j_tx(samples: list[tuple[np.ndarray, np.ndarray]], j_rx: np.ndarray) -> np.ndarray:
    j_tx = np.zeros((2, 2), dtype=complex)
    for col_idx in range(2):
        b_stack = []
        y_stack = []
        for h_meas, s_truth in samples:
            b_stack.append(j_rx @ s_truth)
            y_stack.append(h_meas[:, col_idx])
        solution, *_ = np.linalg.lstsq(np.vstack(b_stack), np.concatenate(y_stack), rcond=None)
        j_tx[:, col_idx] = solution
    return j_tx


def fit_error(samples: list[tuple[np.ndarray, np.ndarray]], j_rx: np.ndarray, j_tx: np.ndarray) -> float:
    sq = 0.0
    count = 0
    for h_meas, s_truth in samples:
        residual = h_meas - j_rx @ s_truth @ j_tx
        sq += float(np.linalg.norm(residual) ** 2)
        count += residual.size
    return float(np.sqrt(sq / max(count, 1)))


def solve_als(samples: list[tuple[np.ndarray, np.ndarray]]) -> tuple[np.ndarray, np.ndarray, int, float]:
    j_rx = np.eye(2, dtype=complex)
    j_tx = np.eye(2, dtype=complex)
    prev = np.inf
    final_error = np.inf
    for iteration in range(1, ALS_MAX_ITER + 1):
        j_rx = solve_j_rx(samples, j_tx)
        j_tx = solve_j_tx(samples, j_rx)
        scale = j_tx[0, 0]
        if abs(scale) > 1e-12:
            j_tx = j_tx / scale
            j_rx = j_rx * scale
        final_error = fit_error(samples, j_rx, j_tx)
        if abs(prev - final_error) <= ALS_TOL:
            return j_rx, j_tx, iteration, final_error
        prev = final_error
    return j_rx, j_tx, ALS_MAX_ITER, final_error


def lp_truth_matrix(row: pd.Series) -> np.ndarray:
    r_tm = complex(row["R_TM_locked_real"], row["R_TM_locked_imag"])
    r_te = complex(row["R_TE_locked_real"], row["R_TE_locked_imag"])
    return np.array([[r_tm, 0.0 + 0.0j], [0.0 + 0.0j, r_te]], dtype=complex)


def cp_truth_matrix(row: pd.Series) -> np.ndarray:
    gamma_same = complex(row["Gamma_same_real"], row["Gamma_same_imag"])
    gamma_flip = complex(row["Gamma_flip_real"], row["Gamma_flip_imag"])
    return np.array([[gamma_same, gamma_flip], [gamma_flip, gamma_same]], dtype=complex)


def lp_branch_dict(s_hat: np.ndarray) -> dict[str, complex]:
    r_tm = complex(s_hat[0, 0])
    r_te = complex(s_hat[1, 1])
    return {
        "R_TM_hat": r_tm,
        "R_TE_hat": r_te,
        "Gamma_X_hat": (r_te + r_tm) / 2.0,
        "Gamma_C_hat": (r_te - r_tm) / 2.0,
    }


def cp_branch_dict(s_hat: np.ndarray) -> dict[str, complex]:
    gamma_same = (complex(s_hat[0, 0]) + complex(s_hat[1, 1])) / 2.0
    gamma_flip = (complex(s_hat[0, 1]) + complex(s_hat[1, 0])) / 2.0
    return {
        "Gamma_same_hat": gamma_same,
        "Gamma_flip_hat": gamma_flip,
    }


def collect_samples_lp(
    linear_truth: pd.DataFrame,
    lp_csv_dir: Path,
) -> tuple[dict[float, list[tuple[str, np.ndarray, np.ndarray]]], float]:
    m1 = load_m1_lp(lp_csv_dir / "LP_m1_los_5000.csv")
    m2 = {material: load_sweep_lp(lp_csv_dir / f"LP_m2_{material}_R_5000.csv") for material in STAGE_TO_TRUTH_MATERIAL}
    freq_idx = nearest_index(m1["freq_ghz"], TARGET_FREQ_GHZ)

    grouped: dict[float, list[tuple[str, np.ndarray, np.ndarray]]] = {}
    for stage_material, truth_material in STAGE_TO_TRUTH_MATERIAL.items():
        truth_sub = linear_truth[linear_truth["material"].str.lower() == truth_material].copy()
        for _, row in truth_sub.iterrows():
            theta_deg = float(row["theta_deg"])
            if theta_deg not in m2[stage_material]:
                continue
            h2 = m2[stage_material][theta_deg]
            h_meas = np.array(
                [
                    [h2["yy"][freq_idx] - m1["yy"][freq_idx], h2["yz"][freq_idx] - m1["yz"][freq_idx]],
                    [h2["zy"][freq_idx] - m1["zy"][freq_idx], h2["zz"][freq_idx] - m1["zz"][freq_idx]],
                ],
                dtype=complex,
            )
            grouped.setdefault(theta_deg, []).append((stage_material, h_meas, lp_truth_matrix(row)))
    return grouped, float(m1["freq_ghz"][freq_idx])


def collect_samples_cp(
    cp_truth: pd.DataFrame,
    cp_csv_dir: Path,
) -> tuple[dict[float, list[tuple[str, np.ndarray, np.ndarray]]], float]:
    m1 = load_m1_cp(cp_csv_dir / "m1_los_5000.csv")
    m2 = {material: load_sweep_cp(cp_csv_dir / f"m2_{material}_R_5000.csv") for material in STAGE_TO_TRUTH_MATERIAL}
    freq_idx = nearest_index(m1["freq_ghz"], TARGET_FREQ_GHZ)

    grouped: dict[float, list[tuple[str, np.ndarray, np.ndarray]]] = {}
    for stage_material, truth_material in STAGE_TO_TRUTH_MATERIAL.items():
        truth_sub = cp_truth[cp_truth["material"].str.lower() == truth_material].copy()
        for _, row in truth_sub.iterrows():
            theta_deg = float(row["theta_deg"])
            if theta_deg not in m2[stage_material]:
                continue
            h2 = m2[stage_material][theta_deg]
            h_meas = np.array(
                [
                    [h2["LL"][freq_idx] - m1["LL"][freq_idx], h2["LR"][freq_idx] - m1["LR"][freq_idx]],
                    [h2["RL"][freq_idx] - m1["RL"][freq_idx], h2["RR"][freq_idx] - m1["RR"][freq_idx]],
                ],
                dtype=complex,
            )
            grouped.setdefault(theta_deg, []).append((stage_material, h_meas, cp_truth_matrix(row)))
    return grouped, float(m1["freq_ghz"][freq_idx])


def run_system(
    system_id: str,
    grouped_samples: dict[float, list[tuple[str, np.ndarray, np.ndarray]]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    matrix_rows: list[dict[str, object]] = []
    sample_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []

    for theta_deg in sorted(grouped_samples):
        samples = [(h_meas, s_truth) for _, h_meas, s_truth in grouped_samples[theta_deg]]
        if len(samples) < 3:
            continue
        j_rx, j_tx, iterations, rms_error = solve_als(samples)
        j_rx_inv = np.linalg.pinv(j_rx)
        j_tx_inv = np.linalg.pinv(j_tx)

        matrix_row: dict[str, object] = {
            "system_id": system_id,
            "theta_deg": float(theta_deg),
            "n_samples": int(len(samples)),
            "als_iterations": int(iterations),
            "fit_rms_error": float(rms_error),
            "cond_j_rx": float(np.linalg.cond(j_rx)),
            "cond_j_tx": float(np.linalg.cond(j_tx)),
        }
        matrix_row.update(matrix_rows_to_dict("j_rx", j_rx))
        matrix_row.update(matrix_rows_to_dict("j_tx", j_tx))
        matrix_rows.append(matrix_row)

        branch_error_values: list[float] = []
        matrix_error_values: list[float] = []
        for material, h_meas, s_truth in grouped_samples[theta_deg]:
            h_fit = j_rx @ s_truth @ j_tx
            s_hat = j_rx_inv @ h_meas @ j_tx_inv
            matrix_error = float(np.linalg.norm(s_hat - s_truth))
            matrix_error_values.append(matrix_error)

            sample_row: dict[str, object] = {
                "system_id": system_id,
                "theta_deg": float(theta_deg),
                "material": material,
                "s_hat_error_fro": matrix_error,
                "measurement_fit_error_fro": float(np.linalg.norm(h_meas - h_fit)),
            }
            sample_row.update(matrix_rows_to_dict("h_meas", h_meas))
            sample_row.update(matrix_rows_to_dict("s_truth", s_truth))
            sample_row.update(matrix_rows_to_dict("s_hat", s_hat))

            if system_id == "lp":
                hat = lp_branch_dict(s_hat)
                truth = lp_branch_dict(s_truth)
                for key, truth_value in truth.items():
                    err = abs(hat[key] - truth_value)
                    sample_row[f"{key}_truth_mag"] = float(abs(truth_value))
                    sample_row[f"{key}_hat_mag"] = float(abs(hat[key]))
                    sample_row[f"{key}_complex_abs_error"] = float(err)
                    branch_error_values.append(float(err))
            else:
                hat = cp_branch_dict(s_hat)
                truth = cp_branch_dict(s_truth)
                for key, truth_value in truth.items():
                    err = abs(hat[key] - truth_value)
                    sample_row[f"{key}_truth_mag"] = float(abs(truth_value))
                    sample_row[f"{key}_hat_mag"] = float(abs(hat[key]))
                    sample_row[f"{key}_complex_abs_error"] = float(err)
                    branch_error_values.append(float(err))

            sample_rows.append(sample_row)

        summary_rows.append(
            {
                "system_id": system_id,
                "theta_deg": float(theta_deg),
                "n_samples": int(len(grouped_samples[theta_deg])),
                "als_iterations": int(iterations),
                "fit_rms_error": float(rms_error),
                "cond_j_rx": float(np.linalg.cond(j_rx)),
                "cond_j_tx": float(np.linalg.cond(j_tx)),
                "mean_s_hat_error_fro": float(np.mean(matrix_error_values)),
                "max_s_hat_error_fro": float(np.max(matrix_error_values)),
                "mean_branch_complex_abs_error": float(np.mean(branch_error_values)),
                "max_branch_complex_abs_error": float(np.max(branch_error_values)),
            }
        )

    matrix_df = pd.DataFrame(matrix_rows)
    sample_df = pd.DataFrame(sample_rows)
    summary_df = pd.DataFrame(summary_rows)
    if not matrix_df.empty:
        matrix_df = matrix_df.sort_values(["system_id", "theta_deg"]).reset_index(drop=True)
    if not sample_df.empty:
        sample_df = sample_df.sort_values(["system_id", "theta_deg", "material"]).reset_index(drop=True)
    if not summary_df.empty:
        summary_df = summary_df.sort_values(["system_id", "theta_deg"]).reset_index(drop=True)
    return matrix_df, sample_df, summary_df


def write_markdown(
    *,
    summary_df: pd.DataFrame,
    freq_ghz_lp: float,
    freq_ghz_cp: float,
    matrix_path: Path,
    sample_path: Path,
    summary_path: Path,
    output_path: Path,
    repo_root: Path,
) -> None:
    lines = [
        "# Prototype 2x2 Calibration",
        "",
        "Execution date: `2026-04-16`",
        "",
        "This is a single-frequency supervised prototype using existing ideal truth at `6.5 GHz`.",
        "It estimates per-theta `J_rx` and `J_tx` with alternating least squares and evaluates `S_hat = J_rx^{-1} H J_tx^{-1}`.",
        "This is not yet wired into the headline Stage 3/4 pipeline.",
        "",
        f"- LP frequency used: `{freq_ghz_lp:.3f} GHz`",
        f"- CP frequency used: `{freq_ghz_cp:.3f} GHz`",
        "",
        "## Theta Summary",
        "",
    ]
    for _, row in summary_df.iterrows():
        lines.append(
            f"- {row['system_id']} theta={row['theta_deg']:.1f} deg: "
            f"fit_rms={row['fit_rms_error']:.3e}, "
            f"mean S_hat error={row['mean_s_hat_error_fro']:.3e}, "
            f"max branch error={row['max_branch_complex_abs_error']:.3e}, "
            f"cond(J_rx/J_tx)={row['cond_j_rx']:.2e}/{row['cond_j_tx']:.2e}"
        )

    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Fitted matrices: `{matrix_path.relative_to(repo_root)}`",
            f"- Sample reconstruction table: `{sample_path.relative_to(repo_root)}`",
            f"- Theta summary: `{summary_path.relative_to(repo_root)}`",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_argparser().parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[3]

    linear_truth = pd.read_csv(args.linear_truth)
    cp_truth = pd.read_csv(args.cp_truth)
    grouped_lp, freq_ghz_lp = collect_samples_lp(linear_truth, args.lp_csv_dir.resolve())
    grouped_cp, freq_ghz_cp = collect_samples_cp(cp_truth, args.cp_csv_dir.resolve())

    lp_matrix_df, lp_sample_df, lp_summary_df = run_system("lp", grouped_lp)
    cp_matrix_df, cp_sample_df, cp_summary_df = run_system("cp", grouped_cp)

    matrix_df = pd.concat([lp_matrix_df, cp_matrix_df], ignore_index=True)
    sample_df = pd.concat([lp_sample_df, cp_sample_df], ignore_index=True)
    summary_df = pd.concat([lp_summary_df, cp_summary_df], ignore_index=True)

    matrix_path = output_dir / "prototype_2x2_calibration_matrices.csv"
    sample_path = output_dir / "prototype_2x2_calibration_sample_reconstruction.csv"
    summary_path = output_dir / "prototype_2x2_calibration_theta_summary.csv"
    md_path = output_dir / "PROTOTYPE_2X2_CALIBRATION.md"

    matrix_df.to_csv(matrix_path, index=False)
    sample_df.to_csv(sample_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    write_markdown(
        summary_df=summary_df,
        freq_ghz_lp=freq_ghz_lp,
        freq_ghz_cp=freq_ghz_cp,
        matrix_path=matrix_path,
        sample_path=sample_path,
        summary_path=summary_path,
        output_path=md_path,
        repo_root=repo_root,
    )
    print(f"Wrote 2x2 calibration prototype outputs to {output_dir}")


if __name__ == "__main__":
    main()
