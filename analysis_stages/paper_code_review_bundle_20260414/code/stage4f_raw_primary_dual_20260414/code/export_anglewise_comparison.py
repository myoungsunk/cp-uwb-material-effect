from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


MATERIALS = ["concrete", "glass", "wood"]


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export angle-wise comparison tables from the Stage 4f raw-primary result."
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results" / "stage4f_raw_primary_full.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
    )
    return parser


def main() -> None:
    args = build_argparser().parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input_csv)
    df = df[df["material"].isin(MATERIALS)].copy().sort_values(["material", "theta_deg"]).reset_index(drop=True)

    anglewise = df[
        [
            "material",
            "theta_deg",
            "G_ideal_db",
            "G_patch_raw_db",
            "G_patch_eff_db",
            "Delta_ideal_minus_raw_db",
            "Delta_ideal_minus_eff_db",
            "gamma_x_ideal_mag",
            "gamma_c_patch_raw_mag",
            "gamma_c_patch_eff_mag",
            "delta_raw_negative",
            "delta_eff_negative",
        ]
    ].copy()
    anglewise = anglewise.rename(
        columns={
            "G_ideal_db": "G_supp_ideal_db",
            "G_patch_raw_db": "G_supp_patch_raw_db",
            "G_patch_eff_db": "G_supp_patch_eff_db",
        }
    )
    csv_path = output_dir / "table1_raw_primary_anglewise.csv"
    anglewise.to_csv(csv_path, index=False)

    wide_rows = []
    for theta_deg, sub in anglewise.groupby("theta_deg"):
        row = {"theta_deg": float(theta_deg)}
        for material in MATERIALS:
            mat_sub = sub[sub["material"] == material]
            if mat_sub.empty:
                continue
            r = mat_sub.iloc[0]
            prefix = material
            row[f"{prefix}_G_ideal_db"] = r["G_supp_ideal_db"]
            row[f"{prefix}_G_raw_db"] = r["G_supp_patch_raw_db"]
            row[f"{prefix}_G_eff_db"] = r["G_supp_patch_eff_db"]
            row[f"{prefix}_Delta_raw_db"] = r["Delta_ideal_minus_raw_db"]
            row[f"{prefix}_Delta_eff_db"] = r["Delta_ideal_minus_eff_db"]
        wide_rows.append(row)
    wide_df = pd.DataFrame(wide_rows).sort_values("theta_deg").reset_index(drop=True)
    wide_path = output_dir / "table1_raw_primary_anglewise_theta_wide.csv"
    wide_df.to_csv(wide_path, index=False)

    lines = [
        "# Stage 4f Angle-Wise Comparison",
        "",
        "Primary interpretation:",
        "",
        "- use `raw` for the current paper headline",
        "- use `eff` as a supplementary corrected series",
        "",
    ]
    for material in MATERIALS:
        sub = anglewise[anglewise["material"] == material].copy()
        lines.append(f"## {material.capitalize()}")
        lines.append("")
        lines.append("| theta_deg | G_ideal_db | G_raw_db | G_eff_db | Delta_raw_db | Delta_eff_db |")
        lines.append("| ---: | ---: | ---: | ---: | ---: | ---: |")
        for _, row in sub.iterrows():
            lines.append(
                f"| {row['theta_deg']:.0f} | {row['G_supp_ideal_db']:.2f} | {row['G_supp_patch_raw_db']:.2f} | {row['G_supp_patch_eff_db']:.2f} | {row['Delta_ideal_minus_raw_db']:.2f} | {row['Delta_ideal_minus_eff_db']:.2f} |"
            )
        lines.append("")
    md_path = output_dir / "STAGE4F_ANGLEWISE_COMPARISON.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print("Wrote Stage 4f angle-wise comparison tables.")


if __name__ == "__main__":
    main()
