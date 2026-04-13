from __future__ import annotations

import argparse
from pathlib import Path
import re

import pandas as pd


FILE_RE = re.compile(
    r"^(?P<design>\d+\.(?P<pol>TE|TM)_(?P<name>[A-Za-z0-9_]+))__"
    r"(?P<field_type>total|scattered)__"
    r"(?P<rect>z_[mp])__"
    r"theta_(?P<theta>[-+]?\d+(?:\.\d+)?)deg__"
    r"kobs_(?P<kobs>[-+]?\d+(?:\.\d+)?)__"
    r"freq_ALL\.csv$",
    re.IGNORECASE,
)


def find_stage_root(start: Path) -> Path:
    return start.resolve().parents[1]


def case_from_name(raw_name: str) -> str:
    name = re.sub(r"\d+$", "", raw_name.lower())
    case_map = {
        "pec": "pec",
        "baseline": "baseline",
        "concrete": "slab_concrete",
        "glass": "slab_glass",
        "wood": "slab_wood",
    }
    if name not in case_map:
        raise ValueError(f"Unsupported case name: {raw_name!r}")
    return case_map[name]


def rect_from_name(rect_name: str) -> str:
    rect_lower = rect_name.lower()
    if rect_lower == "z_m":
        return "refl_rect"
    if rect_lower == "z_p":
        return "trans_rect"
    raise ValueError(f"Unsupported rect name: {rect_name!r}")


def main() -> None:
    stage_root = find_stage_root(Path(__file__))
    parser = argparse.ArgumentParser(description="Generate a manifest from flat HFSS wide-grid CSV exports.")
    parser.add_argument("--input-dir", type=Path, required=True, help="Directory containing flat CSV exports.")
    parser.add_argument(
        "--output",
        type=Path,
        default=stage_root / "config" / "manifest_actual_new_runs_20260412.csv",
        help="Output manifest CSV path.",
    )
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    rows: list[dict] = []
    for csv_path in sorted(input_dir.glob("*.csv")):
        match = FILE_RE.match(csv_path.name)
        if not match:
            continue

        rows.append(
            {
                "case": case_from_name(match.group("name")),
                "pol": match.group("pol").upper(),
                "rect": rect_from_name(match.group("rect")),
                "f_hz": "",
                "theta_deg": float(match.group("theta")),
                "field_type": match.group("field_type").lower(),
                "observation_distance_lambda_scale": float(match.group("kobs")),
                "csv_path": csv_path.resolve().relative_to(stage_root).as_posix(),
            }
        )

    manifest = pd.DataFrame(rows).sort_values(
        ["case", "pol", "rect", "theta_deg", "observation_distance_lambda_scale", "field_type", "csv_path"]
    ).reset_index(drop=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(args.output, index=False)

    print(f"Manifest rows: {len(manifest)}")
    print(f"Input dir:      {input_dir}")
    print(f"Output path:    {args.output}")


if __name__ == "__main__":
    main()
