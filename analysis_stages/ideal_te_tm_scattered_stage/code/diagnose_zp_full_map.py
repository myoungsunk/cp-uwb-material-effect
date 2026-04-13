from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from estimator import matched_plane_wave_estimator
from geometry import (
    GeometryConfig,
    incident_hat,
    load_geometry_config,
    plane_center,
    transmitted_hat,
    wide_plane_axes,
)
from incident_field import analytic_incident_field
from io_adapter import load_normalized_measurements, read_manifest
from projection import project_vector_field


def find_stage_root(start: Path) -> Path:
    return start.resolve().parents[1]


def extract_arrays(sub_df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    points = sub_df[["x", "y", "z"]].to_numpy(dtype=float)
    field = np.column_stack(
        [
            sub_df["Ex"].to_numpy(dtype=complex),
            sub_df["Ey"].to_numpy(dtype=complex),
            sub_df["Ez"].to_numpy(dtype=complex),
        ]
    )
    return points, field


def map_coordinates(
    points: np.ndarray,
    theta_deg: float,
    f_hz: float,
    obs_scale: float,
    geom: GeometryConfig,
) -> tuple[np.ndarray, np.ndarray]:
    center = plane_center(
        theta_deg,
        f_hz,
        geom.trans_rect,
        geom,
        observation_distance_lambda_scale=obs_scale,
    )
    u_hat, v_hat = wide_plane_axes(theta_deg, geom.trans_rect, geom)
    rel = points - center[None, :]
    u = rel @ u_hat
    v = rel @ v_hat
    return u, v


def reshape_map(u: np.ndarray, v: np.ndarray, values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    u_unique = np.unique(np.round(u, 12))
    v_unique = np.unique(np.round(v, 12))
    grid = np.full((len(v_unique), len(u_unique)), np.nan, dtype=float)
    u_index = {value: idx for idx, value in enumerate(u_unique)}
    v_index = {value: idx for idx, value in enumerate(v_unique)}
    for uu, vv, val in zip(np.round(u, 12), np.round(v, 12), values):
        grid[v_index[vv], u_index[uu]] = float(val)
    return u_unique, v_unique, grid


def edge_center_ratio(grid: np.ndarray) -> tuple[float, float, float]:
    if grid.size == 0:
        return np.nan, np.nan, np.nan
    edge_mask = np.zeros_like(grid, dtype=bool)
    edge_mask[0, :] = True
    edge_mask[-1, :] = True
    edge_mask[:, 0] = True
    edge_mask[:, -1] = True

    n_v, n_u = grid.shape
    cv0 = max(0, n_v // 2 - 2)
    cv1 = min(n_v, n_v // 2 + 3)
    cu0 = max(0, n_u // 2 - 2)
    cu1 = min(n_u, n_u // 2 + 3)
    center_block = grid[cv0:cv1, cu0:cu1]

    edge_mean = float(np.nanmean(grid[edge_mask]))
    center_mean = float(np.nanmean(center_block))
    ratio = float(edge_mean / center_mean) if center_mean > 0 else np.nan
    return edge_mean, center_mean, ratio


def normalized_complex_correlation(a: np.ndarray, b: np.ndarray) -> float:
    aa = np.asarray(a, dtype=complex)
    bb = np.asarray(b, dtype=complex)
    denom = np.linalg.norm(aa) * np.linalg.norm(bb)
    if denom == 0:
        return np.nan
    return float(np.abs(np.vdot(aa, bb)) / denom)


def profile_metrics(grid: np.ndarray) -> tuple[float, float, float]:
    mean_val = float(np.nanmean(grid))
    if not np.isfinite(mean_val) or mean_val <= 0:
        return np.nan, np.nan, np.nan
    u_profile = np.nanmean(grid, axis=0)
    v_profile = np.nanmean(grid, axis=1)
    u_std_norm = float(np.nanstd(u_profile) / mean_val)
    v_std_norm = float(np.nanstd(v_profile) / mean_val)
    anisotropy = float(u_std_norm / max(v_std_norm, 1e-15))
    return u_std_norm, v_std_norm, anisotropy


def compute_group_maps(sub_df: pd.DataFrame, geom: GeometryConfig) -> dict:
    points, exported_field = extract_arrays(sub_df)
    f_hz = float(sub_df["f_hz"].iloc[0])
    theta_deg = float(sub_df["theta_deg"].iloc[0])
    pol = str(sub_df["pol"].iloc[0]).upper()
    field_type = str(sub_df["field_type"].iloc[0]).lower()
    obs_scale = float(sub_df["observation_distance_lambda_scale"].iloc[0])

    incident_field = analytic_incident_field(points, f_hz, theta_deg, pol, geom)
    if field_type == "scattered":
        total_field = incident_field + exported_field
        residual_field = exported_field
    elif field_type == "total":
        total_field = exported_field
        residual_field = exported_field - incident_field
    else:
        raise ValueError(f"Unsupported field_type: {field_type!r}")

    scalar_incident = project_vector_field(incident_field, theta_deg, pol, "incident", geom)
    scalar_total = project_vector_field(total_field, theta_deg, pol, "transmitted", geom)
    scalar_residual = project_vector_field(residual_field, theta_deg, pol, "transmitted", geom)

    incident_est = matched_plane_wave_estimator(points, scalar_incident, f_hz, incident_hat(theta_deg, geom))
    total_est = matched_plane_wave_estimator(points, scalar_total, f_hz, transmitted_hat(theta_deg, geom))
    residual_est = matched_plane_wave_estimator(points, scalar_residual, f_hz, transmitted_hat(theta_deg, geom))

    k0 = 2.0 * np.pi * f_hz / 299_792_458.0
    fit_phase = (points - total_est.center_xyz) @ transmitted_hat(theta_deg, geom)
    scalar_fit = total_est.amplitude * np.exp(-1j * k0 * fit_phase)
    scalar_fit_residual = scalar_total - scalar_fit

    inc_norm = max(abs(incident_est.amplitude), 1e-15)
    u, v = map_coordinates(points, theta_deg, f_hz, obs_scale, geom)

    total_norm = np.abs(scalar_total) / inc_norm
    residual_norm = np.abs(scalar_residual) / inc_norm
    fit_residual_norm = np.abs(scalar_fit_residual) / inc_norm

    u_unique, v_unique, total_grid = reshape_map(u, v, total_norm)
    _, _, residual_grid = reshape_map(u, v, residual_norm)
    _, _, fit_residual_grid = reshape_map(u, v, fit_residual_norm)

    edge_mean, center_mean, edge_center = edge_center_ratio(residual_grid)
    u_std_norm, v_std_norm, uv_anisotropy = profile_metrics(residual_grid)
    incident_corr_total = normalized_complex_correlation(scalar_total, scalar_incident)
    incident_corr_residual = normalized_complex_correlation(scalar_residual, scalar_incident)

    return {
        "theta_deg": theta_deg,
        "pol": pol,
        "f_hz": f_hz,
        "field_type": field_type,
        "observation_distance_lambda_scale": obs_scale,
        "u_mm": u_unique * 1e3,
        "v_mm": v_unique * 1e3,
        "total_grid": total_grid,
        "residual_grid": residual_grid,
        "fit_residual_grid": fit_residual_grid,
        "incident_amp_mag": float(abs(incident_est.amplitude)),
        "total_amp_mag": float(abs(total_est.amplitude)),
        "fit_residual_scalar": float(total_est.residual),
        "residual_pw_amp_mag": float(abs(residual_est.amplitude)),
        "residual_pw_fit_scalar": float(residual_est.residual),
        "incident_corr_total": incident_corr_total,
        "incident_corr_residual": incident_corr_residual,
        "residual_mean": float(np.nanmean(residual_grid)),
        "residual_max": float(np.nanmax(residual_grid)),
        "edge_mean": edge_mean,
        "center_mean": center_mean,
        "edge_center_ratio": edge_center,
        "u_profile_std_norm": u_std_norm,
        "v_profile_std_norm": v_std_norm,
        "uv_profile_anisotropy": uv_anisotropy,
    }


def plot_overview(
    maps: list[dict],
    metric_key: str,
    title: str,
    output_path: Path,
) -> None:
    if not maps:
        return
    thetas = sorted({float(item["theta_deg"]) for item in maps})
    kobs_values = sorted({float(item["observation_distance_lambda_scale"]) for item in maps})

    vmax = max(float(np.nanmax(item[metric_key])) for item in maps)
    vmax = max(vmax, 1e-12)

    fig, axes = plt.subplots(
        len(thetas),
        len(kobs_values),
        figsize=(4.0 * len(kobs_values), 3.2 * len(thetas)),
        constrained_layout=True,
    )
    if len(thetas) == 1 and len(kobs_values) == 1:
        axes = np.array([[axes]])
    elif len(thetas) == 1:
        axes = np.array([axes])
    elif len(kobs_values) == 1:
        axes = np.array([[ax] for ax in axes])

    for row, theta_deg in enumerate(thetas):
        for col, obs_scale in enumerate(kobs_values):
            ax = axes[row, col]
            item = next(
                entry for entry in maps
                if float(entry["theta_deg"]) == theta_deg
                and float(entry["observation_distance_lambda_scale"]) == obs_scale
            )
            im = ax.imshow(
                item[metric_key],
                origin="lower",
                extent=[
                    float(item["u_mm"][0]),
                    float(item["u_mm"][-1]),
                    float(item["v_mm"][0]),
                    float(item["v_mm"][-1]),
                ],
                aspect="equal",
                cmap="viridis",
                vmin=0.0,
                vmax=vmax,
            )
            ax.set_title(f"theta={theta_deg:.0f}°, kobs={obs_scale:g}")
            if row == len(thetas) - 1:
                ax.set_xlabel("u [mm]")
            if col == 0:
                ax.set_ylabel("v [mm]")

    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.92)
    cbar.set_label("normalized magnitude")
    fig.suptitle(title)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def main() -> None:
    stage_root = find_stage_root(Path(__file__))
    parser = argparse.ArgumentParser(description="Diagnose z_p full-map behavior for PEC TE/TM datasets.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=stage_root / "config" / "manifest_actual_new_runs_20260412.csv",
    )
    parser.add_argument(
        "--geometry",
        type=Path,
        default=stage_root / "config" / "geometry.yaml",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=stage_root / "results" / "actual_new_runs_20260412_full_map_diagnostics",
    )
    parser.add_argument("--case", default="pec")
    parser.add_argument("--rect", default="trans_rect")
    args = parser.parse_args()

    geom = load_geometry_config(args.geometry)
    manifest = read_manifest(args.manifest, stage_root)
    measurements = load_normalized_measurements(manifest, geom=geom)

    sub = measurements[
        (measurements["case"] == args.case)
        & (measurements["rect"] == args.rect)
    ].copy()

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    maps: list[dict] = []
    group_cols = ["case", "pol", "rect", "f_hz", "theta_deg", "observation_distance_lambda_scale"]
    for _, group in sub.groupby(group_cols, sort=True, dropna=False):
        maps.append(compute_group_maps(group.reset_index(drop=True), geom))

    summary_rows: list[dict] = []
    for item in maps:
        summary_rows.append(
            {
                "pol": item["pol"],
                "theta_deg": item["theta_deg"],
                "f_hz": item["f_hz"],
                "field_type": item["field_type"],
                "observation_distance_lambda_scale": item["observation_distance_lambda_scale"],
                "incident_amp_mag": item["incident_amp_mag"],
                "total_amp_mag": item["total_amp_mag"],
                "fit_residual_scalar": item["fit_residual_scalar"],
                "residual_pw_amp_mag": item["residual_pw_amp_mag"],
                "residual_pw_fit_scalar": item["residual_pw_fit_scalar"],
                "incident_corr_total": item["incident_corr_total"],
                "incident_corr_residual": item["incident_corr_residual"],
                "residual_mean_map": item["residual_mean"],
                "residual_max_map": item["residual_max"],
                "edge_mean_map": item["edge_mean"],
                "center_mean_map": item["center_mean"],
                "edge_center_ratio": item["edge_center_ratio"],
                "u_profile_std_norm": item["u_profile_std_norm"],
                "v_profile_std_norm": item["v_profile_std_norm"],
                "uv_profile_anisotropy": item["uv_profile_anisotropy"],
            }
        )
    summary_df = pd.DataFrame(summary_rows).sort_values(["pol", "observation_distance_lambda_scale", "theta_deg"])
    summary_df.to_csv(output_dir / "zp_full_map_summary.csv", index=False)

    for pol in sorted(summary_df["pol"].unique()):
        pol_maps = [item for item in maps if item["pol"] == pol]
        plot_overview(
            pol_maps,
            "total_grid",
            f"{args.case.upper()} {pol} z_p total map / incident amplitude",
            output_dir / f"{pol}_z_p_total_norm_overview.png",
        )
        plot_overview(
            pol_maps,
            "residual_grid",
            f"{args.case.upper()} {pol} z_p incident-subtracted map / incident amplitude",
            output_dir / f"{pol}_z_p_residual_norm_overview.png",
        )
        plot_overview(
            pol_maps,
            "fit_residual_grid",
            f"{args.case.upper()} {pol} z_p fit-residual map / incident amplitude",
            output_dir / f"{pol}_z_p_fit_residual_norm_overview.png",
        )

    print(f"Wrote summary: {output_dir / 'zp_full_map_summary.csv'}")
    print(f"Wrote overview PNGs into: {output_dir}")


if __name__ == "__main__":
    main()
