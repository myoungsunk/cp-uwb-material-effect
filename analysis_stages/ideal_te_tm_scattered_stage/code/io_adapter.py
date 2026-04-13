from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
import re

import numpy as np
import pandas as pd

from geometry import GeometryConfig, plane_center, wide_plane_axes


CANONICAL_ALIASES = {
    "point_id": ["pointid", "point", "id"],
    "x": ["x", "xm"],
    "y": ["y", "ym"],
    "z": ["z", "zm"],
    "f_hz": ["fhz", "frequencyhz", "frequency", "freq", "f", "ghz", "freqghz"],
    "theta_deg": ["thetadeg", "thetakdeg", "thetak", "theta", "thetai", "incidentangledeg"],
    "ex_real": ["nearexreal", "exreal", "realex", "realnearex"],
    "ex_imag": ["neareximag", "eximag", "imagex", "imagnearex"],
    "ey_real": ["neareyreal", "eyreal", "realey", "realnearey"],
    "ey_imag": ["neareyimag", "eyimag", "imagey", "imagnearey"],
    "ez_real": ["nearezreal", "ezreal", "realez", "realnearez"],
    "ez_imag": ["nearezimag", "ezimag", "imagez", "imagnearez"],
}

REQUIRED_MANIFEST_COLUMNS = ["case", "pol", "rect", "csv_path", "field_type"]
OPTIONAL_MANIFEST_COLUMNS = ["f_hz", "theta_deg", "observation_distance_lambda_scale", "run_label"]

WIDE_GRID_PREFIX_RE = re.compile(
    r"^(?P<kind>mag|ang_deg)\(NearE(?P<axis>[XYZ])\)\s+\[[^\]]+\]\s+-\s+_v='(?P<v>[^']+)'",
    re.IGNORECASE,
)
WIDE_GRID_FREQ_RE = re.compile(r"Freq='(?P<freq>[^']+)'", re.IGNORECASE)
WIDE_GRID_KOBS_RE = re.compile(r"k_obs='(?P<kobs>[^']+)'", re.IGNORECASE)
WIDE_GRID_THETA_RE = re.compile(r"theta_k='(?P<theta>[^']+)'", re.IGNORECASE)


def canonicalize_column(name: str) -> str:
    return "".join(ch for ch in str(name).lower() if ch.isalnum())


def _resolve_column(columns: list[str], alias_key: str, required: bool) -> str | None:
    canonical_map = {canonicalize_column(column): column for column in columns}
    for alias in CANONICAL_ALIASES[alias_key]:
        if alias in canonical_map:
            return canonical_map[alias]
    if required:
        raise KeyError(f"Could not resolve required column '{alias_key}' from {columns}")
    return None


def _normalize_frequency(values: pd.Series, source_column: str) -> pd.Series:
    canonical = canonicalize_column(source_column)
    numeric = pd.to_numeric(values, errors="coerce")
    if "ghz" in canonical:
        return numeric * 1e9
    if numeric.dropna().empty:
        return numeric
    if numeric.abs().max() < 1e6:
        return numeric * 1e9
    return numeric


def _normalize_theta(values: pd.Series, source_column: str) -> pd.Series:
    canonical = canonicalize_column(source_column)
    numeric = pd.to_numeric(values, errors="coerce")
    if "rad" in canonical:
        return np.rad2deg(numeric)
    return numeric


def _resolve_csv_path(raw_path: str, manifest_path: Path, stage_root: Path) -> Path:
    candidate = Path(str(raw_path))
    if candidate.is_absolute():
        return candidate
    search_roots = [manifest_path.parent, stage_root, stage_root / "csv"]
    for root in search_roots:
        resolved = (root / candidate).resolve()
        if _path_exists(resolved):
            return resolved
    return (manifest_path.parent / candidate).resolve()


def _windows_long_path_str(path: Path | str) -> str:
    text = str(path)
    if os.name != "nt":
        return text
    if text.startswith("\\\\?\\"):
        return text
    if text.startswith("\\\\"):
        return "\\\\?\\UNC\\" + text.lstrip("\\")
    return "\\\\?\\" + text


def _path_exists(path: Path) -> bool:
    return os.path.exists(_windows_long_path_str(path))


def _parse_number_and_unit(value: str) -> tuple[float, str]:
    match = re.fullmatch(
        r"\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*([A-Za-z_]+)?\s*",
        str(value),
    )
    if not match:
        raise ValueError(f"Could not parse numeric value with unit from: {value!r}")
    return float(match.group(1)), (match.group(2) or "").lower()


def _parse_length_to_m(value: str) -> float:
    magnitude, unit = _parse_number_and_unit(value)
    scale = {
        "m": 1.0,
        "mm": 1e-3,
        "um": 1e-6,
        "nm": 1e-9,
        "cm": 1e-2,
    }.get(unit)
    if scale is None:
        if unit == "":
            return magnitude
        raise ValueError(f"Unsupported length unit: {unit!r}")
    return magnitude * scale


def _parse_freq_to_hz(value: str) -> float:
    magnitude, unit = _parse_number_and_unit(value)
    scale = {
        "hz": 1.0,
        "khz": 1e3,
        "mhz": 1e6,
        "ghz": 1e9,
    }.get(unit)
    if scale is None:
        if unit == "":
            return magnitude
        raise ValueError(f"Unsupported frequency unit: {unit!r}")
    return magnitude * scale


def _parse_theta_to_deg(value: str) -> float:
    magnitude, unit = _parse_number_and_unit(value)
    if unit in {"", "deg"}:
        return magnitude
    if unit == "rad":
        return float(np.rad2deg(magnitude))
    raise ValueError(f"Unsupported angle unit: {unit!r}")


def _normalize_field_type(value) -> str:
    if pd.isna(value):
        raise ValueError("Manifest field_type must be explicitly set to 'total' or 'scattered'.")
    text = str(value).strip().lower()
    if text in {"total", "scattered"}:
        return text
    raise ValueError(f"Unsupported manifest field_type: {value!r}")


def _parse_wide_grid_header(header: str) -> dict[str, str] | None:
    text = str(header).strip()
    prefix_match = WIDE_GRID_PREFIX_RE.match(text)
    if not prefix_match:
        return None

    freq_match = WIDE_GRID_FREQ_RE.search(text)
    theta_match = WIDE_GRID_THETA_RE.search(text)
    if freq_match is None or theta_match is None:
        return None

    kobs_match = WIDE_GRID_KOBS_RE.search(text)
    return {
        "kind": prefix_match.group("kind").lower(),
        "axis": prefix_match.group("axis").upper(),
        "v": prefix_match.group("v"),
        "freq": freq_match.group("freq"),
        "theta": theta_match.group("theta"),
        "kobs": kobs_match.group("kobs") if kobs_match is not None else "",
    }


def _is_wide_hfss_grid_csv(raw: pd.DataFrame) -> bool:
    if raw.empty or not len(raw.columns):
        return False
    first = str(raw.columns[0]).strip().lower()
    if not first.startswith("_u"):
        return False
    if len(raw.columns) < 2:
        return False
    return _parse_wide_grid_header(str(raw.columns[1])) is not None


def _wide_hfss_grid_to_normalized(raw: pd.DataFrame, manifest_row: pd.Series, geom: GeometryConfig) -> pd.DataFrame:
    u_values = pd.to_numeric(raw.iloc[:, 0], errors="coerce").to_numpy(dtype=float)
    if np.isnan(u_values).any():
        raise ValueError(f"Failed to parse `_u` coordinates from {manifest_row['csv_path']}")

    column_meta: dict[tuple[float, float, float, float], dict[str, str]] = {}
    for column in raw.columns[1:]:
        header_meta = _parse_wide_grid_header(str(column))
        if not header_meta:
            continue
        freq_hz = _parse_freq_to_hz(header_meta["freq"])
        theta_deg = _parse_theta_to_deg(header_meta["theta"])
        v_m = _parse_length_to_m(header_meta["v"])
        observation_distance_lambda_scale = float(header_meta["kobs"]) if header_meta["kobs"] else np.nan
        axis = header_meta["axis"]
        suffix = "mag" if header_meta["kind"] == "mag" else "ang"
        column_meta.setdefault(
            (freq_hz, theta_deg, observation_distance_lambda_scale, v_m),
            {},
        )[f"E{axis}_{suffix}"] = str(column)

    if not column_meta:
        raise ValueError(f"No HFSS wide-grid headers were parsed from {manifest_row['csv_path']}")

    v_order = {value: index for index, value in enumerate(sorted({key[3] for key in column_meta}))}
    frames: list[pd.DataFrame] = []
    manifest_obs_scale = pd.to_numeric(
        pd.Series([manifest_row.get("observation_distance_lambda_scale", np.nan)]),
        errors="coerce",
    ).iloc[0]
    field_type = _normalize_field_type(manifest_row.get("field_type"))

    for (freq_hz, theta_deg, header_obs_scale, v_m), mapping in sorted(column_meta.items()):
        required = [
            "EX_mag", "EX_ang",
            "EY_mag", "EY_ang",
            "EZ_mag", "EZ_ang",
        ]
        missing = [item for item in required if item not in mapping]
        if missing:
            raise ValueError(
                f"Missing wide-grid field columns {missing} for "
                f"f={freq_hz} theta={theta_deg} v={v_m} in {manifest_row['csv_path']}"
            )

        observation_distance_lambda_scale = (
            float(manifest_obs_scale)
            if pd.notna(manifest_obs_scale)
            else (
                float(header_obs_scale)
                if not np.isnan(header_obs_scale)
                else float(geom.observation_distance_lambda_scale)
            )
        )
        u_hat, v_hat = wide_plane_axes(theta_deg, str(manifest_row["rect"]), geom)
        center = plane_center(
            theta_deg,
            freq_hz,
            str(manifest_row["rect"]),
            geom,
            observation_distance_lambda_scale=observation_distance_lambda_scale,
        )
        points = center[None, :] + u_values[:, None] * u_hat[None, :] + float(v_m) * v_hat[None, :]
        point_id = np.arange(len(u_values), dtype=int) + v_order[v_m] * len(u_values)

        def complex_field(axis: str) -> np.ndarray:
            mag = pd.to_numeric(raw[mapping[f"E{axis}_mag"]], errors="coerce").to_numpy(dtype=float)
            ang_deg = pd.to_numeric(raw[mapping[f"E{axis}_ang"]], errors="coerce").to_numpy(dtype=float)
            return mag * np.exp(1j * np.deg2rad(ang_deg))

        frame = pd.DataFrame(
            {
                "case": manifest_row["case"],
                "pol": manifest_row["pol"],
                "rect": manifest_row["rect"],
                "run_label": manifest_row.get("run_label", ""),
                "point_id": point_id,
                "x": points[:, 0],
                "y": points[:, 1],
                "z": points[:, 2],
                "Ex": complex_field("X"),
                "Ey": complex_field("Y"),
                "Ez": complex_field("Z"),
                "f_hz": float(freq_hz),
                "theta_deg": float(theta_deg),
                "field_type": field_type,
                "observation_distance_lambda_scale": observation_distance_lambda_scale,
            }
        )
        frames.append(frame)

    normalized = pd.concat(frames, ignore_index=True)

    if pd.notna(manifest_row["f_hz"]):
        target_f = float(manifest_row["f_hz"])
        atol = max(abs(target_f) * 1e-9, 1.0)
        normalized = normalized[np.isclose(normalized["f_hz"], target_f, atol=atol, rtol=0.0)]

    if pd.notna(manifest_row["theta_deg"]):
        target_theta = float(manifest_row["theta_deg"])
        normalized = normalized[np.isclose(normalized["theta_deg"], target_theta, atol=1e-9, rtol=0.0)]

    if normalized.empty:
        raise ValueError(
            f"No rows left after filtering {manifest_row['csv_path']} "
            f"for f_hz={manifest_row['f_hz']} theta_deg={manifest_row['theta_deg']}."
        )

    return normalized.sort_values(["f_hz", "theta_deg", "point_id"]).reset_index(drop=True)


def read_manifest(path: Path, stage_root: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")
    manifest = pd.read_csv(path)
    missing = [col for col in REQUIRED_MANIFEST_COLUMNS if col not in manifest.columns]
    if missing:
        raise ValueError(f"Manifest missing required columns: {missing}")
    for column in OPTIONAL_MANIFEST_COLUMNS:
        if column not in manifest.columns:
            manifest[column] = np.nan

    manifest["case"] = manifest["case"].astype(str)
    manifest["pol"] = manifest["pol"].astype(str).str.upper()
    manifest["rect"] = manifest["rect"].astype(str)
    manifest["csv_path"] = manifest["csv_path"].astype(str).map(
        lambda item: _resolve_csv_path(item, path, stage_root)
    )
    manifest["f_hz"] = pd.to_numeric(manifest["f_hz"], errors="coerce")
    manifest["theta_deg"] = pd.to_numeric(manifest["theta_deg"], errors="coerce")
    manifest["field_type"] = manifest["field_type"].map(_normalize_field_type)
    manifest["observation_distance_lambda_scale"] = pd.to_numeric(
        manifest["observation_distance_lambda_scale"],
        errors="coerce",
    )
    return manifest


@lru_cache(maxsize=128)
def _load_raw_csv(path_str: str) -> pd.DataFrame:
    return pd.read_csv(_windows_long_path_str(path_str))


def normalize_measurement_csv(manifest_row: pd.Series, geom: GeometryConfig | None = None) -> pd.DataFrame:
    raw = _load_raw_csv(str(manifest_row["csv_path"])).copy()
    if _is_wide_hfss_grid_csv(raw):
        if geom is None:
            raise ValueError("GeometryConfig is required to normalize HFSS wide-grid exports.")
        return _wide_hfss_grid_to_normalized(raw, manifest_row, geom)
    columns = raw.columns.tolist()

    point_col = _resolve_column(columns, "point_id", required=False)
    x_col = _resolve_column(columns, "x", required=True)
    y_col = _resolve_column(columns, "y", required=True)
    z_col = _resolve_column(columns, "z", required=True)
    ex_real_col = _resolve_column(columns, "ex_real", required=True)
    ex_imag_col = _resolve_column(columns, "ex_imag", required=True)
    ey_real_col = _resolve_column(columns, "ey_real", required=True)
    ey_imag_col = _resolve_column(columns, "ey_imag", required=True)
    ez_real_col = _resolve_column(columns, "ez_real", required=True)
    ez_imag_col = _resolve_column(columns, "ez_imag", required=True)
    f_col = _resolve_column(columns, "f_hz", required=False)
    theta_col = _resolve_column(columns, "theta_deg", required=False)

    normalized = pd.DataFrame(
        {
            "case": manifest_row["case"],
            "pol": manifest_row["pol"],
            "rect": manifest_row["rect"],
            "run_label": manifest_row.get("run_label", ""),
            "point_id": raw[point_col].to_numpy() if point_col else np.arange(len(raw)),
            "x": pd.to_numeric(raw[x_col], errors="coerce"),
            "y": pd.to_numeric(raw[y_col], errors="coerce"),
            "z": pd.to_numeric(raw[z_col], errors="coerce"),
            "Ex": pd.to_numeric(raw[ex_real_col], errors="coerce").to_numpy()
            + 1j * pd.to_numeric(raw[ex_imag_col], errors="coerce").to_numpy(),
            "Ey": pd.to_numeric(raw[ey_real_col], errors="coerce").to_numpy()
            + 1j * pd.to_numeric(raw[ey_imag_col], errors="coerce").to_numpy(),
            "Ez": pd.to_numeric(raw[ez_real_col], errors="coerce").to_numpy()
            + 1j * pd.to_numeric(raw[ez_imag_col], errors="coerce").to_numpy(),
        }
    )

    if f_col:
        normalized["f_hz"] = _normalize_frequency(raw[f_col], f_col)
    else:
        normalized["f_hz"] = manifest_row["f_hz"]

    if theta_col:
        normalized["theta_deg"] = _normalize_theta(raw[theta_col], theta_col)
    else:
        normalized["theta_deg"] = manifest_row["theta_deg"]

    normalized["field_type"] = _normalize_field_type(manifest_row.get("field_type"))
    normalized["observation_distance_lambda_scale"] = pd.to_numeric(
        pd.Series([manifest_row.get("observation_distance_lambda_scale", np.nan)]),
        errors="coerce",
    ).iloc[0]

    if pd.notna(manifest_row["f_hz"]):
        target_f = float(manifest_row["f_hz"])
        atol = max(abs(target_f) * 1e-9, 1.0)
        normalized = normalized[np.isclose(normalized["f_hz"], target_f, atol=atol, rtol=0.0)]

    if pd.notna(manifest_row["theta_deg"]):
        target_theta = float(manifest_row["theta_deg"])
        normalized = normalized[np.isclose(normalized["theta_deg"], target_theta, atol=1e-9, rtol=0.0)]

    if normalized.empty:
        raise ValueError(
            f"No rows left after filtering {manifest_row['csv_path']} "
            f"for f_hz={manifest_row['f_hz']} theta_deg={manifest_row['theta_deg']}."
        )

    if normalized["f_hz"].isna().any():
        raise ValueError(f"Missing frequency values in {manifest_row['csv_path']}")
    if normalized["theta_deg"].isna().any():
        raise ValueError(f"Missing theta values in {manifest_row['csv_path']}")

    normalized = normalized.sort_values(["point_id", "x", "y", "z"]).reset_index(drop=True)
    return normalized


def load_normalized_measurements(manifest: pd.DataFrame, geom: GeometryConfig | None = None) -> pd.DataFrame:
    frames = [normalize_measurement_csv(row, geom=geom) for _, row in manifest.iterrows()]
    if not frames:
        return pd.DataFrame(
            columns=[
                "case",
                "pol",
                "rect",
                "f_hz",
                "theta_deg",
                "field_type",
                "observation_distance_lambda_scale",
                "point_id",
                "x",
                "y",
                "z",
                "Ex",
                "Ey",
                "Ez",
            ]
        )
    return pd.concat(frames, ignore_index=True)
