from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from generate_hfss_wide_manifest import (
    find_stage_root,
    kobs_from_filename,
    material_case_from_folder,
    rect_from_dir,
    theta_from_filename,
)
from geometry import load_geometry_config
from io_adapter import normalize_measurement_csv


def canonical_rect_dir_name(rect_dir_name: str) -> str:
    text = rect_dir_name.lower()
    if text.startswith("z_m"):
        return "z_m"
    if text.startswith("z_p"):
        return "z_p"
    raise ValueError(f"Unsupported rect directory name: {rect_dir_name}")


def build_manifest_row(case_dir: Path, rect_dir: Path, csv_path: Path) -> pd.Series:
    case_name, pol = material_case_from_folder(case_dir.name)
    return pd.Series(
        {
            "case": case_name,
            "pol": pol,
            "rect": rect_from_dir(rect_dir.name),
            "f_hz": np.nan,
            "theta_deg": theta_from_filename(csv_path.name),
            "field_type": "scattered",
            "observation_distance_lambda_scale": kobs_from_filename(csv_path.name),
            "run_label": csv_path.stem,
            "csv_path": csv_path.resolve(),
        }
    )


def serialize_complex_fields(frame: pd.DataFrame) -> pd.DataFrame:
    serialized = frame.copy()
    for axis in ["Ex", "Ey", "Ez"]:
        serialized[f"{axis}_real"] = serialized[axis].map(lambda value: complex(value).real)
        serialized[f"{axis}_imag"] = serialized[axis].map(lambda value: complex(value).imag)
    return serialized.drop(columns=["Ex", "Ey", "Ez"])


def merge_design_rect(case_dir: Path, rect_dir: Path, geom_path: Path) -> pd.DataFrame:
    geom = load_geometry_config(geom_path)
    frames: list[pd.DataFrame] = []
    canonical_rect = canonical_rect_dir_name(rect_dir.name)

    for csv_path in sorted(rect_dir.glob("*.csv")):
        manifest_row = build_manifest_row(case_dir, rect_dir, csv_path)
        normalized = normalize_measurement_csv(manifest_row, geom=geom)
        normalized.insert(0, "design_name", case_dir.name)
        normalized.insert(1, "source_rect_dir", rect_dir.name)
        normalized.insert(2, "canonical_rect_dir", canonical_rect)
        normalized.insert(3, "source_csv", csv_path.name)
        frames.append(serialize_complex_fields(normalized))

    if not frames:
        return pd.DataFrame()

    merged = pd.concat(frames, ignore_index=True)
    return merged.sort_values(
        [
            "theta_deg",
            "observation_distance_lambda_scale",
            "run_label",
            "point_id",
            "x",
            "y",
            "z",
        ]
    ).reset_index(drop=True)


def main() -> None:
    stage_root = find_stage_root(Path(__file__))
    parser = argparse.ArgumentParser(
        description="Merge HFSS design exports into one normalized z_m and one normalized z_p CSV per design."
    )
    parser.add_argument(
        "--input-root",
        type=Path,
        required=True,
        help="Root directory containing design folders such as 0.TE_PEC and 2.TM_concrete1.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=stage_root / "csv" / "merged" / "all_available_by_design",
        help="Directory where merged per-design files will be written.",
    )
    parser.add_argument(
        "--geometry-config",
        type=Path,
        default=stage_root / "config" / "geometry.yaml",
        help="Geometry config used by the wide-grid parser.",
    )
    args = parser.parse_args()

    input_root = args.input_root.resolve()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    index_rows: list[dict] = []

    for case_dir in sorted(path for path in input_root.iterdir() if path.is_dir()):
        design_output_dir = output_root / case_dir.name
        design_output_dir.mkdir(parents=True, exist_ok=True)

        for rect_dir in sorted(path for path in case_dir.iterdir() if path.is_dir()):
            merged = merge_design_rect(case_dir, rect_dir, args.geometry_config.resolve())
            if merged.empty:
                continue

            canonical_rect = canonical_rect_dir_name(rect_dir.name)
            output_path = design_output_dir / f"{case_dir.name}__{canonical_rect}.csv"
            merged.to_csv(output_path, index=False)

            index_rows.append(
                {
                    "design_name": case_dir.name,
                    "source_rect_dir": rect_dir.name,
                    "canonical_rect_dir": canonical_rect,
                    "output_csv": output_path,
                    "rows": len(merged),
                    "source_files": merged["run_label"].nunique(),
                    "theta_values": merged["theta_deg"].nunique(),
                    "kobs_values": merged["observation_distance_lambda_scale"].nunique(),
                }
            )

    index = pd.DataFrame(index_rows).sort_values(
        ["design_name", "canonical_rect_dir"]
    ).reset_index(drop=True)
    index_path = output_root / "index.csv"
    index.to_csv(index_path, index=False)

    print(f"Merged designs: {index['design_name'].nunique() if not index.empty else 0}")
    print(f"Output root:    {output_root}")
    print(f"Index path:     {index_path}")
    if not index.empty:
        print(index.to_string(index=False))


if __name__ == "__main__":
    main()
