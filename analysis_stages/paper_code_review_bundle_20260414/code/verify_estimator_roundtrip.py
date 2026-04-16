from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


STAGE_TO_TRUTH_MATERIAL = {
    "metal": "pec",
    "concrete": "concrete1",
    "glass": "glass1",
    "wood": "wood1",
}
LP_CHANNELS = ["yy", "yz", "zy", "zz"]
CP_CHANNELS = ["LL", "LR", "RL", "RR"]
TARGET_FREQ_GHZ = 6.5
DEFAULT_SINGLE_REFERENCE_THETA_DEG = 20.0
IDENTITY_TOL = 1e-9


def build_argparser() -> argparse.ArgumentParser:
    bundle_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description=(
            "Synthetic stage-bridge verification for the Stage 3 LP/CP estimators. "
            "This is an algebraic bridge test, not a new EM replay."
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
        "--cp-m3-csv",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "stage3_patch_paper_final_20260414" / "cp" / "csv" / "m3_off-boresigjt.csv",
    )
    parser.add_argument(
        "--lp-m3-csv",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "stage3_patch_paper_final_20260414" / "lp" / "csv" / "LP_m3_off-boresigjt.csv",
    )
    parser.add_argument(
        "--single-reference-theta-deg",
        type=float,
        default=DEFAULT_SINGLE_REFERENCE_THETA_DEG,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=bundle_root / "results" / "debug",
    )
    return parser


def parse_complex(magnitude: np.ndarray, phase_deg: np.ndarray) -> np.ndarray:
    return magnitude * np.exp(1j * np.deg2rad(phase_deg))


def anchored_geometric_mean(ratio: complex, anchor_approx: complex) -> complex:
    candidate = np.sqrt(np.abs(ratio)) * np.exp(1j * np.angle(ratio) / 2.0)
    if np.abs(anchor_approx) > 1e-18 and abs(np.angle(candidate / anchor_approx)) > (np.pi / 2.0):
        candidate *= -1.0
    return complex(candidate)


def load_sweep_cp(path: Path) -> tuple[np.ndarray, dict[float, dict[str, np.ndarray]]]:
    df = pd.read_csv(path)
    cols = df.columns.tolist()
    thetas = np.array(sorted(df[cols[0]].unique()), dtype=float)
    freq = df[df[cols[0]] == thetas[0]][cols[1]].to_numpy(dtype=float)
    out: dict[float, dict[str, np.ndarray]] = {}
    for theta in thetas:
        sub = df[df[cols[0]] == theta]
        out[float(theta)] = {}
        for idx, ch in enumerate(CP_CHANNELS):
            out[float(theta)][ch] = parse_complex(
                sub[cols[2 + 2 * idx]].to_numpy(dtype=float),
                sub[cols[3 + 2 * idx]].to_numpy(dtype=float),
            )
    return freq, out


def load_sweep_lp(path: Path) -> tuple[np.ndarray, dict[float, dict[str, np.ndarray]]]:
    df = pd.read_csv(path)
    theta_col = df.columns[0]
    freq_col = df.columns[1]
    thetas = np.array(sorted(df[theta_col].unique()), dtype=float)
    freq = df[df[theta_col] == thetas[0]][freq_col].to_numpy(dtype=float)
    channel_cols = {
        "yy": ("mag(S(Rx_y_p1,Tx_y_p1)) []", "ang_deg(S(Rx_y_p1,Tx_y_p1)) [deg]"),
        "yz": ("mag(S(Rx_y_p1,Tx_z_p1)) []", "ang_deg(S(Rx_y_p1,Tx_z_p1)) [deg]"),
        "zy": ("mag(S(Rx_z_p1,Tx_y_p1)) []", "ang_deg(S(Rx_z_p1,Tx_y_p1)) [deg]"),
        "zz": ("mag(S(Rx_z_p1,Tx_z_p1)) []", "ang_deg(S(Rx_z_p1,Tx_z_p1)) [deg]"),
    }
    out: dict[float, dict[str, np.ndarray]] = {}
    for theta in thetas:
        sub = df[df[theta_col] == theta]
        out[float(theta)] = {}
        for ch, (mag_col, phase_col) in channel_cols.items():
            out[float(theta)][ch] = parse_complex(
                sub[mag_col].to_numpy(dtype=float),
                sub[phase_col].to_numpy(dtype=float),
            )
    return freq, out


def nearest_index(freq: np.ndarray, target_freq_ghz: float) -> int:
    return int(np.argmin(np.abs(freq - target_freq_ghz)))


def truth_rows(linear_truth: pd.DataFrame, cp_truth: pd.DataFrame) -> list[tuple[str, float, pd.Series, pd.Series]]:
    rows: list[tuple[str, float, pd.Series, pd.Series]] = []
    for stage_material, truth_material in STAGE_TO_TRUTH_MATERIAL.items():
        linear_sub = linear_truth[linear_truth["material"].str.lower() == truth_material].copy()
        cp_sub = cp_truth[cp_truth["material"].str.lower() == truth_material].copy()
        common_thetas = sorted(set(np.round(linear_sub["theta_deg"], 9)).intersection(set(np.round(cp_sub["theta_deg"], 9))))
        for theta in common_thetas:
            linear_row = linear_sub[np.isclose(linear_sub["theta_deg"], theta)].iloc[0]
            cp_row = cp_sub[np.isclose(cp_sub["theta_deg"], theta)].iloc[0]
            rows.append((stage_material, float(theta), linear_row, cp_row))
    return rows


def lp_extract(htilde: dict[str, complex], h3: dict[str, complex]) -> dict[str, complex]:
    r_tm = htilde["yy"] / h3["yy"]
    r_te = htilde["zz"] / h3["zz"]
    gamma_x = (r_te + r_tm) / 2.0
    gamma_c = (r_te - r_tm) / 2.0
    return {
        "R_TM": complex(r_tm),
        "R_TE": complex(r_te),
        "Gamma_X": complex(gamma_x),
        "Gamma_C": complex(gamma_c),
    }


def cp_extract(htilde: dict[str, complex], h3: dict[str, complex]) -> dict[str, complex]:
    ratio = (htilde["LR"] * htilde["RL"]) / (h3["RR"] * h3["LL"])
    gamma_x = anchored_geometric_mean(ratio, htilde["LR"] / h3["RR"])
    gamma_c_raw = htilde["RR"] / h3["RR"]
    eps_eff = h3["LR"] / h3["RR"]
    gamma_c_eff = gamma_c_raw - eps_eff * gamma_x
    return {
        "Gamma_X": complex(gamma_x),
        "Gamma_C_raw": complex(gamma_c_raw),
        "Gamma_C_eff": complex(gamma_c_eff),
        "eps_eff": complex(eps_eff),
    }


def lp_identity_htilde(h3: dict[str, complex], linear_row: pd.Series) -> dict[str, complex]:
    r_tm = complex(linear_row["R_TM_locked_real"], linear_row["R_TM_locked_imag"])
    r_te = complex(linear_row["R_TE_locked_real"], linear_row["R_TE_locked_imag"])
    return {
        "yy": h3["yy"] * r_tm,
        "yz": 0.0 + 0.0j,
        "zy": 0.0 + 0.0j,
        "zz": h3["zz"] * r_te,
    }


def cp_raw_identity_htilde(h3: dict[str, complex], cp_row: pd.Series) -> dict[str, complex]:
    gamma_x = complex(cp_row["Gamma_same_real"], cp_row["Gamma_same_imag"])
    gamma_c = complex(cp_row["Gamma_flip_real"], cp_row["Gamma_flip_imag"])
    return {
        "LL": h3["LL"] * gamma_c,
        "LR": h3["RR"] * gamma_x,
        "RL": h3["LL"] * gamma_x,
        "RR": h3["RR"] * gamma_c,
    }


def cp_minimal_model_htilde(h3: dict[str, complex], cp_row: pd.Series) -> dict[str, complex]:
    gamma_x = complex(cp_row["Gamma_same_real"], cp_row["Gamma_same_imag"])
    gamma_c = complex(cp_row["Gamma_flip_real"], cp_row["Gamma_flip_imag"])
    return {
        "LL": h3["LL"] * gamma_c + h3["RL"] * gamma_x,
        "LR": h3["RR"] * gamma_x,
        "RL": h3["LL"] * gamma_x,
        "RR": h3["RR"] * gamma_c + h3["LR"] * gamma_x,
    }


def add_result_rows(
    rows: list[dict[str, object]],
    *,
    system_id: str,
    model_mode: str,
    reference_mode: str,
    reference_theta_deg: float,
    material: str,
    theta_deg: float,
    truth_values: dict[str, complex],
    extracted_values: dict[str, complex],
) -> None:
    for quantity, truth_value in truth_values.items():
        extracted_value = complex(extracted_values[quantity])
        complex_error = extracted_value - truth_value
        rows.append(
            {
                "system_id": system_id,
                "model_mode": model_mode,
                "reference_mode": reference_mode,
                "reference_theta_deg": float(reference_theta_deg),
                "material": material,
                "theta_deg": float(theta_deg),
                "quantity": quantity,
                "truth_real": float(np.real(truth_value)),
                "truth_imag": float(np.imag(truth_value)),
                "truth_mag": float(np.abs(truth_value)),
                "extracted_real": float(np.real(extracted_value)),
                "extracted_imag": float(np.imag(extracted_value)),
                "extracted_mag": float(np.abs(extracted_value)),
                "complex_abs_error": float(np.abs(complex_error)),
                "mag_abs_error": float(abs(np.abs(extracted_value) - np.abs(truth_value))),
                "pass_identity_tol": bool(np.abs(complex_error) <= IDENTITY_TOL),
            }
        )


def summarize(result_df: pd.DataFrame) -> pd.DataFrame:
    summary_rows: list[dict[str, object]] = []
    for (system_id, model_mode, reference_mode, quantity), sub in result_df.groupby(
        ["system_id", "model_mode", "reference_mode", "quantity"], sort=True
    ):
        summary_rows.append(
            {
                "system_id": system_id,
                "model_mode": model_mode,
                "reference_mode": reference_mode,
                "quantity": quantity,
                "n_rows": int(len(sub)),
                "identity_pass_rows": int(sub["pass_identity_tol"].sum()),
                "mean_complex_abs_error": float(sub["complex_abs_error"].mean()),
                "max_complex_abs_error": float(sub["complex_abs_error"].max()),
                "mean_mag_abs_error": float(sub["mag_abs_error"].mean()),
                "max_mag_abs_error": float(sub["mag_abs_error"].max()),
            }
        )
    return pd.DataFrame(summary_rows).sort_values(
        ["system_id", "model_mode", "reference_mode", "quantity"]
    ).reset_index(drop=True)


def write_markdown(
    *,
    summary_df: pd.DataFrame,
    output_path: Path,
    result_path: Path,
    summary_path: Path,
    repo_root: Path,
    single_reference_theta_deg: float,
) -> None:
    angle_resolved = summary_df[summary_df["reference_mode"] == "angle_resolved"].copy()
    fixed_ref = summary_df[summary_df["reference_mode"] == "single_reference"].copy()

    lines = [
        "# Verify Estimator Roundtrip",
        "",
        "Execution date: `2026-04-16`",
        "",
        "This is a synthetic algebraic bridge test using the current single-frequency ideal truth at `6.5 GHz`.",
        "It is not a new EM replay and does not relax the current truth-frequency limitation.",
        "",
        "## Modes",
        "",
        "- `lp_identity`: LP extractor with diagonal ideal `R_TM / R_TE` injected into the Stage 3 LP form.",
        "- `cp_raw_identity`: CP raw path identity test with `h_tilde_RR / h3_RR = Gamma_flip`.",
        "- `cp_eff_minimal`: CP minimal model with `h_tilde_RR = h3_RR * Gamma_flip + h3_LR * Gamma_same` so the corrected path should recover the ideal co-term.",
        "",
        f"- `single_reference`: uses one fixed reference stack at `theta={single_reference_theta_deg:.1f} deg` to expose reference-reuse drift.",
        "",
        "## Angle-Resolved Identity",
        "",
    ]

    for _, row in angle_resolved.iterrows():
        lines.append(
            f"- {row['system_id']} / {row['model_mode']} / {row['quantity']}: "
            f"{int(row['identity_pass_rows'])}/{int(row['n_rows'])} pass, "
            f"max complex error={row['max_complex_abs_error']:.3e}"
        )

    lines.extend(
        [
            "",
            "## Fixed-Reference Replay",
            "",
        ]
    )
    for _, row in fixed_ref.iterrows():
        lines.append(
            f"- {row['system_id']} / {row['model_mode']} / {row['quantity']}: "
            f"max complex error={row['max_complex_abs_error']:.3e}, "
            f"mean complex error={row['mean_complex_abs_error']:.3e}"
        )

    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Full rows: `{result_path.relative_to(repo_root)}`",
            f"- Summary: `{summary_path.relative_to(repo_root)}`",
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
    cp_freq, cp_m3 = load_sweep_cp(args.cp_m3_csv)
    lp_freq, lp_m3 = load_sweep_lp(args.lp_m3_csv)
    cp_idx = nearest_index(cp_freq, TARGET_FREQ_GHZ)
    lp_idx = nearest_index(lp_freq, TARGET_FREQ_GHZ)

    cp_thetas = sorted(cp_m3.keys())
    lp_thetas = sorted(lp_m3.keys())
    if args.single_reference_theta_deg not in cp_thetas or args.single_reference_theta_deg not in lp_thetas:
        raise ValueError(f"Requested single reference theta {args.single_reference_theta_deg} not found in both CP and LP M3 sweeps.")

    result_rows: list[dict[str, object]] = []

    for material, theta_deg, linear_row, cp_row in truth_rows(linear_truth, cp_truth):
        if theta_deg not in cp_m3 or theta_deg not in lp_m3:
            continue

        lp_h3_generate = {ch: complex(lp_m3[theta_deg][ch][lp_idx]) for ch in LP_CHANNELS}
        cp_h3_generate = {ch: complex(cp_m3[theta_deg][ch][cp_idx]) for ch in CP_CHANNELS}
        lp_h3_single_ref = {ch: complex(lp_m3[args.single_reference_theta_deg][ch][lp_idx]) for ch in LP_CHANNELS}
        cp_h3_single_ref = {ch: complex(cp_m3[args.single_reference_theta_deg][ch][cp_idx]) for ch in CP_CHANNELS}

        lp_htilde = lp_identity_htilde(lp_h3_generate, linear_row)
        cp_htilde_raw_identity = cp_raw_identity_htilde(cp_h3_generate, cp_row)
        cp_htilde_minimal = cp_minimal_model_htilde(cp_h3_generate, cp_row)

        for reference_mode, lp_h3_extract, cp_h3_extract, reference_theta in [
            ("angle_resolved", lp_h3_generate, cp_h3_generate, theta_deg),
            ("single_reference", lp_h3_single_ref, cp_h3_single_ref, float(args.single_reference_theta_deg)),
        ]:
            add_result_rows(
                result_rows,
                system_id="lp",
                model_mode="lp_identity",
                reference_mode=reference_mode,
                reference_theta_deg=reference_theta,
                material=material,
                theta_deg=theta_deg,
                truth_values={
                    "R_TM": complex(linear_row["R_TM_locked_real"], linear_row["R_TM_locked_imag"]),
                    "R_TE": complex(linear_row["R_TE_locked_real"], linear_row["R_TE_locked_imag"]),
                    "Gamma_X": complex(cp_row["Gamma_same_real"], cp_row["Gamma_same_imag"]),
                    "Gamma_C": complex(cp_row["Gamma_flip_real"], cp_row["Gamma_flip_imag"]),
                },
                extracted_values=lp_extract(lp_htilde, lp_h3_extract),
            )
            add_result_rows(
                result_rows,
                system_id="cp",
                model_mode="cp_raw_identity",
                reference_mode=reference_mode,
                reference_theta_deg=reference_theta,
                material=material,
                theta_deg=theta_deg,
                truth_values={
                    "Gamma_X": complex(cp_row["Gamma_same_real"], cp_row["Gamma_same_imag"]),
                    "Gamma_C_raw": complex(cp_row["Gamma_flip_real"], cp_row["Gamma_flip_imag"]),
                },
                extracted_values=cp_extract(cp_htilde_raw_identity, cp_h3_extract),
            )
            add_result_rows(
                result_rows,
                system_id="cp",
                model_mode="cp_eff_minimal",
                reference_mode=reference_mode,
                reference_theta_deg=reference_theta,
                material=material,
                theta_deg=theta_deg,
                truth_values={
                    "Gamma_X": complex(cp_row["Gamma_same_real"], cp_row["Gamma_same_imag"]),
                    "Gamma_C_eff": complex(cp_row["Gamma_flip_real"], cp_row["Gamma_flip_imag"]),
                },
                extracted_values=cp_extract(cp_htilde_minimal, cp_h3_extract),
            )

    result_df = pd.DataFrame(result_rows).sort_values(
        ["system_id", "model_mode", "reference_mode", "material", "theta_deg", "quantity"]
    ).reset_index(drop=True)
    summary_df = summarize(result_df)

    result_path = output_dir / "verify_estimator_roundtrip_full.csv"
    summary_path = output_dir / "verify_estimator_roundtrip_summary.csv"
    md_path = output_dir / "VERIFY_ESTIMATOR_ROUNDTRIP.md"
    result_df.to_csv(result_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    write_markdown(
        summary_df=summary_df,
        output_path=md_path,
        result_path=result_path,
        summary_path=summary_path,
        repo_root=repo_root,
        single_reference_theta_deg=float(args.single_reference_theta_deg),
    )
    print(f"Wrote synthetic stage-bridge verification outputs to {output_dir}")


if __name__ == "__main__":
    main()
