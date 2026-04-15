# Consolidated review copy for paper-pipeline code assessment.
# Stage: 4
# Role: Metal-floor audit for CP residual normalization using PEC/metal reference rows.
# Source: analysis_stages/stage4d_cp_metal_floor_audit_20260414/code/build_cp_metal_floor_audit.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


VALID_MAX = {"concrete": 55.0, "glass": 60.0, "wood": 45.0}
MATERIALS = ["metal", "concrete", "glass", "wood"]
NON_METAL = ["concrete", "glass", "wood"]
CHANNELS = ["LL", "LR", "RL", "RR"]


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a metal-floor CP export and same-angle audit on the locked paper grid."
    )
    bundle_root = Path(__file__).resolve().parent.parent
    workspace_root = Path(__file__).resolve().parents[3]
    parser.add_argument(
        "--cp-csv-root",
        type=Path,
        default=workspace_root / "analysis_stages" / "stage3_patch_paper_final_20260414" / "cp" / "csv",
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
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
    )
    return parser


def parse_complex(mag: pd.Series, phase_deg: pd.Series) -> np.ndarray:
    return mag.to_numpy(dtype=float) * np.exp(1j * np.deg2rad(phase_deg.to_numpy(dtype=float)))


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


def load_m1(path: Path) -> dict[str, np.ndarray]:
    df = pd.read_csv(path)
    cols = df.columns.tolist()
    out = {"freq_ghz": df[cols[0]].to_numpy(dtype=float)}
    for i, ch in enumerate(CHANNELS):
        out[ch] = parse_complex(df[cols[1 + 2 * i]], df[cols[2 + 2 * i]])
    return out


def load_sweep(path: Path) -> dict[float, dict[str, np.ndarray]]:
    df = pd.read_csv(path)
    cols = df.columns.tolist()
    thetas = sorted(df[cols[0]].unique())
    out: dict[float, dict[str, np.ndarray]] = {}
    for theta in thetas:
        sub = df[df[cols[0]] == theta]
        d: dict[str, np.ndarray] = {}
        for i, ch in enumerate(CHANNELS):
            d[ch] = parse_complex(sub[cols[2 + 2 * i]], sub[cols[3 + 2 * i]])
        out[float(theta)] = d
    return out


def ideal_residual_mag_col(df: pd.DataFrame) -> str:
    return "Gamma_same_mag" if "Gamma_same_mag" in df.columns else "Gamma_X_mag"


def main() -> None:
    args = build_argparser().parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[3]

    cp_csv_root = args.cp_csv_root.resolve()
    m1 = load_m1(cp_csv_root / "m1_los_5000.csv")
    m2 = {m: load_sweep(cp_csv_root / f"m2_{m}_R_5000.csv") for m in MATERIALS}
    freq = m1["freq_ghz"]
    freq_start = float(freq[0])
    freq_stop = float(freq[-1])
    freq_center = float(freq.mean())
    n_freq = int(len(freq))

    rows = []
    for material in MATERIALS:
        for theta_deg, mat_row in sorted(m2[material].items()):
            ht_mat = {ch: mat_row[ch] - m1[ch] for ch in CHANNELS}
            ht_met = {ch: m2["metal"][theta_deg][ch] - m1[ch] for ch in CHANNELS}

            gx_lr = ht_mat["LR"] / ht_met["LR"]
            gx_rl = ht_mat["RL"] / ht_met["RL"]
            ratio_x = gx_lr * gx_rl
            gamma_x = anchored_geometric_mean(ratio_x, gx_lr)
            gamma_c = ht_mat["RR"] / ht_met["RR"]

            rows.append(
                {
                    "material": material,
                    "theta_deg": float(theta_deg),
                    "freq_start_ghz": freq_start,
                    "freq_stop_ghz": freq_stop,
                    "freq_center_ghz": freq_center,
                    "n_freq": n_freq,
                    "gamma_hat_x_metal_floor_real": float(np.mean(np.real(gamma_x))),
                    "gamma_hat_x_metal_floor_imag": float(np.mean(np.imag(gamma_x))),
                    "gamma_hat_x_metal_floor_mag": float(np.mean(np.abs(gamma_x))),
                    "gamma_hat_c_metal_floor_real": float(np.mean(np.real(gamma_c))),
                    "gamma_hat_c_metal_floor_imag": float(np.mean(np.imag(gamma_c))),
                    "gamma_hat_c_metal_floor_mag": float(np.mean(np.abs(gamma_c))),
                    "note": "Metal-floor CP ratio against metal plate using LoS-subtracted M2 responses.",
                }
            )

    metal_floor_df = pd.DataFrame(rows).sort_values(["material", "theta_deg"]).reset_index(drop=True)
    export_path = output_dir / "patch_cp_metal_floor_extracted.csv"
    metal_floor_df.to_csv(export_path, index=False)

    linear = pd.read_csv(args.linear_truth)
    cp_truth = pd.read_csv(args.cp_truth)

    linear = linear[linear["material"].isin(NON_METAL)].copy()
    cp_truth = cp_truth[cp_truth["material"].isin(NON_METAL)].copy()
    metal_non = metal_floor_df[metal_floor_df["material"].isin(NON_METAL)].copy()

    linear_keep = linear[
        ["material", "theta_deg", "R_TE_mag", "R_TM_mag", "use_for_main_claim_TE", "use_for_main_claim_TM"]
    ].copy()
    linear_keep["B_mag"] = linear_keep[["R_TE_mag", "R_TM_mag"]].max(axis=1)
    residual_col = ideal_residual_mag_col(cp_truth)
    cp_keep = cp_truth[["material", "theta_deg", residual_col, "cp_use_for_main_claim"]].copy()
    cp_keep = cp_keep.rename(columns={residual_col: "ideal_residual_mag"})

    audit = (
        metal_non.merge(linear_keep, on=["material", "theta_deg"], how="inner")
        .merge(cp_keep, on=["material", "theta_deg"], how="inner")
        .sort_values(["material", "theta_deg"])
        .reset_index(drop=True)
    )

    def parse_bool(v: object) -> bool:
        if isinstance(v, bool):
            return v
        if pd.isna(v):
            return False
        return str(v).strip().lower() in {"true", "1", "yes", "y", "t"}

    audit["use_for_main_claim_TE"] = audit["use_for_main_claim_TE"].map(parse_bool)
    audit["use_for_main_claim_TM"] = audit["use_for_main_claim_TM"].map(parse_bool)
    audit["cp_use_for_main_claim"] = audit["cp_use_for_main_claim"].map(parse_bool)
    audit["use_for_main_claim"] = (
        audit["use_for_main_claim_TE"]
        & audit["use_for_main_claim_TM"]
        & audit["cp_use_for_main_claim"]
        & (audit["theta_deg"] >= 20.0)
        & audit.apply(lambda row: row["theta_deg"] <= VALID_MAX[row["material"]], axis=1)
    )
    audit = audit[audit["use_for_main_claim"]].copy().reset_index(drop=True)

    audit["G_supp_ideal_db"] = 20.0 * np.log10(audit["B_mag"].clip(lower=1e-12) / audit["ideal_residual_mag"].clip(lower=1e-12))
    audit["G_patch_metal_floor_db"] = 20.0 * np.log10(
        audit["B_mag"].clip(lower=1e-12) / audit["gamma_hat_c_metal_floor_mag"].clip(lower=1e-12)
    )
    audit["Delta_G_ideal_minus_metal_floor_db"] = audit["G_supp_ideal_db"] - audit["G_patch_metal_floor_db"]
    audit["metal_floor_gt_ideal_residual"] = audit["gamma_hat_c_metal_floor_mag"] > audit["ideal_residual_mag"]
    audit["negative_delta_rows"] = audit["Delta_G_ideal_minus_metal_floor_db"] < 0.0

    audit_path = output_dir / "metal_floor_same_angle_audit.csv"
    audit.to_csv(audit_path, index=False)

    summary_rows = []
    for material in NON_METAL + ["overall"]:
        sub = audit if material == "overall" else audit[audit["material"] == material]
        summary_rows.append(
            {
                "material": material,
                "n_rows": int(len(sub)),
                "negative_delta_rows": int(sub["negative_delta_rows"].sum()),
                "negative_delta_frac": float(sub["negative_delta_rows"].mean()),
                "metal_floor_gt_ideal_rows": int(sub["metal_floor_gt_ideal_residual"].sum()),
                "mean_G_patch_metal_floor_db": float(sub["G_patch_metal_floor_db"].mean()),
                "mean_Delta_G_ideal_minus_metal_floor_db": float(sub["Delta_G_ideal_minus_metal_floor_db"].mean()),
                "min_Delta_G_ideal_minus_metal_floor_db": float(sub["Delta_G_ideal_minus_metal_floor_db"].min()),
                "max_Delta_G_ideal_minus_metal_floor_db": float(sub["Delta_G_ideal_minus_metal_floor_db"].max()),
            }
        )
    summary_df = pd.DataFrame(summary_rows)
    summary_path = output_dir / "metal_floor_same_angle_audit_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    overall = summary_df[summary_df["material"] == "overall"].iloc[0]
    md_lines = [
        "# Stage 4d CP Metal-Floor Audit",
        "",
        "Execution date: `2026-04-14`",
        "",
        "This stage was executed in the isolated workspace:",
        "",
        "- `analysis_stages/stage4d_cp_metal_floor_audit_20260414`",
        "",
        "## Core Finding",
        "",
        "Using the legacy metal-floor CP ratio removes the same-angle sign problem,",
        "but the resulting quantity is not a direct substitute for the Stage 4b",
        "patch residual magnitude.",
        "",
        f"- negative same-angle rows: `{int(overall['negative_delta_rows'])}/{int(overall['n_rows'])}`",
        f"- rows with metal-floor residual > ideal residual: `{int(overall['metal_floor_gt_ideal_rows'])}/{int(overall['n_rows'])}`",
        "",
        "## Summary By Material",
        "",
    ]
    for _, row in summary_df[summary_df["material"] != "overall"].iterrows():
        md_lines.append(
            f"- {row['material']}: n={int(row['n_rows'])}, "
            f"negative delta={int(row['negative_delta_rows'])}/{int(row['n_rows'])}, "
            f"mean G_patch_metal_floor={row['mean_G_patch_metal_floor_db']:.2f} dB, "
            f"mean Delta(ideal-metal_floor)={row['mean_Delta_G_ideal_minus_metal_floor_db']:.2f} dB"
        )

    md_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The metal-floor branch stays larger than the ideal residual branch at matched angle.",
            "- That removes the `Delta_G < 0` contradiction seen with `gamma_hat_c_cp_eff`.",
            "- But the metal-floor quantity is normalized to the metal response, not to an absolute interface reflection coefficient.",
            "- So it should be treated as a cross-check reference, not as a drop-in replacement for the paper headline suppression metric.",
            "",
            "## Outputs",
            "",
            f"- CP metal-floor export: `{export_path.relative_to(repo_root)}`",
            f"- Same-angle audit: `{audit_path.relative_to(repo_root)}`",
            f"- Summary table: `{summary_path.relative_to(repo_root)}`",
        ]
    )
    (output_dir / "STAGE4D_CP_METAL_FLOOR_AUDIT.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print("Wrote CP metal-floor export and same-angle audit.")


if __name__ == "__main__":
    main()
