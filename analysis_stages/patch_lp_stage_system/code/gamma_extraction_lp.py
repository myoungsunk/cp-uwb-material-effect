"""
LP patch-stage reflection analysis pipeline.

Current scope:
  - Generate TE/TM Fresnel theory curves.
  - Reuse the existing CP patch-stage CSVs to compute CP-derived TE/TM proxies.
  - Optionally process future LP patch-stage CSVs when they are added.

Important interpretation:
  - CP-derived R_TE / R_TM in this script are patch-stage proxies, not ideal
    plane-wave material-only coefficients.
  - LP-direct R_TE / R_TM become the cleaner reference once LP M1/M2/M3 CSVs
    are available.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


plt.rcParams.update(
    {
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "legend.fontsize": 8,
        "figure.dpi": 150,
    }
)

CP_CHANNELS = ["LL", "LR", "RL", "RR"]
LP_CHANNELS = ["zz", "zy", "yz", "yy"]
MATERIALS = ["metal", "concrete", "glass", "wood"]

WALL_THICKNESS_MM = 100.0  # HFSS wall_thickness_m = 0.1 m

MATERIAL_PROPS = {
    "metal": {
        # HFSS uses the existing PEC material as-is; no new dielectric values are injected.
        "eps_r": None,
        "tan_d": None,
        "conductivity": None,
        "thickness_mm": None,
        "label": "Metal (PEC existing)",
    },
    "concrete": {
        "eps_r": 5.24,
        "tan_d": 0.105,
        "conductivity": 0.0,
        "thickness_mm": WALL_THICKNESS_MM,
        "label": "Concrete",
    },
    "glass": {
        "eps_r": 6.31,
        "tan_d": 0.019,
        "conductivity": 0.0,
        "thickness_mm": WALL_THICKNESS_MM,
        "label": "Glass",
    },
    "wood": {
        "eps_r": 1.99,
        "tan_d": 0.049,
        "conductivity": 0.0,
        "thickness_mm": WALL_THICKNESS_MM,
        "label": "Wood",
    },
}

MAT_COLORS = {
    "metal": "#1e293b",
    "concrete": "#dc2626",
    "glass": "#2563eb",
    "wood": "#059669",
}
MAT_MARKERS = {"metal": "D", "concrete": "o", "glass": "s", "wood": "^"}


def find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / "simulation_inputs" / "csv").exists():
            return parent
    raise FileNotFoundError("Could not locate repository root from script path.")


def parse_complex(magnitude: np.ndarray, phase_deg: np.ndarray) -> np.ndarray:
    return magnitude * np.exp(1j * np.deg2rad(phase_deg))


def load_m1_cp(path: Path) -> dict[str, np.ndarray]:
    df = pd.read_csv(path)
    cols = df.columns.tolist()
    out = {"freq": df[cols[0]].to_numpy()}
    for i, ch in enumerate(CP_CHANNELS):
        out[ch] = parse_complex(df[cols[1 + 2 * i]].to_numpy(), df[cols[2 + 2 * i]].to_numpy())
    return out


def load_sweep_cp(path: Path) -> dict:
    df = pd.read_csv(path)
    cols = df.columns.tolist()
    thetas = np.array(sorted(df[cols[0]].unique()))
    freq = df[df[cols[0]] == thetas[0]][cols[1]].to_numpy()
    out = {"freq": freq, "thetas": thetas}
    for theta in thetas:
        sub = df[df[cols[0]] == theta]
        out[theta] = {}
        for i, ch in enumerate(CP_CHANNELS):
            out[theta][ch] = parse_complex(
                sub[cols[2 + 2 * i]].to_numpy(),
                sub[cols[3 + 2 * i]].to_numpy(),
            )
    return out


def load_m1_lp(path: Path) -> dict[str, np.ndarray]:
    df = pd.read_csv(path)
    out = {"freq": df.iloc[:, 0].to_numpy()}
    channel_cols = {
        "yy": (
            'mag(S(Rx_y_p1,Tx_y_p1)) []',
            'ang_deg(S(Rx_y_p1,Tx_y_p1)) [deg]',
        ),
        "yz": (
            'mag(S(Rx_y_p1,Tx_z_p1)) []',
            'ang_deg(S(Rx_y_p1,Tx_z_p1)) [deg]',
        ),
        "zy": (
            'mag(S(Rx_z_p1,Tx_y_p1)) []',
            'ang_deg(S(Rx_z_p1,Tx_y_p1)) [deg]',
        ),
        "zz": (
            'mag(S(Rx_z_p1,Tx_z_p1)) []',
            'ang_deg(S(Rx_z_p1,Tx_z_p1)) [deg]',
        ),
    }
    for ch, (mag_col, phase_col) in channel_cols.items():
        out[ch] = parse_complex(df[mag_col].to_numpy(), df[phase_col].to_numpy())
    return out


def load_sweep_lp(path: Path) -> dict:
    df = pd.read_csv(path)
    theta_col = df.columns[0]
    freq_col = df.columns[1]
    thetas = np.array(sorted(df[theta_col].unique()))
    freq = df[df[theta_col] == thetas[0]][freq_col].to_numpy()
    out = {"freq": freq, "thetas": thetas}
    channel_cols = {
        "yy": (
            'mag(S(Rx_y_p1,Tx_y_p1)) []',
            'ang_deg(S(Rx_y_p1,Tx_y_p1)) [deg]',
        ),
        "yz": (
            'mag(S(Rx_y_p1,Tx_z_p1)) []',
            'ang_deg(S(Rx_y_p1,Tx_z_p1)) [deg]',
        ),
        "zy": (
            'mag(S(Rx_z_p1,Tx_y_p1)) []',
            'ang_deg(S(Rx_z_p1,Tx_y_p1)) [deg]',
        ),
        "zz": (
            'mag(S(Rx_z_p1,Tx_z_p1)) []',
            'ang_deg(S(Rx_z_p1,Tx_z_p1)) [deg]',
        ),
    }
    for theta in thetas:
        sub = df[df[theta_col] == theta]
        out[theta] = {}
        for ch, (mag_col, phase_col) in channel_cols.items():
            out[theta][ch] = parse_complex(sub[mag_col].to_numpy(), sub[phase_col].to_numpy())
    return out


def fresnel_single(eps_r: complex, theta_i_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    theta = np.deg2rad(theta_i_deg)
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    sqrt_term = np.sqrt(eps_r - sin_t**2 + 0j)
    r_te = (cos_t - sqrt_term) / (cos_t + sqrt_term)
    r_tm = (eps_r * cos_t - sqrt_term) / (eps_r * cos_t + sqrt_term)
    return r_te, r_tm


def fresnel_slab(
    eps_r: complex,
    theta_i_deg: np.ndarray,
    thickness_mm: float | None,
    freq_ghz: float,
) -> tuple[np.ndarray, np.ndarray]:
    theta = np.deg2rad(theta_i_deg)
    lam_mm = 300 / freq_ghz
    k0 = 2 * np.pi / lam_mm
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    sqrt_eps = np.sqrt(eps_r - sin_t**2 + 0j)

    r_te = (cos_t - sqrt_eps) / (cos_t + sqrt_eps)
    r_tm = (eps_r * cos_t - sqrt_eps) / (eps_r * cos_t + sqrt_eps)
    if thickness_mm is None:
        return r_te, r_tm

    delta = k0 * thickness_mm * sqrt_eps
    e2d = np.exp(-2j * delta)
    r_te_total = r_te * (1 - e2d) / (1 - r_te**2 * e2d)
    r_tm_total = r_tm * (1 - e2d) / (1 - r_tm**2 * e2d)
    return r_te_total, r_tm_total


def cp_from_te_tm(r_te: np.ndarray, r_tm: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    gamma_x = (r_te + r_tm) / 2
    gamma_c = (r_te - r_tm) / 2
    return gamma_x, gamma_c


def compute_theory(theta_dense: np.ndarray, freq_ghz: float) -> dict:
    theory = {}
    for mat, props in MATERIAL_PROPS.items():
        if mat == "metal":
            r_te_single = -np.ones_like(theta_dense, dtype=complex)
            r_tm_single = -np.ones_like(theta_dense, dtype=complex)
            r_te_slab = r_te_single.copy()
            r_tm_slab = r_tm_single.copy()
            gamma_x_single, gamma_c_single = cp_from_te_tm(r_te_single, r_tm_single)
            gamma_x_slab, gamma_c_slab = gamma_x_single.copy(), gamma_c_single.copy()
            brewster = np.nan
        else:
            eps_c = props["eps_r"] * (1 - 1j * props["tan_d"])
            r_te_single, r_tm_single = fresnel_single(eps_c, theta_dense)
            r_te_slab, r_tm_slab = fresnel_slab(
                eps_c, theta_dense, props["thickness_mm"], freq_ghz
            )
            gamma_x_single, gamma_c_single = cp_from_te_tm(r_te_single, r_tm_single)
            gamma_x_slab, gamma_c_slab = cp_from_te_tm(r_te_slab, r_tm_slab)
            brewster = np.rad2deg(np.arctan(np.sqrt(np.real(eps_c))))
        theory[mat] = {
            "R_TE_single": r_te_single,
            "R_TM_single": r_tm_single,
            "R_TE_slab": r_te_slab,
            "R_TM_slab": r_tm_slab,
            "Gamma_X_single": gamma_x_single,
            "Gamma_C_single": gamma_c_single,
            "Gamma_X_slab": gamma_x_slab,
            "Gamma_C_slab": gamma_c_slab,
            "Brewster": brewster,
        }
    return theory


def compute_cp_patch_stage(cp_dir: Path) -> tuple[dict, np.ndarray, np.ndarray]:
    m1 = load_m1_cp(cp_dir / "m1_los_5000.csv")
    m3 = load_sweep_cp(cp_dir / "m3_off-boresigjt.csv")
    m2 = {
        mat: load_sweep_cp(cp_dir / f"m2_{mat}_R_5000.csv")
        for mat in MATERIALS
    }

    thetas = m3["thetas"]
    freq = m1["freq"]
    gamma = {}
    for mat in MATERIALS:
        gamma[mat] = {}
        for theta in thetas:
            h2 = m2[mat][theta]
            h3 = m3[theta]
            h_tilde = {ch: h2[ch] - m1[ch] for ch in CP_CHANNELS}

            ratio = (h_tilde["LR"] * h_tilde["RL"]) / (h3["RR"] * h3["LL"])
            gamma_x = np.sqrt(np.abs(ratio)) * np.exp(1j * np.angle(ratio) / 2)

            eps_eff = h3["LR"] / h3["RR"]
            gamma_c_raw = h_tilde["RR"] / h3["RR"]
            gamma_c_corr = gamma_c_raw - eps_eff * gamma_x

            gamma[mat][theta] = {
                "Gamma_X": gamma_x,
                "Gamma_C_raw": gamma_c_raw,
                "Gamma_C_corr": gamma_c_corr,
                "R_TE_proxy": gamma_x + gamma_c_corr,
                "R_TM_proxy": gamma_x - gamma_c_corr,
            }
    return gamma, freq, thetas


def detect_lp_files(csv_dir: Path) -> tuple[dict, list[Path]]:
    def first_existing(*names: str) -> Path | None:
        for name in names:
            path = csv_dir / name
            if path.exists():
                return path
        return None

    lp_files = {
        "m1": first_existing("LP_m1_los_5000.csv", "m1_lp_los_5000.csv"),
        "m3": first_existing("LP_m3_off-boresigjt.csv", "m3_lp_off-boresight.csv"),
        "m2": {
            mat: first_existing(
                f"LP_m2_{mat}_R_5000.csv",
                f"m2_lp_{mat}_R_5000.csv",
            )
            for mat in MATERIALS
        },
        "m2_transmission": {
            mat: first_existing(
                f"LP_m2_{mat}_T_5000.csv",
                f"m2_lp_{mat}_T_5000.csv",
            )
            for mat in MATERIALS
        },
    }

    missing: list[Path] = []
    if lp_files["m1"] is None:
        missing.append(csv_dir / "LP_m1_los_5000.csv")
    if lp_files["m3"] is None:
        missing.append(csv_dir / "LP_m3_off-boresigjt.csv")
    for mat in MATERIALS:
        if lp_files["m2"][mat] is None:
            missing.append(csv_dir / f"LP_m2_{mat}_R_5000.csv")
    return lp_files, missing


def compute_lp_direct(lp_files: dict) -> tuple[dict, np.ndarray]:
    m1 = load_m1_lp(lp_files["m1"])
    m3 = load_sweep_lp(lp_files["m3"])
    m2 = {mat: load_sweep_lp(lp_files["m2"][mat]) for mat in MATERIALS}

    lp_gamma = {}
    for mat in MATERIALS:
        lp_gamma[mat] = {}
        for theta in m3["thetas"]:
            h2 = m2[mat][theta]
            h3 = m3[theta]
            h_tilde = {ch: h2[ch] - m1[ch] for ch in LP_CHANNELS}

            r_te = h_tilde["zz"] / h3["zz"]
            r_tm = h_tilde["yy"] / h3["yy"]
            gamma_x, gamma_c = cp_from_te_tm(r_te, r_tm)

            lp_gamma[mat][theta] = {
                "R_TE": r_te,
                "R_TM": r_tm,
                "Gamma_X": gamma_x,
                "Gamma_C": gamma_c,
                "cross_zy": h_tilde["zy"] / h3["zz"],
                "cross_yz": h_tilde["yz"] / h3["yy"],
            }
    return lp_gamma, m3["thetas"]


def band_mean_abs(values: np.ndarray) -> float:
    return float(np.mean(np.abs(values)))


def plot_theory_vs_stage(
    output_dir: Path,
    theory: dict,
    cp_gamma: dict,
    lp_gamma: dict | None,
    theta_dense: np.ndarray,
    cp_thetas: np.ndarray,
    lp_thetas: np.ndarray | None,
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("TE/TM Theory vs Patch-Stage Outputs", fontweight="bold")

    for idx, mat in enumerate(["concrete", "glass", "wood", "metal"]):
        ax = axes[idx // 2, idx % 2]
        props = MATERIAL_PROPS[mat]
        item = theory[mat]

        ax.plot(theta_dense, np.abs(item["R_TE_single"]), "-", color="#2563eb", lw=1.5, label=r"$|R_{TE}|$ theory(single)")
        ax.plot(theta_dense, np.abs(item["R_TM_single"]), "-", color="#dc2626", lw=1.5, label=r"$|R_{TM}|$ theory(single)")
        if props["thickness_mm"] is not None:
            ax.plot(theta_dense, np.abs(item["R_TE_slab"]), "--", color="#2563eb", lw=1.0, alpha=0.7, label=r"$|R_{TE}|$ theory(slab)")
            ax.plot(theta_dense, np.abs(item["R_TM_slab"]), "--", color="#dc2626", lw=1.0, alpha=0.7, label=r"$|R_{TM}|$ theory(slab)")

        rte_cp = [band_mean_abs(cp_gamma[mat][th]["R_TE_proxy"]) for th in cp_thetas]
        rtm_cp = [band_mean_abs(cp_gamma[mat][th]["R_TM_proxy"]) for th in cp_thetas]
        ax.plot(cp_thetas, rte_cp, "v", color="#2563eb", markersize=6, label=r"$R_{TE}$ CP proxy")
        ax.plot(cp_thetas, rtm_cp, "^", color="#dc2626", markersize=6, label=r"$R_{TM}$ CP proxy")

        if lp_gamma is not None and lp_thetas is not None:
            rte_lp = [band_mean_abs(lp_gamma[mat][th]["R_TE"]) for th in lp_thetas]
            rtm_lp = [band_mean_abs(lp_gamma[mat][th]["R_TM"]) for th in lp_thetas]
            ax.plot(lp_thetas, rte_lp, "o", color="#2563eb", markersize=8, mfc="none", mew=1.8, label=r"$R_{TE}$ LP direct")
            ax.plot(lp_thetas, rtm_lp, "o", color="#dc2626", markersize=8, mfc="none", mew=1.8, label=r"$R_{TM}$ LP direct")

        if np.isfinite(item["Brewster"]):
            ax.axvline(item["Brewster"], color="gray", ls=":", lw=0.8)
        ax.set_xlim([0, 90])
        ax.set_ylim([0, 1.05])
        ax.set_xlabel(r"$\theta_i$ [deg]")
        ax.set_ylabel(r"$|R|$")
        ax.set_title(props["label"])
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7, loc="upper left")

    fig.tight_layout()
    fig.savefig(output_dir / "lp_fig1_theory_vs_sim.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_cp_comparison(
    output_dir: Path,
    theory: dict,
    cp_gamma: dict,
    theta_dense: np.ndarray,
    thetas: np.ndarray,
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("CP Patch-Stage Quantities vs Theory-Derived CP Curves", fontweight="bold")

    for idx, mat in enumerate(["concrete", "glass", "wood", "metal"]):
        ax = axes[idx // 2, idx % 2]
        props = MATERIAL_PROPS[mat]
        item = theory[mat]

        ax.plot(theta_dense, np.abs(item["Gamma_X_single"]), "-", color="#7c3aed", lw=1.5, label=r"$|\Gamma_X|$ theory(single)")
        ax.plot(theta_dense, np.abs(item["Gamma_C_single"]), "-", color="#ea580c", lw=1.5, label=r"$|\Gamma_C|$ theory(single)")
        if props["thickness_mm"] is not None:
            ax.plot(theta_dense, np.abs(item["Gamma_X_slab"]), "--", color="#7c3aed", lw=1.0, alpha=0.7, label=r"$|\Gamma_X|$ theory(slab)")
            ax.plot(theta_dense, np.abs(item["Gamma_C_slab"]), "--", color="#ea580c", lw=1.0, alpha=0.7, label=r"$|\Gamma_C|$ theory(slab)")

        gamma_x = [band_mean_abs(cp_gamma[mat][th]["Gamma_X"]) for th in thetas]
        gamma_c = [band_mean_abs(cp_gamma[mat][th]["Gamma_C_corr"]) for th in thetas]
        ax.plot(thetas, gamma_x, "v", color="#7c3aed", markersize=6, label=r"$\hat{\Gamma}_X$ CP patch")
        ax.plot(thetas, gamma_c, "^", color="#ea580c", markersize=6, label=r"$\hat{\Gamma}_C^{corr}$ CP patch")

        if np.isfinite(item["Brewster"]):
            ax.axvline(item["Brewster"], color="gray", ls=":", lw=0.8)
        ax.set_xlim([0, 90])
        ax.set_xlabel(r"$\theta_i$ [deg]")
        ax.set_ylabel(r"$|\Gamma|$")
        ax.set_title(props["label"])
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7)

    fig.tight_layout()
    fig.savefig(output_dir / "lp_fig2_cp_theory_comparison.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_suppression(
    output_dir: Path,
    theory: dict,
    cp_gamma: dict,
    theta_dense: np.ndarray,
    thetas: np.ndarray,
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("CP Patch-Stage Suppression Metrics", fontweight="bold")

    ax = axes[0]
    for mat in ["concrete", "glass", "wood"]:
        item = theory[mat]
        lp_worst = np.maximum(np.abs(item["R_TE_single"]), np.abs(item["R_TM_single"]))
        cp_co = np.abs(item["Gamma_C_single"])
        suppression = 20 * np.log10(lp_worst / np.maximum(cp_co, 1e-10))
        ax.plot(theta_dense, suppression, "-", color=MAT_COLORS[mat], lw=1.5, label=MATERIAL_PROPS[mat]["label"])
    ax.set_xlim([5, 85])
    ax.set_xlabel(r"$\theta_i$ [deg]")
    ax.set_ylabel("Suppression gain [dB]")
    ax.set_title("(a) Theory: LP worst / CP co")
    ax.grid(True, alpha=0.3)
    ax.legend()

    ax = axes[1]
    for mat in ["concrete", "glass", "wood"]:
        rte = np.array([band_mean_abs(cp_gamma[mat][t]["R_TE_proxy"]) for t in thetas])
        rtm = np.array([band_mean_abs(cp_gamma[mat][t]["R_TM_proxy"]) for t in thetas])
        gamma_c = np.array([band_mean_abs(cp_gamma[mat][t]["Gamma_C_corr"]) for t in thetas])
        lp_proxy = np.maximum(rte, rtm)
        suppression = 20 * np.log10(lp_proxy / np.maximum(gamma_c, 1e-10))
        ax.plot(thetas, suppression, f"{MAT_MARKERS[mat]}-", color=MAT_COLORS[mat], markersize=5, label=MATERIAL_PROPS[mat]["label"])
    ax.set_xlabel(r"$\theta_i$ [deg]")
    ax.set_ylabel("Suppression gain [dB]")
    ax.set_title("(b) CP patch proxy: max(R_TE, R_TM) / Gamma_C")
    ax.grid(True, alpha=0.3)
    ax.legend()

    ax = axes[2]
    for mat in ["concrete", "glass", "wood"]:
        item = theory[mat]
        xpd_theory = 20 * np.log10(np.abs(item["Gamma_X_single"]) / np.maximum(np.abs(item["Gamma_C_single"]), 1e-10))
        ax.plot(theta_dense, xpd_theory, "-", color=MAT_COLORS[mat], lw=1.0, alpha=0.5)
        xpd_cp = [
            20
            * np.log10(
                band_mean_abs(cp_gamma[mat][th]["Gamma_X"])
                / max(band_mean_abs(cp_gamma[mat][th]["Gamma_C_corr"]), 1e-10)
            )
            for th in thetas
        ]
        ax.plot(thetas, xpd_cp, f"{MAT_MARKERS[mat]}-", color=MAT_COLORS[mat], markersize=5, label=MATERIAL_PROPS[mat]["label"])
    ax.axhline(0, color="gray", ls=":", lw=1)
    ax.set_xlim([5, 85])
    ax.set_xlabel(r"$\theta_i$ [deg]")
    ax.set_ylabel("XPD [dB]")
    ax.set_title("(c) Theory line vs CP patch markers")
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_dir / "lp_fig3_suppression_gain.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_accuracy(
    output_dir: Path,
    theory: dict,
    cp_gamma: dict,
    lp_gamma: dict | None,
    cp_thetas: np.ndarray,
    lp_thetas: np.ndarray | None,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Accuracy vs Fresnel Theory", fontweight="bold")

    pairs = [("R_TE_proxy", "R_TE", "R_TE"), ("R_TM_proxy", "R_TM", "R_TM")]
    for col, (cp_key, lp_key, label) in enumerate(pairs):
        ax = axes[col]
        for mat in ["concrete", "glass", "wood"]:
            eps_c = MATERIAL_PROPS[mat]["eps_r"] * (1 - 1j * MATERIAL_PROPS[mat]["tan_d"])
            cp_dev = []
            lp_dev = []
            for theta in cp_thetas:
                r_te_th, r_tm_th = fresnel_single(eps_c, theta)
                theory_val = np.abs(r_te_th) if label == "R_TE" else np.abs(r_tm_th)
                cp_val = band_mean_abs(cp_gamma[mat][theta][cp_key])
                cp_dev.append(20 * np.log10(cp_val / theory_val) if theory_val > 1e-10 else np.nan)
            if lp_gamma is not None and lp_thetas is not None:
                for theta in lp_thetas:
                    r_te_th, r_tm_th = fresnel_single(eps_c, theta)
                    theory_val = np.abs(r_te_th) if label == "R_TE" else np.abs(r_tm_th)
                    lp_val = band_mean_abs(lp_gamma[mat][theta][lp_key])
                    lp_dev.append(20 * np.log10(lp_val / theory_val) if theory_val > 1e-10 else np.nan)

            ax.plot(cp_thetas, cp_dev, f"{MAT_MARKERS[mat]}-", color=MAT_COLORS[mat], markersize=5, label=f"{MATERIAL_PROPS[mat]['label']} CP")
            if lp_gamma is not None and lp_thetas is not None:
                ax.plot(lp_thetas, lp_dev, f"{MAT_MARKERS[mat]}--", color=MAT_COLORS[mat], markersize=5, alpha=0.8, label=f"{MATERIAL_PROPS[mat]['label']} LP")

        ax.axhline(0, color="black", lw=0.6)
        ax.axhline(3, color="gray", ls=":", lw=0.8, alpha=0.6)
        ax.axhline(-3, color="gray", ls=":", lw=0.8, alpha=0.6)
        ax.set_xlabel(r"$\theta_i$ [deg]")
        ax.set_ylabel(f"{label} deviation [dB]")
        ax.set_title(f"{label}: patch-stage output / Fresnel theory")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7)

    fig.tight_layout()
    fig.savefig(output_dir / "lp_fig4_calibration_accuracy.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def print_accuracy_table(cp_gamma: dict, thetas: np.ndarray) -> None:
    print("\n" + "=" * 72)
    print("CP PATCH-STAGE PROXIES VS FRESNEL THEORY (single-interface reference)")
    print("=" * 72)
    for mat in ["concrete", "glass", "wood"]:
        props = MATERIAL_PROPS[mat]
        eps_c = props["eps_r"] * (1 - 1j * props["tan_d"])
        print(f"\n[{props['label']}] eps_r={props['eps_r']:.2f}, tan_d={props['tan_d']:.4f}")
        print(f"{'theta':>5s} | {'|R_TE| th':>9s} {'|R_TE| cp':>10s} {'dB':>7s} | {'|R_TM| th':>9s} {'|R_TM| cp':>10s} {'dB':>7s}")
        print("-" * 72)
        for theta in thetas:
            r_te_th, r_tm_th = fresnel_single(eps_c, theta)
            r_te_cp = band_mean_abs(cp_gamma[mat][theta]["R_TE_proxy"])
            r_tm_cp = band_mean_abs(cp_gamma[mat][theta]["R_TM_proxy"])
            d_te = 20 * np.log10(r_te_cp / np.abs(r_te_th)) if np.abs(r_te_th) > 1e-10 else np.nan
            d_tm = 20 * np.log10(r_tm_cp / np.abs(r_tm_th)) if np.abs(r_tm_th) > 1e-10 else np.nan
            print(
                f"{theta:5.0f} | {np.abs(r_te_th):9.4f} {r_te_cp:10.4f} {d_te:7.1f} | "
                f"{np.abs(r_tm_th):9.4f} {r_tm_cp:10.4f} {d_tm:7.1f}"
            )


def print_lp_isolation(lp_gamma: dict, thetas: np.ndarray) -> None:
    print("\nLP cross-polar isolation check")
    print(f"{'theta':>5s} | {'|cross_zy|':>11s} | {'|cross_yz|':>11s}")
    print("-" * 37)
    for theta in thetas:
        zy_vals = []
        yz_vals = []
        for mat in ["concrete", "glass", "wood"]:
            zy_vals.append(band_mean_abs(lp_gamma[mat][theta]["cross_zy"]))
            yz_vals.append(band_mean_abs(lp_gamma[mat][theta]["cross_yz"]))
        zy_db = 20 * np.log10(np.mean(zy_vals))
        yz_db = 20 * np.log10(np.mean(yz_vals))
        print(f"{theta:5.0f} | {zy_db:9.1f} dB | {yz_db:9.1f} dB")


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LP patch-stage analysis based on theory, CP proxies, and optional LP-direct CSVs."
    )
    stage_root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--csv-dir",
        type=Path,
        default=stage_root / "csv",
        help="Directory that stores stage CSV inputs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=stage_root / "results",
        help="Directory where stage figures are written.",
    )
    parser.add_argument(
        "--with-lp",
        action="store_true",
        help="Require LP CSV inputs and process LP-direct ratios.",
    )
    return parser


def main() -> None:
    args = build_argparser().parse_args()
    csv_dir = args.csv_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("LP PATCH-STAGE ANALYSIS")
    print("Theory + CP-derived proxies + optional LP-direct ratios")
    print("=" * 72)
    print(f"CSV dir:    {csv_dir}")
    print(f"Output dir: {output_dir}")

    cp_gamma, freq, thetas = compute_cp_patch_stage(csv_dir)
    freq_center = float(np.mean(freq))
    theta_dense = np.linspace(0.1, 89.9, 500)
    theory = compute_theory(theta_dense, freq_center)

    print(f"\nLoaded CP patch-stage inputs at {freq[0]:.3f}-{freq[-1]:.3f} GHz, center {freq_center:.3f} GHz")
    print(f"theta_i sweep: {thetas.tolist()}")

    lp_files, missing_lp = detect_lp_files(csv_dir)
    lp_gamma = None
    lp_thetas = None
    if args.with_lp and missing_lp:
        missing_text = "\n".join(str(path) for path in missing_lp)
        raise FileNotFoundError(f"LP CSVs were requested but are missing:\n{missing_text}")
    if not missing_lp:
        print("\nLP CSVs found. Running LP-direct extraction.")
        lp_gamma, lp_thetas = compute_lp_direct(lp_files)
        print_lp_isolation(lp_gamma, lp_thetas)
    else:
        print("\nLP CSVs not found. Running theory + CP patch proxy comparison only.")
        for path in missing_lp:
            print(f"  missing: {path.name}")

    plot_theory_vs_stage(output_dir, theory, cp_gamma, lp_gamma, theta_dense, thetas, lp_thetas)
    plot_cp_comparison(output_dir, theory, cp_gamma, theta_dense, thetas)
    plot_suppression(output_dir, theory, cp_gamma, theta_dense, thetas)
    plot_accuracy(output_dir, theory, cp_gamma, lp_gamma, thetas, lp_thetas)
    print_accuracy_table(cp_gamma, thetas)

    print("\nWrote figures:")
    print(f"  {output_dir / 'lp_fig1_theory_vs_sim.png'}")
    print(f"  {output_dir / 'lp_fig2_cp_theory_comparison.png'}")
    print(f"  {output_dir / 'lp_fig3_suppression_gain.png'}")
    print(f"  {output_dir / 'lp_fig4_calibration_accuracy.png'}")


if __name__ == "__main__":
    main()
