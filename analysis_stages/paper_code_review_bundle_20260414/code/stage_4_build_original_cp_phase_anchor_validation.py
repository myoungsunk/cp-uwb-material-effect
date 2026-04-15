# Consolidated review copy for paper-pipeline code assessment.
# Stage: 4
# Role: Validate phase-anchor impact on the original non-specular CP patch-stage dataset.
# Source: analysis_stages/original_cp_phase_anchor_validation_20260414/code/build_original_cp_phase_anchor_validation.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


CHANNELS = ["LL", "LR", "RL", "RR"]
MATERIALS = ["concrete", "glass", "wood"]
VALID_MAX_THETA = {"concrete": 55.0, "glass": 60.0, "wood": 45.0}
MATERIAL_LABELS = {"concrete": "Concrete", "glass": "Glass", "wood": "Wood"}
MATERIAL_COLORS = {"concrete": "#b91c1c", "glass": "#1d4ed8", "wood": "#047857"}


def ideal_residual_mag_col(df: pd.DataFrame) -> str:
    return "Gamma_same_mag" if "Gamma_same_mag" in df.columns else "Gamma_X_mag"


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate phase-anchor impact on the original non-specular CP patch-stage data."
        )
    )
    bundle_root = Path(__file__).resolve().parent.parent
    workspace_root = Path(__file__).resolve().parents[3]
    parser.add_argument(
        "--csv-dir",
        type=Path,
        default=workspace_root / "analysis_stages" / "patch_cp_stage_system" / "csv",
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
        "--stage3-cp",
        type=Path,
        default=workspace_root
        / "analysis_stages"
        / "stage3_patch_paper_final_20260414"
        / "cp"
        / "results"
        / "patch_cp_extracted.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
    )
    return parser


def parse_complex(magnitude: np.ndarray, phase_deg: np.ndarray) -> np.ndarray:
    return magnitude * np.exp(1j * np.deg2rad(phase_deg))


def load_m1(path: Path) -> dict[str, np.ndarray]:
    df = pd.read_csv(path)
    cols = df.columns.tolist()
    out = {"freq": df[cols[0]].to_numpy(dtype=float)}
    for idx, channel in enumerate(CHANNELS):
        out[channel] = parse_complex(
            df[cols[1 + 2 * idx]].to_numpy(dtype=float),
            df[cols[2 + 2 * idx]].to_numpy(dtype=float),
        )
    return out


def load_sweep(path: Path) -> dict:
    df = pd.read_csv(path)
    cols = df.columns.tolist()
    thetas = np.array(sorted(df[cols[0]].unique()), dtype=float)
    freq = df[df[cols[0]] == thetas[0]][cols[1]].to_numpy(dtype=float)
    out = {"freq": freq, "thetas": thetas}
    for theta in thetas:
        sub = df[df[cols[0]] == theta]
        out[theta] = {}
        for idx, channel in enumerate(CHANNELS):
            out[theta][channel] = parse_complex(
                sub[cols[2 + 2 * idx]].to_numpy(dtype=float),
                sub[cols[3 + 2 * idx]].to_numpy(dtype=float),
            )
    return out


def principal_geometric_mean(ratio: np.ndarray) -> np.ndarray:
    return np.sqrt(np.abs(ratio)) * np.exp(1j * np.angle(ratio) / 2.0)


def anchored_geometric_mean(
    ratio: np.ndarray, anchor_approx: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    principal = principal_geometric_mean(ratio)
    anchored = np.array(principal, copy=True)
    phase_delta = np.zeros_like(np.real(principal), dtype=float)
    valid = np.abs(anchor_approx) > 1e-18
    phase_delta[valid] = np.angle(principal[valid] / anchor_approx[valid])
    flip_mask = valid & (np.abs(phase_delta) > (np.pi / 2.0))
    anchored[flip_mask] *= -1.0
    return anchored, flip_mask, phase_delta


def db20(value: float) -> float:
    return float(20.0 * np.log10(max(value, 1e-12)))


def build_tables(
    m1: dict[str, np.ndarray],
    m3: dict,
    m2: dict[str, dict],
    linear_truth: pd.DataFrame,
    cp_truth: pd.DataFrame,
    stage3_cp: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    freq_rows: list[dict[str, object]] = []
    theta_rows: list[dict[str, object]] = []
    material_rows: list[dict[str, object]] = []

    thetas = m3["thetas"]

    for material in MATERIALS:
        for theta in thetas:
            truth_linear_match = linear_truth[
                (linear_truth["material"] == material)
                & np.isclose(linear_truth["theta_deg"], theta)
            ]
            truth_cp_match = cp_truth[
                (cp_truth["material"] == material)
                & np.isclose(cp_truth["theta_deg"], theta)
            ]
            stage3_match = stage3_cp[
                (stage3_cp["material"] == material)
                & np.isclose(stage3_cp["theta_deg"], theta)
            ]
            if truth_linear_match.empty or truth_cp_match.empty or stage3_match.empty:
                continue

            ht = {ch: m2[material][theta][ch] - m1[ch] for ch in CHANNELS}
            h3 = m3[theta]
            ratio = (ht["LR"] * ht["RL"]) / (h3["RR"] * h3["LL"])
            anchor_approx = ht["LR"] / h3["RR"]

            gamma_x_principal = principal_geometric_mean(ratio)
            gamma_x_anchor, flip_mask, phase_delta = anchored_geometric_mean(ratio, anchor_approx)
            gamma_c_raw = ht["RR"] / h3["RR"]
            eps_eff = h3["LR"] / h3["RR"]
            gamma_c_cal_principal = gamma_c_raw - eps_eff * gamma_x_principal
            gamma_c_cal_anchor = gamma_c_raw - eps_eff * gamma_x_anchor

            truth_linear_row = truth_linear_match.iloc[0]
            truth_cp_row = truth_cp_match.iloc[0]
            stage3_row = stage3_match.iloc[0]

            B_mag = max(float(truth_linear_row["R_TE_mag"]), float(truth_linear_row["R_TM_mag"]))
            gamma_x_ideal_mag = float(truth_cp_row[ideal_residual_mag_col(cp_truth)])

            for idx, freq_ghz in enumerate(m1["freq"]):
                freq_rows.append(
                    {
                        "material": material,
                        "theta_deg": float(theta),
                        "freq_ghz": float(freq_ghz),
                        "flip_applied": bool(flip_mask[idx]),
                        "phase_delta_deg": float(np.rad2deg(phase_delta[idx])),
                        "gamma_x_principal_phase_deg": float(
                            np.rad2deg(np.angle(gamma_x_principal[idx]))
                        ),
                        "gamma_x_anchor_phase_deg": float(
                            np.rad2deg(np.angle(gamma_x_anchor[idx]))
                        ),
                        "gamma_c_raw_mag": float(np.abs(gamma_c_raw[idx])),
                        "gamma_c_cal_principal_mag": float(
                            np.abs(gamma_c_cal_principal[idx])
                        ),
                        "gamma_c_cal_anchor_mag": float(np.abs(gamma_c_cal_anchor[idx])),
                    }
                )

            gamma_x_principal_mag = float(np.mean(np.abs(gamma_x_principal)))
            gamma_x_anchor_mag = float(np.mean(np.abs(gamma_x_anchor)))
            gamma_c_raw_mag = float(np.mean(np.abs(gamma_c_raw)))
            gamma_c_cal_principal_mag = float(np.mean(np.abs(gamma_c_cal_principal)))
            gamma_c_cal_anchor_mag = float(np.mean(np.abs(gamma_c_cal_anchor)))

            theta_rows.append(
                {
                    "material": material,
                    "theta_deg": float(theta),
                    "n_freq": int(len(m1["freq"])),
                    "flip_count": int(flip_mask.sum()),
                    "flip_fraction": float(flip_mask.mean()),
                    "any_flip": bool(flip_mask.any()),
                    "in_valid_range": bool(theta <= VALID_MAX_THETA[material]),
                    "in_headline_oblique_range": bool(
                        (theta >= 20.0) and (theta <= VALID_MAX_THETA[material])
                    ),
                    "B_mag": B_mag,
                    "gamma_x_ideal_mag": gamma_x_ideal_mag,
                    "gamma_x_principal_mag": gamma_x_principal_mag,
                    "gamma_x_anchor_mag": gamma_x_anchor_mag,
                    "gamma_c_raw_mag": gamma_c_raw_mag,
                    "gamma_c_cal_principal_mag": gamma_c_cal_principal_mag,
                    "gamma_c_cal_anchor_mag": gamma_c_cal_anchor_mag,
                    "stage3_gamma_x_anchor_mag": float(stage3_row["gamma_hat_x_cp_sys_mag"]),
                    "stage3_gamma_c_raw_mag": float(stage3_row["gamma_hat_c_cp_raw_mag"]),
                    "stage3_gamma_c_eff_mag": float(stage3_row["gamma_hat_c_cp_eff_mag"]),
                    "stage3_gamma_x_abs_diff": abs(
                        gamma_x_anchor_mag - float(stage3_row["gamma_hat_x_cp_sys_mag"])
                    ),
                    "stage3_gamma_c_raw_abs_diff": abs(
                        gamma_c_raw_mag - float(stage3_row["gamma_hat_c_cp_raw_mag"])
                    ),
                    "stage3_gamma_c_eff_abs_diff": abs(
                        gamma_c_cal_anchor_mag - float(stage3_row["gamma_hat_c_cp_eff_mag"])
                    ),
                    "G_ideal_db": db20(B_mag / gamma_x_ideal_mag),
                    "G_cp_raw_db": db20(B_mag / gamma_c_raw_mag),
                    "G_cp_cal_principal_db": db20(B_mag / gamma_c_cal_principal_mag),
                    "G_cp_cal_anchor_db": db20(B_mag / gamma_c_cal_anchor_mag),
                    "Delta_ideal_minus_raw_db": db20(B_mag / gamma_x_ideal_mag)
                    - db20(B_mag / gamma_c_raw_mag),
                    "Delta_ideal_minus_cal_principal_db": db20(B_mag / gamma_x_ideal_mag)
                    - db20(B_mag / gamma_c_cal_principal_mag),
                    "Delta_ideal_minus_cal_anchor_db": db20(B_mag / gamma_x_ideal_mag)
                    - db20(B_mag / gamma_c_cal_anchor_mag),
                    "cal_anchor_minus_principal_db": db20(B_mag / gamma_c_cal_anchor_mag)
                    - db20(B_mag / gamma_c_cal_principal_mag),
                    "raw_negative_gap": bool(
                        db20(B_mag / gamma_x_ideal_mag) < db20(B_mag / gamma_c_raw_mag)
                    ),
                    "cal_principal_negative_gap": bool(
                        db20(B_mag / gamma_x_ideal_mag)
                        < db20(B_mag / gamma_c_cal_principal_mag)
                    ),
                    "cal_anchor_negative_gap": bool(
                        db20(B_mag / gamma_x_ideal_mag)
                        < db20(B_mag / gamma_c_cal_anchor_mag)
                    ),
                }
            )

    theta_df = pd.DataFrame(theta_rows).sort_values(["material", "theta_deg"]).reset_index(drop=True)
    freq_df = pd.DataFrame(freq_rows).sort_values(["material", "theta_deg", "freq_ghz"]).reset_index(drop=True)

    for scope_name, mask in [
        ("validated_full", theta_df["in_valid_range"]),
        ("headline_oblique", theta_df["in_headline_oblique_range"]),
    ]:
        scoped = theta_df[mask].copy()
        for material in MATERIALS:
            sub = scoped[scoped["material"] == material]
            material_rows.append(
                {
                    "scope": scope_name,
                    "material": material,
                    "theta_min_deg": float(sub["theta_deg"].min()),
                    "theta_max_deg": float(sub["theta_deg"].max()),
                    "n_theta_rows": int(len(sub)),
                    "theta_rows_with_flips": int(sub["any_flip"].sum()),
                    "total_freq_flips": int(sub["flip_count"].sum()),
                    "mean_G_ideal_db": float(sub["G_ideal_db"].mean()),
                    "mean_G_cp_raw_db": float(sub["G_cp_raw_db"].mean()),
                    "mean_G_cp_cal_principal_db": float(sub["G_cp_cal_principal_db"].mean()),
                    "mean_G_cp_cal_anchor_db": float(sub["G_cp_cal_anchor_db"].mean()),
                    "mean_cal_anchor_minus_principal_db": float(
                        sub["cal_anchor_minus_principal_db"].mean()
                    ),
                    "raw_negative_rows": int(sub["raw_negative_gap"].sum()),
                    "cal_principal_negative_rows": int(
                        sub["cal_principal_negative_gap"].sum()
                    ),
                    "cal_anchor_negative_rows": int(sub["cal_anchor_negative_gap"].sum()),
                    "max_stage3_gamma_x_abs_diff": float(sub["stage3_gamma_x_abs_diff"].max()),
                    "max_stage3_gamma_c_raw_abs_diff": float(
                        sub["stage3_gamma_c_raw_abs_diff"].max()
                    ),
                    "max_stage3_gamma_c_eff_abs_diff": float(
                        sub["stage3_gamma_c_eff_abs_diff"].max()
                    ),
                }
            )

    material_df = pd.DataFrame(material_rows).sort_values(["scope", "material"]).reset_index(drop=True)
    return freq_df, theta_df, material_df


def make_plots(theta_df: pd.DataFrame, output_dir: Path) -> None:
    oblique = theta_df[theta_df["in_headline_oblique_range"]].copy()

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = oblique[oblique["material"] == material].sort_values("theta_deg")
        ax.plot(sub["theta_deg"], sub["G_ideal_db"], "o-", color="#111827", lw=1.8, label="Ideal")
        ax.plot(sub["theta_deg"], sub["G_cp_raw_db"], "s--", color="#7c2d12", lw=1.8, label="CP raw")
        ax.plot(
            sub["theta_deg"],
            sub["G_cp_cal_principal_db"],
            "x-.",
            color="#9333ea",
            lw=1.4,
            label="CP cal principal",
        )
        ax.plot(
            sub["theta_deg"],
            sub["G_cp_cal_anchor_db"],
            "d-.",
            color="#2563eb",
            lw=1.8,
            label="CP cal anchored",
        )
        ax.set_title(MATERIAL_LABELS[material])
        ax.set_xlabel("Incident angle [deg]")
        ax.grid(True, alpha=0.25)
        if idx == 0:
            ax.set_ylabel("Suppression gain [dB]")
            ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "fig_original_cp_phase_anchor_gain.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), sharey=True)
    for idx, material in enumerate(MATERIALS):
        ax = axes[idx]
        sub = theta_df[theta_df["material"] == material].sort_values("theta_deg")
        ax.bar(sub["theta_deg"], sub["flip_fraction"], color=MATERIAL_COLORS[material], width=3.2)
        ax.set_title(MATERIAL_LABELS[material])
        ax.set_xlabel("Incident angle [deg]")
        ax.grid(True, axis="y", alpha=0.25)
        if idx == 0:
            ax.set_ylabel("Flip fraction across band")
    fig.tight_layout()
    fig.savefig(output_dir / "fig_original_cp_phase_flip_fraction.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def write_report(
    freq_df: pd.DataFrame,
    theta_df: pd.DataFrame,
    material_df: pd.DataFrame,
    output_dir: Path,
    repo_root: Path,
) -> None:
    oblique = material_df[material_df["scope"] == "headline_oblique"].copy()
    total_freq_rows = int(len(freq_df))
    total_flips = int(freq_df["flip_applied"].sum())
    total_theta_with_flips = int(theta_df["any_flip"].sum())

    lines = [
        "# Original Non-Specular CP Phase-Anchor Validation",
        "",
        "Execution date: `2026-04-14`",
        "",
        "## Purpose",
        "",
        "Check whether the complex geometric-mean phase-anchor changes the original",
        "non-specular CP patch-stage results.",
        "",
        "## Headline",
        "",
        f"- total freq-resolved rows: `{total_freq_rows}`",
        f"- total phase-anchor flips: `{total_flips}`",
        f"- theta rows with at least one flip: `{total_theta_with_flips} / {len(theta_df)}`",
        "",
        "So unlike the earlier non-specular assumption, the original dataset must also",
        "be treated as phase-ambiguous at some angles. The anchor is not just defensive;",
        "it changes the calibrated branch on a measurable subset of rows.",
        "",
        "## Oblique Mean By Material (`20 deg` to valid max)",
        "",
    ]

    for _, row in oblique.iterrows():
        lines.extend(
            [
                f"### {row['material']}",
                "",
                f"- theta rows with flips: `{int(row['theta_rows_with_flips'])} / {int(row['n_theta_rows'])}`",
                f"- total freq flips: `{int(row['total_freq_flips'])}`",
                f"- ideal mean: `{row['mean_G_ideal_db']:.2f} dB`",
                f"- CP raw mean: `{row['mean_G_cp_raw_db']:.2f} dB`",
                f"- CP cal principal mean: `{row['mean_G_cp_cal_principal_db']:.2f} dB`",
                f"- CP cal anchored mean: `{row['mean_G_cp_cal_anchor_db']:.2f} dB`",
                f"- anchored minus principal: `{row['mean_cal_anchor_minus_principal_db']:+.2f} dB`",
                f"- raw negative rows: `{int(row['raw_negative_rows'])}`",
                f"- cal principal negative rows: `{int(row['cal_principal_negative_rows'])}`",
                f"- cal anchored negative rows: `{int(row['cal_anchor_negative_rows'])}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Stage 3 Cross-Check",
            "",
            "Anchored band-mean values are compared against the current Stage 3 export",
            "`patch_cp_extracted.csv`.",
            "",
        ]
    )
    for _, row in oblique.iterrows():
        lines.append(
            f"- {row['material']}: max abs diff vs Stage 3 "
            f"`Gamma_X={row['max_stage3_gamma_x_abs_diff']:.3e}`, "
            f"`Gamma_C_raw={row['max_stage3_gamma_c_raw_abs_diff']:.3e}`, "
            f"`Gamma_C_eff={row['max_stage3_gamma_c_eff_abs_diff']:.3e}`"
        )

    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- freq audit: `{(output_dir / 'original_cp_phase_anchor_freq_audit.csv').relative_to(repo_root)}`",
            f"- theta summary: `{(output_dir / 'original_cp_phase_anchor_theta_summary.csv').relative_to(repo_root)}`",
            f"- material summary: `{(output_dir / 'original_cp_phase_anchor_material_summary.csv').relative_to(repo_root)}`",
            f"- gain figure: `{(output_dir / 'fig_original_cp_phase_anchor_gain.png').relative_to(repo_root)}`",
            f"- flip figure: `{(output_dir / 'fig_original_cp_phase_flip_fraction.png').relative_to(repo_root)}`",
        ]
    )

    (output_dir / "ORIGINAL_CP_PHASE_ANCHOR_VALIDATION.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    args = build_argparser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    m1 = load_m1(args.csv_dir / "m1_los_5000.csv")
    m3 = load_sweep(args.csv_dir / "m3_off-boresigjt.csv")
    m2 = {material: load_sweep(args.csv_dir / f"m2_{material}_R_5000.csv") for material in MATERIALS}

    linear_truth = pd.read_csv(args.linear_truth)
    cp_truth = pd.read_csv(args.cp_truth)
    stage3_cp = pd.read_csv(args.stage3_cp)

    freq_df, theta_df, material_df = build_tables(
        m1, m3, m2, linear_truth, cp_truth, stage3_cp
    )

    freq_df.to_csv(output_dir / "original_cp_phase_anchor_freq_audit.csv", index=False)
    theta_df.to_csv(output_dir / "original_cp_phase_anchor_theta_summary.csv", index=False)
    material_df.to_csv(output_dir / "original_cp_phase_anchor_material_summary.csv", index=False)

    make_plots(theta_df, output_dir)
    write_report(freq_df, theta_df, material_df, output_dir, repo_root)

    print("Wrote original non-specular CP phase-anchor validation outputs.")


if __name__ == "__main__":
    main()
