from __future__ import annotations

import argparse
from pathlib import Path
import re

import pandas as pd


FOLDER_RE = re.compile(r"^\d+\.(?P<pol>TE|TM)_(?P<name>[A-Za-z0-9_]+)$", re.IGNORECASE)
THETA_RE = re.compile(r"__theta(?:_k)?_(?P<theta>[-+]?\d+(?:\.\d+)?)deg(?:__|\.|$)", re.IGNORECASE)
KOBS_RE = re.compile(r"__k_obs_(?P<kobs>[-+]?\d+(?:\.\d+)?)(?:__|\.|$)", re.IGNORECASE)


def find_stage_root(start: Path) -> Path:
    return start.resolve().parents[1]


def manifest_csv_path(csv_path: Path, stage_root: Path) -> str:
    resolved = csv_path.resolve()
    try:
        return resolved.relative_to(stage_root).as_posix()
    except ValueError:
        return resolved.as_posix()


def run_label_from_filename(filename: str) -> str:
    stem = re.sub(r"__z_[mp]__", "__", Path(filename).stem, flags=re.IGNORECASE)
    match = re.match(r"^(?P<index>\d+)\.(?:TE|TM)_(?P<name>[A-Za-z0-9_]+)(?P<rest>.*)$", stem, re.IGNORECASE)
    if match is None:
        return stem
    return f"{match.group('index')}.{match.group('name')}{match.group('rest')}"


def material_case_from_folder(folder_name: str) -> tuple[str, str]:
    match = FOLDER_RE.match(folder_name)
    if not match:
        raise ValueError(f"Unrecognized HFSS export folder name: {folder_name}")

    pol = match.group("pol").upper()
    raw_name = re.sub(r"\d+$", "", match.group("name").lower())
    case_map = {
        "pec": "pec",
        "baseline": "baseline",
        "concrete": "slab_concrete",
        "glass": "slab_glass",
        "wood": "slab_wood",
    }
    if raw_name not in case_map:
        raise ValueError(f"Unsupported material name parsed from folder {folder_name!r}: {raw_name!r}")
    return case_map[raw_name], pol


def rect_from_dir(rect_dir: str) -> str:
    rect_name = rect_dir.lower()
    if rect_name.startswith("z_m"):
        return "refl_rect"
    if rect_name.startswith("z_p"):
        return "trans_rect"
    raise ValueError(f"Unsupported rect directory name: {rect_dir}")


def theta_from_filename(filename: str) -> float:
    match = THETA_RE.search(filename)
    if not match:
        raise ValueError(f"Could not parse theta from filename: {filename}")
    return float(match.group("theta"))


def kobs_from_filename(filename: str) -> float | None:
    match = KOBS_RE.search(filename)
    if not match:
        return None
    return float(match.group("kobs"))


def main() -> None:
    stage_root = find_stage_root(Path(__file__))
    parser = argparse.ArgumentParser(description="Generate an ideal-stage manifest from HFSS wide-grid exports.")
    parser.add_argument(
        "--input-root",
        type=Path,
        required=True,
        help="Root directory containing case folders like 0.TE_PEC / 2.TM_concrete1.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=stage_root / "config" / "manifest_actual_center5x5.csv",
        help="Output manifest CSV path.",
    )
    args = parser.parse_args()

    input_root = args.input_root.resolve()
    rows: list[dict] = []
    for case_dir in sorted(path for path in input_root.iterdir() if path.is_dir()):
        if not FOLDER_RE.match(case_dir.name):
            continue
        case_name, pol = material_case_from_folder(case_dir.name)
        for rect_dir in sorted(path for path in case_dir.iterdir() if path.is_dir()):
            rect = rect_from_dir(rect_dir.name)
            for csv_path in sorted(rect_dir.glob("*.csv")):
                rows.append(
                    {
                        "case": case_name,
                        "pol": pol,
                        "rect": rect,
                        "f_hz": "",
                        "theta_deg": theta_from_filename(csv_path.name),
                        "field_type": "scattered",
                        "observation_distance_lambda_scale": kobs_from_filename(csv_path.name),
                        "run_label": run_label_from_filename(csv_path.name),
                        "csv_path": manifest_csv_path(csv_path, stage_root),
                    }
                )

    manifest = pd.DataFrame(rows).sort_values(
        ["case", "pol", "rect", "theta_deg", "observation_distance_lambda_scale", "csv_path"]
    ).reset_index(drop=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(args.output, index=False)

    print(f"Manifest rows: {len(manifest)}")
    print(f"Input root:    {input_root}")
    print(f"Output path:   {args.output}")


if __name__ == "__main__":
    main()
