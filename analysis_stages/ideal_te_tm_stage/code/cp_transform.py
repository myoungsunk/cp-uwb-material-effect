from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def _to_complex(df: pd.DataFrame, prefix: str) -> np.ndarray:
    return df[f"{prefix}_real"].to_numpy() + 1j * df[f"{prefix}_imag"].to_numpy()


def build_cp_truth_table(linear_truth: pd.DataFrame) -> pd.DataFrame:
    df = linear_truth.copy()
    r_te = _to_complex(df, "R_TE")
    r_tm = _to_complex(df, "R_TM")
    gamma_x = 0.5 * (r_te + r_tm)
    gamma_c = 0.5 * (r_te - r_tm)

    out = df[["case", "material", "f_hz", "theta_deg"]].copy()
    out["Gamma_X_real"] = np.real(gamma_x)
    out["Gamma_X_imag"] = np.imag(gamma_x)
    out["Gamma_X_mag"] = np.abs(gamma_x)
    out["Gamma_X_phase_deg"] = np.rad2deg(np.angle(gamma_x))
    out["Gamma_C_real"] = np.real(gamma_c)
    out["Gamma_C_imag"] = np.imag(gamma_c)
    out["Gamma_C_mag"] = np.abs(gamma_c)
    out["Gamma_C_phase_deg"] = np.rad2deg(np.angle(gamma_c))
    out["note"] = "Derived from linear-basis reflection truth table; CP convention should still be checked explicitly."
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build CP truth table from linear TE/TM truth table.")
    parser.add_argument("linear_truth_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    args = parser.parse_args()

    linear_truth = pd.read_csv(args.linear_truth_csv)
    cp_truth = build_cp_truth_table(linear_truth)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    cp_truth.to_csv(args.output_csv, index=False)
    print(f"Wrote CP truth table: {args.output_csv}")


if __name__ == "__main__":
    main()
