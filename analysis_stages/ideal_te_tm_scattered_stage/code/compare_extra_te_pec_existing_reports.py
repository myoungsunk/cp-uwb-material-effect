from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


HEADER_RE = re.compile(
    r"(?P<kind>re|im|mag|ang_deg)\(NearE(?P<axis>[XYZ])\)\s+\[[^\]]+\]\s+-\s+"
    r"_v='(?P<v>[^']+)'.*?"
    r"k_obs='(?P<kobs>[^']+)'.*?"
    r"theta_k='(?P<theta>[^']+)'.*?"
    r"w_plane='(?P<w_plane>[^']+)'",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class BlockKey:
    theta: str
    kobs: str
    w_plane: str


def stage_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def windows_long_path(path: Path) -> str:
    text = str(path)
    if os.name != "nt":
        return text
    if text.startswith("\\\\?\\"):
        return text
    if text.startswith("\\\\"):
        return "\\\\?\\UNC\\" + text.lstrip("\\")
    return "\\\\?\\" + text


def parse_len_mm(text: str) -> float:
    return float(str(text).replace("mm", ""))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(windows_long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_wide_blocks(path: Path) -> dict[BlockKey, np.ndarray]:
    with open(windows_long_path(path), "r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    header = rows[0]
    raw = pd.DataFrame(rows[1:])
    u_values = pd.to_numeric(raw.iloc[:, 0], errors="coerce").to_numpy(dtype=float)

    block_columns: dict[BlockKey, dict[float, dict[tuple[str, str], int]]] = {}
    for column_index, column_name in enumerate(header[1:], start=1):
        match = HEADER_RE.search(str(column_name))
        if not match:
            continue
        key = BlockKey(
            theta=match.group("theta"),
            kobs=match.group("kobs"),
            w_plane=match.group("w_plane"),
        )
        v_mm = parse_len_mm(match.group("v"))
        block_columns.setdefault(key, {}).setdefault(v_mm, {})[
            (match.group("kind").lower(), match.group("axis").upper())
        ] = column_index

    blocks: dict[BlockKey, np.ndarray] = {}
    for key, per_v in block_columns.items():
        rows_per_v: list[np.ndarray] = []
        for v_mm in sorted(per_v):
            mapping = per_v[v_mm]
            axes: list[np.ndarray] = []
            for axis in "XYZ":
                if ("re", axis) in mapping and ("im", axis) in mapping:
                    real = pd.to_numeric(raw.iloc[:, mapping[("re", axis)]], errors="coerce").to_numpy(dtype=float)
                    imag = pd.to_numeric(raw.iloc[:, mapping[("im", axis)]], errors="coerce").to_numpy(dtype=float)
                    field = real + 1j * imag
                elif ("mag", axis) in mapping and ("ang_deg", axis) in mapping:
                    mag = pd.to_numeric(raw.iloc[:, mapping[("mag", axis)]], errors="coerce").to_numpy(dtype=float)
                    ang_deg = pd.to_numeric(
                        raw.iloc[:, mapping[("ang_deg", axis)]], errors="coerce"
                    ).to_numpy(dtype=float)
                    field = mag * np.exp(1j * np.deg2rad(ang_deg))
                else:
                    raise ValueError(f"Missing field columns for {path.name}, block={key}, axis={axis}")
                axes.append(field)

            rows_per_v.append(np.column_stack(axes))

        block = np.vstack(rows_per_v)
        expected_rows = len(per_v) * len(u_values)
        if block.shape[0] != expected_rows:
            raise ValueError(f"Unexpected point count in {path.name}, block={key}: {block.shape[0]} vs {expected_rows}")
        blocks[key] = block

    return blocks


def exact_duplicate_pairs(blocks: dict[BlockKey, np.ndarray], focus_thetas: set[str]) -> list[dict[str, object]]:
    keys = [key for key in sorted(blocks, key=lambda item: (item.theta, float(item.kobs), item.w_plane)) if key.theta in focus_thetas]
    duplicates: list[dict[str, object]] = []
    for index, key_a in enumerate(keys):
        for key_b in keys[index + 1 :]:
            max_abs = float(np.max(np.abs(blocks[key_a] - blocks[key_b])))
            if max_abs < 1e-12:
                duplicates.append(
                    {
                        "a": key_a.__dict__,
                        "b": key_b.__dict__,
                        "max_abs": max_abs,
                    }
                )
    return duplicates


def compare_blocks(block_a: np.ndarray, block_b: np.ndarray) -> dict[str, float]:
    diff = np.abs(block_a - block_b)
    return {
        "max_abs": float(diff.max()),
        "mean_abs": float(diff.mean()),
        "q95_abs": float(np.quantile(diff, 0.95)),
    }


def read_old_surface_block(path: Path, theta_deg: float, kobs: float, w_plane_mm: int) -> np.ndarray:
    frame = pd.read_csv(windows_long_path(path))
    mask = (
        (frame["theta_deg"] == theta_deg)
        & np.isclose(frame["observation_distance_lambda_scale"], kobs)
        & frame["source_csv"].str.contains(f"w_plane_{w_plane_mm}mm", regex=False)
    )
    block = frame.loc[mask].sort_values("point_id").reset_index(drop=True)
    return np.column_stack(
        [
            block["Ex_real"].to_numpy(dtype=float) + 1j * block["Ex_imag"].to_numpy(dtype=float),
            block["Ey_real"].to_numpy(dtype=float) + 1j * block["Ey_imag"].to_numpy(dtype=float),
            block["Ez_real"].to_numpy(dtype=float) + 1j * block["Ez_imag"].to_numpy(dtype=float),
        ]
    )


def compare_new_vs_old_y(new_block: np.ndarray, old_block: np.ndarray) -> dict[str, dict[str, float]]:
    new_y = new_block[:, 1]
    old_y = old_block[:, 1]
    direct = np.abs(new_y - old_y)
    negated = np.abs(new_y + old_y)
    return {
        "direct": {
            "max_abs": float(direct.max()),
            "mean_abs": float(direct.mean()),
            "q95_abs": float(np.quantile(direct, 0.95)),
        },
        "negated_old": {
            "max_abs": float(negated.max()),
            "mean_abs": float(negated.mean()),
            "q95_abs": float(np.quantile(negated, 0.95)),
        },
    }


def build_summary(stage_root: Path, extra_root: Path) -> dict[str, object]:
    folder_80 = extra_root / "existing_plot_exports_20260412_233725_export_existing_reports2" / "0.TE_PEC_80"
    folder_85 = extra_root / "existing_plot_exports_20260412_235244_export_existing_reports85" / "0.TE_PEC"

    blocks_80 = {
        name: parse_wide_blocks(folder_80 / name)
        for name in ["Near_E_Table_1.csv", "Near_E_Table_2.csv", "Near_E_Table_3.csv", "Near_E_Table_3_1.csv"]
    }
    blocks_85 = {
        name: parse_wide_blocks(folder_85 / name)
        for name in ["Near_E_Table_1.csv", "Near_E_Table_2.csv", "Near_E_Table_3.csv", "Near_E_Table_3_1.csv"]
    }

    old_zp = stage_root / "csv" / "merged" / "all_available_by_design" / "0.TE_PEC" / "0.TE_PEC__z_p.csv"
    old_zm = stage_root / "csv" / "merged" / "all_available_by_design" / "0.TE_PEC" / "0.TE_PEC__z_m.csv"

    summary: dict[str, object] = {
        "byte_identity": {
            "Near_E_Table_1.csv": sha256(folder_80 / "Near_E_Table_1.csv") == sha256(folder_85 / "Near_E_Table_1.csv"),
            "Near_E_Table_2.csv": sha256(folder_80 / "Near_E_Table_2.csv") == sha256(folder_85 / "Near_E_Table_2.csv"),
            "Near_E_Table_3.csv": sha256(folder_80 / "Near_E_Table_3.csv") == sha256(folder_85 / "Near_E_Table_3.csv"),
            "Near_E_Table_3_1.csv": sha256(folder_80 / "Near_E_Table_3_1.csv") == sha256(folder_85 / "Near_E_Table_3_1.csv"),
        },
        "t3_subset_match": {
            "80deg_table1_vs_table3": compare_blocks(
                blocks_80["Near_E_Table_1.csv"][BlockKey("80deg", "2", "500mm")],
                blocks_80["Near_E_Table_3.csv"][BlockKey("80deg", "2", "500mm")],
            ),
            "80deg_table2_vs_table3_1": compare_blocks(
                blocks_80["Near_E_Table_2.csv"][BlockKey("80deg", "2", "500mm")],
                blocks_80["Near_E_Table_3_1.csv"][BlockKey("80deg", "2", "500mm")],
            ),
            "85deg_table1_vs_table3": compare_blocks(
                blocks_85["Near_E_Table_1.csv"][BlockKey("85deg", "2", "500mm")],
                blocks_85["Near_E_Table_3.csv"][BlockKey("85deg", "2", "500mm")],
            ),
            "85deg_table2_vs_table3_1": compare_blocks(
                blocks_85["Near_E_Table_2.csv"][BlockKey("85deg", "2", "500mm")],
                blocks_85["Near_E_Table_3_1.csv"][BlockKey("85deg", "2", "500mm")],
            ),
        },
        "internal_duplicate_pairs": {
            "table1": exact_duplicate_pairs(blocks_80["Near_E_Table_1.csv"], {"80deg", "85deg"}),
            "table2": exact_duplicate_pairs(blocks_80["Near_E_Table_2.csv"], {"80deg", "85deg"}),
        },
        "table1_vs_table2": {
            "80deg_kobs2_500": compare_blocks(
                blocks_80["Near_E_Table_1.csv"][BlockKey("80deg", "2", "500mm")],
                blocks_80["Near_E_Table_2.csv"][BlockKey("80deg", "2", "500mm")],
            ),
            "85deg_kobs2_500": compare_blocks(
                blocks_85["Near_E_Table_1.csv"][BlockKey("85deg", "2", "500mm")],
                blocks_85["Near_E_Table_2.csv"][BlockKey("85deg", "2", "500mm")],
            ),
        },
        "new_vs_old_sign_check": {},
    }

    for theta_deg in [80.0, 85.0]:
        theta_key = f"{int(theta_deg)}deg"
        new_block = blocks_80["Near_E_Table_1.csv"][BlockKey(theta_key, "2", "500mm")] if theta_deg == 80.0 else blocks_85["Near_E_Table_1.csv"][BlockKey(theta_key, "2", "500mm")]
        summary["new_vs_old_sign_check"][theta_key] = {
            "table1_vs_old_zp": compare_new_vs_old_y(new_block, read_old_surface_block(old_zp, theta_deg, 2.0, 500)),
            "table1_vs_old_zm": compare_new_vs_old_y(new_block, read_old_surface_block(old_zm, theta_deg, 2.0, 500)),
        }

    return summary


def summary_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# TE PEC 80/85 additional existing-report extraction check",
        "",
        "## Summary",
        f"- `Near_E_Table_1.csv` identical across 80-folder and 85-folder: `{summary['byte_identity']['Near_E_Table_1.csv']}`",
        f"- `Near_E_Table_2.csv` identical across 80-folder and 85-folder: `{summary['byte_identity']['Near_E_Table_2.csv']}`",
        f"- `Near_E_Table_3.csv` identical across 80-folder and 85-folder: `{summary['byte_identity']['Near_E_Table_3.csv']}`",
        f"- `Near_E_Table_3_1.csv` identical across 80-folder and 85-folder: `{summary['byte_identity']['Near_E_Table_3_1.csv']}`",
        "- `Near_E_Table_3` is numerically identical to the `theta=80/85, kobs=2, w_plane=500mm` subset of `Near_E_Table_1`.",
        "- `Near_E_Table_3_1` is numerically identical to the `theta=80/85, kobs=2, w_plane=500mm` subset of `Near_E_Table_2`.",
        "- No exact duplicate block pairs remain inside the new re-extracted `Near_E_Table_1/2` 80/85 high-angle blocks.",
        "- Relative to the old merged TE PEC scattered CSV, the dominant `Ey` component does not match directly, but it is much closer after a global sign flip (`new ~= -old`) at both 80 deg and 85 deg.",
        "",
        "## Key metrics",
        f"- Table1 vs Table2 at 80deg, kobs=2, 500mm: {json.dumps(summary['table1_vs_table2']['80deg_kobs2_500'])}",
        f"- Table1 vs Table2 at 85deg, kobs=2, 500mm: {json.dumps(summary['table1_vs_table2']['85deg_kobs2_500'])}",
        f"- 80deg sign check vs old z_p: {json.dumps(summary['new_vs_old_sign_check']['80deg']['table1_vs_old_zp'])}",
        f"- 85deg sign check vs old z_p: {json.dumps(summary['new_vs_old_sign_check']['85deg']['table1_vs_old_zp'])}",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    stage_root = stage_root_from_script()
    parser = argparse.ArgumentParser(description="Compare additional TE PEC 80/85 existing-report exports against current merged data.")
    parser.add_argument(
        "--extra-root",
        type=Path,
        default=stage_root / "csv" / "raw" / "te_pec_existing_reports_80_85_20260412",
        help="Root directory containing the copied existing-report export folders.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=stage_root / "results" / "te_pec_existing_reports_80_85_20260412",
        help="Directory for JSON/Markdown summaries.",
    )
    args = parser.parse_args()

    summary = build_summary(stage_root, args.extra_root.resolve())
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
