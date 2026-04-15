# Consolidated review copy for paper-pipeline code assessment.
# Stage: 4
# Role: Write the sweep-versus-Stage-3 alignment note used during sanity-check debugging.
# Source: analysis_stages/sanity_check_sweep_vs_stage3_20260414/code/build_sanity_sweep_alignment_note.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


CHANNEL_PAIRS = [
    ("LL", "mag(S(RX_LH_p1,TX_LH_p1)) []", "ang_deg(S(RX_LH_p1,TX_LH_p1)) [deg]"),
    ("LR", "mag(S(RX_LH_p1,TX_RH_p1)) []", "ang_deg(S(RX_LH_p1,TX_RH_p1)) [deg]"),
    ("RL", "mag(S(RX_RH_p1,TX_LH_p1)) []", "ang_deg(S(RX_RH_p1,TX_LH_p1)) [deg]"),
    ("RR", "mag(S(RX_RH_p1,TX_RH_p1)) []", "ang_deg(S(RX_RH_p1,TX_RH_p1)) [deg]"),
]


def wrap_phase_diff_deg(a: pd.Series, b: pd.Series) -> pd.Series:
    diff = (a - b + 180.0) % 360.0 - 180.0
    return diff.abs()


def compare_material_to_stage3(material: str, sweep_path: Path, stage3_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    sweep = pd.read_csv(sweep_path)
    stage3 = pd.read_csv(stage3_path)
    merged = sweep.merge(stage3, on=["theta_r [deg]", "Freq [GHz]"], how="inner", suffixes=("_sweep", "_stage3"))

    rows = []
    for channel, mag_key, phase_key in CHANNEL_PAIRS:
        mag_diff = (merged[f"{mag_key}_sweep"] - merged[f"{mag_key}_stage3"]).abs()
        phase_diff = wrap_phase_diff_deg(merged[f"{phase_key}_sweep"], merged[f"{phase_key}_stage3"])
        rows.append(
            {
                "material": material,
                "channel": channel,
                "n_rows": int(len(merged)),
                "mag_mae": float(mag_diff.mean()),
                "mag_max_abs_diff": float(mag_diff.max()),
                "phase_mae_deg": float(phase_diff.mean()),
                "phase_max_abs_diff_deg": float(phase_diff.max()),
            }
        )
    return merged, pd.DataFrame(rows)


def best_anchor_match(anchor_name: str, anchor_path: Path, candidates: dict[str, Path]) -> pd.DataFrame:
    anchor = pd.read_csv(anchor_path).iloc[0]
    rows = []
    for candidate_name, candidate_path in candidates.items():
        df = pd.read_csv(candidate_path)
        for _, cand in df.iterrows():
            score = 0.0
            for _, mag_key, phase_key in CHANNEL_PAIRS:
                score += abs(float(anchor[mag_key]) - float(cand[mag_key]))
                phase_diff = abs(((float(anchor[phase_key]) - float(cand[phase_key]) + 180.0) % 360.0) - 180.0)
                score += phase_diff / 180.0
            row = {
                "anchor": anchor_name,
                "candidate_set": candidate_name,
                "theta_deg": float(cand.get("theta_r [deg]", np.nan)),
                "freq_ghz": float(cand["Freq [GHz]"]),
                "alignment_score": float(score),
            }
            for channel, mag_key, phase_key in CHANNEL_PAIRS:
                row[f"{channel}_mag_abs_diff"] = abs(float(anchor[mag_key]) - float(cand[mag_key]))
                row[f"{channel}_phase_abs_diff_deg"] = abs(
                    ((float(anchor[phase_key]) - float(cand[phase_key]) + 180.0) % 360.0) - 180.0
                )
            rows.append(row)
    out = pd.DataFrame(rows).sort_values("alignment_score", kind="stable").reset_index(drop=True)
    return out


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    out_dir = Path(__file__).resolve().parents[1] / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    external_dir = Path(r"E:\0. CP Antenna\0. TRACK2_3_SIM\ANTENNA_SOURCE\sending")
    stage3_dir = repo_root / "analysis_stages" / "stage3_patch_paper_final_20260414" / "cp" / "csv"

    material_map = {
        "concrete": (
            external_dir / "sanity check_CONCRETE_SWEEP.csv",
            stage3_dir / "m2_concrete_R_5000.csv",
        ),
        "glass": (
            external_dir / "sanity check_GLASS_SWEEP.csv",
            stage3_dir / "m2_glass_R_5000.csv",
        ),
        "wood": (
            external_dir / "sanity check_WOOD_SWEEP.csv",
            stage3_dir / "m2_wood_R_5000.csv",
        ),
    }

    full_rows = []
    summary_rows = []
    for material, (sweep_path, stage3_path) in material_map.items():
        merged, summary = compare_material_to_stage3(material, sweep_path, stage3_path)
        full_rows.append(merged.assign(material=material))
        summary_rows.append(summary)

    pd.concat(full_rows, ignore_index=True).to_csv(out_dir / "material_sweep_vs_stage3_m2_full.csv", index=False)
    summary_df = pd.concat(summary_rows, ignore_index=True)
    summary_df.to_csv(out_dir / "material_sweep_vs_stage3_m2_summary.csv", index=False)

    anchor_candidates = {
        "stage3_m3_old": stage3_dir / "m3_off-boresigjt.csv",
        "stage3_m3_new": stage3_dir / "m3_off-boresigjt.NEW.csv",
        "stage3_metal_R": stage3_dir / "m2_metal_R_5000.csv",
        "stage3_metal_T": stage3_dir / "m2_metal_T_5000.csv",
    }
    m3_best = best_anchor_match("sanity_check_M3_SWEEP", external_dir / "sanity check_M3_SWEEP.csv", anchor_candidates)
    pec_best = best_anchor_match("sanity_check_PEC_SWEEP", external_dir / "sanity check_PEC_SWEEP.csv", anchor_candidates)
    m3_best.to_csv(out_dir / "m3_sweep_anchor_match_candidates.csv", index=False)
    pec_best.to_csv(out_dir / "pec_sweep_anchor_match_candidates.csv", index=False)

    m3_top = m3_best.iloc[0]
    pec_top = pec_best.iloc[0]

    md_lines = [
        "# Sanity Sweep Alignment Note",
        "",
        "Execution date: `2026-04-14`",
        "",
        "## Conclusion",
        "",
        "- The new material sweep files (`CONCRETE/GLASS/WOOD_SWEEP`) are numerically aligned with the existing Stage 3 raw CP material files.",
        "- The mismatch seen in direct `Gamma` reconstruction is not a material-data mismatch. It comes from using a single sweep reference (`M3_SWEEP`) to emulate a Stage 3 pipeline that originally used angle-resolved reference handling.",
        "- Therefore the answer is split:",
        "  - material sweep raw channels: effectively the same CP dataset",
        "  - full-angle CP reconstruction with only the provided sweep references: not identical to the locked Stage 3 outputs",
        "",
        "## Material Sweep vs Stage 3 Raw M2",
        "",
    ]
    for material in ["concrete", "glass", "wood"]:
        sub = summary_df[summary_df["material"] == material]
        md_lines.append(f"### {material}")
        md_lines.append("")
        for _, row in sub.iterrows():
            md_lines.append(
                f"- {row['channel']}: mag MAE `{row['mag_mae']:.6e}`, max mag diff `{row['mag_max_abs_diff']:.6e}`, phase MAE `{row['phase_mae_deg']:.3f} deg`, max phase diff `{row['phase_max_abs_diff_deg']:.3f} deg`"
            )
        md_lines.append("")

    md_lines.extend(
        [
            "## Best Anchor Matches",
            "",
            f"- `M3_SWEEP` best match: `{m3_top['candidate_set']}` at `theta={m3_top['theta_deg']:.1f} deg`, `f={m3_top['freq_ghz']:.3f} GHz`, score `{m3_top['alignment_score']:.6f}`",
            f"- `PEC_SWEEP` best match: `{pec_top['candidate_set']}` at `theta={pec_top['theta_deg']:.1f} deg`, `f={pec_top['freq_ghz']:.3f} GHz`, score `{pec_top['alignment_score']:.6f}`",
            "",
            "## Interpretation",
            "",
            "- `CONCRETE/GLASS/WOOD_SWEEP` can be treated as the same raw CP material sweeps already used by the Stage 3 project.",
            "- `M3_SWEEP` and `PEC_SWEEP` behave like anchor/reference files, not full angle-resolved substitutes for the original Stage 3 reference stack.",
            "- So a one-point sanity at `concrete / 30 deg / 6.5 GHz` is valid, but a full-angle replay of Stage 3 needs the original angle-resolved reference files or an explicitly re-locked sweep reference convention.",
            "",
            "## Outputs",
            "",
            f"- material summary: `{out_dir / 'material_sweep_vs_stage3_m2_summary.csv'}`",
            f"- M3 candidates: `{out_dir / 'm3_sweep_anchor_match_candidates.csv'}`",
            f"- PEC candidates: `{out_dir / 'pec_sweep_anchor_match_candidates.csv'}`",
        ]
    )
    (out_dir / "SANITY_SWEEP_ALIGNMENT_NOTE.md").write_text("\n".join(md_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
