from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


MATERIALS = ["concrete", "glass", "wood"]
VALID_MAX = {"concrete": 55.0, "glass": 60.0, "wood": 45.0}
PASS_GAP_DB = 1.0
VARIABLE_SPECS = [
    ("gamma_hat_c_cp_raw", "CP residual raw"),
    ("gamma_hat_c_cp_eff", "CP residual eff-corrected"),
    ("gamma_hat_x_cp_sys", "CP dominant/system"),
    ("gamma_x_from_lp", "LP-derived Gamma_X"),
    ("gamma_c_from_lp", "LP-derived Gamma_C"),
]


def build_argparser() -> argparse.ArgumentParser:
    bundle_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description=(
            "Authoritative coherent-vs-incoherent Stage 4 audit using the existing "
            "Stage 3 frequency-resolved CP/LP exports."
        )
    )
    parser.add_argument(
        "--patch-cp-freq",
        type=Path,
        default=bundle_root / "data" / "stage_3" / "cp" / "patch_cp_extracted_freq_resolved.csv",
    )
    parser.add_argument(
        "--patch-lp-freq",
        type=Path,
        default=bundle_root / "data" / "stage_3" / "lp" / "patch_lp_extracted_freq_resolved.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=bundle_root / "results",
    )
    parser.add_argument(
        "--include-metal",
        action="store_true",
        help="Include metal reference rows in the exported audit tables.",
    )
    parser.add_argument(
        "--all-angles",
        action="store_true",
        help="Disable the Stage 4 main-range filter and keep every locked angle row.",
    )
    return parser


def db20(value: float) -> float:
    return float(20.0 * np.log10(max(float(value), 1e-12)))


def complex_from_cols(df: pd.DataFrame, prefix: str) -> np.ndarray:
    return df[f"{prefix}_real"].to_numpy(dtype=float) + 1j * df[f"{prefix}_imag"].to_numpy(dtype=float)


def ensure_columns(df: pd.DataFrame, prefix: str) -> None:
    required = {f"{prefix}_real", f"{prefix}_imag"}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise KeyError(f"Missing columns for '{prefix}': {missing}")


def valid_stage4_main_range(material: str, theta_deg: float) -> bool:
    return float(theta_deg) >= 20.0 and float(theta_deg) <= VALID_MAX[str(material)]


def selected_materials(include_metal: bool) -> list[str]:
    return ["metal", *MATERIALS] if include_metal else MATERIALS.copy()


def build_frequency_dataframe(
    patch_cp: pd.DataFrame,
    patch_lp: pd.DataFrame,
    *,
    include_metal: bool,
    restrict_stage4_main_range: bool,
) -> pd.DataFrame:
    keep_lp_cols = [
        "material",
        "theta_deg",
        "freq_ghz",
        "gamma_x_from_lp_real",
        "gamma_x_from_lp_imag",
        "gamma_c_from_lp_real",
        "gamma_c_from_lp_imag",
    ]
    freq_df = (
        patch_cp.merge(patch_lp[keep_lp_cols], on=["material", "theta_deg", "freq_ghz"], how="inner")
        .sort_values(["material", "theta_deg", "freq_ghz"])
        .reset_index(drop=True)
    )
    freq_df = freq_df[freq_df["material"].isin(selected_materials(include_metal))].copy()

    if restrict_stage4_main_range:
        freq_df = freq_df[
            freq_df.apply(
                lambda row: row["material"] == "metal"
                or valid_stage4_main_range(str(row["material"]), float(row["theta_deg"])),
                axis=1,
            )
        ].copy()

    for variable_id, _ in VARIABLE_SPECS:
        ensure_columns(freq_df, variable_id)

    return freq_df.reset_index(drop=True)


def build_detail_rows(freq_df: pd.DataFrame) -> pd.DataFrame:
    detail_rows: list[dict[str, object]] = []

    for (material, theta_deg), sub in freq_df.groupby(["material", "theta_deg"], sort=True):
        sub = sub.sort_values("freq_ghz").reset_index(drop=True)
        n_freq = int(len(sub))
        freq_min = float(sub["freq_ghz"].min())
        freq_max = float(sub["freq_ghz"].max())
        freq_center = float(sub["freq_ghz"].mean())

        for variable_id, variable_label in VARIABLE_SPECS:
            values = complex_from_cols(sub, variable_id)
            incoherent_mag = float(np.mean(np.abs(values)))
            coherent_mean = complex(np.mean(values))
            coherent_mag = float(np.abs(coherent_mean))
            incoherent_db = db20(incoherent_mag)
            coherent_db = db20(coherent_mag)
            incoherent_minus_coherent_db = incoherent_db - coherent_db

            detail_rows.append(
                {
                    "material": material,
                    "theta_deg": float(theta_deg),
                    "variable_id": variable_id,
                    "variable_label": variable_label,
                    "n_freq": n_freq,
                    "freq_min_ghz": freq_min,
                    "freq_max_ghz": freq_max,
                    "freq_center_ghz": freq_center,
                    "incoherent_mag": incoherent_mag,
                    "incoherent_db": incoherent_db,
                    "coherent_mag": coherent_mag,
                    "coherent_db": coherent_db,
                    "coherent_mean_real": float(coherent_mean.real),
                    "coherent_mean_imag": float(coherent_mean.imag),
                    "coherent_minus_incoherent_db": coherent_db - incoherent_db,
                    "incoherent_minus_coherent_db": incoherent_minus_coherent_db,
                    "coherent_gap_ge_1db": bool(incoherent_minus_coherent_db >= PASS_GAP_DB),
                }
            )

    return pd.DataFrame(detail_rows).sort_values(
        ["material", "theta_deg", "variable_id"]
    ).reset_index(drop=True)


def summarize(detail_df: pd.DataFrame, materials: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    material_rollup_rows: list[dict[str, object]] = []
    material_order = [m for m in materials if m in detail_df["material"].unique()] + ["overall"]

    for material in material_order:
        material_sub = detail_df if material == "overall" else detail_df[detail_df["material"] == material]
        if material_sub.empty:
            continue

        material_rollup_rows.append(
            {
                "material": material,
                "n_comparisons": int(len(material_sub)),
                "rows_with_gap_ge_1db": int(material_sub["coherent_gap_ge_1db"].sum()),
                "row_frac_with_gap_ge_1db": float(material_sub["coherent_gap_ge_1db"].mean()),
                "max_incoherent_minus_coherent_db": float(material_sub["incoherent_minus_coherent_db"].max()),
                "mean_incoherent_minus_coherent_db": float(material_sub["incoherent_minus_coherent_db"].mean()),
            }
        )

        for variable_id, variable_label in VARIABLE_SPECS:
            sub = material_sub[material_sub["variable_id"] == variable_id].copy()
            if sub.empty:
                continue
            worst_idx = sub["incoherent_minus_coherent_db"].idxmax()
            summary_rows.append(
                {
                    "material": material,
                    "variable_id": variable_id,
                    "variable_label": variable_label,
                    "n_angle_rows": int(len(sub)),
                    "rows_with_gap_ge_1db": int(sub["coherent_gap_ge_1db"].sum()),
                    "row_frac_with_gap_ge_1db": float(sub["coherent_gap_ge_1db"].mean()),
                    "mean_incoherent_db": float(sub["incoherent_db"].mean()),
                    "mean_coherent_db": float(sub["coherent_db"].mean()),
                    "mean_incoherent_minus_coherent_db": float(sub["incoherent_minus_coherent_db"].mean()),
                    "median_incoherent_minus_coherent_db": float(sub["incoherent_minus_coherent_db"].median()),
                    "max_incoherent_minus_coherent_db": float(sub["incoherent_minus_coherent_db"].max()),
                    "worst_material": str(sub.loc[worst_idx, "material"]),
                    "worst_theta_deg": float(sub.loc[worst_idx, "theta_deg"]),
                    "worst_incoherent_db": float(sub.loc[worst_idx, "incoherent_db"]),
                    "worst_coherent_db": float(sub.loc[worst_idx, "coherent_db"]),
                    "pass_criterion_met": bool(sub["coherent_gap_ge_1db"].any()),
                }
            )

    summary_df = pd.DataFrame(summary_rows).sort_values(
        ["variable_id", "material"]
    ).reset_index(drop=True)
    material_rollup_df = pd.DataFrame(material_rollup_rows).reset_index(drop=True)
    return summary_df, material_rollup_df


def write_summary_md(
    *,
    detail_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    material_rollup_df: pd.DataFrame,
    detail_path: Path,
    summary_path: Path,
    rollup_path: Path,
    output_path: Path,
    repo_root: Path,
    title: str,
    scope_lines: list[str],
) -> None:
    overall_summary = summary_df[summary_df["material"] == "overall"].copy()
    flagged_rows = detail_df[detail_df["coherent_gap_ge_1db"]].copy()
    top_rows = detail_df.sort_values("incoherent_minus_coherent_db", ascending=False).head(10)

    md_lines = [
        f"# {title}",
        "",
        "Execution date: `2026-04-16`",
        "",
        "## Scope",
        "",
        *scope_lines,
        "",
        "## Core Finding",
        "",
    ]

    if flagged_rows.empty:
        md_lines.append("- No row crossed the 1 dB threshold; current replay does not show direct cause #1 evidence.")
    else:
        md_lines.append(
            f"- `{int(len(flagged_rows))}` row(s) crossed the 1 dB threshold; cause #1 is directly evidenced at those rows."
        )

    for _, row in overall_summary.iterrows():
        md_lines.append(
            f"- {row['variable_id']}: "
            f"{int(row['rows_with_gap_ge_1db'])}/{int(row['n_angle_rows'])} row(s) >= 1 dB, "
            f"mean gap={row['mean_incoherent_minus_coherent_db']:.3f} dB, "
            f"max gap={row['max_incoherent_minus_coherent_db']:.3f} dB "
            f"at {row['worst_material']} {row['worst_theta_deg']:.0f} deg."
        )

    md_lines.extend(
        [
            "",
            "## Material Rollup",
            "",
        ]
    )

    for _, row in material_rollup_df[material_rollup_df["material"] != "overall"].iterrows():
        md_lines.append(
            f"- {row['material']}: "
            f"{int(row['rows_with_gap_ge_1db'])}/{int(row['n_comparisons'])} comparisons >= 1 dB, "
            f"mean gap={row['mean_incoherent_minus_coherent_db']:.3f} dB, "
            f"max gap={row['max_incoherent_minus_coherent_db']:.3f} dB."
        )

    md_lines.extend(
        [
            "",
            "## Strongest Rows",
            "",
        ]
    )

    for _, row in top_rows.iterrows():
        md_lines.append(
            f"- {row['material']} {row['theta_deg']:.0f} deg {row['variable_id']}: "
            f"incoherent={row['incoherent_db']:.3f} dB, "
            f"coherent={row['coherent_db']:.3f} dB, "
            f"gap={row['incoherent_minus_coherent_db']:.3f} dB, "
            f"flag={bool(row['coherent_gap_ge_1db'])}."
        )

    md_lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Detail CSV: `{detail_path.relative_to(repo_root)}`",
            f"- Variable/material summary CSV: `{summary_path.relative_to(repo_root)}`",
            f"- Material rollup CSV: `{rollup_path.relative_to(repo_root)}`",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")


def run_audit(
    *,
    patch_cp_path: Path,
    patch_lp_path: Path,
    output_dir: Path,
    include_metal: bool,
    restrict_stage4_main_range: bool,
    repo_root: Path,
    detail_filename: str,
    summary_filename: str,
    rollup_filename: str,
    md_filename: str,
    md_title: str,
    scope_lines: list[str],
) -> dict[str, Path]:
    patch_cp = pd.read_csv(patch_cp_path)
    patch_lp = pd.read_csv(patch_lp_path)

    freq_df = build_frequency_dataframe(
        patch_cp=patch_cp,
        patch_lp=patch_lp,
        include_metal=include_metal,
        restrict_stage4_main_range=restrict_stage4_main_range,
    )
    materials = selected_materials(include_metal)
    detail_df = build_detail_rows(freq_df)
    summary_df, material_rollup_df = summarize(detail_df, materials)

    output_dir.mkdir(parents=True, exist_ok=True)
    detail_path = output_dir / detail_filename
    summary_path = output_dir / summary_filename
    rollup_path = output_dir / rollup_filename
    md_path = output_dir / md_filename

    detail_df.to_csv(detail_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    material_rollup_df.to_csv(rollup_path, index=False)
    write_summary_md(
        detail_df=detail_df,
        summary_df=summary_df,
        material_rollup_df=material_rollup_df,
        detail_path=detail_path,
        summary_path=summary_path,
        rollup_path=rollup_path,
        output_path=md_path,
        repo_root=repo_root,
        title=md_title,
        scope_lines=scope_lines,
    )

    return {
        "detail": detail_path,
        "summary": summary_path,
        "rollup": rollup_path,
        "md": md_path,
    }


def main() -> None:
    args = build_argparser().parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    output_dir = args.output_dir.resolve()
    debug_dir = output_dir / "debug"
    restrict_stage4_main_range = not args.all_angles

    scope_lines = [
        "- Input source: existing Stage 3 frequency-resolved CP/LP exports only.",
        "- Incoherent band mean: `mean(|x(f)|)`.",
        "- Coherent band mean: `|mean(x(f))|`.",
        f"- Materials included: `{'metal, concrete, glass, wood' if args.include_metal else 'concrete, glass, wood'}`.",
        (
            "- Angle filter: Stage 4 main range only "
            "(`20 deg <= theta <= material-specific VALID_MAX`)."
            if restrict_stage4_main_range
            else "- Angle filter: all locked angle rows retained."
        ),
        f"- Pass criterion: incoherent-coherent gap `>= {PASS_GAP_DB:.1f} dB`.",
    ]
    outputs = run_audit(
        patch_cp_path=args.patch_cp_freq,
        patch_lp_path=args.patch_lp_freq,
        output_dir=output_dir,
        include_metal=args.include_metal,
        restrict_stage4_main_range=restrict_stage4_main_range,
        repo_root=repo_root,
        detail_filename="audit_coherent_vs_incoherent.csv",
        summary_filename="audit_coherent_vs_incoherent_summary_by_material.csv",
        rollup_filename="audit_coherent_vs_incoherent_material_rollup.csv",
        md_filename=str(Path("debug") / "AUDIT_COHERENT_VS_INCOHERENT.md"),
        md_title="C2 Coherent vs Incoherent Band-Average Audit",
        scope_lines=scope_lines,
    )

    print(f"Wrote {outputs['detail']}")
    print(f"Wrote {outputs['summary']}")
    print(f"Wrote {outputs['rollup']}")
    print(f"Wrote {debug_dir / 'AUDIT_COHERENT_VS_INCOHERENT.md'}")


if __name__ == "__main__":
    main()
