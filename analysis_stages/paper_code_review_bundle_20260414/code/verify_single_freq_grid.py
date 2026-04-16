from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


MATERIALS = ["concrete", "glass", "wood"]
VALID_MAX = {"concrete": 55.0, "glass": 60.0, "wood": 45.0}
REQUESTED_FREQS_GHZ = [5.0, 6.5, 8.0]
BAND_REFERENCE_FREQ_GHZ = 6.5


def default_linear_truth_path(bundle_root: Path) -> Path:
    candidates = [
        bundle_root / "data" / "stage_1_multifreq_20260416" / "truth_table_linear_locked.csv",
        bundle_root / "data" / "stage_1" / "truth_table_linear_locked.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def default_cp_truth_path(bundle_root: Path) -> Path:
    candidates = [
        bundle_root
        / "data"
        / "stage_2_multifreq_20260416"
        / "sameflip_alias_20260416"
        / "truth_table_cp_shared_common_sameflip.csv",
        bundle_root / "data" / "stage_2" / "sameflip_alias_20260415" / "truth_table_cp_shared_common_sameflip.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def build_argparser() -> argparse.ArgumentParser:
    bundle_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description=(
            "Replay the residual ordering grid at three single-frequency points "
            "using the existing Stage 3 frequency-resolved exports."
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
        "--patch-cp-band",
        type=Path,
        default=bundle_root / "data" / "stage_3" / "cp" / "patch_cp_extracted.csv",
    )
    parser.add_argument(
        "--patch-lp-band",
        type=Path,
        default=bundle_root / "data" / "stage_3" / "lp" / "patch_lp_extracted.csv",
    )
    parser.add_argument(
        "--linear-truth",
        type=Path,
        default=default_linear_truth_path(bundle_root),
    )
    parser.add_argument(
        "--cp-truth",
        type=Path,
        default=default_cp_truth_path(bundle_root),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=bundle_root / "results" / "debug",
    )
    return parser


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y", "t"}


def db20_ratio(num: pd.Series, den: pd.Series) -> pd.Series:
    return 20.0 * np.log10(num.clip(lower=1e-12) / den.clip(lower=1e-12))


def build_main_range_ideal_grid(linear_truth: pd.DataFrame, cp_truth: pd.DataFrame) -> pd.DataFrame:
    linear = linear_truth[linear_truth["material"].isin(MATERIALS)].copy()
    cp = cp_truth[cp_truth["material"].isin(MATERIALS)].copy()

    linear["use_for_main_claim_TE"] = linear["use_for_main_claim_TE"].map(parse_bool)
    linear["use_for_main_claim_TM"] = linear["use_for_main_claim_TM"].map(parse_bool)
    cp["cp_use_for_main_claim"] = cp["cp_use_for_main_claim"].map(parse_bool)
    linear["freq_ghz"] = pd.to_numeric(linear["f_hz"], errors="coerce") / 1e9
    cp["freq_ghz"] = pd.to_numeric(cp["f_hz"], errors="coerce") / 1e9

    linear_keep = linear[
        ["material", "theta_deg", "f_hz", "freq_ghz", "R_TE_mag", "R_TM_mag", "use_for_main_claim_TE", "use_for_main_claim_TM"]
    ].copy()
    linear_keep["B_mag"] = linear_keep[["R_TE_mag", "R_TM_mag"]].max(axis=1)
    cp_keep = cp[["material", "theta_deg", "f_hz", "freq_ghz", "Gamma_same_mag", "cp_use_for_main_claim"]].copy()

    ideal = linear_keep.merge(cp_keep, on=["material", "theta_deg", "f_hz", "freq_ghz"], how="inner")
    ideal["use_for_main_claim"] = ideal.apply(
        lambda row: row["use_for_main_claim_TE"]
        and row["use_for_main_claim_TM"]
        and row["cp_use_for_main_claim"]
        and float(row["theta_deg"]) >= 20.0
        and float(row["theta_deg"]) <= VALID_MAX[str(row["material"])],
        axis=1,
    )
    ideal = ideal[ideal["use_for_main_claim"]].copy()
    ideal = ideal.rename(columns={"Gamma_same_mag": "gamma_x_ideal_mag"})
    return ideal[["material", "theta_deg", "f_hz", "freq_ghz", "B_mag", "gamma_x_ideal_mag"]].sort_values(
        ["freq_ghz", "material", "theta_deg"]
    ).reset_index(drop=True)


def select_replay_frequencies(freq_values: np.ndarray, ideal_freq_values: np.ndarray) -> pd.DataFrame:
    unique_freq = np.array(sorted(np.unique(freq_values.astype(float))))
    unique_ideal_freq = np.array(sorted(np.unique(ideal_freq_values.astype(float))))
    selected = []
    for target in REQUESTED_FREQS_GHZ:
        idx = int(np.argmin(np.abs(unique_freq - target)))
        actual = float(unique_freq[idx])
        ideal_match_available = bool(np.isclose(unique_ideal_freq, actual, atol=1e-9, rtol=0.0).any())
        selected.append({"requested_freq_ghz": float(target), "actual_freq_ghz": actual})

    mapping = pd.DataFrame(selected)
    mapping["selector_label"] = ["lower_band_edge", "center_near_6p5", "upper_band_edge"]
    mapping["ideal_match_available_in_bundle"] = [
        bool(np.isclose(unique_ideal_freq, actual_freq, atol=1e-9, rtol=0.0).any())
        for actual_freq in mapping["actual_freq_ghz"]
    ]
    mapping["selection_note"] = mapping.apply(
        lambda row: (
            "Matched to same-frequency Stage 1/2 ideal truth."
            if row["ideal_match_available_in_bundle"]
            else "Mapped from requested out-of-band target to the nearest in-band edge; no same-frequency Stage 1/2 ideal truth is available in the current inputs."
        ),
        axis=1,
    )
    return mapping


def build_band_baseline(
    ideal_grid: pd.DataFrame,
    patch_cp_band: pd.DataFrame,
    patch_lp_band: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int], float]:
    available_freqs = np.array(sorted(ideal_grid["freq_ghz"].dropna().unique()))
    reference_idx = int(np.argmin(np.abs(available_freqs - BAND_REFERENCE_FREQ_GHZ)))
    reference_freq_ghz = float(available_freqs[reference_idx])
    ideal_main = ideal_grid[np.isclose(ideal_grid["freq_ghz"], reference_freq_ghz, atol=1e-9, rtol=0.0)].copy()

    band = (
        ideal_main.merge(
            patch_cp_band[["material", "theta_deg", "gamma_hat_c_cp_raw_mag", "gamma_hat_c_cp_eff_mag"]],
            on=["material", "theta_deg"],
            how="inner",
        )
        .merge(
            patch_lp_band[["material", "theta_deg", "gamma_x_from_lp_mag"]],
            on=["material", "theta_deg"],
            how="inner",
        )
        .sort_values(["material", "theta_deg"])
        .reset_index(drop=True)
    )
    band["raw_below_ideal_flag"] = band["gamma_hat_c_cp_raw_mag"] < band["gamma_x_ideal_mag"]
    band["eff_below_ideal_flag"] = band["gamma_hat_c_cp_eff_mag"] < band["gamma_x_ideal_mag"]
    band["lp_below_ideal_flag"] = band["gamma_x_from_lp_mag"] < band["gamma_x_ideal_mag"]
    return (
        band,
        {
            "raw": int(band["raw_below_ideal_flag"].sum()),
            "eff": int(band["eff_below_ideal_flag"].sum()),
            "lp": int(band["lp_below_ideal_flag"].sum()),
        },
        reference_freq_ghz,
    )


def build_single_frequency_rows(
    ideal_grid: pd.DataFrame,
    patch_cp_freq: pd.DataFrame,
    patch_lp_freq: pd.DataFrame,
    selected_freqs: pd.DataFrame,
) -> pd.DataFrame:
    keep_cp = patch_cp_freq[
        ["material", "theta_deg", "freq_ghz", "gamma_hat_c_cp_raw_mag", "gamma_hat_c_cp_eff_mag", "gamma_hat_x_cp_sys_mag"]
    ].copy()
    keep_lp = patch_lp_freq[
        ["material", "theta_deg", "freq_ghz", "gamma_x_from_lp_mag", "gamma_c_from_lp_mag"]
    ].copy()

    rows: list[pd.DataFrame] = []
    for _, freq_row in selected_freqs.iterrows():
        actual_freq = float(freq_row["actual_freq_ghz"])
        cp_sub = keep_cp[np.isclose(keep_cp["freq_ghz"], actual_freq)].copy()
        lp_sub = keep_lp[np.isclose(keep_lp["freq_ghz"], actual_freq)].copy()
        ideal_sub = ideal_grid[np.isclose(ideal_grid["freq_ghz"], actual_freq, atol=1e-9, rtol=0.0)].copy()
        merged = (
            ideal_sub.merge(cp_sub, on=["material", "theta_deg", "freq_ghz"], how="left")
            .merge(lp_sub, on=["material", "theta_deg", "freq_ghz"], how="left")
            .sort_values(["material", "theta_deg"])
            .reset_index(drop=True)
        )
        merged["requested_freq_ghz"] = float(freq_row["requested_freq_ghz"])
        merged["actual_freq_ghz"] = actual_freq
        merged["selector_label"] = str(freq_row["selector_label"])
        merged["ideal_match_available_in_bundle"] = bool(freq_row["ideal_match_available_in_bundle"])
        merged["selection_note"] = str(freq_row["selection_note"])
        merged["raw_below_ideal_flag"] = merged["gamma_hat_c_cp_raw_mag"] < merged["gamma_x_ideal_mag"]
        merged["eff_below_ideal_flag"] = merged["gamma_hat_c_cp_eff_mag"] < merged["gamma_x_ideal_mag"]
        merged["lp_below_ideal_flag"] = merged["gamma_x_from_lp_mag"] < merged["gamma_x_ideal_mag"]

        if bool(freq_row["ideal_match_available_in_bundle"]):
            merged["G_ideal_db"] = db20_ratio(merged["B_mag"], merged["gamma_x_ideal_mag"])
            merged["G_patch_raw_db"] = db20_ratio(merged["B_mag"], merged["gamma_hat_c_cp_raw_mag"])
            merged["G_patch_eff_db"] = db20_ratio(merged["B_mag"], merged["gamma_hat_c_cp_eff_mag"])
            merged["G_lp_db"] = db20_ratio(merged["B_mag"], merged["gamma_x_from_lp_mag"])
            merged["Delta_ideal_minus_raw_db"] = merged["G_ideal_db"] - merged["G_patch_raw_db"]
            merged["Delta_ideal_minus_eff_db"] = merged["G_ideal_db"] - merged["G_patch_eff_db"]
            merged["Delta_ideal_minus_lp_db"] = merged["G_ideal_db"] - merged["G_lp_db"]
        else:
            merged["G_ideal_db"] = np.nan
            merged["G_patch_raw_db"] = np.nan
            merged["G_patch_eff_db"] = np.nan
            merged["G_lp_db"] = np.nan
            merged["Delta_ideal_minus_raw_db"] = np.nan
            merged["Delta_ideal_minus_eff_db"] = np.nan
            merged["Delta_ideal_minus_lp_db"] = np.nan

        rows.append(merged)

    return pd.concat(rows, ignore_index=True)


def summarize_single_frequency(
    single_df: pd.DataFrame,
    selected_freqs: pd.DataFrame,
    band_counts: dict[str, int],
) -> pd.DataFrame:
    summary_rows = []
    for _, freq_row in selected_freqs.iterrows():
        actual_freq = float(freq_row["actual_freq_ghz"])
        sub = single_df[np.isclose(single_df["actual_freq_ghz"], actual_freq)].copy()
        ideal_match = bool(freq_row["ideal_match_available_in_bundle"])
        summary_rows.append(
            {
                "requested_freq_ghz": float(freq_row["requested_freq_ghz"]),
                "actual_freq_ghz": actual_freq,
                "selector_label": str(freq_row["selector_label"]),
                "ideal_match_available_in_bundle": ideal_match,
                "n_rows": int(len(sub)),
                "raw_below_ideal_rows": int(sub["raw_below_ideal_flag"].sum()) if ideal_match else np.nan,
                "eff_below_ideal_rows": int(sub["eff_below_ideal_flag"].sum()) if ideal_match else np.nan,
                "lp_below_ideal_rows": int(sub["lp_below_ideal_flag"].sum()) if ideal_match else np.nan,
                "band_raw_below_ideal_rows": int(band_counts["raw"]) if ideal_match else np.nan,
                "band_eff_below_ideal_rows": int(band_counts["eff"]) if ideal_match else np.nan,
                "band_lp_below_ideal_rows": int(band_counts["lp"]) if ideal_match else np.nan,
                "pass_criterion_all_zero": bool(
                    ideal_match
                    and int(sub["raw_below_ideal_flag"].sum()) == 0
                    and int(sub["eff_below_ideal_flag"].sum()) == 0
                    and int(sub["lp_below_ideal_flag"].sum()) == 0
                ),
                "selection_note": str(freq_row["selection_note"]),
            }
        )
    return pd.DataFrame(summary_rows)


def write_summary_md(
    *,
    mapping_df: pd.DataFrame,
    band_counts: dict[str, int],
    band_reference_freq_ghz: float,
    ideal_freqs_ghz: list[float],
    summary_df: pd.DataFrame,
    single_df: pd.DataFrame,
    mapping_path: Path,
    full_path: Path,
    summary_path: Path,
    output_path: Path,
    repo_root: Path,
) -> None:
    center_row = summary_df[np.isclose(summary_df["actual_freq_ghz"], BAND_REFERENCE_FREQ_GHZ, atol=1e-9, rtol=0.0)].iloc[0]
    top_eff_rows = single_df[
        np.isclose(single_df["actual_freq_ghz"], BAND_REFERENCE_FREQ_GHZ, atol=1e-9, rtol=0.0)
        & single_df["eff_below_ideal_flag"]
    ][["material", "theta_deg", "gamma_x_ideal_mag", "gamma_hat_c_cp_eff_mag", "Delta_ideal_minus_eff_db"]].copy()

    md_lines = [
        "# Verify Single-Frequency Residual Grid",
        "",
        "Execution date: `2026-04-16`",
        "",
        "## Scope",
        "",
        "- Requested grid points: `5.0 / 6.5 / 8.0 GHz`.",
        "- Current Stage 3 frequency-resolved bundle spans `6.24 GHz` to `6.74 GHz`.",
        "- Replay therefore uses the nearest in-band points: `6.24 / 6.50 / 6.74 GHz`.",
        f"- Stage 1 and Stage 2 ideal truth tables are currently available at: `{', '.join(f'{freq:.2f} GHz' for freq in ideal_freqs_ghz)}`.",
        f"- Band-average baseline stays anchored to the nearest available ideal reference at `{band_reference_freq_ghz:.2f} GHz`.",
        "",
        "## Frequency Mapping",
        "",
    ]

    for _, row in mapping_df.iterrows():
        md_lines.append(
            f"- requested `{row['requested_freq_ghz']:.2f} GHz` -> actual `{row['actual_freq_ghz']:.2f} GHz` "
            f"({row['selector_label']}), ideal-match-available={bool(row['ideal_match_available_in_bundle'])}"
        )

    md_lines.extend(
        [
            "",
            "## Per-Frequency Replay",
            "",
        ]
    )
    for _, row in summary_df.iterrows():
        if bool(row["ideal_match_available_in_bundle"]):
            md_lines.append(
                f"- `{row['actual_freq_ghz']:.2f} GHz`: raw=`{int(row['raw_below_ideal_rows'])}`, "
                f"eff=`{int(row['eff_below_ideal_rows'])}`, LP=`{int(row['lp_below_ideal_rows'])}`, "
                f"all-zero-pass=`{bool(row['pass_criterion_all_zero'])}`"
            )
        else:
            md_lines.append(
                f"- `{row['actual_freq_ghz']:.2f} GHz`: no same-frequency ideal truth available."
            )

    md_lines.extend(
        [
            "",
            "## Band-Average Baseline",
            "",
            f"- main-range raw ordering violations: `{band_counts['raw']}`",
            f"- main-range eff ordering violations: `{band_counts['eff']}`",
            f"- main-range LP ordering violations: `{band_counts['lp']}`",
            "",
            "## 6.50 GHz Replay",
            "",
            f"- raw ordering violations: `{int(center_row['raw_below_ideal_rows'])}`",
            f"- eff ordering violations: `{int(center_row['eff_below_ideal_rows'])}`",
            f"- LP ordering violations: `{int(center_row['lp_below_ideal_rows'])}`",
            f"- pass criterion met: `{bool(center_row['pass_criterion_all_zero'])}`",
            "",
            "## Interpretation",
            "",
        ]
    )

    if bool(center_row["pass_criterion_all_zero"]):
        md_lines.append("- At 6.50 GHz the ordering violations collapse to zero, so band averaging is sufficient to explain the Stage 4 violation pattern.")
    else:
        md_lines.append(
            "- At 6.50 GHz the ordering violations do not collapse to zero, so band averaging alone is not sufficient to explain the Stage 4 violation pattern."
        )
        md_lines.append(
            f"- In particular, the eff path remains at `{int(center_row['eff_below_ideal_rows'])}` violation row(s), compared with the band-mean baseline `{int(center_row['band_eff_below_ideal_rows'])}`."
        )

    md_lines.extend(
        [
            "",
            "## 6.50 GHz Eff Violations",
            "",
        ]
    )

    if top_eff_rows.empty:
        md_lines.append("- None.")
    else:
        for _, row in top_eff_rows.iterrows():
            md_lines.append(
                f"- {row['material']} {row['theta_deg']:.0f} deg: "
                f"ideal={row['gamma_x_ideal_mag']:.6f}, "
                f"eff={row['gamma_hat_c_cp_eff_mag']:.6f}, "
                f"Delta(ideal-eff)={row['Delta_ideal_minus_eff_db']:.2f} dB"
            )

    md_lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Frequency mapping CSV: `{mapping_path.relative_to(repo_root)}`",
            f"- Full replay CSV: `{full_path.relative_to(repo_root)}`",
            f"- Summary CSV: `{summary_path.relative_to(repo_root)}`",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_argparser().parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[3]

    patch_cp_freq = pd.read_csv(args.patch_cp_freq)
    patch_lp_freq = pd.read_csv(args.patch_lp_freq)
    patch_cp_band = pd.read_csv(args.patch_cp_band)
    patch_lp_band = pd.read_csv(args.patch_lp_band)
    linear_truth = pd.read_csv(args.linear_truth)
    cp_truth = pd.read_csv(args.cp_truth)

    ideal_grid = build_main_range_ideal_grid(linear_truth, cp_truth)
    selected_freqs = select_replay_frequencies(
        patch_cp_freq["freq_ghz"].to_numpy(dtype=float),
        ideal_grid["freq_ghz"].to_numpy(dtype=float),
    )
    _, band_counts, band_reference_freq_ghz = build_band_baseline(ideal_grid, patch_cp_band, patch_lp_band)
    single_df = build_single_frequency_rows(ideal_grid, patch_cp_freq, patch_lp_freq, selected_freqs)
    summary_df = summarize_single_frequency(single_df, selected_freqs, band_counts)

    mapping_path = output_dir / "verify_single_freq_grid_mapping.csv"
    full_path = output_dir / "verify_single_freq_grid_full.csv"
    summary_path = output_dir / "verify_single_freq_grid_summary.csv"
    md_path = output_dir / "VERIFY_SINGLE_FREQ_GRID.md"

    selected_freqs.to_csv(mapping_path, index=False)
    single_df.to_csv(full_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    write_summary_md(
        mapping_df=selected_freqs,
        band_counts=band_counts,
        band_reference_freq_ghz=band_reference_freq_ghz,
        ideal_freqs_ghz=sorted(float(freq) for freq in ideal_grid["freq_ghz"].dropna().unique()),
        summary_df=summary_df,
        single_df=single_df,
        mapping_path=mapping_path,
        full_path=full_path,
        summary_path=summary_path,
        output_path=md_path,
        repo_root=repo_root,
    )

    print(f"Wrote {mapping_path}")
    print(f"Wrote {full_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
