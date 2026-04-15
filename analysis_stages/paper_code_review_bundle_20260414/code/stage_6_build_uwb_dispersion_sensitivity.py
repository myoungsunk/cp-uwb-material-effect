# Consolidated review copy for paper-pipeline code assessment.
# Stage: 6
# Role: UWB dispersion-sensitivity study for the ideal suppression metric.
# Source: analysis_stages/stage6_uwb_dispersion_sensitivity_20260414/code/build_uwb_dispersion_sensitivity.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ANGLES_DEG = [20.0, 30.0, 45.0]
MATERIALS = ["concrete", "glass", "wood"]
FREQ_START_GHZ = 3.0
FREQ_STOP_GHZ = 10.0
FREQ_STEP_GHZ = 0.05
BAND_MEAN_TOL_DB = 1.0


def load_fresnel_module(stage_root: Path):
    ideal_code_dir = stage_root / "analysis_stages" / "ideal_te_tm_scattered_stage" / "code"
    ideal_code_dir_str = str(ideal_code_dir)
    if ideal_code_dir_str not in sys.path:
        sys.path.insert(0, ideal_code_dir_str)
    module_path = stage_root / "analysis_stages" / "ideal_te_tm_scattered_stage" / "code" / "sanity_check_fresnel.py"
    spec = importlib.util.spec_from_file_location("stage1_sanity_check_fresnel", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load Fresnel module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_plot(df: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True, constrained_layout=True)
    colors = {20.0: "#1f77b4", 30.0: "#d62728", 45.0: "#2ca02c"}

    for ax, material in zip(axes, MATERIALS):
        sub = df[df["material"] == material]
        for theta_deg in ANGLES_DEG:
            curve = sub[sub["theta_deg"] == theta_deg]
            ax.plot(
                curve["freq_ghz"],
                curve["G_supp_ideal_analytic_db"],
                label=f"{int(theta_deg)} deg",
                linewidth=2.0,
                color=colors[theta_deg],
            )
            ref = curve[np.isclose(curve["freq_ghz"], 6.5)].iloc[0]
            ax.scatter([6.5], [ref["G_supp_ideal_analytic_db"]], color=colors[theta_deg], s=28, zorder=3)
        ax.set_title(material)
        ax.set_xlabel("Frequency [GHz]")
        ax.set_xlim(FREQ_START_GHZ, FREQ_STOP_GHZ)
        ax.grid(True, alpha=0.25)

    axes[0].set_ylabel("Ideal suppression gain [dB]")
    axes[-1].legend(loc="best", frameon=False)
    fig.suptitle("Stage 6: UWB frequency robustness under locked material model", fontsize=12)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def main() -> None:
    stage_root = Path(__file__).resolve().parents[3]
    out_dir = Path(__file__).resolve().parents[1] / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    fresnel = load_fresnel_module(stage_root)
    cp_truth_path = (
        stage_root
        / "analysis_stages"
        / "ideal_te_tm_scattered_stage"
        / "results"
        / "current_manifest_runs"
        / "material_5000mm_kobs5_phase0_nominal_rerun_20260414"
        / "truth_table_cp_recomputed_20260414.csv"
    )
    linear_truth_path = (
        stage_root
        / "analysis_stages"
        / "ideal_te_tm_scattered_stage"
        / "results"
        / "current_manifest_runs"
        / "material_5000mm_kobs5_phase0_nominal_rerun_20260414"
        / "truth_table_linear_locked.csv"
    )

    cp_truth = pd.read_csv(cp_truth_path)
    linear_truth = pd.read_csv(linear_truth_path)
    locked = linear_truth.merge(
        cp_truth[["material", "theta_deg", "Gamma_X_mag"]],
        on=["material", "theta_deg"],
        how="inner",
        validate="one_to_one",
    )
    locked["B_locked_mag"] = locked[["R_TE_mag", "R_TM_mag"]].max(axis=1)
    locked["G_supp_ideal_locked_6p5_db"] = 20.0 * np.log10(locked["B_locked_mag"] / locked["Gamma_X_mag"])
    locked = locked[locked["material"].isin(MATERIALS) & locked["theta_deg"].isin(ANGLES_DEG)][
        ["material", "theta_deg", "G_supp_ideal_locked_6p5_db", "Gamma_X_mag"]
    ]

    freq_ghz_values = np.round(np.arange(FREQ_START_GHZ, FREQ_STOP_GHZ + 1e-9, FREQ_STEP_GHZ), 10)

    rows: list[dict[str, float | str | bool]] = []
    for material in MATERIALS:
        slab_thickness_m = float(fresnel.slab_thickness_for_material(material, float(fresnel.SLAB_THICKNESS_M)))
        eps_r = fresnel.MATERIAL_PERMITTIVITY[material]
        for theta_deg in ANGLES_DEG:
            for freq_ghz in freq_ghz_values:
                coeff = fresnel.slab_fresnel_coefficients(
                    material=material,
                    theta_deg=float(theta_deg),
                    freq_hz=float(freq_ghz) * 1e9,
                    slab_thickness_m=slab_thickness_m,
                )
                gamma_x = (coeff.r_te + coeff.r_tm) / 2.0
                gamma_c = (coeff.r_te - coeff.r_tm) / 2.0
                b_mag = max(abs(coeff.r_te), abs(coeff.r_tm))
                rows.append(
                    {
                        "material": material,
                        "theta_deg": float(theta_deg),
                        "freq_ghz": float(freq_ghz),
                        "slab_thickness_m": slab_thickness_m,
                        "eps_r_real_locked": float(np.real(eps_r)),
                        "eps_r_imag_locked": float(np.imag(eps_r)),
                        "R_TE_real": float(np.real(coeff.r_te)),
                        "R_TE_imag": float(np.imag(coeff.r_te)),
                        "R_TE_mag": float(abs(coeff.r_te)),
                        "R_TM_real": float(np.real(coeff.r_tm)),
                        "R_TM_imag": float(np.imag(coeff.r_tm)),
                        "R_TM_mag": float(abs(coeff.r_tm)),
                        "Gamma_X_real": float(np.real(gamma_x)),
                        "Gamma_X_imag": float(np.imag(gamma_x)),
                        "Gamma_X_mag": float(abs(gamma_x)),
                        "Gamma_C_real": float(np.real(gamma_c)),
                        "Gamma_C_imag": float(np.imag(gamma_c)),
                        "Gamma_C_mag": float(abs(gamma_c)),
                        "B_mag": float(b_mag),
                        "G_supp_ideal_analytic_db": float(20.0 * np.log10(b_mag / max(abs(gamma_x), 1e-15))),
                    }
                )

    full = pd.DataFrame(rows)
    full = full.merge(locked, on=["material", "theta_deg"], how="left", validate="many_to_one")
    full["is_center_6p5ghz"] = np.isclose(full["freq_ghz"], 6.5)
    full.to_csv(out_dir / "uwb_dispersion_sensitivity_full.csv", index=False)

    summary_rows: list[dict[str, float | str | bool]] = []
    for (material, theta_deg), group in full.groupby(["material", "theta_deg"], sort=True):
        center_row = group[group["is_center_6p5ghz"]].iloc[0]
        band_mean = float(group["G_supp_ideal_analytic_db"].mean())
        band_min = float(group["G_supp_ideal_analytic_db"].min())
        band_max = float(group["G_supp_ideal_analytic_db"].max())
        analytic_6p5 = float(center_row["G_supp_ideal_analytic_db"])
        locked_6p5 = float(center_row["G_supp_ideal_locked_6p5_db"])
        summary_rows.append(
            {
                "material": material,
                "theta_deg": float(theta_deg),
                "freq_start_ghz": FREQ_START_GHZ,
                "freq_stop_ghz": FREQ_STOP_GHZ,
                "freq_step_ghz": FREQ_STEP_GHZ,
                "n_freq": int(len(group)),
                "G_supp_ideal_locked_6p5_db": locked_6p5,
                "G_supp_ideal_analytic_6p5_db": analytic_6p5,
                "band_mean_db": band_mean,
                "band_min_db": band_min,
                "band_max_db": band_max,
                "band_mean_minus_locked_6p5_db": band_mean - locked_6p5,
                "band_mean_minus_analytic_6p5_db": band_mean - analytic_6p5,
                "max_abs_excursion_from_locked_6p5_db": max(abs(band_min - locked_6p5), abs(band_max - locked_6p5)),
                "max_abs_excursion_from_analytic_6p5_db": max(abs(band_min - analytic_6p5), abs(band_max - analytic_6p5)),
                "pass_band_mean_within_1db_of_locked_6p5": abs(band_mean - locked_6p5) <= BAND_MEAN_TOL_DB,
                "pass_band_mean_within_1db_of_analytic_6p5": abs(band_mean - analytic_6p5) <= BAND_MEAN_TOL_DB,
            }
        )

    summary = pd.DataFrame(summary_rows).sort_values(["material", "theta_deg"], kind="stable")
    summary.to_csv(out_dir / "uwb_dispersion_sensitivity_summary.csv", index=False)

    build_plot(full, out_dir / "fig_stage6_uwb_dispersion_sensitivity.png")

    all_pass_locked = bool(summary["pass_band_mean_within_1db_of_locked_6p5"].all())
    all_pass_analytic = bool(summary["pass_band_mean_within_1db_of_analytic_6p5"].all())
    md_lines = [
        "# Stage 6 - UWB Dispersion Sensitivity",
        "",
        "Execution date: `2026-04-14`",
        "",
        "## Important Scope Note",
        "",
        "No frequency-dependent material law was identified in the current repository code.",
        "So this stage is executed as a `3-10 GHz` frequency robustness sweep under the",
        "locked complex-permittivity model already used by `sanity_check_fresnel.py`, not as",
        "a full externally calibrated dispersive material characterization.",
        "",
        "## Sweep Setup",
        "",
        f"- materials: `{', '.join(MATERIALS)}`",
        f"- angles: `{', '.join(str(int(v)) for v in ANGLES_DEG)} deg`",
        f"- frequency range: `{FREQ_START_GHZ:.1f}-{FREQ_STOP_GHZ:.1f} GHz`",
        f"- step: `{FREQ_STEP_GHZ:.2f} GHz`",
        "- residual definition: `Gamma_X = (R_TE + R_TM)/2`",
        "- gain definition: `G_supp_ideal = 20 log10(B / |Gamma_X|)`, with `B = max(|R_TE|, |R_TM|)`",
        "",
        "## Pass Condition",
        "",
        "- external reference check: band mean within `+/- 1 dB` of the locked `6.5 GHz` ideal value",
        "- internal frequency-flatness check: band mean within `+/- 1 dB` of the analytic `6.5 GHz` value from the same material model",
        f"- overall result vs locked `6.5 GHz`: `{'PASS' if all_pass_locked else 'PARTIAL / FAIL'}`",
        f"- overall result vs analytic `6.5 GHz`: `{'PASS' if all_pass_analytic else 'PARTIAL / FAIL'}`",
        "",
        "## Summary",
        "",
    ]

    for _, row in summary.iterrows():
        md_lines.extend(
            [
                f"### {row['material']} / {int(row['theta_deg'])} deg",
                "",
                f"- locked `6.5 GHz`: `{row['G_supp_ideal_locked_6p5_db']:.2f} dB`",
                f"- analytic `6.5 GHz`: `{row['G_supp_ideal_analytic_6p5_db']:.2f} dB`",
                f"- band mean: `{row['band_mean_db']:.2f} dB`",
                f"- band min/max: `{row['band_min_db']:.2f} / {row['band_max_db']:.2f} dB`",
                f"- band mean minus locked `6.5 GHz`: `{row['band_mean_minus_locked_6p5_db']:.2f} dB`",
                f"- band mean minus analytic `6.5 GHz`: `{row['band_mean_minus_analytic_6p5_db']:.2f} dB`",
                f"- max excursion from locked `6.5 GHz`: `{row['max_abs_excursion_from_locked_6p5_db']:.2f} dB`",
                f"- max excursion from analytic `6.5 GHz`: `{row['max_abs_excursion_from_analytic_6p5_db']:.2f} dB`",
                f"- pass vs locked `6.5 GHz`: `{bool(row['pass_band_mean_within_1db_of_locked_6p5'])}`",
                f"- pass vs analytic `6.5 GHz`: `{bool(row['pass_band_mean_within_1db_of_analytic_6p5'])}`",
                "",
            ]
        )

    md_lines.extend(
        [
            "## Interpretation",
            "",
            "- The locked-vs-band comparison mixes two effects: frequency variation across the band and any fixed offset between the analytic slab model and the locked `6.5 GHz` HFSS truth.",
            "- The analytic-vs-band comparison isolates only the band-flatness question under the current locked material model.",
            "- So this stage should be reported as an internal robustness check under the current analytic material model, not as a replacement for the locked single-tone truth.",
            "",
            "## Outputs",
            "",
            f"- full CSV: `{out_dir / 'uwb_dispersion_sensitivity_full.csv'}`",
            f"- summary CSV: `{out_dir / 'uwb_dispersion_sensitivity_summary.csv'}`",
            f"- figure: `{out_dir / 'fig_stage6_uwb_dispersion_sensitivity.png'}`",
        ]
    )
    (out_dir / "STAGE6_SUMMARY.md").write_text("\n".join(md_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
