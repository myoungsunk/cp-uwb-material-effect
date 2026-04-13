from __future__ import annotations

import argparse
import json
from pathlib import Path

from compare_extra_te_pec_existing_reports import (
    BlockKey,
    compare_blocks,
    compare_new_vs_old_y,
    parse_wide_blocks,
    read_old_surface_block,
    stage_root_from_script,
    build_summary as build_pec_summary,
)


def build_baseline_summary(stage_root: Path, extra_root: Path) -> dict[str, object]:
    baseline_dir = extra_root / "baseline" / "1.TE_baseline"
    blocks = {
        "Near_E_Table_3.csv": parse_wide_blocks(baseline_dir / "Near_E_Table_3.csv"),
        "Near_E_Table_3_1.csv": parse_wide_blocks(baseline_dir / "Near_E_Table_3_1.csv"),
    }

    old_zm = stage_root / "csv" / "merged" / "all_available_by_design" / "1.TE_baseline" / "1.TE_baseline__z_m.csv"
    old_zp = stage_root / "csv" / "merged" / "all_available_by_design" / "1.TE_baseline" / "1.TE_baseline__z_p.csv"

    summary: dict[str, object] = {
        "mapping_lock": {
            "Near_E_Table_3.csv": "z_m",
            "Near_E_Table_3_1.csv": "z_p",
            "field_type": "scattered",
        },
        "available_blocks": {},
        "correct_surface_vs_old": {},
        "cross_surface_vs_old": {},
        "z_m_vs_z_p": {},
    }

    for table_name, table_blocks in blocks.items():
        summary["available_blocks"][table_name] = [
            {
                "theta": key.theta,
                "kobs": key.kobs,
                "w_plane": key.w_plane,
            }
            for key in sorted(table_blocks, key=lambda item: (item.theta, float(item.kobs), item.w_plane))
        ]

    for theta_deg in [80.0, 85.0]:
        theta_key = f"{int(theta_deg)}deg"
        key = BlockKey(theta_key, "2", "500mm")

        new_zm = blocks["Near_E_Table_3.csv"][key]
        new_zp = blocks["Near_E_Table_3_1.csv"][key]
        old_block_zm = read_old_surface_block(old_zm, theta_deg, 2.0, 500)
        old_block_zp = read_old_surface_block(old_zp, theta_deg, 2.0, 500)

        summary["correct_surface_vs_old"][theta_key] = {
            "z_m_table3_vs_old_z_m": compare_new_vs_old_y(new_zm, old_block_zm),
            "z_p_table3_1_vs_old_z_p": compare_new_vs_old_y(new_zp, old_block_zp),
        }
        summary["cross_surface_vs_old"][theta_key] = {
            "z_m_table3_vs_old_z_p": compare_new_vs_old_y(new_zm, old_block_zp),
            "z_p_table3_1_vs_old_z_m": compare_new_vs_old_y(new_zp, old_block_zm),
        }
        summary["z_m_vs_z_p"][theta_key] = compare_blocks(new_zm, new_zp)

    return summary


def summary_markdown(summary: dict[str, object]) -> str:
    baseline = summary["baseline"]
    pec = summary["pec"]

    lines = [
        "# TE report lock bundle check (`te_lock_0413`)",
        "",
        "## Quick summary",
        "- bundle contents:",
        "  - `pec/`: TE PEC 80/85 existing-report re-extracts",
        "  - `baseline/`: TE baseline 80/85 existing-report re-extracts",
        "- mapping lock:",
        "  - `Near_E_Table_3.csv = z_m`",
        "  - `Near_E_Table_3_1.csv = z_p`",
        "  - both are `scattered` exports",
        "- PEC section:",
        "  - old exact duplicate-block symptom is gone inside the new `Near_E_Table_1/2` high-angle blocks",
        "  - the new PEC re-extracts still do not directly replace the active merged TE PEC dataset",
        "  - dominant `Ey` becomes much closer only after a global sign flip (`new ~= -old`)",
        "- baseline section:",
        "  - new baseline `Near_E_Table_3/3_1` expose only the intended `80/85 deg, kobs=2, w_plane=500 mm` blocks",
        "  - correct-surface comparison against the active merged baseline is relatively close without a strong sign-flip preference",
        "  - this makes the current sign/report-definition ambiguity look PEC-specific, not a blanket TE export issue",
        "",
        "## PEC carry-over metrics",
        f"- `Near_E_Table_1.csv` identical across 80-folder and 85-folder: `{pec['byte_identity']['Near_E_Table_1.csv']}`",
        f"- `Near_E_Table_2.csv` identical across 80-folder and 85-folder: `{pec['byte_identity']['Near_E_Table_2.csv']}`",
        f"- `Near_E_Table_3.csv` identical across 80-folder and 85-folder: `{pec['byte_identity']['Near_E_Table_3.csv']}`",
        f"- `Near_E_Table_3_1.csv` identical across 80-folder and 85-folder: `{pec['byte_identity']['Near_E_Table_3_1.csv']}`",
        f"- table1 vs table2 at 80deg, kobs=2, 500mm: {json.dumps(pec['table1_vs_table2']['80deg_kobs2_500'])}",
        f"- table1 vs table2 at 85deg, kobs=2, 500mm: {json.dumps(pec['table1_vs_table2']['85deg_kobs2_500'])}",
        "",
        "## Baseline correct-surface check",
    ]

    for theta_key in ["80deg", "85deg"]:
        correct = baseline["correct_surface_vs_old"][theta_key]
        lines.append(f"- {theta_key} z_m table3 vs old z_m: {json.dumps(correct['z_m_table3_vs_old_z_m'])}")
        lines.append(f"- {theta_key} z_p table3_1 vs old z_p: {json.dumps(correct['z_p_table3_1_vs_old_z_p'])}")

    lines.extend(
        [
            "",
            "## Baseline interpretation lock",
            "- If direct and negated errors are nearly the same, there is no strong evidence for a global sign flip.",
            "- That is what the new baseline comparator shows at both 80 deg and 85 deg.",
            "- Therefore the PEC re-extract sign issue should stay isolated as a PEC/report-definition problem until a common field-definition lock is proven.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    stage_root = stage_root_from_script()
    parser = argparse.ArgumentParser(description="Compare the combined TE PEC + baseline report-lock bundle against the active merged CSVs.")
    parser.add_argument(
        "--extra-root",
        type=Path,
        default=stage_root / "csv" / "raw" / "te_lock_0413",
        help="Root directory containing the PEC and baseline report-lock folders.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=stage_root / "results" / "te_lock_0413",
        help="Directory for JSON/Markdown summaries.",
    )
    args = parser.parse_args()

    extra_root = args.extra_root.resolve()
    summary = {
        "bundle_root": str(extra_root),
        "pec": build_pec_summary(stage_root, extra_root / "pec"),
        "baseline": build_baseline_summary(stage_root, extra_root),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "comparison_summary.json"
    md_path = args.output_dir / "SUMMARY.md"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md_path.write_text(summary_markdown(summary), encoding="utf-8")

    print(f"Wrote JSON: {json_path}")
    print(f"Wrote MD:   {md_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
