# Consolidated review copy for paper-pipeline code assessment.
# Stage: 4
# Role: Comparator script for the direct CP one-point sanity check outputs.
# Source: analysis_stages/direct_cp_one_point_sanity_20260414/code/compare_direct_cp_one_point.py
# Note: This copy is centralized for code rationality review; the original staged workflow remains unchanged.

from __future__ import annotations

import argparse
import cmath
import csv
import math
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a direct-CP one-point reference and compare future direct-CP "
            "measurements against the locked ideal/patch/LP branches."
        )
    )
    parser.add_argument("--material", required=True)
    parser.add_argument("--theta-deg", type=float, required=True)
    parser.add_argument("--freq-ghz", type=float, required=True)
    parser.add_argument("--truth-csv", type=Path, required=True)
    parser.add_argument("--patch-cp-csv", type=Path)
    parser.add_argument("--lp-csv", type=Path)
    parser.add_argument("--measurement-csv", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--theta-tol", type=float, default=1e-6)
    parser.add_argument("--freq-tol-ghz", type=float, default=0.02)
    return parser.parse_args()


def normalize_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return (Path.cwd() / path).resolve()


def read_csv(path: Path) -> List[Dict[str, str]]:
    normalized = normalize_path(path)
    with normalized.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return float(text)


def first_present(row: Dict[str, str], keys: Iterable[str]) -> Optional[float]:
    for key in keys:
        if key in row:
            value = parse_float(row.get(key))
            if value is not None:
                return value
    return None


def row_freq_ghz(row: Dict[str, str]) -> Optional[float]:
    ghz = first_present(row, ["freq_ghz", "freq_center_ghz", "f_ghz"])
    if ghz is not None:
        return ghz
    hz = first_present(row, ["f_hz", "freq_hz"])
    if hz is not None:
        return hz / 1e9
    return None


def select_rows(
    rows: Iterable[Dict[str, str]],
    material: str,
    theta_deg: float,
    freq_ghz: float,
    theta_tol: float,
    freq_tol_ghz: float,
) -> List[Dict[str, str]]:
    selected: List[Dict[str, str]] = []
    for row in rows:
        if str(row.get("material", "")).strip().lower() != material.lower():
            continue
        theta = parse_float(row.get("theta_deg"))
        if theta is None or abs(theta - theta_deg) > theta_tol:
            continue
        freq = row_freq_ghz(row)
        if freq is None or abs(freq - freq_ghz) > freq_tol_ghz:
            continue
        selected.append(row)
    return selected


def complex_from_row(
    row: Dict[str, str],
    real_key: str,
    imag_key: str,
    mag_key: Optional[str] = None,
    phase_key: Optional[str] = None,
) -> complex:
    real = parse_float(row.get(real_key))
    imag = parse_float(row.get(imag_key))
    if real is not None and imag is not None:
        return complex(real, imag)
    if mag_key is None or phase_key is None:
        raise ValueError(f"Missing complex fields: {real_key}, {imag_key}")
    mag = parse_float(row.get(mag_key))
    phase_deg = parse_float(row.get(phase_key))
    if mag is None or phase_deg is None:
        raise ValueError(
            f"Need either {real_key}/{imag_key} or {mag_key}/{phase_key}."
        )
    return cmath.rect(mag, math.radians(phase_deg))


def branch_record(
    source: str,
    branch_name: str,
    value: complex,
    role: str = "",
    extra: Optional[Dict[str, str]] = None,
    mag_override: Optional[float] = None,
) -> Dict[str, object]:
    phase_deg = math.degrees(cmath.phase(value))
    if phase_deg <= -180.0:
        phase_deg += 360.0
    if phase_deg > 180.0:
        phase_deg -= 360.0
    record: Dict[str, object] = {
        "source": source,
        "branch_name": branch_name,
        "branch_role": role,
        "real": value.real,
        "imag": value.imag,
        "mag": abs(value) if mag_override is None else mag_override,
        "phase_deg": phase_deg,
    }
    if extra:
        record.update(extra)
    return record


def order_small_large(records: List[Dict[str, object]]) -> List[Dict[str, object]]:
    ordered = sorted(records, key=lambda item: float(item["mag"]))
    if len(ordered) >= 1:
        ordered[0]["branch_role"] = "small"
    if len(ordered) >= 2:
        ordered[1]["branch_role"] = "large"
    return ordered


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        return
    fieldnames: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def get_single_row(
    path: Path,
    material: str,
    theta_deg: float,
    freq_ghz: float,
    theta_tol: float,
    freq_tol_ghz: float,
) -> Dict[str, str]:
    rows = select_rows(
        read_csv(path), material, theta_deg, freq_ghz, theta_tol, freq_tol_ghz
    )
    if not rows:
        raise SystemExit(f"No matching row found in {path}")
    if len(rows) > 1:
        raise SystemExit(f"Multiple matching rows found in {path}")
    return rows[0]


def build_ideal_records(row: Dict[str, str]) -> List[Dict[str, object]]:
    return order_small_large(
        [
            branch_record(
                "ideal_cp",
                "Gamma_X",
                complex_from_row(row, "Gamma_X_real", "Gamma_X_imag"),
            ),
            branch_record(
                "ideal_cp",
                "Gamma_C",
                complex_from_row(row, "Gamma_C_real", "Gamma_C_imag"),
            ),
        ]
    )


def build_patch_records(row: Dict[str, str]) -> List[Dict[str, object]]:
    return order_small_large(
        [
            branch_record(
                "patch_cp",
                "gamma_hat_x_cp_sys",
                complex_from_row(
                    row, "gamma_hat_x_cp_sys_real", "gamma_hat_x_cp_sys_imag"
                ),
                mag_override=parse_float(row.get("gamma_hat_x_cp_sys_mag")),
            ),
            branch_record(
                "patch_cp",
                "gamma_hat_c_cp_eff",
                complex_from_row(
                    row, "gamma_hat_c_cp_eff_real", "gamma_hat_c_cp_eff_imag"
                ),
                mag_override=parse_float(row.get("gamma_hat_c_cp_eff_mag")),
            ),
        ]
    )


def build_lp_records(row: Dict[str, str]) -> List[Dict[str, object]]:
    return order_small_large(
        [
            branch_record(
                "lp_bridge",
                "gamma_x_from_lp",
                complex_from_row(row, "gamma_x_from_lp_real", "gamma_x_from_lp_imag"),
                mag_override=parse_float(row.get("gamma_x_from_lp_mag")),
            ),
            branch_record(
                "lp_bridge",
                "gamma_c_from_lp",
                complex_from_row(row, "gamma_c_from_lp_real", "gamma_c_from_lp_imag"),
                mag_override=parse_float(row.get("gamma_c_from_lp_mag")),
            ),
        ]
    )


def build_measurement_records(
    path: Path,
    material: str,
    theta_deg: float,
    freq_ghz: float,
    theta_tol: float,
    freq_tol_ghz: float,
) -> List[Dict[str, object]]:
    rows = select_rows(read_csv(path), material, theta_deg, freq_ghz, theta_tol, freq_tol_ghz)
    if len(rows) != 2:
        raise SystemExit(
            f"Measurement CSV must contain exactly 2 matching rows, found {len(rows)} in {path}"
        )
    records: List[Dict[str, object]] = []
    for row in rows:
        rx_cp = str(row.get("rx_cp", "")).strip() or "unlabeled_rx_cp"
        tx_cp = str(row.get("tx_cp", "")).strip()
        value = complex_from_row(
            row,
            "coeff_real",
            "coeff_imag",
            mag_key="coeff_mag",
            phase_key="coeff_phase_deg",
        )
        records.append(
            branch_record(
                "direct_cp_measurement",
                rx_cp,
                value,
                extra={"tx_cp": tx_cp},
                mag_override=parse_float(row.get("coeff_mag")),
            )
        )
    return order_small_large(records)


def nearest_branch(
    measured: Dict[str, object], candidates: List[Dict[str, object]]
) -> Tuple[str, float]:
    mag = float(measured["mag"])
    distances = [
        (f"{candidate['source']}:{candidate['branch_name']}", abs(mag - float(candidate["mag"])))
        for candidate in candidates
    ]
    return min(distances, key=lambda item: item[1])


def relative_db_ratio(smaller: float, larger: float) -> float:
    if smaller <= 0.0 or larger <= 0.0:
        return float("nan")
    return 20.0 * math.log10(smaller / larger)


def build_reference_markdown(
    material: str,
    theta_deg: float,
    freq_ghz: float,
    reference_rows: List[Dict[str, object]],
) -> str:
    lines = [
        "# Direct CP Target Reference",
        "",
        f"- material: `{material}`",
        f"- theta: `{theta_deg:.1f} deg`",
        f"- frequency: `{freq_ghz:.3f} GHz`",
        "",
        "## Branch Snapshot",
        "",
        "| source | branch | role | mag | phase_deg |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for row in reference_rows:
        lines.append(
            "| {source} | {branch_name} | {branch_role} | {mag:.6f} | {phase_deg:.3f} |".format(
                **row
            )
        )
    return "\n".join(lines) + "\n"


def build_comparison_markdown(
    material: str,
    theta_deg: float,
    freq_ghz: float,
    ideal_rows: List[Dict[str, object]],
    measurement_rows: List[Dict[str, object]],
    patch_rows: List[Dict[str, object]],
    lp_rows: List[Dict[str, object]],
    checks: List[Tuple[str, bool]],
    nearest_rows: List[Dict[str, object]],
) -> str:
    lines = [
        "# Direct CP Comparison",
        "",
        f"- material: `{material}`",
        f"- theta: `{theta_deg:.1f} deg`",
        f"- frequency: `{freq_ghz:.3f} GHz`",
        "",
        "## Measured Branches",
        "",
        "| branch | role | mag | phase_deg | tx_cp |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in measurement_rows:
        lines.append(
            "| {branch_name} | {branch_role} | {mag:.6f} | {phase_deg:.3f} | {tx_cp} |".format(
                tx_cp=row.get("tx_cp", ""),
                **row,
            )
        )
    lines.extend(
        [
            "",
            "## Closest Locked Branches By Magnitude",
            "",
            "| measured branch | role | nearest locked branch | |delta mag| |",
            "| --- | --- | --- | ---: |",
        ]
    )
    for row in nearest_rows:
        lines.append(
            "| {measured_branch} | {measured_role} | {nearest_locked_branch} | {delta_mag:.6f} |".format(
                **row
            )
        )
    lines.extend(["", "## Acceptance Checks", ""])
    for label, ok in checks:
        lines.append(f"- {'PASS' if ok else 'CHECK'}: {label}")
    if ideal_rows:
        lines.extend(["", "## Locked Ideal Ordering", ""])
        for row in ideal_rows:
            lines.append(
                f"- {row['branch_role']}: `{row['branch_name']}` with |.| = {float(row['mag']):.6f}"
            )
    if patch_rows:
        lines.extend(["", "## Current Patch Ordering", ""])
        for row in patch_rows:
            lines.append(
                f"- {row['branch_role']}: `{row['branch_name']}` with |.| = {float(row['mag']):.6f}"
            )
    if lp_rows:
        lines.extend(["", "## Current LP Bridge Ordering", ""])
        for row in lp_rows:
            lines.append(
                f"- {row['branch_role']}: `{row['branch_name']}` with |.| = {float(row['mag']):.6f}"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    ideal_row = get_single_row(
        args.truth_csv,
        args.material,
        args.theta_deg,
        args.freq_ghz,
        args.theta_tol,
        args.freq_tol_ghz,
    )
    ideal_rows = build_ideal_records(ideal_row)

    patch_rows: List[Dict[str, object]] = []
    if args.patch_cp_csv:
        patch_row = get_single_row(
            args.patch_cp_csv,
            args.material,
            args.theta_deg,
            args.freq_ghz,
            args.theta_tol,
            args.freq_tol_ghz,
        )
        patch_rows = build_patch_records(patch_row)

    lp_rows: List[Dict[str, object]] = []
    if args.lp_csv:
        lp_row = get_single_row(
            args.lp_csv,
            args.material,
            args.theta_deg,
            args.freq_ghz,
            args.theta_tol,
            args.freq_tol_ghz,
        )
        lp_rows = build_lp_records(lp_row)

    reference_rows = ideal_rows + patch_rows + lp_rows
    write_csv(args.output_dir / "direct_cp_target_reference.csv", reference_rows)
    (args.output_dir / "direct_cp_target_reference.md").write_text(
        build_reference_markdown(
            args.material, args.theta_deg, args.freq_ghz, reference_rows
        ),
        encoding="utf-8",
    )

    if not args.measurement_csv:
        print("Wrote direct-CP target reference only.")
        return

    measurement_rows = build_measurement_records(
        args.measurement_csv,
        args.material,
        args.theta_deg,
        args.freq_ghz,
        args.theta_tol,
        args.freq_tol_ghz,
    )

    ideal_small = next(row for row in ideal_rows if row["branch_role"] == "small")
    ideal_large = next(row for row in ideal_rows if row["branch_role"] == "large")
    meas_small = next(row for row in measurement_rows if row["branch_role"] == "small")
    meas_large = next(row for row in measurement_rows if row["branch_role"] == "large")

    locked_candidates = ideal_rows + patch_rows + lp_rows
    nearest_rows: List[Dict[str, object]] = []
    for row in measurement_rows:
        nearest_name, delta_mag = nearest_branch(row, locked_candidates)
        nearest_rows.append(
            {
                "measured_branch": row["branch_name"],
                "measured_role": row["branch_role"],
                "nearest_locked_branch": nearest_name,
                "delta_mag": delta_mag,
            }
        )

    checks: List[Tuple[str, bool]] = []
    ratio_db = relative_db_ratio(float(meas_small["mag"]), float(meas_large["mag"]))
    checks.append(
        (
            "measured branches separate into a smaller and larger branch",
            float(meas_small["mag"]) < float(meas_large["mag"]),
        )
    )
    checks.append(
        (
            "measured small branch is closer to ideal small than to ideal large",
            abs(float(meas_small["mag"]) - float(ideal_small["mag"]))
            < abs(float(meas_small["mag"]) - float(ideal_large["mag"])),
        )
    )
    checks.append(
        (
            "measured large branch is closer to ideal large than to ideal small",
            abs(float(meas_large["mag"]) - float(ideal_large["mag"]))
            < abs(float(meas_large["mag"]) - float(ideal_small["mag"])),
        )
    )
    checks.append(
        (
            f"measured small branch stays below measured large branch by at least 6 dB ({ratio_db:.2f} dB observed)",
            math.isfinite(ratio_db) and ratio_db <= -6.0,
        )
    )
    if patch_rows:
        patch_small = next(row for row in patch_rows if row["branch_role"] == "small")
        patch_large = next(row for row in patch_rows if row["branch_role"] == "large")
        checks.append(
            (
                "measured small branch is closer to the current patch small branch than to the current patch large branch",
                abs(float(meas_small["mag"]) - float(patch_small["mag"]))
                < abs(float(meas_small["mag"]) - float(patch_large["mag"])),
            )
        )
    if lp_rows:
        lp_small = next(row for row in lp_rows if row["branch_role"] == "small")
        lp_large = next(row for row in lp_rows if row["branch_role"] == "large")
        checks.append(
            (
                "measured small branch is closer to the LP bridge small branch than to the LP bridge large branch",
                abs(float(meas_small["mag"]) - float(lp_small["mag"]))
                < abs(float(meas_small["mag"]) - float(lp_large["mag"])),
            )
        )

    comparison_rows = reference_rows + measurement_rows
    write_csv(args.output_dir / "direct_cp_comparison.csv", comparison_rows)
    (args.output_dir / "direct_cp_comparison.md").write_text(
        build_comparison_markdown(
            args.material,
            args.theta_deg,
            args.freq_ghz,
            ideal_rows,
            measurement_rows,
            patch_rows,
            lp_rows,
            checks,
            nearest_rows,
        ),
        encoding="utf-8",
    )
    print("Wrote direct-CP comparison outputs.")


if __name__ == "__main__":
    main()
