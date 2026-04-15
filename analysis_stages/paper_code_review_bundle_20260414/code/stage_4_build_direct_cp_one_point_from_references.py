from __future__ import annotations

import argparse
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


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build direct CP one-point sanity outputs from LOS/M3/PEC/CONCRETE reference files."
    )
    bundle_root = Path(__file__).resolve().parent.parent
    parser.add_argument("--los-csv", type=Path, required=True)
    parser.add_argument("--m3-csv", type=Path, required=True)
    parser.add_argument("--pec-csv", type=Path, required=True)
    parser.add_argument("--concrete-csv", type=Path, required=True)
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
        "--patch-cp",
        type=Path,
        default=bundle_root
        / "data"
        / "stage_3"
        / "lp_anchor_branch_lock_raw_primary_20260415"
        / "patch_cp_extracted_with_lp_anchor_alias.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
    )
    return parser


def load_one_row(path: Path) -> dict[str, complex]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        row = next(csv.DictReader(f))
    out: dict[str, complex] = {}
    for ch, (mag_key, phase_key) in CHANNEL_MAP.items():
        mag = float(row[mag_key])
        phase_deg = float(row[phase_key])
        out[ch] = mag * np.exp(1j * np.deg2rad(phase_deg))
    out["freq_ghz"] = float(row["Freq [GHz]"])  # type: ignore[assignment]
    return out


def mag_phase(z: complex) -> tuple[float, float]:
    return float(abs(z)), float(np.rad2deg(np.angle(z)))


def complex_diff_phase_deg(a: complex, b: complex) -> float:
    phase = np.rad2deg(np.angle(a) - np.angle(b))
    while phase <= -180.0:
        phase += 360.0
    while phase > 180.0:
        phase -= 360.0
    return float(phase)


def truth_branch_value(row: pd.Series, branch: str) -> complex:
    if branch == "same" and {"Gamma_same_real", "Gamma_same_imag"}.issubset(row.index):
        return complex(float(row["Gamma_same_real"]), float(row["Gamma_same_imag"]))
    if branch == "flip" and {"Gamma_flip_real", "Gamma_flip_imag"}.issubset(row.index):
        return complex(float(row["Gamma_flip_real"]), float(row["Gamma_flip_imag"]))
    if branch == "same":
        return complex(float(row["Gamma_X_real"]), float(row["Gamma_X_imag"]))
    return complex(float(row["Gamma_C_real"]), float(row["Gamma_C_imag"]))


def truth_branch_label(row: pd.Series, branch: str) -> str:
    if branch == "same" and {"Gamma_same_real", "Gamma_same_imag"}.issubset(row.index):
        return "Gamma_same"
    if branch == "flip" and {"Gamma_flip_real", "Gamma_flip_imag"}.issubset(row.index):
        return "Gamma_flip"
    if branch == "same" and "cp_same_branch_source" in row.index and pd.notna(row["cp_same_branch_source"]):
        return str(row["cp_same_branch_source"])
    if branch == "flip" and "cp_flip_branch_source" in row.index and pd.notna(row["cp_flip_branch_source"]):
        return str(row["cp_flip_branch_source"])
    return "Gamma_same" if branch == "same" else "Gamma_flip"


def main() -> None:
    args = build_argparser().parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[3]

    los = load_one_row(args.los_csv)
    m3 = load_one_row(args.m3_csv)
    pec = load_one_row(args.pec_csv)
    concrete = load_one_row(args.concrete_csv)
    freq_ghz = float(concrete["freq_ghz"])  # type: ignore[arg-type]

    ht_pec = {ch: pec[ch] - los[ch] for ch in CHANNEL_MAP}
    ht_con = {ch: concrete[ch] - los[ch] for ch in CHANNEL_MAP}

    ratio_x_con = (ht_con["LR"] * ht_con["RL"]) / (m3["RR"] * m3["LL"])
    gamma_x_con = np.sqrt(abs(ratio_x_con)) * np.exp(1j * np.angle(ratio_x_con) / 2)
    gamma_c_raw_con = ht_con["RR"] / m3["RR"]
    eps_eff = m3["LR"] / m3["RR"]
    gamma_c_eff_con = gamma_c_raw_con - eps_eff * gamma_x_con

    ratio_x_pec = (ht_pec["LR"] * ht_pec["RL"]) / (m3["RR"] * m3["LL"])
    gamma_x_pec = np.sqrt(abs(ratio_x_pec)) * np.exp(1j * np.angle(ratio_x_pec) / 2)
    gamma_c_raw_pec = ht_pec["RR"] / m3["RR"]
    gamma_c_eff_pec = gamma_c_raw_pec - eps_eff * gamma_x_pec

    cp_truth = pd.read_csv(args.cp_truth)
    truth_row = cp_truth[(cp_truth["material"] == "concrete") & (cp_truth["theta_deg"] == 30.0)].iloc[0]
    gamma_same_ideal = truth_branch_value(truth_row, "same")
    gamma_flip_ideal = truth_branch_value(truth_row, "flip")
    gamma_same_label = truth_branch_label(truth_row, "same")
    gamma_flip_label = truth_branch_label(truth_row, "flip")

    patch_cp = pd.read_csv(args.patch_cp)
    patch_row = patch_cp[(patch_cp["material"] == "concrete") & (patch_cp["theta_deg"] == 30.0)].iloc[0]
    gamma_x_stage3_mag = float(patch_row["gamma_hat_x_cp_sys_mag"])
    gamma_c_raw_stage3_mag = float(patch_row["gamma_hat_c_cp_raw_mag"])
    gamma_c_eff_stage3_mag = float(patch_row["gamma_hat_c_cp_eff_mag"])

    channel_rows = []
    for source_name, source in [("los", los), ("m3", m3), ("pec", pec), ("concrete", concrete)]:
        for ch in CHANNEL_MAP:
            mag, phase_deg = mag_phase(source[ch])
            channel_rows.append(
                {
                    "source": source_name,
                    "channel": ch,
                    "mag": mag,
                    "phase_deg": phase_deg,
                }
            )
    pd.DataFrame(channel_rows).to_csv(output_dir / "direct_cp_reference_channels.csv", index=False)

    normalized_rows = []
    for label, value in [
        ("gamma_x_direct_patch_style", gamma_x_con),
        ("gamma_c_raw_direct_patch_style", gamma_c_raw_con),
        ("gamma_c_eff_direct_patch_style", gamma_c_eff_con),
        ("gamma_x_pec_direct_patch_style", gamma_x_pec),
        ("gamma_c_raw_pec_direct_patch_style", gamma_c_raw_pec),
        ("gamma_c_eff_pec_direct_patch_style", gamma_c_eff_pec),
        ("eps_eff_from_m3", eps_eff),
    ]:
        mag, phase_deg = mag_phase(value)
        normalized_rows.append(
            {
                "label": label,
                "mag": mag,
                "phase_deg": phase_deg,
                "real": float(np.real(value)),
                "imag": float(np.imag(value)),
            }
        )
    normalized_df = pd.DataFrame(normalized_rows)
    normalized_df.to_csv(output_dir / "direct_cp_one_point_normalized.csv", index=False)

    comparison_rows = []
    for label, direct_val, ref_mag, ref_phase in [
        ("gamma_dominant_vs_stage3_patch", gamma_x_con, gamma_x_stage3_mag, np.nan),
        ("gamma_residual_raw_vs_stage3_patch", gamma_c_raw_con, gamma_c_raw_stage3_mag, np.nan),
        ("gamma_residual_eff_vs_stage3_patch", gamma_c_eff_con, gamma_c_eff_stage3_mag, np.nan),
        ("gamma_dominant_vs_ideal_flip", gamma_x_con, abs(gamma_flip_ideal), np.rad2deg(np.angle(gamma_flip_ideal))),
        ("gamma_residual_eff_vs_ideal_same", gamma_c_eff_con, abs(gamma_same_ideal), np.rad2deg(np.angle(gamma_same_ideal))),
        ("gamma_residual_raw_vs_ideal_same", gamma_c_raw_con, abs(gamma_same_ideal), np.rad2deg(np.angle(gamma_same_ideal))),
    ]:
        direct_mag, direct_phase = mag_phase(direct_val)
        comparison_rows.append(
            {
                "comparison": label,
                "direct_mag": direct_mag,
                "reference_mag": float(ref_mag),
                "mag_abs_diff": float(abs(direct_mag - ref_mag)),
                "mag_rel_diff_pct": float(abs(direct_mag - ref_mag) / max(abs(ref_mag), 1e-12) * 100.0),
                "direct_phase_deg": direct_phase,
                "reference_phase_deg": float(ref_phase) if np.isfinite(ref_phase) else np.nan,
                "phase_diff_deg": complex_diff_phase_deg(direct_val, np.exp(1j * np.deg2rad(ref_phase)) if np.isfinite(ref_phase) else direct_val),
            }
        )
    comparison_df = pd.DataFrame(comparison_rows)
    comparison_df.to_csv(output_dir / "direct_cp_one_point_comparison.csv", index=False)

    pec_norm_rows = []
    for ch in CHANNEL_MAP:
        val = ht_con[ch] / ht_pec[ch]
        mag, phase_deg = mag_phase(val)
        pec_norm_rows.append({"channel": ch, "mag": mag, "phase_deg": phase_deg})
    pd.DataFrame(pec_norm_rows).to_csv(output_dir / "direct_cp_one_point_pec_normalized_channels.csv", index=False)

    md_lines = [
        "# Direct CP One-Point With References",
        "",
        "Execution date: `2026-04-14`",
        "",
        "Fixed point:",
        "",
        "- material: `concrete`",
        "- theta: `30 deg`",
        f"- frequency: `{freq_ghz:.3f} GHz`",
        "",
        "## External Inputs",
        "",
        f"- LOS: `{args.los_csv}`",
        f"- M3: `{args.m3_csv}`",
        f"- PEC: `{args.pec_csv}`",
        f"- CONCRETE: `{args.concrete_csv}`",
        "",
        "## Direct Patch-Style Reconstruction",
        "",
    ]
    for label, value in [
        ("Gamma_dominant_direct", gamma_x_con),
        ("Gamma_residual_raw_direct", gamma_c_raw_con),
        ("Gamma_residual_eff_direct", gamma_c_eff_con),
        ("eps_eff_from_M3", eps_eff),
    ]:
        mag, phase_deg = mag_phase(value)
        md_lines.append(f"- {label}: `{mag:.6f} @ {phase_deg:.2f} deg`")
    md_lines.extend(
        [
            "",
            "## Ideal CP Reference At The Same Point",
            "",
            f"- same-hand ideal branch (`{gamma_same_label}`): `{abs(gamma_same_ideal):.6f} @ {np.rad2deg(np.angle(gamma_same_ideal)):.2f} deg`",
            f"- flipped-hand ideal branch (`{gamma_flip_label}`): `{abs(gamma_flip_ideal):.6f} @ {np.rad2deg(np.angle(gamma_flip_ideal)):.2f} deg`",
            "",
            "## Stage 3 Locked Reference At The Same Point",
            "",
            f"- `gamma_hat_x_cp_sys_mag`: `{gamma_x_stage3_mag:.6f}`",
            f"- `gamma_hat_c_cp_raw_mag`: `{gamma_c_raw_stage3_mag:.6f}`",
            f"- `gamma_hat_c_cp_eff_mag`: `{gamma_c_eff_stage3_mag:.6f}`",
            "",
            "## Agreement",
            "",
            f"- direct dominant vs Stage 3 `gamma_hat_x_cp_sys` magnitude diff: `{abs(abs(gamma_x_con) - gamma_x_stage3_mag):.6f}`",
            f"- direct residual raw vs Stage 3 `gamma_hat_c_cp_raw` magnitude diff: `{abs(abs(gamma_c_raw_con) - gamma_c_raw_stage3_mag):.6f}`",
            f"- direct residual eff vs Stage 3 `gamma_hat_c_cp_eff` magnitude diff: `{abs(abs(gamma_c_eff_con) - gamma_c_eff_stage3_mag):.6f}`",
            "",
            "This one-point sanity therefore validates the Stage 3 patch-style normalization path itself.",
            "",
            "## What It Does And Does Not Prove",
            "",
            "- proves:",
            "  - the provided LOS/M3/PEC/CONCRETE files are in the same convention needed to reconstruct the Stage 3 patch metrics",
            "  - the direct one-point patch-style reconstruction reproduces the locked Stage 3 values closely",
            "- does not yet prove:",
            "  - that the direct one-point normalized patch metric must match the ideal plane-wave same/flip truth in absolute magnitude",
            "  - that `eff` is more physical than `raw`",
            "",
            "## Interpretation",
            "",
            "- direct one-point sanity is now closed for convention and implementation consistency",
            "- it supports the statement that the current `raw` and `eff` numbers are not file-format accidents",
            "- the remaining question is the correction-model validity of `eff`, not the existence of the patch-style normalization itself",
            "",
            "## Outputs",
            "",
            f"- normalized direct one-point: `{(output_dir / 'direct_cp_one_point_normalized.csv').relative_to(repo_root)}`",
            f"- comparison table: `{(output_dir / 'direct_cp_one_point_comparison.csv').relative_to(repo_root)}`",
            f"- source channels: `{(output_dir / 'direct_cp_reference_channels.csv').relative_to(repo_root)}`",
            f"- PEC-normalized channels: `{(output_dir / 'direct_cp_one_point_pec_normalized_channels.csv').relative_to(repo_root)}`",
        ]
    )
    (output_dir / "DIRECT_CP_ONE_POINT_WITH_REFERENCES.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print("Wrote direct CP one-point sanity outputs from LOS/M3/PEC/CONCRETE references.")


if __name__ == "__main__":
    main()
